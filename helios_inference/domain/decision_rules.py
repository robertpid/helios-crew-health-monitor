"""
Modelos y catálogo de las 15 reglas críticas de la Matriz de Decisiones del Cerebro Central.
Basado en NASA-STD-3001, OCHMO-TB-002/003/004, NOAA SWPC, Barger et al. (2014) y Law et al. (2014).

Define la estructura de reglas multivariadas, niveles de severidad y contramedidas (máximo 3).
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, ConfigDict


class NivelSeveridadRegla(str, Enum):
    """Nivel de severidad operacional de la alerta según la matriz de la NASA."""
    PRECAUCION = "PRECAUCION"  # 🟡 Tendencia de riesgo; se corrige con hábitos (mismo día)
    ALERTA = "ALERTA"          # 🟠 Varios factores combinados; riesgo de afectar salud (pocas horas)
    CRITICA = "CRITICA"        # 🔴 Riesgo inmediato para la vida o misión (inmediato)


class DominioRegla(str, Enum):
    """Categoría temática del riesgo aeroespacial."""
    SEGURIDAD_INMEDIATA = "seguridad_inmediata"
    ESTADO_ALERTA_COGNITIVO = "estado_alerta_cognitivo"
    AMBIENTE_CABINA = "ambiente_cabina"
    HUESO_NUTRICION = "hueso_nutricion"
    CONDUCTA_PSICOLOGICA = "conducta_psicologica"


class DestinatarioNotificacion(str, Enum):
    """Receptores designados de la alerta."""
    ASTRONAUTA = "astronauta"
    MEDICO_VUELO = "medico_vuelo"
    CONTROL_MISION = "control_mision"
    TRIPULACION_COMPLETA = "tripulacion"


class AlertaReglaMatriz(BaseModel):
    """Instancia de alerta generada al activarse un cruce crítico de la matriz."""

    model_config = ConfigDict(frozen=True)

    id_regla: str = Field(..., description="Identificador único del cruce (ej. CX-01 a CX-15).")
    dominio: DominioRegla = Field(..., description="Categoría temática del riesgo.")
    nivel: NivelSeveridadRegla = Field(..., description="Nivel de severidad operacional.")
    evaluacion_preliminar: str = Field(
        ...,
        description="Dictamen preliminar que describe el patrón de riesgo identificado."
    )
    contramedidas_sugeridas: list[str] = Field(
        ...,
        max_length=3,
        description="Hasta 3 acciones inmediatas priorizadas por impacto para evitar sobrecarga cognitiva."
    )
    destinatarios: list[DestinatarioNotificacion] = Field(
        ...,
        description="Quién debe recibir y actuar sobre la alerta."
    )
    estandar_base: str = Field(
        ...,
        description="Evidencia o estándar científico (NASA-STD-3001, NOAA, Barger et al.)."
    )
    ventana_tiempo: str = Field(
        ...,
        description="Ventana de persistencia requerida para confirmación del cruce."
    )
    escalada: bool = Field(
        default=False,
        description="Indica si la alerta escaló de nivel por persistencia sin corrección."
    )


class ReglaDefinicion(BaseModel):
    """Definición estática de una regla de cruce en el catálogo de decisión."""

    model_config = ConfigDict(frozen=True)

    id_regla: str
    dominio: DominioRegla
    nivel: NivelSeveridadRegla
    evaluacion_preliminar: str
    contramedidas: list[str] = Field(..., max_length=3)
    destinatarios: list[DestinatarioNotificacion]
    base_evidencia: str
    ventana_persistencia: str
    prioridad_jerarquica: int = Field(
        ...,
        description="1 = Máxima (Seguridad inmediata), 2 = Alerta tareas críticas, 3 = Salud ósea/renal, 4 = Bienestar."
    )


# ======================================================================================
# CATÁLOGO OFICIAL DE LAS 15 REGLAS DE CRUCE DE MARTINA (NOV 2026)
# ======================================================================================
CATALOGO_REGLAS_CRITICAS: list[ReglaDefinicion] = [
    # 4.1 Seguridad Inmediata (Prioridad 1)
    ReglaDefinicion(
        id_regla="CX-01",
        dominio=DominioRegla.SEGURIDAD_INMEDIATA,
        nivel=NivelSeveridadRegla.CRITICA,
        evaluacion_preliminar="Exposición radiológica aguda en curso (Tormenta Solar / SPE)",
        contramedidas=[
            "Trasladarse de inmediato al área más blindada (refugio de tormenta en nave o hábitat).",
            "Posponer caminata espacial (EVA) o salida a la superficie marciana.",
            "Registrar dosis dosimétrica personal cada hora hasta que el flujo baje de 10 pfu.",
        ],
        destinatarios=[
            DestinatarioNotificacion.TRIPULACION_COMPLETA,
            DestinatarioNotificacion.MEDICO_VUELO,
            DestinatarioNotificacion.CONTROL_MISION,
        ],
        base_evidencia="NOAA SWPC; NASA-STD-3001 [V1 4030] SPE",
        ventana_persistencia="Inmediata ante detección de protones >= 10 pfu",
        prioridad_jerarquica=1,
    ),
    ReglaDefinicion(
        id_regla="CX-02",
        dominio=DominioRegla.SEGURIDAD_INMEDIATA,
        nivel=NivelSeveridadRegla.CRITICA,
        evaluacion_preliminar="Patrón compatible con falla del soporte vital atmosférico de cabina",
        contramedidas=[
            "Aviso de emergencia atmosférica inmediata a toda la tripulación y control de misión.",
            "Revisar el sistema de remoción de CO2 y la ventilación forzada del módulo.",
            "Aplicar el procedimiento de emergencia atmosférica y colocación de mascarillas si aplica.",
        ],
        destinatarios=[
            DestinatarioNotificacion.TRIPULACION_COMPLETA,
            DestinatarioNotificacion.MEDICO_VUELO,
            DestinatarioNotificacion.CONTROL_MISION,
        ],
        base_evidencia="NASA-STD-3001 [V2 6004]; SpO2 < 94% + CO2 >= 4 mmHg",
        ventana_persistencia="Sostenida 10 minutos en 2 o más tripulantes",
        prioridad_jerarquica=1,
    ),

    # 4.2 Estado de Alerta y Desempeño Cognitivo (Prioridad 2)
    ReglaDefinicion(
        id_regla="CX-03",
        dominio=DominioRegla.ESTADO_ALERTA_COGNITIVO,
        nivel=NivelSeveridadRegla.ALERTA,
        evaluacion_preliminar="Incongruencia cognitiva por fatiga ambiental",
        contramedidas=[
            "Solicitar al control ambiental reducir CO2 y reforzar ventilación de la estación de sueño.",
            "Bloquear 8.5 h de ciclo de descanso estricto en la agenda diaria (estándar NASA).",
            "Realizar prueba PVT-B antes de tareas críticas; reprogramar si hay lapsos fuera de línea base.",
        ],
        destinatarios=[
            DestinatarioNotificacion.ASTRONAUTA,
            DestinatarioNotificacion.MEDICO_VUELO,
        ],
        base_evidencia="Barger et al. (2014); Law et al. (2014); ASTRA Protocol",
        ventana_persistencia="3 noches con sueño < 6h + CO2 > 2.5 mmHg",
        prioridad_jerarquica=2,
    ),
    ReglaDefinicion(
        id_regla="CX-04",
        dominio=DominioRegla.ESTADO_ALERTA_COGNITIVO,
        nivel=NivelSeveridadRegla.PRECAUCION,
        evaluacion_preliminar="Deuda de sueño no percibida (la persona se siente bien, pero su vigilancia empeoró)",
        contramedidas=[
            "Mostrar al astronauta su gráfica objetiva de lapsos PVT-B para evitar autopercepción engañosa.",
            "Programar 2 noches continuas de sueño de recuperación de 8.5 h.",
            "Eliminar exposición a luz azul de pantallas 60 minutos antes de dormir.",
        ],
        destinatarios=[DestinatarioNotificacion.ASTRONAUTA],
        base_evidencia="Van Dongen et al. (2003); Barger et al. (2014)",
        ventana_persistencia="Deuda > 10h en 7 días + lapsos PVT-B +50%",
        prioridad_jerarquica=2,
    ),
    ReglaDefinicion(
        id_regla="CX-05",
        dominio=DominioRegla.ESTADO_ALERTA_COGNITIVO,
        nivel=NivelSeveridadRegla.ALERTA,
        evaluacion_preliminar="Riesgo de alerta reducida residual (uso previo de hipnótico)",
        contramedidas=[
            "Notificar al médico de vuelo sobre la proximidad de la tarea crítica.",
            "Proponer reasignar o reprogramar la tarea crítica (atraque, robótica o EVA).",
            "Implementar protocolo de doble verificación cruzada por otro tripulante.",
        ],
        destinatarios=[
            DestinatarioNotificacion.ASTRONAUTA,
            DestinatarioNotificacion.MEDICO_VUELO,
        ],
        base_evidencia="Barger et al. (2014) Lancet Neurology",
        ventana_persistencia="Uso de hipnótico < 8h previas + tarea crítica programada",
        prioridad_jerarquica=2,
    ),
    ReglaDefinicion(
        id_regla="CX-06",
        dominio=DominioRegla.ESTADO_ALERTA_COGNITIVO,
        nivel=NivelSeveridadRegla.ALERTA,
        evaluacion_preliminar="Sobrecarga fisiológica por estrés operativo continuado",
        contramedidas=[
            "Recomendar al planificador de misión redistribuir tareas no críticas de la jornada.",
            "Establecer un bloque obligatorio de descanso de 2 h sin pantallas de trabajo.",
            "Sesión de ejercicio aeróbico moderado de 20 minutos para regulación autonómica.",
        ],
        destinatarios=[
            DestinatarioNotificacion.ASTRONAUTA,
            DestinatarioNotificacion.MEDICO_VUELO,
        ],
        base_evidencia="NASA Behavioral Health & Performance (BHP); HRV -20%",
        ventana_persistencia="Jornada > 12h durante 3 días + FC +10% + HRV -20%",
        prioridad_jerarquica=2,
    ),

    # 4.3 Ambiente de Cabina (Prioridad 2)
    ReglaDefinicion(
        id_regla="CX-07",
        dominio=DominioRegla.AMBIENTE_CABINA,
        nivel=NivelSeveridadRegla.ALERTA,
        evaluacion_preliminar="Síntomas compatibles con exposición a concentración elevada de CO2",
        contramedidas=[
            "Trasladarse a un módulo de la nave o hábitat con mayor tasa de ventilación forzada.",
            "Avisar a control ambiental para elevar el ciclo de absorción de cartuchos de CO2.",
            "Registrar autoevaluación sintomática cada 4 horas en el sistema de salud.",
        ],
        destinatarios=[
            DestinatarioNotificacion.ASTRONAUTA,
            DestinatarioNotificacion.MEDICO_VUELO,
        ],
        base_evidencia="NASA-STD-3001 [V2 6004]; Law et al. (2014)",
        ventana_persistencia="CO2 1h >= 3.0 mmHg + cefalea reportada + día > 7",
        prioridad_jerarquica=2,
    ),
    ReglaDefinicion(
        id_regla="CX-08",
        dominio=DominioRegla.AMBIENTE_CABINA,
        nivel=NivelSeveridadRegla.PRECAUCION,
        evaluacion_preliminar="Calidad de descanso alterada por estrés térmico ambiental",
        contramedidas=[
            "Ajustar el termostato de la estación de sueño hacia el rango confortable (20-22 °C).",
            "Revisar el difusor de ventilación personal en el camarote individual.",
            "Ajustar la vestimenta térmica o capas del saco de dormir espacial.",
        ],
        destinatarios=[DestinatarioNotificacion.ASTRONAUTA],
        base_evidencia="NASA-STD-3001 [V2 6003]; Barger et al. (2014)",
        ventana_persistencia="Temperatura/humedad fuera de rango durante 2 noches",
        prioridad_jerarquica=4,
    ),

    # 4.4 Hueso, Riñón y Nutrición (Foco Primario de Prevención - Prioridad 3)
    ReglaDefinicion(
        id_regla="CX-09",
        dominio=DominioRegla.HUESO_NUTRICION,
        nivel=NivelSeveridadRegla.ALERTA,
        evaluacion_preliminar="Riesgo acelerado de pérdida ósea en ventana crítica de misión",
        contramedidas=[
            "Reprogramar sesiones de sentadilla y peso muerto en ARED hasta cubrir meta semanal.",
            "Incorporar un suplemento o snack con alta biodisponibilidad de proteína.",
            "Avisar al médico de vuelo si el déficit de carga mecánica persiste por 7 días.",
        ],
        destinatarios=[
            DestinatarioNotificacion.ASTRONAUTA,
            DestinatarioNotificacion.MEDICO_VUELO,
        ],
        base_evidencia="Metaanálisis npj Microgravity (2020); NASA HSRB; Carga ARED < 80%",
        ventana_persistencia="Día misión 1-30 + carga semanal < 80% + energía < 80%",
        prioridad_jerarquica=3,
    ),
    ReglaDefinicion(
        id_regla="CX-10",
        dominio=DominioRegla.HUESO_NUTRICION,
        nivel=NivelSeveridadRegla.ALERTA,
        evaluacion_preliminar="Riesgo de saturación mineral y formación de cálculos renales",
        contramedidas=[
            "Incrementar la ingesta de líquidos hasta la meta prescrita (2.0 a 2.5 L/día).",
            "Reducir el consumo de sodio en las raciones alimentarias del día.",
            "Avisar al médico de vuelo para evaluar profilaxis médica (el citrato lo decide el médico).",
        ],
        destinatarios=[
            DestinatarioNotificacion.ASTRONAUTA,
            DestinatarioNotificacion.MEDICO_VUELO,
        ],
        base_evidencia="NASA NTRS Goodenow et al. (2022); Orina < 2 L/día durante 3 días",
        ventana_persistencia="Volumen orina < 2 L/día durante 3 días + ingesta < 2 L",
        prioridad_jerarquica=3,
    ),
    ReglaDefinicion(
        id_regla="CX-11",
        dominio=DominioRegla.HUESO_NUTRICION,
        nivel=NivelSeveridadRegla.PRECAUCION,
        evaluacion_preliminar="Riesgo de deficiencia de vitamina D por falta de radiación solar UV",
        contramedidas=[
            "Recordatorio activo de ingesta de la dosis prescrita de vitamina D (800 UI/día).",
            "Confirmar y registrar la toma del suplemento en el panel del astronauta.",
        ],
        destinatarios=[DestinatarioNotificacion.ASTRONAUTA],
        base_evidencia="NASA Nutritional Requirements; Smith et al. (2012)",
        ventana_persistencia="Dosis < 800 UI/día durante 7 días consecutivos",
        prioridad_jerarquica=3,
    ),
    ReglaDefinicion(
        id_regla="CX-12",
        dominio=DominioRegla.HUESO_NUTRICION,
        nivel=NivelSeveridadRegla.ALERTA,
        evaluacion_preliminar="Balance energético negativo sostenido (gasto calórico superior a la ingesta)",
        contramedidas=[
            "Ajustar el menú diario al requerimiento calórico total de la misión.",
            "Priorizar colaciones con carbohidratos complejos y proteína tras el entrenamiento.",
            "Solicitar teleconsulta de revisión con el especialista en nutrición de vuelo.",
        ],
        destinatarios=[
            DestinatarioNotificacion.ASTRONAUTA,
            DestinatarioNotificacion.MEDICO_VUELO,
        ],
        base_evidencia="NASA Human Research Program; Pérdida corporal > 2% en 2 semanas",
        ventana_persistencia="Masa corporal -2% en 2 semanas + energía < 80%",
        prioridad_jerarquica=3,
    ),
    ReglaDefinicion(
        id_regla="CX-13",
        dominio=DominioRegla.HUESO_NUTRICION,
        nivel=NivelSeveridadRegla.PRECAUCION,
        evaluacion_preliminar="Descarga osteo-mecánica por confinamiento forzado en hábitat marciano",
        contramedidas=[
            "Incrementar la carga de resistencia en el equipo de ejercicio del hábitat para compensar.",
            "Completar una rutina corta de saltos o impacto controlado dentro de las instalaciones.",
        ],
        destinatarios=[DestinatarioNotificacion.ASTRONAUTA],
        base_evidencia="NASA JPL (Tormentas globales de polvo); Actividad EVA < 50% en 5 soles",
        ventana_persistencia="5 soles con actividad exterior reducida + carga < 80%",
        prioridad_jerarquica=3,
    ),

    # 4.5 Conducta y Bienestar Psicológico (Prioridad 4)
    ReglaDefinicion(
        id_regla="CX-14",
        dominio=DominioRegla.CONDUCTA_PSICOLOGICA,
        nivel=NivelSeveridadRegla.ALERTA,
        evaluacion_preliminar="Patrón compatible con retraimiento por aislamiento prolongado",
        contramedidas=[
            "Habilitar ventana privada para enlace con familiares (mensaje de video asíncrono en Marte).",
            "Proponer una actividad colaborativa de grupo o tareas de biofilia (cuidado del invernadero).",
            "Notificar discretamente al equipo de soporte psicológico de la misión.",
        ],
        destinatarios=[
            DestinatarioNotificacion.ASTRONAUTA,
            DestinatarioNotificacion.MEDICO_VUELO,
        ],
        base_evidencia="NASA Behavioral Health Protocol; Contacto social -50% durante 5 días",
        ventana_persistencia="Contacto social -50% durante 5 días + ánimo bajo",
        prioridad_jerarquica=4,
    ),
    ReglaDefinicion(
        id_regla="CX-15",
        dominio=DominioRegla.CONDUCTA_PSICOLOGICA,
        nivel=NivelSeveridadRegla.PRECAUCION,
        evaluacion_preliminar="Disminución de motivación operativa con impacto en el autocuidado",
        contramedidas=[
            "Presentar en dashboard un resumen de refuerzo positivo con hitos cumplidos en la misión.",
            "Ajustar temporalmente la meta de ejercicio del día para favorecer la adherencia al hábito.",
            "Si la desmotivación persiste 7 días, derivar a sesión de apoyo con psicología de vuelo.",
        ],
        destinatarios=[DestinatarioNotificacion.ASTRONAUTA],
        base_evidencia="Gao et al. (2022); Adherencia a ejercicio < 70% semanal + voz alterada",
        ventana_persistencia="Ánimo bajo + adherencia < 70% semanal",
        prioridad_jerarquica=4,
    ),
]
