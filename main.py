"""
H.E.L.I.O.S. (Holistic Edge Life-support Intelligence & Operational Support)
Motor de Inferencia Central y Servidor API Edge (FastAPI + Pure NumPy).

Desarrollado para computación en el borde (Edge Computing) en misiones espaciales profundas.
Ejecuta 4 cerebros analíticos con álgebra lineal pura sin dependencias pesadas:
- Cerebro 1: Motor Ambiental (Heurísticas de cabina y radiación).
- Cerebro 2: Motor Biométrico (Desviación de línea base y fatiga circadiana/ósea).
- Cerebro 3: Grafo Lógico y Fusión Espacial (Producto Tensorial de Kronecker: np.kron).
- Cerebro 4: Inteligencia Vectorial Cognitiva ASTRA (Similitud Coseno: np.dot).

Consume asíncronamente desde colas de Redis ('buzon_telemetria_tierra') mediante RPOP
y expone endpoints REST para monitorización y control por la tripulación.
"""

from contextlib import asynccontextmanager
import logging
import os
import sys
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

from helios_inference.cerebros.cerebro_1_ambiental import CerebroAmbiental
from helios_inference.cerebros.cerebro_2_biometrico import CerebroBiometrico
from helios_inference.cerebros.cerebro_3_grafo_fusion import CerebroGrafoFusion
from helios_inference.cerebros.cerebro_4_astra import CerebroCognitivoAstra
from helios_inference.domain.decision_rules import CATALOGO_REGLAS_CRITICAS, ReglaDefinicion
from helios_inference.domain.inference_models import ReporteInferenciaConsolidado
from helios_inference.infrastructure.redis_consumer import AsyncRedisTelemetryConsumer
from helios_inference.services.decision_matrix_evaluator import DecisionMatrixEvaluator
from helios_inference.services.inference_engine import InferenceEngine
from helios_inference.api.psicologia_router import router as psicologia_router

# Configuración del subsistema de logging según normas aeroespaciales
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d UTC | %(levelname)-8s | [%(name)s] | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("helios_inference")


# ======================================================================================
# INYECCIÓN DE DEPENDENCIAS (SOLID - DIP): CONSTRUCCIÓN MODULAR DE LOS 4 CEREBROS
# ======================================================================================
def instanciar_motor_inferencia() -> InferenceEngine:
    """Ensambla el motor inyectando instancias independientes para cada cerebro (DIP)."""
    cerebro_ambiental = CerebroAmbiental(
        umbral_co2_mmhg=3.0, umbral_radiacion_msv=600.0,
        presion_minima_kpa=95.0, presion_maxima_kpa=103.0,
    )
    cerebro_biometrico = CerebroBiometrico(
        umbral_taquicardia_bpm=95.0, umbral_bradicardia_bpm=50.0,
        umbral_sueno_minimo_horas=6.0, dia_mision_inicio_riesgo_oseo=30,
        umbral_perdida_osea_pct=1.5,
    )
    cerebro_grafo = CerebroGrafoFusion(umbral_peligro_severo=6.5)
    cerebro_astra = CerebroCognitivoAstra(
        latencia_base_ms=200.0, densidad_base_score=1.0,
        umbral_caida_similitud=0.88, umbral_latencia_fatiga_ms=500.0,
    )
    evaluador_matriz = DecisionMatrixEvaluator()

    return InferenceEngine(
        cerebro_ambiental=cerebro_ambiental,
        cerebro_biometrico=cerebro_biometrico,
        cerebro_grafo_fusion=cerebro_grafo,
        cerebro_cognitivo_astra=cerebro_astra,
        evaluador_matriz=evaluador_matriz,
    )


# Instancia única del orquestador analítico
motor_inferencia_global = instanciar_motor_inferencia()

# Consumidor asíncrono para ingesta en background desde Redis
consumidor_redis_global = AsyncRedisTelemetryConsumer(
    motor_inferencia=motor_inferencia_global,
    host="127.0.0.1",
    port=6379,
    colas=["buzon_telemetria_tierra", "buzon_telemetria_tierra_queue"],
    intervalo_sondeo_segundos=0.5,
    intervalo_reintento_segundos=3.0,
)


