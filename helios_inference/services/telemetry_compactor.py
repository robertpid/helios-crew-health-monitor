"""
H.E.L.I.O.S. telemetry compactor.

Converts the consolidated report (text-rich, for debugging) into the compact record
that is persisted and transmitted, and provides the inverse operation for any
consumer that needs the text on the server.

Design principle: the compactor reads ONLY structured fields (boolean flags,
indices, scores). It never parses the descriptive strings of the report, so a
wording change in the brains cannot break the compaction or alter the size of the
persisted stream.
"""

from typing import Any

from helios_inference.domain.compact_models import CompactTelemetryRecord
from helios_inference.domain.inference_models import ConsolidatedInferenceReport
from helios_inference.domain.telemetry_codebook import (
    ASTRA_INCONGRUENCE_CODE,
    ASTRA_INCONGRUENCE_TEXT,
    BIOMETRIC_CODES,
    ENVIRONMENTAL_CODES,
    FUSION_TEMPLATE,
    METRIC_ORDER,
    NOMINAL_FUSION_CODE,
    NOMINAL_FUSION_TEXT,
    SCHEMA_VERSION,
    SEVERE_FUSION_TEMPLATE,
    STATIC_EDGE_METADATA,
)
from helios_inference.brains.brain_3_fusion_graph import FusionGraphBrain

ESCALATION_SUFFIX = "!"


def _extract_metrics(payload: dict[str, Any]) -> list[float]:
    """
    Flattens the input payload into the positional vector of METRIC_ORDER.

    Args:
        payload: Raw telemetry with environment/biometrics/cognition sub-dictionaries.

    Returns:
        List of floats in the canonical order declared by the codebook.
    """
    flat: dict[str, Any] = {}
    for section in ("environment", "biometrics", "cognition"):
        data = payload.get(section) or {}
        if isinstance(data, dict):
            flat.update(data)

    values: list[float] = []
    for key in METRIC_ORDER:
        try:
            values.append(round(float(flat.get(key, 0.0)), 3))
        except (TypeError, ValueError):
            values.append(0.0)
    return values


def compact_record(
    report: ConsolidatedInferenceReport,
    payload: dict[str, Any],
) -> CompactTelemetryRecord:
    """
    Reduces a consolidated report to its equivalent compact record.

    Args:
        report: Complete result emitted by the inference engine.
        payload: Raw telemetry that produced the report (supplies the numeric values).

    Returns:
        CompactTelemetryRecord ready to persist or transmit.
    """
    b1 = report.brain_1_environmental
    b2 = report.brain_2_biometric
    b3 = report.brain_3_fusion_graph
    b4 = report.brain_4_astra

    environment = payload.get("environment") or {}
    solar_event = bool(environment.get("solar_event_active", False)) if isinstance(environment, dict) else False

    # An edge is only meaningful if there was synergy; the nominal name is encoded as -1.
    has_synergy = b3.critical_synergy_edge in FusionGraphBrain.GRAPH_EDGE_NAMES
    edge_index = b3.argmax_index if has_synergy else -1

    rule_codes = [
        f"{alert.rule_id}{ESCALATION_SUFFIX}" if alert.escalation else alert.rule_id
        for alert in report.decision_matrix_alerts
    ]

    return CompactTelemetryRecord(
        v=SCHEMA_VERSION,
        ts=int(report.inference_timestamp.timestamp()),
        mis=report.mission_id,
        ast=report.astronaut_id,
        day=report.mission_day,
        amb=[int(x) for x in b1.environmental_vector],
        bio=[int(x) for x in b2.biometric_vector],
        sol=int(solar_event),
        met=_extract_metrics(payload),
        kr=edge_index,
        krs=round(b3.max_severity_score, 2),
        krx=int(b3.severe_physiological_stress),
        cos=round(b4.baseline_cosine_similarity, 4),
        inc=int(b4.cognitive_incongruence_detected),
        rg=rule_codes,
        ms=report.compute_time_ms,
    )


