"""
Consumidor asíncrono de telemetría espacial mediante Redis (redis.asyncio).

Extrae mensajes de la cola de telemetría de espacio profundo utilizando operaciones RPOP
sin bloquear el hilo de ejecución principal de FastAPI. Aplica reconexión automática y
tolerancia a fallos de enlace.
"""

import asyncio
import json
import logging
from typing import Any, Callable
import redis.asyncio as aioredis
from redis.exceptions import ConnectionError as RedisConnectionError, RedisError

from helios_inference.domain.inference_models import ReporteInferenciaConsolidado
from helios_inference.services.inference_engine import InferenceEngine

logger = logging.getLogger(__name__)


class AsyncRedisTelemetryConsumer:
    """
    Consumidor asíncrono no bloqueante para ingesta de telemetría desde colas Redis.
    Desacopla la capa de red del procesamiento analítico de los 4 cerebros.
    """

    def __init__(
        self,
        motor_inferencia: InferenceEngine,
        host: str = "127.0.0.1",
        port: int = 6379,
        db: int = 0,
        colas: list[str] | None = None,
        intervalo_sondeo_segundos: float = 0.5,
        intervalo_reintento_segundos: float = 3.0,
        callback_reporte: Callable[[ReporteInferenciaConsolidado], None] | None = None,
    ) -> None:
        """
        Inicializa el consumidor asíncrono.

        Args:
            motor_inferencia: Instancia del orquestador central con los 4 cerebros.
            host: Dirección de red del servidor Redis.
            port: Puerto del servicio Redis.
            db: Base de datos lógica en Redis.
            colas: Lista priorizada de colas donde buscar mensajes con RPOP.
            intervalo_sondeo_segundos: Pausa entre comprobaciones cuando la cola está vacía.
            intervalo_reintento_segundos: Tiempo de espera ante interrupciones de enlace.
            callback_reporte: Función opcional invocada con cada reporte consolidado producido.
        """
        self._motor = motor_inferencia
        self._host = host
        self._port = port
        self._db = db
        self._colas = colas or ["buzon_telemetria_tierra", "buzon_telemetria_tierra_queue"]
        self._intervalo_sondeo = intervalo_sondeo_segundos
        self._intervalo_reintento = intervalo_reintento_segundos
        self._callback = callback_reporte

        self._cliente: aioredis.Redis | None = None
        self._activo: bool = False
        self._tarea_background: asyncio.Task[None] | None = None
        self._ultimo_reporte: ReporteInferenciaConsolidado | None = None
        self._ultimo_payload: dict[str, Any] | None = None
        self._contador_procesados: int = 0
        self._conectado: bool = False

    @property
    def conectado(self) -> bool:
        """Indica si el enlace con Redis está actualmente operativo."""
        return self._conectado

    @property
    def contador_procesados(self) -> int:
        """Número de payloads de telemetría procesados desde el inicio."""
        return self._contador_procesados

    @property
    def ultimo_reporte(self) -> ReporteInferenciaConsolidado | None:
        """Último reporte de inferencia generado por el motor."""
        return self._ultimo_reporte

    @property
    def ultimo_payload(self) -> dict[str, Any] | None:
        """
        Telemetría cruda que originó el último reporte.

        El compactador la requiere para emitir los valores numéricos del registro
        de enlace sin tener que parsear las cadenas descriptivas del reporte.
        """
        return self._ultimo_payload

    async def conectar(self) -> bool:
        """
        Establece el enlace asíncrono con el servidor Redis.

        Returns:
            True si el servidor responde a PING, False si la conexión falla.
        """
        try:
            self._cliente = aioredis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                socket_timeout=2.0,
                socket_connect_timeout=2.0,
                decode_responses=True,
            )
            await self._cliente.ping()
            self._conectado = True
            logger.info("Consumidor asíncrono conectado exitosamente a Redis en %s:%d", self._host, self._port)
            return True
        except (RedisConnectionError, RedisError, OSError) as error:
            self._conectado = False
            logger.info(
                "Redis no disponible en %s:%d (%s). El consumidor continuará reintentando en background.",
                self._host,
                self._port,
                str(error),
            )
            return False

    async def iniciar(self) -> None:
        """Inicia el bucle asíncrono de consumo en segundo plano."""
        if self._activo:
            return
        self._activo = True
        self._tarea_background = asyncio.create_task(self._bucle_consumo())
        logger.info("Tarea de consumo en background iniciada.")

    async def detener(self) -> None:
        """Detiene de forma ordenada el bucle asíncrono y cierra el socket de Redis."""
        self._activo = False
        if self._tarea_background:
            self._tarea_background.cancel()
            try:
                await self._tarea_background
            except asyncio.CancelledError:
                pass
        if self._cliente:
            await self._cliente.aclose()
            self._cliente = None
        self._conectado = False
        logger.info("Consumidor asíncrono detenido correctamente.")

    async def _bucle_consumo(self) -> None:
        """Bucle principal asíncrono que sondea las colas de Redis con RPOP."""
        while self._activo:
            if not self._conectado or self._cliente is None:
                exito = await self.conectar()
                if not exito:
                    await asyncio.sleep(self._intervalo_reintento)
                    continue

            try:
                mensaje_crudo: str | None = None
                cola_activa: str | None = None

                # Revisar las colas configuradas mediante RPOP
                for cola in self._colas:
                    mensaje_crudo = await self._cliente.rpop(cola)
                    if mensaje_crudo:
                        cola_activa = cola
                        break

                if mensaje_crudo:
                    logger.debug("Mensaje de telemetría extraído de '%s' (%d bytes)", cola_activa, len(mensaje_crudo))
                    self._procesar_mensaje_json(mensaje_crudo)
                else:
                    # Si no hay mensajes pendientes, esperar el intervalo de sondeo
                    await asyncio.sleep(self._intervalo_sondeo)

            except (RedisConnectionError, RedisError, OSError) as error_red:
                self._conectado = False
                logger.error("Error en comunicación con Redis: %s. Esperando reintento...", str(error_red))
                await asyncio.sleep(self._intervalo_reintento)
            except Exception as error_inesperado:
                logger.error("Excepción inesperada en bucle de consumo: %s", str(error_inesperado), exc_info=True)
                await asyncio.sleep(self._intervalo_sondeo)

    def _procesar_mensaje_json(self, mensaje_crudo: str) -> None:
        """
        Deserializa el payload y lo envía al pipeline analítico de los 4 cerebros.

        Args:
            mensaje_crudo: Cadena JSON extraída de Redis.
        """
        try:
            payload: dict[str, Any] = json.loads(mensaje_crudo)
            reporte = self._motor.procesar_telemetria(payload)
            self._ultimo_reporte = reporte
            self._ultimo_payload = payload
            self._contador_procesados += 1

            if self._callback:
                self._callback(reporte)

        except json.JSONDecodeError as error_json:
            logger.error("Error al decodificar JSON de telemetría: %s", str(error_json))
        except Exception as error_inferencia:
            logger.error("Error en el pipeline de inferencia: %s", str(error_inferencia), exc_info=True)
