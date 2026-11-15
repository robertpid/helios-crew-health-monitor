"""
Pruebas de la compactación de telemetría de H.E.L.I.O.S.

Garantizan que el formato de enlace reducido (códigos + valores numéricos)
reconstruye exactamente el texto del reporte consolidado y que el ahorro de
volumen se mantiene dentro del orden de magnitud comprometido.
"""

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from helios_inference.domain.compact_models import RegistroTelemetriaCompacto
from helios_inference.domain.telemetry_codebook import ORDEN_METRICAS, construir_codebook
from helios_inference.services.inference_engine import InferenceEngine
from helios_inference.services.telemetry_compactor import compactar, expandir
from main import app


def _payload(**sobrescribir: Any) -> dict[str, Any]:
    """Construye un payload de telemetría nominal, permitiendo sobrescribir secciones."""
    base: dict[str, Any] = {
        "id_mision": "ARES-VI-MARS-EXPEDITION",
        "dia_mision": 120,
        "astronauta_id": "ASTRO-HELIOS-01",
        "entorno": {
            "co2_mmHg": 3.4,
            "radiacion_acumulada_mSv": 85.0,
            "presion_cabina_kpa": 101.3,
            "evento_solar_activo": False,
        },
        "biometria": {
            "ritmo_cardiaco_bpm": 68.0,
            "horas_sueno_ultimo_ciclo": 5.8,
            "perdida_osea_pct": 1.8,
            "alerta_riesgo_fatiga": False,
        },
        "cognicion": {
            "latencia_voz_ms": 720.0,
            "densidad_lexica_score": 0.82,
            "sans_sintoma_vision": True,
        },
    }
    base.update(sobrescribir)
    return base


@pytest.fixture(scope="module")
def motor() -> InferenceEngine:
    return InferenceEngine()


@pytest.fixture(scope="module")
def codebook() -> dict[str, Any]:
    return construir_codebook()


@pytest.fixture(scope="module")
def cliente() -> TestClient:
    return TestClient(app)


class TestLibroDeCodigos:
    """El libro de códigos debe cubrir el catálogo completo sin divergir de él."""

    def test_codebook_cubre_las_15_reglas(self, codebook: dict[str, Any]) -> None:
        assert len(codebook["reglas"]) == 15
        assert {r["codigo"] for r in codebook["reglas"]} >= {"CX-01", "CX-03", "CX-15"}

    def test_codebook_cubre_las_12_aristas_de_kronecker(self, codebook: dict[str, Any]) -> None:
        assert len(codebook["aristas_kronecker"]) == 12
        assert codebook["aristas_kronecker"][3]["codigo"] == "KR03"

    def test_orden_de_metricas_es_contrato_estable(self, codebook: dict[str, Any]) -> None:
        assert codebook["orden_metricas"] == list(ORDEN_METRICAS)
        assert codebook["orden_metricas"][0] == "co2_mmHg"


