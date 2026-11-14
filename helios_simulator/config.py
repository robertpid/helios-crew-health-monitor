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
class PerfilAmbienteMision:
    """
    Parámetros específicos para cada uno de los cuatro hábitats operacionales de misión.
    Sustentado en datos de radiación (RadLab, Curiosity RAD, Chang'e 4 LND) y modelos biomecánicos.
    """

    nombre_descriptivo: str
    gravedad_g: float
    radiacion_diaria_base_msv: float
    radiacion_desviacion_msv: float
    probabilidad_tormenta_solar: float
    presion_cabina_nominal_kpa: float
    presion_cabina_min_kpa: float
    presion_cabina_max_kpa: float
    temperatura_cabina_nominal_c: float
    latencia_comunicacion_tierra_segundos: float
    duracion_ciclo_horas: float
    prevalencia_sans_factor: float
    factor_estres_aislamiento: float


def obtener_perfiles_ambientes() -> dict[str, PerfilAmbienteMision]:
    """
    Devuelve los perfiles de configuración aeroespacial para los 4 entornos analizados.

    Returns:
        Diccionario con las configuraciones de Estación Espacial, Base Lunar, Nave Espacial y Base de Marte.
    """
    return {
        "estacion_espacial": PerfilAmbienteMision(
            nombre_descriptivo="Estación Espacial Internacional (ISS / LEO)",
            gravedad_g=0.0,
            radiacion_diaria_base_msv=0.35,  # 0.2 a 0.5 mSv/día (Simonsen et al., 2025)
            radiacion_desviacion_msv=0.06,
            probabilidad_tormenta_solar=0.005,  # Protegida parcialmente por magnetosfera
            presion_cabina_nominal_kpa=101.3,
            presion_cabina_min_kpa=95.0,
            presion_cabina_max_kpa=103.0,
            temperatura_cabina_nominal_c=21.5,
            latencia_comunicacion_tierra_segundos=0.5,
            duracion_ciclo_horas=24.0,
            prevalencia_sans_factor=1.0,  # 81% prevalencia máxima (LSAH)
            factor_estres_aislamiento=1.0,
        ),
        "base_lunar": PerfilAmbienteMision(
            nombre_descriptivo="Base Lunar (Artemis Base Camp - Superficie Lunar)",
            gravedad_g=0.166,  # 1/6 g
            radiacion_diaria_base_msv=1.35,  # ~60 uSv/h medido por Chang'e 4 LND
            radiacion_desviacion_msv=0.15,
            probabilidad_tormenta_solar=0.020,  # Sin magnetosfera protectora
            presion_cabina_nominal_kpa=70.3,   # Atmósfera de exploración NASA
            presion_cabina_min_kpa=65.0,
            presion_cabina_max_kpa=75.0,
            temperatura_cabina_nominal_c=22.0,
            latencia_comunicacion_tierra_segundos=1.3,  # ~1.3s ida a la Luna
            duracion_ciclo_horas=24.0,
            prevalencia_sans_factor=0.70,  # Gravedad parcial alivia congestión cefálica
            factor_estres_aislamiento=1.2,
        ),
        "nave_espacial": PerfilAmbienteMision(
            nombre_descriptivo="Nave Espacial de Tránsito (Deep Space Transit a Marte)",
            gravedad_g=0.0,  # Microgravedad estricta
            radiacion_diaria_base_msv=1.80,  # Medición Curiosity RAD camino a Marte (Hassler et al., 2013)
            radiacion_desviacion_msv=0.20,
            probabilidad_tormenta_solar=0.025,  # Fuera de la magnetosfera terrestre
            presion_cabina_nominal_kpa=101.3,
            presion_cabina_min_kpa=95.0,
            presion_cabina_max_kpa=103.0,
            temperatura_cabina_nominal_c=20.8,
            latencia_comunicacion_tierra_segundos=900.0,  # 15 minutos en tránsito medio
            duracion_ciclo_horas=24.0,
            prevalencia_sans_factor=1.0,  # 81% prevalencia máxima (LSAH)
            factor_estres_aislamiento=1.6,  # Confinamiento severo en espacio profundo
        ),
        "base_marte": PerfilAmbienteMision(
            nombre_descriptivo="Base de Superficie de Marte (Hábitat Marciano)",
            gravedad_g=0.38,  # 3/8 g
            radiacion_diaria_base_msv=0.67,  # Medición Curiosity RAD en superficie (Hassler et al., 2013)
            radiacion_desviacion_msv=0.08,
            probabilidad_tormenta_solar=0.015,
            presion_cabina_nominal_kpa=101.3,
            presion_cabina_min_kpa=95.0,
            presion_cabina_max_kpa=103.0,
            temperatura_cabina_nominal_c=21.0,
            latencia_comunicacion_tierra_segundos=1200.0,  # 20+ minutos de retraso (Peligro D)
            duracion_ciclo_horas=24.65,  # Sol marciano: 24h 39min (desincronización circadiana)
            prevalencia_sans_factor=0.55,  # Gravedad marciana reduce gradiente de fluidos
            factor_estres_aislamiento=1.4,
        ),
    }


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
