"""
Servicio de evaluación preliminar y correlación sinérgica de peligros RIDGE.

Analiza las interacciones cruzadas entre Entorno, Biometría y Cognición,
emitiendo alertas normativas que citan directamente los estándares de la NASA.
"""

import logging
from helios_simulator.config import LimitesNasaConfig
from helios_simulator.domain.enums import NivelAlerta, PeligroRidge
from helios_simulator.domain.models import (
    AlertaEvaluacionPreliminar,
    BiometriaModel,
    CognicionModel,
    EntornoModel,
)

logger = logging.getLogger(__name__)


class EvaluadorCorrelacionService:
    """
    Motor de reglas analíticas para la detección temprana de riesgos y
    evaluaciones preliminares en soporte vital de espacio profundo.
    """

    def __init__(self, config_limites: LimitesNasaConfig | None = None) -> None:
        """
        Inicializa el evaluador de correlación.

        Args:
            config_limites: Parámetros normativos aeroespaciales.
        """
        self._config = config_limites or LimitesNasaConfig()

    def evaluar_estado_sistemico(
        self,
        entorno: EntornoModel,
        biometria: BiometriaModel,
        cognicion: CognicionModel,
    ) -> list[AlertaEvaluacionPreliminar]:
        """
        Ejecuta la matriz de evaluación preliminar cruzando los 5 peligros RIDGE.

        Args:
            entorno: Datos de sensores ambientales.
            biometria: Parámetros fisiológicos del tripulante.
            cognicion: Indicadores conductuales y cognitivos.

        Returns:
            Lista de alertas y evaluaciones preliminares activas.
        """
        alertas: list[AlertaEvaluacionPreliminar] = []

        # 1. Evaluación de CO2 (NASA-STD-3001 [V2 6004])
        if entorno.co2_mmHg > self._config.co2_limite_max_nasa_v2_6004_mmhg:
            alertas.append(
                AlertaEvaluacionPreliminar(
                    codigo="ALERTA-CO2-MAX-V2-6004",
                    nivel=NivelAlerta.CRITICA,
                    peligro_ridge=PeligroRidge.E_ENTORNO_CERRADO,
                    estandar_referencia="NASA-STD-3001 Vol.2 [V2 6004]",
                    descripcion=(
                        f"Concentración de CO2 ({entorno.co2_mmHg} mmHg) sobrepasa el límite normativo "
                        f"de 3.0 mmHg. Riesgo inminente de cefalea y letargo operativo."
                    ),
                    cruce_multivariado=False,
                )
            )
        elif entorno.co2_mmHg > self._config.co2_limite_7dias_mmhg:
            alertas.append(
                AlertaEvaluacionPreliminar(
                    codigo="ALERTA-CO2-ELEVADO-TB004",
                    nivel=NivelAlerta.PRECAUCION,
                    peligro_ridge=PeligroRidge.E_ENTORNO_CERRADO,
                    estandar_referencia="NASA OCHMO-TB-004",
                    descripcion=(
                        f"CO2 a {entorno.co2_mmHg} mmHg excede el umbral de seguridad de 7 días (2.5 mmHg). "
                        f"Síntomas reportados en ISS a partir de 2.3 mmHg."
                    ),
                    cruce_multivariado=False,
                )
            )

        # 2. Evaluación de Presión Atmosférica de Cabina (NASA-STD-3001 [V2 6006])
        if (
            entorno.presion_cabina_kpa < self._config.presion_cabina_min_kpa
            or entorno.presion_cabina_kpa > self._config.presion_cabina_max_kpa
        ):
            alertas.append(
                AlertaEvaluacionPreliminar(
                    codigo="ALERTA-PRESION-CABINA-V2-6006",
                    nivel=NivelAlerta.ADVERTENCIA,
                    peligro_ridge=PeligroRidge.E_ENTORNO_CERRADO,
                    estandar_referencia="NASA-STD-3001 Vol.2 [V2 6006]",
                    descripcion=(
                        f"Presión de cabina ({entorno.presion_cabina_kpa} kPa) fuera del intervalo "
                        f"estándar operativo (95.0 - 103.0 kPa)."
                    ),
                    cruce_multivariado=False,
                )
            )

        # 3. Evaluación de Radiación (NASA-STD-3001 [V1 4030])
        if entorno.evento_solar_activo:
            alertas.append(
                AlertaEvaluacionPreliminar(
                    codigo="ALERTA-SPE-EVENTO-SOLAR-V1-4030",
                    nivel=NivelAlerta.CRITICA,
                    peligro_ridge=PeligroRidge.R_RADIACION,
                    estandar_referencia="NASA-STD-3001 Vol.1 [V1 4030]",
                    descripcion=(
                        f"Tormenta solar / SPE detectada. Dosis súbita inyectada (+20 mSv). "
                        f"Límite por evento: <250 mSv. Dosis acumulada actual: {entorno.radiacion_acumulada_mSv} mSv."
                    ),
                    cruce_multivariado=False,
                )
            )

        # 4. Evaluación de Fatiga Circadiana y Sueño (HSRB / The Lancet Neurology 2014)
        if biometria.alerta_riesgo_fatiga:
            alertas.append(
                AlertaEvaluacionPreliminar(
                    codigo="ALERTA-FATIGA-CRONICA-HSRB",
                    nivel=NivelAlerta.ADVERTENCIA,
                    peligro_ridge=PeligroRidge.I_AISLAMIENTO,
                    estandar_referencia="NASA HSRB & The Lancet Neurology (2014)",
                    descripcion=(
                        f"Riesgo de fatiga severa activado: {biometria.ciclos_sueno_insuficiente_consecutivos} "
                        f"ciclos consecutivos con sueño menor a 6.0 horas (último: {biometria.horas_sueno_ultimo_ciclo}h)."
                    ),
                    cruce_multivariado=False,
                )
            )

        # 5. Cruce Multivariado: Latencia Verbal por Sinergia de Factores (CO2 + Sueño)
        if cognicion.latencia_voz_ms >= self._config.latencia_voz_estres_min_ms:
            motivo = []
            if entorno.co2_mmHg > self._config.co2_limite_7dias_mmhg:
                motivo.append(f"CO2 {entorno.co2_mmHg} mmHg")
            if biometria.horas_sueno_ultimo_ciclo < self._config.umbral_horas_sueno_riesgo:
                motivo.append(f"sueño deficitario {biometria.horas_sueno_ultimo_ciclo}h")

            causa_str = " y ".join(motivo) if motivo else "estrés multimodal"
            alertas.append(
                AlertaEvaluacionPreliminar(
                    codigo="ALERTA-CRUCE-LATENCIA-COGNITIVA",
                    nivel=NivelAlerta.ADVERTENCIA,
                    peligro_ridge=PeligroRidge.D_DISTANCIA,
                    estandar_referencia="NASA OCHMO-TB-004 & Protocolo ASTRA",
                    descripcion=(
                        f"Enlentecimiento cognitivo detectado: latencia verbal en {cognicion.latencia_voz_ms} ms "
                        f"(normal: ~200 ms). Disparado por cruce sinérgico de {causa_str}."
                    ),
                    cruce_multivariado=True,
                )
            )

        # 6. Incongruencia Cognitiva: Estrés Oculto
        if cognicion.incongruencia_estres_oculto:
            alertas.append(
                AlertaEvaluacionPreliminar(
                    codigo="ALERTA-INCONGRUENCIA-ESTRES-ASTRA",
                    nivel=NivelAlerta.PRECAUCION,
                    peligro_ridge=PeligroRidge.I_AISLAMIENTO,
                    estandar_referencia="Modelo Psicométrico ASTRA (NASA Edge AI)",
                    descripcion=(
                        f"Disociación psicofisiológica: ritmo cardiaco elevado ({biometria.ritmo_cardiaco_bpm} bpm) "
                        f"con densidad léxica sostenida ({cognicion.densidad_lexica_score}), indicando ocultamiento voluntario de estrés."
                    ),
                    cruce_multivariado=True,
                )
            )

        # 7. SANS: Síndrome Neuro-ocular (NASA LSAH)
        if cognicion.sans_sintoma_vision:
            alertas.append(
                AlertaEvaluacionPreliminar(
                    codigo="ALERTA-SANS-SINTOMA-VISION",
                    nivel=NivelAlerta.ADVERTENCIA,
                    peligro_ridge=PeligroRidge.G_GRAVEDAD,
                    estandar_referencia="NASA Lifetime Surveillance of Astronaut Health (LSAH 2026)",
                    descripcion=(
                        "Sintomatología neuro-ocular de SANS reportada (visión borrosa / cefalea). "
                        "Correlacionada con desplazamiento cefálico de fluidos (1000-1500 ml) y estrés sistémico."
                    ),
                    cruce_multivariado=True,
                )
            )

        return alertas
