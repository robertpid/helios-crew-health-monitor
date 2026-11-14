"""
Cerebro 2: Motor Biométrico de H.E.L.I.O.S. (Desviación de Línea Base Fisiológica).

Monitorea biomarcadores vitales contra la línea base personalizada del astronauta:
- Frecuencia cardíaca (bpm): umbral de taquicardia o esfuerzo agudo (> 95.0 bpm) o bradicardia (< 50.0 bpm).
- Horas de sueño: déficit de descanso (< 6.0 h) o fatiga acumulada multi-ciclo.
- Desmineralización ósea: detección de riesgo de fatiga ósea por duración de misión (> 30 días)
  o pérdida acumulada significativa (> 1.5%).
- Síndrome Neuro-ocular Asociado al Vuelo Espacial (SANS): edema de disco óptico y visión borrosa.

Genera un vector de estado fisiológico en R^4: [pulso_anomalo, deficit_sueno, fatiga_osea, sintoma_sans].
"""

import logging
from typing import Any
import numpy as np

from helios_inference.domain.inference_models import EstadoBiometricoInferencia

logger = logging.getLogger(__name__)


class CerebroBiometrico:
    """
    Motor analítico para evaluación de la salud física y desviación de línea base.
    Implementa el principio de Responsabilidad Única (SRP).
    """

    def __init__(
        self,
        umbral_taquicardia_bpm: float = 95.0,
        umbral_bradicardia_bpm: float = 50.0,
        umbral_sueno_minimo_horas: float = 6.0,
        dia_mision_inicio_riesgo_oseo: int = 30,
        umbral_perdida_osea_pct: float = 1.5,
    ) -> None:
        """
        Configura los límites operacionales para la evaluación preliminar fisiológica.

        Args:
            umbral_taquicardia_bpm: Límite superior de frecuencia cardíaca en reposo/rutina.
            umbral_bradicardia_bpm: Límite inferior de frecuencia cardíaca.
            umbral_sueno_minimo_horas: Duración mínima aceptable de descanso reparador.
            dia_mision_inicio_riesgo_oseo: Día de misión a partir del cual el riesgo óseo se activa.
            umbral_perdida_osea_pct: Porcentaje acumulado de pérdida mineral ósea de preocupación.
        """
        self._umbral_taquicardia_bpm = umbral_taquicardia_bpm
        self._umbral_bradicardia_bpm = umbral_bradicardia_bpm
        self._umbral_sueno_minimo_horas = umbral_sueno_minimo_horas
        self._dia_mision_inicio_riesgo_oseo = dia_mision_inicio_riesgo_oseo
        self._umbral_perdida_osea_pct = umbral_perdida_osea_pct

    def procesar(
        self,
        datos_biometria: dict[str, Any],
        dia_mision: int,
        sintoma_sans: bool = False,
    ) -> tuple[np.ndarray, EstadoBiometricoInferencia]:
        """
        Evalúa el estado fisiológico y genera el vector biométrico en R^4.

        Args:
            datos_biometria: Diccionario con biomarcadores ('ritmo_cardiaco_bpm',
                             'horas_sueno_ultimo_ciclo', 'perdida_osea_pct', etc.).
            dia_mision: Día acumulado transcurrido de la misión espacial.
            sintoma_sans: Presencia de alteraciones visuales neuro-oculares reportadas.

        Returns:
            Tupla conteniendo:
            - np.ndarray: Vector de estado fisiológico con shape (4,).
            - EstadoBiometricoInferencia: Datos estructurados del estado biométrico.
        """
        pulso = float(datos_biometria.get("ritmo_cardiaco_bpm", 65.0))
        sueno = float(datos_biometria.get("horas_sueno_ultimo_ciclo", 7.0))
        perdida_osea = float(datos_biometria.get("perdida_osea_pct", 0.0))
        riesgo_fatiga = bool(datos_biometria.get("alerta_riesgo_fatiga", False))

        # 1. Alerta de pulso (taquicardia o bradicardia)
        alerta_pulso = 1.0 if (pulso > self._umbral_taquicardia_bpm or pulso < self._umbral_bradicardia_bpm) else 0.0

        # 2. Alerta de sueño / fatiga
        alerta_sueno = 1.0 if (sueno < self._umbral_sueno_minimo_horas or riesgo_fatiga) else 0.0

        # 3. Alerta de fatiga ósea (Día de misión > 30 o pérdida acumulada > umbral)
        alerta_osea = 1.0 if (dia_mision > self._dia_mision_inicio_riesgo_oseo or perdida_osea > self._umbral_perdida_osea_pct) else 0.0

        # 4. Alerta de sintomatología SANS
        alerta_sans = 1.0 if sintoma_sans else 0.0

        vector_biometrico = np.array([alerta_pulso, alerta_sueno, alerta_osea, alerta_sans], dtype=np.float64)

        etiquetas: list[str] = []
        if alerta_pulso > 0.0:
            etiquetas.append(f"ALERTA_PULSO_ANOMALO: {pulso:.1f} bpm")
        if alerta_sueno > 0.0:
            etiquetas.append(f"ALERTA_DEFICIT_SUENO: {sueno:.1f} horas")
        if alerta_osea > 0.0:
            etiquetas.append(f"ALERTA_RIESGO_OSEO: Día {dia_mision} ({perdida_osea:.2f}% de pérdida)")
        if alerta_sans > 0.0:
            etiquetas.append("ALERTA_SANS_ACTIVA: Alteración neuro-ocular")

        metricas_normales = bool(np.sum(vector_biometrico) == 0.0)
        cuerpo_panico = bool(pulso > self._umbral_taquicardia_bpm)

        if etiquetas:
            logger.warning("Cerebro 2 detectó desviaciones fisiológicas: %s", ", ".join(etiquetas))
        else:
            logger.debug("Cerebro 2: Signos fisiológicos dentro de los parámetros de línea base.")

        estado = EstadoBiometricoInferencia(
            vector_biometrico=vector_biometrico.tolist(),
            etiquetas_activadas=etiquetas,
            metricas_fisicas_normales=metricas_normales,
            cuerpo_en_panico=cuerpo_panico,
        )

        return vector_biometrico, estado
