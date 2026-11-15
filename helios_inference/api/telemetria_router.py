"""
Router de telemetría compacta de H.E.L.I.O.S.

Expone el formato de enlace reducido y el libro de códigos que lo acompaña:

    GET /api/v1/telemetria/codebook   -> plantillas y catálogo (descarga única)
    GET /api/v1/telemetria/compacto   -> último ciclo en códigos + números
    GET /api/v1/telemetria/ahorro     -> comparativa de caudal medida en vivo

El reporte completo con texto sigue disponible en /api/v1/fusion/resultado para
depuración; este router es el que debe consumir el HUD en operación nominal.
"""

import json
import logging
from typing import Any, Callable

from fastapi import APIRouter, Response

from helios_inference.domain.compact_models import RegistroTelemetriaCompacto
from helios_inference.domain.telemetry_codebook import construir_codebook
from helios_inference.services.telemetry_compactor import compactar

logger = logging.getLogger(__name__)

router = APIRouter()

# El libro de códigos es inmutable en ejecución: se serializa una sola vez y se
# sirve desde memoria con cabecera de caché agresiva.
_CODEBOOK: dict[str, Any] = construir_codebook()
_CODEBOOK_JSON: str = json.dumps(_CODEBOOK, ensure_ascii=False, separators=(",", ":"))

# Inyección tardía: main.py registra aquí cómo obtener el ciclo vigente.
_proveedor_ciclo: Callable[[], tuple[Any, dict[str, Any]] | None] | None = None


def registrar_proveedor_ciclo(
    proveedor: Callable[[], tuple[Any, dict[str, Any]] | None],
) -> None:
    """
    Inyecta la función que entrega (reporte, payload) del último ciclo procesado.

    Args:
        proveedor: Invocable que retorna la tupla vigente o None si no hay telemetría.
    """
    global _proveedor_ciclo
    _proveedor_ciclo = proveedor


@router.get(
    "/codebook",
    summary="Libro de Códigos de Telemetría (descarga única)",
)
async def obtener_codebook() -> Response:
    """Retorna las plantillas de texto y el catálogo de reglas que traduce el HUD."""
    return Response(
        content=_CODEBOOK_JSON,
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=86400, immutable"},
    )


@router.get(
    "/compacto",
    response_model=RegistroTelemetriaCompacto,
    summary="Último Ciclo en Formato Compacto (códigos + valores)",
)
async def obtener_ciclo_compacto() -> RegistroTelemetriaCompacto:
    """Retorna el ciclo vigente reducido a códigos estables y métricas numéricas."""
    ciclo = _proveedor_ciclo() if _proveedor_ciclo else None
    if ciclo is None:
        raise _sin_telemetria()
    reporte, payload = ciclo
    return compactar(reporte, payload)


@router.get(
    "/ahorro",
    summary="Comparativa de Caudal: Reporte Completo vs Registro Compacto",
)
async def medir_ahorro(cadencia_hz: float = 0.5, dias: int = 120) -> dict[str, Any]:
    """
    Mide en vivo la reducción de volumen sobre el ciclo actual.

    Args:
        cadencia_hz: Frecuencia de emisión de telemetría.
        dias: Horizonte de misión para el acumulado.

    Returns:
        Tamaños por ciclo, por día y por misión en ambos formatos.
    """
    ciclo = _proveedor_ciclo() if _proveedor_ciclo else None
    if ciclo is None:
        raise _sin_telemetria()
    reporte, payload = ciclo

    bytes_completo = len(reporte.model_dump_json().encode("utf-8"))
    compacto = compactar(reporte, payload)
    bytes_compacto = len(
        compacto.model_dump_json().encode("utf-8")
    )

    ciclos_dia = cadencia_hz * 86400.0
    return {
        "cadencia_hz": cadencia_hz,
        "por_ciclo": {
            "completo_bytes": bytes_completo,
            "compacto_bytes": bytes_compacto,
            "reduccion_pct": round((1 - bytes_compacto / bytes_completo) * 100, 2),
            "factor": round(bytes_completo / bytes_compacto, 2),
        },
        "por_dia_mb": {
            "completo": round(bytes_completo * ciclos_dia / 1e6, 2),
            "compacto": round(bytes_compacto * ciclos_dia / 1e6, 2),
        },
        f"mision_{dias}_dias_gb": {
            "completo": round(bytes_completo * ciclos_dia * dias / 1e9, 3),
            "compacto": round(bytes_compacto * ciclos_dia * dias / 1e9, 3),
        },
        "codebook_bytes_descarga_unica": len(_CODEBOOK_JSON.encode("utf-8")),
    }


def _sin_telemetria() -> Exception:
    """Construye el error uniforme de ausencia de telemetría en la cola."""
    from fastapi import HTTPException, status

    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Sin telemetrías registradas en la cola.",
    )
