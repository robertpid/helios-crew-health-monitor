"""
Configuración centralizada para el simulador HELIOS.

Define constantes operativas, rangos de referencia aeroespacial y parámetros de conexión
conforme a NASA-STD-3001 y las especificaciones de misión de espacio profundo.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RedisConfig:
    """Parámetros de configuración de conexión a la infraestructura de mensajería Redis."""

    host: str = "127.0.0.1"
    port: int = 6379
    db: int = 0
    password: str | None = None
    canal_publicacion: str = "buzon_telemetria_tierra"
    cola_publicacion: str = "buzon_telemetria_tierra_queue"
    tiempo_espera_conexion_segundos: float = 2.0
    intervalo_reintento_reconexion_segundos: float = 3.0
    limite_cola_buffer_memoria: int = 500


@dataclass(frozen=True)
class MisionConfig:
    """Parámetros de la misión espacial de referencia."""

    id_mision: str = "ARES-VI-MARS-EXPEDITION"
    astronauta_id: str = "ASTRO-HELIOS-01"
    dia_mision_default: int = 120
    intervalo_emision_segundos: float = 2.0


@dataclass(frozen=True)
class LimitesNasaConfig:
    """Límites y umbrales normativos según NASA-STD-3001 y HSRB."""

    # Entorno (Cerebro 1)
    co2_normal_min_mmhg: float = 1.0
    co2_normal_max_mmhg: float = 2.2
    co2_umbral_sintomas_mmhg: float = 2.3
    co2_limite_7dias_mmhg: float = 2.5
    co2_limite_max_nasa_v2_6004_mmhg: float = 3.0

    presion_cabina_min_kpa: float = 95.0
    presion_cabina_max_kpa: float = 103.0

    radiacion_base_acumulada_msv: float = 50.0
    radiacion_tasa_diaria_min_msv: float = 0.2
    radiacion_tasa_diaria_max_msv: float = 0.5
    radiacion_tormenta_solar_impacto_msv: float = 20.0
    probabilidad_tormenta_solar: float = 0.01
    radiacion_limite_carrera_msv: float = 600.0
    radiacion_limite_evento_solar_msv: float = 250.0

    # Fisiología (Cerebro 2)
    ritmo_cardiaco_base_bpm: float = 65.0
    ritmo_cardiaco_desviacion_bpm: float = 5.0
    horas_sueno_promedio: float = 6.0
    umbral_horas_sueno_riesgo: float = 6.0
    consecutivos_sueno_para_alerta: int = 3
    tasa_perdida_osea_mensual_pct: float = 1.5

    # Cognición / Psicología (Cerebro 4 - ASTRA)
    latencia_voz_base_ms: float = 200.0
    latencia_voz_estres_min_ms: float = 600.0
    latencia_voz_estres_max_ms: float = 900.0
    probabilidad_incongruencia_estres: float = 0.15
    ritmo_cardiaco_umbral_estres_alto_bpm: float = 95.0
    prevalencia_sans_historica_lsah_pct: float = 81.0
