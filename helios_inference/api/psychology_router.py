"""
REST API module: ASTRA Psychological and Cognitive Assessment (NASA-BHP).

Evaluates the vocal articulation rate (Words Per Minute - WPM), syllabic cadence,
lexical density and multivariate physiological crossover with biosignals (heart
rate and stress).

Complies strictly with:
- PEP 8 and static type annotations (Type Hints).
- Single Responsibility Principle (SRP).
- Traceability through the logging module (no print).
- Zero occurrences of restricted medical terms.
- Maximum file length <= 400 lines.
"""

import logging
import re
from typing import Any, List
from fastapi import APIRouter, HTTPException, status
import numpy as np
from pydantic import BaseModel, Field

from helios_inference.brains.brain_4_astra import AstraCognitiveBrain
from helios_inference.domain.inference_models import BiometricInferenceState

logger = logging.getLogger(__name__)

router = APIRouter()

_astra_brain = AstraCognitiveBrain(
    base_latency_ms=200.0,
    base_density_score=1.0,
    similarity_drop_threshold=0.88,
    fatigue_latency_threshold_ms=500.0,
)


class PsychologicalAssessmentInput(BaseModel):
    """Input schema for evaluating the astronaut's response and speech."""

    question_id: int = Field(..., ge=1, le=3, description="Question identifier (1-3)")
    response_text: str = Field(..., min_length=1, description="Text typed or dictated by voice")
    latency_ms: float = Field(default=2000.0, ge=0.0, description="Interaction duration in ms")
    words_per_minute: float = Field(default=135.0, ge=10.0, le=400.0, description="Vocal rate (WPM)")
    heart_rate_bpm: float = Field(default=72.0, ge=30.0, le=220.0, description="Current heart rate")
    body_in_panic: bool = Field(default=False, description="Severe stress indicator from Brain 2")


class PsychologicalAssessmentOutput(BaseModel):
    """Output schema with articulation metrics and the preliminary assessment."""

    question_id: int
    words_per_minute: float
    cadence_ms_per_word: float
    lexical_density: float
    cosine_similarity: float
    incongruence_detected: bool
    preliminary_assessment: str
    assistant_response: str
    cognitive_state: str


class PsychologicalQuestionItem(BaseModel):
    """Schema of a NASA-BHP protocol question."""

    question_id: int
    category: str
    question: str
    quick_suggestions: List[str]


BHP_QUESTIONS: List[PsychologicalQuestionItem] = [
    PsychologicalQuestionItem(
        question_id=1,
        category="Alertness & Attention Level",
        question="How would you describe your concentration and energy level for today's operations?",
        quick_suggestions=[
            "100% focused and clear for the shift.",
            "Normal, within the usual parameters.",
            "I have felt mental slowness and attentional fatigue today.",
        ],
    ),
    PsychologicalQuestionItem(
        question_id=2,
        category="Workload & Decision Making",
        question="Have you experienced overload or delay in resolving technical tasks today?",
        quick_suggestions=[
            "Zero overload, procedures executed in optimal time.",
            "Fine, standard operational load.",
            "The checklists have taken me more time and effort than expected.",
        ],
    ),
    PsychologicalQuestionItem(
        question_id=3,
        category="Emotional State & Sol 120 Confinement",
        question="Sol 120 report: How do you perceive the cabin environment and the distance from Earth?",
        quick_suggestions=[
            "Excellent team morale, fluid communication with Houston.",
            "Fine, we are relaxed and in order here.",
            "The prolonged isolation is noticeable today, I need a short break.",
        ],
    ),
]


def compute_density_and_type(text: str) -> tuple[float, str]:
    """Analyzes lexical richness and classifies the tenor of the response."""
    tokens = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    total = len(tokens)
    if total == 0:
        return 0.20, "empty"

    fatigue_words = {
        "sleep", "sleepy", "tired", "tiredness", "fatigue", "slow", "slowness",
        "heavy", "isolation", "delay", "overload", "stress", "stressed",
        "overwhelmed", "difficulty", "time", "effort", "exhausted", "drained",
    }
    positive_words = {
        "fine", "good", "normal", "order", "control", "focused", "clear",
        "optimal", "excellent", "stable", "fluid", "calm",
        "quiet", "relaxed", "zero", "steady", "no", "problems",
        "usual", "peace", "sharp",
    }

    has_fatigue = any(tok in fatigue_words for tok in tokens)
    has_positives = any(tok in positive_words for tok in tokens)

    if has_fatigue:
        response_type = "declared_fatigue"
        density = 0.75 + min(0.15, total * 0.02)
    elif has_positives:
        response_type = "concise_nominal"
        density = 0.92
    else:
        response_type = "elaborate"
        unique = len(set(tokens))
        ratio = unique / float(total)
        density = float(np.clip((ratio * 0.65) + min(0.35, total * 0.03), 0.35, 1.0))

    return round(density, 3), response_type