class TestReconstruccionSinPerdida:
    """La expansión debe devolver exactamente el texto que emitió el motor."""

    @pytest.mark.parametrize(
        "mutacion",
        [
            {},
            {"entorno": {"co2_mmHg": 1.2, "radiacion_acumulada_mSv": 40.0,
                         "presion_cabina_kpa": 101.3, "evento_solar_activo": False}},
            {"entorno": {"co2_mmHg": 4.2, "radiacion_acumulada_mSv": 700.0,
                         "presion_cabina_kpa": 88.0, "evento_solar_activo": True}},
            {"biometria": {"ritmo_cardiaco_bpm": 132.0, "horas_sueno_ultimo_ciclo": 3.1,
                           "perdida_osea_pct": 3.2, "alerta_riesgo_fatiga": True}},
            {"dia_mision": 5},
        ],
        ids=["nominal", "sin_alertas", "tormenta_solar", "taquicardia", "dia_temprano"],
    )
    def test_evaluaciones_identicas(
        self, motor: InferenceEngine, codebook: dict[str, Any], mutacion: dict[str, Any]
    ) -> None:
        payload = _payload(**mutacion)
        reporte = motor.procesar_telemetria(payload)
        expandido = expandir(compactar(reporte, payload), codebook)

        assert sorted(expandido["evaluaciones_preliminares_activas"]) == sorted(
            reporte.evaluaciones_preliminares_activas
        )
        assert expandido["contramedidas_priorizadas"] == reporte.contramedidas_priorizadas
        assert (
            expandido["arista_sinergica_critica"]
            == reporte.cerebro_3_grafo_fusion.arista_sinergica_critica
        )

    def test_niveles_de_regla_respetan_la_escalada(
        self, motor: InferenceEngine, codebook: dict[str, Any]
    ) -> None:
        payload = _payload(
            biometria={
                "ritmo_cardiaco_bpm": 68.0,
                "horas_sueno_ultimo_ciclo": 4.0,
                "perdida_osea_pct": 1.8,
                "alerta_riesgo_fatiga": True,
                "ciclos_sueno_insuficiente_consecutivos": 4,
            }
        )
        reporte = motor.procesar_telemetria(payload)
        expandido = expandir(compactar(reporte, payload), codebook)

        niveles_originales = [(a.id_regla, a.nivel.value) for a in reporte.alertas_matriz_decisiones]
        niveles_expandidos = [(a["id_regla"], a["nivel"]) for a in expandido["alertas_matriz_decisiones"]]
        assert niveles_expandidos == niveles_originales

    def test_el_compactador_no_depende_del_texto_del_reporte(
        self, motor: InferenceEngine
    ) -> None:
        """Cambiar la redacción no debe alterar el registro compacto."""
        payload = _payload()
        reporte = motor.procesar_telemetria(payload)
        registro_original = compactar(reporte, payload)

        mutado = reporte.model_copy(
            update={"evaluaciones_preliminares_activas": ["TEXTO ARBITRARIO DISTINTO"]}
        )
        assert compactar(mutado, payload).model_dump() == registro_original.model_dump()


class TestAhorroDeVolumen:
    """El registro compacto debe mantener el orden de magnitud de reducción."""

    def test_reduccion_minima_de_un_orden_de_magnitud(self, motor: InferenceEngine) -> None:
        payload = _payload()
        reporte = motor.procesar_telemetria(payload)

        bytes_completo = len(reporte.model_dump_json().encode("utf-8"))
        bytes_compacto = len(compactar(reporte, payload).model_dump_json().encode("utf-8"))

        assert bytes_compacto < bytes_completo / 10, (
            f"Reducción insuficiente: {bytes_completo} B -> {bytes_compacto} B"
        )

    def test_el_registro_absorbe_las_metricas_crudas(self, motor: InferenceEngine) -> None:
        """El compacto sustituye también al payload de entrada: debe portar las métricas."""
        payload = _payload()
        registro = compactar(motor.procesar_telemetria(payload), payload)

        assert len(registro.met) == len(ORDEN_METRICAS)
        assert registro.met[0] == pytest.approx(payload["entorno"]["co2_mmHg"])
        assert registro.met[3] == pytest.approx(payload["biometria"]["ritmo_cardiaco_bpm"])


class TestEndpointsDeTelemetria:
    """Contrato HTTP del router de telemetría compacta."""

    def test_codebook_se_sirve_cacheable(self, cliente: TestClient) -> None:
        resp = cliente.get("/api/v1/telemetria/codebook")
        assert resp.status_code == 200
        assert "max-age" in resp.headers.get("cache-control", "")
        assert len(resp.json()["reglas"]) == 15

    def test_ciclo_compacto_es_menor_que_el_reporte_completo(self, cliente: TestClient) -> None:
        compacto = cliente.get("/api/v1/telemetria/compacto")
        completo = cliente.get("/api/v1/fusion/resultado")
        assert compacto.status_code == 200
        assert len(compacto.content) < len(completo.content)

    def test_registro_compacto_valida_contra_su_esquema(self, cliente: TestClient) -> None:
        registro = RegistroTelemetriaCompacto(**cliente.get("/api/v1/telemetria/compacto").json())
        assert registro.v == 1
        assert len(registro.amb) == 3
        assert len(registro.bio) == 4

    def test_endpoint_de_ahorro_reporta_reduccion(self, cliente: TestClient) -> None:
        datos = cliente.get("/api/v1/telemetria/ahorro").json()
        assert datos["por_ciclo"]["factor"] > 1.0
        assert datos["por_dia_mb"]["compacto"] < datos["por_dia_mb"]["completo"]

    def test_el_hud_carga_el_traductor_de_codigos(self, cliente: TestClient) -> None:
        assert "codebook_service.js" in cliente.get("/dashboard").text
