"""
Suite de pruebas unitarias y de integración para helios_simulator.

Valida cumplimiento de NASA-STD-3001, marco RIDGE, modelos Pydantic,
lógica de cruce multivariado, tolerancia a fallos en Redis y principios SOLID.
"""

import json
from unittest.mock import MagicMock, patch
import pytest

from helios_simulator.config import LimitesNasaConfig, MisionConfig, RedisConfig
from helios_simulator.domain.enums import EstadoConexion, NivelAlerta, PeligroRidge
from helios_simulator.domain.models import (
    AlertaEvaluacionPreliminar,
    BiometriaModel,
    CognicionModel,
    EntornoModel,
    TelemetriaPayload,
)
from helios_simulator.infrastructure.publisher_interface import TelemetryPublisherInterface
from helios_simulator.infrastructure.redis_publisher import RedisTelemetryPublisher
from helios_simulator.presentation.orchestrator import TelemetriaOrchestrator
from helios_simulator.services.biometrics_generator import GeneradorBiometria
from helios_simulator.services.cognition_generator import GeneradorCognicion
from helios_simulator.services.correlation_evaluator import EvaluadorCorrelacionService
from helios_simulator.services.environment_generator import GeneradorEntorno
from helios_simulator.services.math_noise import (
    calcular_perdida_osea_acumulada,
    evaluar_probabilidad_evento,
    generar_ruido_gaussiano,
    redondear_telemetria,
)


class MockTelemetryPublisher(TelemetryPublisherInterface):
    """Implementación de prueba para verificar Inversión de Dependencias (DIP)."""

    def __init__(self) -> None:
        self.conectado = False
        self.payloads_recibidos: list[TelemetriaPayload] = []

    def conectar(self) -> bool:
        self.conectado = True
        return True

    def publicar_telemetria(self, payload: TelemetriaPayload) -> bool:
        self.payloads_recibidos.append(payload)
        return True

    def cerrar(self) -> None:
        self.conectado = False

    def obtener_estado_conexion(self) -> EstadoConexion:
        return EstadoConexion.CONECTADO if self.conectado else EstadoConexion.DESCONECTADO


def test_calcular_perdida_osea_dia_120() -> None:
    """Valida la fórmula de pérdida ósea mensual de HSRB: (dia / 30) * 1.5%."""
    # Para el Día 120: (120 / 30) * 1.5 = 4 * 1.5 = 6.0%
    perdida_dia_120 = calcular_perdida_osea_acumulada(120, tasa_mensual_pct=1.5)
    assert perdida_dia_120 == 6.0

    # Para el Día 60: (60 / 30) * 1.5 = 3.0%
    perdida_dia_60 = calcular_perdida_osea_acumulada(60, tasa_mensual_pct=1.5)
    assert perdida_dia_60 == 3.0

    # Día 0
    assert calcular_perdida_osea_acumulada(0) == 0.0


def test_ruido_gaussiano_y_acotamiento() -> None:
    """Verifica que el ruido respete las cotas superior e inferior."""
    for _ in range(50):
        val = generar_ruido_gaussiano(valor_medio=100.0, desviacion_estandar=10.0, limite_inferior=90.0, limite_superior=110.0)
        assert 90.0 <= val <= 110.0


def test_generador_entorno_pico_co2_nasa_v2_6004() -> None:
    """Verifica la generación nominal y la inyección de picos de CO2 > 3.0 mmHg."""
    generador = GeneradorEntorno(dia_mision_inicial=120)

    # Forzar pico de CO2
    lectura_pico = generador.generar_lectura(forzar_pico_co2=True)
    assert lectura_pico.co2_mmHg > 3.0
    assert 95.0 <= lectura_pico.presion_cabina_kpa <= 103.0

    # Lectura nominal
    with patch("helios_simulator.services.environment_generator.evaluar_probabilidad_evento", return_value=False):
        lectura_nominal = generador.generar_lectura(forzar_pico_co2=False)
        assert 1.0 <= lectura_nominal.co2_mmHg <= 2.2


