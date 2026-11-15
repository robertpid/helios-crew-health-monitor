"""
Módulo de API REST: Evaluación Psicológica y Cognitiva ASTRA (NASA-BHP).

Evalúa la tasa de articulación vocal (Palabras Por Minuto - WPM), cadencia silábica,
densidad léxica y cruce fisiológico multivariado con bioseñales (ritmo cardíaco y estrés).

Cumple estrictamente con:
- PEP 8 y anotaciones de tipo estático (Type Hints).
- Principio de Responsabilidad Única (SRP).
- Trazabilidad mediante el módulo logging (sin print).
- Cero ocurrencias de términos médicos restringidos.
- Línea máxima <= 400 líneas.
"""

import logging
import re
from typing import Any, List
from fastapi import APIRouter, HTTPException, status
import numpy as np
from pydantic import BaseModel, Field

from helios_inference.cerebros.cerebro_4_astra import CerebroCognitivoAstra
from helios_inference.domain.inference_models import EstadoBiometricoInferencia

logger = logging.getLogger(__name__)

router = APIRouter()

_cerebro_astra = CerebroCognitivoAstra(
    latencia_base_ms=200.0,
    densidad_base_score=1.0,
    umbral_caida_similitud=0.88,
    umbral_latencia_fatiga_ms=500.0,
)


class EvaluacionPsicologicaInput(BaseModel):
    """Esquema de entrada para la evaluación de respuesta y habla del astronauta."""

    id_pregunta: int = Field(..., ge=1, le=3, description="Identificador de la pregunta (1-3)")
    texto_respuesta: str = Field(..., min_length=1, description="Texto escrito o dictado por voz")
    latencia_ms: float = Field(default=2000.0, ge=0.0, description="Duración de interacción en ms")
    palabras_por_minuto: float = Field(default=135.0, ge=10.0, le=400.0, description="Velocidad vocal (WPM)")
    ritmo_cardiaco_bpm: float = Field(default=72.0, ge=30.0, le=220.0, description="Pulso cardíaco actual")
    cuerpo_en_panico: bool = Field(default=False, description="Indicador de estrés severo del Cerebro 2")


class EvaluacionPsicologicaOutput(BaseModel):
    """Esquema de salida con métricas de articulación y evaluación preliminar."""

    id_pregunta: int
    palabras_por_minuto: float
    cadencia_ms_palabra: float
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
            "He sentido lentitud mental y fatiga atencional hoy.",
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
            "Excelente moral de equipo, comunicación fluida con Houston.",
            "Bien, aquí estamos relajados y en orden.",
            "El aislamiento prolongado se hace notar hoy, requiero pausa breve.",
        ],
    ),
]


def calcular_densidad_y_tipo(texto: str) -> tuple[float, str]:
    """Analiza la riqueza léxica y clasifica el tenor de la respuesta."""
    tokens = re.findall(r"\b[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9]+\b", texto.lower())
    total = len(tokens)
    if total == 0:
        return 0.20, "vacio"

    palabras_fatiga = {
        "sueno", "sueño", "cansado", "cansancio", "fatiga", "lento", "lentitud",
        "pesado", "aislamiento", "retraso", "sobrecarga", "estres", "estrés",
        "agobiado", "dificultad", "tiempo", "esfuerzo"
    }
    palabras_positivas = {
        "bien", "normal", "orden", "control", "enfocado", "despejado",
        "optimo", "óptimo", "excelente", "estable", "fluida", "calma",
        "tranquilo", "tranquilos", "cero", "firme", "sin", "problemas",
        "habituales", "relajados", "relajado", "paz"
    }

    tiene_fatiga = any(tok in palabras_fatiga for tok in tokens)
    tiene_positivas = any(tok in palabras_positivas for tok in tokens)

    if tiene_fatiga:
        tipo = "fatiga_declarada"
        densidad = 0.75 + min(0.15, total * 0.02)
    elif tiene_positivas:
        tipo = "nominal_conciso"
        densidad = 0.92
    else:
        tipo = "elaborada"
        unicas = len(set(tokens))
        ratio = unicas / float(total)
        densidad = float(np.clip((ratio * 0.65) + min(0.35, total * 0.03), 0.35, 1.0))

    return round(densidad, 3), tipo


