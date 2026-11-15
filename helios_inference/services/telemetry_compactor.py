"""
Compactador de telemetría de H.E.L.I.O.S.

Convierte el reporte consolidado (rico en texto, para depuración) en el registro
compacto que se persiste y se transmite, y provee la operación inversa para
cualquier consumidor que necesite el texto en servidor.

Principio de diseño: el compactador lee ÚNICAMENTE campos estructurados
(banderas booleanas, índices, puntajes). Nunca parsea las cadenas descriptivas
del reporte, de modo que un cambio de redacción en los cerebros no puede romper
la compactación ni alterar el tamaño del flujo persistido.
"""

from typing import Any

from helios_inference.domain.compact_models import RegistroTelemetriaCompacto
from helios_inference.domain.inference_models import ReporteInferenciaConsolidado
from helios_inference.domain.telemetry_codebook import (
    CODIGOS_AMBIENTAL,
    CODIGOS_BIOMETRICO,
    CODIGO_ASTRA_INCONGRUENCIA,
    CODIGO_FUSION_NOMINAL,
    METADATOS_EDGE_ESTATICOS,
    ORDEN_METRICAS,
    PLANTILLA_FUSION,
    PLANTILLA_FUSION_SEVERA,
    TEXTO_ASTRA_INCONGRUENCIA,
    TEXTO_FUSION_NOMINAL,
    VERSION_ESQUEMA,
)
from helios_inference.cerebros.cerebro_3_grafo_fusion import CerebroGrafoFusion

SUFIJO_ESCALADA = "!"


def _extraer_metricas(payload: dict[str, Any]) -> list[float]:
    """
    Aplana el payload de entrada al vector posicional de ORDEN_METRICAS.

    Args:
        payload: Telemetría cruda con sub-diccionarios entorno/biometria/cognicion.

    Returns:
        Lista de floats en el orden canónico declarado por el libro de códigos.
    """
    plano: dict[str, Any] = {}
    for seccion in ("entorno", "biometria", "cognicion"):
        datos = payload.get(seccion) or {}
        if isinstance(datos, dict):
            plano.update(datos)

    valores: list[float] = []
    for clave in ORDEN_METRICAS:
        try:
            valores.append(round(float(plano.get(clave, 0.0)), 3))
        except (TypeError, ValueError):
            valores.append(0.0)
    return valores


def compactar(
    reporte: ReporteInferenciaConsolidado,
    payload: dict[str, Any],
) -> RegistroTelemetriaCompacto:
    """
    Reduce un reporte consolidado a su registro compacto equivalente.

    Args:
        reporte: Resultado completo emitido por el motor de inferencia.
        payload: Telemetría cruda que originó el reporte (aporta los valores numéricos).

    Returns:
        RegistroTelemetriaCompacto listo para persistir o transmitir.
    """
    c1 = reporte.cerebro_1_ambiental
    c2 = reporte.cerebro_2_biometrico
    c3 = reporte.cerebro_3_grafo_fusion
    c4 = reporte.cerebro_4_astra

    entorno = payload.get("entorno") or {}
    evento_solar = bool(entorno.get("evento_solar_activo", False)) if isinstance(entorno, dict) else False

    # Una arista sólo es significativa si hubo sinergia; el nombre nominal se codifica como -1.
    hay_sinergia = c3.arista_sinergica_critica in CerebroGrafoFusion.NOMBRES_ARISTAS_GRAFO
    indice_arista = c3.indice_argmax if hay_sinergia else -1

    codigos_regla = [
        f"{alerta.id_regla}{SUFIJO_ESCALADA}" if alerta.escalada else alerta.id_regla
        for alerta in reporte.alertas_matriz_decisiones
    ]

    return RegistroTelemetriaCompacto(
        v=VERSION_ESQUEMA,
        ts=int(reporte.timestamp_inferencia.timestamp()),
        mis=reporte.id_mision,
        ast=reporte.astronauta_id,
        dia=reporte.dia_mision,
        amb=[int(x) for x in c1.vector_ambiental],
        bio=[int(x) for x in c2.vector_biometrico],
        sol=int(evento_solar),
        met=_extraer_metricas(payload),
        kr=indice_arista,
        krs=round(c3.puntaje_severidad_maximo, 2),
        krx=int(c3.estres_fisiologico_severo),
        cos=round(c4.similitud_coseno_linea_base, 4),
        inc=int(c4.incongruencia_cognitiva_detectada),
        rg=codigos_regla,
        ms=reporte.tiempo_computo_ms,
    )


