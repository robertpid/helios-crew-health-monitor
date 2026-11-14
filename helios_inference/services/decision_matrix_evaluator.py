"""
Evaluador de la Matriz de Decisiones de Cruces Críticos (Motor de Reglas Clínico-Aeroespaciales).

Aplica la jerarquía de prioridades de la NASA:
    Seguridad Inmediata (Radiación, O2) -> Alertas de Tareas Críticas -> Salud a Mediano Plazo (Hueso, Riñón) -> Bienestar.

Garantiza la regla de diseño:
    Máximo 3 contramedidas priorizadas por alerta para prevenir fatiga y saturación cognitiva.
"""

import logging
from typing import Any

from helios_inference.domain.decision_rules import (
    AlertaReglaMatriz,
    CATALOGO_REGLAS_CRITICAS,
    DominioRegla,
    NivelSeveridadRegla,
    ReglaDefinicion,
)

logger = logging.getLogger(__name__)


class DecisionMatrixEvaluator:
    """
    Motor evaluador de los 15 cruces multivariados críticos.
    Implementa el principio de Responsabilidad Única (SRP) y no prescribe fármacos.
    """

    def __init__(self, catalogo_reglas: list[ReglaDefinicion] | None = None) -> None:
        """Inicializa el evaluador con el catálogo de reglas de referencia."""
        self._catalogo = catalogo_reglas or CATALOGO_REGLAS_CRITICAS
        self._mapa_reglas = {r.id_regla: r for r in self._catalogo}

    def evaluar_telemetria(
        self,
        payload: dict[str, Any],
        historial_dias_consecutivos: dict[str, int] | None = None,
    ) -> list[AlertaReglaMatriz]:
        """
        Evalúa el estado sistémico contra las 15 reglas críticas de cruce.

        Args:
            payload: Diccionario de telemetría consolidado (entorno, biometria, cognicion).
            historial_dias_consecutivos: Diccionario opcional de seguimiento de ventanas de persistencia.

        Returns:
            Lista de alertas activas ordenadas por prioridad jerárquica estricta (1 a 4).
        """
        dia_mision = int(payload.get("dia_mision", 120))
        entorno = payload.get("entorno", {})
        biometria = payload.get("biometria", {})
        cognicion = payload.get("cognicion", {})

        # Variables ambientales
        co2_mmhg = float(entorno.get("co2_mmHg", 1.5))
        radiacion_msv = float(entorno.get("radiacion_acumulada_mSv", 50.0))
        evento_solar = bool(entorno.get("evento_solar_activo", False))
        temperatura_c = float(entorno.get("temperatura_cabina_c", 22.0))
        humedad_pct = float(entorno.get("humedad_relativa_pct", 45.0))

        # Variables biométricas
        ritmo_cardiaco = float(biometria.get("ritmo_cardiaco_bpm", 65.0))
        horas_sueno = float(biometria.get("horas_sueno_ultimo_ciclo", 7.0))
        ciclos_sueno_bajo = int(biometria.get("ciclos_sueno_insuficiente_consecutivos", 0))
        riesgo_fatiga = bool(biometria.get("alerta_riesgo_fatiga", False))
        perdida_osea = float(biometria.get("perdida_osea_pct", 0.0))
        spo2 = float(biometria.get("spo2_pct", 98.0))
        cefalea_reportada = bool(biometria.get("dolor_cabeza_sintoma", False))
        actividad_minutos = float(biometria.get("actividad_fisica_minutos", 120.0))

        # Variables cognitivas (ASTRA)
        latencia_voz = float(cognicion.get("latencia_voz_ms", 200.0))
        densidad_lexica = float(cognicion.get("densidad_lexica_score", 1.0))
        sans_vision = bool(cognicion.get("sans_sintoma_vision", False))

        alertas_disparadas: list[tuple[int, AlertaReglaMatriz]] = []

        # -----------------------------------------------------------------------------
        # 4.1 SEGURIDAD INMEDIATA (Prioridad 1)
        # -----------------------------------------------------------------------------
        # CX-01: Radiación Aguda / Tormenta Solar
        if evento_solar or radiacion_msv > 600.0:
            regla = self._mapa_reglas["CX-01"]
            alertas_disparadas.append((
                regla.prioridad_jerarquica,
                self._crear_alerta(regla, escalada=False)
            ))

        # CX-02: Falla de Soporte Vital Atmosférico
        if spo2 < 94.0 and co2_mmhg >= 3.8:
            regla = self._mapa_reglas["CX-02"]
            alertas_disparadas.append((
                regla.prioridad_jerarquica,
                self._crear_alerta(regla, escalada=True)
            ))

        # -----------------------------------------------------------------------------
        # 4.2 ESTADO DE ALERTA Y COGNICIÓN (Prioridad 2)
        # -----------------------------------------------------------------------------
        # CX-03: Incongruencia cognitiva por fatiga ambiental
        if (horas_sueno < 6.0 or ciclos_sueno_bajo >= 2) and co2_mmhg > 2.5 and latencia_voz >= 300.0:
            regla = self._mapa_reglas["CX-03"]
            alertas_disparadas.append((
                regla.prioridad_jerarquica,
                self._crear_alerta(regla, escalada=ciclos_sueno_bajo >= 3)
            ))

        # CX-04: Deuda de sueño no percibida
        if (riesgo_fatiga or ciclos_sueno_bajo >= 3) and latencia_voz > 450.0 and densidad_lexica >= 0.8:
            regla = self._mapa_reglas["CX-04"]
            alertas_disparadas.append((
                regla.prioridad_jerarquica,
                self._crear_alerta(regla, escalada=True)
            ))

        # CX-06: Sobrecarga fisiológica por estrés operativo
        if ritmo_cardiaco > 90.0 and horas_sueno < 6.0 and actividad_minutos > 110.0:
            regla = self._mapa_reglas["CX-06"]
            alertas_disparadas.append((
                regla.prioridad_jerarquica,
                self._crear_alerta(regla, escalada=False)
            ))

        # -----------------------------------------------------------------------------
        # 4.3 AMBIENTE DE CABINA (Prioridad 2 / 4)
        # -----------------------------------------------------------------------------
        # CX-07: CO2 elevado con síntomas reportados (excluyendo primeros 7 días)
        if co2_mmhg >= 3.0 and dia_mision > 7 and cefalea_reportada:
            regla = self._mapa_reglas["CX-07"]
            alertas_disparadas.append((
                regla.prioridad_jerarquica,
                self._crear_alerta(regla, escalada=False)
            ))

        # CX-08: Estrés térmico ambiental
        if (temperatura_c < 18.0 or temperatura_c > 27.0 or humedad_pct < 25.0 or humedad_pct > 75.0) and horas_sueno < 6.0:
            regla = self._mapa_reglas["CX-08"]
            alertas_disparadas.append((
                regla.prioridad_jerarquica,
                self._crear_alerta(regla, escalada=False)
            ))

        # -----------------------------------------------------------------------------
        # 4.4 HUESO, RIÑÓN Y NUTRICIÓN (Prioridad 3)
        # -----------------------------------------------------------------------------
        # CX-09: Pérdida ósea acelerada en ventana crítica (primeros 30 días o carga baja)
        if (dia_mision <= 30 or perdida_osea > 1.5) and actividad_minutos < 100.0:
            regla = self._mapa_reglas["CX-09"]
            alertas_disparadas.append((
                regla.prioridad_jerarquica,
                self._crear_alerta(regla, escalada=dia_mision > 30)
            ))

        # CX-10: Riesgo de cálculos renales por pérdida ósea y orina
        if perdida_osea > 2.0 and actividad_minutos < 90.0:
            regla = self._mapa_reglas["CX-10"]
            alertas_disparadas.append((
                regla.prioridad_jerarquica,
                self._crear_alerta(regla, escalada=False)
            ))

        # CX-11: Deficiencia de Vitamina D en misiones prolongadas
        if dia_mision > 60 and perdida_osea > 1.0:
            regla = self._mapa_reglas["CX-11"]
            alertas_disparadas.append((
                regla.prioridad_jerarquica,
                self._crear_alerta(regla, escalada=False)
            ))

        # CX-13: Descarga mecánica en Marte
        if "MARS" in payload.get("id_mision", "") and actividad_minutos < 60.0:
            regla = self._mapa_reglas["CX-13"]
            alertas_disparadas.append((
                regla.prioridad_jerarquica,
                self._crear_alerta(regla, escalada=False)
            ))

        # -----------------------------------------------------------------------------
        # 4.5 CONDUCTA Y BIENESTAR PSICOLÓGICO (Prioridad 4)
        # -----------------------------------------------------------------------------
        # CX-14: Retraimiento por aislamiento
        if latencia_voz > 650.0 and horas_sueno < 5.5 and densidad_lexica < 0.6:
            regla = self._mapa_reglas["CX-14"]
            alertas_disparadas.append((
                regla.prioridad_jerarquica,
                self._crear_alerta(regla, escalada=False)
            ))

        # CX-15: Disminución de motivación con impacto en autocuidado
        if latencia_voz > 500.0 and actividad_minutos < 75.0 and densidad_lexica < 0.7:
            regla = self._mapa_reglas["CX-15"]
            alertas_disparadas.append((
                regla.prioridad_jerarquica,
                self._crear_alerta(regla, escalada=False)
            ))

        # Ordenar estrictamente por prioridad jerárquica de la NASA (1: Seguridad Inmediata -> 4: Bienestar)
        alertas_disparadas.sort(key=lambda item: item[0])

        resultado_alertas = [alerta for _, alerta in alertas_disparadas]
        logger.debug("Evaluador de Matriz activó %d cruces críticos.", len(resultado_alertas))
        return resultado_alertas

    def _crear_alerta(self, regla: ReglaDefinicion, escalada: bool = False) -> AlertaReglaMatriz:
        """Crea una instancia inmutable de AlertaReglaMatriz con máximo 3 contramedidas."""
        nivel = regla.nivel
        if escalada and nivel == NivelSeveridadRegla.PRECAUCION:
            nivel = NivelSeveridadRegla.ALERTA
        elif escalada and nivel == NivelSeveridadRegla.ALERTA:
            nivel = NivelSeveridadRegla.CRITICA

        return AlertaReglaMatriz(
            id_regla=regla.id_regla,
            dominio=regla.dominio,
            nivel=nivel,
            evaluacion_preliminar=regla.evaluacion_preliminar,
            contramedidas_sugeridas=regla.contramedidas[:3],  # Garantiza máximo 3 acciones
            destinatarios=regla.destinatarios,
            estandar_base=regla.base_evidencia,
            ventana_tiempo=regla.ventana_persistencia,
            escalada=escalada,
        )