def test_generador_entorno_tormenta_solar() -> None:
    """Valida el incremento de radiación de +20 mSv tras un evento de partículas solares."""
    generador = GeneradorEntorno(dia_mision_inicial=120)
    lectura_base = generador.generar_lectura(forzar_tormenta_solar=False)

    lectura_tormenta = generador.generar_lectura(forzar_tormenta_solar=True)
    assert lectura_tormenta.evento_solar_activo is True
    assert lectura_tormenta.radiacion_acumulada_mSv >= lectura_base.radiacion_acumulada_mSv + 19.5


def test_generador_biometria_alerta_fatiga_3_ciclos() -> None:
    """Valida que 3 ciclos sucesivos con sueño < 6h activen la bandera de riesgo de fatiga."""
    generador = GeneradorBiometria(dia_mision_inicial=120)

    # Ciclo 1: sueño deficitario (5.0h)
    generador.simular_nuevo_ciclo_sueno(5.0)
    lectura_1 = generador.generar_lectura()
    assert lectura_1.ciclos_sueno_insuficiente_consecutivos == 1
    assert lectura_1.alerta_riesgo_fatiga is False

    # Ciclo 2: sueño deficitario (5.5h)
    generador.simular_nuevo_ciclo_sueno(5.5)
    lectura_2 = generador.generar_lectura()
    assert lectura_2.ciclos_sueno_insuficiente_consecutivos == 2
    assert lectura_2.alerta_riesgo_fatiga is False

    # Ciclo 3: sueño deficitario (4.8h) -> Dispara bandera
    generador.simular_nuevo_ciclo_sueno(4.8)
    lectura_3 = generador.generar_lectura()
    assert lectura_3.ciclos_sueno_insuficiente_consecutivos == 3
    assert lectura_3.alerta_riesgo_fatiga is True
    assert lectura_3.perdida_osea_pct == 6.0  # Día 120


def test_generador_cognicion_cruce_latencia_voz() -> None:
    """Valida el cruce lógico: si CO2 > 2.5 o sueño < 6h, la latencia sube a 600-900ms."""
    generador = GeneradorCognicion()

    # Caso 1: Nominal (CO2 = 1.5, sueño = 7.5h)
    nominal = generador.generar_lectura(co2_mmhg=1.5, horas_sueno=7.5, ritmo_cardiaco_bpm=65.0)
    assert 140.0 <= nominal.latencia_voz_ms <= 300.0

    # Caso 2: CO2 alto (> 2.5) -> Dispara latencia 600-900ms
    degradado_co2 = generador.generar_lectura(co2_mmhg=3.2, horas_sueno=7.5, ritmo_cardiaco_bpm=65.0)
    assert 600.0 <= degradado_co2.latencia_voz_ms <= 900.0

    # Caso 3: Sueño deficiente (< 6.0) -> Dispara latencia 600-900ms
    degradado_sueno = generador.generar_lectura(co2_mmhg=1.5, horas_sueno=5.2, ritmo_cardiaco_bpm=65.0)
    assert 600.0 <= degradado_sueno.latencia_voz_ms <= 900.0


def test_generador_cognicion_incongruencia_estres_oculto() -> None:
    """Valida simulación de estrés oculto (ritmo > 95 bpm pero densidad léxica ~0.80)."""
    generador = GeneradorCognicion()
    lectura = generador.generar_lectura(
        co2_mmhg=1.5,
        horas_sueno=7.0,
        ritmo_cardiaco_bpm=102.0,
        forzar_incongruencia=True,
    )
    assert lectura.incongruencia_estres_oculto is True
    assert 0.75 <= lectura.densidad_lexica_score <= 0.85


