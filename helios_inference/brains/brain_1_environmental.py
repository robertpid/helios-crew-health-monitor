"""
Brain 1: H.E.L.I.O.S. Environmental Engine (Environmental Heuristic Rules).

Evaluates the critical life support variables per NASA limits:
- Cabin CO2: normative threshold > 3.0 mmHg (NASA-STD-3001 Vol. 2, Req. 6004).
- Cumulative radiation: cumulative career limit > 600 mSv or the presence of a solar storm (SPE).
- Cabin pressure: normative range 95.0 - 103.0 kPa (NASA-STD-3001 Vol. 2, Req. 6006).

Generates an environmental state vector in R^3 with binary/one-hot encoding.
"""

import logging
from typing import Any
import numpy as np

from helios_inference.domain.inference_models import EnvironmentalInferenceState

logger = logging.getLogger(__name__)


class EnvironmentalBrain:
    """
    Analytical engine for evaluating the environmental conditions of the habitat or spacecraft.
    Implements the Single Responsibility Principle (SRP).
    """

    def __init__(
        self,
        co2_threshold_mmhg: float = 3.0,
        radiation_threshold_msv: float = 600.0,
        min_pressure_kpa: float = 95.0,
        max_pressure_kpa: float = 103.0,
    ) -> None:
        """
        Initializes the environmental engine with the aerospace normative reference thresholds.

        Args:
            co2_threshold_mmhg: Upper limit for the partial pressure of cabin CO2.
            radiation_threshold_msv: Cumulative effective dose limit for an astronaut's career.
            min_pressure_kpa: Safe lower limit of cabin atmospheric pressure.
            max_pressure_kpa: Safe upper limit of cabin atmospheric pressure.
        """
        self._co2_threshold_mmhg = co2_threshold_mmhg
        self._radiation_threshold_msv = radiation_threshold_msv
        self._min_pressure_kpa = min_pressure_kpa
        self._max_pressure_kpa = max_pressure_kpa

    def process(self, environment_data: dict[str, Any]) -> tuple[np.ndarray, EnvironmentalInferenceState]:
        """
        Analyzes the cabin environmental metrics and produces the state vector in R^3.

        Args:
            environment_data: Dictionary with keys 'co2_mmHg', 'cumulative_radiation_mSv',
                              'cabin_pressure_kpa', and optionally 'solar_event_active'.

        Returns:
            Tuple containing:
            - np.ndarray: Environmental state vector with shape (3,), e.g. np.array([1.0, 0.0, 0.0]).
            - EnvironmentalInferenceState: Immutable model with the alerts and structured details.
        """
        co2 = float(environment_data.get("co2_mmHg", 1.5))
        radiation = float(environment_data.get("cumulative_radiation_mSv", 50.0))
        pressure = float(environment_data.get("cabin_pressure_kpa", 101.3))
        solar_event = bool(environment_data.get("solar_event_active", False))

        # Heuristic evaluation based on NASA standards
        co2_alert = 1.0 if co2 > self._co2_threshold_mmhg else 0.0
        radiation_alert = 1.0 if (radiation > self._radiation_threshold_msv or solar_event) else 0.0
        pressure_alert = 1.0 if (pressure < self._min_pressure_kpa or pressure > self._max_pressure_kpa) else 0.0

        environmental_vector = np.array([co2_alert, radiation_alert, pressure_alert], dtype=np.float64)

        labels: list[str] = []
        if co2_alert > 0.0:
            labels.append(f"ELEVATED_CO2_ALERT: {co2:.2f} mmHg (Limit: {self._co2_threshold_mmhg} mmHg)")
        if radiation_alert > 0.0:
            cause = "Solar Storm Active (SPE)" if solar_event else f"Career dose {radiation:.1f} mSv"
            labels.append(f"CRITICAL_RADIATION_ALERT: {cause}")
        if pressure_alert > 0.0:
            labels.append(f"ABNORMAL_CABIN_PRESSURE_ALERT: {pressure:.2f} kPa")

        if labels:
            logger.warning("Brain 1 detected environmental anomalies: %s", ", ".join(labels))
        else:
            logger.debug("Brain 1: Cabin parameters in a nominal state.")

        state = EnvironmentalInferenceState(
            environmental_vector=environmental_vector.tolist(),
            activated_labels=labels,
            co2_exceeded=(co2_alert > 0.0),
            critical_radiation=(radiation_alert > 0.0),
            abnormal_pressure=(pressure_alert > 0.0),
        )

        return environmental_vector, state
