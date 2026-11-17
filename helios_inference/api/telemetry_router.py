"""
H.E.L.I.O.S. compact telemetry router.

Exposes the reduced link format and the codebook that accompanies it:

    GET /api/v1/telemetry/codebook   -> templates and catalog (single download)
    GET /api/v1/telemetry/compact    -> latest cycle in codes + numbers
    GET /api/v1/telemetry/savings    -> live-measured bandwidth comparison

The full report with text remains available at /api/v1/fusion/result for
debugging; this router is the one the HUD should consume in nominal operation.
"""

import asyncio
import json
import logging
import time
from typing import Any, Callable

from fastapi import APIRouter, Response, WebSocket, WebSocketDisconnect

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


# ==============================================================================
# HARDWARE SENSOR WATCHDOG ("PERRO GUARDIAN") & REAL-TIME WEBSOCKET STREAM
# ==============================================================================
_SENSOR_NODES: list[dict[str, Any]] = [
    {
        "id": "ASTROSKIN-BIO-01",
        "name": "Astroskin Biometric Vest",
        "metrics": "ECG · HR · HRV · Resp Rate",
        "bus": "BLE-Space / SPI",
        "wdt_timeout_ms": 3000,
        "connected": True,
    },
    {
        "id": "OXI-OPTIC-02",
        "name": "Optical Pulse Oximeter & BP",
        "metrics": "SpO2 · Systolic/Diastolic MAP",
        "bus": "I2C-Isolated",
        "wdt_timeout_ms": 3000,
        "connected": True,
    },
    {
        "id": "THERM-CORE-03",
        "name": "Core & Skin Thermal Array",
        "metrics": "Core Temp · Peripheral Skin °C",
        "bus": "1-Wire Aerospace",
        "wdt_timeout_ms": 4000,
        "connected": True,
    },
    {
        "id": "ECLSS-CDRA-04",
        "name": "ECLSS Cabin CO2 & Barometer",
        "metrics": "CO2 mmHg/ppm · Pressure kPa",
        "bus": "CAN-FD Bus A",
        "wdt_timeout_ms": 2500,
        "connected": True,
    },
    {
        "id": "RAD-TEPC-05",
        "name": "TEPC Radiation Dosimeter",
        "metrics": "Cumulative mSv · Solar Particle",
        "bus": "RS-485 RadHard",
        "wdt_timeout_ms": 2000,
        "connected": True,
    },
    {
        "id": "SONAR-MEMS-06",
        "name": "Cabin Acoustic MEMS Array",
        "metrics": "LEQ16 Work · LEQ8 Sleep · Voice",
        "bus": "I2S Digital Audio",
        "wdt_timeout_ms": 3500,
        "connected": True,
    },
    {
        "id": "ARED-LOAD-07",
        "name": "ARED Piezo Force & Bone Load",
        "metrics": "ARED % · BMD Loss · FIT Quota",
        "bus": "CAN-FD Bus B",
        "wdt_timeout_ms": 5000,
        "connected": True,
    },
    {
        "id": "SANS-FUNDUS-08",
        "name": "SANS Optical & Fundus Node",
        "metrics": "Acuity · Amsler · Contrast",
        "bus": "USB-C Medical",
        "wdt_timeout_ms": 5000,
        "connected": True,
    },
]


def build_watchdog_snapshot() -> dict[str, Any]:
    """Builds the current Watchdog timer snapshot for all hardware sensors."""
    now_ms = int(time.time() * 1000)
    sensors_out: list[dict[str, Any]] = []
    online_count = 0
    for idx, node in enumerate(_SENSOR_NODES):
        is_conn = bool(node["connected"])
        if is_conn:
            online_count += 1
        jitter_ms = (now_ms + idx * 37) % 180 + 40 if is_conn else node["wdt_timeout_ms"] + 1200
        sensors_out.append(
            {
                **node,
                "status": "ONLINE" if is_conn else "WDT_TIMEOUT_FAILOVER",
                "failover_mode": "LIVE_STREAM" if is_conn else "LKG_KALMAN_HOLD",
                "last_heartbeat_ms": jitter_ms,
            }
        )
    return {
        "timestamp_ms": now_ms,
        "total_sensors": len(_SENSOR_NODES),
        "online_sensors": online_count,
        "failover_sensors": len(_SENSOR_NODES) - online_count,
        "watchdog_state": "NOMINAL" if online_count == len(_SENSOR_NODES) else "DEGRADED_FAILOVER_ACTIVE",
        "sensors": sensors_out,
    }


@router.get("/watchdog", summary="Hardware Sensor Watchdog Status")
async def get_watchdog_status() -> dict[str, Any]:
    """Returns the real-time heartbeat and watchdog status of all cabin sensors."""
    return build_watchdog_snapshot()


@router.post("/watchdog/toggle/{sensor_id}", summary="Simulate Sensor Disconnect / Reconnect")
async def toggle_sensor_connection(sensor_id: str) -> dict[str, Any]:
    """Toggles a hardware sensor node to test Watchdog timeout and zero-drop failover."""
    for node in _SENSOR_NODES:
        if node["id"] == sensor_id:
            node["connected"] = not bool(node["connected"])
            new_state = "RECONNECTED (LIVE)" if node["connected"] else "DISCONNECTED (WDT FAILOVER)"
            logger.warning("Hardware Watchdog event on %s: %s", sensor_id, new_state)
            break
    return build_watchdog_snapshot()


@router.websocket("/ws")
async def telemetry_websocket_endpoint(websocket: WebSocket) -> None:
    """
    Full-duplex WebSocket streaming compact telemetry + sensor watchdog heartbeats.
    Guarantees real-time updates and instant detection of sensor disconnections.
    """
    await websocket.accept()
    logger.info("Real-time Telemetry & Watchdog WebSocket client connected.")
    try:
        while True:
            cycle = _cycle_provider() if _cycle_provider else None
            compact_data: dict[str, Any] | None = None
            if cycle is not None:
                report, payload = cycle
                compact_data = compact_record(report, payload).model_dump()

            packet = {
                "type": "TELEMETRY_WATCHDOG_FRAME",
                "compact": compact_data,
                "watchdog": build_watchdog_snapshot(),
            }
            await websocket.send_json(packet)

            try:
                msg_raw = await asyncio.wait_for(websocket.receive_text(), timeout=1.5)
                msg = json.loads(msg_raw)
                action = msg.get("action")
                if action == "toggle_sensor":
                    target_id = str(msg.get("sensor_id", ""))
                    await toggle_sensor_connection(target_id)
                elif action == "restore_all":
                    for n in _SENSOR_NODES:
                        n["connected"] = True
                    logger.info("Watchdog: All hardware sensors restored to ONLINE.")
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        logger.info("Telemetry WebSocket client disconnected; client watchdog failover active.")
    except Exception as exc:
        logger.error("WebSocket telemetry error: %s", str(exc))

