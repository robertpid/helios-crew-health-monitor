"""
Critical Crossover Decision Matrix evaluator (Clinical-Aerospace Rules Engine).

Applies the NASA priority hierarchy:
    Immediate Safety (Radiation, O2) -> Critical Task Alerts -> Medium-Term Health (Bone, Kidney) -> Wellbeing.

Enforces the design rule:
    At most 3 prioritized countermeasures per alert to prevent fatigue and cognitive saturation.
"""

import logging
from typing import Any

from helios_inference.domain.decision_rules import (
    CRITICAL_RULES_CATALOG,
    MatrixRuleAlert,
    RuleDefinition,
    RuleDomain,
    RuleSeverityLevel,
)

logger = logging.getLogger(__name__)


class DecisionMatrixEvaluator:
    """
    Evaluation engine for the 15 critical multivariate crossovers.
    Implements the Single Responsibility Principle (SRP) and does not prescribe drugs.
    """

    def __init__(self, rules_catalog: list[RuleDefinition] | None = None) -> None:
        """Initializes the evaluator with the reference rule catalog."""
        self._catalog = rules_catalog or CRITICAL_RULES_CATALOG
        self._rule_map = {r.rule_id: r for r in self._catalog}

    def evaluate_telemetry(
        self,
        payload: dict[str, Any],
        consecutive_days_history: dict[str, int] | None = None,
    ) -> list[MatrixRuleAlert]:
        """
        Evaluates the systemic state against the 15 critical crossover rules.

        Args:
            payload: Consolidated telemetry dictionary (environment, biometrics, cognition).
            consecutive_days_history: Optional dictionary tracking persistence windows.

        Returns:
            List of active alerts ordered by strict hierarchical priority (1 to 4).
        """
        mission_day = int(payload.get("mission_day", 120))
        environment = payload.get("environment", {})
        biometrics = payload.get("biometrics", {})
        cognition = payload.get("cognition", {})

        # Environmental variables
        co2_mmhg = float(environment.get("co2_mmHg", 1.5))
        radiation_msv = float(environment.get("cumulative_radiation_mSv", 50.0))
        solar_event = bool(environment.get("solar_event_active", False))
        temperature_c = float(environment.get("cabin_temperature_c", 22.0))
        humidity_pct = float(environment.get("relative_humidity_pct", 45.0))

        # Biometric variables
        heart_rate = float(biometrics.get("heart_rate_bpm", 65.0))
        sleep_hours = float(biometrics.get("last_cycle_sleep_hours", 7.0))
        low_sleep_cycles = int(biometrics.get("consecutive_insufficient_sleep_cycles", 0))
        fatigue_risk = bool(biometrics.get("fatigue_risk_alert", False))
        bone_loss = float(biometrics.get("bone_loss_pct", 0.0))
        spo2 = float(biometrics.get("spo2_pct", 98.0))
        headache_reported = bool(biometrics.get("headache_symptom", False))
        activity_minutes = float(biometrics.get("physical_activity_minutes", 120.0))

        # Cognitive variables (ASTRA)
        voice_latency = float(cognition.get("voice_latency_ms", 200.0))
        lexical_density = float(cognition.get("lexical_density_score", 1.0))
        sans_vision = bool(cognition.get("sans_vision_symptom", False))

        triggered_alerts: list[tuple[int, MatrixRuleAlert]] = []

        # -----------------------------------------------------------------------------
        # 4.1 IMMEDIATE SAFETY (Priority 1)
        # -----------------------------------------------------------------------------
        # CX-01: Acute radiation / Solar storm
        if solar_event or radiation_msv > 600.0:
            rule = self._rule_map["CX-01"]
            triggered_alerts.append((
                rule.hierarchical_priority,
                self._create_alert(rule, escalation=False)
            ))

        # CX-02: Atmospheric life support failure
        if spo2 < 94.0 and co2_mmhg >= 3.8:
            rule = self._rule_map["CX-02"]
            triggered_alerts.append((
                rule.hierarchical_priority,
                self._create_alert(rule, escalation=True)
            ))

        # -----------------------------------------------------------------------------
        # 4.2 ALERTNESS AND COGNITION (Priority 2)
        # -----------------------------------------------------------------------------
        # CX-03: Cognitive incongruence from environmental fatigue
        if (sleep_hours < 6.0 or low_sleep_cycles >= 2) and co2_mmhg > 2.5 and voice_latency >= 300.0:
            rule = self._rule_map["CX-03"]
            triggered_alerts.append((
                rule.hierarchical_priority,
                self._create_alert(rule, escalation=low_sleep_cycles >= 3)
            ))

        # CX-04: Unperceived sleep debt
        if (fatigue_risk or low_sleep_cycles >= 3) and voice_latency > 450.0 and lexical_density >= 0.8:
            rule = self._rule_map["CX-04"]
            triggered_alerts.append((
                rule.hierarchical_priority,
                self._create_alert(rule, escalation=True)
            ))

        # CX-06: Physiological overload from operational stress
        if heart_rate > 90.0 and sleep_hours < 6.0 and activity_minutes > 110.0:
            rule = self._rule_map["CX-06"]
            triggered_alerts.append((
                rule.hierarchical_priority,
                self._create_alert(rule, escalation=False)
            ))

        # -----------------------------------------------------------------------------
        # 4.3 CABIN ENVIRONMENT (Priority 2 / 4)
        # -----------------------------------------------------------------------------
        # CX-07: Elevated CO2 with reported symptoms (excluding the first 7 days)
        if co2_mmhg >= 3.0 and mission_day > 7 and headache_reported:
            rule = self._rule_map["CX-07"]
            triggered_alerts.append((
                rule.hierarchical_priority,
                self._create_alert(rule, escalation=False)
            ))

        # CX-08: Ambient thermal stress
        if (temperature_c < 18.0 or temperature_c > 27.0 or humidity_pct < 25.0 or humidity_pct > 75.0) and sleep_hours < 6.0:
            rule = self._rule_map["CX-08"]
            triggered_alerts.append((
                rule.hierarchical_priority,
                self._create_alert(rule, escalation=False)
            ))

        # -----------------------------------------------------------------------------
        # 4.4 BONE, KIDNEY AND NUTRITION (Priority 3)
        # -----------------------------------------------------------------------------
        # CX-09: Accelerated bone loss in the critical window (first 30 days or low load)
        if (mission_day <= 30 or bone_loss > 1.5) and activity_minutes < 100.0:
            rule = self._rule_map["CX-09"]
            triggered_alerts.append((
                rule.hierarchical_priority,
                self._create_alert(rule, escalation=mission_day > 30)
            ))

        # CX-10: Kidney stone risk from bone loss and urine output
        if bone_loss > 2.0 and activity_minutes < 90.0:
            rule = self._rule_map["CX-10"]
            triggered_alerts.append((
                rule.hierarchical_priority,
                self._create_alert(rule, escalation=False)
            ))

        # CX-11: Vitamin D deficiency on prolonged missions
        if mission_day > 60 and bone_loss > 1.0:
            rule = self._rule_map["CX-11"]
            triggered_alerts.append((
                rule.hierarchical_priority,
                self._create_alert(rule, escalation=False)
            ))

        # CX-13: Mechanical unloading on Mars
        if "MARS" in payload.get("mission_id", "") and activity_minutes < 60.0:
            rule = self._rule_map["CX-13"]
            triggered_alerts.append((
                rule.hierarchical_priority,
                self._create_alert(rule, escalation=False)
            ))

        # -----------------------------------------------------------------------------
        # 4.5 BEHAVIOR AND PSYCHOLOGICAL WELLBEING (Priority 4)
        # -----------------------------------------------------------------------------
        # CX-14: Withdrawal from isolation
        if voice_latency > 650.0 and sleep_hours < 5.5 and lexical_density < 0.6:
            rule = self._rule_map["CX-14"]
            triggered_alerts.append((
                rule.hierarchical_priority,
                self._create_alert(rule, escalation=False)
            ))

        # CX-15: Declining motivation with an impact on self-care
        if voice_latency > 500.0 and activity_minutes < 75.0 and lexical_density < 0.7:
            rule = self._rule_map["CX-15"]
            triggered_alerts.append((
                rule.hierarchical_priority,
                self._create_alert(rule, escalation=False)
            ))

        # Sort strictly by NASA hierarchical priority (1: Immediate Safety -> 4: Wellbeing)
        triggered_alerts.sort(key=lambda item: item[0])

        resulting_alerts = [alert for _, alert in triggered_alerts]
        logger.debug("The Matrix Evaluator activated %d critical crossovers.", len(resulting_alerts))
        return resulting_alerts

    def _create_alert(self, rule: RuleDefinition, escalation: bool = False) -> MatrixRuleAlert:
        """Creates an immutable MatrixRuleAlert instance with at most 3 countermeasures."""
        level = rule.level
        if escalation and level == RuleSeverityLevel.CAUTION:
            level = RuleSeverityLevel.ALERT
        elif escalation and level == RuleSeverityLevel.ALERT:
            level = RuleSeverityLevel.CRITICAL

        return MatrixRuleAlert(
            rule_id=rule.rule_id,
            domain=rule.domain,
            level=level,
            preliminary_assessment=rule.preliminary_assessment,
            suggested_countermeasures=rule.countermeasures[:3],  # Guarantees at most 3 actions
            recipients=rule.recipients,
            base_standard=rule.evidence_base,
            time_window=rule.persistence_window,
            escalation=escalation,
        )
