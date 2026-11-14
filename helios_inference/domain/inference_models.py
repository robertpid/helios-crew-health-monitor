"""
Modelos de datos para el motor de inferencia H.E.L.I.O.S.

Estructuras tipadas con Pydantic v2 para representar los estados vectoriales de los 4 cerebros,
el resultado de la fusión topológica y las evaluaciones preliminares operacionales.
"""

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

from helios_inference.domain.decision_rules import AlertaReglaMatriz


class EstadoAmbientalInferencia(BaseModel):
    """Resultado del procesamiento del Cerebro 1 (Motor Ambiental)."""

    model_config = ConfigDict(frozen=True)

    vector_ambiental: list[float] = Field(
        ...,
        description="Vector de estado ambiental [alerta_co2, alerta_radiacion, alerta_presion]."
    )
    etiquetas_activadas: list[str] = Field(
        default_factory=list,
        description="Etiquetas operacionales de peligros ambientales activos."
    )
    co2_excedido: bool = Field(..., description="Indica si el CO2 supera el límite normativo de 3.0 mmHg.")
    radiacion_critica: bool = Field(..., description="Indica si la radiación supera 600 mSv o hay evento solar.")
    presion_anomala: bool = Field(..., description="Indica si la presión de cabina está fuera del rango 95-103 kPa.")


class EstadoBiometricoInferencia(BaseModel):
    """Resultado del procesamiento del Cerebro 2 (Motor Biométrico)."""

    model_config = ConfigDict(frozen=True)

    vector_biometrico: list[float] = Field(
        ...,
        description="Vector de estado fisiológico [alerta_pulso, alerta_sueno, alerta_osea, alerta_sans]."
    )
    etiquetas_activadas: list[str] = Field(
        default_factory=list,
        description="Etiquetas de anomalías fisiológicas detectadas."
    )
    metricas_fisicas_normales: bool = Field(
        ...,
        description="Indica si todos los signos físicos se encuentran dentro de los límites nominales."
    )
    cuerpo_en_panico: bool = Field(
        ...,
        description="Indica taquicardia o estrés fisiológico agudo (ej. ritmo cardíaco > 95 bpm)."
    )


class EstadoFusionKroneckerInferencia(BaseModel):
    """Resultado de la fusión matricial del Cerebro 3 (Grafo de Decisiones)."""

    model_config = ConfigDict(frozen=True)

    vector_kronecker_dimension: int = Field(
        ...,
        description="Dimensión del vector tensorial resultante (ej. 12 para 3 ambientales x 4 biométricos)."
    )
    arista_sinergica_critica: str = Field(
        ...,
        description="Descripción de la interacción o arista del grafo con mayor ponderación activada."
    )
    indice_argmax: int = Field(
        ...,
        description="Índice del componente de máxima severidad sinérgica en el espacio vectorial tensorial."
    )
    puntaje_severidad_maximo: float = Field(
        ...,
        description="Puntuación ponderada calculada para la arista crítica activa."
    )
    estres_fisiologico_severo: bool = Field(
        ...,
        description="Bandera de peligro levantada si la interacción sinérgica supera el umbral crítico."
    )
    evaluacion_preliminar_fusion: str | None = Field(
        default=None,
        description="Dictamen de evaluación preliminar sobre el acoplamiento ambiente-tripulante."
    )


class EstadoAstraInferencia(BaseModel):
    """Resultado del procesamiento del Cerebro 4 (Subsistema ASTRA - Psicología y Cognición)."""

    model_config = ConfigDict(frozen=True)

    similitud_coseno_linea_base: float = Field(
        ...,
        description="Coeficiente de similitud coseno entre el vector actual y la línea base dinámica."
    )
    incongruencia_cognitiva_detectada: bool = Field(
        ...,
        description="Indica si se detecta discordancia entre estado físico y conducta comunicacional."
    )
    alerta_astra: str | None = Field(
        default=None,
        description="Mensaje formal de evaluación preliminar emitido ante detección de incongruencia."
    )


class ReporteInferenciaConsolidado(BaseModel):
    """Reporte consolidado generado por los 4 Cerebros de H.E.L.I.O.S."""

    model_config = ConfigDict(frozen=True)

    timestamp_inferencia: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Marca de tiempo UTC del ciclo de inferencia."
    )
    id_mision: str = Field(..., description="Identificador de la misión espacial.")
    dia_mision: int = Field(..., description="Día operacional de misión.")
    astronauta_id: str = Field(..., description="Identificador del astronauta analizado.")
    cerebro_1_ambiental: EstadoAmbientalInferencia
    cerebro_2_biometrico: EstadoBiometricoInferencia
    cerebro_3_grafo_fusion: EstadoFusionKroneckerInferencia
    cerebro_4_astra: EstadoAstraInferencia
    evaluaciones_preliminares_activas: list[str] = Field(
        default_factory=list,
        description="Lista de todas las evaluaciones preliminares y alertas emitidas en el ciclo."
    )
    alertas_matriz_decisiones: list[AlertaReglaMatriz] = Field(
        default_factory=list,
        description="Cruces críticos activos de la matriz de decisiones de la NASA con contramedidas."
    )
    contramedidas_priorizadas: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Hasta 3 acciones inmediatas consolidadas de mayor impacto para el dashboard."
    )
    tiempo_computo_ms: float = Field(
        ...,
        description="Tiempo de ejecución del ciclo completo de inferencia en milisegundos."
    )
    metadatos_edge: dict[str, Any] = Field(
        default_factory=dict,
        description="Detalles de ejecución del runtime ligero de Edge AI."
    )
