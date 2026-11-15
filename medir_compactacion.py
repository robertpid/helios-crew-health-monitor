"""
Medición del ahorro de volumen por compactación de telemetría en H.E.L.I.O.S.

Contrasta el reporte consolidado (texto descriptivo en cada ciclo) contra el
registro compacto (códigos de regla + valores numéricos) sobre el dataset real
de 120 días x 4 hábitats, de modo que la distribución de alertas sea la de la
misión y no la de un payload elegido a mano.

Mide además el tamaño tras compresión gzip: un enlace real comprime, y el texto
repetitivo comprime mucho mejor que los números, así que la comparación honesta
debe incluir ambos ejes.
"""

import gzip
import json
import logging
import statistics
from pathlib import Path
from typing import Any

import pandas as pd

logging.disable(logging.CRITICAL)

from helios_inference.domain.telemetry_codebook import construir_codebook
from helios_inference.services.inference_engine import InferenceEngine
from helios_inference.services.telemetry_compactor import compactar, expandir

CADENCIA_HZ = 0.5
DIAS_MISION = 120
SEGUNDOS_DIA = 86_400
RUTA_DATASET = Path("datos_generados/telemetria_120_dias_cuatro_habitats.parquet")


def fila_a_payload(fila: pd.Series) -> dict[str, Any]:
    """Proyecta una fila del dataset multihábitat al contrato de telemetría."""
    return {
        "id_mision": f"{fila['entorno_mision']}-EXPEDITION",
        "dia_mision": int(fila["dia_mision"]),
        "astronauta_id": "ASTRO-HELIOS-01",
        "entorno": {
            "co2_mmHg": float(fila["co2_mmHg"]),
            "radiacion_acumulada_mSv": float(fila["radiacion_acumulada_mSv"]),
            "presion_cabina_kpa": float(fila["presion_cabina_kpa"]),
            "evento_solar_activo": bool(fila["evento_solar_activo"]),
            "temperatura_cabina_c": float(fila["temperatura_cabina_c"]),
            "humedad_relativa_pct": float(fila["humedad_relativa_pct"]),
        },
        "biometria": {
            "ritmo_cardiaco_bpm": float(fila["ritmo_cardiaco_bpm"]),
            "horas_sueno_ultimo_ciclo": float(fila["horas_sueno"]),
            "ciclos_sueno_insuficiente_consecutivos": int(fila["ciclos_sueno_insuficiente_consecutivos"]),
            "alerta_riesgo_fatiga": bool(fila["alerta_riesgo_fatiga"]),
            "perdida_osea_pct": float(fila["perdida_osea_pct"]),
            "spo2_pct": float(fila["spo2_pct"]),
            "dolor_cabeza_sintoma": bool(fila["dolor_cabeza_sintoma"]),
            "actividad_fisica_minutos": float(fila["actividad_fisica_minutos"]),
        },
        "cognicion": {
            "latencia_voz_ms": float(fila["latencia_voz_ms"]),
            "densidad_lexica_score": float(fila["densidad_lexica_score"]),
            "sans_sintoma_vision": bool(fila["sans_sintoma_vision"]),
        },
    }


def _fmt(n: float) -> str:
    """Formatea un entero con separador de millares."""
    return f"{n:,.0f}"


