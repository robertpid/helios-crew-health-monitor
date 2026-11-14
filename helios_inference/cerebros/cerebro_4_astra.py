"""
Cerebro 4: Inteligencia Vectorial Cognitiva (Subsistema ASTRA).

========================================================================================
DETECCIÓN DE INCONGRUENCIA COGNITIVA MEDIANTE SIMILITUD COSENO (ÁLGEBRA LINEAL CON NUMPY)
========================================================================================
En misiones de espacio profundo, los astronautas tienden involuntariamente o por cultura
operativa a minimizar síntomas de agotamiento ("fingiendo estar bien").

ASTRA (Automated Speech & Temporal Response Analysis) analiza las comunicaciones de cabina:
- latencia_voz_ms: tiempo de respuesta verbal (línea base nominal: ~200.0 ms).
- densidad_lexica_score: variedad y complejidad léxica (línea base nominal: ~1.0).

Se construye el vector cognitivo actual:
    C = [latencia_voz_ms, densidad_lexica_score]
y se compara contra la Línea Base Dinámica del tripulante:
    B = [200.0, 1.0]

Para preservar la sensibilidad de la métrica angular sin distorsión por escalas heterogéneas
(milisegundos vs rango unitario [0, 1]), normalizamos los componentes respecto a su línea base:
    C_norm = [ latencia_voz_ms / 200.0, densidad_lexica_score / 1.0 ]
    B_norm = [ 1.0, 1.0 ]

La similitud coseno se calcula mediante álgebra vectorial pura:
    similitud = np.dot(C_norm, B_norm) / (np.linalg.norm(C_norm) * np.linalg.norm(B_norm))

REGLA DE NEGOCIO (INCONGRUENCIA COGNITIVA):
1. Si la similitud cae abruptamente (por ejemplo latencia elevada a 600-900 ms), pero el
   Cerebro 2 indica que las métricas físicas están nominales ("bien"), O
2. Si el cuerpo está en pánico o estrés fisiológico (ritmo cardíaco > 95 bpm) pero la voz
   aparenta estar artificialmente calmada y formalizada con alta densidad léxica (0.8),
el Cerebro 4 concluye que existe un sesgo conductual y emite:
   {"alerta_astra": "Incongruencia Cognitiva Detectada. Evaluación preliminar: Posible ocultamiento de fatiga."}
"""

import logging
from typing import Any
import numpy as np

from helios_inference.domain.inference_models import EstadoAstraInferencia
from helios_inference.domain.inference_models import EstadoBiometricoInferencia

logger = logging.getLogger(__name__)


