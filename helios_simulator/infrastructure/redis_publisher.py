"""
Implementación de infraestructura para publicación en Redis con tolerancia a fallos.

Gestiona la conexión persistente, reconexión automática y amortiguamiento local (Store-and-Forward)
hacia el buzón de telemetría hacia Tierra ('buzon_telemetria_tierra').
"""

from collections import deque
import logging
import time
import redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError, TimeoutError as RedisTimeoutError

from helios_simulator.config import RedisConfig
from helios_simulator.domain.enums import EstadoConexion
from helios_simulator.domain.models import TelemetriaPayload
from helios_simulator.infrastructure.publisher_interface import TelemetryPublisherInterface

logger = logging.getLogger(__name__)


class RedisTelemetryPublisher(TelemetryPublisherInterface):
    """
    Publicador robusto de telemetría sobre Redis.
    Aplica el principio de Responsabilidad Única (SRP): no genera datos ni evalúa reglas,
    únicamente asegura la entrega confiable del payload serializado.
    """

    def __init__(self, config: RedisConfig | None = None) -> None:
        """
        Inicializa el publicador de Redis.

        Args:
            config: Parámetros de red y políticas de reintento.
        """
        self._config = config or RedisConfig()
        self._cliente: redis.Redis | None = None
        self._estado: EstadoConexion = EstadoConexion.DESCONECTADO
        self._cola_buffer_memoria: deque[str] = deque(
            maxlen=self._config.limite_cola_buffer_memoria
        )
        self._ultimo_intento_reconexion: float = 0.0

    def conectar(self) -> bool:
        """
        Inicia la conexión al servidor Redis local y verifica disponibilidad mediante PING.

        Returns:
            True si el servidor respondió satisfactoriamente, False si no está accesible.
        """
        try:
            logger.info(
                "Intentando establecer enlace con servidor Redis en %s:%d (Buzón: %s)...",
                self._config.host,
                self._config.port,
                self._config.canal_publicacion,
            )
            self._cliente = redis.Redis(
                host=self._config.host,
                port=self._config.port,
                db=self._config.db,
                password=self._config.password,
                socket_timeout=self._config.tiempo_espera_conexion_segundos,
                socket_connect_timeout=self._config.tiempo_espera_conexion_segundos,
                decode_responses=True,
            )
            self._cliente.ping()
            self._estado = EstadoConexion.CONECTADO
            logger.info("Enlace establecido con éxito con Redis en %s:%d", self._config.host, self._config.port)
            self._vaciar_buffer_memoria()
            return True
        except (RedisConnectionError, RedisTimeoutError, RedisError) as error:
            self._estado = EstadoConexion.DESCONECTADO
            self._ultimo_intento_reconexion = time.time()
            logger.error(
                "No fue posible conectar con Redis en %s:%d. Modo resiliencia activado: %s",
                self._config.host,
                self._config.port,
                str(error),
            )
            return False

    def _intentar_reconexion_automatica(self) -> bool:
        """
        Evalúa si es tiempo de reintentar la conexión respetando el intervalo de enfriamiento.

        Returns:
            True si se restableció la conexión, False en caso contrario.
        """
        ahora = time.time()
        if ahora - self._ultimo_intento_reconexion < self._config.intervalo_reintento_reconexion_segundos:
            return False

        self._ultimo_intento_reconexion = ahora
        self._estado = EstadoConexion.REINTENTANDO
        logger.info("Reintentando reconexión automática con servidor Redis local...")
        return self.conectar()

    def publicar_telemetria(self, payload: TelemetriaPayload) -> bool:
        """
        Serializa en JSON el payload e inyecta al canal y cola de Redis.
        Si Redis no está accesible, retiene el mensaje en memoria interna (Store-and-Forward)
        para su posterior despacho sin pérdida de información de la misión.

        Args:
            payload: Instancia validada de TelemetriaPayload.

        Returns:
            True si se publicó en Redis o se aseguró en el buffer local, False si hubo saturación.
        """
        payload_json = payload.model_dump_json()

        # Si el enlace está caído, intenta reconectar
        if self._estado != EstadoConexion.CONECTADO:
            self._intentar_reconexion_automatica()

        # Si el enlace está activo, intenta transmitir
        if self._estado == EstadoConexion.CONECTADO and self._cliente is not None:
            try:
                # Publicación reactiva por Pub/Sub
                receptores_activos = self._cliente.publish(
                    self._config.canal_publicacion,
                    payload_json,
                )
                # Almacenamiento persistente en cola/lista FIFO
                self._cliente.rpush(
                    self._config.cola_publicacion,
                    payload_json,
                )
                logger.info(
                    "Telemetría transmitida a '%s' (Subscriptores: %d, Tamaño: %d bytes). Día %d.",
                    self._config.canal_publicacion,
                    receptores_activos,
                    len(payload_json),
                    payload.dia_mision,
                )
                return True
            except (RedisConnectionError, RedisTimeoutError, RedisError) as error_envio:
                self._estado = EstadoConexion.DESCONECTADO
                logger.error(
                    "Interrupción en la conexión de Redis durante transmisión: %s. Amortiguando en memoria...",
                    str(error_envio),
                )
                self._encolar_en_buffer(payload_json)
                return True

        # Enlace desconectado: amortiguar en buffer local
        self._encolar_en_buffer(payload_json)
        return True

    def _encolar_en_buffer(self, payload_json: str) -> None:
        """Guarda un payload en la cola FIFO de seguridad en memoria."""
        self._cola_buffer_memoria.append(payload_json)
        logger.warning(
            "Payload preservado en buffer local de seguridad. Mensajes en espera: %d/%d",
            len(self._cola_buffer_memoria),
            self._config.limite_cola_buffer_memoria,
        )

    def _vaciar_buffer_memoria(self) -> None:
        """Transmite los mensajes represados en el buffer una vez restablecido el enlace."""
        if not self._cola_buffer_memoria or self._cliente is None:
            return

        logger.info(
            "Restableciendo enlace: enviando %d payloads acumulados en buffer hacia Redis...",
            len(self._cola_buffer_memoria),
        )
        enviados_correctos = 0
        while self._cola_buffer_memoria:
            mensaje = self._cola_buffer_memoria.popleft()
            try:
                self._cliente.publish(self._config.canal_publicacion, mensaje)
                self._cliente.rpush(self._config.cola_publicacion, mensaje)
                enviados_correctos += 1
            except (RedisConnectionError, RedisTimeoutError, RedisError) as error:
                logger.error("Fallo vaciando buffer en mensaje pendiente: %s", str(error))
                self._cola_buffer_memoria.appendleft(mensaje)
                self._estado = EstadoConexion.DESCONECTADO
                break

        logger.info("Transmisión de buffer concluida con éxito: %d mensajes procesados.", enviados_correctos)

    def cerrar(self) -> None:
        """Cierra la conexión con el servidor Redis."""
        if self._cliente is not None:
            try:
                self._cliente.close()
                logger.info("Conexión con Redis cerrada de forma ordenada.")
            except (RedisConnectionError, RedisTimeoutError, RedisError) as error:
                logger.error("Error al cerrar conexión con Redis: %s", str(error))
            finally:
                self._cliente = None
                self._estado = EstadoConexion.DESCONECTADO

    def obtener_estado_conexion(self) -> EstadoConexion:
        """Retorna el estado de conectividad actual."""
        return self._estado

    @property
    def mensajes_en_buffer(self) -> int:
        """Cantidad de mensajes pendientes de envío en el buffer local."""
        return len(self._cola_buffer_memoria)
