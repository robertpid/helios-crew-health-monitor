"""
Domain models for the HELIOS simulator space telemetry.

Implements immutable, typed data structures with Pydantic v2 to guarantee the
integrity of the payload sent to the ground station and life support nodes.
"""

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

from helios_simulator.domain.enums import AlertLevel, RidgeHazard


class EnvironmentModel(BaseModel):
    """
    Brain 1: Environmental telemetry of the cabin and surrounding space.
    Grounded in NASA-STD-3001 Vol. 2 and radiation measurements from the NTRS server.
    """

    model_config = ConfigDict(frozen=True)

    co2_mmHg: float = Field(
        ...,
        description="Partial pressure of cabin CO2 in mmHg. NASA V2 6004 normative threshold <= 3.0 mmHg."
    )
    cumulative_radiation_mSv: float = Field(
        ...,
        description="Cumulative effective radiation dose in mSv (NASA career limit: 600 mSv)."
    )
    daily_radiation_rate_mSv: float = Field(
        ...,
        description="Daily dose rate in mSv/day (typical ISS: 0.2 to 0.5 mSv/day)."
    )
    cabin_pressure_kpa: float = Field(
        ...,
        description="Cabin atmospheric pressure in kPa. NASA V2 6006 normative threshold: 95.0 - 103.0 kPa."
    )
    cabin_temperature_c: float = Field(
        ...,
        description="Internal ambient temperature in degrees Celsius."
    )
    relative_humidity_pct: float = Field(
        default=45.0,
        ge=0.0,
        le=100.0,
        description="Cabin relative humidity sensor (NASA OSDR N22: 40-60%)."
    )
    solar_event_active: bool = Field(
        default=False,
        description="Anomaly indicator for a Solar Storm or Solar Particle Event (SPE)."
    )


class BiometricsModel(BaseModel):
    """
    Brain 2: Physiological biometrics of the astronaut.
    Based on personalized baselines (NASA Twins Study) and HSRB countermeasures.
    """

    model_config = ConfigDict(frozen=True)

    heart_rate_bpm: float = Field(
        ...,
        description="Instantaneous heart rate in beats per minute (BPM)."
    )
    last_cycle_sleep_hours: float = Field(
        ...,
        description="Effective hours of rest in the last circadian cycle."
    )
    consecutive_insufficient_sleep_cycles: int = Field(
        ...,
        ge=0,
        description="Counter of consecutive cycles with sleep below the 6.0 hour threshold."
    )
    fatigue_risk_alert: bool = Field(
        default=False,
        description="Accumulated fatigue flag raised after 3 successive cycles with a sleep deficit."
    )
    bone_loss_pct: float = Field(
        ...,
        ge=0.0,
        description="Estimated cumulative bone mineral density loss per the HSRB model."
    )
    systolic_pressure_mmHg: float = Field(
        ...,
        description="Systolic arterial pressure in mmHg."
    )
    diastolic_pressure_mmHg: float = Field(
        ...,
        description="Diastolic arterial pressure in mmHg."
    )
    spo2_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Peripheral oxygen saturation in blood."
    )
    skin_temperature_c: float = Field(
        default=34.8,
        description="Astroskin Bio-Monitor cutaneous thermal sensor in degrees Celsius."
    )
    respiratory_rate_rpm: float = Field(
        default=14.0,
        description="Thoracic respiratory rate sensor in breaths per minute (Astroskin Bio-Monitor)."
    )
    heart_rate_variability_hrv_ms: float = Field(
        default=42.0,
        description="Heart rate variability HRV in milliseconds (Frontiers in Physiology 2024 / E13)."
    )
    headache_symptom: bool = Field(
        default=False,
        description="Symptomatic record of headache associated with elevated CO2 or fluid shift."
    )
    physical_activity_minutes: float = Field(
        default=120.0,
        description="Daily resistance exercise time as a bone mass countermeasure (NASA HSRB)."
    )
    self_reported_stress_scale: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Subjective self-report of fatigue and psychophysiological stress on a 1 to 10 scale."
    )


class CognitionModel(BaseModel):
    """
    Brain 4: Psychology and Cognition (ASTRA subsystem).
    Monitors communication latency, coherence and neuro-ocular strain detection.
    """

    model_config = ConfigDict(frozen=True)

    voice_latency_ms: float = Field(
        ...,
        description="Verbal response time in milliseconds during cabin communications."
    )
    lexical_density_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Index of lexical complexity and variety in verbal communications (0.0 to 1.0)."
    )
    hidden_stress_incongruence: bool = Field(
        default=False,
        description="Detection of psychological incongruence (elevated heart rate with formalized speech)."
    )
    sans_vision_symptom: bool = Field(
        default=False,
        description="Presence of SANS neuro-ocular symptoms under stress and elevated pressures."
    )


class PreliminaryAssessmentAlert(BaseModel):
    """
    Formal structure for preliminary risk assessments and operational alerts.
    Cites official NASA-STD-3001 and RIDGE standards to back technical validation.
    """

    model_config = ConfigDict(frozen=True)

    code: str = Field(..., description="Unique identifier of the normative alert.")
    level: AlertLevel = Field(..., description="Alert severity.")
    ridge_hazard: RidgeHazard = Field(..., description="Risk category from the RIDGE framework.")
    reference_standard: str = Field(..., description="Reference to the official NASA standard.")
    description: str = Field(..., description="Explanatory detail of the detected event.")
    multivariate_crossover: bool = Field(
        default=False,
        description="Indicates whether the alert results from the synergistic crossover of multiple factors."
    )


class TelemetryPayload(BaseModel):
    """
    Consolidated payload injected into the telemetry downlink to Earth.
    Represents the systemic state of the astronaut and their habitat in real time.
    """

    model_config = ConfigDict(frozen=True)

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp in UTC standard with microsecond resolution."
    )
    mission_id: str = Field(..., description="Unique identifier of the aerospace mission.")
    mission_day: int = Field(..., ge=1, description="Elapsed day of the mission (sol).")
    astronaut_id: str = Field(..., description="Identifier of the crew member.")
    environment: EnvironmentModel = Field(..., description="Environmental metrics (Brain 1).")
    biometrics: BiometricsModel = Field(..., description="Physiological metrics (Brain 2).")
    cognition: CognitionModel = Field(..., description="Cognitive and behavioral metrics (Brain 4).")
    preliminary_assessments: list[PreliminaryAssessmentAlert] = Field(
        default_factory=list,
        description="Collection of preliminary assessments and alerts active at this instant."
    )
    career_radiation_budget_pct: float = Field(
        ...,
        description="Percentage consumed of the 600 mSv limit allowed for the astronaut's career."
    )
    system_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Operational metadata of the edge producer (Edge AI)."
    )