# ======================================================================================
# CICLO DE VIDA DE FASTAPI (LIFESPAN ASÍNCRONO)
# ======================================================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gestiona el inicio y detención limpia del consumidor asíncrono de Redis.
    Asegura que el servicio FastAPI arranque inmediatamente sin bloquearse por la red.
    """
    logger.info("Iniciando H.E.L.I.O.S. Inference Engine (Edge Computing Mode)...")
    await consumidor_redis_global.iniciar()
    yield
    logger.info("Deteniendo servicios de H.E.L.I.O.S. y liberando conexiones...")
    await consumidor_redis_global.detener()


# ======================================================================================
# SERVIDOR FASTAPI
# ======================================================================================
app = FastAPI(
    title="H.E.L.I.O.S. - Deep Space Life Support Inference Engine",
    description=(
        "Motor de inferencia en el borde (Edge AI) para soporte vital y evaluación preliminar "
        "de tripulaciones espaciales basada en 4 cerebros modulares con álgebra lineal pura (NumPy)."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Montaje de la capa estática del Frontend N-Capas
ruta_frontend = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(ruta_frontend):
    app.mount("/static", StaticFiles(directory=ruta_frontend), name="static")

# Inclusión del router para evaluación psicológica y bienestar del astronauta (ASTRA BHP)
app.include_router(psicologia_router, prefix="/api/v1/psicologico", tags=["Evaluación Psicológica"])


def servir_dashboard_html() -> HTMLResponse:
    """Retorna el documento HTML del Cockpit HUD con cabeceras anti-caché estrictas."""
    ruta_html = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if not os.path.exists(ruta_html):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo de interfaz frontend/index.html no encontrado.",
        )
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    with open(ruta_html, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), headers=headers)


# Esquema para inyección directa HTTP (pruebas sin Redis)
class TelemetriaInputSchema(BaseModel):
    """Payload de entrada para evaluación preliminar inmediata vía REST."""
    id_mision: str = Field(default="ARES-VI-MARS-EXPEDITION")
    dia_mision: int = Field(default=120)
    astronauta_id: str = Field(default="ASTRO-HELIOS-01")
    entorno: dict[str, Any] = Field(
        default={
            "co2_mmHg": 1.8,
            "radiacion_acumulada_mSv": 85.0,
            "presion_cabina_kpa": 101.3,
            "evento_solar_activo": False,
        }
    )
    biometria: dict[str, Any] = Field(
        default={
            "ritmo_cardiaco_bpm": 68.0,
            "horas_sueno_ultimo_ciclo": 7.0,
            "perdida_osea_pct": 0.8,
            "alerta_riesgo_fatiga": False,
        }
    )
    cognicion: dict[str, Any] = Field(
        default={
            "latencia_voz_ms": 210.0,
            "densidad_lexica_score": 0.95,
            "sans_sintoma_vision": False,
        }
    )


# ======================================================================================
# ENDPOINTS REST
# ======================================================================================
@app.get(
    "/",
    summary="Dashboard Visual / Estado General de H.E.L.I.O.S.",
    tags=["Sistema"],
)
async def estado_sistema(request: Request) -> Any:
    """
    Retorna el Dashboard Holográfico interactivo en navegadores web (Accept text/html)
    o los metadatos JSON operacionales en llamadas API de máquina (Accept application/json).
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept and not (
        "application/json" in accept and accept.index("application/json") < accept.index("text/html")
    ):
        return servir_dashboard_html()

    return {
        "sistema": "H.E.L.I.O.S. Edge AI Inference Engine",
        "mision_referencia": "ARES-VI-MARS-EXPEDITION (Día 120)",
        "estado": "OPERACIONAL",
        "cerebros_activos": [
            "Cerebro 1: Motor Ambiental (Reglas Heurísticas en R^3)",
            "Cerebro 2: Motor Biométrico (Desviación de Línea Base en R^4)",
            "Cerebro 3: Grafo Lógico y Fusión Espacial (Producto Tensorial de Kronecker en R^12)",
            "Cerebro 4: Inteligencia Vectorial Cognitiva ASTRA (Similitud Coseno en R^2)",
        ],
        "edge_ai_restricciones": {
            "pytorch_tensorflow": "DESHABILITADOS (Pure-NumPy Mode)",
            "bases_vectoriales_grafos": "DESHABILITADAS (Álgebra matricial np.kron/np.dot)",
            "consumo_memoria": "< 60 MB",
            "latencia_inferencia_tipica": "< 1.0 ms",
        },
        "redis_enlace": {
            "conectado": consumidor_redis_global.conectado,
            "paquetes_procesados": consumidor_redis_global.contador_procesados,
        },
        "dashboard_ui_url": "http://127.0.0.1:8000/dashboard",
    }


@app.get(
    "/dashboard",
    response_class=HTMLResponse,
    summary="Dashboard Holográfico de Soporte Vital",
    tags=["Interfaz Visual"],
)
async def ver_dashboard() -> HTMLResponse:
    """Despliega directamente la interfaz visual de cabina con el cuerpo holográfico y hábitat."""
    return servir_dashboard_html()


@app.get(
    "/health",
    summary="Verificación de Salud del Nodo Edge",
    tags=["Sistema"],
)
async def healthcheck() -> dict[str, Any]:
    """Comprueba el estado del motor y la conectividad con la infraestructura Redis."""
    return {
        "estado": "OK",
        "redis_conectado": consumidor_redis_global.conectado,
        "mensajes_ingeridos": consumidor_redis_global.contador_procesados,
    }


