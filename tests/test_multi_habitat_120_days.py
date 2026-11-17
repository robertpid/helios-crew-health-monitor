"""
Automated tests for the 120-day multi-habitat simulator.

Verifies the generation of the 120-day time series for:
Space Station, Lunar Base, Spacecraft and Mars Base.
Validates biomechanical computations (gravity-weighted bone loss), dosimetry and logical crossovers.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from helios_simulator.config import NasaLimitsConfig
from helios_simulator.domain.enums import MissionEnvironment
from helios_simulator.services.multi_habitat_simulator import MultiHabitat120DaySimulator


@pytest.fixture
def simulator() -> MultiHabitat120DaySimulator:
    """Fixture providing a reproducible instance of the simulator."""
    return MultiHabitat120DaySimulator(
        limits_config=NasaLimitsConfig(),
        random_seed=42,
    )


def test_120_day_generation_single_habitat(simulator: MultiHabitat120DaySimulator) -> None:
    """Verifies that simulating one habitat produces exactly 120 daily observations."""
    df_iss = simulator.simulate_habitat(MissionEnvironment.SPACE_STATION, total_days=120)

    assert isinstance(df_iss, pd.DataFrame)
    assert len(df_iss) == 120
    assert df_iss["mission_day"].tolist() == list(range(1, 121))
    assert (df_iss["mission_environment"] == "space_station").all()
    assert (df_iss["gravity_g"] == 0.0).all()


def test_consolidated_generation_four_habitats(simulator: MultiHabitat120DaySimulator) -> None:
    """Verifies the generation of the master table with 4 habitats (480 total rows)."""
    master_df = simulator.simulate_all_habitats(total_days=120)

    assert len(master_df) == 480  # 4 habitats x 120 days
    expected_habitats = {"space_station", "lunar_base", "spacecraft", "mars_base"}
    assert set(master_df["mission_environment"].unique()) == expected_habitats

    # Required column check
    mandatory_columns = [
        "mission_day", "mission_environment", "gravity_g",
        "co2_mmHg", "daily_radiation_rate_mSv", "cumulative_radiation_mSv",
        "cabin_pressure_kpa", "cabin_temperature_c", "relative_humidity_pct",
        "heart_rate_bpm", "heart_rate_variability_hrv_ms", "respiratory_rate_rpm",
        "skin_temperature_c", "sleep_hours", "fatigue_risk_alert", "bone_loss_pct",
        "systolic_pressure_mmHg", "diastolic_pressure_mmHg", "spo2_pct",
        "headache_symptom", "physical_activity_minutes", "self_reported_stress_scale",
        "voice_latency_ms", "lexical_density_score", "hidden_stress_incongruence", "sans_vision_symptom",
        "total_active_alerts", "career_radiation_budget_pct",
    ]
    for col in mandatory_columns:
        assert col in master_df.columns, f"Missing required column: {col}"


def test_gravity_weighted_bone_loss(simulator: MultiHabitat120DaySimulator) -> None:
    """
    Validates the cumulative bone loss at Day 120 per the gravity vector:
    - ISS (0g): 6.0%
    - Spacecraft (0g): 6.0%
    - Moon (0.166g): ~5.0%
    - Mars (0.38g): ~3.72%
    """
    df_iss = simulator.simulate_habitat(MissionEnvironment.SPACE_STATION, total_days=120)
    df_moon = simulator.simulate_habitat(MissionEnvironment.LUNAR_BASE, total_days=120)
    df_craft = simulator.simulate_habitat(MissionEnvironment.SPACECRAFT, total_days=120)
    df_mars = simulator.simulate_habitat(MissionEnvironment.MARS_BASE, total_days=120)

    iss_loss_day_120 = df_iss.loc[df_iss["mission_day"] == 120, "bone_loss_pct"].values[0]
    craft_loss_day_120 = df_craft.loc[df_craft["mission_day"] == 120, "bone_loss_pct"].values[0]
    moon_loss_day_120 = df_moon.loc[df_moon["mission_day"] == 120, "bone_loss_pct"].values[0]
    mars_loss_day_120 = df_mars.loc[df_mars["mission_day"] == 120, "bone_loss_pct"].values[0]

    assert iss_loss_day_120 == 6.00
    assert craft_loss_day_120 == 6.00
    assert pytest.approx(moon_loss_day_120, abs=0.05) == 5.00
    assert pytest.approx(mars_loss_day_120, abs=0.05) == 3.72


def test_radiation_gradient_between_habitats(simulator: MultiHabitat120DaySimulator) -> None:
    """Verifies that the cumulative 120-day exposure reflects the real radiological profiles."""
    master_df = simulator.simulate_all_habitats(total_days=120)
    summary = simulator.generate_comparative_summary(master_df)

    rad_iss = summary.loc["space_station", "final_radiation_mSv"]
    rad_craft = summary.loc["spacecraft", "final_radiation_mSv"]
    rad_mars = summary.loc["mars_base", "final_radiation_mSv"]

    # The deep space craft (GCR with no atmosphere or shield) accumulates substantially more radiation than the ISS
    assert rad_craft > rad_iss
    # The Mars surface has partial protection from the planet body vs interplanetary space
    assert rad_craft > rad_mars


def test_vectorized_verbal_latency_crossover(simulator: MultiHabitat120DaySimulator) -> None:
    """Validates that when CO2 > 2.5 or sleep_hours < 6.0, the verbal latency falls in 600-900ms."""
    master_df = simulator.simulate_all_habitats(total_days=120)

    # Degraded rows
    degraded_mask = (master_df["co2_mmHg"] > 2.5) | (master_df["sleep_hours"] < 6.0)
    degraded_latencies = master_df.loc[degraded_mask, "voice_latency_ms"]
    assert (degraded_latencies >= 600.0).all()
    assert (degraded_latencies <= 900.0).all()

    # Nominal rows
    nominal_mask = (master_df["co2_mmHg"] <= 2.5) & (master_df["sleep_hours"] >= 6.0)
    nominal_latencies = master_df.loc[nominal_mask, "voice_latency_ms"]
    assert (nominal_latencies < 300.0).all()


def test_hidden_stress_incongruence(simulator: MultiHabitat120DaySimulator) -> None:
    """Validates the detection of covert stress (tachycardia > 95 bpm with lexical density >= 0.75)."""
    master_df = simulator.simulate_all_habitats(total_days=120)

    incongruences = master_df.loc[master_df["hidden_stress_incongruence"] == True]
    assert len(incongruences) > 0  # It must have occurred at least once across 480 simulated days
    assert (incongruences["heart_rate_bpm"] > 95.0).all()
    assert (incongruences["lexical_density_score"] >= 0.75).all()


def test_dataset_export(simulator: MultiHabitat120DaySimulator, tmp_path: Path) -> None:
    """Validates that the exporters generate valid CSV, Parquet and JSONL files."""
    master_df = simulator.simulate_all_habitats(total_days=120)
    paths = simulator.export_dataset(
        df=master_df,
        target_directory=tmp_path,
        base_name="test_120_days",
    )

    assert paths["csv"].exists()
    assert paths["parquet"].exists()
    assert paths["jsonl"].exists()

    # Verification read
    df_csv = pd.read_csv(paths["csv"])
    df_parquet = pd.read_parquet(paths["parquet"])
    assert len(df_csv) == 480
    assert len(df_parquet) == 480
