"""
Brain 2: H.E.L.I.O.S. Biometric Engine (Physiological Baseline Deviation).

Monitors vital biomarkers against the astronaut's personalized baseline:
- Heart rate (bpm): tachycardia or acute exertion threshold (> 95.0 bpm) or bradycardia (< 50.0 bpm).
- Sleep hours: rest deficit (< 6.0 h) or multi-cycle cumulative fatigue.
- Bone demineralization: detection of bone fatigue risk from mission duration (> 30 days)
  or significant cumulative loss (> 1.5%).
- Spaceflight-Associated Neuro-ocular Syndrome (SANS): optic disc edema and blurred vision.

Generates a physiological state vector in R^4: [abnormal_pulse, sleep_deficit, bone_fatigue, sans_symptom].
"""

import logging
from typing import Any
import numpy as np

from helios_inference.domain.inference_models import BiometricInferenceState

logger = logging.getLogger(__name__)


class BiometricBrain:
    """
    Analytical engine for evaluating physical health and baseline deviation.
    Implements the Single Responsibility Principle (SRP).
    """

    def __init__(
        self,
        tachycardia_threshold_bpm: float = 95.0,
        bradycardia_threshold_bpm: float = 50.0,
        min_sleep_threshold_hours: float = 6.0,
        bone_risk_start_mission_day: int = 30,
        bone_loss_threshold_pct: float = 1.5,
    ) -> None:
        """
        Configures the operational limits for the physiological preliminary assessment.

        Args:
            tachycardia_threshold_bpm: Upper heart rate limit at rest/routine.
            bradycardia_threshold_bpm: Lower heart rate limit.
            min_sleep_threshold_hours: Minimum acceptable duration of restorative rest.
            bone_risk_start_mission_day: Mission day from which bone risk activates.
            bone_loss_threshold_pct: Cumulative bone mineral loss percentage of concern.
        """
        self._tachycardia_threshold_bpm = tachycardia_threshold_bpm
        self._bradycardia_threshold_bpm = bradycardia_threshold_bpm
        self._min_sleep_threshold_hours = min_sleep_threshold_hours
        self._bone_risk_start_mission_day = bone_risk_start_mission_day
        self._bone_loss_threshold_pct = bone_loss_threshold_pct

    def process(
        self,
        biometrics_data: dict[str, Any],
        mission_day: int,
        sans_symptom: bool = False,
    ) -> tuple[np.ndarray, BiometricInferenceState]:
        """
        Evaluates the physiological state and generates the biometric vector in R^4.

        Args:
            biometrics_data: Dictionary with biomarkers ('heart_rate_bpm',
                             'last_cycle_sleep_hours', 'bone_loss_pct', etc.).
            mission_day: Cumulative elapsed day of the space mission.
            sans_symptom: Presence of reported neuro-ocular visual alterations.

        Returns:
            Tuple containing:
            - np.ndarray: Physiological state vector with shape (4,).
            - BiometricInferenceState: Structured data of the biometric state.
        """
        pulse = float(biometrics_data.get("heart_rate_bpm", 65.0))
        sleep = float(biometrics_data.get("last_cycle_sleep_hours", 7.0))
        bone_loss = float(biometrics_data.get("bone_loss_pct", 0.0))
        fatigue_risk = bool(biometrics_data.get("fatigue_risk_alert", False))

        # 1. Pulse alert (tachycardia or bradycardia)
        pulse_alert = 1.0 if (pulse > self._tachycardia_threshold_bpm or pulse < self._bradycardia_threshold_bpm) else 0.0

        # 2. Sleep / fatigue alert
        sleep_alert = 1.0 if (sleep < self._min_sleep_threshold_hours or fatigue_risk) else 0.0

        # 3. Bone fatigue alert (Mission day > 30 or cumulative loss > threshold)
        bone_alert = 1.0 if (mission_day > self._bone_risk_start_mission_day or bone_loss > self._bone_loss_threshold_pct) else 0.0

        # 4. SANS symptom alert
        sans_alert = 1.0 if sans_symptom else 0.0

        biometric_vector = np.array([pulse_alert, sleep_alert, bone_alert, sans_alert], dtype=np.float64)

        labels: list[str] = []
        if pulse_alert > 0.0:
            labels.append(f"ABNORMAL_PULSE_ALERT: {pulse:.1f} bpm")
        if sleep_alert > 0.0:
            labels.append(f"SLEEP_DEFICIT_ALERT: {sleep:.1f} hours")
        if bone_alert > 0.0:
            labels.append(f"BONE_RISK_ALERT: Day {mission_day} ({bone_loss:.2f}% loss)")
        if sans_alert > 0.0:
            labels.append("SANS_ACTIVE_ALERT: Neuro-ocular alteration")

        normal_metrics = bool(np.sum(biometric_vector) == 0.0)
        body_panic = bool(pulse > self._tachycardia_threshold_bpm)

        if labels:
            logger.warning("Brain 2 detected physiological deviations: %s", ", ".join(labels))
        else:
            logger.debug("Brain 2: Physiological signs within baseline parameters.")

        state = BiometricInferenceState(
            biometric_vector=biometric_vector.tolist(),
            activated_labels=labels,
            normal_physical_metrics=normal_metrics,
            body_in_panic=body_panic,
        )

        return biometric_vector, state
