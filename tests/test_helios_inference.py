"""
Unit and integration test suite for the H.E.L.I.O.S. Inference Engine.

Verifies the mathematical formulation of the 4 brains, the Kronecker tensor product,
the ASTRA cosine similarity, dependency injection and the FastAPI endpoints.
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient

from helios_inference.brains.brain_1_environmental import EnvironmentalBrain
from helios_inference.brains.brain_2_biometric import BiometricBrain
from helios_inference.brains.brain_3_fusion_graph import FusionGraphBrain
from helios_inference.brains.brain_4_astra import AstraCognitiveBrain
from helios_inference.domain.inference_models import BiometricInferenceState
from helios_inference.domain.decision_rules import CRITICAL_RULES_CATALOG, RuleSeverityLevel
from helios_inference.services.decision_matrix_evaluator import DecisionMatrixEvaluator
from helios_inference.services.inference_engine import InferenceEngine
from main import app


@pytest.fixture
def api_client() -> TestClient:
    """Fixture for the FastAPI test HTTP client."""
    return TestClient(app)


class TestEnvironmentalBrain:
    """Tests of the environmental engine (Brain 1)."""

    def test_nominal_conditions(self) -> None:
        brain = EnvironmentalBrain()
        data = {
            "co2_mmHg": 1.5,
            "cumulative_radiation_mSv": 50.0,
            "cabin_pressure_kpa": 101.3,
            "solar_event_active": False,
        }
        vec, state = brain.process(data)
        assert np.array_equal(vec, np.array([0.0, 0.0, 0.0]))
        assert not state.co2_exceeded
        assert not state.critical_radiation
        assert not state.abnormal_pressure
        assert len(state.activated_labels) == 0

    def test_co2_exceeded_alert(self) -> None:
        brain = EnvironmentalBrain(co2_threshold_mmhg=3.0)
        data = {"co2_mmHg": 3.8, "cumulative_radiation_mSv": 40.0, "cabin_pressure_kpa": 100.0}
        vec, state = brain.process(data)
        assert np.array_equal(vec, np.array([1.0, 0.0, 0.0]))
        assert state.co2_exceeded
        assert any("ELEVATED_CO2_ALERT" in label for label in state.activated_labels)

    def test_solar_storm_alert(self) -> None:
        brain = EnvironmentalBrain()
        data = {
            "co2_mmHg": 1.5,
            "cumulative_radiation_mSv": 70.0,
            "cabin_pressure_kpa": 101.3,
            "solar_event_active": True,
        }
        vec, state = brain.process(data)
        assert np.array_equal(vec, np.array([0.0, 1.0, 0.0]))
        assert state.critical_radiation


class TestBiometricBrain:
    """Tests of the physiological engine (Brain 2)."""

    def test_nominal_biometrics(self) -> None:
        brain = BiometricBrain()
        data = {
            "heart_rate_bpm": 65.0,
            "last_cycle_sleep_hours": 7.5,
            "bone_loss_pct": 0.5,
        }
        vec, state = brain.process(data, mission_day=15, sans_symptom=False)
        assert np.array_equal(vec, np.array([0.0, 0.0, 0.0, 0.0]))
        assert state.normal_physical_metrics
        assert not state.body_in_panic

    def test_fatigue_and_bone_risk_alert(self) -> None:
        brain = BiometricBrain()
        data = {
            "heart_rate_bpm": 68.0,
            "last_cycle_sleep_hours": 4.5,
            "bone_loss_pct": 2.1,
            "fatigue_risk_alert": True,
        }
        vec, state = brain.process(data, mission_day=45, sans_symptom=True)
        # nominal pulse (0), low sleep (1), bone > 30 days (1), sans (1)
        assert np.array_equal(vec, np.array([0.0, 1.0, 1.0, 1.0]))
        assert not state.normal_physical_metrics


class TestKroneckerFusionGraphBrain:
    """Tests of the Kronecker tensor product and matrix graph (Brain 3)."""

    def test_nominal_state_kronecker_zero(self) -> None:
        brain = FusionGraphBrain(severe_hazard_threshold=6.5)
        v_env = np.array([0.0, 0.0, 0.0])
        v_bio = np.array([0.0, 0.0, 0.0, 0.0])

        hazard_vec, state = brain.fuse(v_env, v_bio)
        assert hazard_vec.shape == (12,)
        assert np.all(hazard_vec == 0.0)
        assert not state.severe_physiological_stress
        assert state.max_severity_score == 0.0

    def test_co2_and_sans_severe_trigger(self) -> None:
        """
        Critical crossover: elevated CO2 (environmental index 0) and SANS present (biometric index 3).
        In the Kronecker product, the resulting index is 4*0 + 3 = 3 (CO2_WITH_SANS_INTRACRANIAL_HYPERTENSION).
        The clinical weight is 9.2, exceeding the 6.5 threshold.
        """
        brain = FusionGraphBrain(severe_hazard_threshold=6.5)
        v_env = np.array([1.0, 0.0, 0.0])  # CO2 alert
        v_bio = np.array([0.0, 0.0, 0.0, 1.0])  # SANS alert

        hazard_vec, state = brain.fuse(v_env, v_bio)
        assert state.argmax_index == 3
        assert state.critical_synergy_edge == "CO2_WITH_SANS_INTRACRANIAL_HYPERTENSION"
        assert state.max_severity_score == 9.2
        assert state.severe_physiological_stress


class TestAstraCognitiveBrain:
    """Tests of ASTRA and cognitive incongruence detection (Brain 4)."""

    def test_nominal_similarity(self) -> None:
        brain = AstraCognitiveBrain()
        data = {"voice_latency_ms": 200.0, "lexical_density_score": 1.0}
        bio_state = BiometricInferenceState(
            biometric_vector=[0.0, 0.0, 0.0, 0.0],
            activated_labels=[],
            normal_physical_metrics=True,
            body_in_panic=False,
        )

        sim, state = brain.process(data, bio_state, heart_rate_bpm=65.0)
        assert pytest.approx(sim, abs=0.01) == 1.0
        assert not state.cognitive_incongruence_detected
        assert state.astra_alert is None

    def test_hidden_fatigue_incongruence(self) -> None:
        """
        Voice latency spiked to 850 ms (acute psychomotor delay),
        while the body apparently reports normal metrics.
        """
        brain = AstraCognitiveBrain()
        data = {"voice_latency_ms": 850.0, "lexical_density_score": 0.35}
        bio_state = BiometricInferenceState(
            biometric_vector=[0.0, 0.0, 0.0, 0.0],
            activated_labels=[],
            normal_physical_metrics=True,
            body_in_panic=False,
        )

        sim, state = brain.process(data, bio_state, heart_rate_bpm=64.0)
        assert state.cognitive_incongruence_detected
        assert state.astra_alert == (
            "Cognitive Incongruence Detected. "
            "Preliminary assessment: Possible fatigue masking."
        )

    def test_physical_panic_calm_speech_incongruence(self) -> None:
        """
        Body in severe tachycardia (115 bpm) but the voice is formalized and calm (density 0.85).
        """
        brain = AstraCognitiveBrain()
        data = {"voice_latency_ms": 220.0, "lexical_density_score": 0.85}
        bio_state = BiometricInferenceState(
            biometric_vector=[1.0, 0.0, 0.0, 0.0],
            activated_labels=["ABNORMAL_PULSE_ALERT: 115 bpm"],
            normal_physical_metrics=False,
            body_in_panic=True,
        )

        sim, state = brain.process(data, bio_state, heart_rate_bpm=115.0)
        assert state.cognitive_incongruence_detected
        assert "Cognitive Incongruence Detected" in str(state.astra_alert)


class TestInferenceEngineOrchestrator:
    """Tests of the complete central orchestrator."""

    def test_full_run_in_milliseconds(self) -> None:
        engine = InferenceEngine()
        payload = {
            "mission_id": "ARES-VI-MARS-EXPEDITION",
            "mission_day": 120,
            "astronaut_id": "ASTRO-HELIOS-01",
            "environment": {"co2_mmHg": 3.4, "cumulative_radiation_mSv": 90.0, "cabin_pressure_kpa": 101.3},
            "biometrics": {"heart_rate_bpm": 70.0, "last_cycle_sleep_hours": 5.2, "bone_loss_pct": 1.8},
            "cognition": {"voice_latency_ms": 750.0, "lexical_density_score": 0.4, "sans_vision_symptom": True},
        }

        report = engine.process_telemetry(payload)
        assert report.mission_day == 120
        assert report.compute_time_ms < 15.0  # Under 15 ms on Edge AI
        assert len(report.active_preliminary_assessments) > 0
        assert report.brain_3_fusion_graph.kronecker_vector_dimension == 12


class TestFastAPIEndpoints:
    """Tests of the FastAPI REST endpoints."""

    def test_root_endpoint(self, api_client: TestClient) -> None:
        resp = api_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["system"] == "H.E.L.I.O.S. Edge AI Inference Engine"
        assert len(data["active_brains"]) == 4

    def test_health_endpoint(self, api_client: TestClient) -> None:
        resp = api_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["state"] == "OK"

    def test_fusion_result_endpoint(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/fusion/result")
        assert resp.status_code == 200
        data = resp.json()
        assert "brain_1_environmental" in data
        assert "brain_2_biometric" in data
        assert "brain_3_fusion_graph" in data
        assert "brain_4_astra" in data

    def test_infer_post_endpoint(self, api_client: TestClient) -> None:
        test_payload = {
            "mission_id": "ARES-TEST",
            "mission_day": 95,
            "astronaut_id": "ASTRO-02",
            "environment": {"co2_mmHg": 3.6, "cumulative_radiation_mSv": 110.0, "cabin_pressure_kpa": 101.0},
            "biometrics": {"heart_rate_bpm": 62.0, "last_cycle_sleep_hours": 6.8, "bone_loss_pct": 1.2},
            "cognition": {"voice_latency_ms": 210.0, "lexical_density_score": 0.92, "sans_vision_symptom": False},
        }
        resp = api_client.post("/api/v1/infer", json=test_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["mission_id"] == "ARES-TEST"
        assert data["brain_1_environmental"]["co2_exceeded"] is True

    def test_decision_matrix_catalog_endpoint(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/decision-matrix")
        assert resp.status_code == 200
        rules = resp.json()
        assert len(rules) == 15
        ids = [r["rule_id"] for r in rules]
        assert "CX-01" in ids
        assert "CX-09" in ids
        assert "CX-15" in ids

    def test_active_countermeasures_endpoint(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/countermeasures/active")
        assert resp.status_code == 200
        data = resp.json()
        assert data["max_allowed_actions"] == 3
        assert len(data["prioritized_countermeasures"]) <= 3

    def test_psychological_questions_endpoint(self, api_client: TestClient) -> None:
        resp = api_client.get("/api/v1/psychological/questions")
        assert resp.status_code == 200
        questions = resp.json()
        assert len(questions) == 3
        assert questions[0]["question_id"] == 1

    def test_psychological_assessment_endpoint(self, api_client: TestClient) -> None:
        payload = {
            "question_id": 3,
            "response_text": "Fine, we are relaxed here.",
            "words_per_minute": 133.0,
            "heart_rate_bpm": 68.0,
        }
        resp = api_client.post("/api/v1/psychological/evaluate", json=payload)
        assert resp.status_code == 200
        res = resp.json()
        assert res["cognitive_state"] == "NOMINAL"
        assert res["cosine_similarity"] > 0.90
        assert not res["incongruence_detected"]
        assert "Sol 120" in res["assistant_response"] or "relaxed" in payload["response_text"]


class TestDecisionMatrixEvaluator:
    """Tests of the evaluator of NASA's 15-crossover matrix."""

    def test_full_catalog_15_rules(self) -> None:
        evaluator = DecisionMatrixEvaluator()
        assert len(evaluator._catalog) == 15

    def test_cx01_solar_storm_trigger_max_3_countermeasures(self) -> None:
        evaluator = DecisionMatrixEvaluator()
        payload = {
            "mission_id": "ARES-MARS",
            "mission_day": 95,
            "environment": {"solar_event_active": True, "co2_mmHg": 1.8},
            "biometrics": {"heart_rate_bpm": 65.0, "last_cycle_sleep_hours": 7.0},
            "cognition": {"voice_latency_ms": 200.0},
        }
        alerts = evaluator.evaluate_telemetry(payload)
        cx01 = next((a for a in alerts if a.rule_id == "CX-01"), None)
        assert cx01 is not None
        assert cx01.level == RuleSeverityLevel.CRITICAL
        assert len(cx01.suggested_countermeasures) <= 3
        assert any("storm shelter" in c for c in cx01.suggested_countermeasures)

    def test_cx09_bone_loss_critical_window_trigger(self) -> None:
        evaluator = DecisionMatrixEvaluator()
        payload = {
            "mission_id": "ARES-MARS",
            "mission_day": 20,  # Within the first 30 days
            "environment": {"co2_mmHg": 1.8},
            "biometrics": {"bone_loss_pct": 1.2, "physical_activity_minutes": 70.0},  # Low load
            "cognition": {"voice_latency_ms": 200.0},
        }
        alerts = evaluator.evaluate_telemetry(payload)
        cx09 = next((a for a in alerts if a.rule_id == "CX-09"), None)
        assert cx09 is not None
        assert cx09.domain.value == "bone_nutrition"
        assert len(cx09.suggested_countermeasures) <= 3
        assert any("squat and deadlift" in c for c in cx09.suggested_countermeasures)
