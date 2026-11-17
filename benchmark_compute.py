"""
H.E.L.I.O.S. computational resource evaluation and profiling script.
Measures inference latency, throughput, RAM usage and bus consumption to assess
deployment viability on aerospace onboard computers (SBC / RAD750).
"""

import json
import logging
import os
import sys
import time
import tracemalloc
import numpy as np

# Silence logging during the high-performance benchmark
logging.disable(logging.CRITICAL)

from helios_inference.services.inference_engine import InferenceEngine

def run_benchmark(iteration_count: int = 5000) -> dict[str, float]:
    engine = InferenceEngine()

    sample_payload = {
        "mission_id": "ARES-VI-MARS-EXPEDITION",
        "mission_day": 120,
        "astronaut_id": "ASTRO-HELIOS-01",
        "environment": {
            "co2_mmHg": 3.4,
            "cumulative_radiation_mSv": 85.0,
            "cabin_pressure_kpa": 101.3,
            "solar_event_active": False,
        },
        "biometrics": {
            "heart_rate_bpm": 68.0,
            "last_cycle_sleep_hours": 5.8,
            "bone_loss_pct": 1.8,
            "fatigue_risk_alert": False,
        },
        "cognition": {
            "voice_latency_ms": 720.0,
            "lexical_density_score": 0.82,
            "sans_vision_symptom": True,
        },
    }

    # Warm-up phase
    for _ in range(100):
        engine.process_telemetry(sample_payload)

    # Dynamic memory measurement
    tracemalloc.start()
    tracemalloc.reset_peak()

    # Timing with a high-resolution clock
    start = time.perf_counter()
    final_report = None
    for _ in range(iteration_count):
        final_report = engine.process_telemetry(sample_payload)
    end = time.perf_counter()

    _, peak_memory_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    total_time = end - start
    time_per_inference_ms = (total_time / iteration_count) * 1000.0
    time_per_inference_us = time_per_inference_ms * 1000.0
    throughput_inf_per_sec = iteration_count / total_time

    payload_bytes = len(json.dumps(sample_payload).encode("utf-8"))
    report_bytes = len(final_report.model_dump_json().encode("utf-8")) if final_report else 0

    return {
        "iterations": float(iteration_count),
        "mean_latency_us": round(time_per_inference_us, 2),
        "mean_latency_ms": round(time_per_inference_ms, 4),
        "throughput_per_second": round(throughput_inf_per_sec, 1),
        "peak_memory_kb": round(peak_memory_bytes / 1024.0, 2),
        "input_payload_bytes": float(payload_bytes),
        "output_report_bytes": float(report_bytes),
    }

if __name__ == "__main__":
    metrics = run_benchmark(5000)
    print("=== H.E.L.I.O.S. COMPUTATIONAL BENCHMARK RESULTS ===")
    print(json.dumps(metrics, indent=2))
