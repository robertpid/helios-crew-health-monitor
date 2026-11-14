"""
Cerebro 3: Grafo Lógico y Fusión Espacial de H.E.L.I.O.S. (Orquestador Matemático).

========================================================================================
FUNDAMENTACIÓN MATEMÁTICA Y TOPOLÓGICA (ÁLGEBRA LINEAL PURA EN EL BORDE):
========================================================================================
En sistemas embebidos de espacio profundo (Edge AI), el consumo computacional y la latencia
impiden el uso de motores pesados de grafos (como Neo4j) o redes neuronales masivas.
En su lugar, este módulo formula la topología de un grafo bipartito de toma de decisiones
utilizando el Producto Tensorial de Kronecker de álgebra multilineal:

    Sea v_amb in R^3 el vector de estado ambiental:
        [0]: Alerta de CO2 elevado
        [1]: Alerta de Radiación crítica
        [2]: Alerta de Presión anómala

    Sea v_bio in R^4 el vector de estado fisiológico del astronauta:
        [0]: Pulso anómalo (taquicardia / bradicardia)
        [1]: Déficit de descanso / fatiga circadiana
        [2]: Deterioro de densidad ósea
        [3]: Síntomas de congestión neuro-ocular SANS

    El Producto Tensorial de Kronecker se define como:
        V_kron = v_amb (X) v_bio = [ v_amb_0 * v_bio, v_amb_1 * v_bio, v_amb_2 * v_bio ]^T in R^12

Cada una de las 12 componentes del vector resultante V_kron representa la activación
simultánea (conjunción lógica binaria o difusa) de un nodo ambiental y un nodo fisiológico:
    - Índice 0  (CO2 x Pulso)     : Acidosis respiratoria con compensación adrenérgica.
    - Índice 1  (CO2 x Sueño)     : Despertares por hipercapnia y desaturación nocturna.
    - Índice 2  (CO2 x Hueso)     : Acidosis metabólica crónica favoreciendo resorción ósea.
    - Índice 3  (CO2 x SANS)      : Hipertensión intracraneal y congestión venosa cerebral aguda.
    - Índice 4  (Rad x Pulso)     : Estrés oxidativo miocárdico por partículas de alta energía.
    - Índice 5  (Rad x Sueño)     : Disrupción circadiana inducida por radiación de fondo.
    - Índice 6  (Rad x Hueso)     : Daño sinérgico estromal y pérdida severa de masa trabecular.
    - Índice 7  (Rad x SANS)      : Radiotoxemia endotelial microvascular en retina y nervio óptico.
    - Índice 8  (Presión x Pulso) : Barorreflejo agudo por hipobaria en cabina.
    - Índice 9  (Presión x Sueño) : Apnea central y mala calidad de descanso por presión inestable.
    - Índice 10 (Presión x Hueso) : Riesgo de aeroembolismo óseo y descompresión lenta.
    - Índice 11 (Presión x SANS)  : Aumento del gradiente translaminar de presión en la lámina cribosa.

Al ponderar V_kron mediante el vector de pesos clínicos W in R^12, la operación:
    P = V_kron (elem-wise) W
    k* = argmax(P)
determina en tiempo O(1) la arista crítica de mayor peligro en el grafo de decisiones sin
realizar búsquedas iterativas en memoria.
"""

import logging
import numpy as np

from helios_inference.domain.inference_models import EstadoFusionKroneckerInferencia

logger = logging.getLogger(__name__)