def main() -> None:
    df = pd.read_parquet(RUTA_DATASET)
    motor = InferenceEngine()
    codebook = construir_codebook()

    completos: list[int] = []
    compactos: list[int] = []
    entradas: list[int] = []
    reglas_por_ciclo: list[int] = []
    lineas_completo: list[str] = []
    lineas_compacto: list[str] = []
    fallos_reconstruccion = 0

    for _, fila in df.iterrows():
        payload = fila_a_payload(fila)
        reporte = motor.procesar_telemetria(payload)
        registro = compactar(reporte, payload)

        json_completo = reporte.model_dump_json()
        json_compacto = registro.model_dump_json()

        completos.append(len(json_completo.encode("utf-8")))
        compactos.append(len(json_compacto.encode("utf-8")))
        entradas.append(len(json.dumps(payload).encode("utf-8")))
        reglas_por_ciclo.append(len(reporte.alertas_matriz_decisiones))
        lineas_completo.append(json_completo)
        lineas_compacto.append(json_compacto)

        # Verificación de reconstrucción sin pérdida en cada ciclo medido
        rehidratado = expandir(registro, codebook)
        if sorted(rehidratado["evaluaciones_preliminares_activas"]) != sorted(
            reporte.evaluaciones_preliminares_activas
        ):
            fallos_reconstruccion += 1

    n = len(completos)
    media_completo = statistics.mean(completos)
    media_compacto = statistics.mean(compactos)
    media_entrada = statistics.mean(entradas)

    # Caudal a nivel de bus: el registro compacto ya contiene las métricas crudas,
    # de modo que sustituye al payload de entrada además de al reporte.
    bus_actual = media_entrada + media_completo
    bus_nuevo = media_compacto

    ciclos_dia = CADENCIA_HZ * SEGUNDOS_DIA
    blob_completo = "\n".join(lineas_completo).encode("utf-8")
    blob_compacto = "\n".join(lineas_compacto).encode("utf-8")
    gz_completo = len(gzip.compress(blob_completo, 9)) / n
    gz_compacto = len(gzip.compress(blob_compacto, 9)) / n
    codebook_bytes = len(json.dumps(codebook, ensure_ascii=False, separators=(",", ":")).encode())

    print("=" * 78)
    print(" COMPACTACIÓN DE TELEMETRÍA H.E.L.I.O.S. — DATASET REAL 120 DÍAS x 4 HÁBITATS")
    print("=" * 78)
    print(f"\nCiclos medidos: {n}   ·   Reglas activas/ciclo: "
          f"media {statistics.mean(reglas_por_ciclo):.2f}, máx {max(reglas_por_ciclo)}")
    print(f"Reconstrucción sin pérdida: {n - fallos_reconstruccion}/{n} ciclos "
          f"{'OK' if fallos_reconstruccion == 0 else '<<< FALLOS'}")

    print(f"\n{'TAMAÑO POR CICLO (JSON crudo)':<40}{'ACTUAL':>12}{'COMPACTO':>12}{'FACTOR':>10}")
    print("-" * 78)
    print(f"{'Reporte de inferencia':<40}{_fmt(media_completo)+' B':>12}"
          f"{_fmt(media_compacto)+' B':>12}{media_completo/media_compacto:>9.1f}x")
    print(f"{'  mínimo':<40}{_fmt(min(completos))+' B':>12}{_fmt(min(compactos))+' B':>12}")
    print(f"{'  máximo':<40}{_fmt(max(completos))+' B':>12}{_fmt(max(compactos))+' B':>12}")
    print(f"{'Payload de entrada (absorbido)':<40}{_fmt(media_entrada)+' B':>12}{'—':>12}")
    print("-" * 78)
    print(f"{'TOTAL EN EL BUS':<40}{_fmt(bus_actual)+' B':>12}{_fmt(bus_nuevo)+' B':>12}"
          f"{bus_actual/bus_nuevo:>9.1f}x")

    print(f"\n{'VOLUMEN ACUMULADO A 0.5 Hz':<40}{'ACTUAL':>12}{'COMPACTO':>12}{'AHORRO':>10}")
    print("-" * 78)
    d_act, d_new = bus_actual * ciclos_dia / 1e6, bus_nuevo * ciclos_dia / 1e6
    m_act, m_new = d_act * DIAS_MISION / 1000, d_new * DIAS_MISION / 1000
    print(f"{'Por día':<40}{d_act:>9.1f} MB{d_new:>9.1f} MB{(1-d_new/d_act)*100:>9.1f}%")
    print(f"{'Misión de 120 días':<40}{m_act:>9.2f} GB{m_new:>9.2f} GB{(1-m_new/m_act)*100:>9.1f}%")
    print(f"{'Caudal sostenido':<40}"
          f"{bus_actual*CADENCIA_HZ*8/1000:>8.1f} kbps{bus_nuevo*CADENCIA_HZ*8/1000:>8.1f} kbps")

    print(f"\n{'SOBRE ENLACE COMPRIMIDO (gzip -9)':<40}{'ACTUAL':>12}{'COMPACTO':>12}{'FACTOR':>10}")
    print("-" * 78)
    print(f"{'Por ciclo':<40}{gz_completo:>9.0f} B{gz_compacto:>9.0f} B{gz_completo/gz_compacto:>9.1f}x")
    print(f"{'Misión de 120 días':<40}"
          f"{gz_completo*ciclos_dia*DIAS_MISION/1e9:>9.2f} GB"
          f"{gz_compacto*ciclos_dia*DIAS_MISION/1e9:>9.2f} GB"
          f"{(1-gz_compacto/gz_completo)*100:>9.1f}%")

    print(f"\nLibro de códigos: {_fmt(codebook_bytes)} B, descarga ÚNICA por sesión.")
    print(f"Se amortiza en {codebook_bytes/(bus_actual-bus_nuevo):.1f} ciclos "
          f"({codebook_bytes/(bus_actual-bus_nuevo)/CADENCIA_HZ:.0f} s de misión).")
    print("=" * 78)


if __name__ == "__main__":
    main()
