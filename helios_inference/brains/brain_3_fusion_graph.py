"""
Brain 3: H.E.L.I.O.S. Logic Graph and Spatial Fusion (Mathematical Orchestrator).

========================================================================================
MATHEMATICAL AND TOPOLOGICAL FOUNDATION (PURE LINEAR ALGEBRA AT THE EDGE):
========================================================================================
In deep space embedded systems (Edge AI), compute consumption and latency rule out
heavy graph engines (such as Neo4j) or massive neural networks. Instead, this module
formulates the topology of a bipartite decision-making graph using the Kronecker
tensor product from multilinear algebra:

    Let v_env in R^3 be the environmental state vector:
        [0]: Elevated CO2 alert
        [1]: Critical radiation alert
        [2]: Abnormal pressure alert

    Let v_bio in R^4 be the astronaut's physiological state vector:
        [0]: Abnormal pulse (tachycardia / bradycardia)
        [1]: Rest deficit / circadian fatigue
        [2]: Bone density deterioration
        [3]: SANS neuro-ocular congestion symptoms

    The Kronecker tensor product is defined as:
        V_kron = v_env (X) v_bio = [ v_env_0 * v_bio, v_env_1 * v_bio, v_env_2 * v_bio ]^T in R^12

Each of the 12 components of the resulting vector V_kron represents the simultaneous
activation (binary or fuzzy logical conjunction) of an environmental node and a
physiological node:
    - Index 0  (CO2 x Pulse)    : Respiratory acidosis with adrenergic compensation.
    - Index 1  (CO2 x Sleep)    : Awakenings from hypercapnia and nocturnal desaturation.
    - Index 2  (CO2 x Bone)     : Chronic metabolic acidosis favoring bone resorption.
    - Index 3  (CO2 x SANS)     : Intracranial hypertension and acute cerebral venous congestion.
    - Index 4  (Rad x Pulse)    : Myocardial oxidative stress from high-energy particles.
    - Index 5  (Rad x Sleep)    : Circadian disruption induced by background radiation.
    - Index 6  (Rad x Bone)     : Synergistic stromal damage and severe trabecular mass loss.
    - Index 7  (Rad x SANS)     : Microvascular endothelial radiotoxemia in the retina and optic nerve.
    - Index 8  (Pressure x Pulse): Acute baroreflex from cabin hypobaria.
    - Index 9  (Pressure x Sleep): Central apnea and poor rest quality from unstable pressure.
    - Index 10 (Pressure x Bone) : Risk of bone aeroembolism and slow decompression.
    - Index 11 (Pressure x SANS) : Increased translaminar pressure gradient at the lamina cribrosa.

By weighting V_kron with the clinical weight vector W in R^12, the operation:
    P = V_kron (elem-wise) W
    k* = argmax(P)
determines in O(1) time the most hazardous critical edge of the decision graph without
performing iterative searches in memory.
"""

import logging
import numpy as np

from helios_inference.domain.inference_models import KroneckerFusionInferenceState

logger = logging.getLogger(__name__)