class CerebroGrafoFusion:
    """
    Orquestador matemático de fusión sensorial basado en producto tensorial de Kronecker.
    Transforma la evaluación multivariada en un grafo matricial ligero de decisión.
    """

    # Definición formal de las 12 aristas de interacción ambiente-fisiología
    NOMBRES_ARISTAS_GRAFO: list[str] = [
        "CO2_HIPERCAPNIA_CON_TAQUICARDIA_REFLEJA",          # 0: CO2 x Pulso
        "CO2_ELEVADO_CON_DEFICIT_SUENO_Y_FATIGA",           # 1: CO2 x Sueño
        "CO2_ACIDOSIS_CON_RESORCION_OSEA_ACELERADA",        # 2: CO2 x Hueso
        "CO2_CON_HIPERTENSION_INTRACRANEAL_SANS",           # 3: CO2 x SANS (Crítico)
        "RADIACION_IONIZANTE_CON_ESTRES_CARDIACO",          # 4: Rad x Pulso
        "RADIACION_ESPACIAL_CON_DISRUPCION_DEL_SUENO",      # 5: Rad x Sueño
        "RADIACION_CON_DEGENERACION_OSEA_SEVERA",           # 6: Rad x Hueso (Crítico)
        "RADIACION_CON_DANIO_MICROVASCULAR_OPTICO_SANS",    # 7: Rad x SANS
        "HIPOBARIA_CON_RESPUESTA_ADRENERGICA",              # 8: Presión x Pulso (Crítico)
        "FLUCTUACION_PRESION_CON_APNEA_CIRCADIANAS",        # 9: Presión x Sueño
        "DISBARISMO_CON_DOLOR_Y_FATIGA_ESQUELETICA",        # 10: Presión x Hueso
        "PRESION_CABINA_ANOMALA_AGRAVANDO_SANS",            # 11: Presión x SANS (Crítico)
    ]

    def __init__(self, umbral_peligro_severo: float = 6.5) -> None:
        """
        Inicializa el grafo de decisiones con la matriz de pesos clínicos espaciales (NASA-STD-3001).

        Args:
            umbral_peligro_severo: Valor mínimo ponderado para disparar la bandera de estrés severo.
        """
        self._umbral_peligro_severo = umbral_peligro_severo

        # Ponderación calibrada de severidad clínica para cada arista del grafo (escala 0.0 a 10.0)
        self._vector_pesos_clinicos = np.array([
            7.5,   # 0: CO2 x Pulso (acidosis con sobrecarga cardiaca)
            6.0,   # 1: CO2 x Sueño (fatiga respiratoria)
            5.0,   # 2: CO2 x Hueso (desmineralización acelerada por acidosis)
            9.2,   # 3: CO2 x SANS (peligro crítico de pérdida visual y edema)
            8.0,   # 4: Rad x Pulso (tormenta solar con taquicardia)
            5.5,   # 5: Rad x Sueño
            8.7,   # 6: Rad x Hueso (sinergia altamente destructiva osteo-celular)
            7.8,   # 7: Rad x SANS
            9.5,   # 8: Presión x Pulso (despresurización rápida / hipoxia)
            6.2,   # 9: Presión x Sueño
            8.0,   # 10: Presión x Hueso (enfermedad por descompresión tisular)
            8.9,   # 11: Presión x SANS (gradiente transmural ocular comprometido)
        ], dtype=np.float64)

    def fusionar(
        self,
        vector_ambiental: np.ndarray,
        vector_biometrico: np.ndarray,
    ) -> tuple[np.ndarray, EstadoFusionKroneckerInferencia]:
        """
        Aplica el producto tensorial de Kronecker para construir el grafo de decisiones de interacción.

        Args:
            vector_ambiental: Vector en R^3 [co2, radiacion, presion].
            vector_biometrico: Vector en R^4 [pulso, sueno, hueso, sans].

        Returns:
            Tupla conteniendo:
            - np.ndarray: Vector tensorial en R^12 con los pesos activos de peligro.
            - EstadoFusionKroneckerInferencia: Estructura descriptiva de la fusión y evaluación preliminar.
        """
        # Verificación estricta de dimensionalidad para garantizar la integridad topológica
        if vector_ambiental.shape != (3,) or vector_biometrico.shape != (4,):
            raise ValueError(
                f"Dimensiones inválidas para producto tensorial: "
                f"ambiental={vector_ambiental.shape} (requerido (3,)), "
                f"biométrico={vector_biometrico.shape} (requerido (4,))"
            )

        # -----------------------------------------------------------------------------
        # PRODUCTO TENSORIAL DE KRONECKER (np.kron):
        # Mapea simultáneamente todas las aristas de interacción entre Ambiente y Biometría.
        # -----------------------------------------------------------------------------
        vector_interaccion_kronecker = np.kron(vector_ambiental, vector_biometrico)

        # Ponderación matricial de aristas activas con los pesos aeroespaciales
        vector_peligro_ponderado = vector_interaccion_kronecker * self._vector_pesos_clinicos

        # Localización de la arista dominante mediante álgebra vectorial pura
        indice_max = int(np.argmax(vector_peligro_ponderado))
        peso_maximo = float(vector_peligro_ponderado[indice_max])

        # Determinación de activación de aristas sinérgicas
        hay_sinergia_activa = bool(peso_maximo > 0.0)
        estres_severo = bool(peso_maximo >= self._umbral_peligro_severo)

        if hay_sinergia_activa:
            arista_dominante = self.NOMBRES_ARISTAS_GRAFO[indice_max]
            evaluacion_preliminar = (
                f"Evaluación preliminar de interacción cruzada: Arista '{arista_dominante}' activada "
                f"con severidad {peso_maximo:.1f}/{np.max(self._vector_pesos_clinicos):.1f}."
            )
            if estres_severo:
                evaluacion_preliminar += (
                    " ALERTA: Nivel de peligro supera el umbral seguro. "
                    "Se confirma estrés fisiológico severo por acoplamiento ambiente-humano."
                )
                logger.error("CEREBRO 3: %s", evaluacion_preliminar)
            else:
                logger.info("CEREBRO 3: %s", evaluacion_preliminar)
        else:
            arista_dominante = "ESTADO_NOMINAL_SIN_SINERGIAS_ADVERSAS"
            evaluacion_preliminar = "Evaluación preliminar: Parámetros cruzados dentro de la envolvente de seguridad."
            logger.debug("CEREBRO 3: %s", evaluacion_preliminar)

        estado = EstadoFusionKroneckerInferencia(
            vector_kronecker_dimension=len(vector_interaccion_kronecker),
            arista_sinergica_critica=arista_dominante,
            indice_argmax=indice_max,
            puntaje_severidad_maximo=peso_maximo,
            estres_fisiologico_severo=estres_severo,
            evaluacion_preliminar_fusion=evaluacion_preliminar,
        )

        return vector_peligro_ponderado, estado
