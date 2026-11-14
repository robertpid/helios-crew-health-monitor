"""
Generador de telemetría de biometría fisiológica (Cerebro 2).

Modela la respuesta hemodinámica, ciclos de sueño circadiano y pérdida de masa ósea
por descondicionamiento musculoesquelético según los estudios de la NASA.
"""

import logging
from helios_simulator.config import LimitesNasaConfig
from helios_simulator.domain.models import BiometriaModel
from helios_simulator.services.math_noise import (
    calcular_perdida_osea_acumulada,
    evaluar_probabilidad_evento,
    generar_ruido_gaussiano,
    redondear_telemetria,
)

logger = logging.getLogger(__name__)


class GeneradorBiometria:
    """
    Servicio de modelado fisiológico del astronauta.
    Mantiene el seguimiento de ciclos circadianos continuos y desmineralización ósea.
    """

    def __init__(
        self,
        config_limites: LimitesNasaConfig | None = None,
        dia_mision_inicial: int = 120,
    ) -> None:
        """
        Inicializa el generador biomédico.

        Args:
            config_limites: Parámetros normativos y umbrales biológicos.
            dia_mision_inicial: Día actual de la expedición en espacio profundo.
        """
        self._config = config_limites or LimitesNasaConfig()
        self._dia_mision = dia_mision_inicial
        self._ciclos_insuficientes = 0
        self._horas_sueno_actual = 6.0
        self._contador_muestras_ciclo = 0

    def simular_nuevo_ciclo_sueno(self, horas_dormidas: float) -> None:
        """
        Registra la conclusión de un ciclo circadiano de sueño para actualizar fatiga.

        Args:
            horas_dormidas: Duración registrada en el actígrafo inteligente.
        """
        self._horas_sueno_actual = horas_dormidas
        if horas_dormidas < self._config.umbral_horas_sueno_riesgo:
            self._ciclos_insuficientes += 1
            logger.warning(
                "Ciclo de descanso insuficiente detectado (%.1fh < %.1fh). Ciclos acumulados: %d",
                horas_dormidas,
                self._config.umbral_horas_sueno_riesgo,
                self._ciclos_insuficientes,
            )
        else:
            self._ciclos_insuficientes = max(0, self._ciclos_insuficientes - 1)

    def generar_lectura(
        self,
        estres_ambiental: bool = False,
        forzar_deficiencia_sueno: bool = False,
        forzar_taquicardia: bool = False,
    ) -> BiometriaModel:
        """
        Produce una lectura instantánea de signos vitales.

        Args:
            estres_ambiental: Indica condiciones ambientales hostiles (CO2 alto o Tormenta Solar).
            forzar_deficiencia_sueno: Fuerza acumulación de sueño < 6.0h.
            forzar_taquicardia: Fuerza ritmo cardiaco elevado (> 95 bpm).

        Returns:
            Instancia validada de BiometriaModel.
        """
        self._contador_muestras_ciclo += 1

        # Simulación de alternancia o persistencia de ciclos de sueño (ej. cada 15 muestras avanza ciclo o fluctúa)
        if self._contador_muestras_ciclo % 15 == 0 or forzar_deficiencia_sueno:
            if forzar_deficiencia_sueno:
                horas_simuladas = generar_ruido_gaussiano(5.2, 0.4, 4.0, 5.8)
            else:
                # Estudio The Lancet Neurology (2014): promedio ~6h por noche
                horas_simuladas = generar_ruido_gaussiano(
                    valor_medio=self._config.horas_sueno_promedio,
                    desviacion_estandar=0.9,
                    limite_inferior=4.2,
                    limite_superior=8.0,
                )
            self.simular_nuevo_ciclo_sueno(horas_simuladas)

        # 1. Ritmo cardiaco (ritmo_cardiaco_bpm): Base 65 +/- 5 bpm
        media_ritmo = self._config.ritmo_cardiaco_base_bpm
        if estres_ambiental:
            media_ritmo += 18.0
        if forzar_taquicardia:
            media_ritmo = 98.0

        ritmo_val = generar_ruido_gaussiano(
            valor_medio=media_ritmo,
            desviacion_estandar=self._config.ritmo_cardiaco_desviacion_bpm,
            limite_inferior=50.0,
            limite_superior=130.0,
        )

        # 2. Bandera de alerta por riesgo de fatiga (si cae a <6h durante 3 ciclos)
        alerta_fatiga = self._ciclos_insuficientes >= self._config.consecutivos_sueno_para_alerta

        # 3. Pérdida ósea acumulada (perdida_osea_pct): (dia_mision / 30) * 1.5%
        perdida_osea = calcular_perdida_osea_acumulada(
            dia_mision=self._dia_mision,
            tasa_mensual_pct=self._config.tasa_perdida_osea_mensual_pct,
        )

        # 4. Parámetros hemodinámicos complementarios (Presión arterial y SpO2)
        base_sistolica = 120.0 + (12.0 if estres_ambiental or ritmo_val > 90 else 0.0)
        sistolica = generar_ruido_gaussiano(base_sistolica, 4.0, 100.0, 160.0)
        diastolica = generar_ruido_gaussiano(sistolica * 0.65, 3.0, 60.0, 95.0)

        spo2 = generar_ruido_gaussiano(98.2, 0.6, 94.0, 100.0)

        return BiometriaModel(
            ritmo_cardiaco_bpm=redondear_telemetria(ritmo_val, 1),
            horas_sueno_ultimo_ciclo=redondear_telemetria(self._horas_sueno_actual, 2),
            ciclos_sueno_insuficiente_consecutivos=self._ciclos_insuficientes,
            alerta_riesgo_fatiga=alerta_fatiga,
            perdida_osea_pct=redondear_telemetria(perdida_osea, 2),
            presion_sistolica_mmHg=redondear_telemetria(sistolica, 1),
            presion_diastolica_mmHg=redondear_telemetria(diastolica, 1),
            spo2_pct=redondear_telemetria(spo2, 1),
        )