@app.get(
    "/api/v1/fusion/resultado",
    response_model=ReporteInferenciaConsolidado,
    summary="Obtener Último Resultado de Fusión de los 4 Cerebros",
    tags=["Inferencia"],
)
async def obtener_resultado_fusion() -> ReporteInferenciaConsolidado:
    """
    Expone el resultado consolidado de la última telemetría procesada por los 4 Cerebros.
    Si aún no ha llegado telemetría desde Redis, procesa una muestra nominal por defecto.
    """
    reporte = consumidor_redis_global.ultimo_reporte
    if reporte is None:
        # Generar inferencia inicial de demostración para el estado de arranque
        payload_inicial = TelemetriaInputSchema().model_dump()
        reporte = motor_inferencia_global.procesar_telemetria(payload_inicial)

    return reporte


@app.get(
    "/api/v1/alertas",
    summary="Lista de Evaluaciones Preliminares y Alertas Activas",
    tags=["Inferencia"],
)
async def obtener_alertas_activas() -> dict[str, Any]:
    """Retorna las alertas y evaluaciones preliminares vigentes derivadas del cruce multivariado."""
    reporte = consumidor_redis_global.ultimo_reporte
    if reporte is None:
        return {
            "evaluaciones_preliminares_activas": [],
            "estres_fisiologico_severo": False,
            "incongruencia_cognitiva": False,
            "mensaje": "Sin telemetrías registradas en la cola.",
        }

    return {
        "timestamp": reporte.timestamp_inferencia.isoformat(),
        "astronauta_id": reporte.astronauta_id,
        "dia_mision": reporte.dia_mision,
        "evaluaciones_preliminares_activas": reporte.evaluaciones_preliminares_activas,
        "estres_fisiologico_severo": reporte.cerebro_3_grafo_fusion.estres_fisiologico_severo,
        "incongruencia_cognitiva": reporte.cerebro_4_astra.incongruencia_cognitiva_detectada,
        "arista_grafo_critica": reporte.cerebro_3_grafo_fusion.arista_sinergica_critica,
    }


@app.post(
    "/api/v1/inferir",
    response_model=ReporteInferenciaConsolidado,
    status_code=status.HTTP_200_OK,
    summary="Inferencia Directa vía REST (Prueba sin Redis)",
    tags=["Inferencia"],
)
async def inferir_directo(payload: TelemetriaInputSchema) -> ReporteInferenciaConsolidado:
    """
    Permite inyectar un payload de telemetría directamente por HTTP para obtener
    la evaluación preliminar inmediata y verificar el comportamiento de los 4 cerebros.
    """
    try:
        reporte = motor_inferencia_global.procesar_telemetria(payload.model_dump())
        return reporte
    except Exception as error:
        logger.error("Error al procesar inferencia directa: %s", str(error), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Fallo en motor de inferencia: {error}",
        )


@app.get(
    "/api/v1/matriz-decisiones",
    summary="Catálogo de las 15 Reglas Críticas de Cruce (NASA-STD-3001)",
    tags=["Matriz de Decisiones"],
)
async def obtener_catalogo_matriz() -> list[ReglaDefinicion]:
    """Retorna las 15 reglas formales de la matriz de Martina para inspección o configuración del frontend."""
    return CATALOGO_REGLAS_CRITICAS


@app.get(
    "/api/v1/contramedidas/activas",
    summary="Contramedidas Inmediatas Priorizadas (Máximo 3 Acciones)",
    tags=["Contramedidas"],
)
async def obtener_contramedidas_activas() -> dict[str, Any]:
    """
    Retorna hasta 3 contramedidas priorizadas de las alertas dominantes activas,
    ordenadas por jerarquía estricta para evitar la saturación cognitiva del astronauta.
    """
    reporte = consumidor_redis_global.ultimo_reporte
    if reporte is None:
        payload_inicial = TelemetriaInputSchema().model_dump()
        reporte = motor_inferencia_global.procesar_telemetria(payload_inicial)

    return {
        "timestamp": reporte.timestamp_inferencia.isoformat(),
        "astronauta_id": reporte.astronauta_id,
        "dia_mision": reporte.dia_mision,
        "max_acciones_permitidas": 3,
        "contramedidas_priorizadas": reporte.contramedidas_priorizadas,
        "cruces_activos_total": len(reporte.alertas_matriz_decisiones),
        "alertas_detalladas": [
            {
                "id_regla": a.id_regla,
                "nivel": a.nivel.value,
                "dominio": a.dominio.value,
                "evaluacion_preliminar": a.evaluacion_preliminar,
                "acciones_sugeridas": a.contramedidas_sugeridas,
                "destinatarios": [d.value for d in a.destinatarios],
                "estandar_base": a.estandar_base,
            }
            for a in reporte.alertas_matriz_decisiones
        ],
    }


# ======================================================================================
# PUNTO DE ENTRADA PRINCIPAL SEGURO (PEP 8)
# ======================================================================================
if __name__ == "__main__":
    logger.info("Iniciando servidor web aeroespacial en http://127.0.0.1:8000...")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False,
    )
