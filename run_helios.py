"""
Main entry point for the HELIOS telemetry simulator.

Life support orchestrator for deep space missions to Mars (Day 120).
Injects a JSON payload every 2 seconds into the local Redis server on 'earth_telemetry_mailbox'.

Usage:
    python run_helios.py
    python run_helios.py --redis-host 127.0.0.1 --mission-day 120 --interval 2.0
    python run_helios.py --simulate-crisis-demo
"""

import argparse
import logging
import sys

from helios_simulator.config import MissionConfig, NasaLimitsConfig, RedisConfig
from helios_simulator.infrastructure.redis_publisher import RedisTelemetryPublisher
from helios_simulator.presentation.orchestrator import TelemetryOrchestrator


def configure_logging_subsystem(verbose_level: bool = False) -> None:
    """
    Configures the standard formatter of the logging module per engineering guidelines.

    Args:
        verbose_level: If True, raises the level to DEBUG.
    """
    aerospace_format = (
        "%(asctime)s.%(msecs)03d UTC | %(levelname)-8s | [%(name)s] | %(message)s"
    )
    level = logging.DEBUG if verbose_level else logging.INFO

    logging.basicConfig(
        level=level,
        format=aerospace_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def parse_mission_arguments() -> argparse.Namespace:
    """
    Parses the operational parameters received from the command line.

    Returns:
        Namespace with the configured options.
    """
    parser = argparse.ArgumentParser(
        description="HELIOS Telemetry Simulator - Deep Space Life Support System (NASA-STD-3001)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--redis-host",
        type=str,
        default="127.0.0.1",
        help="IP address or hostname of the local Redis server.",
    )
    parser.add_argument(
        "--redis-port",
        type=int,
        default=6379,
        help="Redis listening port.",
    )
    parser.add_argument(
        "--redis-channel",
        type=str,
        default="earth_telemetry_mailbox",
        help="Pub/Sub channel and mailbox name in Redis.",
    )
    parser.add_argument(
        "--mission-day",
        type=int,
        default=120,
        help="Elapsed day of the mission to Mars (default: Day 120).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Telemetry injection frequency in seconds.",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=None,
        help="Maximum number of cycles before finishing (useful for automated tests).",
    )
    parser.add_argument(
        "--simulate-crisis-demo",
        action="store_true",
        help="Injects a severe contingency sequence: CO2 peak, solar storm and stress.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enables detailed debug logging.",
    )

    return parser.parse_args()


def main() -> None:
    """
    Safe entry point of the synthetic telemetry producer.
    Applies Dependency Inversion (DIP) by injecting the publisher into the orchestrator.
    """
    arguments = parse_mission_arguments()
    configure_logging_subsystem(verbose_level=arguments.verbose)

    logger = logging.getLogger("helios_simulator.main")
    logger.info("================================================================================")
    logger.info("  HELIOS DEEP SPACE LIFE SUPPORT TELEMETRY PRODUCER - NASA SPACE APPS 2026")
    logger.info("  Standard: NASA-STD-3001 | Framework: RIDGE | Target: Redis ('%s')", arguments.redis_channel)
    logger.info("================================================================================")

    # 1. Infrastructure layer configuration
    redis_config = RedisConfig(
        host=arguments.redis_host,
        port=arguments.redis_port,
        publish_channel=arguments.redis_channel,
        publish_queue=f"{arguments.redis_channel}_queue",
    )
    redis_publisher = RedisTelemetryPublisher(config=redis_config)

    # 2. Domain and mission configuration
    mission_config = MissionConfig(
        default_mission_day=arguments.mission_day,
        emission_interval_seconds=arguments.interval,
    )
    limits_config = NasaLimitsConfig()

    # 3. Dependency Inversion: injecting the Publisher into the Orchestrator
    orchestrator = TelemetryOrchestrator(
        publisher=redis_publisher,
        mission_config=mission_config,
        limits_config=limits_config,
    )

    # 4. Contingency demonstration mode (if requested)
    if arguments.simulate_crisis_demo:
        logger.warning("MULTIVARIATE CONTINGENCY DEMO MODE ACTIVATED.")
        orchestrator.initialize_links()
        crisis_payload = orchestrator.produce_sample(
            force_co2_peak=True,
            force_solar_storm=True,
            force_sleep_deficit=True,
            force_tachycardia=True,
            force_incongruence=True,
        )
        redis_publisher.publish_telemetry(crisis_payload)
        logger.info("Contingency sample injected successfully. Alert codes:")
        for alert in crisis_payload.preliminary_assessments:
            logger.warning(" -> [%s] %s: %s", alert.level.value, alert.code, alert.description)

    # 5. Running the continuous loop (every 2 seconds)
    orchestrator.run_loop(max_cycles=arguments.max_cycles)


if __name__ == "__main__":
    main()