def generar_retroalimentacion_asistente(
    id_pregunta: int,
    tipo_respuesta: str,
    incongruencia: bool,
    wpm: float,
    ritmo_bpm: float,
) -> tuple[str, str, str]:
    """Genera mensaje del asistente, veredicto y categoría sin revelar métricas al tripulante."""
    # 1. Incongruencia: activación fisiológica con palabras de calma fingida
    if incongruencia and ritmo_bpm > 95.0:
        vered = "INCONGRUENCIA DETECTADA: DISCURSO EN CALMA BAJO ACTIVACIÓN FISIOLÓGICA"
        msg = (
            "Comandante, los registros fisiológicos de cabina reflejan activación de estrés durante "
            "tu reporte. Te recomendamos realizar una breve pausa activa y la guía de respiración 4-4-6."
        )
        return vered, msg, "INCONGRUENCIA_CRITICA"

    # 2. Bradilalia / lentitud psicomotora (< 85 WPM)
    if wpm < 85.0:
        vered = "FATIGA OPERACIONAL POR BRADILALIA (CADENCIA LENTA)"
        msg = (
            "Comandante, registramos signos de fatiga y desgaste atencional acumulado en este reporte. "
            "Se sugiere hidratación de cabina y un receso preventivo de 15 minutos."
        )
        return vered, msg, "FATIGA_LEVE"

    # 3. Fatiga declarada honestamente por el tripulante
    if tipo_respuesta == "fatiga_declarada":
        vered = "FATIGA OPERACIONAL REPORTADA (HONESTIDAD OPERACIONAL)"
        mensajes_fatiga = {
            1: "Fatiga y nivel de energía asentados en la bitácora operacional. Hidrátate con 500 ml y ajusta la iluminación de cabina.",
            2: "Sobrecarga en checklists registrada en la bitácora. El sistema ASTRA reorganiza tareas secundarias de la misión.",
            3: "Reporte de bienestar del Sol 120 asentado. Procedimiento de apoyo de cabina activado.",
        }
        msg = mensajes_fatiga.get(id_pregunta, "Reporte de fatiga asentado en la bitácora operacional.")
        return vered, msg, "FATIGA_LEVE"

    # 4. Estado Nominal / Coherente (incluye "relajados", "bien", "óptimo")
    vered = "COHERENTE: ESTADO OPERACIONAL NOMINAL"
    mensajes_nominales = {
        1: "Recibido, Comandante. Comunicación clara y estado óptimo para las operaciones de vuelo.",
        2: "Excelente. Respuestas registradas dentro de los márgenes nominales esperados de la misión.",
        3: "Reporte Sol 120 asentado con éxito. Estado equilibrado y moral firme de la tripulación.",
    }
    msg = mensajes_nominales.get(
        id_pregunta,
        "Reporte asentado con éxito en la bitácora de misión. Parámetros estables.",
    )
    return vered, msg, "NOMINAL"


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
    summary="Evaluar Respuesta Psicológica y Cadencia Vocal",
)
async def evaluar_respuesta_astronauta(
    payload: EvaluacionPsicologicaInput,
) -> EvaluacionPsicologicaOutput:
    """
    Evalúa la tasa de articulación (WPM), cadencia, riqueza léxica y cruce fisiológico.
    """
    try:
        densidad, tipo_resp = calcular_densidad_y_tipo(payload.texto_respuesta)
        wpm = float(np.clip(payload.palabras_por_minuto, 40.0, 280.0))
        cadencia_ms = round(60000.0 / wpm, 1)

        # Mapeo a vector cognitivo ASTRA normalizado
        ratio_wpm = wpm / 135.0  # 135 WPM es la línea base nominal
        latencia_equiv_ms = 200.0 / ratio_wpm

        datos_cognicion = {
            "latencia_voz_ms": latencia_equiv_ms,
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

        incongruencia = bool(
            (payload.ritmo_cardiaco_bpm > 95.0 and tipo_resp in ["nominal_conciso", "elaborada"])
            or wpm < 85.0
        )

        eval_preliminar, respuesta_asistente, estado_cognitivo = generar_retroalimentacion_asistente(
            id_pregunta=payload.id_pregunta,
            tipo_respuesta=tipo_resp,
            incongruencia=incongruencia,
            wpm=wpm,
            ritmo_bpm=payload.ritmo_cardiaco_bpm,
        )

        logger.info(
            "ASTRA BHP P%d | %s | WPM: %.0f (%.0f ms/pal) | Densidad: %.2f | CosSim: %.3f | %s",
            payload.id_pregunta,
            tipo_resp,
            wpm,
            cadencia_ms,
            densidad,
            similitud,
            estado_cognitivo,
        )

        return EvaluacionPsicologicaOutput(
            id_pregunta=payload.id_pregunta,
            palabras_por_minuto=round(wpm, 1),
            cadencia_ms_palabra=cadencia_ms,
            densidad_lexica=densidad,
            similitud_coseno=round(similitud, 4),
            incongruencia_detectada=incongruencia,
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
