"""
H.E.L.I.O.S. computational resource profiling per subsystem.

Extends benchmark_compute.py by breaking down the cost of each of the 4 brains,
the decision matrix evaluator and the Pydantic serialization, in addition to
measuring the real resident memory footprint of the process and the duty cycle at
the nominal operational cadence of the mission.
"""

import ctypes
import json
import logging
import statistics
import time
from ctypes import wintypes
from typing import Any, Callable

import numpy as np

logging.disable(logging.CRITICAL)

from helios_inference.brains.brain_1_environmental import EnvironmentalBrain
from helios_inference.brains.brain_2_biometric import BiometricBrain
from helios_inference.brains.brain_3_fusion_graph import FusionGraphBrain
from helios_inference.brains.brain_4_astra import AstraCognitiveBrain
from helios_inference.services.decision_matrix_evaluator import DecisionMatrixEvaluator
from helios_inference.services.inference_engine import InferenceEngine

TELEMETRY_CADENCE_HZ = 0.5  # 1 sample every 2 s (emission_interval_seconds)

PAYLOAD: dict[str, Any] = {
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


class _PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


_psapi = ctypes.WinDLL("psapi")
_kernel32 = ctypes.WinDLL("kernel32")
_psapi.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(_PROCESS_MEMORY_COUNTERS),
    wintypes.DWORD,
]
_psapi.GetProcessMemoryInfo.restype = wintypes.BOOL


def resident_memory_mb() -> float:
    """Returns the working set of the current process in MiB (Win32 API).

    The argtypes/restype signatures are mandatory: without them ctypes truncates
    the pointer to 32 bits on Windows x64 and the call fails returning zero.
    """
    counters = _PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(_PROCESS_MEMORY_COUNTERS)
    if not _psapi.GetProcessMemoryInfo(
        _kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return counters.WorkingSetSize / (1024.0 * 1024.0)


def stopwatch(label: str, fn: Callable[[], Any], repetitions: int = 20000) -> dict[str, float]:
    """Measures the latency of an isolated operation with a high-resolution clock."""
    for _ in range(500):  # warm-up
        fn()
    samples: list[float] = []
    for _ in range(7):
        start = time.perf_counter()
        for _ in range(repetitions // 7):
            fn()
        samples.append((time.perf_counter() - start) / (repetitions // 7))
    median_us = statistics.median(samples) * 1e6
    return {"label": label, "latency_us": round(median_us, 2)}


def main() -> None:
    base_mb = resident_memory_mb()

    b1 = EnvironmentalBrain()
    b2 = BiometricBrain()
    b3 = FusionGraphBrain()
    b4 = AstraCognitiveBrain()
    matrix = DecisionMatrixEvaluator()
    engine = InferenceEngine(b1, b2, b3, b4, matrix)

    environment = PAYLOAD["environment"]
    biometrics = PAYLOAD["biometrics"]
    cognition = PAYLOAD["cognition"]

    v_env, _ = b1.process(environment)
    v_bio, state_b2 = b2.process(biometrics_data=biometrics, mission_day=120, sans_symptom=True)

    stages = [
        stopwatch("Brain 1 - Environmental", lambda: b1.process(environment)),
        stopwatch("Brain 2 - Biometric",
                  lambda: b2.process(biometrics_data=biometrics, mission_day=120, sans_symptom=True)),
        stopwatch("Brain 3 - Kronecker", lambda: b3.fuse(v_env, v_bio)),
        stopwatch("Brain 4 - ASTRA cognitive",
                  lambda: b4.process(cognition_data=cognition, biometric_state=state_b2,
                                     heart_rate_bpm=68.0)),
        stopwatch("Decision matrix (15 rules)", lambda: matrix.evaluate_telemetry(PAYLOAD), 10000),
        stopwatch("np.kron isolated (R3 x R4)", lambda: np.kron(v_env, v_bio)),
    ]

    cycle = stopwatch("FULL CYCLE process_telemetry",
                      lambda: engine.process_telemetry(PAYLOAD), 7000)
    report = engine.process_telemetry(PAYLOAD)
    serialization = stopwatch("Pydantic -> JSON serialization",
                              lambda: report.model_dump_json(), 7000)

    engine_mb = resident_memory_mb() - base_mb
    cycle_us = cycle["latency_us"]
    stage_sum = sum(s["latency_us"] for s in stages[:5])

    print("=" * 74)
    print(" H.E.L.I.O.S. COMPUTATIONAL PROFILE - BREAKDOWN BY SUBSYSTEM")
    print("=" * 74)
    print(f"\n{'STAGE':<36}{'LATENCY':>13}{'% OF CYCLE':>14}")
    print("-" * 74)
    for s in stages:
        pct = s["latency_us"] / cycle_us * 100.0
        print(f"{s['label']:<36}{s['latency_us']:>10.2f} us{pct:>13.1f}%")
    print("-" * 74)
    pct_ser = serialization["latency_us"] / cycle_us * 100.0
    print(f"{serialization['label']:<36}{serialization['latency_us']:>10.2f} us{pct_ser:>13.1f}%")
    print(f"{'Orchestration + Pydantic (rest)':<36}"
          f"{cycle_us - stage_sum:>10.2f} us{(cycle_us - stage_sum) / cycle_us * 100.0:>13.1f}%")
    print("=" * 74)
    print(f"{'FULL CYCLE':<36}{cycle_us:>10.2f} us{100.0:>13.1f}%")
    print("=" * 74)

    throughput = 1e6 / cycle_us
    duty = cycle_us * 1e-6 * TELEMETRY_CADENCE_HZ * 100.0
    print(f"\nMaximum throughput           : {throughput:,.0f} inferences/s (1 core)")
    print(f"Nominal operational cadence  : {TELEMETRY_CADENCE_HZ} Hz (1 sample / 2 s)")
    print(f"DUTY CYCLE                   : {duty:.6f} % of one core")
    print(f"Margin over the cadence      : x{throughput / TELEMETRY_CADENCE_HZ:,.0f}")
    print(f"Engine RAM footprint         : {engine_mb:.2f} MiB (4 brains + matrix instantiated)")
    print(f"Total process working set    : {resident_memory_mb():.2f} MiB (includes CPython + NumPy)")

    input_bytes = len(json.dumps(PAYLOAD).encode())
    output_bytes = len(report.model_dump_json().encode())
    bps = (input_bytes + output_bytes) * TELEMETRY_CADENCE_HZ
    print(f"\nInput / output payload       : {input_bytes} B / {output_bytes} B")
    print(f"Bus bandwidth at {TELEMETRY_CADENCE_HZ} Hz      : {bps:,.0f} B/s  ({bps * 8 / 1000:.1f} kbit/s)")
    print(f"Daily telemetry volume       : {bps * 86400 / 1e6:.1f} MB/day")
    print(f"120-day mission volume       : {bps * 86400 * 120 / 1e9:.2f} GB")


if __name__ == "__main__":
    main()
