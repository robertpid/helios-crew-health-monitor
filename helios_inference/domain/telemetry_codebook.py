"""
H.E.L.I.O.S. telemetry codebook (single source of textual truth).

Rationale
---------
An edge inference system must REDUCE the downlink volume, not amplify it. The
consolidated report repeats the same descriptive strings every cycle (findings,
countermeasures, base standards), which are catalog invariants: they are not
mission data, they are templates.

This module extracts those invariants into a codebook that is downloaded ONCE.
The persisted stream carries only:

    - stable codes   (CO2_ELEV, CX-03, KR03, ...)
    - numeric values (3.40, 5.8, 9.2, ...)

and the HUD reconstructs the text locally. The rule catalog and the edge names
are IMPORTED from their source modules, so the codebook cannot drift out of sync
with the inference logic.

Templates use positional `{0}`, `{1}`... markers over the numeric values that
accompany each code.
"""

from typing import Any, Final

from helios_inference.brains.brain_3_fusion_graph import FusionGraphBrain
from helios_inference.domain.decision_rules import CRITICAL_RULES_CATALOG

SCHEMA_VERSION: Final[int] = 1

# ======================================================================================
# CANONICAL ORDER OF THE METRICS VECTOR
# The compact record carries a positional array without keys; this order is the
# contract between the compactor and the HUD.
# ======================================================================================
METRIC_ORDER: Final[tuple[str, ...]] = (
    "co2_mmHg",
    "cumulative_radiation_mSv",
    "cabin_pressure_kpa",
    "heart_rate_bpm",
    "last_cycle_sleep_hours",
    "bone_loss_pct",
    "voice_latency_ms",
    "lexical_density_score",
)

# Indices within METRIC_ORDER, so templates can reference positions.
IDX_CO2: Final[int] = 0
IDX_RAD: Final[int] = 1
IDX_PRES: Final[int] = 2
IDX_PULSE: Final[int] = 3
IDX_SLEEP: Final[int] = 4
IDX_BONE: Final[int] = 5

# ======================================================================================
# BRAIN 1 CODES (ENVIRONMENTAL) — vector order in R^3
# ======================================================================================
ENVIRONMENTAL_CODES: Final[tuple[dict[str, Any], ...]] = (
    {
        "code": "CO2_ELEV",
        "metric": IDX_CO2,
        "template": "ELEVATED_CO2_ALERT: {0:.2f} mmHg (Limit: 3.0 mmHg)",
        "standard": "NASA-STD-3001 [V2 6004]",
    },
    {
        "code": "RAD_CRIT",
        "metric": IDX_RAD,
        "template": "CRITICAL_RADIATION_ALERT: Career dose {0:.1f} mSv",
        "event_template": "CRITICAL_RADIATION_ALERT: Solar Storm Active (SPE)",
        "standard": "NASA-STD-3001 [V1 4030]; NOAA SWPC",
    },
    {
        "code": "PRES_ANOM",
        "metric": IDX_PRES,
        "template": "ABNORMAL_CABIN_PRESSURE_ALERT: {0:.2f} kPa",
        "standard": "NASA-STD-3001 (range 95-103 kPa)",
    },
)

# ======================================================================================
# BRAIN 2 CODES (BIOMETRIC) — vector order in R^4
# ======================================================================================
BIOMETRIC_CODES: Final[tuple[dict[str, Any], ...]] = (
    {
        "code": "PULSE_ANOM",
        "metric": IDX_PULSE,
        "template": "ABNORMAL_PULSE_ALERT: {0:.1f} bpm",
    },
    {
        "code": "SLEEP_DEF",
        "metric": IDX_SLEEP,
        "template": "SLEEP_DEFICIT_ALERT: {0:.1f} hours",
    },
    {
        "code": "BONE_RISK",
        "metric": IDX_BONE,
        "template": "BONE_RISK_ALERT: Day {day} ({0:.2f}% loss)",
    },
    {
        "code": "SANS_ACT",
        "metric": None,
        "template": "SANS_ACTIVE_ALERT: Neuro-ocular alteration",
    },
)

# ======================================================================================
# BRAIN 3 CODES (KRONECKER EDGES) — KR00..KR11
# The names are imported from the brain to prevent divergence.
# ======================================================================================
FUSION_TEMPLATE: Final[str] = (
    "Preliminary cross-interaction assessment: Edge '{edge}' activated "
    "with severity {severity:.1f}/9.5."
)
SEVERE_FUSION_TEMPLATE: Final[str] = (
    " ALERT: Hazard level exceeds the safe threshold. "
    "Severe physiological stress from environment-human coupling is confirmed."
)
NOMINAL_FUSION_CODE: Final[str] = "KR_NOM"
NOMINAL_FUSION_TEXT: Final[str] = (
    "Preliminary assessment: Cross parameters within the safety envelope."
)

# ======================================================================================
# BRAIN 4 CODE (ASTRA)
# ======================================================================================
ASTRA_INCONGRUENCE_CODE: Final[str] = "ASTRA_INC"
ASTRA_INCONGRUENCE_TEXT: Final[str] = (
    "Cognitive Incongruence Detected. Preliminary assessment: Possible fatigue masking."
)

# ======================================================================================
# EXECUTION METADATA (constants: they used to travel in full every cycle)
# ======================================================================================
STATIC_EDGE_METADATA: Final[dict[str, str]] = {
    "engine": "H.E.L.I.O.S. Pure-NumPy Inference Engine",
    "linear_algebra": "np.kron + np.dot + np.argmax",
    "hardware_target": "Deep Space Radiation-Tolerant Single Board Computer",
}


def build_codebook() -> dict[str, Any]:
    """
    Assembles the complete codebook that the HUD downloads once.

    Returns:
        Serializable dictionary with every template, the rule catalog and the
        canonical metric order.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "metric_order": list(METRIC_ORDER),
        "environmental": [dict(c) for c in ENVIRONMENTAL_CODES],
        "biometric": [dict(c) for c in BIOMETRIC_CODES],
        "kronecker_edges": [
            {"code": f"KR{i:02d}", "name": name}
            for i, name in enumerate(FusionGraphBrain.GRAPH_EDGE_NAMES)
        ],
        "fusion_template": FUSION_TEMPLATE,
        "severe_fusion_template": SEVERE_FUSION_TEMPLATE,
        "fusion_nominal": {"code": NOMINAL_FUSION_CODE, "text": NOMINAL_FUSION_TEXT},
        "astra": {"code": ASTRA_INCONGRUENCE_CODE, "text": ASTRA_INCONGRUENCE_TEXT},
        "edge_metadata": dict(STATIC_EDGE_METADATA),
        "rules": [
            {
                "code": r.rule_id,
                "domain": r.domain.value,
                "level": r.level.value,
                "preliminary_assessment": r.preliminary_assessment,
                "countermeasures": list(r.countermeasures),
                "recipients": [d.value for d in r.recipients],
                "base_standard": r.evidence_base,
                "time_window": r.persistence_window,
                "priority": r.hierarchical_priority,
            }
            for r in CRITICAL_RULES_CATALOG
        ],
    }