def test_evaluador_correlacion_alertas_nasa() -> None:
    """Valida que el evaluador genere las alertas normativas con citas a estándares NASA."""
    evaluador = EvaluadorCorrelacionService()

    entorno = EntornoModel(
        co2_mmHg=3.4,
        radiacion_acumulada_mSv=72.0,
        radiacion_tasa_diaria_mSv=0.4,
        presion_cabina_kpa=101.2,
        temperatura_cabina_c=22.0,
        evento_solar_activo=True,
    )
    biometria = BiometriaModel(
        ritmo_cardiaco_bpm=105.0,
        horas_sueno_ultimo_ciclo=5.0,
        ciclos_sueno_insuficiente_consecutivos=3,
        alerta_riesgo_fatiga=True,
        perdida_osea_pct=6.0,
        presion_sistolica_mmHg=135.0,
        presion_diastolica_mmHg=85.0,
        spo2_pct=98.0,
    )
    cognicion = CognicionModel(
        latencia_voz_ms=780.0,
        densidad_lexica_score=0.80,
        incongruencia_estres_oculto=True,
        sans_sintoma_vision=True,
    )

    alertas = evaluador.evaluar_estado_sistemico(entorno, biometria, cognicion)
    codigos = {alerta.codigo for alerta in alertas}

    assert "ALERTA-CO2-MAX-V2-6004" in codigos
    assert "ALERTA-SPE-EVENTO-SOLAR-V1-4030" in codigos
    assert "ALERTA-FATIGA-CRONICA-HSRB" in codigos
    assert "ALERTA-CRUCE-LATENCIA-COGNITIVA" in codigos
    assert "ALERTA-INCONGRUENCIA-ESTRES-ASTRA" in codigos
    assert "ALERTA-SANS-SINTOMA-VISION" in codigos


def test_redis_publisher_buffer_tolerancia_fallos() -> None:
    """Valida la reconexión automática y el buffer local (Store-and-Forward) cuando Redis no responde."""
    config = RedisConfig(host="127.0.0.1", port=6399)  # Puerto inaccesible intencional
    publisher = RedisTelemetryPublisher(config=config)

    # Intento de conexión inicial fallará sin lanzar excepciones no controladas
    conexion = publisher.conectar()
    assert conexion is False
    assert publisher.obtener_estado_conexion() == EstadoConexion.DESCONECTADO

    payload = TelemetriaPayload(
        id_mision="TEST-MISSION",
        dia_mision=120,
        astronauta_id="ASTRO-TEST",
        entorno=EntornoModel(
            co2_mmHg=1.8,
            radiacion_acumulada_mSv=55.0,
            radiacion_tasa_diaria_mSv=0.35,
            presion_cabina_kpa=101.3,
            temperatura_cabina_c=21.0,
            evento_solar_activo=False,
        ),
        biometria=BiometriaModel(
            ritmo_cardiaco_bpm=64.0,
            horas_sueno_ultimo_ciclo=6.5,
            ciclos_sueno_insuficiente_consecutivos=0,
            alerta_riesgo_fatiga=False,
            perdida_osea_pct=6.0,
            presion_sistolica_mmHg=120.0,
            presion_diastolica_mmHg=78.0,
            spo2_pct=99.0,
        ),
        cognicion=CognicionModel(
            latencia_voz_ms=210.0,
            densidad_lexica_score=0.68,
            incongruencia_estres_oculto=False,
            sans_sintoma_vision=False,
        ),
        evaluaciones_preliminares=[],
        porcentaje_presupuesto_radiacion_carrera=9.17,
    )

    # Debe amortiguar en buffer local de memoria sin perder el dato
    exito = publisher.publicar_telemetria(payload)
    assert exito is True
    assert publisher.mensajes_en_buffer == 1


def test_orquestador_con_inyeccion_dependencias() -> None:
    """Verifica que el orquestador funcione correctamente con publicador inyectado (DIP)."""
    mock_publisher = MockTelemetryPublisher()
    config_mision = MisionConfig(dia_mision_default=120, intervalo_emision_segundos=0.01)

    orquestador = TelemetriaOrchestrator(
        publicador=mock_publisher,
        config_mision=config_mision,
    )

    # Ejecutar 3 ciclos rápidos
    orquestador.ejecutar_bucle(max_ciclos=3)

    assert mock_publisher.conectado is False  # cerrado al finalizar
    assert len(mock_publisher.payloads_recibidos) == 3

    primer_payload = mock_publisher.payloads_recibidos[0]
    assert primer_payload.dia_mision == 120
    assert primer_payload.biometria.perdida_osea_pct == 6.0
    # Comprobar serialización Pydantic
    json_data = primer_payload.model_dump_json()
    assert isinstance(json_data, str)
    parsed = json.loads(json_data)
    assert parsed["dia_mision"] == 120
    assert "entorno" in parsed
    assert "biometria" in parsed
    assert "cognicion" in parsed
