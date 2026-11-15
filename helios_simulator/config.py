"""
Centralized configuration for the HELIOS simulator.

Defines operational constants, aerospace reference ranges and connection parameters
in accordance with NASA-STD-3001 and deep space mission specifications.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RedisConfig:
    """Connection configuration parameters for the Redis messaging infrastructure."""

    host: str = "127.0.0.1"
    port: int = 6379
    db: int = 0
    password: str | None = None
    publish_channel: str = "earth_telemetry_mailbox"
    publish_queue: str = "earth_telemetry_mailbox_queue"
    connection_timeout_seconds: float = 2.0
    reconnect_retry_interval_seconds: float = 3.0
    memory_buffer_queue_limit: int = 500


@dataclass(frozen=True)
class MissionConfig:
    """Parameters of the reference space mission."""

    mission_id: str = "ARES-VI-MARS-EXPEDITION"
    astronaut_id: str = "ASTRO-HELIOS-01"
    default_mission_day: int = 120
    emission_interval_seconds: float = 2.0


@dataclass(frozen=True)
class MissionEnvironmentProfile:
    """
    Parameters specific to each of the four operational mission habitats.
    Backed by radiation data (RadLab, Curiosity RAD, Chang'e 4 LND) and biomechanical models.
    """

    display_name: str
    gravity_g: float
    base_daily_radiation_msv: float
    radiation_deviation_msv: float
    solar_storm_probability: float
    cabin_pressure_nominal_kpa: float
    cabin_pressure_min_kpa: float
    cabin_pressure_max_kpa: float
    cabin_temperature_nominal_c: float
    earth_comm_latency_seconds: float
    cycle_duration_hours: float
    sans_prevalence_factor: float
    isolation_stress_factor: float


def get_environment_profiles() -> dict[str, MissionEnvironmentProfile]:
    """
    Returns the aerospace configuration profiles for the 4 analyzed environments.

    Returns:
        Dictionary with the configurations for Space Station, Lunar Base, Spacecraft and Mars Base.
    """
    return {
        "space_station": MissionEnvironmentProfile(
            display_name="International Space Station (ISS / LEO)",
            gravity_g=0.0,
            base_daily_radiation_msv=0.35,  # 0.2 to 0.5 mSv/day (Simonsen et al., 2025)
            radiation_deviation_msv=0.06,
            solar_storm_probability=0.005,  # Partially shielded by the magnetosphere
            cabin_pressure_nominal_kpa=101.3,
            cabin_pressure_min_kpa=95.0,
            cabin_pressure_max_kpa=103.0,
            cabin_temperature_nominal_c=21.5,
            earth_comm_latency_seconds=0.5,
            cycle_duration_hours=24.0,
            sans_prevalence_factor=1.0,  # 81% peak prevalence (LSAH)
            isolation_stress_factor=1.0,
        ),
        "lunar_base": MissionEnvironmentProfile(
            display_name="Lunar Base (Artemis Base Camp - Lunar Surface)",
            gravity_g=0.166,  # 1/6 g
            base_daily_radiation_msv=1.35,  # ~60 uSv/h measured by Chang'e 4 LND
            radiation_deviation_msv=0.15,
            solar_storm_probability=0.020,  # No protective magnetosphere
            cabin_pressure_nominal_kpa=70.3,   # NASA exploration atmosphere
            cabin_pressure_min_kpa=65.0,
            cabin_pressure_max_kpa=75.0,
            cabin_temperature_nominal_c=22.0,
            earth_comm_latency_seconds=1.3,  # ~1.3s one way to the Moon
            cycle_duration_hours=24.0,
            sans_prevalence_factor=0.70,  # Partial gravity relieves cephalic congestion
            isolation_stress_factor=1.2,
        ),
        "spacecraft": MissionEnvironmentProfile(
            display_name="Transit Spacecraft (Deep Space Transit to Mars)",
            gravity_g=0.0,  # Strict microgravity
            base_daily_radiation_msv=1.80,  # Curiosity RAD measurement en route to Mars (Hassler et al., 2013)
            radiation_deviation_msv=0.20,
            solar_storm_probability=0.025,  # Outside Earth's magnetosphere
            cabin_pressure_nominal_kpa=101.3,
            cabin_pressure_min_kpa=95.0,
            cabin_pressure_max_kpa=103.0,
            cabin_temperature_nominal_c=20.8,
            earth_comm_latency_seconds=900.0,  # 15 minutes at mid transit
            cycle_duration_hours=24.0,
            sans_prevalence_factor=1.0,  # 81% peak prevalence (LSAH)
            isolation_stress_factor=1.6,  # Severe confinement in deep space
        ),
        "mars_base": MissionEnvironmentProfile(
            display_name="Mars Surface Base (Martian Habitat)",
            gravity_g=0.38,  # 3/8 g
            base_daily_radiation_msv=0.67,  # Curiosity RAD surface measurement (Hassler et al., 2013)
            radiation_deviation_msv=0.08,
            solar_storm_probability=0.015,
            cabin_pressure_nominal_kpa=101.3,
            cabin_pressure_min_kpa=95.0,
            cabin_pressure_max_kpa=103.0,
            cabin_temperature_nominal_c=21.0,
            earth_comm_latency_seconds=1200.0,  # 20+ minutes of delay (Hazard D)
            cycle_duration_hours=24.65,  # Martian sol: 24h 39min (circadian desynchronization)
            sans_prevalence_factor=0.55,  # Martian gravity reduces the fluid gradient
            isolation_stress_factor=1.4,
        ),
    }


@dataclass(frozen=True)
class NasaLimitsConfig:
    """Normative limits and thresholds per NASA-STD-3001 and HSRB."""

    # Environment (Brain 1)
    co2_normal_min_mmhg: float = 1.0
    co2_normal_max_mmhg: float = 2.2
    co2_symptom_threshold_mmhg: float = 2.3
    co2_limit_7day_mmhg: float = 2.5
    co2_max_limit_nasa_v2_6004_mmhg: float = 3.0

    cabin_pressure_min_kpa: float = 95.0
    cabin_pressure_max_kpa: float = 103.0

    base_cumulative_radiation_msv: float = 50.0
    daily_radiation_rate_min_msv: float = 0.2
    daily_radiation_rate_max_msv: float = 0.5
    solar_storm_radiation_impact_msv: float = 20.0
    solar_storm_probability: float = 0.01
    career_radiation_limit_msv: float = 600.0
    solar_event_radiation_limit_msv: float = 250.0

    # Physiology (Brain 2)
    base_heart_rate_bpm: float = 65.0
    heart_rate_deviation_bpm: float = 5.0
    average_sleep_hours: float = 6.0
    sleep_hours_risk_threshold: float = 6.0
    consecutive_sleep_for_alert: int = 3
    monthly_bone_loss_rate_pct: float = 1.5

    # Cognition / Psychology (Brain 4 - ASTRA)
    base_voice_latency_ms: float = 200.0
    stress_voice_latency_min_ms: float = 600.0
    stress_voice_latency_max_ms: float = 900.0
    stress_incongruence_probability: float = 0.15
    heart_rate_high_stress_threshold_bpm: float = 95.0
    historical_sans_prevalence_lsah_pct: float = 81.0
