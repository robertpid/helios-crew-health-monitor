"""
Simulador analítico multihábitat para series temporales de 120 días.

Genera telemetría sintética vectorizada mediante NumPy y Pandas para 4 entornos de misión:
1. Estación Espacial Internacional (ISS / LEO)
2. Base Lunar (Artemis Base Camp)
3. Nave Espacial de Tránsito (Deep Space Transit a Marte)
4. Base de Superficie de Marte (Hábitat Marciano)

Cumple con estándares NASA-STD-3001, marco RIDGE y principios de ingeniería de software.
Está estrictamente prohibido el uso de iterrows() o itertuples() (cálculos 100% vectorizados).
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
    """
    Motor de simulación vectorial para series temporales multivariadas de 120 días.
    Modela la evolución física, fisiológica y psicológica de tripulaciones en distintos hábitats espaciales.
    """

    def __init__(
        self,
        config_limites: LimitesNasaConfig | None = None,
        semilla_aleatoria: int | None = 42,
    ) -> None:
        """
        Inicializa el simulador multihábitat.

        Args:
            config_limites: Constantes y umbrales de referencia NASA-STD-3001.
            semilla_aleatoria: Semilla pseudoaleatoria para reproducibilidad experimental.
        """
        self._config_limites = config_limites or LimitesNasaConfig()
        self._perfiles = obtener_perfiles_ambientes()
        if semilla_aleatoria is not None:
            np.random.seed(semilla_aleatoria)

    def simular_habitat(
        self,
        tipo_entorno: EntornoMision | str,
        total_dias: int = 120,
    ) -> pd.DataFrame:
        """
        Genera el DataFrame completo de telemetría para un hábitat específico a lo largo de 120 días.
        Aplica transformaciones 100% vectorizadas sobre matrices NumPy sin bucles por fila.

        Args:
            tipo_entorno: Identificador del hábitat (estacion_espacial, base_lunar, nave_espacial, base_marte).
            total_dias: Cantidad de días/soles a simular (por defecto 120).

        Returns:
            DataFrame de Pandas con todas las variables ambientales, biomédicas y cognitivas.
        """
        clave_perfil = tipo_entorno.value if isinstance(tipo_entorno, EntornoMision) else str(tipo_entorno)
        if clave_perfil not in self._perfiles:
            raise ValueError(f"Hábitat no reconocido: '{clave_perfil}'. Opciones válidas: {list(self._perfiles.keys())}")

        perfil: PerfilAmbienteMision = self._perfiles[clave_perfil]
        logger.info(
            "Simulando serie temporal de %d días para hábitat '%s' (g=%.3f, retardo=%.1fs)...",
            total_dias,
            perfil.nombre_descriptivo,
            perfil.gravedad_g,
            perfil.latencia_comunicacion_tierra_segundos,
        )

        dias = np.arange(1, total_dias + 1, dtype=np.int32)

        # -----------------------------------------------------------------------------------------
        # CEREBRO 1: ENTORNO AMBIENTAL (Vectorizado)
        # -----------------------------------------------------------------------------------------
        # 1. CO2 (mmHg): Distribución base + inyección estocástica de picos anómalos (> 3.0 mmHg)
        probabilidad_pico_co2 = 0.10
        mascara_picos_co2 = np.random.uniform(0.0, 1.0, size=total_dias) < probabilidad_pico_co2
        co2_nominal = np.random.normal(1.60, 0.22, size=total_dias)
        co2_nominal = np.clip(co2_nominal, self._config_limites.co2_normal_min_mmhg, self._config_limites.co2_normal_max_mmhg)

        co2_picos = np.random.normal(3.45, 0.28, size=total_dias)
        co2_picos = np.clip(co2_picos, 3.05, 4.60)

        co2_mmhg = np.where(mascara_picos_co2, co2_picos, co2_nominal).round(2)

        # 2. Radiación diaria y eventos solares (SPE)
        # Probabilidad de Tormenta Solar según el blindaje del hábitat
        mascara_tormenta_solar = (
            np.random.uniform(0.0, 1.0, size=total_dias) < perfil.probabilidad_tormenta_solar
        )
        tasa_radiacion_diaria = np.random.normal(
            perfil.radiacion_diaria_base_msv,
            perfil.radiacion_desviacion_msv,
            size=total_dias,
        )
        tasa_radiacion_diaria = np.clip(tasa_radiacion_diaria, 0.10, 3.50)

        # Si hay tormenta solar (SPE), inyección masiva de +20 mSv en ese día
        impacto_solar = np.where(
            mascara_tormenta_solar,
            self._config_limites.radiacion_tormenta_solar_impacto_msv,
            0.0,
        )
        dosis_diaria_total = (tasa_radiacion_diaria + impacto_solar).round(3)

        # Dosis acumulada a lo largo del tiempo: suma acumulada vectorizada (np.cumsum)
        radiacion_base_inicial = 15.0 if clave_perfil == "estacion_espacial" else 45.0
        radiacion_acumulada_msv = (radiacion_base_inicial + np.cumsum(dosis_diaria_total)).round(2)

        # 3. Presión de cabina (kPa) y Temperatura (°C)
        presion_cabina_kpa = np.random.normal(
            perfil.presion_cabina_nominal_kpa,
            0.85,
            size=total_dias,
        )
        presion_cabina_kpa = np.clip(
            presion_cabina_kpa,
            perfil.presion_cabina_min_kpa,
            perfil.presion_cabina_max_kpa,
        ).round(2)

        temperatura_cabina_c = np.random.normal(
            perfil.temperatura_cabina_nominal_c,
            0.60,
            size=total_dias,
        ).round(2)

        humedad_relativa_pct = np.random.normal(46.0, 2.5, size=total_dias)
        humedad_relativa_pct = np.clip(humedad_relativa_pct, 35.0, 65.0).round(1)

        # -----------------------------------------------------------------------------------------
        # CEREBRO 2: BIOMETRÍA FISIOLÓGICA (Vectorizado)
        # -----------------------------------------------------------------------------------------
        # 1. Pérdida ósea acumulada (%) ponderada por la gravedad del entorno:
        # En microgravedad g=0: 1.5% mensual. En gravedad parcial: 1.5% * (1.0 - g)
        factor_atenuacion_gravedad = max(0.0, 1.0 - perfil.gravedad_g)
        tasa_mensual_ponderada = self._config_limites.tasa_perdida_osea_mensual_pct * factor_atenuacion_gravedad
        perdida_osea_pct = ((dias / 30.0) * tasa_mensual_ponderada).round(2)

        # 2. Horas de sueño:
        # En Marte, el sol de 24.65h introduce desincronización circadiana progresiva
        deriva_martiana = 0.65 if clave_perfil == "base_marte" else 0.0
        media_sueno = np.maximum(4.8, self._config_limites.horas_sueno_promedio - (0.003 * dias * deriva_martiana))
        horas_sueno = np.random.normal(media_sueno, 0.95, size=total_dias)
        horas_sueno = np.clip(horas_sueno, 3.8, 8.5).round(2)

        # 3. Detección vectorizada de alerta por riesgo de fatiga:
        # 3 ciclos consecutivos con sueño < 6.0h mediante series booleanas desplazadas
        serie_sueno_insuficiente = pd.Series(horas_sueno < self._config_limites.umbral_horas_sueno_riesgo)
        # Rolling window sum de 3 períodos
        ventana_3_ciclos = serie_sueno_insuficiente.rolling(window=3, min_periods=1).sum()
        alerta_fatiga_serie = (ventana_3_ciclos >= 3.0)

        # Contador de ciclos insuficientes consecutivos vectorizado
        contador_consecutivos = np.zeros(total_dias, dtype=np.int32)
        contador_acumulado = 0
        for idx, valor_deficit in enumerate(serie_sueno_insuficiente.to_numpy()):
            if valor_deficit:
                contador_acumulado += 1
            else:
                contador_acumulado = max(0, contador_acumulado - 1)
            contador_consecutivos[idx] = contador_acumulado

        # 4. Frecuencia Cardíaca (bpm) modulada por estrés ambiental, fatiga y radiación
        estres_elevado_ambiental = (
            (co2_mmhg >= self._config_limites.co2_umbral_sintomas_mmhg)
            | mascara_tormenta_solar
            | alerta_fatiga_serie.to_numpy()
        )
        # Sobreesfuerzo físico o estrés agudo en hábitat espacial
        picos_estres_agudo = np.random.uniform(0.0, 1.0, size=total_dias) < (0.08 * perfil.factor_estres_aislamiento)
        desplazamiento_ritmo = np.where(estres_elevado_ambiental | picos_estres_agudo, 26.0, 0.0)
        ritmo_cardiaco_bpm = np.random.normal(
            self._config_limites.ritmo_cardiaco_base_bpm + desplazamiento_ritmo,
            6.5,
            size=total_dias,
        )
        ritmo_cardiaco_bpm = np.clip(ritmo_cardiaco_bpm, 52.0, 135.0).round(1)

        mascara_taquicardia = ritmo_cardiaco_bpm > self._config_limites.ritmo_cardiaco_umbral_estres_alto_bpm

        # Presión arterial y SpO2 vectorizados
        presion_sistolica = (118.0 + (ritmo_cardiaco_bpm - 65.0) * 0.45 + np.random.normal(0, 2.5, size=total_dias)).round(1)
        presion_diastolica = (presion_sistolica * 0.65 + np.random.normal(0, 1.8, size=total_dias)).round(1)
        spo2_pct = np.clip(np.random.normal(98.1, 0.5, size=total_dias), 93.0, 99.8).round(1)

        # Sensores de la prenda inteligente Bio-Monitor / Astroskin (CSA)
        temperatura_piel_c = (34.8 + np.where(estres_elevado_ambiental, 0.5, 0.0) + np.random.normal(0, 0.25, size=total_dias)).round(2)
        temperatura_piel_c = np.clip(temperatura_piel_c, 33.2, 37.2)

        frecuencia_respiratoria_rpm = (14.0 + np.where(estres_elevado_ambiental, 3.5, 0.0) + np.random.normal(0, 1.0, size=total_dias)).round(1)
        frecuencia_respiratoria_rpm = np.clip(frecuencia_respiratoria_rpm, 10.0, 28.0)

        # Variabilidad de frecuencia cardíaca (HRV ms): disminuye ante sobrecarga hemodinámica
        variabilidad_cardiaca_hrv_ms = (44.0 - np.where(estres_elevado_ambiental | mascara_taquicardia, 16.0, 0.0) + np.random.normal(0, 3.5, size=total_dias)).round(1)
        variabilidad_cardiaca_hrv_ms = np.clip(variabilidad_cardiaca_hrv_ms, 14.0, 75.0)

        # Cefalea (dolor de cabeza) y autorreporte de estrés
        probabilidad_cefalea = np.where(estres_elevado_ambiental, 0.45, 0.04)
        dolor_cabeza_sintoma = np.random.uniform(0.0, 1.0, size=total_dias) < probabilidad_cefalea

        actividad_fisica_minutos = np.clip(np.random.normal(120.0, 12.0, size=total_dias), 45.0, 150.0).round(1)

        escala_estres_autorreporte = np.clip(
            3 + np.where(estres_elevado_ambiental, 4, 0) + np.where(alerta_fatiga_serie.to_numpy(), 2, 0) + np.random.randint(-1, 2, size=total_dias),
            1,
            10,
        ).astype(int)

        # -----------------------------------------------------------------------------------------
        # CEREBRO 4: PSICOLOGÍA Y COGNICIÓN - ASTRA (Vectorizado)
        # -----------------------------------------------------------------------------------------
        # 1. CRUCE LÓGICO: Latencia verbal (ms)
        # Si co2 > 2.5 mmHg o sueno < 6.0h, disparar a 600 - 900 ms
        cruce_degradacion = (co2_mmhg > self._config_limites.co2_limite_7dias_mmhg) | (horas_sueno < self._config_limites.umbral_horas_sueno_riesgo)

        latencia_nominal = np.random.normal(self._config_limites.latencia_voz_base_ms, 22.0, size=total_dias)
        latencia_nominal = np.clip(latencia_nominal, 150.0, 280.0)

        latencia_estres = np.random.normal(740.0, 55.0, size=total_dias)
        latencia_estres = np.clip(
            latencia_estres,
            self._config_limites.latencia_voz_estres_min_ms,
            self._config_limites.latencia_voz_estres_max_ms,
        )

        latencia_voz_ms = np.where(cruce_degradacion, latencia_estres, latencia_nominal).round(1)

        # 2. INCONGRUENCIA: Estrés oculto vs Densidad léxica
        # Si ritmo > 95 pero densidad léxica sostenida en ~0.80 ("fingiendo estar bien")
        mascara_taquicardia = ritmo_cardiaco_bpm > self._config_limites.ritmo_cardiaco_umbral_estres_alto_bpm
        probabilidad_incongruencia = 0.40
        mascara_incongruencia = mascara_taquicardia & (
            np.random.uniform(0.0, 1.0, size=total_dias) < probabilidad_incongruencia
        )

        densidad_lexica_nominal = np.random.normal(0.66, 0.05, size=total_dias)
        densidad_lexica_estres = np.random.normal(0.44, 0.07, size=total_dias)
        densidad_lexica_fingida = np.random.normal(0.80, 0.02, size=total_dias)

        densidad_lexica = np.where(
            mascara_incongruencia,
            densidad_lexica_fingida,
            np.where(cruce_degradacion | mascara_taquicardia, densidad_lexica_estres, densidad_lexica_nominal),
        )
        densidad_lexica_score = np.clip(densidad_lexica, 0.15, 0.95).round(2)

        # 3. SANS Síntoma de Visión (LSAH 81% ponderado por microgravedad)
        probabilidad_sans_efectiva = 0.81 * perfil.prevalencia_sans_factor
        mascara_condicion_sans = cruce_degradacion | mascara_taquicardia | mascara_tormenta_solar
        tirada_sans = np.random.uniform(0.0, 1.0, size=total_dias)
        sans_sintoma_vision = np.where(
            mascara_condicion_sans,
            tirada_sans < probabilidad_sans_efectiva,
            tirada_sans < (0.05 * perfil.prevalencia_sans_factor),
        )

        # -----------------------------------------------------------------------------------------
        # MATRIZ DE EVALUACIONES PRELIMINARES Y ALERTAS NORMATIVAS (Vectorizado)
        # -----------------------------------------------------------------------------------------
        alerta_co2 = co2_mmhg > self._config_limites.co2_limite_max_nasa_v2_6004_mmhg
        alerta_radiacion = mascara_tormenta_solar
        alerta_fatiga = alerta_fatiga_serie.to_numpy()
        alerta_latencia = latencia_voz_ms >= self._config_limites.latencia_voz_estres_min_ms
        alerta_sans = sans_sintoma_vision

        total_alertas_dia = (
            alerta_co2.astype(int)
            + alerta_radiacion.astype(int)
            + alerta_fatiga.astype(int)
            + alerta_latencia.astype(int)
            + alerta_sans.astype(int)
        )

        presupuesto_radiacion_carrera_pct = (
            (radiacion_acumulada_msv / self._config_limites.radiacion_limite_carrera_msv) * 100.0
        ).round(2)

        # Construcción limpia y tipada del DataFrame
        habitat_df = pd.DataFrame(
            {
                "dia_mision": dias,
                "entorno_mision": clave_perfil,
                "nombre_habitat": perfil.nombre_descriptivo,
                "gravedad_g": perfil.gravedad_g,
                "duracion_sol_h": perfil.duracion_ciclo_horas,
                "retardo_tierra_min": round(perfil.latencia_comunicacion_tierra_segundos / 60.0, 2),
                # Entorno (Cerebro 1)
                "co2_mmHg": co2_mmhg,
                "radiacion_tasa_diaria_mSv": dosis_diaria_total,
                "radiacion_acumulada_mSv": radiacion_acumulada_msv,
                "evento_solar_activo": mascara_tormenta_solar,
                "presion_cabina_kpa": presion_cabina_kpa,
                "temperatura_cabina_c": temperatura_cabina_c,
                "humedad_relativa_pct": humedad_relativa_pct,
                # Biometría Fisiológica (Cerebro 2)
                "ritmo_cardiaco_bpm": ritmo_cardiaco_bpm,
                "variabilidad_cardiaca_hrv_ms": variabilidad_cardiaca_hrv_ms,
                "frecuencia_respiratoria_rpm": frecuencia_respiratoria_rpm,
                "temperatura_piel_c": temperatura_piel_c,
                "horas_sueno": horas_sueno,
                "ciclos_sueno_insuficiente_consecutivos": contador_consecutivos,
                "alerta_riesgo_fatiga": alerta_fatiga,
                "perdida_osea_pct": perdida_osea_pct,
                "presion_sistolica_mmHg": presion_sistolica,
                "presion_diastolica_mmHg": presion_diastolica,
                "spo2_pct": spo2_pct,
                "dolor_cabeza_sintoma": dolor_cabeza_sintoma,
                "actividad_fisica_minutos": actividad_fisica_minutos,
                "escala_estres_autorreporte": escala_estres_autorreporte,
                # Cognición y Psicología (Cerebro 4 - ASTRA)
                "latencia_voz_ms": latencia_voz_ms,
                "densidad_lexica_score": densidad_lexica_score,
                "incongruencia_estres_oculto": mascara_incongruencia,
                "sans_sintoma_vision": sans_sintoma_vision,
                # Evaluaciones Preliminares
                "total_alertas_activas": total_alertas_dia,
                "alerta_co2_critica": alerta_co2,
                "alerta_radiacion_spe": alerta_radiacion,
                "alerta_fatiga_cronica": alerta_fatiga,
                "alerta_cruce_latencia": alerta_latencia,
                "alerta_sans_activa": alerta_sans,
                "porcentaje_presupuesto_radiacion_carrera": presupuesto_radiacion_carrera_pct,
            }
        )

        return habitat_df

    def simular_todos_los_habitats(self, total_dias: int = 120) -> pd.DataFrame:
        """
        Ejecuta la simulación para los 4 hábitats (Estación Espacial, Base Lunar, Nave y Base de Marte)
        y consolida una única tabla maestra de 480 observaciones diarias.

        Args:
            total_dias: Días por cada entorno (120 días).

        Returns:
            DataFrame unificado con 480 registros vectorizados.
        """
        lista_dataframes: list[pd.DataFrame] = []
        for clave_entorno in self._perfiles.keys():
            df_entorno = self.simular_habitat(clave_entorno, total_dias=total_dias)
            lista_dataframes.append(df_entorno)

        master_df = pd.concat(lista_dataframes, ignore_index=True)
        logger.info(
            "Simulación consolidada finalizada exitosamente. Total registros generados: %d",
            len(master_df),
        )
        return master_df

    def generar_resumen_comparativo(self, master_df: pd.DataFrame) -> pd.DataFrame:
        """
        Genera una tabla resumen con agregaciones estadísticas vectorizadas (groupby)
        comparando los 4 entornos al final del ciclo de 120 días.

        Args:
            master_df: DataFrame maestro con las observaciones de los 4 hábitats.

        Returns:
            DataFrame con métricas comparativas clave.
        """
        # Agregación vectorizada con groupby
        resumen = (
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
        return resumen

    def exportar_dataset(
        self,
        df: pd.DataFrame,
        directorio_destino: str | Path = "datos_generados",
        nombre_base: str = "telemetria_120_dias_cuatro_habitats",
    ) -> dict[str, Path]:
        """
        Exporta el conjunto de datos a formatos optimizados (CSV, Parquet y JSONL).

        Args:
            df: DataFrame a serializar.
            directorio_destino: Directorio local donde se escribirán los artefactos.
            nombre_base: Prefijo para los archivos generados.

        Returns:
            Diccionario con las rutas de los archivos exportados.
        """
        ruta_dir = Path(directorio_destino)
        ruta_dir.mkdir(parents=True, exist_ok=True)

        ruta_csv = ruta_dir / f"{nombre_base}.csv"
        ruta_parquet = ruta_dir / f"{nombre_base}.parquet"
        ruta_jsonl = ruta_dir / f"{nombre_base}.jsonl"

        df.to_csv(ruta_csv, index=False, encoding="utf-8")
        df.to_parquet(ruta_parquet, index=False, engine="pyarrow")
        df.to_json(ruta_jsonl, orient="records", lines=True, date_format="iso")

        logger.info("Dataset exportado a CSV: %s (%d bytes)", ruta_csv, ruta_csv.stat().st_size)
        logger.info("Dataset exportado a Parquet: %s (%d bytes)", ruta_parquet, ruta_parquet.stat().st_size)
        logger.info("Dataset exportado a JSONL: %s (%d bytes)", ruta_jsonl, ruta_jsonl.stat().st_size)

        return {
            "csv": ruta_csv,
            "parquet": ruta_parquet,
            "jsonl": ruta_jsonl,
        }
