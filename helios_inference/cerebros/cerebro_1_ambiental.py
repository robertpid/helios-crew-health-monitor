"""
Cerebro 1: Motor Ambiental de H.E.L.I.O.S. (Reglas Heurísticas Ambientales).

Evalúa las variables críticas del soporte vital según los límites de la NASA:
- CO2 en cabina: umbral normativo > 3.0 mmHg (NASA-STD-3001 Vol. 2, Req. 6004).
- Radiación acumulada: límite de carrera acumulada > 600 mSv o presencia de tormenta solar (SPE).
- Presión de cabina: rango normativo 95.0 - 103.0 kPa (NASA-STD-3001 Vol. 2, Req. 6006).

Genera un vector de estado ambiental en R^3 con codificación binaria/one-hot.
"""

import logging
from typing import Any
import numpy as np

from helios_inference.domain.inference_models import EstadoAmbientalInferencia

logger = logging.getLogger(__name__)


class CerebroAmbiental:
    """
    Motor analítico para evaluación de condiciones ambientales del hábitat o nave.
    Implementa el principio de Responsabilidad Única (SRP).
    """

    def __init__(
        self,
        umbral_co2_mmhg: float = 3.0,
        umbral_radiacion_msv: float = 600.0,
        presion_minima_kpa: float = 95.0,
        presion_maxima_kpa: float = 103.0,
    ) -> None:
        """
        Inicializa el motor ambiental con los umbrales normativos de referencia aeroespacial.

        Args:
            umbral_co2_mmhg: Límite superior para la presión parcial de CO2 en cabina.
            umbral_radiacion_msv: Límite de dosis acumulada efectiva para la carrera de un astronauta.
            presion_minima_kpa: Límite inferior seguro de presión atmosférica en cabina.
            presion_maxima_kpa: Límite superior seguro de presión atmosférica en cabina.
        """
        self._umbral_co2_mmhg = umbral_co2_mmhg
        self._umbral_radiacion_msv = umbral_radiacion_msv
        self._presion_minima_kpa = presion_minima_kpa
        self._presion_maxima_kpa = presion_maxima_kpa

    def procesar(self, datos_entorno: dict[str, Any]) -> tuple[np.ndarray, EstadoAmbientalInferencia]:
        """
        Analiza las métricas ambientales de cabina y produce el vector de estado en R^3.

        Args:
            datos_entorno: Diccionario con llaves 'co2_mmHg', 'radiacion_acumulada_mSv',
                           'presion_cabina_kpa', y opcionalmente 'evento_solar_activo'.

        Returns:
            Tupla conteniendo:
            - np.ndarray: Vector de estado ambiental con shape (3,), ej. np.array([1.0, 0.0, 0.0]).
            - EstadoAmbientalInferencia: Modelo inmutable con las alertas y detalles estructurados.
        """
        co2 = float(datos_entorno.get("co2_mmHg", 1.5))
        radiacion = float(datos_entorno.get("radiacion_acumulada_mSv", 50.0))
        presion = float(datos_entorno.get("presion_cabina_kpa", 101.3))
        evento_solar = bool(datos_entorno.get("evento_solar_activo", False))

        # Evaluación heurística basada en estándares de la NASA
        alerta_co2 = 1.0 if co2 > self._umbral_co2_mmhg else 0.0
        alerta_radiacion = 1.0 if (radiacion > self._umbral_radiacion_msv or evento_solar) else 0.0
        alerta_presion = 1.0 if (presion < self._presion_minima_kpa or presion > self._presion_maxima_kpa) else 0.0

        vector_ambiental = np.array([alerta_co2, alerta_radiacion, alerta_presion], dtype=np.float64)

        etiquetas: list[str] = []
        if alerta_co2 > 0.0:
            etiquetas.append(f"ALERTA_CO2_ELEVADO: {co2:.2f} mmHg (Límite: {self._umbral_co2_mmhg} mmHg)")
        if alerta_radiacion > 0.0:
            causa = "Tormenta Solar Activa (SPE)" if evento_solar else f"Dosis carrera {radiacion:.1f} mSv"
            etiquetas.append(f"ALERTA_RADIACION_CRITICA: {causa}")
        if alerta_presion > 0.0:
            etiquetas.append(f"ALERTA_PRESION_CABINA_ANOMALA: {presion:.2f} kPa")

        if etiquetas:
            logger.warning("Cerebro 1 detectó anomalías ambientales: %s", ", ".join(etiquetas))
        else:
            logger.debug("Cerebro 1: Parámetros de cabina en estado nominal.")

        estado = EstadoAmbientalInferencia(
            vector_ambiental=vector_ambiental.tolist(),
            etiquetas_activadas=etiquetas,
            co2_excedido=(alerta_co2 > 0.0),
            radiacion_critica=(alerta_radiacion > 0.0),
            presion_anomala=(alerta_presion > 0.0),
        )

        return vector_ambiental, estado
