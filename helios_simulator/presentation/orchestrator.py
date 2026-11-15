"""
Orchestrator of the main telemetry loop (Presentation / Main layer).

Applies Dependency Inversion (DIP) by receiving the infrastructure publisher via
injection and coordinates the generation and preliminary assessment services.
"""

from datetime import datetime, timezone
import logging
import signal
import time
from typing import Any

from helios_simulator.config import MissionConfig, NasaLimitsConfig
from helios_simulator.domain.enums import ConnectionState
from helios_simulator.domain.models import TelemetryPayload
from helios_simulator.infrastructure.publisher_interface import TelemetryPublisherInterface
from helios_simulator.services.biometrics_generator import BiometricsGenerator
from helios_simulator.services.cognition_generator import CognitionGenerator
from helios_simulator.services.correlation_evaluator import CorrelationEvaluatorService
from helios_simulator.services.environment_generator import EnvironmentGenerator
from helios_simulator.services.math_noise import round_telemetry

logger = logging.getLogger(__name__)


class TelemetryOrchestrator:
    """
    Orchestrator of the HELIOS life support telemetry producer.
    Coordinates periodic generation every 2 seconds and emission to the Earth mailbox.
    """

    def __init__(
        self,
        publisher: TelemetryPublisherInterface,
        mission_config: MissionConfig | None = None,
        limits_config: NasaLimitsConfig | None = None,
        environment_generator: EnvironmentGenerator | None = None,
        biometrics_generator: BiometricsGenerator | None = None,
        cognition_generator: CognitionGenerator | None = None,
        correlation_evaluator: CorrelationEvaluatorService | None = None,
    ) -> None:
        """
        Constructor with Dependency Injection (DIP).

        Args:
            publisher: Concrete telemetry publisher implementation (e.g. Redis).
            mission_config: Mission identification and timing configuration.
            limits_config: NASA reference standards and thresholds.
            environment_generator: Environmental simulation service (Brain 1).
            biometrics_generator: Vital signs and fatigue service (Brain 2).
            cognition_generator: Cognition and language service (Brain 4).
            correlation_evaluator: Preliminary assessment and risk crossover engine.
        """
        self._publisher = publisher
        self._mission_config = mission_config or MissionConfig()
        self._limits_config = limits_config or NasaLimitsConfig()

        self._mission_day = self._mission_config.default_mission_day
        self._environment_generator = environment_generator or EnvironmentGenerator(
            limits_config=self._limits_config,
            initial_mission_day=self._mission_day,
        )
        self._biometrics_generator = biometrics_generator or BiometricsGenerator(
            limits_config=self._limits_config,
            initial_mission_day=self._mission_day,
        )
        self._cognition_generator = cognition_generator or CognitionGenerator(
            limits_config=self._limits_config,
        )
        self._correlation_evaluator = correlation_evaluator or CorrelationEvaluatorService(
            limits_config=self._limits_config,
        )

        self._running = False
        self._current_cycle = 0

    def initialize_links(self) -> bool:
        """
        Starts the communication components toward the telemetry mailbox.

        Returns:
            True if the publisher connected immediately, False if it started in resilient mode.
        """
        if self._publisher.get_connection_state() == ConnectionState.CONNECTED:
            return True

        logger.info(
            "Starting HELIOS v2.1 subsystem for mission %s (Crew member: %s, Sol: %d)...",
            self._mission_config.mission_id,
            self._mission_config.astronaut_id,
            self._mission_day,
        )
        return self._publisher.connect()

    def produce_sample(
        self,
        force_co2_peak: bool = False,
        force_solar_storm: bool = False,
        force_sleep_deficit: bool = False,
        force_tachycardia: bool = False,
        force_incongruence: bool = False,
    ) -> TelemetryPayload:
        """
        Runs a full multivariate computation cycle and generates the consolidated payload.

        Args:
            force_co2_peak: Injects an anomalous CO2 peak > 3.0 mmHg.
            force_solar_storm: Injects a Solar Storm event (+20 mSv).
            force_sleep_deficit: Forces a sleep record < 6.0h.
            force_tachycardia: Forces an elevated heart rate.
            force_incongruence: Forces hidden cognitive stress.

        Returns:
            Complete TelemetryPayload instance ready for transmission.
        """
        self._current_cycle += 1

        # 1. Brain 1 simulation: Cabin environment
        environment = self._environment_generator.generate_reading(
            force_co2_peak=force_co2_peak,
            force_solar_storm=force_solar_storm,
        )

        # 2. Brain 2 simulation: Physiology and Biometrics
        environmental_stress = (
            environment.co2_mmHg >= self._limits_config.co2_symptom_threshold_mmhg
            or environment.solar_event_active
        )
        biometrics = self._biometrics_generator.generate_reading(
            environmental_stress=environmental_stress,
            force_sleep_deficit=force_sleep_deficit,
            force_tachycardia=force_tachycardia,
        )

        # 3. Brain 4 simulation: Psychology and Cognition (ASTRA)
        cognition = self._cognition_generator.generate_reading(
            co2_mmhg=environment.co2_mmHg,
            sleep_hours=biometrics.last_cycle_sleep_hours,
            heart_rate_bpm=biometrics.heart_rate_bpm,
            solar_event_active=environment.solar_event_active,
            force_incongruence=force_incongruence,
        )

        # 4. Preliminary assessment and NASA-STD-3001 normative crossover
        assessments = self._correlation_evaluator.evaluate_systemic_state(
            environment=environment,
            biometrics=biometrics,
            cognition=cognition,
        )

        # 5. Computation of the consumed career radiation budget (% of 600 mSv)
        radiation_budget_pct = (
            environment.cumulative_radiation_mSv / self._limits_config.career_radiation_limit_msv
        ) * 100.0

        metadata: dict[str, Any] = {
            "producer_module": "helios_simulator",
            "architecture": "N-Layer Edge AI",
            "sampling_frequency_hz": 0.5,
            "interval_seconds": self._mission_config.emission_interval_seconds,
            "sample_cycle_id": self._current_cycle,
            "redis_channel": "earth_telemetry_mailbox",
            "link_status": self._publisher.get_connection_state().value,
        }

        payload = TelemetryPayload(
            timestamp=datetime.now(timezone.utc),
            mission_id=self._mission_config.mission_id,
            mission_day=self._mission_day,
            astronaut_id=self._mission_config.astronaut_id,
            environment=environment,
            biometrics=biometrics,
            cognition=cognition,
            preliminary_assessments=assessments,
            career_radiation_budget_pct=round_telemetry(radiation_budget_pct, 2),
            system_metadata=metadata,
        )

        return payload

    def run_loop(self, max_cycles: int | None = None) -> None:
        """
        Continuous telemetry production loop.
        Emits one sample every 2 seconds toward the infrastructure layer.

        Args:
            max_cycles: Optional iteration limit (ideal for tests and bounded runs).
        """
        self._running = True
        self._configure_signal_handler()
        self.initialize_links()

        logger.info(
            "Starting continuous transmission to 'earth_telemetry_mailbox' every %.1f seconds...",
            self._mission_config.emission_interval_seconds,
        )

        try:
            while self._running:
                cycle_start = time.time()

                payload = self.produce_sample()
                self._publisher.publish_telemetry(payload)

                # Detailed formatting of sign and variable telemetry for live display
                logger.info(
                    "SAMPLE #%d [Day %d - %s] | ENVIRONMENT: CO2=%.2f mmHg | Cum.Rad=%.2f mSv (%.1f%%) | Pressure=%.1f kPa | Temp=%.1f°C | Hum=%.1f%% | SPE=%s",
                    self._current_cycle,
                    payload.mission_day,
                    payload.astronaut_id,
                    payload.environment.co2_mmHg,
                    payload.environment.cumulative_radiation_mSv,
                    payload.career_radiation_budget_pct,
                    payload.environment.cabin_pressure_kpa,
                    payload.environment.cabin_temperature_c,
                    payload.environment.relative_humidity_pct,
                    "YES" if payload.environment.solar_event_active else "NO",
                )
                logger.info(
                    "             [BIOMETRICS]: HR=%.1f bpm | SpO2=%.1f%% | BP=%.1f/%.1f | Skin=%.1f°C | Resp=%.1f rpm | HRV=%.1f ms | Sleep=%.1fh | BoneLoss=%.2f%% | Headache=%s",
                    payload.biometrics.heart_rate_bpm,
                    payload.biometrics.spo2_pct,
                    payload.biometrics.systolic_pressure_mmHg,
                    payload.biometrics.diastolic_pressure_mmHg,
                    payload.biometrics.skin_temperature_c,
                    payload.biometrics.respiratory_rate_rpm,
                    payload.biometrics.heart_rate_variability_hrv_ms,
                    payload.biometrics.last_cycle_sleep_hours,
                    payload.biometrics.bone_loss_pct,
                    "YES" if payload.biometrics.headache_symptom else "NO",
                )
                logger.info(
                    "             [COGNITION]: VoiceLat=%.1f ms | Density=%.2f | HiddenStress=%s | SANS(Vision)=%s | Fatigue=%s",
                    payload.cognition.voice_latency_ms,
                    payload.cognition.lexical_density_score,
                    "YES" if payload.cognition.hidden_stress_incongruence else "NO",
                    "YES" if payload.cognition.sans_vision_symptom else "NO",
                    "ALERT" if payload.biometrics.fatigue_risk_alert else "NOMINAL",
                )

                if payload.preliminary_assessments:
                    for alert in payload.preliminary_assessments:
                        logger.warning(
                            "   >>> [%s] %s: %s (Standard: %s)",
                            alert.level.value,
                            alert.code,
                            alert.description,
                            alert.reference_standard,
                        )

                if max_cycles is not None and self._current_cycle >= max_cycles:
                    logger.info("Reached the requested maximum number of cycles (%d). Stopping...", max_cycles)
                    break

                elapsed_time = time.time() - cycle_start
                pause_time = max(0.0, self._mission_config.emission_interval_seconds - elapsed_time)
                time.sleep(pause_time)
        except KeyboardInterrupt:
            logger.info("Voluntary interruption by the mission operator detected.")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stops the emission in a controlled manner and releases the publisher resources."""
        self._running = False
        logger.info("Stopping the HELIOS telemetry orchestrator...")
        self._publisher.close()

    def _configure_signal_handler(self) -> None:
        """Configures POSIX/Windows signal interceptors for a clean exit."""
        try:
            signal.signal(signal.SIGINT, self._interrupt_handler)
            signal.signal(signal.SIGTERM, self._interrupt_handler)
        except (ValueError, AttributeError):
            pass

    def _interrupt_handler(self, signum: int, frame: Any) -> None:
        """Callback invoked when SIGINT or SIGTERM is intercepted."""
        logger.info("Termination signal received (%d). Concluding cycle...", signum)
        self.stop()