def generate_assistant_feedback(
    question_id: int,
    response_type: str,
    incongruence: bool,
    wpm: float,
    rate_bpm: float,
) -> tuple[str, str, str]:
    """Generates the assistant message, finding and category without revealing metrics to the crew member."""
    # 1. Incongruence: physiological activation with feigned calm wording
    if incongruence and rate_bpm > 95.0:
        finding = "INCONGRUENCE DETECTED: CALM SPEECH UNDER PHYSIOLOGICAL ACTIVATION"
        msg = (
            "Commander, the cabin physiological records reflect stress activation during "
            "your report. We recommend taking a short active break and the 4-4-6 breathing guide."
        )
        return finding, msg, "CRITICAL_INCONGRUENCE"

    # 2. Bradylalia / psychomotor slowing (< 85 WPM)
    if wpm < 85.0:
        finding = "OPERATIONAL FATIGUE FROM BRADYLALIA (SLOW CADENCE)"
        msg = (
            "Commander, we are recording signs of fatigue and cumulative attentional wear in this report. "
            "Cabin hydration and a preventive 15-minute break are suggested."
        )
        return finding, msg, "MILD_FATIGUE"

    # 3. Fatigue honestly declared by the crew member
    if response_type == "declared_fatigue":
        finding = "OPERATIONAL FATIGUE REPORTED (OPERATIONAL HONESTY)"
        fatigue_messages = {
            1: "Fatigue and energy level logged in the operational record. Hydrate with 500 ml and adjust the cabin lighting.",
            2: "Checklist overload logged in the record. The ASTRA system is reorganizing secondary mission tasks.",
            3: "Sol 120 wellbeing report logged. Cabin support procedure activated.",
        }
        msg = fatigue_messages.get(question_id, "Fatigue report logged in the operational record.")
        return finding, msg, "MILD_FATIGUE"

    # 4. Nominal / Coherent state (includes "relaxed", "fine", "optimal")
    finding = "COHERENT: NOMINAL OPERATIONAL STATE"
    nominal_messages = {
        1: "Copy that, Commander. Clear communication and optimal state for flight operations.",
        2: "Excellent. Responses recorded within the expected nominal margins of the mission.",
        3: "Sol 120 report logged successfully. Balanced state and steady crew morale.",
    }
    msg = nominal_messages.get(
        question_id,
        "Report logged successfully in the mission record. Parameters stable.",
    )
    return finding, msg, "NOMINAL"


@router.get(
    "/questions",
    response_model=List[PsychologicalQuestionItem],
    summary="BHP Protocol Question Catalog",
)
async def get_protocol_questions() -> List[PsychologicalQuestionItem]:
    """Returns the 3 standardized questions of the psychological check protocol."""
    return BHP_QUESTIONS


@router.post(
    "/evaluate",
    response_model=PsychologicalAssessmentOutput,
    summary="Evaluate Psychological Response and Vocal Cadence",
)
async def evaluate_astronaut_response(
    payload: PsychologicalAssessmentInput,
) -> PsychologicalAssessmentOutput:
    """
    Evaluates the articulation rate (WPM), cadence, lexical richness and physiological crossover.
    """
    try:
        density, response_type = compute_density_and_type(payload.response_text)
        wpm = float(np.clip(payload.words_per_minute, 40.0, 280.0))
        cadence_ms = round(60000.0 / wpm, 1)

        # Mapping to the normalized ASTRA cognitive vector
        wpm_ratio = wpm / 135.0  # 135 WPM is the nominal baseline
        equivalent_latency_ms = 200.0 / wpm_ratio

        cognition_data = {
            "voice_latency_ms": equivalent_latency_ms,
            "lexical_density_score": density,
        }

        bio_state = BiometricInferenceState(
            biometric_vector=[1.0 if payload.heart_rate_bpm > 95.0 else 0.0, 0.0, 0.0, 0.0],
            activated_labels=[],
            normal_physical_metrics=bool(payload.heart_rate_bpm <= 95.0),
            body_in_panic=payload.body_in_panic,
        )

        similarity, astra_state = _astra_brain.process(
            cognition_data=cognition_data,
            biometric_state=bio_state,
            heart_rate_bpm=payload.heart_rate_bpm,
        )

        incongruence = bool(
            (payload.heart_rate_bpm > 95.0 and response_type in ["concise_nominal", "elaborate"])
            or wpm < 85.0
        )

        preliminary_assessment, assistant_response, cognitive_state = generate_assistant_feedback(
            question_id=payload.question_id,
            response_type=response_type,
            incongruence=incongruence,
            wpm=wpm,
            rate_bpm=payload.heart_rate_bpm,
        )

        logger.info(
            "ASTRA BHP Q%d | %s | WPM: %.0f (%.0f ms/word) | Density: %.2f | CosSim: %.3f | %s",
            payload.question_id,
            response_type,
            wpm,
            cadence_ms,
            density,
            similarity,
            cognitive_state,
        )

        return PsychologicalAssessmentOutput(
            question_id=payload.question_id,
            words_per_minute=round(wpm, 1),
            cadence_ms_per_word=cadence_ms,
            lexical_density=density,
            cosine_similarity=round(similarity, 4),
            incongruence_detected=incongruence,
            preliminary_assessment=preliminary_assessment,
            assistant_response=assistant_response,
            cognitive_state=cognitive_state,
        )
    except Exception as exc:
        logger.error("Failed to evaluate the psychological protocol: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error in the psychological analytical engine: {exc}",
        )


if __name__ == "__main__":
    logger.info("Psychological API module loaded correctly.")
