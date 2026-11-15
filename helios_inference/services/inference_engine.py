"""
Central H.E.L.I.O.S. inference engine (Orchestrator of the 4 Brains).

Applies Dependency Inversion (DIP) and Single Responsibility (SRP):
Receives the injected instances of the 4 brains and coordinates the sequential flow
of vector and matrix inference in real time at the computational edge.
"""

import logging
import time
from typing import Any

from helios_inference.brains.brain_1_environmental import EnvironmentalBrain
from helios_inference.brains.brain_2_biometric import BiometricBrain
from helios_inference.brains.brain_3_fusion_graph import FusionGraphBrain
from helios_inference.brains.brain_4_astra import AstraCognitiveBrain
from helios_inference.domain.inference_models import ConsolidatedInferenceReport
from helios_inference.services.decision_matrix_evaluator import DecisionMatrixEvaluator

logger = logging.getLogger(__name__)


class InferenceEngine:
    """
    H.E.L.I.O.S. Edge AI inference orchestrator.
    Runs the preliminary assessment pipeline over space telemetry.
    """

    def __init__(
        self,
        environmental_brain: EnvironmentalBrain | None = None,
        biometric_brain: BiometricBrain | None = None,
        fusion_graph_brain: FusionGraphBrain | None = None,
        astra_cognitive_brain: AstraCognitiveBrain | None = None,
        matrix_evaluator: DecisionMatrixEvaluator | None = None,
    ) -> None:
        """
        Initializes the engine with dependency injection of the 4 brains and the matrix evaluator.

        Args:
            environmental_brain: Instance of the environmental engine (Brain 1).
            biometric_brain: Instance of the biometric engine (Brain 2).
            fusion_graph_brain: Instance of the matrix graph orchestrator (Brain 3).
            astra_cognitive_brain: Instance of ASTRA cognitive intelligence (Brain 4).
            matrix_evaluator: Evaluator of the 15 critical NASA crossover rules.
        """
        self._b1 = environmental_brain or EnvironmentalBrain()
        self._b2 = biometric_brain or BiometricBrain()
        self._b3 = fusion_graph_brain or FusionGraphBrain()
        self._b4 = astra_cognitive_brain or AstraCognitiveBrain()
        self._matrix_evaluator = matrix_evaluator or DecisionMatrixEvaluator()

    def process_telemetry(self, payload: dict[str, Any]) -> ConsolidatedInferenceReport:
        """
        Runs the full multivariate inference cycle over a telemetry payload.

        Args:
            payload: Deserialized space telemetry dictionary.

        Returns:
            ConsolidatedInferenceReport with the analysis of the 4 brains and preliminary assessments.
        """
        start_time = time.perf_counter()

        # Extraction and decoupling of sub-domains
        mission_id = str(payload.get("mission_id", "ARES-VI-MARS-EXPEDITION"))
        mission_day = int(payload.get("mission_day", 120))
        astronaut_id = str(payload.get("astronaut_id", "ASTRO-HELIOS-01"))

        environment_data: dict[str, Any] = payload.get("environment", {})
        biometrics_data: dict[str, Any] = payload.get("biometrics", {})
        cognition_data: dict[str, Any] = payload.get("cognition", {})

        sans_symptom = bool(
            cognition_data.get("sans_vision_symptom", False)
            or biometrics_data.get("sans_vision_symptom", False)
        )
        heart_rate = float(biometrics_data.get("heart_rate_bpm", 65.0))

        # -----------------------------------------------------------------------------
        # PHASE 1: Environmental inference (Brain 1)
        # -----------------------------------------------------------------------------
        environmental_vector, state_b1 = self._b1.process(environment_data)

        # -----------------------------------------------------------------------------
        # PHASE 2: Physiological inference (Brain 2)
        # -----------------------------------------------------------------------------
        biometric_vector, state_b2 = self._b2.process(
            biometrics_data=biometrics_data,
            mission_day=mission_day,
            sans_symptom=sans_symptom,
        )

        # -----------------------------------------------------------------------------
        # PHASE 3: Matrix graph and Kronecker fusion (Brain 3)
        # -----------------------------------------------------------------------------
        _, state_b3 = self._b3.fuse(
            environmental_vector=environmental_vector,
            biometric_vector=biometric_vector,
        )

        # -----------------------------------------------------------------------------
        # PHASE 4: ASTRA cognitive vector intelligence (Brain 4)
        # -----------------------------------------------------------------------------
        _, state_b4 = self._b4.process(
            cognition_data=cognition_data,
            biometric_state=state_b2,
            heart_rate_bpm=heart_rate,
        )

        # -----------------------------------------------------------------------------
        # PHASE 5: Critical Decision Matrix evaluation (15 NASA crossovers)
        # -----------------------------------------------------------------------------
        matrix_alerts = self._matrix_evaluator.evaluate_telemetry(payload)

        # -----------------------------------------------------------------------------
        # CONSOLIDATION OF PRELIMINARY ASSESSMENTS AND ALERTS
        # -----------------------------------------------------------------------------
        assessments: list[str] = []

        # Add Brain 1 alerts
        assessments.extend(state_b1.activated_labels)

        # Add Brain 2 alerts
        assessments.extend(state_b2.activated_labels)

        # Add the fusion alert if severe stress triggers
        if state_b3.severe_physiological_stress and state_b3.fusion_preliminary_assessment:
            assessments.append(state_b3.fusion_preliminary_assessment)

        # Add the ASTRA alert if there is cognitive incongruence
        if state_b4.cognitive_incongruence_detected and state_b4.astra_alert:
            assessments.append(state_b4.astra_alert)

        # Add the findings of the decision matrix
        for matrix_alert in matrix_alerts:
            assessments.append(f"[{matrix_alert.rule_id} - {matrix_alert.level.value}] {matrix_alert.preliminary_assessment}")

        # Consolidate up to 3 prioritized countermeasures from the most critical alerts
        consolidated_countermeasures: list[str] = []
        for matrix_alert in matrix_alerts:
            for action in matrix_alert.suggested_countermeasures:
                if action not in consolidated_countermeasures and len(consolidated_countermeasures) < 3:
                    consolidated_countermeasures.append(action)
            if len(consolidated_countermeasures) >= 3:
                break

        total_time_ms = (time.perf_counter() - start_time) * 1000.0

        report = ConsolidatedInferenceReport(
            mission_id=mission_id,
            mission_day=mission_day,
            astronaut_id=astronaut_id,
            brain_1_environmental=state_b1,
            brain_2_biometric=state_b2,
            brain_3_fusion_graph=state_b3,
            brain_4_astra=state_b4,
            active_preliminary_assessments=assessments,
            decision_matrix_alerts=matrix_alerts,
            prioritized_countermeasures=consolidated_countermeasures,
            compute_time_ms=round(total_time_ms, 3),
            edge_metadata={
                "engine": "H.E.L.I.O.S. Pure-NumPy Inference Engine",
                "linear_algebra": "np.kron + np.dot + np.argmax",
                "processing_latency_ms": round(total_time_ms, 3),
                "hardware_target": "Deep Space Radiation-Tolerant Single Board Computer",
                "active_matrix_rules": len(matrix_alerts),
            },
        )

        logger.info(
            "Inference cycle completed in %.3f ms. Active preliminary assessments: %d",
            total_time_ms,
            len(assessments),
        )

        return report
