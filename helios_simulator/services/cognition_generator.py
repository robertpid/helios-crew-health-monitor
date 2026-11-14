"""
Generador de telemetría psicológica y cognitiva (Cerebro 4 - ASTRA).

Modela la interacción y cruce entre estresores ambientales, sobrecarga biológica
y manifestaciones conductuales (latencia verbal, ocultamiento de estrés y SANS).
"""

import logging
from helios_simulator.config import LimitesNasaConfig
from helios_simulator.domain.models import CognicionModel
from helios_simulator.services.math_noise import (
    evaluar_probabilidad_evento,
    generar_ruido_gaussiano,
    redondear_telemetria,
)

logger = logging.getLogger(__name__)


class GeneradorCognicion:
    """
    Servicio de evaluación de parámetros cognitivos del subsistema ASTRA.
    Aplica cruces lógicos multivariados para detectar fatiga y tensión psicológica.
    """

    def __init__(self, config_limites: LimitesNasaConfig | None = None) -> None:
        """
        Inicializa el generador cognitivo.

        Args:
            config_limites: Parámetros y umbrales de referencia.
        """
        self._config = config_limites or LimitesNasaConfig()

    def generar_lectura(
        self,
        co2_mmhg: float,
        horas_sueno: float,
        ritmo_cardiaco_bpm: float,
        evento_solar_activo: bool = False,
        forzar_incongruencia: bool = False,
    ) -> CognicionModel:
        """
        Calcula las métricas de respuesta psicológica y verbal cruzando con el entorno y biometría.

        Reglas de Negocio:
            1. Latencia de Voz: Base 200ms. CRUCE LÓGICO: Si co2_mmHg > 2.5 o horas_sueno < 6.0,
               disparar a 600-900ms (refleja letargo y enlentecimiento psicomotor por hipercapnia o insomnio).
            2. Densidad Léxica: 0.0 a 1.0. INCONGRUENCIA: En ocasiones simula estrés oculto
               (ritmo_cardiaco > 95 pero densidad_lexica en 0.8 "fingiendo estar bien").
            3. SANS Síntoma Visión: Booleano, cambia a True bajo estrés alto o elevación de CO2,
               reflejando el 81% de prevalencia en astronautas de NASA según el programa LSAH.

        Args:
            co2_mmhg: Concentración actual de CO2 en cabina.
            horas_sueno: Horas dormidas en el último ciclo.
            ritmo_cardiaco_bpm: Frecuencia cardiaca instantánea.
            evento_solar_activo: Bandera de emergencia radiológica.
            forzar_incongruencia: Bandera para activar prueba de estrés encubierto.

        Returns:
            Instancia validada de CognicionModel.
        """
        # 1. CRUCE LÓGICO: Latencia de voz
        cruce_degradacion = (
            co2_mmhg > self._config.co2_limite_7dias_mmhg
            or horas_sueno < self._config.umbral_horas_sueno_riesgo
        )

        if cruce_degradacion:
            # Latencia disparada entre 600 y 900 ms
            latencia_val = generar_ruido_gaussiano(
                valor_medio=750.0,
                desviacion_estandar=60.0,
                limite_inferior=self._config.latencia_voz_estres_min_ms,
                limite_superior=self._config.latencia_voz_estres_max_ms,
            )
            logger.info(
                "Cruce multivariado activado: latencia verbal retardada a %.1f ms (CO2: %.2f mmHg, Sueño: %.1f h)",
                latencia_val,
                co2_mmhg,
                horas_sueno,
            )
        else:
            # Latencia nominal base ~200 ms
            latencia_val = generar_ruido_gaussiano(
                valor_medio=self._config.latencia_voz_base_ms,
                desviacion_estandar=25.0,
                limite_inferior=140.0,
                limite_superior=280.0,
            )

        # 2. INCONGRUENCIA: Estrés oculto vs Densidad léxica
        es_ritmo_estres = ritmo_cardiaco_bpm > self._config.ritmo_cardiaco_umbral_estres_alto_bpm
        disparar_incongruencia = forzar_incongruencia or (
            es_ritmo_estres and evaluar_probabilidad_evento(self._config.probabilidad_incongruencia_estres)
        )

        if disparar_incongruencia:
            # Fingiendo compostura: densidad léxica artificialmente alta (0.80) a pesar de taquicardia
            densidad_val = generar_ruido_gaussiano(0.80, 0.02, 0.75, 0.85)
            incongruencia_activa = True
            logger.warning(
                "Incongruencia cognitiva detectada: Ritmo cardiaco elevado (%.1f bpm) con densidad léxica fingida (%.2f)",
                ritmo_cardiaco_bpm,
                densidad_val,
            )
        else:
            incongruencia_activa = False
            if es_ritmo_estres or cruce_degradacion:
                # Bajo estrés evidente, la riqueza léxica suele contraerse (0.35 - 0.55)
                densidad_val = generar_ruido_gaussiano(0.45, 0.08, 0.20, 0.60)
            else:
                # Estado normal balanceado (0.60 - 0.72)
                densidad_val = generar_ruido_gaussiano(0.65, 0.05, 0.40, 0.85)

        # 3. SANS Síntoma de Visión (Spaceflight-Associated Neuro-ocular Syndrome)
        # 81% de astronautas según programa LSAH bajo condiciones de estrés/hipercapnia/desplazamiento de fluidos
        condicion_estres_alto = (
            co2_mmhg >= self._config.co2_umbral_sintomas_mmhg
            or evento_solar_activo
            or ritmo_cardiaco_bpm >= self._config.ritmo_cardiaco_umbral_estres_alto_bpm
            or latencia_val >= 600.0
        )

        if condicion_estres_alto:
            # 81% de probabilidad empírica de manifestación sintomática según LSAH
            sans_activo = evaluar_probabilidad_evento(
                self._config.prevalencia_sans_historica_lsah_pct / 100.0
            )
        else:
            # En condiciones basales estables, probabilidad muy baja
            sans_activo = evaluar_probabilidad_evento(0.08)

        return CognicionModel(
            latencia_voz_ms=redondear_telemetria(latencia_val, 1),
            densidad_lexica_score=redondear_telemetria(densidad_val, 2),
            incongruencia_estres_oculto=incongruencia_activa,
            sans_sintoma_vision=sans_activo,
        )
