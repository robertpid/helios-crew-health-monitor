"""
H.E.L.I.O.S. (Holistic Edge Life-support Intelligence & Operational Support)
Central Inference Engine and Edge API Server (FastAPI + Pure NumPy).

Built for edge computing on deep space missions.
Runs 4 analytical brains with pure linear algebra and no heavy dependencies:
- Brain 1: Environmental Engine (Cabin and radiation heuristics).
- Brain 2: Biometric Engine (Baseline deviation and circadian/bone fatigue).
- Brain 3: Logic Graph and Spatial Fusion (Kronecker Tensor Product: np.kron).
- Brain 4: ASTRA Cognitive Vector Intelligence (Cosine Similarity: np.dot).

Consumes asynchronously from Redis queues ('earth_telemetry_mailbox') via RPOP
and exposes REST endpoints for crew monitoring and control.
"""

from contextlib import asynccontextmanager
import logging
import os
import sys
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

from helios_inference.brains.brain_1_environmental import EnvironmentalBrain
from helios_inference.brains.brain_2_biometric import BiometricBrain
from helios_inference.brains.brain_3_fusion_graph import FusionGraphBrain
from helios_inference.brains.brain_4_astra import AstraCognitiveBrain
from helios_inference.domain.decision_rules import CRITICAL_RULES_CATALOG, RuleDefinition
from helios_inference.domain.inference_models import ConsolidatedInferenceReport
from helios_inference.infrastructure.redis_consumer import AsyncRedisTelemetryConsumer
from helios_inference.services.decision_matrix_evaluator import DecisionMatrixEvaluator
from helios_inference.services.inference_engine import InferenceEngine
from helios_inference.api.psychology_router import router as psychology_router
from helios_inference.api.telemetry_router import (
    router as telemetry_router,
    register_cycle_provider,
)

# Logging subsystem configuration per aerospace standards
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d UTC | %(levelname)-8s | [%(name)s] | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("helios_inference")


# ======================================================================================
# DEPENDENCY INJECTION (SOLID - DIP): MODULAR CONSTRUCTION OF THE 4 BRAINS
# ======================================================================================
def instantiate_inference_engine() -> InferenceEngine:
    """Assembles the engine by injecting independent instances for each brain (DIP)."""
    environmental_brain = EnvironmentalBrain(
        co2_threshold_mmhg=3.0, radiation_threshold_msv=600.0,
        min_pressure_kpa=95.0, max_pressure_kpa=103.0,
    )
    biometric_brain = BiometricBrain(
        tachycardia_threshold_bpm=95.0, bradycardia_threshold_bpm=50.0,
        min_sleep_threshold_hours=6.0, bone_risk_start_mission_day=30,
        bone_loss_threshold_pct=1.5,
    )
    graph_brain = FusionGraphBrain(severe_hazard_threshold=6.5)
    astra_brain = AstraCognitiveBrain(
        base_latency_ms=200.0, base_density_score=1.0,
        similarity_drop_threshold=0.88, fatigue_latency_threshold_ms=500.0,
    )
    matrix_evaluator = DecisionMatrixEvaluator()

    return InferenceEngine(
        environmental_brain=environmental_brain,
        biometric_brain=biometric_brain,
        fusion_graph_brain=graph_brain,
        astra_cognitive_brain=astra_brain,
        matrix_evaluator=matrix_evaluator,
    )


# Single instance of the analytical orchestrator
global_inference_engine = instantiate_inference_engine()

# Asynchronous consumer for background ingestion from Redis
global_redis_consumer = AsyncRedisTelemetryConsumer(
    inference_engine=global_inference_engine,
    host="127.0.0.1",
    port=6379,
    queues=["earth_telemetry_mailbox", "earth_telemetry_mailbox_queue"],
    polling_interval_seconds=0.5,
    retry_interval_seconds=3.0,
)


