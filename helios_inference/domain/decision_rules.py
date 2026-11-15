"""
Models and catalog of the 15 critical rules of the Central Brain Decision Matrix.
Based on NASA-STD-3001, OCHMO-TB-002/003/004, NOAA SWPC, Barger et al. (2014) and Law et al. (2014).

Defines the structure of multivariate rules, severity levels and countermeasures (maximum 3).
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class RuleSeverityLevel(str, Enum):
    """Operational severity level of the alert per the NASA matrix."""
    CAUTION = "CAUTION"    # 🟡 Risk trend; corrected with habits (same day)
    ALERT = "ALERT"        # 🟠 Several combined factors; risk of affecting health (a few hours)
    CRITICAL = "CRITICAL"  # 🔴 Immediate risk to life or mission (immediate)


class RuleDomain(str, Enum):
    """Thematic category of the aerospace risk."""
    IMMEDIATE_SAFETY = "immediate_safety"
    COGNITIVE_ALERTNESS = "cognitive_alertness"
    CABIN_ENVIRONMENT = "cabin_environment"
    BONE_NUTRITION = "bone_nutrition"
    PSYCHOLOGICAL_BEHAVIOR = "psychological_behavior"


class NotificationRecipient(str, Enum):
    """Designated receivers of the alert."""
    ASTRONAUT = "astronaut"
    FLIGHT_SURGEON = "flight_surgeon"
    MISSION_CONTROL = "mission_control"
    FULL_CREW = "crew"


class MatrixRuleAlert(BaseModel):
    """Alert instance generated when a critical matrix crossover activates."""

    model_config = ConfigDict(frozen=True)

    rule_id: str = Field(..., description="Unique identifier of the crossover (e.g. CX-01 to CX-15).")
    domain: RuleDomain = Field(..., description="Thematic category of the risk.")
    level: RuleSeverityLevel = Field(..., description="Operational severity level.")
    preliminary_assessment: str = Field(
        ...,
        description="Preliminary finding describing the identified risk pattern."
    )
    suggested_countermeasures: list[str] = Field(
        ...,
        max_length=3,
        description="Up to 3 immediate actions prioritized by impact to avoid cognitive overload."
    )
    recipients: list[NotificationRecipient] = Field(
        ...,
        description="Who must receive and act on the alert."
    )
    base_standard: str = Field(
        ...,
        description="Scientific evidence or standard (NASA-STD-3001, NOAA, Barger et al.)."
    )
    time_window: str = Field(
        ...,
        description="Persistence window required to confirm the crossover."
    )
    escalation: bool = Field(
        default=False,
        description="Indicates whether the alert escalated in level due to persistence without correction."
    )


class RuleDefinition(BaseModel):
    """Static definition of a crossover rule in the decision catalog."""

    model_config = ConfigDict(frozen=True)

    rule_id: str
    domain: RuleDomain
    level: RuleSeverityLevel
    preliminary_assessment: str
    countermeasures: list[str] = Field(..., max_length=3)
    recipients: list[NotificationRecipient]
    evidence_base: str
    persistence_window: str
    hierarchical_priority: int = Field(
        ...,
        description="1 = Maximum (Immediate safety), 2 = Critical task alertness, 3 = Bone/renal health, 4 = Wellbeing."
    )


# ======================================================================================
# OFFICIAL CATALOG OF MARTINA'S 15 CROSSOVER RULES (NOV 2026)
# ======================================================================================
CRITICAL_RULES_CATALOG: list[RuleDefinition] = [
    # 4.1 Immediate Safety (Priority 1)
    RuleDefinition(
        rule_id="CX-01",
        domain=RuleDomain.IMMEDIATE_SAFETY,
        level=RuleSeverityLevel.CRITICAL,
        preliminary_assessment="Acute radiological exposure in progress (Solar Storm / SPE)",
        countermeasures=[
            "Move immediately to the most shielded area (storm shelter in the spacecraft or habitat).",
            "Postpone the spacewalk (EVA) or Martian surface excursion.",
            "Record personal dosimetric dose every hour until the flux drops below 10 pfu.",
        ],
        recipients=[
            NotificationRecipient.FULL_CREW,
            NotificationRecipient.FLIGHT_SURGEON,
            NotificationRecipient.MISSION_CONTROL,
        ],
        evidence_base="NOAA SWPC; NASA-STD-3001 [V1 4030] SPE",
        persistence_window="Immediate upon detection of protons >= 10 pfu",
        hierarchical_priority=1,
    ),
    RuleDefinition(
        rule_id="CX-02",
        domain=RuleDomain.IMMEDIATE_SAFETY,
        level=RuleSeverityLevel.CRITICAL,
        preliminary_assessment="Pattern consistent with a failure of the cabin atmospheric life support",
        countermeasures=[
            "Immediate atmospheric emergency notice to the full crew and mission control.",
            "Inspect the CO2 removal system and the forced ventilation of the module.",
            "Apply the atmospheric emergency procedure and don masks if applicable.",
        ],
        recipients=[
            NotificationRecipient.FULL_CREW,
            NotificationRecipient.FLIGHT_SURGEON,
            NotificationRecipient.MISSION_CONTROL,
        ],
        evidence_base="NASA-STD-3001 [V2 6004]; SpO2 < 94% + CO2 >= 4 mmHg",
        persistence_window="Sustained 10 minutes in 2 or more crew members",
        hierarchical_priority=1,
    ),

    # 4.2 Alertness and Cognitive Performance (Priority 2)
    RuleDefinition(
        rule_id="CX-03",
        domain=RuleDomain.COGNITIVE_ALERTNESS,
        level=RuleSeverityLevel.ALERT,
        preliminary_assessment="Cognitive incongruence from environmental fatigue",
        countermeasures=[
            "Ask environmental control to reduce CO2 and reinforce ventilation of the sleep station.",
            "Block 8.5 h of strict rest cycle in the daily schedule (NASA standard).",
            "Run a PVT-B test before critical tasks; reschedule if there are lapses outside the baseline.",
        ],
        recipients=[
            NotificationRecipient.ASTRONAUT,
            NotificationRecipient.FLIGHT_SURGEON,
        ],
        evidence_base="Barger et al. (2014); Law et al. (2014); ASTRA Protocol",
        persistence_window="3 nights with sleep < 6h + CO2 > 2.5 mmHg",
        hierarchical_priority=2,
    ),
    RuleDefinition(
        rule_id="CX-04",
        domain=RuleDomain.COGNITIVE_ALERTNESS,
        level=RuleSeverityLevel.CAUTION,
        preliminary_assessment="Unperceived sleep debt (the person feels fine, but their vigilance worsened)",
        countermeasures=[
            "Show the astronaut their objective PVT-B lapse chart to counter misleading self-perception.",
            "Schedule 2 continuous nights of 8.5 h recovery sleep.",
            "Eliminate blue light exposure from screens 60 minutes before sleep.",
        ],
        recipients=[NotificationRecipient.ASTRONAUT],
        evidence_base="Van Dongen et al. (2003); Barger et al. (2014)",
        persistence_window="Debt > 10h over 7 days + PVT-B lapses +50%",
        hierarchical_priority=2,
    ),
    RuleDefinition(
        rule_id="CX-05",
        domain=RuleDomain.COGNITIVE_ALERTNESS,
        level=RuleSeverityLevel.ALERT,
        preliminary_assessment="Risk of residual reduced alertness (prior hypnotic use)",
        countermeasures=[
            "Notify the flight surgeon about the proximity of the critical task.",
            "Propose reassigning or rescheduling the critical task (docking, robotics or EVA).",
            "Implement a cross double-check protocol with another crew member.",
        ],
        recipients=[
            NotificationRecipient.ASTRONAUT,
            NotificationRecipient.FLIGHT_SURGEON,
        ],
        evidence_base="Barger et al. (2014) Lancet Neurology",
        persistence_window="Hypnotic use < 8h prior + critical task scheduled",
        hierarchical_priority=2,
    ),
    RuleDefinition(
        rule_id="CX-06",
        domain=RuleDomain.COGNITIVE_ALERTNESS,
        level=RuleSeverityLevel.ALERT,
        preliminary_assessment="Physiological overload from sustained operational stress",
        countermeasures=[
            "Recommend the mission planner redistribute non-critical tasks for the day.",
            "Establish a mandatory 2 h rest block with no work screens.",
            "20-minute moderate aerobic exercise session for autonomic regulation.",
        ],
        recipients=[
            NotificationRecipient.ASTRONAUT,
            NotificationRecipient.FLIGHT_SURGEON,
        ],
        evidence_base="NASA Behavioral Health & Performance (BHP); HRV -20%",
        persistence_window="Workday > 12h over 3 days + HR +10% + HRV -20%",
        hierarchical_priority=2,
    ),

    # 4.3 Cabin Environment (Priority 2)
    RuleDefinition(
        rule_id="CX-07",
        domain=RuleDomain.CABIN_ENVIRONMENT,
        level=RuleSeverityLevel.ALERT,
        preliminary_assessment="Symptoms consistent with exposure to elevated CO2 concentration",
        countermeasures=[
            "Move to a spacecraft or habitat module with a higher forced ventilation rate.",
            "Notify environmental control to raise the absorption cycle of the CO2 cartridges.",
            "Log a symptomatic self-assessment every 4 hours in the health system.",
        ],
        recipients=[
            NotificationRecipient.ASTRONAUT,
            NotificationRecipient.FLIGHT_SURGEON,
        ],
        evidence_base="NASA-STD-3001 [V2 6004]; Law et al. (2014)",
        persistence_window="CO2 1h >= 3.0 mmHg + headache reported + day > 7",
        hierarchical_priority=2,
    ),
    RuleDefinition(
        rule_id="CX-08",
        domain=RuleDomain.CABIN_ENVIRONMENT,
        level=RuleSeverityLevel.CAUTION,
        preliminary_assessment="Rest quality degraded by ambient thermal stress",
        countermeasures=[
            "Adjust the sleep station thermostat toward the comfortable range (20-22 °C).",
            "Inspect the personal ventilation diffuser in the individual crew quarters.",
            "Adjust the thermal clothing or layers of the space sleeping bag.",
        ],
        recipients=[NotificationRecipient.ASTRONAUT],
        evidence_base="NASA-STD-3001 [V2 6003]; Barger et al. (2014)",
        persistence_window="Temperature/humidity out of range for 2 nights",
        hierarchical_priority=4,
    ),

    # 4.4 Bone, Kidney and Nutrition (Primary Prevention Focus - Priority 3)
    RuleDefinition(
        rule_id="CX-09",
        domain=RuleDomain.BONE_NUTRITION,
        level=RuleSeverityLevel.ALERT,
        preliminary_assessment="Accelerated bone loss risk in a critical mission window",
        countermeasures=[
            "Reschedule squat and deadlift sessions on ARED until the weekly target is met.",
            "Add a supplement or snack with high protein bioavailability.",
            "Notify the flight surgeon if the mechanical loading deficit persists for 7 days.",
        ],
        recipients=[
            NotificationRecipient.ASTRONAUT,
            NotificationRecipient.FLIGHT_SURGEON,
        ],
        evidence_base="npj Microgravity meta-analysis (2020); NASA HSRB; ARED load < 80%",
        persistence_window="Mission day 1-30 + weekly load < 80% + energy < 80%",
        hierarchical_priority=3,
    ),
    RuleDefinition(
        rule_id="CX-10",
        domain=RuleDomain.BONE_NUTRITION,
        level=RuleSeverityLevel.ALERT,
        preliminary_assessment="Risk of mineral saturation and kidney stone formation",
        countermeasures=[
            "Increase fluid intake up to the prescribed target (2.0 to 2.5 L/day).",
            "Reduce sodium consumption in the day's food rations.",
            "Notify the flight surgeon to evaluate medical prophylaxis (citrate is the surgeon's call).",
        ],
        recipients=[
            NotificationRecipient.ASTRONAUT,
            NotificationRecipient.FLIGHT_SURGEON,
        ],
        evidence_base="NASA NTRS Goodenow et al. (2022); Urine < 2 L/day for 3 days",
        persistence_window="Urine volume < 2 L/day for 3 days + intake < 2 L",
        hierarchical_priority=3,
    ),
    RuleDefinition(
        rule_id="CX-11",
        domain=RuleDomain.BONE_NUTRITION,
        level=RuleSeverityLevel.CAUTION,
        preliminary_assessment="Risk of vitamin D deficiency from lack of solar UV radiation",
        countermeasures=[
            "Active reminder to take the prescribed vitamin D dose (800 IU/day).",
            "Confirm and log the supplement intake in the astronaut panel.",
        ],
        recipients=[NotificationRecipient.ASTRONAUT],
        evidence_base="NASA Nutritional Requirements; Smith et al. (2012)",
        persistence_window="Dose < 800 IU/day for 7 consecutive days",
        hierarchical_priority=3,
    ),
    RuleDefinition(
        rule_id="CX-12",
        domain=RuleDomain.BONE_NUTRITION,
        level=RuleSeverityLevel.ALERT,
        preliminary_assessment="Sustained negative energy balance (caloric expenditure above intake)",
        countermeasures=[
            "Adjust the daily menu to the total caloric requirement of the mission.",
            "Prioritize snacks with complex carbohydrates and protein after training.",
            "Request a review teleconsultation with the flight nutrition specialist.",
        ],
        recipients=[
            NotificationRecipient.ASTRONAUT,
            NotificationRecipient.FLIGHT_SURGEON,
        ],
        evidence_base="NASA Human Research Program; Body loss > 2% in 2 weeks",
        persistence_window="Body mass -2% in 2 weeks + energy < 80%",
        hierarchical_priority=3,
    ),
    RuleDefinition(
        rule_id="CX-13",
        domain=RuleDomain.BONE_NUTRITION,
        level=RuleSeverityLevel.CAUTION,
        preliminary_assessment="Osteo-mechanical unloading from forced confinement in the Martian habitat",
        countermeasures=[
            "Increase the resistance load on the habitat exercise equipment to compensate.",
            "Complete a short routine of jumps or controlled impact inside the facility.",
        ],
        recipients=[NotificationRecipient.ASTRONAUT],
        evidence_base="NASA JPL (Global dust storms); EVA activity < 50% over 5 sols",
        persistence_window="5 sols with reduced outdoor activity + load < 80%",
        hierarchical_priority=3,
    ),

    # 4.5 Behavior and Psychological Wellbeing (Priority 4)
    RuleDefinition(
        rule_id="CX-14",
        domain=RuleDomain.PSYCHOLOGICAL_BEHAVIOR,
        level=RuleSeverityLevel.ALERT,
        preliminary_assessment="Pattern consistent with withdrawal from prolonged isolation",
        countermeasures=[
            "Enable a private window for a family link (asynchronous video message on Mars).",
            "Propose a collaborative group activity or biophilia tasks (greenhouse care).",
            "Discreetly notify the mission psychological support team.",
        ],
        recipients=[
            NotificationRecipient.ASTRONAUT,
            NotificationRecipient.FLIGHT_SURGEON,
        ],
        evidence_base="NASA Behavioral Health Protocol; Social contact -50% over 5 days",
        persistence_window="Social contact -50% over 5 days + low mood",
        hierarchical_priority=4,
    ),
    RuleDefinition(
        rule_id="CX-15",
        domain=RuleDomain.PSYCHOLOGICAL_BEHAVIOR,
        level=RuleSeverityLevel.CAUTION,
        preliminary_assessment="Decline in operational motivation with an impact on self-care",
        countermeasures=[
            "Present a positive reinforcement summary on the dashboard with mission milestones met.",
            "Temporarily adjust the day's exercise goal to favor habit adherence.",
            "If the demotivation persists for 7 days, refer to a support session with flight psychology.",
        ],
        recipients=[NotificationRecipient.ASTRONAUT],
        evidence_base="Gao et al. (2022); Exercise adherence < 70% weekly + altered voice",
        persistence_window="Low mood + adherence < 70% weekly",
        hierarchical_priority=4,
    ),
]
