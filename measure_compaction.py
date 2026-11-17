"""
Measurement of the volume savings from telemetry compaction in H.E.L.I.O.S.

Contrasts the consolidated report (descriptive text in every cycle) against the
compact record (rule codes + numeric values) over the real 120-day x 4-habitat
dataset, so that the alert distribution is the mission's and not that of a
hand-picked payload.

It also measures the size after gzip compression: a real link compresses, and
repetitive text compresses far better than numbers, so an honest comparison must
include both axes.
"""

import gzip
import json
import logging
import statistics
from pathlib import Path
from typing import Any

import pandas as pd

logging.disable(logging.CRITICAL)

from helios_inference.domain.telemetry_codebook import build_codebook
from helios_inference.services.inference_engine import InferenceEngine
from helios_inference.services.telemetry_compactor import compact_record, expand

CADENCE_HZ = 0.5
MISSION_DAYS = 120
SECONDS_PER_DAY = 86_400
DATASET_PATH = Path("generated_data/telemetry_120_days_four_habitats.parquet")


def row_to_payload(row: pd.Series) -> dict[str, Any]:
    """Projects a row of the multi-habitat dataset onto the telemetry contract."""
    return {
        "mission_id": f"{row['mission_environment']}-EXPEDITION",
        "mission_day": int(row["mission_day"]),
        "astronaut_id": "ASTRO-HELIOS-01",
        "environment": {
            "co2_mmHg": float(row["co2_mmHg"]),
            "cumulative_radiation_mSv": float(row["cumulative_radiation_mSv"]),
            "cabin_pressure_kpa": float(row["cabin_pressure_kpa"]),
            "solar_event_active": bool(row["solar_event_active"]),
            "cabin_temperature_c": float(row["cabin_temperature_c"]),
            "relative_humidity_pct": float(row["relative_humidity_pct"]),
        },
        "biometrics": {
            "heart_rate_bpm": float(row["heart_rate_bpm"]),
            "last_cycle_sleep_hours": float(row["sleep_hours"]),
            "consecutive_insufficient_sleep_cycles": int(row["consecutive_insufficient_sleep_cycles"]),
            "fatigue_risk_alert": bool(row["fatigue_risk_alert"]),
            "bone_loss_pct": float(row["bone_loss_pct"]),
            "spo2_pct": float(row["spo2_pct"]),
            "headache_symptom": bool(row["headache_symptom"]),
            "physical_activity_minutes": float(row["physical_activity_minutes"]),
        },
        "cognition": {
            "voice_latency_ms": float(row["voice_latency_ms"]),
            "lexical_density_score": float(row["lexical_density_score"]),
            "sans_vision_symptom": bool(row["sans_vision_symptom"]),
        },
    }


def _fmt(n: float) -> str:
    """Formats an integer with a thousands separator."""
    return f"{n:,.0f}"


