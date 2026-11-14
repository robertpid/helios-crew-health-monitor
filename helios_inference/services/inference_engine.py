"""
Motor de inferencia central de H.E.L.I.O.S. (Orquestador de los 4 Cerebros).

Aplica Inversión de Dependencias (DIP) y Responsabilidad Única (SRP):
Recibe las instancias inyectadas de los 4 cerebros y coordina el flujo secuencial
de inferencia vectorial y matricial en tiempo real sobre el borde computacional.
"""

import logging
import time
from typing import Any

from helios_inference.cerebros.cerebro_1_ambiental import CerebroAmbiental
from helios_inference.cerebros.cerebro_2_biometrico import CerebroBiometrico
from helios_inference.cerebros.cerebro_3_grafo_fusion import CerebroGrafoFusion
from helios_inference.cerebros.cerebro_4_astra import CerebroCognitivoAstra
from helios_inference.domain.inference_models import ReporteInferenciaConsolidado
from helios_inference.services.decision_matrix_evaluator import DecisionMatrixEvaluator

logger = logging.getLogger(__name__)


class InferenceEngine:
    """
    Orquestador de inferencia Edge AI de H.E.L.I.O.S.
    Ejecuta el pipeline de evaluación preliminar sobre telemetría espacial.
    """

    def __init__(
        self,
        cerebro_ambiental: CerebroAmbiental | None = None,
        cerebro_biometrico: CerebroBiometrico | None = None,
        cerebro_grafo_fusion: CerebroGrafoFusion | None = None,
        cerebro_cognitivo_astra: CerebroCognitivoAstra | None = None,
        evaluador_matriz: DecisionMatrixEvaluator | None = None,
    ) -> None:
        """
        Inicializa el motor con inyección de dependencias de los 4 cerebros y el evaluador de matriz.

        Args:
            cerebro_ambiental: Instancia del motor ambiental (Cerebro 1).
            cerebro_biometrico: Instancia del motor biométrico (Cerebro 2).
            cerebro_grafo_fusion: Instancia del orquestador matricial de grafos (Cerebro 3).
            cerebro_cognitivo_astra: Instancia de inteligencia cognitiva ASTRA (Cerebro 4).
            evaluador_matriz: Evaluador de las 15 reglas críticas de cruce de la NASA.
        """
        self._c1 = cerebro_ambiental or CerebroAmbiental()
        self._c2 = cerebro_biometrico or CerebroBiometrico()
        self._c3 = cerebro_grafo_fusion or CerebroGrafoFusion()
        self._c4 = cerebro_cognitivo_astra or CerebroCognitivoAstra()
        self._evaluador_matriz = evaluador_matriz or DecisionMatrixEvaluator()

    def procesar_telemetria(self, payload: dict[str, Any]) -> ReporteInferenciaConsolidado:
        """
        Ejecuta el ciclo completo de inferencia multivariada sobre un payload de telemetría.

        Args:
            payload: Diccionario deserializado de telemetría espacial.

        Returns:
            ReporteInferenciaConsolidado con el análisis de los 4 cerebros y evaluaciones preliminares.
        """
        tiempo_inicio = time.perf_counter()

        # Extracción y desacoplamiento de sub-dominios
        id_mision = str(payload.get("id_mision", "ARES-VI-MARS-EXPEDITION"))
        dia_mision = int(payload.get("dia_mision", 120))
        astronauta_id = str(payload.get("astronauta_id", "ASTRO-HELIOS-01"))

        datos_entorno: dict[str, Any] = payload.get("entorno", {})
        datos_biometria: dict[str, Any] = payload.get("biometria", {})
        datos_cognicion: dict[str, Any] = payload.get("cognicion", {})

        sintoma_sans = bool(
            datos_cognicion.get("sans_sintoma_vision", False)
            or datos_biometria.get("sans_sintoma_vision", False)
        )
        ritmo_cardiaco = float(datos_biometria.get("ritmo_cardiaco_bpm", 65.0))

        # -----------------------------------------------------------------------------
        # FASE 1: Inferencia Ambiental (Cerebro 1)
        # -----------------------------------------------------------------------------
        vector_ambiental, estado_c1 = self._c1.procesar(datos_entorno)

        # -----------------------------------------------------------------------------
        # FASE 2: Inferencia Fisiológica (Cerebro 2)
        # -----------------------------------------------------------------------------
        vector_biometrico, estado_c2 = self._c2.procesar(
            datos_biometria=datos_biometria,
            dia_mision=dia_mision,
            sintoma_sans=sintoma_sans,
        )

        # -----------------------------------------------------------------------------
        # FASE 3: Grafo Matricial y Fusión de Kronecker (Cerebro 3)
        # -----------------------------------------------------------------------------
        _, estado_c3 = self._c3.fusionar(
            vector_ambiental=vector_ambiental,
            vector_biometrico=vector_biometrico,
        )

        # -----------------------------------------------------------------------------
        # FASE 4: Inteligencia Vectorial Cognitiva ASTRA (Cerebro 4)
        # -----------------------------------------------------------------------------
        _, estado_c4 = self._c4.procesar(
            datos_cognicion=datos_cognicion,
            estado_biometrico=estado_c2,
            ritmo_cardiaco_bpm=ritmo_cardiaco,
        )

        # -----------------------------------------------------------------------------
        # FASE 5: Evaluación de la Matriz de Decisiones Críticas (15 Cruces NASA)
        # -----------------------------------------------------------------------------
        alertas_matriz = self._evaluador_matriz.evaluar_telemetria(payload)

        # -----------------------------------------------------------------------------
        # CONSOLIDACIÓN DE EVALUACIONES PRELIMINARES Y ALERTAS
        # -----------------------------------------------------------------------------
        evaluaciones: list[str] = []

        # Agregar alertas de Cerebro 1
        evaluaciones.extend(estado_c1.etiquetas_activadas)

        # Agregar alertas de Cerebro 2
        evaluaciones.extend(estado_c2.etiquetas_activadas)

        # Agregar alerta de fusión si se dispara estrés severo
        if estado_c3.estres_fisiologico_severo and estado_c3.evaluacion_preliminar_fusion:
            evaluaciones.append(estado_c3.evaluacion_preliminar_fusion)

        # Agregar alerta de ASTRA si hay incongruencia cognitiva
        if estado_c4.incongruencia_cognitiva_detectada and estado_c4.alerta_astra:
            evaluaciones.append(estado_c4.alerta_astra)

        # Agregar dictámenes de la matriz de decisiones
        for alerta_m in alertas_matriz:
            evaluaciones.append(f"[{alerta_m.id_regla} - {alerta_m.nivel.value}] {alerta_m.evaluacion_preliminar}")

        # Consolidar hasta 3 contramedidas priorizadas de las alertas más críticas
        contramedidas_consolidadas: list[str] = []
        for alerta_m in alertas_matriz:
            for accion in alerta_m.contramedidas_sugeridas:
                if accion not in contramedidas_consolidadas and len(contramedidas_consolidadas) < 3:
                    contramedidas_consolidadas.append(accion)
            if len(contramedidas_consolidadas) >= 3:
                break

        tiempo_total_ms = (time.perf_counter() - tiempo_inicio) * 1000.0

        reporte = ReporteInferenciaConsolidado(
            id_mision=id_mision,
            dia_mision=dia_mision,
            astronauta_id=astronauta_id,
            cerebro_1_ambiental=estado_c1,
            cerebro_2_biometrico=estado_c2,
            cerebro_3_grafo_fusion=estado_c3,
            cerebro_4_astra=estado_c4,
            evaluaciones_preliminares_activas=evaluaciones,
            alertas_matriz_decisiones=alertas_matriz,
            contramedidas_priorizadas=contramedidas_consolidadas,
            tiempo_computo_ms=round(tiempo_total_ms, 3),
            metadatos_edge={
                "motor": "H.E.L.I.O.S. Pure-NumPy Inference Engine",
                "algebra_lineal": "np.kron + np.dot + np.argmax",
                "latencia_procesamiento_ms": round(tiempo_total_ms, 3),
                "hardware_target": "Deep Space Radiation-Tolerant Single Board Computer",
                "reglas_matriz_activas": len(alertas_matriz),
            },
        )

        logger.info(
            "Ciclo de inferencia completado en %.3f ms. Evaluaciones preliminares activas: %d",
            tiempo_total_ms,
            len(evaluaciones),
        )

        return reporte
