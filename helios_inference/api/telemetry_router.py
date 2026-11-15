"""
H.E.L.I.O.S. compact telemetry router.

Exposes the reduced link format and the codebook that accompanies it:

    GET /api/v1/telemetry/codebook   -> templates and catalog (single download)
    GET /api/v1/telemetry/compact    -> latest cycle in codes + numbers
    GET /api/v1/telemetry/savings    -> live-measured bandwidth comparison

The full report with text remains available at /api/v1/fusion/result for
debugging; this router is the one the HUD should consume in nominal operation.
"""

import json
import logging
from typing import Any, Callable

from fastapi import APIRouter, Response

from helios_inference.domain.compact_models import CompactTelemetryRecord
from helios_inference.domain.telemetry_codebook import build_codebook
from helios_inference.services.telemetry_compactor import compact_record

logger = logging.getLogger(__name__)

router = APIRouter()

# The codebook is immutable at runtime: it is serialized once and served from
# memory with an aggressive cache header.
_CODEBOOK: dict[str, Any] = build_codebook()
_CODEBOOK_JSON: str = json.dumps(_CODEBOOK, ensure_ascii=False, separators=(",", ":"))

# Late injection: main.py registers here how to obtain the current cycle.
_cycle_provider: Callable[[], tuple[Any, dict[str, Any]] | None] | None = None


def register_cycle_provider(
    provider: Callable[[], tuple[Any, dict[str, Any]] | None],
) -> None:
    """
    Injects the function that delivers (report, payload) of the last processed cycle.

    Args:
        provider: Callable returning the current tuple or None if there is no telemetry.
    """
    global _cycle_provider
    _cycle_provider = provider


@router.get(
    "/codebook",
    summary="Telemetry Codebook (single download)",
)
async def get_codebook() -> Response:
    """Returns the text templates and the rule catalog that the HUD translates."""
    return Response(
        content=_CODEBOOK_JSON,
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=86400, immutable"},
    )


@router.get(
    "/compact",
    response_model=CompactTelemetryRecord,
    summary="Latest Cycle in Compact Format (codes + values)",
)
async def get_compact_cycle() -> CompactTelemetryRecord:
    """Returns the current cycle reduced to stable codes and numeric metrics."""
    cycle = _cycle_provider() if _cycle_provider else None
    if cycle is None:
        raise _without_telemetry()
    report, payload = cycle
    return compact_record(report, payload)


@router.get(
    "/savings",
    summary="Bandwidth Comparison: Full Report vs Compact Record",
)
async def measure_savings(cadence_hz: float = 0.5, days: int = 120) -> dict[str, Any]:
    """
    Measures the volume reduction over the current cycle in real time.

    Args:
        cadence_hz: Telemetry emission frequency.
        days: Mission horizon for the cumulative total.

    Returns:
        Sizes per cycle, per day and per mission in both formats.
    """
    cycle = _cycle_provider() if _cycle_provider else None
    if cycle is None:
        raise _without_telemetry()
    report, payload = cycle

    full_bytes = len(report.model_dump_json().encode("utf-8"))
    compact = compact_record(report, payload)
    compact_bytes = len(
        compact.model_dump_json().encode("utf-8")
    )

    cycles_per_day = cadence_hz * 86400.0
    return {
        "cadence_hz": cadence_hz,
        "per_cycle": {
            "full_bytes": full_bytes,
            "compact_bytes": compact_bytes,
            "reduction_pct": round((1 - compact_bytes / full_bytes) * 100, 2),
            "factor": round(full_bytes / compact_bytes, 2),
        },
        "per_day_mb": {
            "full": round(full_bytes * cycles_per_day / 1e6, 2),
            "compact": round(compact_bytes * cycles_per_day / 1e6, 2),
        },
        f"mission_{days}_days_gb": {
            "full": round(full_bytes * cycles_per_day * days / 1e9, 3),
            "compact": round(compact_bytes * cycles_per_day * days / 1e9, 3),
        },
        "codebook_single_download_bytes": len(_CODEBOOK_JSON.encode("utf-8")),
    }


def _without_telemetry() -> Exception:
    """Builds the uniform error for the absence of telemetry in the queue."""
    from fastapi import HTTPException, status

    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="No telemetry recorded in the queue.",
    )
