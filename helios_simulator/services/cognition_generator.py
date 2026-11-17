"""
Psychological and cognitive telemetry generator (Brain 4 - ASTRA).

Models the interaction and crossover between environmental stressors, biological
overload and behavioral manifestations (verbal latency, stress masking and SANS).
"""

import logging
from helios_simulator.config import NasaLimitsConfig
from helios_simulator.domain.models import CognitionModel
from helios_simulator.services.math_noise import (
    evaluate_event_probability,
    generate_gaussian_noise,
    round_telemetry,
)

logger = logging.getLogger(__name__)


class CognitionGenerator:
    """
    Cognitive parameter assessment service for the ASTRA subsystem.
    Applies multivariate logical crossovers to detect fatigue and psychological strain.
    """

    def __init__(self, limits_config: NasaLimitsConfig | None = None) -> None:
        """
        Initializes the cognitive generator.

        Args:
            limits_config: Reference parameters and thresholds.
        """
        self._config = limits_config or NasaLimitsConfig()

    def generate_reading(
        self,
        co2_mmhg: float,
        sleep_hours: float,
        heart_rate_bpm: float,
        solar_event_active: bool = False,
        force_incongruence: bool = False,
    ) -> CognitionModel:
        """
        Computes psychological and verbal response metrics by crossing environment and biometrics.

        Business Rules:
            1. Voice Latency: Base 200ms. LOGICAL CROSSOVER: If co2_mmHg > 2.5 or sleep_hours < 6.0,
               spike to 600-900ms (reflects lethargy and psychomotor slowing from hypercapnia or insomnia).
            2. Lexical Density: 0.0 to 1.0. INCONGRUENCE: Occasionally simulates hidden stress
               (heart_rate > 95 but lexical_density at 0.8, "pretending to be fine").
            3. SANS Vision Symptom: Boolean, flips to True under high stress or CO2 elevation,
               reflecting the 81% prevalence in NASA astronauts per the LSAH program.

        Args:
            co2_mmhg: Current cabin CO2 concentration.
            sleep_hours: Hours slept in the last cycle.
            heart_rate_bpm: Instantaneous heart rate.
            solar_event_active: Radiological emergency flag.
            force_incongruence: Flag to activate the covert stress test.

        Returns:
            Validated CognitionModel instance.
        """
        # 1. LOGICAL CROSSOVER: Voice latency
        degradation_crossover = (
            co2_mmhg > self._config.co2_limit_7day_mmhg
            or sleep_hours < self._config.sleep_hours_risk_threshold
        )

        if degradation_crossover:
            # Latency spiked between 600 and 900 ms
            latency_val = generate_gaussian_noise(
                mean_value=750.0,
                standard_deviation=60.0,
                lower_bound=self._config.stress_voice_latency_min_ms,
                upper_bound=self._config.stress_voice_latency_max_ms,
            )
            logger.info(
                "Multivariate crossover activated: verbal latency delayed to %.1f ms (CO2: %.2f mmHg, Sleep: %.1f h)",
                latency_val,
                co2_mmhg,
                sleep_hours,
            )
        else:
            # Nominal base latency ~200 ms
            latency_val = generate_gaussian_noise(
                mean_value=self._config.base_voice_latency_ms,
                standard_deviation=25.0,
                lower_bound=140.0,
                upper_bound=280.0,
            )

        # 2. INCONGRUENCE: Hidden stress vs lexical density
        is_stress_rate = heart_rate_bpm > self._config.heart_rate_high_stress_threshold_bpm
        trigger_incongruence = force_incongruence or (
            is_stress_rate and evaluate_event_probability(self._config.stress_incongruence_probability)
        )

        if trigger_incongruence:
            # Feigning composure: artificially high lexical density (0.80) despite tachycardia
            density_val = generate_gaussian_noise(0.80, 0.02, 0.75, 0.85)
            incongruence_active = True
            logger.warning(
                "Cognitive incongruence detected: Elevated heart rate (%.1f bpm) with feigned lexical density (%.2f)",
                heart_rate_bpm,
                density_val,
            )
        else:
            incongruence_active = False
            if is_stress_rate or degradation_crossover:
                # Under evident stress, lexical richness usually contracts (0.35 - 0.55)
                density_val = generate_gaussian_noise(0.45, 0.08, 0.20, 0.60)
            else:
                # Normal balanced state (0.60 - 0.72)
                density_val = generate_gaussian_noise(0.65, 0.05, 0.40, 0.85)

        # 3. SANS Vision Symptom (Spaceflight-Associated Neuro-ocular Syndrome)
        # 81% of astronauts per the LSAH program under stress/hypercapnia/fluid shift conditions
        high_stress_condition = (
            co2_mmhg >= self._config.co2_symptom_threshold_mmhg
            or solar_event_active
            or heart_rate_bpm >= self._config.heart_rate_high_stress_threshold_bpm
            or latency_val >= 600.0
        )

        if high_stress_condition:
            # 81% empirical probability of symptomatic manifestation per LSAH
            sans_active = evaluate_event_probability(
                self._config.historical_sans_prevalence_lsah_pct / 100.0
            )
        else:
            # Under stable baseline conditions, probability is very low
            sans_active = evaluate_event_probability(0.08)

        return CognitionModel(
            voice_latency_ms=round_telemetry(latency_val, 1),
            lexical_density_score=round_telemetry(density_val, 2),
            hidden_stress_incongruence=incongruence_active,
            sans_vision_symptom=sans_active,
        )