class FusionGraphBrain:
    """
    Mathematical sensor fusion orchestrator based on the Kronecker tensor product.
    Transforms the multivariate assessment into a lightweight matrix decision graph.
    """

    # Formal definition of the 12 environment-physiology interaction edges
    GRAPH_EDGE_NAMES: list[str] = [
        "CO2_HYPERCAPNIA_WITH_REFLEX_TACHYCARDIA",         # 0: CO2 x Pulse
        "ELEVATED_CO2_WITH_SLEEP_DEFICIT_AND_FATIGUE",     # 1: CO2 x Sleep
        "CO2_ACIDOSIS_WITH_ACCELERATED_BONE_RESORPTION",   # 2: CO2 x Bone
        "CO2_WITH_SANS_INTRACRANIAL_HYPERTENSION",         # 3: CO2 x SANS (Critical)
        "IONIZING_RADIATION_WITH_CARDIAC_STRESS",          # 4: Rad x Pulse
        "SPACE_RADIATION_WITH_SLEEP_DISRUPTION",           # 5: Rad x Sleep
        "RADIATION_WITH_SEVERE_BONE_DEGENERATION",         # 6: Rad x Bone (Critical)
        "RADIATION_WITH_SANS_OPTIC_MICROVASCULAR_DAMAGE",  # 7: Rad x SANS
        "HYPOBARIA_WITH_ADRENERGIC_RESPONSE",              # 8: Pressure x Pulse (Critical)
        "PRESSURE_FLUCTUATION_WITH_CIRCADIAN_APNEA",       # 9: Pressure x Sleep
        "DYSBARISM_WITH_SKELETAL_PAIN_AND_FATIGUE",        # 10: Pressure x Bone
        "ABNORMAL_CABIN_PRESSURE_AGGRAVATING_SANS",        # 11: Pressure x SANS (Critical)
    ]

    def __init__(self, severe_hazard_threshold: float = 6.5) -> None:
        """
        Initializes the decision graph with the space clinical weight matrix (NASA-STD-3001).

        Args:
            severe_hazard_threshold: Minimum weighted value to raise the severe stress flag.
        """
        self._severe_hazard_threshold = severe_hazard_threshold

        # Calibrated clinical severity weighting for each graph edge (scale 0.0 to 10.0)
        self._clinical_weight_vector = np.array([
            7.5,   # 0: CO2 x Pulse (acidosis with cardiac overload)
            6.0,   # 1: CO2 x Sleep (respiratory fatigue)
            5.0,   # 2: CO2 x Bone (demineralization accelerated by acidosis)
            9.2,   # 3: CO2 x SANS (critical hazard of vision loss and edema)
            8.0,   # 4: Rad x Pulse (solar storm with tachycardia)
            5.5,   # 5: Rad x Sleep
            8.7,   # 6: Rad x Bone (highly destructive osteo-cellular synergy)
            7.8,   # 7: Rad x SANS
            9.5,   # 8: Pressure x Pulse (rapid depressurization / hypoxia)
            6.2,   # 9: Pressure x Sleep
            8.0,   # 10: Pressure x Bone (tissue decompression sickness)
            8.9,   # 11: Pressure x SANS (compromised ocular transmural gradient)
        ], dtype=np.float64)

    def fuse(
        self,
        environmental_vector: np.ndarray,
        biometric_vector: np.ndarray,
    ) -> tuple[np.ndarray, KroneckerFusionInferenceState]:
        """
        Applies the Kronecker tensor product to build the interaction decision graph.

        Args:
            environmental_vector: Vector in R^3 [co2, radiation, pressure].
            biometric_vector: Vector in R^4 [pulse, sleep, bone, sans].

        Returns:
            Tuple containing:
            - np.ndarray: Tensor vector in R^12 with the active hazard weights.
            - KroneckerFusionInferenceState: Descriptive structure of the fusion and preliminary assessment.
        """
        # Strict dimensionality check to guarantee topological integrity
        if environmental_vector.shape != (3,) or biometric_vector.shape != (4,):
            raise ValueError(
                f"Invalid dimensions for the tensor product: "
                f"environmental={environmental_vector.shape} (required (3,)), "
                f"biometric={biometric_vector.shape} (required (4,))"
            )

        # -----------------------------------------------------------------------------
        # KRONECKER TENSOR PRODUCT (np.kron):
        # Simultaneously maps every interaction edge between Environment and Biometrics.
        # -----------------------------------------------------------------------------
        kronecker_interaction_vector = np.kron(environmental_vector, biometric_vector)

        # Matrix weighting of active edges with the aerospace weights
        weighted_hazard_vector = kronecker_interaction_vector * self._clinical_weight_vector

        # Locating the dominant edge through pure vector algebra
        max_index = int(np.argmax(weighted_hazard_vector))
        max_weight = float(weighted_hazard_vector[max_index])

        # Determining the activation of synergistic edges
        synergy_active = bool(max_weight > 0.0)
        severe_stress = bool(max_weight >= self._severe_hazard_threshold)

        if synergy_active:
            dominant_edge = self.GRAPH_EDGE_NAMES[max_index]
            preliminary_assessment = (
                f"Preliminary cross-interaction assessment: Edge '{dominant_edge}' activated "
                f"with severity {max_weight:.1f}/{np.max(self._clinical_weight_vector):.1f}."
            )
            if severe_stress:
                preliminary_assessment += (
                    " ALERT: Hazard level exceeds the safe threshold. "
                    "Severe physiological stress from environment-human coupling is confirmed."
                )
                logger.error("BRAIN 3: %s", preliminary_assessment)
            else:
                logger.info("BRAIN 3: %s", preliminary_assessment)
        else:
            dominant_edge = "NOMINAL_STATE_NO_ADVERSE_SYNERGIES"
            preliminary_assessment = "Preliminary assessment: Cross parameters within the safety envelope."
            logger.debug("BRAIN 3: %s", preliminary_assessment)

        state = KroneckerFusionInferenceState(
            kronecker_vector_dimension=len(kronecker_interaction_vector),
            critical_synergy_edge=dominant_edge,
            argmax_index=max_index,
            max_severity_score=max_weight,
            severe_physiological_stress=severe_stress,
            fusion_preliminary_assessment=preliminary_assessment,
        )

        return weighted_hazard_vector, state
