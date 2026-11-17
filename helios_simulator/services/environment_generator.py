"""
Environmental telemetry generator (Brain 1).

Applies physical and stochastic rules based on NASA-STD-3001 Vol. 2 for carbon
dioxide, cabin pressure and galactic and solar cosmic radiation dosimetry.
"""

import logging
from helios_simulator.config import NasaLimitsConfig
from helios_simulator.domain.models import EnvironmentModel
from helios_simulator.services.math_noise import (
    evaluate_event_probability,
    generate_gaussian_noise,
    round_telemetry,
)

logger = logging.getLogger(__name__)


class EnvironmentGenerator:
    """
    Service responsible for generating the environmental telemetry of the space cabin.
    Maintains the cumulative radiation state and models vital gas fluctuations.
    """

    def __init__(
        self,
        limits_config: NasaLimitsConfig | None = None,
        initial_mission_day: int = 120,
    ) -> None:
        """
        Initializes the environment generator.

        Args:
            limits_config: Configuration with NASA ranges and standards.
            initial_mission_day: Reference mission day (e.g. Day 120).
        """
        self._config = limits_config or NasaLimitsConfig()
        self._mission_day = initial_mission_day

        # Cumulative base dose at Day 120: base 50.0 mSv + daily increment (~0.35 mSv/day)
        average_dose_per_day = (
            self._config.daily_radiation_rate_min_msv + self._config.daily_radiation_rate_max_msv
        ) / 2.0
        self._cumulative_radiation_msv = (
            self._config.base_cumulative_radiation_msv
            + (self._mission_day * average_dose_per_day)
        )
        self._solar_storm_active = False

    def generate_reading(
        self,
        force_co2_peak: bool = False,
        force_solar_storm: bool = False,
    ) -> EnvironmentModel:
        """
        Computes a new environmental telemetry sample.

        Args:
            force_co2_peak: If True, forces a CO2 peak > 3.0 mmHg for tests or demo.
            force_solar_storm: If True, forces a Solar Storm event (+20 mSv).

        Returns:
            Validated EnvironmentModel instance.
        """
        # 1. Carbon dioxide (co2_mmHg): Normal 1.0 - 2.2 mmHg. Inject peaks > 3.0 (NASA V2 6004)
        co2_peak_probability = 0.12
        generate_peak = force_co2_peak or evaluate_event_probability(co2_peak_probability)

        if generate_peak:
            # Peak above 3.0 mmHg (NASA-STD-3001 [V2 6004] violation)
            co2_val = generate_gaussian_noise(
                mean_value=3.4,
                standard_deviation=0.3,
                lower_bound=3.05,
                upper_bound=4.5,
            )
            logger.info("Injecting anomalous cabin CO2 peak: %.2f mmHg (NASA V2 6004)", co2_val)
        else:
            # Nominal range: 1.0 - 2.2 mmHg
            co2_val = generate_gaussian_noise(
                mean_value=1.6,
                standard_deviation=0.25,
                lower_bound=self._config.co2_normal_min_mmhg,
                upper_bound=self._config.co2_normal_max_mmhg,
            )

        # 2. Cosmic and solar radiation
        # Usual daily rate in deep space / ISS: 0.2 to 0.5 mSv/day
        daily_rate_val = generate_gaussian_noise(
            mean_value=0.35,
            standard_deviation=0.08,
            lower_bound=self._config.daily_radiation_rate_min_msv,
            upper_bound=self._config.daily_radiation_rate_max_msv,
        )

        # Fractional increment per telemetry cycle
        sample_increment = daily_rate_val / (24.0 * 3600.0 / 2.0)
        self._cumulative_radiation_msv += sample_increment

        # 1% probability of a Solar Storm (+20 mSv at once)
        storm_occurred = force_solar_storm or evaluate_event_probability(
            self._config.solar_storm_probability
        )

        if storm_occurred:
            self._cumulative_radiation_msv += self._config.solar_storm_radiation_impact_msv
            self._solar_storm_active = True
            logger.warning(
                "ENVIRONMENTAL ALERT! Solar Particle Event (SPE) detected. Impact: +%.1f mSv. Cumulative: %.2f mSv",
                self._config.solar_storm_radiation_impact_msv,
                self._cumulative_radiation_msv,
            )
        else:
            self._solar_storm_active = False

        # 3. Cabin pressure (cabin_pressure_kpa): 95.0 - 103.0 kPa (NASA V2 6006)
        pressure_val = generate_gaussian_noise(
            mean_value=101.3,
            standard_deviation=1.2,
            lower_bound=self._config.cabin_pressure_min_kpa,
            upper_bound=self._config.cabin_pressure_max_kpa,
        )

        # 4. Cabin temperature
        temperature_val = generate_gaussian_noise(
            mean_value=21.5,
            standard_deviation=0.6,
            lower_bound=18.0,
            upper_bound=26.0,
        )

        # 5. Cabin relative humidity (NASA OSDR N22: 40-60%)
        humidity_val = generate_gaussian_noise(
            mean_value=46.0,
            standard_deviation=3.0,
            lower_bound=35.0,
            upper_bound=65.0,
        )

        return EnvironmentModel(
            co2_mmHg=round_telemetry(co2_val, 2),
            cumulative_radiation_mSv=round_telemetry(self._cumulative_radiation_msv, 2),
            daily_radiation_rate_mSv=round_telemetry(daily_rate_val, 3),
            cabin_pressure_kpa=round_telemetry(pressure_val, 2),
            cabin_temperature_c=round_telemetry(temperature_val, 2),
            relative_humidity_pct=round_telemetry(humidity_val, 1),
            solar_event_active=self._solar_storm_active,
        )
