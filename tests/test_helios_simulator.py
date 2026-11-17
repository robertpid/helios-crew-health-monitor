"""
Unit and integration test suite for helios_simulator.

Validates compliance with NASA-STD-3001, the RIDGE framework, Pydantic models,
multivariate crossover logic, Redis fault tolerance and SOLID principles.
"""

import json
from unittest.mock import MagicMock, patch
import pytest

from helios_simulator.config import MissionConfig, NasaLimitsConfig, RedisConfig
from helios_simulator.domain.enums import AlertLevel, ConnectionState, RidgeHazard
from helios_simulator.domain.models import (
    BiometricsModel,
    CognitionModel,
    EnvironmentModel,
    PreliminaryAssessmentAlert,
    TelemetryPayload,
)
from helios_simulator.infrastructure.publisher_interface import TelemetryPublisherInterface
from helios_simulator.infrastructure.redis_publisher import RedisTelemetryPublisher
from helios_simulator.presentation.orchestrator import TelemetryOrchestrator
from helios_simulator.services.biometrics_generator import BiometricsGenerator
from helios_simulator.services.cognition_generator import CognitionGenerator
from helios_simulator.services.correlation_evaluator import CorrelationEvaluatorService
from helios_simulator.services.environment_generator import EnvironmentGenerator
from helios_simulator.services.math_noise import (
    compute_cumulative_bone_loss,
    evaluate_event_probability,
    generate_gaussian_noise,
    round_telemetry,
)


class MockTelemetryPublisher(TelemetryPublisherInterface):
    """Test implementation to verify Dependency Inversion (DIP)."""

    def __init__(self) -> None:
        self.connected = False
        self.received_payloads: list[TelemetryPayload] = []

    def connect(self) -> bool:
        self.connected = True
        return True

    def publish_telemetry(self, payload: TelemetryPayload) -> bool:
        self.received_payloads.append(payload)
        return True

    def close(self) -> None:
        self.connected = False

    def get_connection_state(self) -> ConnectionState:
        return ConnectionState.CONNECTED if self.connected else ConnectionState.DISCONNECTED


def test_compute_bone_loss_day_120() -> None:
    """Validates the HSRB monthly bone loss formula: (day / 30) * 1.5%."""
    # For Day 120: (120 / 30) * 1.5 = 4 * 1.5 = 6.0%
    loss_day_120 = compute_cumulative_bone_loss(120, monthly_rate_pct=1.5)
    assert loss_day_120 == 6.0

    # For Day 60: (60 / 30) * 1.5 = 3.0%
    loss_day_60 = compute_cumulative_bone_loss(60, monthly_rate_pct=1.5)
    assert loss_day_60 == 3.0

    # Day 0
    assert compute_cumulative_bone_loss(0) == 0.0


def test_gaussian_noise_and_clamping() -> None:
    """Verifies that the noise respects the upper and lower bounds."""
    for _ in range(50):
        val = generate_gaussian_noise(mean_value=100.0, standard_deviation=10.0, lower_bound=90.0, upper_bound=110.0)
        assert 90.0 <= val <= 110.0


def test_environment_generator_co2_peak_nasa_v2_6004() -> None:
    """Verifies nominal generation and the injection of CO2 peaks > 3.0 mmHg."""
    generator = EnvironmentGenerator(initial_mission_day=120)

    # Force a CO2 peak
    peak_reading = generator.generate_reading(force_co2_peak=True)
    assert peak_reading.co2_mmHg > 3.0
    assert 95.0 <= peak_reading.cabin_pressure_kpa <= 103.0

    # Nominal reading
    with patch("helios_simulator.services.environment_generator.evaluate_event_probability", return_value=False):
        nominal_reading = generator.generate_reading(force_co2_peak=False)
        assert 1.0 <= nominal_reading.co2_mmHg <= 2.2


def test_environment_generator_solar_storm() -> None:
    """Validates the +20 mSv radiation increase after a solar particle event."""
    generator = EnvironmentGenerator(initial_mission_day=120)
    base_reading = generator.generate_reading(force_solar_storm=False)

    storm_reading = generator.generate_reading(force_solar_storm=True)
    assert storm_reading.solar_event_active is True
    assert storm_reading.cumulative_radiation_mSv >= base_reading.cumulative_radiation_mSv + 19.5


def test_biometrics_generator_fatigue_alert_3_cycles() -> None:
    """Validates that 3 successive cycles with sleep < 6h raise the fatigue risk flag."""
    generator = BiometricsGenerator(initial_mission_day=120)

    # Cycle 1: sleep deficit (5.0h)
    generator.simulate_new_sleep_cycle(5.0)
    reading_1 = generator.generate_reading()
    assert reading_1.consecutive_insufficient_sleep_cycles == 1
    assert reading_1.fatigue_risk_alert is False

    # Cycle 2: sleep deficit (5.5h)
    generator.simulate_new_sleep_cycle(5.5)
    reading_2 = generator.generate_reading()
    assert reading_2.consecutive_insufficient_sleep_cycles == 2
    assert reading_2.fatigue_risk_alert is False

    # Cycle 3: sleep deficit (4.8h) -> Raises the flag
    generator.simulate_new_sleep_cycle(4.8)
    reading_3 = generator.generate_reading()
    assert reading_3.consecutive_insufficient_sleep_cycles == 3
    assert reading_3.fatigue_risk_alert is True
    assert reading_3.bone_loss_pct == 6.0  # Day 120


