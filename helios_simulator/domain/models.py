"""
Modelos de dominio para telemetría espacial del simulador HELIOS.

Implementa estructuras de datos inmutables y tipadas con Pydantic v2 para garantizar
la integridad del payload enviado a la estación terrestre y nodos de soporte vital.
"""

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

from helios_simulator.domain.enums import NivelAlerta, PeligroRidge


class EntornoModel(BaseModel):
    """
    Cerebro 1: Telemetría ambiental de la cabina y espacio circumambiente.
    Fundamentado en NASA-STD-3001 Vol. 2 y mediciones de radiación del servidor NTRS.
    """

    model_config = ConfigDict(frozen=True)

    co2_mmHg: float = Field(
        ...,
        description="Presión parcial de CO2 en cabina en mmHg. Umbral normativo NASA V2 6004 <= 3.0 mmHg."
    )
    radiacion_acumulada_mSv: float = Field(
        ...,
        description="Dosis acumulada efectiva de radiación en mSv (límite de carrera NASA: 600 mSv)."
    )
    radiacion_tasa_diaria_mSv: float = Field(
        ...,
        description="Tasa de dosis diaria en mSv/día (típico ISS: 0.2 a 0.5 mSv/día)."
    )
    presion_cabina_kpa: float = Field(
        ...,
        description="Presión atmosférica de cabina en kPa. Umbral normativo NASA V2 6006: 95.0 - 103.0 kPa."
    )
    temperatura_cabina_c: float = Field(
        ...,
        description="Temperatura ambiental interna en grados Celsius."
    )
    humedad_relativa_pct: float = Field(
        default=45.0,
        ge=0.0,
        le=100.0,
        description="Sensor de humedad relativa de cabina (NASA OSDR N22: 40-60%)."
    )
    evento_solar_activo: bool = Field(
        default=False,
        description="Indicador de anomalía por Tormenta Solar o Evento de Partículas Solares (SPE)."
    )


class BiometriaModel(BaseModel):
    """
    Cerebro 2: Biometría Fisiológica del astronauta.
    Basado en líneas de base personalizadas (NASA Twins Study) y contramedidas de HSRB.
    """

    model_config = ConfigDict(frozen=True)

    ritmo_cardiaco_bpm: float = Field(
        ...,
        description="Frecuencia cardiaca instantánea en latidos por minuto (LPM)."
    )
    horas_sueno_ultimo_ciclo: float = Field(
        ...,
        description="Horas efectivas de descanso en el último ciclo circadiano."
    )
    ciclos_sueno_insuficiente_consecutivos: int = Field(
        ...,
        ge=0,
        description="Contador de ciclos continuos con sueño inferior al umbral de 6.0 horas."
    )
    alerta_riesgo_fatiga: bool = Field(
        default=False,
        description="Bandera de fatiga acumulada activada tras 3 ciclos sucesivos con déficit de sueño."
    )
    perdida_osea_pct: float = Field(
        ...,
        ge=0.0,
        description="Estimación de pérdida de densidad mineral ósea acumulada según modelo HSRB."
    )
    presion_sistolica_mmHg: float = Field(
        ...,
        description="Presión arterial sistólica en mmHg."
    )
    presion_diastolica_mmHg: float = Field(
        ...,
        description="Presión arterial diastólica en mmHg."
    )
    spo2_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Saturación periférica de oxígeno en sangre."
    )
    temperatura_piel_c: float = Field(
        default=34.8,
        description="Sensor térmico cutáneo del Bio-Monitor Astroskin en grados Celsius."
    )
    frecuencia_respiratoria_rpm: float = Field(
        default=14.0,
        description="Sensor torácico de frecuencia respiratoria en respiraciones por minuto (Bio-Monitor Astroskin)."
    )
    variabilidad_cardiaca_hrv_ms: float = Field(
        default=42.0,
        description="Variabilidad de la frecuencia cardíaca HRV en milisegundos (Frontiers in Physiology 2024 / E13)."
    )
    dolor_cabeza_sintoma: bool = Field(
        default=False,
        description="Registro sintomático de cefalea asociado a elevación de CO2 o desplazamiento de fluidos."
    )
    actividad_fisica_minutos: float = Field(
        default=120.0,
        description="Tiempo diario de ejercicio de resistencia física como contramedida de masa ósea (NASA HSRB)."
    )
    escala_estres_autorreporte: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Autorreporte subjetivo de fatiga y estrés psicofisiológico en escala de 1 a 10."
    )


class CognicionModel(BaseModel):
    """
    Cerebro 4: Psicología y Cognición (Subsistema ASTRA).
    Monitoreo de latencia comunicacional, coherencia y detección de tensión neuro-ocular.
    """

    model_config = ConfigDict(frozen=True)

    latencia_voz_ms: float = Field(
        ...,
        description="Tiempo de respuesta verbal en milisegundos durante comunicaciones de cabina."
    )
    densidad_lexica_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Índice de complejidad y variedad léxica en comunicaciones verbales (0.0 a 1.0)."
    )
    incongruencia_estres_oculto: bool = Field(
        default=False,
        description="Detección de incongruencia psicológica (frecuencia elevada con discurso formalizado)."
    )
    sans_sintoma_vision: bool = Field(
        default=False,
        description="Presencia de sintomatología neuro-ocular SANS bajo estrés y presiones elevadas."
    )


class AlertaEvaluacionPreliminar(BaseModel):
    """
    Estructura formal para evaluaciones preliminares de riesgo y alertas operacionales.
    Cita normativas oficiales NASA-STD-3001 y RIDGE para respaldo de validación técnica.
    """

    model_config = ConfigDict(frozen=True)

    codigo: str = Field(..., description="Identificador único de la alerta normativa.")
    nivel: NivelAlerta = Field(..., description="Severidad de la alerta.")
    peligro_ridge: PeligroRidge = Field(..., description="Categoría de riesgo del marco RIDGE.")
    estandar_referencia: str = Field(..., description="Referencia a estándar oficial NASA.")
    descripcion: str = Field(..., description="Detalle explicativo del evento detectado.")
    cruce_multivariado: bool = Field(
        default=False,
        description="Indica si la alerta es resultado del cruce sinérgico de múltiples factores."
    )


class TelemetriaPayload(BaseModel):
    """
    Payload consolidado inyectado al buzón de telemetría hacia Tierra.
    Representa el estado sistémico del astronauta y su habitáculo en tiempo real.
    """

    model_config = ConfigDict(frozen=True)

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Marca de tiempo en estándar UTC con resolución de microsegundos."
    )
    id_mision: str = Field(..., description="Identificador único de la misión aeroespacial.")
    dia_mision: int = Field(..., ge=1, description="Día transcurrido de la misión (sol).")
    astronauta_id: str = Field(..., description="Identificador del miembro de tripulación.")
    entorno: EntornoModel = Field(..., description="Métricas ambientales (Cerebro 1).")
    biometria: BiometriaModel = Field(..., description="Métricas fisiológicas (Cerebro 2).")
    cognicion: CognicionModel = Field(..., description="Métricas cognitivas y conductuales (Cerebro 4).")
    evaluaciones_preliminares: list[AlertaEvaluacionPreliminar] = Field(
        default_factory=list,
        description="Colección de evaluaciones preliminares y alertas activas en el instante."
    )
    porcentaje_presupuesto_radiacion_carrera: float = Field(
        ...,
        description="Porcentaje consumido del límite de 600 mSv permitido para la carrera del astronauta."
    )
    metadatos_sistema: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadatos operacionales del productor en el borde (Edge AI)."
    )