def expandir(registro: RegistroTelemetriaCompacto, codebook: dict[str, Any]) -> dict[str, Any]:
    """
    Reconstruye el texto descriptivo a partir del registro compacto y el libro de códigos.

    Es la referencia normativa del algoritmo que ejecuta el HUD en JavaScript:
    ambas implementaciones deben producir exactamente las mismas cadenas.

    Args:
        registro: Registro compacto recibido del enlace.
        codebook: Libro de códigos descargado una única vez.

    Returns:
        Diccionario con las evaluaciones y contramedidas ya en texto legible.
    """
    evaluaciones: list[str] = []
    met = registro.met

    # --- Cerebro 1: etiquetas ambientales ---------------------------------------
    for i, bandera in enumerate(registro.amb):
        if not bandera or i >= len(codebook["ambiental"]):
            continue
        entrada = codebook["ambiental"][i]
        if entrada["codigo"] == "RAD_CRIT" and registro.sol:
            evaluaciones.append(entrada["plantilla_evento"])
        else:
            idx = entrada["metrica"]
            valor = met[idx] if idx is not None and idx < len(met) else 0.0
            evaluaciones.append(entrada["plantilla"].format(valor))

    # --- Cerebro 2: etiquetas biométricas ---------------------------------------
    for i, bandera in enumerate(registro.bio):
        if not bandera or i >= len(codebook["biometrico"]):
            continue
        entrada = codebook["biometrico"][i]
        idx = entrada["metrica"]
        valor = met[idx] if idx is not None and idx < len(met) else 0.0
        evaluaciones.append(entrada["plantilla"].format(valor, dia=registro.dia))

    # --- Cerebro 3: arista dominante del grafo ----------------------------------
    if registro.kr >= 0:
        arista = codebook["aristas_kronecker"][registro.kr]["nombre"]
        texto_fusion = codebook["plantilla_fusion"].format(arista=arista, severidad=registro.krs)
        if registro.krx:
            texto_fusion += codebook["plantilla_fusion_severa"]
            evaluaciones.append(texto_fusion)
        arista_critica = arista
    else:
        texto_fusion = codebook["fusion_nominal"]["texto"]
        arista_critica = "ESTADO_NOMINAL_SIN_SINERGIAS_ADVERSAS"

    # --- Cerebro 4: ASTRA --------------------------------------------------------
    alerta_astra = codebook["astra"]["texto"] if registro.inc else None
    if alerta_astra:
        evaluaciones.append(alerta_astra)

    # --- Matriz de decisiones ----------------------------------------------------
    mapa_reglas = {r["codigo"]: r for r in codebook["reglas"]}
    escalado = {"PRECAUCION": "ALERTA", "ALERTA": "CRITICA", "CRITICA": "CRITICA"}

    alertas: list[dict[str, Any]] = []
    contramedidas: list[str] = []
    for codigo_bruto in registro.rg:
        escalada = codigo_bruto.endswith(SUFIJO_ESCALADA)
        codigo = codigo_bruto.rstrip(SUFIJO_ESCALADA)
        regla = mapa_reglas.get(codigo)
        if regla is None:
            continue
        nivel = escalado[regla["nivel"]] if escalada else regla["nivel"]
        evaluaciones.append(f"[{codigo} - {nivel}] {regla['evaluacion_preliminar']}")
        alertas.append({
            "id_regla": codigo,
            "dominio": regla["dominio"],
            "nivel": nivel,
            "evaluacion_preliminar": regla["evaluacion_preliminar"],
            "contramedidas_sugeridas": regla["contramedidas"],
            "destinatarios": regla["destinatarios"],
            "estandar_base": regla["estandar_base"],
            "ventana_tiempo": regla["ventana_tiempo"],
            "escalada": escalada,
        })
        for accion in regla["contramedidas"]:
            if accion not in contramedidas and len(contramedidas) < 3:
                contramedidas.append(accion)

    return {
        "timestamp_inferencia": registro.ts,
        "id_mision": registro.mis,
        "astronauta_id": registro.ast,
        "dia_mision": registro.dia,
        "evaluaciones_preliminares_activas": evaluaciones,
        "arista_sinergica_critica": arista_critica,
        "evaluacion_preliminar_fusion": texto_fusion,
        "estres_fisiologico_severo": bool(registro.krx),
        "similitud_coseno_linea_base": registro.cos,
        "incongruencia_cognitiva_detectada": bool(registro.inc),
        "alerta_astra": alerta_astra,
        "alertas_matriz_decisiones": alertas,
        "contramedidas_priorizadas": contramedidas,
        "tiempo_computo_ms": registro.ms,
        "metadatos_edge": dict(METADATOS_EDGE_ESTATICOS),
    }