def test_cognition_generator_voice_latency_crossover() -> None:
    """Validates the logical crossover: if CO2 > 2.5 or sleep < 6h, latency rises to 600-900ms."""
    generator = CognitionGenerator()

    # Case 1: Nominal (CO2 = 1.5, sleep = 7.5h)
    nominal = generator.generate_reading(co2_mmhg=1.5, sleep_hours=7.5, heart_rate_bpm=65.0)
    assert 140.0 <= nominal.voice_latency_ms <= 300.0

    # Case 2: High CO2 (> 2.5) -> Spikes latency to 600-900ms
    co2_degraded = generator.generate_reading(co2_mmhg=3.2, sleep_hours=7.5, heart_rate_bpm=65.0)
    assert 600.0 <= co2_degraded.voice_latency_ms <= 900.0

    # Case 3: Insufficient sleep (< 6.0) -> Spikes latency to 600-900ms
    sleep_degraded = generator.generate_reading(co2_mmhg=1.5, sleep_hours=5.2, heart_rate_bpm=65.0)
    assert 600.0 <= sleep_degraded.voice_latency_ms <= 900.0


def test_cognition_generator_hidden_stress_incongruence() -> None:
    """Validates the hidden stress simulation (rate > 95 bpm but lexical density ~0.80)."""
    generator = CognitionGenerator()
    reading = generator.generate_reading(
        co2_mmhg=1.5,
        sleep_hours=7.0,
        heart_rate_bpm=102.0,
        force_incongruence=True,
    )
    assert reading.hidden_stress_incongruence is True
    assert 0.75 <= reading.lexical_density_score <= 0.85


def test_correlation_evaluator_nasa_alerts() -> None:
    """Validates that the evaluator generates normative alerts citing NASA standards."""
    evaluator = CorrelationEvaluatorService()

    environment = EnvironmentModel(
        co2_mmHg=3.4,
        cumulative_radiation_mSv=72.0,
        daily_radiation_rate_mSv=0.4,
        cabin_pressure_kpa=101.2,
        cabin_temperature_c=22.0,
        solar_event_active=True,
    )
    biometrics = BiometricsModel(
        heart_rate_bpm=105.0,
        last_cycle_sleep_hours=5.0,
        consecutive_insufficient_sleep_cycles=3,
        fatigue_risk_alert=True,
        bone_loss_pct=6.0,
        systolic_pressure_mmHg=135.0,
        diastolic_pressure_mmHg=85.0,
        spo2_pct=98.0,
    )
    cognition = CognitionModel(
        voice_latency_ms=780.0,
        lexical_density_score=0.80,
        hidden_stress_incongruence=True,
        sans_vision_symptom=True,
    )

    alerts = evaluator.evaluate_systemic_state(environment, biometrics, cognition)
    codes = {alert.code for alert in alerts}

    assert "ALERT-CO2-MAX-V2-6004" in codes
    assert "ALERT-SPE-SOLAR-EVENT-V1-4030" in codes
    assert "ALERT-CHRONIC-FATIGUE-HSRB" in codes
    assert "ALERT-COGNITIVE-LATENCY-CROSSOVER" in codes
    assert "ALERT-STRESS-INCONGRUENCE-ASTRA" in codes
    assert "ALERT-SANS-VISION-SYMPTOM" in codes


def test_redis_publisher_buffer_fault_tolerance() -> None:
    """Validates automatic reconnection and the local buffer (Store-and-Forward) when Redis does not respond."""
    config = RedisConfig(host="127.0.0.1", port=6399)  # Intentionally unreachable port
    publisher = RedisTelemetryPublisher(config=config)

    # The initial connection attempt will fail without raising unhandled exceptions
    connection = publisher.connect()
    assert connection is False
    assert publisher.get_connection_state() == ConnectionState.DISCONNECTED

    payload = TelemetryPayload(
        mission_id="TEST-MISSION",
        mission_day=120,
        astronaut_id="ASTRO-TEST",
        environment=EnvironmentModel(
            co2_mmHg=1.8,
            cumulative_radiation_mSv=55.0,
            daily_radiation_rate_mSv=0.35,
            cabin_pressure_kpa=101.3,
            cabin_temperature_c=21.0,
            solar_event_active=False,
        ),
        biometrics=BiometricsModel(
            heart_rate_bpm=64.0,
            last_cycle_sleep_hours=6.5,
            consecutive_insufficient_sleep_cycles=0,
            fatigue_risk_alert=False,
            bone_loss_pct=6.0,
            systolic_pressure_mmHg=120.0,
            diastolic_pressure_mmHg=78.0,
            spo2_pct=99.0,
        ),
        cognition=CognitionModel(
            voice_latency_ms=210.0,
            lexical_density_score=0.68,
            hidden_stress_incongruence=False,
            sans_vision_symptom=False,
        ),
        preliminary_assessments=[],
        career_radiation_budget_pct=9.17,
    )

    # It must buffer in local memory without losing the data
    success = publisher.publish_telemetry(payload)
    assert success is True
    assert publisher.buffered_messages == 1


def test_orchestrator_with_dependency_injection() -> None:
    """Verifies that the orchestrator works correctly with an injected publisher (DIP)."""
    mock_publisher = MockTelemetryPublisher()
    mission_config = MissionConfig(default_mission_day=120, emission_interval_seconds=0.01)

    orchestrator = TelemetryOrchestrator(
        publisher=mock_publisher,
        mission_config=mission_config,
    )

    # Run 3 fast cycles
    orchestrator.run_loop(max_cycles=3)

    assert mock_publisher.connected is False  # closed on completion
    assert len(mock_publisher.received_payloads) == 3

    first_payload = mock_publisher.received_payloads[0]
    assert first_payload.mission_day == 120
    assert first_payload.biometrics.bone_loss_pct == 6.0
    # Check Pydantic serialization
    json_data = first_payload.model_dump_json()
    assert isinstance(json_data, str)
    parsed = json.loads(json_data)
    assert parsed["mission_day"] == 120
    assert "environment" in parsed
    assert "biometrics" in parsed
    assert "cognition" in parsed
