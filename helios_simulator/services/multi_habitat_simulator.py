"""
Analytical multi-habitat simulator for 120-day time series.

Generates vectorized synthetic telemetry with NumPy and Pandas for 4 mission environments:
1. International Space Station (ISS / LEO)
2. Lunar Base (Artemis Base Camp)
3. Transit Spacecraft (Deep Space Transit to Mars)
4. Mars Surface Base (Martian Habitat)

Complies with NASA-STD-3001 standards, the RIDGE framework and Clean Code principles.
Calculations are 100% vectorized with no iterrows() or itertuples().
"""

from pathlib import Path
import logging
import numpy as np
import pandas as pd

from helios_simulator.config import (
    MissionEnvironmentProfile,
    NasaLimitsConfig,
    get_environment_profiles,
)
from helios_simulator.domain.enums import MissionEnvironment

logger = logging.getLogger(__name__)


class MultiHabitat120DaySimulator:
    """Vector simulation engine for 120-day multivariate time series."""

    def __init__(
        self,
        limits_config: NasaLimitsConfig | None = None,
        random_seed: int | None = 42,
    ) -> None:
        self._limits_config = limits_config or NasaLimitsConfig()
        self._profiles = get_environment_profiles()
        if random_seed is not None:
            np.random.seed(random_seed)

    def simulate_habitat(
        self,
        environment_type: MissionEnvironment | str,
        total_days: int = 120,
    ) -> pd.DataFrame:
        """Generates the telemetry DataFrame for a specific habitat (120 days)."""
        key = environment_type.value if isinstance(environment_type, MissionEnvironment) else str(environment_type)
        if key not in self._profiles:
            raise ValueError(f"Unrecognized habitat: '{key}'. Valid: {list(self._profiles.keys())}")

        profile: MissionEnvironmentProfile = self._profiles[key]
        logger.info("Simulating %d days for '%s' (g=%.3f)...", total_days, profile.display_name, profile.gravity_g)
        days = np.arange(1, total_days + 1, dtype=np.int32)

        # BRAIN 1: ENVIRONMENT
        co2_peak_mask = np.random.uniform(0.0, 1.0, size=total_days) < 0.10
        co2_nominal = np.clip(np.random.normal(1.60, 0.22, size=total_days), self._limits_config.co2_normal_min_mmhg, self._limits_config.co2_normal_max_mmhg)
        co2_peaks = np.clip(np.random.normal(3.45, 0.28, size=total_days), 3.05, 4.60)
        co2_mmhg = np.where(co2_peak_mask, co2_peaks, co2_nominal).round(2)

        solar_storm_mask = np.random.uniform(0.0, 1.0, size=total_days) < profile.solar_storm_probability
        rad_rate = np.clip(np.random.normal(profile.base_daily_radiation_msv, profile.radiation_deviation_msv, size=total_days), 0.10, 3.50)
        solar_impact = np.where(solar_storm_mask, self._limits_config.solar_storm_radiation_impact_msv, 0.0)
        total_daily_dose = (rad_rate + solar_impact).round(3)
        initial_base_radiation = 15.0 if key == "space_station" else 45.0
        cumulative_radiation_msv = (initial_base_radiation + np.cumsum(total_daily_dose)).round(2)

        cabin_pressure_kpa = np.clip(np.random.normal(profile.cabin_pressure_nominal_kpa, 0.85, size=total_days), profile.cabin_pressure_min_kpa, profile.cabin_pressure_max_kpa).round(2)
        cabin_temperature_c = np.random.normal(profile.cabin_temperature_nominal_c, 0.60, size=total_days).round(2)
        relative_humidity_pct = np.clip(np.random.normal(46.0, 2.5, size=total_days), 35.0, 65.0).round(1)

        # BRAIN 2: PHYSIOLOGICAL BIOMETRICS
        gravity_attenuation_factor = max(0.0, 1.0 - profile.gravity_g)
        bone_loss_pct = ((days / 30.0) * (self._limits_config.monthly_bone_loss_rate_pct * gravity_attenuation_factor)).round(2)

        martian_drift = 0.65 if key == "mars_base" else 0.0
        sleep_mean = np.maximum(4.8, self._limits_config.average_sleep_hours - (0.003 * days * martian_drift))
        sleep_hours = np.clip(np.random.normal(sleep_mean, 0.95, size=total_days), 3.8, 8.5).round(2)

        insufficient_sleep_series = pd.Series(sleep_hours < self._limits_config.sleep_hours_risk_threshold)
        fatigue_alert_series = (insufficient_sleep_series.rolling(window=3, min_periods=1).sum() >= 3.0)

        consecutive_counter = np.zeros(total_days, dtype=np.int32)
        running_counter = 0
        for idx, deficit in enumerate(insufficient_sleep_series.to_numpy()):
            running_counter = (running_counter + 1) if deficit else max(0, running_counter - 1)
            consecutive_counter[idx] = running_counter

        elevated_stress = (co2_mmhg >= self._limits_config.co2_symptom_threshold_mmhg) | solar_storm_mask | fatigue_alert_series.to_numpy()
        acute_stress_peaks = np.random.uniform(0.0, 1.0, size=total_days) < (0.08 * profile.isolation_stress_factor)
        hr_shift = np.where(elevated_stress | acute_stress_peaks, 26.0, 0.0)
        heart_rate_bpm = np.clip(np.random.normal(self._limits_config.base_heart_rate_bpm + hr_shift, 6.5, size=total_days), 52.0, 135.0).round(1)

        tachycardia_mask = heart_rate_bpm > self._limits_config.heart_rate_high_stress_threshold_bpm
        systolic_pressure = (118.0 + (heart_rate_bpm - 65.0) * 0.45 + np.random.normal(0, 2.5, size=total_days)).round(1)
        diastolic_pressure = (systolic_pressure * 0.65 + np.random.normal(0, 1.8, size=total_days)).round(1)
        spo2_pct = np.clip(np.random.normal(98.1, 0.5, size=total_days), 93.0, 99.8).round(1)

        skin_temperature_c = np.clip(34.8 + np.where(elevated_stress, 0.5, 0.0) + np.random.normal(0, 0.25, size=total_days), 33.2, 37.2).round(2)
        respiratory_rate_rpm = np.clip(14.0 + np.where(elevated_stress, 3.5, 0.0) + np.random.normal(0, 1.0, size=total_days), 10.0, 28.0).round(1)
        heart_rate_variability_hrv_ms = np.clip(44.0 - np.where(elevated_stress | tachycardia_mask, 16.0, 0.0) + np.random.normal(0, 3.5, size=total_days), 14.0, 75.0).round(1)
        headache_symptom = np.random.uniform(0.0, 1.0, size=total_days) < np.where(elevated_stress, 0.45, 0.04)
        physical_activity_minutes = np.clip(np.random.normal(120.0, 12.0, size=total_days), 45.0, 150.0).round(1)
        stress_scale = np.clip(3 + np.where(elevated_stress, 4, 0) + np.where(fatigue_alert_series.to_numpy(), 2, 0) + np.random.randint(-1, 2, size=total_days), 1, 10).astype(int)

        # BRAIN 4: PSYCHOLOGY AND COGNITION (ASTRA)
        degradation_crossover = (co2_mmhg > self._limits_config.co2_limit_7day_mmhg) | (sleep_hours < self._limits_config.sleep_hours_risk_threshold)
        lat_nom = np.clip(np.random.normal(self._limits_config.base_voice_latency_ms, 22.0, size=total_days), 150.0, 280.0)
        lat_stress = np.clip(np.random.normal(740.0, 55.0, size=total_days), self._limits_config.stress_voice_latency_min_ms, self._limits_config.stress_voice_latency_max_ms)
        voice_latency_ms = np.where(degradation_crossover, lat_stress, lat_nom).round(1)

        incongruence_mask = tachycardia_mask & (np.random.uniform(0.0, 1.0, size=total_days) < 0.40)
        dens_nom = np.random.normal(0.66, 0.05, size=total_days)
        dens_stress = np.random.normal(0.44, 0.07, size=total_days)
        dens_feigned = np.random.normal(0.80, 0.02, size=total_days)
        lexical_density = np.where(incongruence_mask, dens_feigned, np.where(degradation_crossover | tachycardia_mask, dens_stress, dens_nom))
        lexical_density_score = np.clip(lexical_density, 0.15, 0.95).round(2)

        sans_prob = 0.81 * profile.sans_prevalence_factor
        sans_condition = degradation_crossover | tachycardia_mask | solar_storm_mask
        sans_roll = np.random.uniform(0.0, 1.0, size=total_days)
        sans_vision_symptom = np.where(sans_condition, sans_roll < sans_prob, sans_roll < (0.05 * profile.sans_prevalence_factor))

        # NORMATIVE ALERTS AND BUDGET
        co2_alert = co2_mmhg > self._limits_config.co2_max_limit_nasa_v2_6004_mmhg
        radiation_alert = solar_storm_mask
        fatigue_alert = fatigue_alert_series.to_numpy()
        latency_alert = voice_latency_ms >= self._limits_config.stress_voice_latency_min_ms
        sans_alert = sans_vision_symptom
        total_daily_alerts = co2_alert.astype(int) + radiation_alert.astype(int) + fatigue_alert.astype(int) + latency_alert.astype(int) + sans_alert.astype(int)
        radiation_budget_pct = ((cumulative_radiation_msv / self._limits_config.career_radiation_limit_msv) * 100.0).round(2)

        return pd.DataFrame({
            "mission_day": days, "mission_environment": key, "habitat_name": profile.display_name,
            "gravity_g": profile.gravity_g, "sol_duration_h": profile.cycle_duration_hours,
            "earth_delay_min": round(profile.earth_comm_latency_seconds / 60.0, 2),
            "co2_mmHg": co2_mmhg, "daily_radiation_rate_mSv": total_daily_dose,
            "cumulative_radiation_mSv": cumulative_radiation_msv, "solar_event_active": solar_storm_mask,
            "cabin_pressure_kpa": cabin_pressure_kpa, "cabin_temperature_c": cabin_temperature_c,
            "relative_humidity_pct": relative_humidity_pct, "heart_rate_bpm": heart_rate_bpm,
            "heart_rate_variability_hrv_ms": heart_rate_variability_hrv_ms, "respiratory_rate_rpm": respiratory_rate_rpm,
            "skin_temperature_c": skin_temperature_c, "sleep_hours": sleep_hours,
            "consecutive_insufficient_sleep_cycles": consecutive_counter, "fatigue_risk_alert": fatigue_alert,
            "bone_loss_pct": bone_loss_pct, "systolic_pressure_mmHg": systolic_pressure,
            "diastolic_pressure_mmHg": diastolic_pressure, "spo2_pct": spo2_pct,
            "headache_symptom": headache_symptom, "physical_activity_minutes": physical_activity_minutes,
            "self_reported_stress_scale": stress_scale, "voice_latency_ms": voice_latency_ms,
            "lexical_density_score": lexical_density_score, "hidden_stress_incongruence": incongruence_mask,
            "sans_vision_symptom": sans_vision_symptom, "total_active_alerts": total_daily_alerts,
            "critical_co2_alert": co2_alert, "spe_radiation_alert": radiation_alert,
            "chronic_fatigue_alert": fatigue_alert, "latency_crossover_alert": latency_alert,
            "sans_alert_active": sans_alert, "career_radiation_budget_pct": radiation_budget_pct,
        })

    def simulate_all_habitats(self, total_days: int = 120) -> pd.DataFrame:
        """Consolidates the simulations of the 4 habitats into a single 480-record DataFrame."""
        frames = [self.simulate_habitat(key, total_days=total_days) for key in self._profiles.keys()]
        master_df = pd.concat(frames, ignore_index=True)
        logger.info("Consolidated simulation finished. Total records: %d", len(master_df))
        return master_df

    def generate_comparative_summary(self, master_df: pd.DataFrame) -> pd.DataFrame:
        """Generates a summary table with vectorized statistical aggregations comparing environments."""
        return (
            master_df.groupby("mission_environment")
            .agg(
                gravity_g=("gravity_g", "first"),
                earth_delay_min=("earth_delay_min", "first"),
                final_radiation_mSv=("cumulative_radiation_mSv", "max"),
                final_radiation_budget_pct=("career_radiation_budget_pct", "max"),
                total_solar_storms=("solar_event_active", "sum"),
                final_bone_loss_pct=("bone_loss_pct", "max"),
                mean_co2_mmHg=("co2_mmHg", "mean"),
                days_with_fatigue_alert=("fatigue_risk_alert", "sum"),
                mean_voice_latency_ms=("voice_latency_ms", "mean"),
                days_with_sans_vision=("sans_vision_symptom", "sum"),
                days_with_stress_incongruence=("hidden_stress_incongruence", "sum"),
            )
            .round(2)
        )

    def export_dataset(
        self,
        df: pd.DataFrame,
        target_directory: str | Path = "generated_data",
        base_name: str = "telemetry_120_days_four_habitats",
    ) -> dict[str, Path]:
        """Exports the dataset to CSV, Parquet and JSONL formats."""
        dir_path = Path(target_directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        csv_path, parquet_path, jsonl_path = dir_path / f"{base_name}.csv", dir_path / f"{base_name}.parquet", dir_path / f"{base_name}.jsonl"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        df.to_parquet(parquet_path, index=False, engine="pyarrow")
        df.to_json(jsonl_path, orient="records", lines=True, date_format="iso")
        logger.info("Dataset exported to CSV, Parquet and JSONL in %s", dir_path)
        return {"csv": csv_path, "parquet": parquet_path, "jsonl": jsonl_path}
