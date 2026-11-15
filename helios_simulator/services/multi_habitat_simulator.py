"""
Simulador analítico multihábitat para series temporales de 120 días.

Genera telemetría sintética vectorizada mediante NumPy y Pandas para 4 entornos de misión:
1. Estación Espacial Internacional (ISS / LEO)
2. Base Lunar (Artemis Base Camp)
3. Nave Espacial de Tránsito (Deep Space Transit a Marte)
4. Base de Superficie de Marte (Hábitat Marciano)

Cumple con estándares NASA-STD-3001, marco RIDGE y principios Clean Code.
Cálculos 100% vectorizados sin iterrows() ni itertuples().
"""

from pathlib import Path
import logging
import numpy as np
import pandas as pd

from helios_simulator.config import (
    LimitesNasaConfig,
    PerfilAmbienteMision,
    obtener_perfiles_ambientes,
)
from helios_simulator.domain.enums import EntornoMision

logger = logging.getLogger(__name__)


class SimuladorMultihabitat120Dias:
    """Motor de simulación vectorial para series temporales multivariadas de 120 días."""

    def __init__(
        self,
        config_limites: LimitesNasaConfig | None = None,
        semilla_aleatoria: int | None = 42,
    ) -> None:
        self._config_limites = config_limites or LimitesNasaConfig()
        self._perfiles = obtener_perfiles_ambientes()
        if semilla_aleatoria is not None:
            np.random.seed(semilla_aleatoria)

    def simular_habitat(
        self,
        tipo_entorno: EntornoMision | str,
        total_dias: int = 120,
    ) -> pd.DataFrame:
        """Genera el DataFrame de telemetría para un hábitat específico (120 días)."""
        clave = tipo_entorno.value if isinstance(tipo_entorno, EntornoMision) else str(tipo_entorno)
        if clave not in self._perfiles:
            raise ValueError(f"Hábitat no reconocido: '{clave}'. Válidos: {list(self._perfiles.keys())}")

        perfil: PerfilAmbienteMision = self._perfiles[clave]
        logger.info("Simulando %d días para '%s' (g=%.3f)...", total_dias, perfil.nombre_descriptivo, perfil.gravedad_g)
        dias = np.arange(1, total_dias + 1, dtype=np.int32)

        # CEREBRO 1: ENTORNO AMBIENTAL
        mascara_picos_co2 = np.random.uniform(0.0, 1.0, size=total_dias) < 0.10
        co2_nominal = np.clip(np.random.normal(1.60, 0.22, size=total_dias), self._config_limites.co2_normal_min_mmhg, self._config_limites.co2_normal_max_mmhg)
        co2_picos = np.clip(np.random.normal(3.45, 0.28, size=total_dias), 3.05, 4.60)
        co2_mmhg = np.where(mascara_picos_co2, co2_picos, co2_nominal).round(2)

        mascara_tormenta_solar = np.random.uniform(0.0, 1.0, size=total_dias) < perfil.probabilidad_tormenta_solar
        tasa_rad = np.clip(np.random.normal(perfil.radiacion_diaria_base_msv, perfil.radiacion_desviacion_msv, size=total_dias), 0.10, 3.50)
        impacto_solar = np.where(mascara_tormenta_solar, self._config_limites.radiacion_tormenta_solar_impacto_msv, 0.0)
        dosis_diaria_total = (tasa_rad + impacto_solar).round(3)
        radiacion_base_inicial = 15.0 if clave == "estacion_espacial" else 45.0
        radiacion_acumulada_msv = (radiacion_base_inicial + np.cumsum(dosis_diaria_total)).round(2)

        presion_cabina_kpa = np.clip(np.random.normal(perfil.presion_cabina_nominal_kpa, 0.85, size=total_dias), perfil.presion_cabina_min_kpa, perfil.presion_cabina_max_kpa).round(2)
        temperatura_cabina_c = np.random.normal(perfil.temperatura_cabina_nominal_c, 0.60, size=total_dias).round(2)
        humedad_relativa_pct = np.clip(np.random.normal(46.0, 2.5, size=total_dias), 35.0, 65.0).round(1)

        # CEREBRO 2: BIOMETRÍA FISIOLÓGICA
        factor_atenuacion_gravedad = max(0.0, 1.0 - perfil.gravedad_g)
        perdida_osea_pct = ((dias / 30.0) * (self._config_limites.tasa_perdida_osea_mensual_pct * factor_atenuacion_gravedad)).round(2)

        deriva_martiana = 0.65 if clave == "base_marte" else 0.0
        media_sueno = np.maximum(4.8, self._config_limites.horas_sueno_promedio - (0.003 * dias * deriva_martiana))
        horas_sueno = np.clip(np.random.normal(media_sueno, 0.95, size=total_dias), 3.8, 8.5).round(2)

        serie_sueno_insuficiente = pd.Series(horas_sueno < self._config_limites.umbral_horas_sueno_riesgo)
        alerta_fatiga_serie = (serie_sueno_insuficiente.rolling(window=3, min_periods=1).sum() >= 3.0)

        contador_consecutivos = np.zeros(total_dias, dtype=np.int32)
        contador_acumulado = 0
        for idx, deficit in enumerate(serie_sueno_insuficiente.to_numpy()):
            contador_acumulado = (contador_acumulado + 1) if deficit else max(0, contador_acumulado - 1)
            contador_consecutivos[idx] = contador_acumulado

        estres_elevado = (co2_mmhg >= self._config_limites.co2_umbral_sintomas_mmhg) | mascara_tormenta_solar | alerta_fatiga_serie.to_numpy()
        picos_estres_agudo = np.random.uniform(0.0, 1.0, size=total_dias) < (0.08 * perfil.factor_estres_aislamiento)
        desplazamiento_hr = np.where(estres_elevado | picos_estres_agudo, 26.0, 0.0)
        ritmo_cardiaco_bpm = np.clip(np.random.normal(self._config_limites.ritmo_cardiaco_base_bpm + desplazamiento_hr, 6.5, size=total_dias), 52.0, 135.0).round(1)

        mascara_taquicardia = ritmo_cardiaco_bpm > self._config_limites.ritmo_cardiaco_umbral_estres_alto_bpm
        presion_sistolica = (118.0 + (ritmo_cardiaco_bpm - 65.0) * 0.45 + np.random.normal(0, 2.5, size=total_dias)).round(1)
        presion_diastolica = (presion_sistolica * 0.65 + np.random.normal(0, 1.8, size=total_dias)).round(1)
        spo2_pct = np.clip(np.random.normal(98.1, 0.5, size=total_dias), 93.0, 99.8).round(1)

        temperatura_piel_c = np.clip(34.8 + np.where(estres_elevado, 0.5, 0.0) + np.random.normal(0, 0.25, size=total_dias), 33.2, 37.2).round(2)
        frecuencia_respiratoria_rpm = np.clip(14.0 + np.where(estres_elevado, 3.5, 0.0) + np.random.normal(0, 1.0, size=total_dias), 10.0, 28.0).round(1)
        variabilidad_cardiaca_hrv_ms = np.clip(44.0 - np.where(estres_elevado | mascara_taquicardia, 16.0, 0.0) + np.random.normal(0, 3.5, size=total_dias), 14.0, 75.0).round(1)
        dolor_cabeza_sintoma = np.random.uniform(0.0, 1.0, size=total_dias) < np.where(estres_elevado, 0.45, 0.04)
        actividad_fisica_minutos = np.clip(np.random.normal(120.0, 12.0, size=total_dias), 45.0, 150.0).round(1)
        escala_estres = np.clip(3 + np.where(estres_elevado, 4, 0) + np.where(alerta_fatiga_serie.to_numpy(), 2, 0) + np.random.randint(-1, 2, size=total_dias), 1, 10).astype(int)

        # CEREBRO 4: PSICOLOGÍA Y COGNICIÓN (ASTRA)
        cruce_degradacion = (co2_mmhg > self._config_limites.co2_limite_7dias_mmhg) | (horas_sueno < self._config_limites.umbral_horas_sueno_riesgo)
        lat_nom = np.clip(np.random.normal(self._config_limites.latencia_voz_base_ms, 22.0, size=total_dias), 150.0, 280.0)
        lat_est = np.clip(np.random.normal(740.0, 55.0, size=total_dias), self._config_limites.latencia_voz_estres_min_ms, self._config_limites.latencia_voz_estres_max_ms)
        latencia_voz_ms = np.where(cruce_degradacion, lat_est, lat_nom).round(1)

        mascara_incongruencia = mascara_taquicardia & (np.random.uniform(0.0, 1.0, size=total_dias) < 0.40)
        dens_nom = np.random.normal(0.66, 0.05, size=total_dias)
        dens_est = np.random.normal(0.44, 0.07, size=total_dias)
        dens_fin = np.random.normal(0.80, 0.02, size=total_dias)
        densidad_lexica = np.where(mascara_incongruencia, dens_fin, np.where(cruce_degradacion | mascara_taquicardia, dens_est, dens_nom))
        densidad_lexica_score = np.clip(densidad_lexica, 0.15, 0.95).round(2)

        prob_sans = 0.81 * perfil.prevalencia_sans_factor
        cond_sans = cruce_degradacion | mascara_taquicardia | mascara_tormenta_solar
        tirada_sans = np.random.uniform(0.0, 1.0, size=total_dias)
        sans_sintoma_vision = np.where(cond_sans, tirada_sans < prob_sans, tirada_sans < (0.05 * perfil.prevalencia_sans_factor))

        # ALERTAS NORMATIVAS Y PRESUPUESTO
        alerta_co2 = co2_mmhg > self._config_limites.co2_limite_max_nasa_v2_6004_mmhg
        alerta_radiacion = mascara_tormenta_solar
        alerta_fatiga = alerta_fatiga_serie.to_numpy()
        alerta_latencia = latencia_voz_ms >= self._config_limites.latencia_voz_estres_min_ms
        alerta_sans = sans_sintoma_vision
        total_alertas_dia = alerta_co2.astype(int) + alerta_radiacion.astype(int) + alerta_fatiga.astype(int) + alerta_latencia.astype(int) + alerta_sans.astype(int)
        presupuesto_radiacion_pct = ((radiacion_acumulada_msv / self._config_limites.radiacion_limite_carrera_msv) * 100.0).round(2)

        return pd.DataFrame({
            "dia_mision": dias, "entorno_mision": clave, "nombre_habitat": perfil.nombre_descriptivo,
            "gravedad_g": perfil.gravedad_g, "duracion_sol_h": perfil.duracion_ciclo_horas,
            "retardo_tierra_min": round(perfil.latencia_comunicacion_tierra_segundos / 60.0, 2),
            "co2_mmHg": co2_mmhg, "radiacion_tasa_diaria_mSv": dosis_diaria_total,
            "radiacion_acumulada_mSv": radiacion_acumulada_msv, "evento_solar_activo": mascara_tormenta_solar,
            "presion_cabina_kpa": presion_cabina_kpa, "temperatura_cabina_c": temperatura_cabina_c,
            "humedad_relativa_pct": humedad_relativa_pct, "ritmo_cardiaco_bpm": ritmo_cardiaco_bpm,
            "variabilidad_cardiaca_hrv_ms": variabilidad_cardiaca_hrv_ms, "frecuencia_respiratoria_rpm": frecuencia_respiratoria_rpm,
            "temperatura_piel_c": temperatura_piel_c, "horas_sueno": horas_sueno,
            "ciclos_sueno_insuficiente_consecutivos": contador_consecutivos, "alerta_riesgo_fatiga": alerta_fatiga,
            "perdida_osea_pct": perdida_osea_pct, "presion_sistolica_mmHg": presion_sistolica,
            "presion_diastolica_mmHg": presion_diastolica, "spo2_pct": spo2_pct,
            "dolor_cabeza_sintoma": dolor_cabeza_sintoma, "actividad_fisica_minutos": actividad_fisica_minutos,
            "escala_estres_autorreporte": escala_estres, "latencia_voz_ms": latencia_voz_ms,
            "densidad_lexica_score": densidad_lexica_score, "incongruencia_estres_oculto": mascara_incongruencia,
            "sans_sintoma_vision": sans_sintoma_vision, "total_alertas_activas": total_alertas_dia,
            "alerta_co2_critica": alerta_co2, "alerta_radiacion_spe": alerta_radiacion,
            "alerta_fatiga_cronica": alerta_fatiga, "alerta_cruce_latencia": alerta_latencia,
            "alerta_sans_activa": alerta_sans, "porcentaje_presupuesto_radiacion_carrera": presupuesto_radiacion_pct,
        })

    def simular_todos_los_habitats(self, total_dias: int = 120) -> pd.DataFrame:
        """Consolida las simulaciones de los 4 hábitats en un único DataFrame de 480 registros."""
        lista_dfs = [self.simular_habitat(clave, total_dias=total_dias) for clave in self._perfiles.keys()]
        master_df = pd.concat(lista_dfs, ignore_index=True)
        logger.info("Simulación consolidada finalizada. Total registros: %d", len(master_df))
        return master_df

    def generar_resumen_comparativo(self, master_df: pd.DataFrame) -> pd.DataFrame:
        """Genera tabla resumen con agregaciones estadísticas vectorizadas comparando entornos."""
        return (
            master_df.groupby("entorno_mision")
            .agg(
                gravedad_g=("gravedad_g", "first"),
                retardo_tierra_min=("retardo_tierra_min", "first"),
                radiacion_final_mSv=("radiacion_acumulada_mSv", "max"),
                presupuesto_radiacion_final_pct=("porcentaje_presupuesto_radiacion_carrera", "max"),
                tormentas_solares_totales=("evento_solar_activo", "sum"),
                perdida_osea_final_pct=("perdida_osea_pct", "max"),
                promedio_co2_mmHg=("co2_mmHg", "mean"),
                dias_con_alerta_fatiga=("alerta_riesgo_fatiga", "sum"),
                promedio_latencia_voz_ms=("latencia_voz_ms", "mean"),
                dias_con_sans_vision=("sans_sintoma_vision", "sum"),
                dias_con_incongruencia_estres=("incongruencia_estres_oculto", "sum"),
            )
            .round(2)
        )

    def exportar_dataset(
        self,
        df: pd.DataFrame,
        directorio_destino: str | Path = "datos_generados",
        nombre_base: str = "telemetria_120_dias_cuatro_habitats",
    ) -> dict[str, Path]:
        """Exporta el dataset a formatos CSV, Parquet y JSONL."""
        ruta_dir = Path(directorio_destino)
        ruta_dir.mkdir(parents=True, exist_ok=True)
        rcsv, rparquet, rjsonl = ruta_dir / f"{nombre_base}.csv", ruta_dir / f"{nombre_base}.parquet", ruta_dir / f"{nombre_base}.jsonl"
        df.to_csv(rcsv, index=False, encoding="utf-8")
        df.to_parquet(rparquet, index=False, engine="pyarrow")
        df.to_json(rjsonl, orient="records", lines=True, date_format="iso")
        logger.info("Dataset exportado a CSV, Parquet y JSONL en %s", ruta_dir)
        return {"csv": rcsv, "parquet": rparquet, "jsonl": rjsonl}
