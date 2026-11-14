"""
Script de evaluación y perfilado de recursos computacionales de H.E.L.I.O.S.
Mide latencia de inferencia, throughput, memoria RAM y consumo de bus para
evaluar la viabilidad de despliegue en computadoras de abordo aeroespaciales (SBC / RAD750).
"""

import json
import logging
import os
import sys
import time
import tracemalloc
import numpy as np

# Silenciar logging durante benchmark de alto rendimiento
logging.disable(logging.CRITICAL)

from helios_inference.services.inference_engine import InferenceEngine

def ejecutar_benchmark(num_iteraciones: int = 5000) -> dict[str, float]:
    motor = InferenceEngine()

    payload_ejemplo = {
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

    # Fase de calentamiento (Warm-up)
    for _ in range(100):
        motor.procesar_telemetria(payload_ejemplo)

    # Medición de memoria dinámica
    tracemalloc.start()
    tracemalloc.reset_peak()

    # Medición de tiempo con reloj de alta resolución
    inicio = time.perf_counter()
    reporte_final = None
    for _ in range(num_iteraciones):
        reporte_final = motor.procesar_telemetria(payload_ejemplo)
    fin = time.perf_counter()

    _, memoria_pico_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tiempo_total = fin - inicio
    tiempo_por_inferencia_ms = (tiempo_total / num_iteraciones) * 1000.0
    tiempo_por_inferencia_us = tiempo_por_inferencia_ms * 1000.0
    throughput_infe_seg = num_iteraciones / tiempo_total

    payload_bytes = len(json.dumps(payload_ejemplo).encode("utf-8"))
    reporte_bytes = len(reporte_final.model_dump_json().encode("utf-8")) if reporte_final else 0

    return {
        "iteraciones": float(num_iteraciones),
        "latencia_media_us": round(tiempo_por_inferencia_us, 2),
        "latencia_media_ms": round(tiempo_por_inferencia_ms, 4),
        "throughput_por_segundo": round(throughput_infe_seg, 1),
        "memoria_pico_kb": round(memoria_pico_bytes / 1024.0, 2),
        "payload_entrada_bytes": float(payload_bytes),
        "reporte_salida_bytes": float(reporte_bytes),
    }

if __name__ == "__main__":
    metricas = ejecutar_benchmark(5000)
    print("=== RESULTADOS DEL BENCHMARK COMPUTACIONAL H.E.L.I.O.S. ===")
    print(json.dumps(metricas, indent=2))
