"""
Orquestador del bucle principal de telemetría (Capa de Presentación / Main).

Aplica Inversión de Dependencias (DIP) al recibir el publicador de infraestructura
por inyección y coordina los servicios de generación y evaluación preliminar.
"""

from datetime import datetime, timezone
import logging
import signal
import time
from typing import Any

from helios_simulator.config import LimitesNasaConfig, MisionConfig
from helios_simulator.domain.enums import EstadoConexion
from helios_simulator.domain.models import TelemetriaPayload
from helios_simulator.infrastructure.publisher_interface import TelemetryPublisherInterface
from helios_simulator.services.biometrics_generator import GeneradorBiometria
from helios_simulator.services.cognition_generator import GeneradorCognicion
from helios_simulator.services.correlation_evaluator import EvaluadorCorrelacionService
from helios_simulator.services.environment_generator import GeneradorEntorno
from helios_simulator.services.math_noise import redondear_telemetria

logger = logging.getLogger(__name__)


class TelemetriaOrchestrator:
    """
    Orquestador del productor de telemetría de soporte vital HELIOS.
    Coordina la generación periódica cada 2 segundos y la emisión al buzón de Tierra.
    """

    def __init__(
        self,
        publicador: TelemetryPublisherInterface,
        config_mision: MisionConfig | None = None,
        config_limites: LimitesNasaConfig | None = None,
        generador_entorno: GeneradorEntorno | None = None,
        generador_biometria: GeneradorBiometria | None = None,
        generador_cognicion: GeneradorCognicion | None = None,
        evaluador_correlacion: EvaluadorCorrelacionService | None = None,
    ) -> None:
        """
        Constructor con Inyección de Dependencias (DIP).

        Args:
            publicador: Implementación concreta del publicador de telemetría (ej. Redis).
            config_mision: Configuración de identificación y tiempos de misión.
            config_limites: Normativas y umbrales de referencia NASA.
            generador_entorno: Servicio de simulación ambiental (Cerebro 1).
            generador_biometria: Servicio de signos vitales y fatiga (Cerebro 2).
            generador_cognicion: Servicio de cognición y lenguaje (Cerebro 4).
            evaluador_correlacion: Motor de evaluación preliminar y cruce de riesgos.
        """
        self._publicador = publicador
        self._config_mision = config_mision or MisionConfig()
        self._config_limites = config_limites or LimitesNasaConfig()

        self._dia_mision = self._config_mision.dia_mision_default
        self._generador_entorno = generador_entorno or GeneradorEntorno(
            config_limites=self._config_limites,
            dia_mision_inicial=self._dia_mision,
        )
        self._generador_biometria = generador_biometria or GeneradorBiometria(
            config_limites=self._config_limites,
            dia_mision_inicial=self._dia_mision,
        )
        self._generador_cognicion = generador_cognicion or GeneradorCognicion(
            config_limites=self._config_limites,
        )
        self._evaluador_correlacion = evaluador_correlacion or EvaluadorCorrelacionService(
            config_limites=self._config_limites,
        )

        self._en_ejecucion = False
        self._ciclo_actual = 0

    def inicializar_enlaces(self) -> bool:
        """
        Inicia los componentes de comunicación hacia el buzón de telemetría.

        Returns:
            True si el publicador se conectó de inmediato, False si inició en modo resiliente.
        """
        if self._publicador.obtener_estado_conexion() == EstadoConexion.CONECTADO:
            return True

        logger.info(
            "Iniciando subsistema HELIOS v2.1 para la misión %s (Tripulante: %s, Sol: %d)...",
            self._config_mision.id_mision,
            self._config_mision.astronauta_id,
            self._dia_mision,
        )
        return self._publicador.conectar()

    def producir_muestra(
        self,
        forzar_pico_co2: bool = False,
        forzar_tormenta_solar: bool = False,
        forzar_deficiencia_sueno: bool = False,
        forzar_taquicardia: bool = False,
        forzar_incongruencia: bool = False,
    ) -> TelemetriaPayload:
        """
        Ejecuta un ciclo completo de cálculo multivariado y genera el payload consolidado.

        Args:
            forzar_pico_co2: Inyecta pico anómalo de CO2 > 3.0 mmHg.
            forzar_tormenta_solar: Inyecta evento de Tormenta Solar (+20 mSv).
            forzar_deficiencia_sueno: Fuerza registro de sueño < 6.0h.
            forzar_taquicardia: Fuerza ritmo cardiaco elevado.
            forzar_incongruencia: Fuerza estrés cognitivo oculto.

        Returns:
            Instancia completa de TelemetriaPayload lista para transmisión.
        """
        self._ciclo_actual += 1

        # 1. Simulación Cerebro 1: Entorno de cabina
        entorno = self._generador_entorno.generar_lectura(
            forzar_pico_co2=forzar_pico_co2,
            forzar_tormenta_solar=forzar_tormenta_solar,
        )

        # 2. Simulación Cerebro 2: Fisiología y Biometría
        estres_ambiental = (
            entorno.co2_mmHg >= self._config_limites.co2_umbral_sintomas_mmhg
            or entorno.evento_solar_activo
        )
        biometria = self._generador_biometria.generar_lectura(
            estres_ambiental=estres_ambiental,
            forzar_deficiencia_sueno=forzar_deficiencia_sueno,
            forzar_taquicardia=forzar_taquicardia,
        )

        # 3. Simulación Cerebro 4: Psicología y Cognición (ASTRA)
        cognicion = self._generador_cognicion.generar_lectura(
            co2_mmhg=entorno.co2_mmHg,
            horas_sueno=biometria.horas_sueno_ultimo_ciclo,
            ritmo_cardiaco_bpm=biometria.ritmo_cardiaco_bpm,
            evento_solar_activo=entorno.evento_solar_activo,
            forzar_incongruencia=forzar_incongruencia,
        )

        # 4. Evaluación Preliminar y Cruce Normativo NASA-STD-3001
        evaluaciones = self._evaluador_correlacion.evaluar_estado_sistemico(
            entorno=entorno,
            biometria=biometria,
            cognicion=cognicion,
        )

        # 5. Cálculo del presupuesto de radiación de carrera consumido (% de 600 mSv)
        presupuesto_radiacion_pct = (
            entorno.radiacion_acumulada_mSv / self._config_limites.radiacion_limite_carrera_msv
        ) * 100.0

        metadatos: dict[str, Any] = {
            "modulo_productor": "helios_simulator",
            "arquitectura": "Edge AI N-Capas",
            "frecuencia_muestreo_hz": 0.5,
            "intervalo_segundos": self._config_mision.intervalo_emision_segundos,
            "ciclo_muestra_id": self._ciclo_actual,
            "canal_redis": "buzon_telemetria_tierra",
            "enlace_estado": self._publicador.obtener_estado_conexion().value,
        }

        payload = TelemetriaPayload(
            timestamp=datetime.now(timezone.utc),
            id_mision=self._config_mision.id_mision,
            dia_mision=self._dia_mision,
            astronauta_id=self._config_mision.astronauta_id,
            entorno=entorno,
            biometria=biometria,
            cognicion=cognicion,
            evaluaciones_preliminares=evaluaciones,
            porcentaje_presupuesto_radiacion_carrera=redondear_telemetria(presupuesto_radiacion_pct, 2),
            metadatos_sistema=metadatos,
        )

        return payload

    def ejecutar_bucle(self, max_ciclos: int | None = None) -> None:
        """
        Bucle de producción continua de telemetría.
        Emite una muestra cada 2 segundos hacia la capa de infraestructura.

        Args:
            max_ciclos: Límite opcional de iteraciones (ideal para pruebas y ejecuciones acotadas).
        """
        self._en_ejecucion = True
        self._configurar_manejador_senales()
        self.inicializar_enlaces()

        logger.info(
            "Iniciando transmisión continua hacia 'buzon_telemetria_tierra' cada %.1f segundos...",
            self._config_mision.intervalo_emision_segundos,
        )

        try:
            while self._en_ejecucion:
                inicio_ciclo = time.time()

                payload = self.producir_muestra()
                self._publicador.publicar_telemetria(payload)

                # Formateo detallado de telemetría de signos y variables para visualización en vivo
                logger.info(
                    "MUESTRA #%d [Día %d - %s] | ENTORNO: CO2=%.2f mmHg | Rad.Acum=%.2f mSv (%.1f%%) | Presión=%.1f kPa | Temp=%.1f°C | Hum=%.1f%% | SPE=%s",
                    self._ciclo_actual,
                    payload.dia_mision,
                    payload.astronauta_id,
                    payload.entorno.co2_mmHg,
                    payload.entorno.radiacion_acumulada_mSv,
                    payload.porcentaje_presupuesto_radiacion_carrera,
                    payload.entorno.presion_cabina_kpa,
                    payload.entorno.temperatura_cabina_c,
                    payload.entorno.humedad_relativa_pct,
                    "SI" if payload.entorno.evento_solar_activo else "NO",
                )
                logger.info(
                    "             [BIOMETRÍA]: FC=%.1f bpm | SpO2=%.1f%% | PA=%.1f/%.1f | Piel=%.1f°C | Resp=%.1f rpm | HRV=%.1f ms | Sueño=%.1fh | P.Ósea=%.2f%% | Cefalea=%s",
                    payload.biometria.ritmo_cardiaco_bpm,
                    payload.biometria.spo2_pct,
                    payload.biometria.presion_sistolica_mmHg,
                    payload.biometria.presion_diastolica_mmHg,
                    payload.biometria.temperatura_piel_c,
                    payload.biometria.frecuencia_respiratoria_rpm,
                    payload.biometria.variabilidad_cardiaca_hrv_ms,
                    payload.biometria.horas_sueno_ultimo_ciclo,
                    payload.biometria.perdida_osea_pct,
                    "SI" if payload.biometria.dolor_cabeza_sintoma else "NO",
                )
                logger.info(
                    "             [COGNICIÓN]: Lat.Voz=%.1f ms | Densidad=%.2f | EstrésOculto=%s | SANS(Visión)=%s | Fatiga=%s",
                    payload.cognicion.latencia_voz_ms,
                    payload.cognicion.densidad_lexica_score,
                    "SI" if payload.cognicion.incongruencia_estres_oculto else "NO",
                    "SI" if payload.cognicion.sans_sintoma_vision else "NO",
                    "ALERTA" if payload.biometria.alerta_riesgo_fatiga else "NOMINAL",
                )

                if payload.evaluaciones_preliminares:
                    for alerta in payload.evaluaciones_preliminares:
                        logger.warning(
                            "   >>> [%s] %s: %s (Estándar: %s)",
                            alerta.nivel.value,
                            alerta.codigo,
                            alerta.descripcion,
                            alerta.estandar_referencia,
                        )

                if max_ciclos is not None and self._ciclo_actual >= max_ciclos:
                    logger.info("Alcanzado el número máximo de ciclos solicitado (%d). Deteniendo...", max_ciclos)
                    break

                tiempo_transcurrido = time.time() - inicio_ciclo
                tiempo_pausa = max(0.0, self._config_mision.intervalo_emision_segundos - tiempo_transcurrido)
                time.sleep(tiempo_pausa)
        except KeyboardInterrupt:
            logger.info("Interrupción voluntaria del operador de misión detectada.")
        finally:
            self.detener()

    def detener(self) -> None:
        """Detiene de manera controlada la emisión y libera los recursos del publicador."""
        self._en_ejecucion = False
        logger.info("Deteniendo orquestador de telemetría HELIOS...")
        self._publicador.cerrar()

    def _configurar_manejador_senales(self) -> None:
        """Configura los interceptores de señales POSIX/Windows para salida limpia."""
        try:
            signal.signal(signal.SIGINT, self._manejador_interrupcion)
            signal.signal(signal.SIGTERM, self._manejador_interrupcion)
        except (ValueError, AttributeError):
            pass

    def _manejador_interrupcion(self, signum: int, frame: Any) -> None:
        """Callback invocado al interceptar SIGINT o SIGTERM."""
        logger.info("Señal de terminación recibida (%d). Concluyendo ciclo...", signum)
        self.detener()
