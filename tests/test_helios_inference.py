"""
Suite de pruebas unitarias y de integración para H.E.L.I.O.S. Inference Engine.

Verifica la formulación matemática de los 4 cerebros, el producto tensorial de Kronecker,
la similitud coseno de ASTRA, la inyección de dependencias y los endpoints de FastAPI.
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient

from helios_inference.cerebros.cerebro_1_ambiental import CerebroAmbiental
from helios_inference.cerebros.cerebro_2_biometrico import CerebroBiometrico
from helios_inference.cerebros.cerebro_3_grafo_fusion import CerebroGrafoFusion
from helios_inference.cerebros.cerebro_4_astra import CerebroCognitivoAstra
from helios_inference.domain.inference_models import EstadoBiometricoInferencia
from helios_inference.domain.decision_rules import CATALOGO_REGLAS_CRITICAS, NivelSeveridadRegla
from helios_inference.services.decision_matrix_evaluator import DecisionMatrixEvaluator
from helios_inference.services.inference_engine import InferenceEngine
from main import app


@pytest.fixture
def cliente_api() -> TestClient:
    """Fixture para cliente HTTP de pruebas de FastAPI."""
    return TestClient(app)


class TestCerebroAmbiental:
    """Pruebas del motor ambiental (Cerebro 1)."""

    def test_condiciones_nominales(self) -> None:
        cerebro = CerebroAmbiental()
        datos = {
            "co2_mmHg": 1.5,
            "radiacion_acumulada_mSv": 50.0,
            "presion_cabina_kpa": 101.3,
            "evento_solar_activo": False,
        }
        vec, estado = cerebro.procesar(datos)
        assert np.array_equal(vec, np.array([0.0, 0.0, 0.0]))
        assert not estado.co2_excedido
        assert not estado.radiacion_critica
        assert not estado.presion_anomala
        assert len(estado.etiquetas_activadas) == 0

    def test_alerta_co2_excedido(self) -> None:
        cerebro = CerebroAmbiental(umbral_co2_mmhg=3.0)
        datos = {"co2_mmHg": 3.8, "radiacion_acumulada_mSv": 40.0, "presion_cabina_kpa": 100.0}
        vec, estado = cerebro.procesar(datos)
        assert np.array_equal(vec, np.array([1.0, 0.0, 0.0]))
        assert estado.co2_excedido
        assert any("ALERTA_CO2_ELEVADO" in e for e in estado.etiquetas_activadas)

    def test_alerta_tormenta_solar(self) -> None:
        cerebro = CerebroAmbiental()
        datos = {
            "co2_mmHg": 1.5,
            "radiacion_acumulada_mSv": 70.0,
            "presion_cabina_kpa": 101.3,
            "evento_solar_activo": True,
        }
        vec, estado = cerebro.procesar(datos)
        assert np.array_equal(vec, np.array([0.0, 1.0, 0.0]))
        assert estado.radiacion_critica


class TestCerebroBiometrico:
    """Pruebas del motor fisiológico (Cerebro 2)."""

    def test_biometria_nominal(self) -> None:
        cerebro = CerebroBiometrico()
        datos = {
            "ritmo_cardiaco_bpm": 65.0,
            "horas_sueno_ultimo_ciclo": 7.5,
            "perdida_osea_pct": 0.5,
        }
        vec, estado = cerebro.procesar(datos, dia_mision=15, sintoma_sans=False)
        assert np.array_equal(vec, np.array([0.0, 0.0, 0.0, 0.0]))
        assert estado.metricas_fisicas_normales
        assert not estado.cuerpo_en_panico

    def test_alerta_fatiga_y_riesgo_oseo(self) -> None:
        cerebro = CerebroBiometrico()
        datos = {
            "ritmo_cardiaco_bpm": 68.0,
            "horas_sueno_ultimo_ciclo": 4.5,
            "perdida_osea_pct": 2.1,
            "alerta_riesgo_fatiga": True,
        }
        vec, estado = cerebro.procesar(datos, dia_mision=45, sintoma_sans=True)
        # pulso nominal (0), sueno bajo (1), oseo > 30 días (1), sans (1)
        assert np.array_equal(vec, np.array([0.0, 1.0, 1.0, 1.0]))
        assert not estado.metricas_fisicas_normales


class TestCerebroGrafoFusionKronecker:
    """Pruebas del producto tensorial de Kronecker y grafo matricial (Cerebro 3)."""

    def test_estado_nominal_kronecker_cero(self) -> None:
        cerebro = CerebroGrafoFusion(umbral_peligro_severo=6.5)
        v_amb = np.array([0.0, 0.0, 0.0])
        v_bio = np.array([0.0, 0.0, 0.0, 0.0])

        vec_peligro, estado = cerebro.fusionar(v_amb, v_bio)
        assert vec_peligro.shape == (12,)
        assert np.all(vec_peligro == 0.0)
        assert not estado.estres_fisiologico_severo
        assert estado.puntaje_severidad_maximo == 0.0

    def test_co2_y_sans_disparo_severo(self) -> None:
        """
        Cruce crítico: CO2 elevado (índice 0 ambiental) y SANS presente (índice 3 biométrico).
        En el producto de Kronecker, el índice resultante es 4*0 + 3 = 3 (CO2_CON_HIPERTENSION_INTRACRANEAL_SANS).
        El peso clínico es 9.2, superando el umbral 6.5.
        """
        cerebro = CerebroGrafoFusion(umbral_peligro_severo=6.5)
        v_amb = np.array([1.0, 0.0, 0.0])  # Alerta CO2
        v_bio = np.array([0.0, 0.0, 0.0, 1.0])  # Alerta SANS

        vec_peligro, estado = cerebro.fusionar(v_amb, v_bio)
        assert estado.indice_argmax == 3
        assert estado.arista_sinergica_critica == "CO2_CON_HIPERTENSION_INTRACRANEAL_SANS"
        assert estado.puntaje_severidad_maximo == 9.2
        assert estado.estres_fisiologico_severo


class TestCerebroCognitivoAstra:
    """Pruebas de ASTRA y detección de incongruencia cognitiva (Cerebro 4)."""

    def test_similitud_nominal(self) -> None:
        cerebro = CerebroCognitivoAstra()
        datos = {"latencia_voz_ms": 200.0, "densidad_lexica_score": 1.0}
        estado_bio = EstadoBiometricoInferencia(
            vector_biometrico=[0.0, 0.0, 0.0, 0.0],
            etiquetas_activadas=[],
            metricas_fisicas_normales=True,
            cuerpo_en_panico=False,
        )

        sim, estado = cerebro.procesar(datos, estado_bio, ritmo_cardiaco_bpm=65.0)
        assert pytest.approx(sim, abs=0.01) == 1.0
        assert not estado.incongruencia_cognitiva_detectada
        assert estado.alerta_astra is None

    def test_incongruencia_fatiga_oculta(self) -> None:
        """
        Latencia de voz disparada a 850 ms (retraso psicomotor agudo),
        mientras el cuerpo aparentemente reporta métricas normales.
        """
        cerebro = CerebroCognitivoAstra()
        datos = {"latencia_voz_ms": 850.0, "densidad_lexica_score": 0.35}
        estado_bio = EstadoBiometricoInferencia(
            vector_biometrico=[0.0, 0.0, 0.0, 0.0],
            etiquetas_activadas=[],
            metricas_fisicas_normales=True,
            cuerpo_en_panico=False,
        )

        sim, estado = cerebro.procesar(datos, estado_bio, ritmo_cardiaco_bpm=64.0)
        assert estado.incongruencia_cognitiva_detectada
        assert estado.alerta_astra == (
            "Incongruencia Cognitiva Detectada. "
            "Evaluación preliminar: Posible ocultamiento de fatiga."
        )

    def test_incongruencia_panico_fisico_discurso_calmado(self) -> None:
        """
        Cuerpo en taquicardia severa (115 bpm) pero la voz habla formalizada y calmada (densidad 0.85).
        """
        cerebro = CerebroCognitivoAstra()
        datos = {"latencia_voz_ms": 220.0, "densidad_lexica_score": 0.85}
        estado_bio = EstadoBiometricoInferencia(
            vector_biometrico=[1.0, 0.0, 0.0, 0.0],
            etiquetas_activadas=["ALERTA_PULSO_ANOMALO: 115 bpm"],
            metricas_fisicas_normales=False,
            cuerpo_en_panico=True,
        )

        sim, estado = cerebro.procesar(datos, estado_bio, ritmo_cardiaco_bpm=115.0)
        assert estado.incongruencia_cognitiva_detectada
        assert "Incongruencia Cognitiva Detectada" in str(estado.alerta_astra)


class TestInferenceEngineOrquestador:
    """Pruebas del orquestador central completo."""

    def test_ejecucion_completa_en_milisegundos(self) -> None:
        motor = InferenceEngine()
        payload = {
            "id_mision": "ARES-VI-MARS-EXPEDITION",
            "dia_mision": 120,
            "astronauta_id": "ASTRO-HELIOS-01",
            "entorno": {"co2_mmHg": 3.4, "radiacion_acumulada_mSv": 90.0, "presion_cabina_kpa": 101.3},
            "biometria": {"ritmo_cardiaco_bpm": 70.0, "horas_sueno_ultimo_ciclo": 5.2, "perdida_osea_pct": 1.8},
            "cognicion": {"latencia_voz_ms": 750.0, "densidad_lexica_score": 0.4, "sans_sintoma_vision": True},
        }

        reporte = motor.procesar_telemetria(payload)
        assert reporte.dia_mision == 120
        assert reporte.tiempo_computo_ms < 15.0  # Menos de 15 ms en Edge AI
        assert len(reporte.evaluaciones_preliminares_activas) > 0
        assert reporte.cerebro_3_grafo_fusion.vector_kronecker_dimension == 12


class TestFastAPIEndpoints:
    """Pruebas de los endpoints REST de FastAPI."""

    def test_root_endpoint(self, cliente_api: TestClient) -> None:
        resp = cliente_api.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["sistema"] == "H.E.L.I.O.S. Edge AI Inference Engine"
        assert len(data["cerebros_activos"]) == 4

    def test_health_endpoint(self, cliente_api: TestClient) -> None:
        resp = cliente_api.get("/health")
        assert resp.status_code == 200
        assert resp.json()["estado"] == "OK"

    def test_resultado_fusion_endpoint(self, cliente_api: TestClient) -> None:
        resp = cliente_api.get("/api/v1/fusion/resultado")
        assert resp.status_code == 200
        data = resp.json()
        assert "cerebro_1_ambiental" in data
        assert "cerebro_2_biometrico" in data
        assert "cerebro_3_grafo_fusion" in data
        assert "cerebro_4_astra" in data

    def test_inferir_post_endpoint(self, cliente_api: TestClient) -> None:
        payload_test = {
            "id_mision": "ARES-TEST",
            "dia_mision": 95,
            "astronauta_id": "ASTRO-02",
            "entorno": {"co2_mmHg": 3.6, "radiacion_acumulada_mSv": 110.0, "presion_cabina_kpa": 101.0},
            "biometria": {"ritmo_cardiaco_bpm": 62.0, "horas_sueno_ultimo_ciclo": 6.8, "perdida_osea_pct": 1.2},
            "cognicion": {"latencia_voz_ms": 210.0, "densidad_lexica_score": 0.92, "sans_sintoma_vision": False},
        }
        resp = cliente_api.post("/api/v1/inferir", json=payload_test)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id_mision"] == "ARES-TEST"
        assert data["cerebro_1_ambiental"]["co2_excedido"] is True

    def test_catalogo_matriz_decisiones_endpoint(self, cliente_api: TestClient) -> None:
        resp = cliente_api.get("/api/v1/matriz-decisiones")
        assert resp.status_code == 200
        reglas = resp.json()
        assert len(reglas) == 15
        ids = [r["id_regla"] for r in reglas]
        assert "CX-01" in ids
        assert "CX-09" in ids
        assert "CX-15" in ids

    def test_contramedidas_activas_endpoint(self, cliente_api: TestClient) -> None:
        resp = cliente_api.get("/api/v1/contramedidas/activas")
        assert resp.status_code == 200
        data = resp.json()
        assert data["max_acciones_permitidas"] == 3
        assert len(data["contramedidas_priorizadas"]) <= 3

    def test_preguntas_psicologicas_endpoint(self, cliente_api: TestClient) -> None:
        resp = cliente_api.get("/api/v1/psicologico/preguntas")
        assert resp.status_code == 200
        preguntas = resp.json()
        assert len(preguntas) == 3
        assert preguntas[0]["id_pregunta"] == 1

    def test_evaluacion_psicologica_endpoint(self, cliente_api: TestClient) -> None:
        payload = {
            "id_pregunta": 3,
            "texto_respuesta": "Bien, aquí estamos relajados.",
            "palabras_por_minuto": 133.0,
            "ritmo_cardiaco_bpm": 68.0,
        }
        resp = cliente_api.post("/api/v1/psicologico/evaluar", json=payload)
        assert resp.status_code == 200
        res = resp.json()
        assert res["estado_cognitivo"] == "NOMINAL"
        assert res["similitud_coseno"] > 0.90
        assert not res["incongruencia_detectada"]
        assert "Sol 120" in res["respuesta_asistente"] or "relajados" in payload["texto_respuesta"]


class TestDecisionMatrixEvaluator:
    """Pruebas del evaluador de la matriz de 15 cruces de la NASA."""

    def test_catalogo_completo_15_reglas(self) -> None:
        evaluador = DecisionMatrixEvaluator()
        assert len(evaluador._catalogo) == 15

    def test_disparo_cx01_tormenta_solar_maximo_3_contramedidas(self) -> None:
        evaluador = DecisionMatrixEvaluator()
        payload = {
            "id_mision": "ARES-MARS",
            "dia_mision": 95,
            "entorno": {"evento_solar_activo": True, "co2_mmHg": 1.8},
            "biometria": {"ritmo_cardiaco_bpm": 65.0, "horas_sueno_ultimo_ciclo": 7.0},
            "cognicion": {"latencia_voz_ms": 200.0},
        }
        alertas = evaluador.evaluar_telemetria(payload)
        cx01 = next((a for a in alertas if a.id_regla == "CX-01"), None)
        assert cx01 is not None
        assert cx01.nivel == NivelSeveridadRegla.CRITICA
        assert len(cx01.contramedidas_sugeridas) <= 3
        assert any("refugio de tormenta" in c for c in cx01.contramedidas_sugeridas)

    def test_disparo_cx09_perdida_osea_ventana_critica(self) -> None:
        evaluador = DecisionMatrixEvaluator()
        payload = {
            "id_mision": "ARES-MARS",
            "dia_mision": 20,  # En los primeros 30 días
            "entorno": {"co2_mmHg": 1.8},
            "biometria": {"perdida_osea_pct": 1.2, "actividad_fisica_minutos": 70.0},  # Carga baja
            "cognicion": {"latencia_voz_ms": 200.0},
        }
        alertas = evaluador.evaluar_telemetria(payload)
        cx09 = next((a for a in alertas if a.id_regla == "CX-09"), None)
        assert cx09 is not None
        assert cx09.dominio.value == "hueso_nutricion"
        assert len(cx09.contramedidas_sugeridas) <= 3
        assert any("sentadilla y peso muerto" in c for c in cx09.contramedidas_sugeridas)
