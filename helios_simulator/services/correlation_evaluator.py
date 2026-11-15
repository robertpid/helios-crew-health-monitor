"""
Preliminary assessment and synergistic RIDGE hazard correlation service.

Analyzes the cross interactions between Environment, Biometrics and Cognition,
emitting normative alerts that cite NASA standards directly.
"""

import logging
from helios_simulator.config import NasaLimitsConfig
from helios_simulator.domain.enums import AlertLevel, RidgeHazard
from helios_simulator.domain.models import (
    BiometricsModel,
    CognitionModel,
    EnvironmentModel,
    PreliminaryAssessmentAlert,
)

logger = logging.getLogger(__name__)


class CorrelationEvaluatorService:
    """
    Analytical rules engine for early risk detection and preliminary
    assessments in deep space life support.
    """

    def __init__(self, limits_config: NasaLimitsConfig | None = None) -> None:
        """
        Initializes the correlation evaluator.

        Args:
            limits_config: Aerospace normative parameters.
        """
        self._config = limits_config or NasaLimitsConfig()

    def evaluate_systemic_state(
        self,
        environment: EnvironmentModel,
        biometrics: BiometricsModel,
        cognition: CognitionModel,
    ) -> list[PreliminaryAssessmentAlert]:
        """
        Runs the preliminary assessment matrix crossing the 5 RIDGE hazards.

        Args:
            environment: Environmental sensor data.
            biometrics: Physiological parameters of the crew member.
            cognition: Behavioral and cognitive indicators.

        Returns:
            List of active alerts and preliminary assessments.
        """
        alerts: list[PreliminaryAssessmentAlert] = []

        # 1. CO2 assessment (NASA-STD-3001 [V2 6004])
        if environment.co2_mmHg > self._config.co2_max_limit_nasa_v2_6004_mmhg:
            alerts.append(
                PreliminaryAssessmentAlert(
                    code="ALERT-CO2-MAX-V2-6004",
                    level=AlertLevel.CRITICAL,
                    ridge_hazard=RidgeHazard.E_CLOSED_ENVIRONMENT,
                    reference_standard="NASA-STD-3001 Vol.2 [V2 6004]",
                    description=(
                        f"CO2 concentration ({environment.co2_mmHg} mmHg) exceeds the normative limit "
                        f"of 3.0 mmHg. Imminent risk of headache and operational lethargy."
                    ),
                    multivariate_crossover=False,
                )
            )
        elif environment.co2_mmHg > self._config.co2_limit_7day_mmhg:
            alerts.append(
                PreliminaryAssessmentAlert(
                    code="ALERT-CO2-ELEVATED-TB004",
                    level=AlertLevel.CAUTION,
                    ridge_hazard=RidgeHazard.E_CLOSED_ENVIRONMENT,
                    reference_standard="NASA OCHMO-TB-004",
                    description=(
                        f"CO2 at {environment.co2_mmHg} mmHg exceeds the 7-day safety threshold (2.5 mmHg). "
                        f"Symptoms reported on the ISS from 2.3 mmHg onward."
                    ),
                    multivariate_crossover=False,
                )
            )

        # 2. Cabin atmospheric pressure assessment (NASA-STD-3001 [V2 6006])
        if (
            environment.cabin_pressure_kpa < self._config.cabin_pressure_min_kpa
            or environment.cabin_pressure_kpa > self._config.cabin_pressure_max_kpa
        ):
            alerts.append(
                PreliminaryAssessmentAlert(
                    code="ALERT-CABIN-PRESSURE-V2-6006",
                    level=AlertLevel.WARNING,
                    ridge_hazard=RidgeHazard.E_CLOSED_ENVIRONMENT,
                    reference_standard="NASA-STD-3001 Vol.2 [V2 6006]",
                    description=(
                        f"Cabin pressure ({environment.cabin_pressure_kpa} kPa) outside the standard "
                        f"operating interval (95.0 - 103.0 kPa)."
                    ),
                    multivariate_crossover=False,
                )
            )

        # 3. Radiation assessment (NASA-STD-3001 [V1 4030])
        if environment.solar_event_active:
            alerts.append(
                PreliminaryAssessmentAlert(
                    code="ALERT-SPE-SOLAR-EVENT-V1-4030",
                    level=AlertLevel.CRITICAL,
                    ridge_hazard=RidgeHazard.R_RADIATION,
                    reference_standard="NASA-STD-3001 Vol.1 [V1 4030]",
                    description=(
                        f"Solar storm / SPE detected. Sudden dose injected (+20 mSv). "
                        f"Per-event limit: <250 mSv. Current cumulative dose: {environment.cumulative_radiation_mSv} mSv."
                    ),
                    multivariate_crossover=False,
                )
            )

        # 4. Circadian fatigue and sleep assessment (HSRB / The Lancet Neurology 2014)
        if biometrics.fatigue_risk_alert:
            alerts.append(
                PreliminaryAssessmentAlert(
                    code="ALERT-CHRONIC-FATIGUE-HSRB",
                    level=AlertLevel.WARNING,
                    ridge_hazard=RidgeHazard.I_ISOLATION,
                    reference_standard="NASA HSRB & The Lancet Neurology (2014)",
                    description=(
                        f"Severe fatigue risk activated: {biometrics.consecutive_insufficient_sleep_cycles} "
                        f"consecutive cycles with sleep under 6.0 hours (last: {biometrics.last_cycle_sleep_hours}h)."
                    ),
                    multivariate_crossover=False,
                )
            )

        # 5. Multivariate crossover: Verbal latency from factor synergy (CO2 + Sleep)
        if cognition.voice_latency_ms >= self._config.stress_voice_latency_min_ms:
            reasons = []
            if environment.co2_mmHg > self._config.co2_limit_7day_mmhg:
                reasons.append(f"CO2 {environment.co2_mmHg} mmHg")
            if biometrics.last_cycle_sleep_hours < self._config.sleep_hours_risk_threshold:
                reasons.append(f"sleep deficit {biometrics.last_cycle_sleep_hours}h")

            cause_str = " and ".join(reasons) if reasons else "multimodal stress"
            alerts.append(
                PreliminaryAssessmentAlert(
                    code="ALERT-COGNITIVE-LATENCY-CROSSOVER",
                    level=AlertLevel.WARNING,
                    ridge_hazard=RidgeHazard.D_DISTANCE,
                    reference_standard="NASA OCHMO-TB-004 & ASTRA Protocol",
                    description=(
                        f"Cognitive slowing detected: verbal latency at {cognition.voice_latency_ms} ms "
                        f"(normal: ~200 ms). Triggered by the synergistic crossover of {cause_str}."
                    ),
                    multivariate_crossover=True,
                )
            )

        # 6. Cognitive incongruence: Hidden stress
        if cognition.hidden_stress_incongruence:
            alerts.append(
                PreliminaryAssessmentAlert(
                    code="ALERT-STRESS-INCONGRUENCE-ASTRA",
                    level=AlertLevel.CAUTION,
                    ridge_hazard=RidgeHazard.I_ISOLATION,
                    reference_standard="ASTRA Psychometric Model (NASA Edge AI)",
                    description=(
                        f"Psychophysiological dissociation: elevated heart rate ({biometrics.heart_rate_bpm} bpm) "
                        f"with sustained lexical density ({cognition.lexical_density_score}), indicating voluntary stress masking."
                    ),
                    multivariate_crossover=True,
                )
            )

        # 7. SANS: Neuro-ocular syndrome (NASA LSAH)
        if cognition.sans_vision_symptom:
            alerts.append(
                PreliminaryAssessmentAlert(
                    code="ALERT-SANS-VISION-SYMPTOM",
                    level=AlertLevel.WARNING,
                    ridge_hazard=RidgeHazard.G_GRAVITY,
                    reference_standard="NASA Lifetime Surveillance of Astronaut Health (LSAH 2026)",
                    description=(
                        "SANS neuro-ocular symptoms reported (blurred vision / headache). "
                        "Correlated with cephalic fluid shift (1000-1500 ml) and systemic stress."
                    ),
                    multivariate_crossover=True,
                )
            )

        return alerts
