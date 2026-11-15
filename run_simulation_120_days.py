"""
Execution script for the 120-day time series simulation.

Simulates every vital sign and environmental variable in vectorized form for:
1. International Space Station (ISS / LEO)
2. Lunar Base (Artemis Base Camp)
3. Spacecraft (Deep Space Transit to Mars)
4. Mars Base (Martian Surface Habitat)

Exports analytical artifacts (CSV, Parquet, JSONL) and presents a comparative summary.

Usage:
    python run_simulation_120_days.py
    python run_simulation_120_days.py --days 120 --output-directory generated_data
"""

import argparse
import logging
from pathlib import Path
import sys

from helios_simulator.config import NasaLimitsConfig
from helios_simulator.services.multi_habitat_simulator import MultiHabitat120DaySimulator


def configure_logging(verbose: bool = False) -> None:
    """Configures the standard logging subsystem for aerospace auditing."""
    level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(asctime)s.%(msecs)03d UTC | %(levelname)-8s | [%(name)s] | %(message)s"
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def parse_arguments() -> argparse.Namespace:
    """Parses the command line arguments."""
    parser = argparse.ArgumentParser(
        description="120-Day Multi-Habitat Telemetry Simulator (Space Apps 2026)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--days",
        type=int,
        default=120,
        help="Duration of the mission period in days or sols.",
    )
    parser.add_argument(
        "--output-directory",
        type=str,
        default="generated_data",
        help="Folder where the CSV, Parquet and JSONL files will be stored.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed of the pseudorandom generator.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enables detailed debug traces.",
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for the 120-day multi-habitat simulation."""
    arguments = parse_arguments()
    configure_logging(verbose=arguments.verbose)

    logger = logging.getLogger("helios.simulator_120_days")
    logger.info("================================================================================")
    logger.info("   120-DAY SPACE TELEMETRY SIMULATOR - FOUR HABITATS (NASA RIDGE)               ")
    logger.info("   Standard: NASA-STD-3001 | ISS vs Moon vs Transit Spacecraft vs Mars Base     ")
    logger.info("================================================================================")

    simulator = MultiHabitat120DaySimulator(
        limits_config=NasaLimitsConfig(),
        random_seed=arguments.seed,
    )

    logger.info("Starting the generation of vectorized data for a period of %d days...", arguments.days)
    master_df = simulator.simulate_all_habitats(total_days=arguments.days)

    # Export to disk in structured formats
    paths = simulator.export_dataset(
        df=master_df,
        target_directory=arguments.output_directory,
        base_name=f"telemetry_{arguments.days}_days_four_habitats",
    )

    # End-of-mission comparative summary
    summary_table = simulator.generate_comparative_summary(master_df)

    logger.info("--------------------------------------------------------------------------------")
    logger.info("COMPARATIVE SUMMARY AT MISSION DAY %d:", arguments.days)
    logger.info("--------------------------------------------------------------------------------")
    summary_records = summary_table.reset_index().to_dict(orient="records")
    for record in summary_records:
        logger.info(
            "Habitat: %-18s | g=%.3f | Delay=%5.1f min | Cum.Rad=%6.1f mSv (%5.1f%% career) | BoneLoss=%4.1f%% | Fatigue=%2d d | SANS=%2d d",
            record["mission_environment"],
            record["gravity_g"],
            record["earth_delay_min"],
            record["final_radiation_mSv"],
            record["final_radiation_budget_pct"],
            record["final_bone_loss_pct"],
            int(record["days_with_fatigue_alert"]),
            int(record["days_with_sans_vision"]),
        )

    logger.info("--------------------------------------------------------------------------------")
    logger.info("Artifacts generated successfully:")
    for file_format, path in paths.items():
        logger.info(" -> [%s]: %s (Size: %d bytes)", file_format.upper(), Path(path).resolve(), Path(path).stat().st_size)
    logger.info("================================================================================")


if __name__ == "__main__":
    main()
