"""
Libro de códigos de telemetría de H.E.L.I.O.S. (fuente única de verdad textual).

Fundamento
----------
Un sistema de inferencia en el borde debe REDUCIR el caudal hacia tierra, no
amplificarlo. El reporte consolidado repite en cada ciclo las mismas cadenas
descriptivas (dictámenes, contramedidas, estándares base), que son invariantes
del catálogo: no son datos de la misión, son plantillas.

Este módulo extrae esas invariantes a un libro de códigos que se descarga UNA
sola vez. El flujo persistido transporta únicamente:

    - códigos estables  (CO2_ELEV, CX-03, KR03, ...)
    - valores numéricos (3.40, 5.8, 9.2, ...)

y el HUD reconstruye el texto localmente. El catálogo de reglas y los nombres de
las aristas se IMPORTAN de sus módulos de origen, de modo que el libro de
códigos no puede desincronizarse de la lógica de inferencia.

Las plantillas usan marcadores `{0}`, `{1}`... posicionales sobre los valores
numéricos que acompañan a cada código.
"""

from typing import Any, Final

from helios_inference.cerebros.cerebro_3_grafo_fusion import CerebroGrafoFusion
from helios_inference.domain.decision_rules import CATALOGO_REGLAS_CRITICAS

VERSION_ESQUEMA: Final[int] = 1

# ======================================================================================
# ORDEN CANÓNICO DEL VECTOR DE MÉTRICAS
# El registro compacto transporta un array posicional sin claves; este orden es el
# contrato entre el compactador y el HUD.
# ======================================================================================
ORDEN_METRICAS: Final[tuple[str, ...]] = (
    "co2_mmHg",
    "radiacion_acumulada_mSv",
    "presion_cabina_kpa",
    "ritmo_cardiaco_bpm",
    "horas_sueno_ultimo_ciclo",
    "perdida_osea_pct",
    "latencia_voz_ms",
    "densidad_lexica_score",
)

# Índices dentro de ORDEN_METRICAS, para que las plantillas referencien posiciones.
IDX_CO2: Final[int] = 0
IDX_RAD: Final[int] = 1
IDX_PRES: Final[int] = 2
IDX_PULSO: Final[int] = 3
IDX_SUENO: Final[int] = 4
IDX_OSEA: Final[int] = 5

# ======================================================================================
# CÓDIGOS DEL CEREBRO 1 (AMBIENTAL) — orden del vector en R^3
# ======================================================================================
CODIGOS_AMBIENTAL: Final[tuple[dict[str, Any], ...]] = (
    {
        "codigo": "CO2_ELEV",
        "metrica": IDX_CO2,
        "plantilla": "ALERTA_CO2_ELEVADO: {0:.2f} mmHg (Límite: 3.0 mmHg)",
        "estandar": "NASA-STD-3001 [V2 6004]",
    },
    {
        "codigo": "RAD_CRIT",
        "metrica": IDX_RAD,
        "plantilla": "ALERTA_RADIACION_CRITICA: Dosis carrera {0:.1f} mSv",
        "plantilla_evento": "ALERTA_RADIACION_CRITICA: Tormenta Solar Activa (SPE)",
        "estandar": "NASA-STD-3001 [V1 4030]; NOAA SWPC",
    },
    {
        "codigo": "PRES_ANOM",
        "metrica": IDX_PRES,
        "plantilla": "ALERTA_PRESION_CABINA_ANOMALA: {0:.2f} kPa",
        "estandar": "NASA-STD-3001 (rango 95-103 kPa)",
    },
)

# ======================================================================================
# CÓDIGOS DEL CEREBRO 2 (BIOMÉTRICO) — orden del vector en R^4
# ======================================================================================
CODIGOS_BIOMETRICO: Final[tuple[dict[str, Any], ...]] = (
    {
        "codigo": "PULSO_ANOM",
        "metrica": IDX_PULSO,
        "plantilla": "ALERTA_PULSO_ANOMALO: {0:.1f} bpm",
    },
    {
        "codigo": "SUENO_DEF",
        "metrica": IDX_SUENO,
        "plantilla": "ALERTA_DEFICIT_SUENO: {0:.1f} horas",
    },
    {
        "codigo": "OSEO_RIESGO",
        "metrica": IDX_OSEA,
        "plantilla": "ALERTA_RIESGO_OSEO: Día {dia} ({0:.2f}% de pérdida)",
    },
    {
        "codigo": "SANS_ACT",
        "metrica": None,
        "plantilla": "ALERTA_SANS_ACTIVA: Alteración neuro-ocular",
    },
)

