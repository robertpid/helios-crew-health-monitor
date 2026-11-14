"""
Generador de telemetría de entorno ambiental (Cerebro 1).

Aplica reglas físicas y estocásticas basadas en NASA-STD-3001 Vol. 2 para dióxido de
carbono, presión de cabina y dosimetría de radiación cósmica galáctica y solar.
"""

import logging
from helios_simulator.config import LimitesNasaConfig
from helios_simulator.domain.models import EntornoModel
from helios_simulator.services.math_noise import (
    evaluar_probabilidad_evento,
    generar_ruido_gaussiano,
    redondear_telemetria,
)

logger = logging.getLogger(__name__)


class GeneradorEntorno:
    """
    Servicio responsable de generar la telemetría ambiental de la cabina espacial.
    Mantiene el estado acumulativo de radiación y modela fluctuaciones de gases vitales.
    """

    def __init__(
        self,
        config_limites: LimitesNasaConfig | None = None,
        dia_mision_inicial: int = 120,
    ) -> None:
        """
        Inicializa el generador de entorno.

        Args:
            config_limites: Configuración con rangos y normativas de la NASA.
            dia_mision_inicial: Día de misión de referencia (ej. Día 120).
        """
        self._config = config_limites or LimitesNasaConfig()
        self._dia_mision = dia_mision_inicial

        # Dosis base acumulada al Día 120: base 50.0 mSv + incremento diario (~0.35 mSv/día)
        dosis_por_dia_promedio = (
            self._config.radiacion_tasa_diaria_min_msv + self._config.radiacion_tasa_diaria_max_msv
        ) / 2.0
        self._radiacion_acumulada_msv = (
            self._config.radiacion_base_acumulada_msv
            + (self._dia_mision * dosis_por_dia_promedio)
        )
        self._tormenta_solar_activa = False

    def generar_lectura(
        self,
        forzar_pico_co2: bool = False,
        forzar_tormenta_solar: bool = False,
    ) -> EntornoModel:
        """
        Calcula una nueva muestra de telemetría de entorno.

        Args:
            forzar_pico_co2: Si es True, fuerza un pico de CO2 > 3.0 mmHg para pruebas o demo.
            forzar_tormenta_solar: Si es True, fuerza un evento de Tormenta Solar (+20 mSv).

        Returns:
            Instancia validada de EntornoModel.
        """
        # 1. Dióxido de carbono (co2_mmHg): Normal 1.0 - 2.2 mmHg. Inyectar picos > 3.0 (NASA V2 6004)
        probabilidad_pico_co2 = 0.12
        generar_pico = forzar_pico_co2 or evaluar_probabilidad_evento(probabilidad_pico_co2)

        if generar_pico:
            # Pico superior a 3.0 mmHg (violación NASA-STD-3001 [V2 6004])
            co2_val = generar_ruido_gaussiano(
                valor_medio=3.4,
                desviacion_estandar=0.3,
                limite_inferior=3.05,
                limite_superior=4.5,
            )
            logger.info("Inyectando pico anómalo de CO2 en cabina: %.2f mmHg (NASA V2 6004)", co2_val)
        else:
            # Rango nominal: 1.0 - 2.2 mmHg
            co2_val = generar_ruido_gaussiano(
                valor_medio=1.6,
                desviacion_estandar=0.25,
                limite_inferior=self._config.co2_normal_min_mmhg,
                limite_superior=self._config.co2_normal_max_mmhg,
            )

        # 2. Radiación cósmica y solar
        # Tasa diaria habitual en espacio profundo / ISS: 0.2 a 0.5 mSv/día
        tasa_diaria_val = generar_ruido_gaussiano(
            valor_medio=0.35,
            desviacion_estandar=0.08,
            limite_inferior=self._config.radiacion_tasa_diaria_min_msv,
            limite_superior=self._config.radiacion_tasa_diaria_max_msv,
        )

        # Incremento fraccional por ciclo de telemetría
        incremento_muestra = tasa_diaria_val / (24.0 * 3600.0 / 2.0)
        self._radiacion_acumulada_msv += incremento_muestra

        # 1% de probabilidad de Tormenta Solar (+20 mSv de golpe)
        hubo_tormenta = forzar_tormenta_solar or evaluar_probabilidad_evento(
            self._config.probabilidad_tormenta_solar
        )

        if hubo_tormenta:
            self._radiacion_acumulada_msv += self._config.radiacion_tormenta_solar_impacto_msv
            self._tormenta_solar_activa = True
            logger.warning(
                "¡ALERTA AMBIENTAL! Detectado Evento de Partículas Solares (SPE). Impacto: +%.1f mSv. Acumulado: %.2f mSv",
                self._config.radiacion_tormenta_solar_impacto_msv,
                self._radiacion_acumulada_msv,
            )
        else:
            self._tormenta_solar_activa = False

        # 3. Presión de cabina (presion_cabina_kpa): 95.0 - 103.0 kPa (NASA V2 6006)
        presion_val = generar_ruido_gaussiano(
            valor_medio=101.3,
            desviacion_estandar=1.2,
            limite_inferior=self._config.presion_cabina_min_kpa,
            limite_superior=self._config.presion_cabina_max_kpa,
        )

        # 4. Temperatura de cabina
        temperatura_val = generar_ruido_gaussiano(
            valor_medio=21.5,
            desviacion_estandar=0.6,
            limite_inferior=18.0,
            limite_superior=26.0,
        )

        return EntornoModel(
            co2_mmHg=redondear_telemetria(co2_val, 2),
            radiacion_acumulada_mSv=redondear_telemetria(self._radiacion_acumulada_msv, 2),
            radiacion_tasa_diaria_mSv=redondear_telemetria(tasa_diaria_val, 3),
            presion_cabina_kpa=redondear_telemetria(presion_val, 2),
            temperatura_cabina_c=redondear_telemetria(temperatura_val, 2),
            evento_solar_activo=self._tormenta_solar_activa,
        )