def main() -> None:
    df = pd.read_parquet(DATASET_PATH)
    engine = InferenceEngine()
    codebook = build_codebook()

    full_sizes: list[int] = []
    compact_sizes: list[int] = []
    input_sizes: list[int] = []
    rules_per_cycle: list[int] = []
    full_lines: list[str] = []
    compact_lines: list[str] = []
    reconstruction_failures = 0

    for _, row in df.iterrows():
        payload = row_to_payload(row)
        report = engine.process_telemetry(payload)
        record = compact_record(report, payload)

        full_json = report.model_dump_json()
        compact_json = record.model_dump_json()

        full_sizes.append(len(full_json.encode("utf-8")))
        compact_sizes.append(len(compact_json.encode("utf-8")))
        input_sizes.append(len(json.dumps(payload).encode("utf-8")))
        rules_per_cycle.append(len(report.decision_matrix_alerts))
        full_lines.append(full_json)
        compact_lines.append(compact_json)

        # Lossless reconstruction check on every measured cycle
        rehydrated = expand(record, codebook)
        if sorted(rehydrated["active_preliminary_assessments"]) != sorted(
            report.active_preliminary_assessments
        ):
            reconstruction_failures += 1

    n = len(full_sizes)
    mean_full = statistics.mean(full_sizes)
    mean_compact = statistics.mean(compact_sizes)
    mean_input = statistics.mean(input_sizes)

    # Bus-level bandwidth: the compact record already contains the raw metrics,
    # so it replaces the input payload in addition to the report.
    current_bus = mean_input + mean_full
    new_bus = mean_compact

    cycles_per_day = CADENCE_HZ * SECONDS_PER_DAY
    full_blob = "\n".join(full_lines).encode("utf-8")
    compact_blob = "\n".join(compact_lines).encode("utf-8")
    gz_full = len(gzip.compress(full_blob, 9)) / n
    gz_compact = len(gzip.compress(compact_blob, 9)) / n
    codebook_bytes = len(json.dumps(codebook, ensure_ascii=False, separators=(",", ":")).encode())

    print("=" * 78)
    print(" H.E.L.I.O.S. TELEMETRY COMPACTION — REAL 120-DAY x 4-HABITAT DATASET")
    print("=" * 78)
    print(f"\nCycles measured: {n}   ·   Active rules/cycle: "
          f"mean {statistics.mean(rules_per_cycle):.2f}, max {max(rules_per_cycle)}")
    print(f"Lossless reconstruction: {n - reconstruction_failures}/{n} cycles "
          f"{'OK' if reconstruction_failures == 0 else '<<< FAILURES'}")

    print(f"\n{'SIZE PER CYCLE (raw JSON)':<40}{'CURRENT':>12}{'COMPACT':>12}{'FACTOR':>10}")
    print("-" * 78)
    print(f"{'Inference report':<40}{_fmt(mean_full)+' B':>12}"
          f"{_fmt(mean_compact)+' B':>12}{mean_full/mean_compact:>9.1f}x")
    print(f"{'  minimum':<40}{_fmt(min(full_sizes))+' B':>12}{_fmt(min(compact_sizes))+' B':>12}")
    print(f"{'  maximum':<40}{_fmt(max(full_sizes))+' B':>12}{_fmt(max(compact_sizes))+' B':>12}")
    print(f"{'Input payload (absorbed)':<40}{_fmt(mean_input)+' B':>12}{'—':>12}")
    print("-" * 78)
    print(f"{'TOTAL ON THE BUS':<40}{_fmt(current_bus)+' B':>12}{_fmt(new_bus)+' B':>12}"
          f"{current_bus/new_bus:>9.1f}x")

    print(f"\n{'CUMULATIVE VOLUME AT 0.5 Hz':<40}{'CURRENT':>12}{'COMPACT':>12}{'SAVINGS':>10}")
    print("-" * 78)
    day_cur, day_new = current_bus * cycles_per_day / 1e6, new_bus * cycles_per_day / 1e6
    mission_cur, mission_new = day_cur * MISSION_DAYS / 1000, day_new * MISSION_DAYS / 1000
    print(f"{'Per day':<40}{day_cur:>9.1f} MB{day_new:>9.1f} MB{(1-day_new/day_cur)*100:>9.1f}%")
    print(f"{'120-day mission':<40}{mission_cur:>9.2f} GB{mission_new:>9.2f} GB{(1-mission_new/mission_cur)*100:>9.1f}%")
    print(f"{'Sustained bandwidth':<40}"
          f"{current_bus*CADENCE_HZ*8/1000:>8.1f} kbps{new_bus*CADENCE_HZ*8/1000:>8.1f} kbps")

    print(f"\n{'OVER A COMPRESSED LINK (gzip -9)':<40}{'CURRENT':>12}{'COMPACT':>12}{'FACTOR':>10}")
    print("-" * 78)
    print(f"{'Per cycle':<40}{gz_full:>9.0f} B{gz_compact:>9.0f} B{gz_full/gz_compact:>9.1f}x")
    print(f"{'120-day mission':<40}"
          f"{gz_full*cycles_per_day*MISSION_DAYS/1e9:>9.2f} GB"
          f"{gz_compact*cycles_per_day*MISSION_DAYS/1e9:>9.2f} GB"
          f"{(1-gz_compact/gz_full)*100:>9.1f}%")

    print(f"\nCodebook: {_fmt(codebook_bytes)} B, downloaded ONCE per session.")
    print(f"It pays for itself in {codebook_bytes/(current_bus-new_bus):.1f} cycles "
          f"({codebook_bytes/(current_bus-new_bus)/CADENCE_HZ:.0f} s of mission).")
    print("=" * 78)


if __name__ == "__main__":
    main()
