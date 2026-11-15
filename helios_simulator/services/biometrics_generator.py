"""
Physiological biometrics telemetry generator (Brain 2).

Models the hemodynamic response, circadian sleep cycles and bone mass loss from
musculoskeletal deconditioning per NASA studies.
"""

import logging
from helios_simulator.config import NasaLimitsConfig
from helios_simulator.domain.models import BiometricsModel
from helios_simulator.services.math_noise import (
    compute_cumulative_bone_loss,
    evaluate_event_probability,
    generate_gaussian_noise,
    round_telemetry,
)

logger = logging.getLogger(__name__)


class BiometricsGenerator:
    """
    Astronaut physiological modeling service.
    Tracks continuous circadian cycles and bone demineralization.
    """

    def __init__(
        self,
        limits_config: NasaLimitsConfig | None = None,
        initial_mission_day: int = 120,
    ) -> None:
        """
        Initializes the biomedical generator.

        Args:
            limits_config: Normative parameters and biological thresholds.
            initial_mission_day: Current day of the deep space expedition.
        """
        self._config = limits_config or NasaLimitsConfig()
        self._mission_day = initial_mission_day
        self._insufficient_cycles = 0
        self._current_sleep_hours = 6.0
        self._cycle_sample_counter = 0

    def simulate_new_sleep_cycle(self, hours_slept: float) -> None:
        """
        Records the completion of a circadian sleep cycle to update fatigue.

        Args:
            hours_slept: Duration recorded by the smart actigraph.
        """
        self._current_sleep_hours = hours_slept
        if hours_slept < self._config.sleep_hours_risk_threshold:
            self._insufficient_cycles += 1
            logger.warning(
                "Insufficient rest cycle detected (%.1fh < %.1fh). Cumulative cycles: %d",
                hours_slept,
                self._config.sleep_hours_risk_threshold,
                self._insufficient_cycles,
            )
        else:
            self._insufficient_cycles = max(0, self._insufficient_cycles - 1)

    def generate_reading(
        self,
        environmental_stress: bool = False,
        force_sleep_deficit: bool = False,
        force_tachycardia: bool = False,
    ) -> BiometricsModel:
        """
        Produces an instantaneous vital signs reading.

        Args:
            environmental_stress: Indicates hostile environmental conditions (high CO2 or Solar Storm).
            force_sleep_deficit: Forces accumulation of sleep < 6.0h.
            force_tachycardia: Forces an elevated heart rate (> 95 bpm).

        Returns:
            Validated BiometricsModel instance.
        """
        self._cycle_sample_counter += 1

        # Simulates alternating or persistent sleep cycles (e.g. every 15 samples the cycle advances or fluctuates)
        if self._cycle_sample_counter % 15 == 0 or force_sleep_deficit:
            if force_sleep_deficit:
                simulated_hours = generate_gaussian_noise(5.2, 0.4, 4.0, 5.8)
            else:
                # The Lancet Neurology study (2014): average ~6h per night
                simulated_hours = generate_gaussian_noise(
                    mean_value=self._config.average_sleep_hours,
                    standard_deviation=0.9,
                    lower_bound=4.2,
                    upper_bound=8.0,
                )
            self.simulate_new_sleep_cycle(simulated_hours)

        # 1. Heart rate (heart_rate_bpm): Base 65 +/- 5 bpm
        rate_mean = self._config.base_heart_rate_bpm
        if environmental_stress:
            rate_mean += 18.0
        if force_tachycardia:
            rate_mean = 98.0

        rate_val = generate_gaussian_noise(
            mean_value=rate_mean,
            standard_deviation=self._config.heart_rate_deviation_bpm,
            lower_bound=50.0,
            upper_bound=130.0,
        )

        # 2. Fatigue risk alert flag (if it drops below 6h for 3 cycles)
        fatigue_alert = self._insufficient_cycles >= self._config.consecutive_sleep_for_alert

        # 3. Cumulative bone loss (bone_loss_pct): (mission_day / 30) * 1.5%
        bone_loss = compute_cumulative_bone_loss(
            mission_day=self._mission_day,
            monthly_rate_pct=self._config.monthly_bone_loss_rate_pct,
        )

        # 4. Complementary hemodynamic parameters (Blood pressure and SpO2)
        base_systolic = 120.0 + (12.0 if environmental_stress or rate_val > 90 else 0.0)
        systolic = generate_gaussian_noise(base_systolic, 4.0, 100.0, 160.0)
        diastolic = generate_gaussian_noise(systolic * 0.65, 3.0, 60.0, 95.0)

        spo2 = generate_gaussian_noise(98.2, 0.6, 94.0, 100.0)

        # 5. Bio-Monitor / Astroskin smart garment sensors (CSA)
        skin_temp = generate_gaussian_noise(34.8 + (0.5 if environmental_stress else 0.0), 0.3, 33.0, 37.0)
        resp_rate = generate_gaussian_noise(14.0 + (3.5 if environmental_stress else 0.0), 1.2, 10.0, 26.0)
        # HRV (heart rate variability): physiologically decreases under stress
        hrv_ms = generate_gaussian_noise(42.0 - (15.0 if environmental_stress or rate_val > 90 else 0.0), 4.0, 15.0, 75.0)

        headache = environmental_stress and evaluate_event_probability(0.40)
        physical_activity = generate_gaussian_noise(120.0, 15.0, 45.0, 150.0)
        stress_scale = min(10, max(1, int(3 + (4 if environmental_stress else 0) + (2 if fatigue_alert else 0))))

        return BiometricsModel(
            heart_rate_bpm=round_telemetry(rate_val, 1),
            last_cycle_sleep_hours=round_telemetry(self._current_sleep_hours, 2),
            consecutive_insufficient_sleep_cycles=self._insufficient_cycles,
            fatigue_risk_alert=fatigue_alert,
            bone_loss_pct=round_telemetry(bone_loss, 2),
            systolic_pressure_mmHg=round_telemetry(systolic, 1),
            diastolic_pressure_mmHg=round_telemetry(diastolic, 1),
            spo2_pct=round_telemetry(spo2, 1),
            skin_temperature_c=round_telemetry(skin_temp, 2),
            respiratory_rate_rpm=round_telemetry(resp_rate, 1),
            heart_rate_variability_hrv_ms=round_telemetry(hrv_ms, 1),
            headache_symptom=headache,
            physical_activity_minutes=round_telemetry(physical_activity, 1),
            self_reported_stress_scale=stress_scale,
        )