# ======================================================================================
# FASTAPI LIFECYCLE (ASYNCHRONOUS LIFESPAN)
# ======================================================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages the clean startup and shutdown of the asynchronous Redis consumer.
    Ensures the FastAPI service starts immediately without blocking on the network.
    """
    logger.info("Starting the H.E.L.I.O.S. Inference Engine (Edge Computing Mode)...")
    await global_redis_consumer.start()
    yield
    logger.info("Stopping H.E.L.I.O.S. services and releasing connections...")
    await global_redis_consumer.stop()


# ======================================================================================
# FASTAPI SERVER
# ======================================================================================
app = FastAPI(
    title="H.E.L.I.O.S. - Deep Space Life Support Inference Engine",
    description=(
        "Edge inference engine (Edge AI) for life support and preliminary assessment "
        "of space crews, based on 4 modular brains with pure linear algebra (NumPy)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Mounting the static layer of the N-Layer Frontend
frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Including the router for astronaut psychological assessment and wellbeing (ASTRA BHP)
app.include_router(psychology_router, prefix="/api/v1/psychological", tags=["Psychological Assessment"])

# Compact telemetry router (codes + numeric values) and its codebook
app.include_router(telemetry_router, prefix="/api/v1/telemetry", tags=["Compact Telemetry"])


def _get_current_cycle() -> tuple[ConsolidatedInferenceReport, dict[str, Any]] | None:
    """
    Delivers the (report, payload) pair of the current cycle for the compactor.

    If no telemetry has arrived over Redis yet, it processes the default nominal
    sample so the HUD has a valid cycle from startup.
    """
    report = global_redis_consumer.last_report
    payload = global_redis_consumer.last_payload
    if report is not None and payload is not None:
        return report, payload

    initial_payload = TelemetryInputSchema().model_dump()
    return global_inference_engine.process_telemetry(initial_payload), initial_payload


register_cycle_provider(_get_current_cycle)


def serve_dashboard_html() -> HTMLResponse:
    """Returns the Cockpit HUD HTML document with strict anti-cache headers."""
    html_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if not os.path.exists(html_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interface file frontend/index.html not found.",
        )
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), headers=headers)


# Schema for direct HTTP injection (tests without Redis)
class TelemetryInputSchema(BaseModel):
    """Input payload for an immediate preliminary assessment over REST."""
    mission_id: str = Field(default="ARES-VI-MARS-EXPEDITION")
    mission_day: int = Field(default=120)
    astronaut_id: str = Field(default="ASTRO-HELIOS-01")
    environment: dict[str, Any] = Field(
        default={
            "co2_mmHg": 1.8,
            "cumulative_radiation_mSv": 85.0,
            "cabin_pressure_kpa": 101.3,
            "solar_event_active": False,
        }
    )
    biometrics: dict[str, Any] = Field(
        default={
            "heart_rate_bpm": 68.0,
            "last_cycle_sleep_hours": 7.0,
            "bone_loss_pct": 0.8,
            "fatigue_risk_alert": False,
        }
    )
    cognition: dict[str, Any] = Field(
        default={
            "voice_latency_ms": 210.0,
            "lexical_density_score": 0.95,
            "sans_vision_symptom": False,
        }
    )


# ======================================================================================
# REST ENDPOINTS
# ======================================================================================
@app.get(
    "/",
    summary="Visual Dashboard / General H.E.L.I.O.S. Status",
    tags=["System"],
)
async def system_status(request: Request) -> Any:
    """
    Returns the interactive Holographic Dashboard in web browsers (Accept text/html)
    or the operational JSON metadata on machine API calls (Accept application/json).
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept and not (
        "application/json" in accept and accept.index("application/json") < accept.index("text/html")
    ):
        return serve_dashboard_html()

    return {
        "system": "H.E.L.I.O.S. Edge AI Inference Engine",
        "reference_mission": "ARES-VI-MARS-EXPEDITION (Day 120)",
        "state": "OPERATIONAL",
        "active_brains": [
            "Brain 1: Environmental Engine (Heuristic Rules in R^3)",
            "Brain 2: Biometric Engine (Baseline Deviation in R^4)",
            "Brain 3: Logic Graph and Spatial Fusion (Kronecker Tensor Product in R^12)",
            "Brain 4: ASTRA Cognitive Vector Intelligence (Cosine Similarity in R^2)",
        ],
        "edge_ai_constraints": {
            "pytorch_tensorflow": "DISABLED (Pure-NumPy Mode)",
            "graph_vector_bases": "DISABLED (np.kron/np.dot matrix algebra)",
            "memory_usage": "< 60 MB",
            "typical_inference_latency": "< 1.0 ms",
        },
        "redis_link": {
            "connected": global_redis_consumer.connected,
            "processed_packets": global_redis_consumer.processed_counter,
        },
        "dashboard_ui_url": "http://127.0.0.1:8000/dashboard",
    }


@app.get(
    "/dashboard",
    response_class=HTMLResponse,
    summary="Holographic Life Support Dashboard",
    tags=["Visual Interface"],
)
async def view_dashboard() -> HTMLResponse:
    """Directly renders the cabin visual interface with the holographic body and habitat."""
    return serve_dashboard_html()


