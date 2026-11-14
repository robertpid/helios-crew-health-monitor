"""
Pruebas automatizadas para el simulador de 120 días multihábitat.

Verifica la generación de las series temporales de 120 días para:
Estación Espacial, Base Lunar, Nave Espacial y Base de Marte.
Valida cálculos biomecánicos (pérdida ósea por gravedad), dosimetría y cruces lógicos.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from helios_simulator.config import LimitesNasaConfig
from helios_simulator.domain.enums import EntornoMision
from helios_simulator.services.multi_habitat_simulator import SimuladorMultihabitat120Dias


@pytest.fixture
def simulador() -> SimuladorMultihabitat120Dias:
    """Fixture que provee una instancia reproducible del simulador."""
    return SimuladorMultihabitat120Dias(
        config_limites=LimitesNasaConfig(),
        semilla_aleatoria=42,
    )


def test_generacion_120_dias_un_habitat(simulador: SimuladorMultihabitat120Dias) -> None:
    """Verifica que simular un hábitat produzca exactamente 120 observaciones diarias."""
    df_iss = simulador.simular_habitat(EntornoMision.ESTACION_ESPACIAL, total_dias=120)

    assert isinstance(df_iss, pd.DataFrame)
    assert len(df_iss) == 120
    assert df_iss["dia_mision"].tolist() == list(range(1, 121))
    assert (df_iss["entorno_mision"] == "estacion_espacial").all()
    assert (df_iss["gravedad_g"] == 0.0).all()


def test_generacion_consolidada_cuatro_habitats(simulador: SimuladorMultihabitat120Dias) -> None:
    """Verifica la generación de la tabla maestra con 4 hábitats (480 filas totales)."""
    master_df = simulador.simular_todos_los_habitats(total_dias=120)

    assert len(master_df) == 480  # 4 hábitats x 120 días
    habitats_esperados = {"estacion_espacial", "base_lunar", "nave_espacial", "base_marte"}
    assert set(master_df["entorno_mision"].unique()) == habitats_esperados

    # Verificación de columnas requeridas
    columnas_mandatorias = [
        "dia_mision", "entorno_mision", "gravedad_g",
        "co2_mmHg", "radiacion_tasa_diaria_mSv", "radiacion_acumulada_mSv",
        "presion_cabina_kpa", "ritmo_cardiaco_bpm", "horas_sueno",
        "alerta_riesgo_fatiga", "perdida_osea_pct", "latencia_voz_ms",
        "densidad_lexica_score", "incongruencia_estres_oculto", "sans_sintoma_vision",
        "total_alertas_activas", "porcentaje_presupuesto_radiacion_carrera",
    ]
    for col in columnas_mandatorias:
        assert col in master_df.columns, f"Falta la columna requerida: {col}"


def test_perdida_osea_ponderada_por_gravedad(simulador: SimuladorMultihabitat120Dias) -> None:
    """
    Valida la pérdida ósea acumulada al Día 120 según el vector gravitatorio:
    - ISS (0g): 6.0%
    - Nave Espacial (0g): 6.0%
    - Luna (0.166g): ~5.0%
    - Marte (0.38g): ~3.72%
    """
    df_iss = simulador.simular_habitat(EntornoMision.ESTACION_ESPACIAL, total_dias=120)
    df_luna = simulador.simular_habitat(EntornoMision.BASE_LUNAR, total_dias=120)
    df_nave = simulador.simular_habitat(EntornoMision.NAVE_ESPACIAL, total_dias=120)
    df_marte = simulador.simular_habitat(EntornoMision.BASE_MARTE, total_dias=120)

    perdida_iss_dia_120 = df_iss.loc[df_iss["dia_mision"] == 120, "perdida_osea_pct"].values[0]
    perdida_nave_dia_120 = df_nave.loc[df_nave["dia_mision"] == 120, "perdida_osea_pct"].values[0]
    perdida_luna_dia_120 = df_luna.loc[df_luna["dia_mision"] == 120, "perdida_osea_pct"].values[0]
    perdida_marte_dia_120 = df_marte.loc[df_marte["dia_mision"] == 120, "perdida_osea_pct"].values[0]

    assert perdida_iss_dia_120 == 6.00
    assert perdida_nave_dia_120 == 6.00
    assert pytest.approx(perdida_luna_dia_120, abs=0.05) == 5.00
    assert pytest.approx(perdida_marte_dia_120, abs=0.05) == 3.72


def test_gradiente_radiacion_entre_habitats(simulador: SimuladorMultihabitat120Dias) -> None:
    """Verifica que la exposición acumulada a 120 días refleje los perfiles radiológicos reales."""
    master_df = simulador.simular_todos_los_habitats(total_dias=120)
    resumen = simulador.generar_resumen_comparativo(master_df)

    rad_iss = resumen.loc["estacion_espacial", "radiacion_final_mSv"]
    rad_nave = resumen.loc["nave_espacial", "radiacion_final_mSv"]
    rad_marte = resumen.loc["base_marte", "radiacion_final_mSv"]

    # La nave en espacio profundo (GCR sin atmósfera ni escudo) acumula sustancialmente más radiación que la ISS
    assert rad_nave > rad_iss
    # La superficie de Marte tiene protección parcial por el cuerpo del planeta vs espacio interplanetario
    assert rad_nave > rad_marte


def test_cruce_latencia_verbal_vectorizado(simulador: SimuladorMultihabitat120Dias) -> None:
    """Valida que cuando CO2 > 2.5 o horas_sueno < 6.0, la latencia verbal esté en 600-900ms."""
    master_df = simulador.simular_todos_los_habitats(total_dias=120)

    # Filas con degradación
    mascara_degradada = (master_df["co2_mmHg"] > 2.5) | (master_df["horas_sueno"] < 6.0)
    latencias_degradadas = master_df.loc[mascara_degradada, "latencia_voz_ms"]
    assert (latencias_degradadas >= 600.0).all()
    assert (latencias_degradadas <= 900.0).all()

    # Filas nominales
    mascara_nominal = (master_df["co2_mmHg"] <= 2.5) & (master_df["horas_sueno"] >= 6.0)
    latencias_nominales = master_df.loc[mascara_nominal, "latencia_voz_ms"]
    assert (latencias_nominales < 300.0).all()


def test_incongruencia_estres_oculto(simulador: SimuladorMultihabitat120Dias) -> None:
    """Valida la detección de estrés encubierto (taquicardia > 95 bpm con densidad léxica >= 0.75)."""
    master_df = simulador.simular_todos_los_habitats(total_dias=120)

    incongruencias = master_df.loc[master_df["incongruencia_estres_oculto"] == True]
    assert len(incongruencias) > 0  # Debe haber ocurrido al menos una vez en 480 días simulados
    assert (incongruencias["ritmo_cardiaco_bpm"] > 95.0).all()
    assert (incongruencias["densidad_lexica_score"] >= 0.75).all()


def test_exportacion_dataset(simulador: SimuladorMultihabitat120Dias, tmp_path: Path) -> None:
    """Valida que los exportadores generen archivos válidos en CSV, Parquet y JSONL."""
    master_df = simulador.simular_todos_los_habitats(total_dias=120)
    rutas = simulador.exportar_dataset(
        df=master_df,
        directorio_destino=tmp_path,
        nombre_base="test_120_dias",
    )

    assert rutas["csv"].exists()
    assert rutas["parquet"].exists()
    assert rutas["jsonl"].exists()

    # Lectura de verificación
    df_csv = pd.read_csv(rutas["csv"])
    df_parquet = pd.read_parquet(rutas["parquet"])
    assert len(df_csv) == 480
    assert len(df_parquet) == 480