class CerebroCognitivoAstra:
    """
    Motor analítico cognitivo para detección de tensión psicológica oculta.
    Implementa el principio de Responsabilidad Única (SRP).
    """

    def __init__(
        self,
        latencia_base_ms: float = 200.0,
        densidad_base_score: float = 1.0,
        umbral_caida_similitud: float = 0.88,
        umbral_latencia_fatiga_ms: float = 500.0,
    ) -> None:
        """
        Configura los parámetros de referencia para la línea base dinámica de ASTRA.

        Args:
            latencia_base_ms: Tiempo de reacción verbal nominal del astronauta.
            densidad_base_score: Índice léxico nominal en condiciones de reposo.
            umbral_caida_similitud: Valor de corte por debajo del cual se considera discordancia angular.
            umbral_latencia_fatiga_ms: Latencia a partir de la cual se sospecha retraso psicomotor.
        """
        self._latencia_base_ms = latencia_base_ms
        self._densidad_base_score = densidad_base_score
        self._umbral_caida_similitud = umbral_caida_similitud
        self._umbral_latencia_fatiga_ms = umbral_latencia_fatiga_ms

        # Vector de línea base normalizado en R^2
        self._linea_base_vector = np.array([1.0, 1.0], dtype=np.float64)

    def calcular_similitud_coseno(self, vector_a: np.ndarray, vector_b: np.ndarray) -> float:
        """
        Calcula la similitud coseno entre dos vectores usando np.dot y np.linalg.norm.

        Args:
            vector_a: Primer vector en R^n.
            vector_b: Segundo vector en R^n.

        Returns:
            Valor escalar de similitud en el rango [-1.0, 1.0].
        """
        norma_a = float(np.linalg.norm(vector_a))
        norma_b = float(np.linalg.norm(vector_b))

        if norma_a == 0.0 or norma_b == 0.0:
            return 0.0

        producto_punto = float(np.dot(vector_a, vector_b))
        similitud = producto_punto / (norma_a * norma_b)
        # Asegurar confinamiento numérico
        return float(np.clip(similitud, -1.0, 1.0))

    def procesar(
        self,
        datos_cognicion: dict[str, Any],
        estado_biometrico: EstadoBiometricoInferencia,
        ritmo_cardiaco_bpm: float = 65.0,
    ) -> tuple[float, EstadoAstraInferencia]:
        """
        Evalúa el vector cognitivo del astronauta y detecta posible ocultamiento de fatiga o estrés.

        Args:
            datos_cognicion: Diccionario con 'latencia_voz_ms' y 'densidad_lexica_score'.
            estado_biometrico: Estado fisiológico evaluado previamente por el Cerebro 2.
            ritmo_cardiaco_bpm: Pulso cardíaco instantáneo para validar incongruencias cruzadas.

        Returns:
            Tupla conteniendo:
            - float: Coeficiente de similitud coseno con la línea base dinámica.
            - EstadoAstraInferencia: Resultado estructurado del análisis de ASTRA.
        """
        latencia_ms = float(datos_cognicion.get("latencia_voz_ms", self._latencia_base_ms))
        densidad_score = float(datos_cognicion.get("densidad_lexica_score", self._densidad_base_score))

        # Normalización dimensional para preservar proporcionalidad angular
        vector_cognitivo_norm = np.array([
            latencia_ms / self._latencia_base_ms,
            densidad_score / self._densidad_base_score,
        ], dtype=np.float64)

        # Cálculo de similitud coseno mediante álgebra lineal pura con NumPy
        similitud_coseno = self.calcular_similitud_coseno(
            vector_cognitivo_norm,
            self._linea_base_vector,
        )

        # -----------------------------------------------------------------------------
        # REGLAS DE NEGOCIO DE INCONGRUENCIA COGNITIVA
        # -----------------------------------------------------------------------------
        # Condición A: La similitud cae abruptamente (latencia se dispara a 600-900 ms)
        # pero el Cerebro 2 dice que las métricas físicas están "bien" (aparentemente normales).
        caida_similitud_con_fisico_normal = bool(
            (similitud_coseno < self._umbral_caida_similitud or latencia_ms >= self._umbral_latencia_fatiga_ms)
            and estado_biometrico.metricas_fisicas_normales
        )

        # Condición B: El cuerpo está en pánico (ritmo cardiaco > 95 bpm / cuerpo_en_panico)
        # pero la voz es formal y calmada con densidad léxica alta (ej. >= 0.75 "fingiendo estar bien").
        panico_fisico_con_voz_calmada = bool(
            (estado_biometrico.cuerpo_en_panico or ritmo_cardiaco_bpm > 95.0)
            and densidad_score >= 0.75
            and latencia_ms < 350.0
        )

        incongruencia_detectada = caida_similitud_con_fisico_normal or panico_fisico_con_voz_calmada

        alerta_mensaje: str | None = None
        if incongruencia_detectada:
            alerta_mensaje = (
                "Incongruencia Cognitiva Detectada. "
                "Evaluación preliminar: Posible ocultamiento de fatiga."
            )
            logger.warning(
                "CEREBRO 4 (ASTRA): %s | Similitud: %.3f | Latencia: %.1f ms | Pulso: %.1f bpm",
                alerta_mensaje,
                similitud_coseno,
                latencia_ms,
                ritmo_cardiaco_bpm,
            )
        else:
            logger.debug(
                "Cerebro 4 (ASTRA): Coherencia cognitiva dentro de los márgenes nominales (Similitud: %.3f)",
                similitud_coseno,
            )

        estado = EstadoAstraInferencia(
            similitud_coseno_linea_base=similitud_coseno,
            incongruencia_cognitiva_detectada=incongruencia_detectada,
            alerta_astra=alerta_mensaje,
        )

        return similitud_coseno, estado