@app.get(
    "/health",
    summary="Edge Node Health Check",
    tags=["System"],
)
async def healthcheck() -> dict[str, Any]:
    """Checks the engine state and connectivity with the Redis infrastructure."""
    return {
        "state": "OK",
        "redis_connected": global_redis_consumer.connected,
        "ingested_messages": global_redis_consumer.processed_counter,
    }


@app.get(
    "/api/v1/fusion/result",
    response_model=ConsolidatedInferenceReport,
    summary="Get the Latest Fusion Result of the 4 Brains",
    tags=["Inference"],
)
async def get_fusion_result() -> ConsolidatedInferenceReport:
    """
    Exposes the consolidated result of the latest telemetry processed by the 4 Brains.
    If no telemetry has arrived from Redis yet, it processes a default nominal sample.
    """
    report = global_redis_consumer.last_report
    if report is None:
        # Generate an initial demonstration inference for the startup state
        initial_payload = TelemetryInputSchema().model_dump()
        report = global_inference_engine.process_telemetry(initial_payload)

    return report


@app.get(
    "/api/v1/alerts",
    summary="List of Active Preliminary Assessments and Alerts",
    tags=["Inference"],
)
async def get_active_alerts() -> dict[str, Any]:
    """Returns the current alerts and preliminary assessments derived from the multivariate crossover."""
    report = global_redis_consumer.last_report
    if report is None:
        return {
            "active_preliminary_assessments": [],
            "severe_physiological_stress": False,
            "cognitive_incongruence": False,
            "message": "No telemetry recorded in the queue.",
        }

    return {
        "timestamp": report.inference_timestamp.isoformat(),
        "astronaut_id": report.astronaut_id,
        "mission_day": report.mission_day,
        "active_preliminary_assessments": report.active_preliminary_assessments,
        "severe_physiological_stress": report.brain_3_fusion_graph.severe_physiological_stress,
        "cognitive_incongruence": report.brain_4_astra.cognitive_incongruence_detected,
        "critical_graph_edge": report.brain_3_fusion_graph.critical_synergy_edge,
    }


@app.post(
    "/api/v1/infer",
    response_model=ConsolidatedInferenceReport,
    status_code=status.HTTP_200_OK,
    summary="Direct Inference over REST (Test without Redis)",
    tags=["Inference"],
)
async def infer_direct(payload: TelemetryInputSchema) -> ConsolidatedInferenceReport:
    """
    Allows injecting a telemetry payload directly over HTTP to obtain the immediate
    preliminary assessment and verify the behavior of the 4 brains.
    """
    try:
        report = global_inference_engine.process_telemetry(payload.model_dump())
        return report
    except Exception as error:
        logger.error("Error processing direct inference: %s", str(error), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Inference engine failure: {error}",
        )


@app.get(
    "/api/v1/decision-matrix",
    summary="Catalog of the 15 Critical Crossover Rules (NASA-STD-3001)",
    tags=["Decision Matrix"],
)
async def get_matrix_catalog() -> list[RuleDefinition]:
    """Returns the 15 formal rules of Martina's matrix for inspection or frontend configuration."""
    return CRITICAL_RULES_CATALOG


@app.get(
    "/api/v1/countermeasures/active",
    summary="Prioritized Immediate Countermeasures (Maximum 3 Actions)",
    tags=["Countermeasures"],
)
async def get_active_countermeasures() -> dict[str, Any]:
    """
    Returns up to 3 prioritized countermeasures from the dominant active alerts,
    ordered by strict hierarchy to avoid cognitive saturation of the astronaut.
    """
    report = global_redis_consumer.last_report
    if report is None:
        initial_payload = TelemetryInputSchema().model_dump()
        report = global_inference_engine.process_telemetry(initial_payload)

    return {
        "timestamp": report.inference_timestamp.isoformat(),
        "astronaut_id": report.astronaut_id,
        "mission_day": report.mission_day,
        "max_allowed_actions": 3,
        "prioritized_countermeasures": report.prioritized_countermeasures,
        "total_active_crossovers": len(report.decision_matrix_alerts),
        "detailed_alerts": [
            {
                "rule_id": a.rule_id,
                "level": a.level.value,
                "domain": a.domain.value,
                "preliminary_assessment": a.preliminary_assessment,
                "suggested_actions": a.suggested_countermeasures,
                "recipients": [d.value for d in a.recipients],
                "base_standard": a.base_standard,
            }
            for a in report.decision_matrix_alerts
        ],
    }


# ======================================================================================
# SAFE MAIN ENTRY POINT (PEP 8)
# ======================================================================================
if __name__ == "__main__":
    logger.info("Starting the aerospace web server at http://0.0.0.0:8000 (local network active)...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
    )
