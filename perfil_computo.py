"""
Perfilado de recursos computacionales de H.E.L.I.O.S. por subsistema.

Amplía benchmark_computo.py desglosando el coste de cada uno de los 4 cerebros,
el evaluador de la matriz de decisiones y la serialización Pydantic, además de
medir la huella de memoria residente real del proceso y el ciclo de trabajo
(duty cycle) a la cadencia operativa nominal de la misión.
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

from helios_inference.cerebros.cerebro_1_ambiental import CerebroAmbiental
from helios_inference.cerebros.cerebro_2_biometrico import CerebroBiometrico
from helios_inference.cerebros.cerebro_3_grafo_fusion import CerebroGrafoFusion
from helios_inference.cerebros.cerebro_4_astra import CerebroCognitivoAstra
from helios_inference.services.decision_matrix_evaluator import DecisionMatrixEvaluator
from helios_inference.services.inference_engine import InferenceEngine

CADENCIA_TELEMETRIA_HZ = 0.5  # 1 muestra cada 2 s (intervalo_emision_segundos)

PAYLOAD: dict[str, Any] = {
    "id_mision": "ARES-VI-MARS-EXPEDITION",
    "dia_mision": 120,
    "astronauta_id": "ASTRO-HELIOS-01",
    "entorno": {
        "co2_mmHg": 3.4,
        "radiacion_acumulada_mSv": 85.0,
        "presion_cabina_kpa": 101.3,
        "evento_solar_activo": False,
    },
    "biometria": {
        "ritmo_cardiaco_bpm": 68.0,
        "horas_sueno_ultimo_ciclo": 5.8,
        "perdida_osea_pct": 1.8,
        "alerta_riesgo_fatiga": False,
    },
    "cognicion": {
        "latencia_voz_ms": 720.0,
        "densidad_lexica_score": 0.82,
        "sans_sintoma_vision": True,
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


def memoria_residente_mb() -> float:
    """Devuelve el working set del proceso actual en MiB (API Win32).

    Las firmas de argtypes/restype son obligatorias: sin ellas ctypes trunca el
    puntero a 32 bits en Windows x64 y la llamada falla devolviendo cero.
    """
    contadores = _PROCESS_MEMORY_COUNTERS()
    contadores.cb = ctypes.sizeof(_PROCESS_MEMORY_COUNTERS)
    if not _psapi.GetProcessMemoryInfo(
        _kernel32.GetCurrentProcess(), ctypes.byref(contadores), contadores.cb
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    return contadores.WorkingSetSize / (1024.0 * 1024.0)


def cronometrar(etiqueta: str, fn: Callable[[], Any], repeticiones: int = 20000) -> dict[str, float]:
    """Mide la latencia de una operación aislada con reloj de alta resolución."""
    for _ in range(500):  # calentamiento
        fn()
    muestras: list[float] = []
    for _ in range(7):
        inicio = time.perf_counter()
        for _ in range(repeticiones // 7):
            fn()
        muestras.append((time.perf_counter() - inicio) / (repeticiones // 7))
    mediana_us = statistics.median(muestras) * 1e6
    return {"etiqueta": etiqueta, "latencia_us": round(mediana_us, 2)}


def main() -> None:
    base_mb = memoria_residente_mb()

    c1 = CerebroAmbiental()
    c2 = CerebroBiometrico()
    c3 = CerebroGrafoFusion()
    c4 = CerebroCognitivoAstra()
    matriz = DecisionMatrixEvaluator()
    motor = InferenceEngine(c1, c2, c3, c4, matriz)

    entorno = PAYLOAD["entorno"]
    biometria = PAYLOAD["biometria"]
    cognicion = PAYLOAD["cognicion"]

    v_amb, _ = c1.procesar(entorno)
    v_bio, est_c2 = c2.procesar(datos_biometria=biometria, dia_mision=120, sintoma_sans=True)

    etapas = [
        cronometrar("Cerebro 1 - Ambiental", lambda: c1.procesar(entorno)),
        cronometrar("Cerebro 2 - Biometrico",
                    lambda: c2.procesar(datos_biometria=biometria, dia_mision=120, sintoma_sans=True)),
        cronometrar("Cerebro 3 - Kronecker", lambda: c3.fusionar(v_amb, v_bio)),
        cronometrar("Cerebro 4 - ASTRA cognitivo",
                    lambda: c4.procesar(datos_cognicion=cognicion, estado_biometrico=est_c2,
                                        ritmo_cardiaco_bpm=68.0)),
        cronometrar("Matriz decisiones (15 reglas)", lambda: matriz.evaluar_telemetria(PAYLOAD), 10000),
        cronometrar("np.kron aislado (R3 x R4)", lambda: np.kron(v_amb, v_bio)),
    ]

    ciclo = cronometrar("CICLO COMPLETO procesar_telemetria",
                        lambda: motor.procesar_telemetria(PAYLOAD), 7000)
    reporte = motor.procesar_telemetria(PAYLOAD)
    serializacion = cronometrar("Serializacion Pydantic -> JSON",
                                lambda: reporte.model_dump_json(), 7000)

    motor_mb = memoria_residente_mb() - base_mb
    ciclo_us = ciclo["latencia_us"]
    suma_etapas = sum(e["latencia_us"] for e in etapas[:5])

    print("=" * 74)
    print(" PERFIL COMPUTACIONAL H.E.L.I.O.S. - DESGLOSE POR SUBSISTEMA")
    print("=" * 74)
    print(f"\n{'ETAPA':<36}{'LATENCIA':>13}{'% DEL CICLO':>14}")
    print("-" * 74)
    for e in etapas:
        pct = e["latencia_us"] / ciclo_us * 100.0
        print(f"{e['etiqueta']:<36}{e['latencia_us']:>10.2f} us{pct:>13.1f}%")
    print("-" * 74)
    pct_ser = serializacion["latencia_us"] / ciclo_us * 100.0
    print(f"{serializacion['etiqueta']:<36}{serializacion['latencia_us']:>10.2f} us{pct_ser:>13.1f}%")
    print(f"{'Orquestacion + Pydantic (resto)':<36}"
          f"{ciclo_us - suma_etapas:>10.2f} us{(ciclo_us - suma_etapas) / ciclo_us * 100.0:>13.1f}%")
    print("=" * 74)
    print(f"{'CICLO COMPLETO':<36}{ciclo_us:>10.2f} us{100.0:>13.1f}%")
    print("=" * 74)

    rendimiento = 1e6 / ciclo_us
    duty = ciclo_us * 1e-6 * CADENCIA_TELEMETRIA_HZ * 100.0
    print(f"\nRendimiento maximo           : {rendimiento:,.0f} inferencias/s (1 nucleo)")
    print(f"Cadencia operativa nominal   : {CADENCIA_TELEMETRIA_HZ} Hz (1 muestra / 2 s)")
    print(f"CICLO DE TRABAJO (duty cycle): {duty:.6f} % de un nucleo")
    print(f"Margen sobre la cadencia     : x{rendimiento / CADENCIA_TELEMETRIA_HZ:,.0f}")
    print(f"Huella del motor en RAM      : {motor_mb:.2f} MiB (4 cerebros + matriz instanciados)")
    print(f"Working set total del proceso: {memoria_residente_mb():.2f} MiB (incluye CPython + NumPy)")

    entrada = len(json.dumps(PAYLOAD).encode())
    salida = len(reporte.model_dump_json().encode())
    bps = (entrada + salida) * CADENCIA_TELEMETRIA_HZ
    print(f"\nPayload entrada / salida     : {entrada} B / {salida} B")
    print(f"Caudal de bus a {CADENCIA_TELEMETRIA_HZ} Hz        : {bps:,.0f} B/s  ({bps * 8 / 1000:.1f} kbit/s)")
    print(f"Volumen diario de telemetria : {bps * 86400 / 1e6:.1f} MB/dia")
    print(f"Volumen mision 120 dias      : {bps * 86400 * 120 / 1e9:.2f} GB")


if __name__ == "__main__":
    main()
