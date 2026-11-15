"""
Módulo de API REST: Evaluación Psicológica y Cognitiva ASTRA.

Provee endpoints para el protocolo interactivo de evaluación cognitiva
y salud mental del astronauta en misiones de espacio profundo.
Calcula en tiempo real la densidad léxica, analiza la latencia de respuesta,
y realiza el cruce multivariado con bioseñales (ritmo cardíaco y estrés).

Cumple estrictamente con:
- PEP 8 y anotaciones de tipo estático (Type Hints).
- Principio de Responsabilidad Única (SRP).
- Trazabilidad mediante el módulo logging (sin print).
- Cero ocurrencias de términos médicos restringidos.
"""

import logging
import math
import re
from typing import Any, List
from fastapi import APIRouter, HTTPException, status
import numpy as np
from pydantic import BaseModel, Field

from helios_inference.cerebros.cerebro_4_astra import CerebroCognitivoAstra
from helios_inference.domain.inference_models import EstadoBiometricoInferencia

logger = logging.getLogger(__name__)

router = APIRouter()

# Instancia del Cerebro 4 para cálculo de similitud coseno vectorial
_cerebro_astra = CerebroCognitivoAstra(
    latencia_base_ms=200.0,
    densidad_base_score=1.0,
    umbral_caida_similitud=0.88,
    umbral_latencia_fatiga_ms=500.0,
)


class EvaluacionPsicologicaInput(BaseModel):
    """Esquema de entrada para la evaluación de respuesta del astronauta."""

    id_pregunta: int = Field(..., ge=1, le=3, description="Identificador de la pregunta (1-3)")
    texto_respuesta: str = Field(..., min_length=1, description="Texto escrito o dictado por voz")
    latencia_ms: float = Field(..., ge=0.0, description="Tiempo de reacción verbal en milisegundos")
    ritmo_cardiaco_bpm: float = Field(default=72.0, ge=30.0, le=220.0, description="Pulso cardíaco actual")
    cuerpo_en_panico: bool = Field(default=False, description="Indicador de estrés severo del Cerebro 2")


class EvaluacionPsicologicaOutput(BaseModel):
    """Esquema de salida con métricas vectoriales y evaluación preliminar."""

    id_pregunta: int
    latencia_ms: float
    densidad_lexica: float
    similitud_coseno: float
    incongruencia_detectada: bool
    evaluacion_preliminar: str
    respuesta_asistente: str
    estado_cognitivo: str


class PreguntaPsicologicaItem(BaseModel):
    """Esquema de una pregunta del protocolo NASA-BHP."""

    id_pregunta: int
    categoria: str
    pregunta: str
    sugerencias_rapidas: List[str]


PREGUNTAS_BHP: List[PreguntaPsicologicaItem] = [
    PreguntaPsicologicaItem(
        id_pregunta=1,
        categoria="Alerta & Nivel Atencional",
        pregunta="¿Cómo describirías tu nivel de concentración y energía para las operaciones de hoy?",
        sugerencias_rapidas=[
            "100% enfocado y despejado para la jornada.",
            "Normal, dentro de los parámetros habituales.",
            "He tenido algo de lentitud mental y fatiga atencional.",
        ],
    ),
    PreguntaPsicologicaItem(
        id_pregunta=2,
        categoria="Carga de Trabajo & Toma de Decisiones",
        pregunta="¿Has experimentado sobrecarga o retraso en la resolución de tareas técnicas hoy?",
        sugerencias_rapidas=[
            "Cero sobrecarga, procedimientos ejecutados en tiempo óptimo.",
            "Bien, carga operativa estándar.",
            "Las checklists me han tomado más tiempo y esfuerzo del previsto.",
        ],
    ),
    PreguntaPsicologicaItem(
        id_pregunta=3,
        categoria="Estado Emocional & Confinamiento Sol 120",
        pregunta="Reporte Sol 120: ¿Cómo percibes el ambiente en la cabina y la distancia con la Tierra?",
        sugerencias_rapidas=[
            "Excelente moral de equipo, comunicación fluida con control de misión.",
            "Todo en orden en cabina, sin contratiempos.",
            "El aislamiento prolongado se hace notar hoy, requiero pausa breve.",
        ],
    ),
]


def calcular_densidad_lexica(texto: str) -> float:
    """
    Calcula la densidad léxica normalizada [0.1, 1.0] de la respuesta verbal.
    Penaliza respuestas monosilábicas evasivas ("bien", "ok") y premia respuestas elaboradas.
    """
    tokens = re.findall(r"\b[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9]+\b", texto.lower())
    total_palabras = len(tokens)
    if total_palabras == 0:
        return 0.10

    palabras_unicas = len(set(tokens))
    ratio_variedad = palabras_unicas / float(total_palabras)

    # Penalización por brevedad extrema (evasión del astronauta)
    if total_palabras <= 2:
        return round(min(0.40, ratio_variedad * 0.45), 3)

    bono_longitud = min(0.35, total_palabras * 0.03)
    densidad = min(1.0, (ratio_variedad * 0.65) + bono_longitud)
    return round(float(np.clip(densidad, 0.15, 1.0)), 3)