def expand(record: CompactTelemetryRecord, codebook: dict[str, Any]) -> dict[str, Any]:
    """
    Reconstructs the descriptive text from the compact record and the codebook.

    This is the normative reference of the algorithm the HUD runs in JavaScript:
    both implementations must produce exactly the same strings.

    Args:
        record: Compact record received from the link.
        codebook: Codebook downloaded once.

    Returns:
        Dictionary with the assessments and countermeasures already in readable text.
    """
    assessments: list[str] = []
    met = record.met

    # --- Brain 1: environmental labels -------------------------------------------
    for i, flag in enumerate(record.amb):
        if not flag or i >= len(codebook["environmental"]):
            continue
        entry = codebook["environmental"][i]
        if entry["code"] == "RAD_CRIT" and record.sol:
            assessments.append(entry["event_template"])
        else:
            idx = entry["metric"]
            value = met[idx] if idx is not None and idx < len(met) else 0.0
            assessments.append(entry["template"].format(value))

    # --- Brain 2: biometric labels ------------------------------------------------
    for i, flag in enumerate(record.bio):
        if not flag or i >= len(codebook["biometric"]):
            continue
        entry = codebook["biometric"][i]
        idx = entry["metric"]
        value = met[idx] if idx is not None and idx < len(met) else 0.0
        assessments.append(entry["template"].format(value, day=record.day))

    # --- Brain 3: dominant graph edge ---------------------------------------------
    if record.kr >= 0:
        edge = codebook["kronecker_edges"][record.kr]["name"]
        fusion_text = codebook["fusion_template"].format(edge=edge, severity=record.krs)
        if record.krx:
            fusion_text += codebook["severe_fusion_template"]
            assessments.append(fusion_text)
        critical_edge = edge
    else:
        fusion_text = codebook["fusion_nominal"]["text"]
        critical_edge = "NOMINAL_STATE_NO_ADVERSE_SYNERGIES"

    # --- Brain 4: ASTRA ------------------------------------------------------------
    astra_alert = codebook["astra"]["text"] if record.inc else None
    if astra_alert:
        assessments.append(astra_alert)

    # --- Decision matrix -----------------------------------------------------------
    rule_map = {r["code"]: r for r in codebook["rules"]}
    escalated = {"CAUTION": "ALERT", "ALERT": "CRITICAL", "CRITICAL": "CRITICAL"}

    alerts: list[dict[str, Any]] = []
    countermeasures: list[str] = []
    for raw_code in record.rg:
        escalation = raw_code.endswith(ESCALATION_SUFFIX)
        code = raw_code.rstrip(ESCALATION_SUFFIX)
        rule = rule_map.get(code)
        if rule is None:
            continue
        level = escalated[rule["level"]] if escalation else rule["level"]
        assessments.append(f"[{code} - {level}] {rule['preliminary_assessment']}")
        alerts.append({
            "rule_id": code,
            "domain": rule["domain"],
            "level": level,
            "preliminary_assessment": rule["preliminary_assessment"],
            "suggested_countermeasures": rule["countermeasures"],
            "recipients": rule["recipients"],
            "base_standard": rule["base_standard"],
            "time_window": rule["time_window"],
            "escalation": escalation,
        })
        for action in rule["countermeasures"]:
            if action not in countermeasures and len(countermeasures) < 3:
                countermeasures.append(action)

    return {
        "inference_timestamp": record.ts,
        "mission_id": record.mis,
        "astronaut_id": record.ast,
        "mission_day": record.day,
        "active_preliminary_assessments": assessments,
        "critical_synergy_edge": critical_edge,
        "fusion_preliminary_assessment": fusion_text,
        "severe_physiological_stress": bool(record.krx),
        "baseline_cosine_similarity": record.cos,
        "cognitive_incongruence_detected": bool(record.inc),
        "astra_alert": astra_alert,
        "decision_matrix_alerts": alerts,
        "prioritized_countermeasures": countermeasures,
        "compute_time_ms": record.ms,
        "edge_metadata": dict(STATIC_EDGE_METADATA),
    }