# ======================================================================================
# CÓDIGOS DEL CEREBRO 3 (ARISTAS DE KRONECKER) — KR00..KR11
# Los nombres se importan del cerebro para impedir la divergencia.
# ======================================================================================
PLANTILLA_FUSION: Final[str] = (
    "Evaluación preliminar de interacción cruzada: Arista '{arista}' activada "
    "con severidad {severidad:.1f}/9.5."
)
PLANTILLA_FUSION_SEVERA: Final[str] = (
    " ALERTA: Nivel de peligro supera el umbral seguro. "
    "Se confirma estrés fisiológico severo por acoplamiento ambiente-humano."
)
CODIGO_FUSION_NOMINAL: Final[str] = "KR_NOM"
TEXTO_FUSION_NOMINAL: Final[str] = (
    "Evaluación preliminar: Parámetros cruzados dentro de la envolvente de seguridad."
)

# ======================================================================================
# CÓDIGO DEL CEREBRO 4 (ASTRA)
# ======================================================================================
CODIGO_ASTRA_INCONGRUENCIA: Final[str] = "ASTRA_INC"
TEXTO_ASTRA_INCONGRUENCIA: Final[str] = (
    "Incongruencia Cognitiva Detectada. Evaluación preliminar: Posible ocultamiento de fatiga."
)

# ======================================================================================
# METADATOS DE EJECUCIÓN (constantes: viajaban íntegros en cada ciclo)
# ======================================================================================
METADATOS_EDGE_ESTATICOS: Final[dict[str, str]] = {
    "motor": "H.E.L.I.O.S. Pure-NumPy Inference Engine",
    "algebra_lineal": "np.kron + np.dot + np.argmax",
    "hardware_target": "Deep Space Radiation-Tolerant Single Board Computer",
}


def construir_codebook() -> dict[str, Any]:
    """
    Ensambla el libro de códigos completo que el HUD descarga una única vez.

    Returns:
        Diccionario serializable con todas las plantillas, el catálogo de reglas
        y el orden canónico de métricas.
    """
    return {
        "version_esquema": VERSION_ESQUEMA,
        "orden_metricas": list(ORDEN_METRICAS),
        "ambiental": [dict(c) for c in CODIGOS_AMBIENTAL],
        "biometrico": [dict(c) for c in CODIGOS_BIOMETRICO],
        "aristas_kronecker": [
            {"codigo": f"KR{i:02d}", "nombre": nombre}
            for i, nombre in enumerate(CerebroGrafoFusion.NOMBRES_ARISTAS_GRAFO)
        ],
        "plantilla_fusion": PLANTILLA_FUSION,
        "plantilla_fusion_severa": PLANTILLA_FUSION_SEVERA,
        "fusion_nominal": {"codigo": CODIGO_FUSION_NOMINAL, "texto": TEXTO_FUSION_NOMINAL},
        "astra": {"codigo": CODIGO_ASTRA_INCONGRUENCIA, "texto": TEXTO_ASTRA_INCONGRUENCIA},
        "metadatos_edge": dict(METADATOS_EDGE_ESTATICOS),
        "reglas": [
            {
                "codigo": r.id_regla,
                "dominio": r.dominio.value,
                "nivel": r.nivel.value,
                "evaluacion_preliminar": r.evaluacion_preliminar,
                "contramedidas": list(r.contramedidas),
                "destinatarios": [d.value for d in r.destinatarios],
                "estandar_base": r.base_evidencia,
                "ventana_tiempo": r.ventana_persistencia,
                "prioridad": r.prioridad_jerarquica,
            }
            for r in CATALOGO_REGLAS_CRITICAS
        ],
    }