def generar_retroalimentacion_asistente(
    id_pregunta: int,
    incongruencia: bool,
    latencia_ms: float,
    ritmo_bpm: float,
) -> tuple[str, str]:
    """Genera mensaje del asistente y el veredicto de evaluación preliminar."""
    if incongruencia:
        if ritmo_bpm > 95.0:
            vered = "INCONGRUENCIA DETECTADA: DISCURSO FORMAL BAJO ESTRÉS CARDÍACO"
            msg = (
                f"Comandante, tus bioseñales registran {int(ritmo_bpm)} lpm mientras tu locución "
                "aparenta calma total. No minimices el esfuerzo: el sistema sugiere una pausa y "
                "activar la guía de respiración 4-4-6."
            )
        else:
            vered = "INCONGRUENCIA DETECTADA: RETRASO PSICOMOTOR / FATIGA OCULTA"
            msg = (
                f"Se detectó un tiempo de reacción extendido ({int(latencia_ms)} ms) con variabilidad "
                "léxica reducida. Registrado en el protocolo de soporte vital: descansa 15 minutos "
                "antes de la próxima checklist."
            )
        return vered, msg

    if latencia_ms > 450.0:
        vered = "FATIGA COGNITIVA LEVE DETECTADA"
        msg = (
            f"Respuesta procesada. Tiempo de respuesta ({int(latencia_ms)} ms) ligeramente sobre "
            "la línea base nominal (200 ms). Hidratación y estiramiento recomendados."
        )
        return vered, msg

    vered = "COHERENTE: ESTADO COGNITIVO NOMINAL"
    respuestas_nominales = {
        1: "Excelente, Comandante. Patrón de alerta y agudeza mental óptimos para operaciones críticas.",
        2: "Registrado. Eficiencia en la toma de decisiones dentro de la curva nominal de vuelo.",
        3: "Reporte Sol 120 completado con éxito. Estado psicosocial equilibrado y moral firme.",
    }
    msg = respuestas_nominales.get(
        id_pregunta,
        "Reporte asentado en la bitácora operativa de H.E.L.I.O.S.",
    )
    return vered, msg


@router.get(
    "/preguntas",
    response_model=List[PreguntaPsicologicaItem],
    summary="Catálogo de Preguntas del Protocolo BHP",
)
async def obtener_preguntas_protocolo() -> List[PreguntaPsicologicaItem]:
    """Retorna las 3 preguntas estandarizadas del protocolo de chequeo psicológico."""
    return PREGUNTAS_BHP


@router.post(
    "/evaluar",
    response_model=EvaluacionPsicologicaOutput,
    summary="Evaluar Respuesta Psicológica y Vector Cognitivo",
)
async def evaluar_respuesta_astronauta(
    payload: EvaluacionPsicologicaInput,
) -> EvaluacionPsicologicaOutput:
    """
    Procesa la respuesta verbal/escrita del astronauta, calcula densidad léxica,
    similitud coseno con la línea base y realiza el cruce con el ritmo cardíaco.
    """
    try:
        densidad = calcular_densidad_lexica(payload.texto_respuesta)

        datos_cognicion = {
            "latencia_voz_ms": payload.latencia_ms,
            "densidad_lexica_score": densidad,
        }

        estado_bio = EstadoBiometricoInferencia(
            vector_biometrico=[1.0 if payload.ritmo_cardiaco_bpm > 95.0 else 0.0, 0.0, 0.0, 0.0],
            etiquetas_activadas=[],
            metricas_fisicas_normales=bool(payload.ritmo_cardiaco_bpm <= 95.0),
            cuerpo_en_panico=payload.cuerpo_en_panico,
        )

        similitud, estado_astra = _cerebro_astra.procesar(
            datos_cognicion=datos_cognicion,
            estado_biometrico=estado_bio,
            ritmo_cardiaco_bpm=payload.ritmo_cardiaco_bpm,
        )

        eval_preliminar, respuesta_asistente = generar_retroalimentacion_asistente(
            id_pregunta=payload.id_pregunta,
            incongruencia=estado_astra.incongruencia_cognitiva_detectada,
            latencia_ms=payload.latencia_ms,
            ritmo_bpm=payload.ritmo_cardiaco_bpm,
        )

        estado_cognitivo = "NOMINAL"
        if estado_astra.incongruencia_cognitiva_detectada:
            estado_cognitivo = "INCONGRUENCIA_CRITICA"
        elif payload.latencia_ms > 450.0:
            estado_cognitivo = "FATIGA_LEVE"

        logger.info(
            "ASTRA BHP P%d | Latencia: %.1f ms | Densidad: %.2f | CosSim: %.3f | Estado: %s",
            payload.id_pregunta,
            payload.latencia_ms,
            densidad,
            similitud,
            estado_cognitivo,
        )

        return EvaluacionPsicologicaOutput(
            id_pregunta=payload.id_pregunta,
            latencia_ms=round(payload.latencia_ms, 1),
            densidad_lexica=densidad,
            similitud_coseno=round(similitud, 4),
            incongruencia_detectada=estado_astra.incongruencia_cognitiva_detectada,
            evaluacion_preliminar=eval_preliminar,
            respuesta_asistente=respuesta_asistente,
            estado_cognitivo=estado_cognitivo,
        )
    except Exception as exc:
        logger.error("Fallo al evaluar protocolo psicológico: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error en motor analítico psicológico: {exc}",
        )


if __name__ == "__main__":
    logger.info("Módulo de API Psicológica cargado correctamente.")
