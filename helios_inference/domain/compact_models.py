"""
Registro de telemetría compacto de H.E.L.I.O.S. (formato de persistencia y enlace).

Este es el formato que se GUARDA y se TRANSMITE. Transporta exclusivamente
códigos estables y valores numéricos; todo el texto descriptivo se reconstruye
en el cliente a partir del libro de códigos (`telemetry_codebook.py`), que se
descarga una única vez por sesión.

Las claves son deliberadamente cortas: a 0.5 Hz durante 120 días cada byte de
nombre de campo se repite 5.184.000 veces.
"""

from pydantic import BaseModel, ConfigDict, Field

from helios_inference.domain.telemetry_codebook import VERSION_ESQUEMA


class RegistroTelemetriaCompacto(BaseModel):
    """Un ciclo de inferencia expresado en códigos y números."""

    model_config = ConfigDict(frozen=True)

    v: int = Field(default=VERSION_ESQUEMA, description="Versión del esquema de códigos.")
    ts: int = Field(..., description="Marca de tiempo UTC en segundos desde época Unix.")
    mis: str = Field(..., description="Identificador de misión.")
    ast: str = Field(..., description="Identificador de astronauta.")
    dia: int = Field(..., description="Día operacional de misión.")

    # Vectores de decisión de los Cerebros 1 y 2 (banderas 0/1)
    amb: list[int] = Field(..., description="Vector ambiental R^3 [co2, radiacion, presion].")
    bio: list[int] = Field(..., description="Vector biométrico R^4 [pulso, sueno, osea, sans].")
    sol: int = Field(default=0, description="Evento solar activo (selecciona plantilla de radiación).")

    # Métricas crudas en el orden canónico de ORDEN_METRICAS
    met: list[float] = Field(..., description="Valores numéricos posicionales según orden_metricas.")

    # Cerebro 3: arista dominante del grafo de Kronecker
    kr: int = Field(..., description="Índice argmax de la arista crítica (-1 = nominal).")
    krs: float = Field(..., description="Puntaje de severidad ponderado de la arista.")
    krx: int = Field(default=0, description="Estrés fisiológico severo (supera el umbral).")

    # Cerebro 4: ASTRA
    cos: float = Field(..., description="Similitud coseno respecto a la línea base cognitiva.")
    inc: int = Field(default=0, description="Incongruencia cognitiva detectada.")

    # Matriz de decisiones: códigos de regla. Sufijo '!' indica escalada de nivel.
    rg: list[str] = Field(default_factory=list, description="Códigos de regla activos (ej. 'CX-03!').")

    ms: float = Field(..., description="Tiempo de cómputo del ciclo en milisegundos.")
