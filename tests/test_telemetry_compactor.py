"""
Tests of the H.E.L.I.O.S. telemetry compaction.

They guarantee that the reduced link format (codes + numeric values) reconstructs
exactly the text of the consolidated report and that the volume savings stay
within the committed order of magnitude.
"""

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from helios_inference.domain.compact_models import CompactTelemetryRecord
from helios_inference.domain.telemetry_codebook import METRIC_ORDER, build_codebook
from helios_inference.services.inference_engine import InferenceEngine
from helios_inference.services.telemetry_compactor import compact_record, expand
from main import app


def _payload(**overrides: Any) -> dict[str, Any]:
    """Builds a nominal telemetry payload, allowing sections to be overridden."""
    base: dict[str, Any] = {
        "mission_id": "ARES-VI-MARS-EXPEDITION",
        "mission_day": 120,
        "astronaut_id": "ASTRO-HELIOS-01",
        "environment": {
            "co2_mmHg": 3.4,
            "cumulative_radiation_mSv": 85.0,
            "cabin_pressure_kpa": 101.3,
            "solar_event_active": False,
        },
        "biometrics": {
            "heart_rate_bpm": 68.0,
            "last_cycle_sleep_hours": 5.8,
            "bone_loss_pct": 1.8,
            "fatigue_risk_alert": False,
        },
        "cognition": {
            "voice_latency_ms": 720.0,
            "lexical_density_score": 0.82,
            "sans_vision_symptom": True,
        },
    }
    base.update(overrides)
    return base


@pytest.fixture(scope="module")
def engine() -> InferenceEngine:
    return InferenceEngine()


@pytest.fixture(scope="module")
def codebook() -> dict[str, Any]:
    return build_codebook()


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


class TestCodebook:
    """The codebook must cover the full catalog without diverging from it."""

    def test_codebook_covers_the_15_rules(self, codebook: dict[str, Any]) -> None:
        assert len(codebook["rules"]) == 15
        assert {r["code"] for r in codebook["rules"]} >= {"CX-01", "CX-03", "CX-15"}

    def test_codebook_covers_the_12_kronecker_edges(self, codebook: dict[str, Any]) -> None:
        assert len(codebook["kronecker_edges"]) == 12
        assert codebook["kronecker_edges"][3]["code"] == "KR03"

    def test_metric_order_is_a_stable_contract(self, codebook: dict[str, Any]) -> None:
        assert codebook["metric_order"] == list(METRIC_ORDER)
        assert codebook["metric_order"][0] == "co2_mmHg"


class TestLosslessReconstruction:
    """The expansion must return exactly the text the engine emitted."""

    @pytest.mark.parametrize(
        "mutation",
        [
            {},
            {"environment": {"co2_mmHg": 1.2, "cumulative_radiation_mSv": 40.0,
                             "cabin_pressure_kpa": 101.3, "solar_event_active": False}},
            {"environment": {"co2_mmHg": 4.2, "cumulative_radiation_mSv": 700.0,
                             "cabin_pressure_kpa": 88.0, "solar_event_active": True}},
            {"biometrics": {"heart_rate_bpm": 132.0, "last_cycle_sleep_hours": 3.1,
                            "bone_loss_pct": 3.2, "fatigue_risk_alert": True}},
            {"mission_day": 5},
        ],
        ids=["nominal", "no_alerts", "solar_storm", "tachycardia", "early_day"],
    )
    def test_identical_assessments(
        self, engine: InferenceEngine, codebook: dict[str, Any], mutation: dict[str, Any]
    ) -> None:
        payload = _payload(**mutation)
        report = engine.process_telemetry(payload)
        expanded = expand(compact_record(report, payload), codebook)

        assert sorted(expanded["active_preliminary_assessments"]) == sorted(
            report.active_preliminary_assessments
        )
        assert expanded["prioritized_countermeasures"] == report.prioritized_countermeasures
        assert (
            expanded["critical_synergy_edge"]
            == report.brain_3_fusion_graph.critical_synergy_edge
        )

    def test_rule_levels_respect_escalation(
        self, engine: InferenceEngine, codebook: dict[str, Any]
    ) -> None:
        payload = _payload(
            biometrics={
                "heart_rate_bpm": 68.0,
                "last_cycle_sleep_hours": 4.0,
                "bone_loss_pct": 1.8,
                "fatigue_risk_alert": True,
                "consecutive_insufficient_sleep_cycles": 4,
            }
        )
        report = engine.process_telemetry(payload)
        expanded = expand(compact_record(report, payload), codebook)

        original_levels = [(a.rule_id, a.level.value) for a in report.decision_matrix_alerts]
        expanded_levels = [(a["rule_id"], a["level"]) for a in expanded["decision_matrix_alerts"]]
        assert expanded_levels == original_levels

    def test_compactor_does_not_depend_on_report_text(
        self, engine: InferenceEngine
    ) -> None:
        """Changing the wording must not alter the compact record."""
        payload = _payload()
        report = engine.process_telemetry(payload)
        original_record = compact_record(report, payload)

        mutated = report.model_copy(
            update={"active_preliminary_assessments": ["ARBITRARY DIFFERENT TEXT"]}
        )
        assert compact_record(mutated, payload).model_dump() == original_record.model_dump()


class TestVolumeSavings:
    """The compact record must preserve the order of magnitude of the reduction."""

    def test_minimum_reduction_of_one_order_of_magnitude(self, engine: InferenceEngine) -> None:
        payload = _payload()
        report = engine.process_telemetry(payload)

        full_bytes = len(report.model_dump_json().encode("utf-8"))
        compact_bytes = len(compact_record(report, payload).model_dump_json().encode("utf-8"))

        assert compact_bytes < full_bytes / 10, (
            f"Insufficient reduction: {full_bytes} B -> {compact_bytes} B"
        )

    def test_record_absorbs_the_raw_metrics(self, engine: InferenceEngine) -> None:
        """The compact record also replaces the input payload: it must carry the metrics."""
        payload = _payload()
        record = compact_record(engine.process_telemetry(payload), payload)

        assert len(record.met) == len(METRIC_ORDER)
        assert record.met[0] == pytest.approx(payload["environment"]["co2_mmHg"])
        assert record.met[3] == pytest.approx(payload["biometrics"]["heart_rate_bpm"])


class TestTelemetryEndpoints:
    """HTTP contract of the compact telemetry router."""

    def test_codebook_is_served_cacheable(self, client: TestClient) -> None:
        resp = client.get("/api/v1/telemetry/codebook")
        assert resp.status_code == 200
        assert "max-age" in resp.headers.get("cache-control", "")
        assert len(resp.json()["rules"]) == 15

    def test_compact_cycle_is_smaller_than_the_full_report(self, client: TestClient) -> None:
        compact = client.get("/api/v1/telemetry/compact")
        full = client.get("/api/v1/fusion/result")
        assert compact.status_code == 200
        assert len(compact.content) < len(full.content)

    def test_compact_record_validates_against_its_schema(self, client: TestClient) -> None:
        record = CompactTelemetryRecord(**client.get("/api/v1/telemetry/compact").json())
        assert record.v == 1
        assert len(record.amb) == 3
        assert len(record.bio) == 4

    def test_savings_endpoint_reports_a_reduction(self, client: TestClient) -> None:
        data = client.get("/api/v1/telemetry/savings").json()
        assert data["per_cycle"]["factor"] > 1.0
        assert data["per_day_mb"]["compact"] < data["per_day_mb"]["full"]

    def test_the_hud_loads_the_code_translator(self, client: TestClient) -> None:
        assert "codebook_service.js" in client.get("/dashboard").text
