"""
Brain 4: Cognitive Vector Intelligence (ASTRA Subsystem).

========================================================================================
COGNITIVE INCONGRUENCE DETECTION VIA COSINE SIMILARITY (LINEAR ALGEBRA WITH NUMPY)
========================================================================================
In deep space missions, astronauts tend — involuntarily or by operational culture — to
minimize symptoms of exhaustion ("pretending to be fine").

ASTRA (Automated Speech & Temporal Response Analysis) analyzes cabin communications:
- voice_latency_ms: verbal response time (nominal baseline: ~200.0 ms).
- lexical_density_score: lexical variety and complexity (nominal baseline: ~1.0).

The current cognitive vector is built:
    C = [voice_latency_ms, lexical_density_score]
and compared against the crew member's Dynamic Baseline:
    B = [200.0, 1.0]

To preserve the sensitivity of the angular metric without distortion from heterogeneous
scales (milliseconds vs the unit range [0, 1]), the components are normalized against
their baseline:
    C_norm = [ voice_latency_ms / 200.0, lexical_density_score / 1.0 ]
    B_norm = [ 1.0, 1.0 ]

Cosine similarity is computed through pure vector algebra:
    similarity = np.dot(C_norm, B_norm) / (np.linalg.norm(C_norm) * np.linalg.norm(B_norm))

BUSINESS RULE (COGNITIVE INCONGRUENCE):
1. If the similarity drops abruptly (for example latency elevated to 600-900 ms), but
   Brain 2 indicates that the physical metrics are nominal ("fine"), OR
2. If the body is in panic or physiological stress (heart rate > 95 bpm) but the voice
   sounds artificially calm and formalized with high lexical density (0.8),
Brain 4 concludes that a behavioral bias exists and emits:
   {"astra_alert": "Cognitive Incongruence Detected. Preliminary assessment: Possible fatigue masking."}
"""

import logging
from typing import Any
import numpy as np

from helios_inference.domain.inference_models import AstraInferenceState
from helios_inference.domain.inference_models import BiometricInferenceState

logger = logging.getLogger(__name__)


class AstraCognitiveBrain:
    """
    Cognitive analytical engine for detecting hidden psychological strain.
    Implements the Single Responsibility Principle (SRP).
    """

    def __init__(
        self,
        base_latency_ms: float = 200.0,
        base_density_score: float = 1.0,
        similarity_drop_threshold: float = 0.88,
        fatigue_latency_threshold_ms: float = 500.0,
    ) -> None:
        """
        Configures the reference parameters for the ASTRA dynamic baseline.

        Args:
            base_latency_ms: Nominal verbal reaction time of the astronaut.
            base_density_score: Nominal lexical index under resting conditions.
            similarity_drop_threshold: Cutoff below which angular mismatch is considered.
            fatigue_latency_threshold_ms: Latency from which psychomotor delay is suspected.
        """
        self._base_latency_ms = base_latency_ms
        self._base_density_score = base_density_score
        self._similarity_drop_threshold = similarity_drop_threshold
        self._fatigue_latency_threshold_ms = fatigue_latency_threshold_ms

        # Normalized baseline vector in R^2
        self._baseline_vector = np.array([1.0, 1.0], dtype=np.float64)

    def compute_cosine_similarity(self, vector_a: np.ndarray, vector_b: np.ndarray) -> float:
        """
        Computes the cosine similarity between two vectors using np.dot and np.linalg.norm.

        Args:
            vector_a: First vector in R^n.
            vector_b: Second vector in R^n.

        Returns:
            Scalar similarity value in the range [-1.0, 1.0].
        """
        norm_a = float(np.linalg.norm(vector_a))
        norm_b = float(np.linalg.norm(vector_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        dot_product = float(np.dot(vector_a, vector_b))
        similarity = dot_product / (norm_a * norm_b)
        # Ensure numerical confinement
        return float(np.clip(similarity, -1.0, 1.0))

    def process(
        self,
        cognition_data: dict[str, Any],
        biometric_state: BiometricInferenceState,
        heart_rate_bpm: float = 65.0,
    ) -> tuple[float, AstraInferenceState]:
        """
        Evaluates the astronaut's cognitive vector and detects possible fatigue or stress masking.

        Args:
            cognition_data: Dictionary with 'voice_latency_ms' and 'lexical_density_score'.
            biometric_state: Physiological state previously evaluated by Brain 2.
            heart_rate_bpm: Instantaneous heart rate to validate cross incongruences.

        Returns:
            Tuple containing:
            - float: Cosine similarity coefficient against the dynamic baseline.
            - AstraInferenceState: Structured result of the ASTRA analysis.
        """
        latency_ms = float(cognition_data.get("voice_latency_ms", self._base_latency_ms))
        density_score = float(cognition_data.get("lexical_density_score", self._base_density_score))

        # Dimensional normalization to preserve angular proportionality
        normalized_cognitive_vector = np.array([
            latency_ms / self._base_latency_ms,
            density_score / self._base_density_score,
        ], dtype=np.float64)

        # Cosine similarity computed through pure linear algebra with NumPy
        cosine_similarity = self.compute_cosine_similarity(
            normalized_cognitive_vector,
            self._baseline_vector,
        )

        # -----------------------------------------------------------------------------
        # COGNITIVE INCONGRUENCE BUSINESS RULES
        # -----------------------------------------------------------------------------
        # Condition A: The similarity drops abruptly (latency spikes to 600-900 ms)
        # but Brain 2 says the physical metrics are "fine" (apparently normal).
        similarity_drop_with_normal_physical = bool(
            (cosine_similarity < self._similarity_drop_threshold or latency_ms >= self._fatigue_latency_threshold_ms)
            and biometric_state.normal_physical_metrics
        )

        # Condition B: The body is in panic (heart rate > 95 bpm / body_in_panic)
        # but the voice is formal and calm with high lexical density (e.g. >= 0.75, "pretending to be fine").
        physical_panic_with_calm_voice = bool(
            (biometric_state.body_in_panic or heart_rate_bpm > 95.0)
            and density_score >= 0.75
            and latency_ms < 350.0
        )

        incongruence_detected = similarity_drop_with_normal_physical or physical_panic_with_calm_voice

        alert_message: str | None = None
        if incongruence_detected:
            alert_message = (
                "Cognitive Incongruence Detected. "
                "Preliminary assessment: Possible fatigue masking."
            )
            logger.warning(
                "BRAIN 4 (ASTRA): %s | Similarity: %.3f | Latency: %.1f ms | Pulse: %.1f bpm",
                alert_message,
                cosine_similarity,
                latency_ms,
                heart_rate_bpm,
            )
        else:
            logger.debug(
                "Brain 4 (ASTRA): Cognitive coherence within nominal margins (Similarity: %.3f)",
                cosine_similarity,
            )

        state = AstraInferenceState(
            baseline_cosine_similarity=cosine_similarity,
            cognitive_incongruence_detected=incongruence_detected,
            astra_alert=alert_message,
        )

        return cosine_similarity, state
