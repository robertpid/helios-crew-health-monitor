/**
 * ==============================================================================
 * CAPA DE SERVICIOS: CodebookService
 *
 * Descarga UNA sola vez el libro de códigos de telemetría y reconstruye en el
 * cliente las cadenas descriptivas que antes viajaban en cada ciclo.
 *
 * El enlace transporta sólo códigos estables (CO2_ELEV, CX-03, KR03...) y
 * valores numéricos; el texto se compone aquí. La salida replica exactamente la
 * forma del reporte consolidado, de modo que el resto del HUD no necesita
 * cambio alguno.
 *
 * Esta implementación es el espejo en JavaScript de
 * `helios_inference/services/telemetry_compactor.expandir()`: ambas deben
 * producir cadenas idénticas.
 * ==============================================================================
 */

class CodebookService {
  constructor() {
    this._codebook = null;
    this._cargando = null;
    this._ESCALADO = { PRECAUCION: "ALERTA", ALERTA: "CRITICA", CRITICA: "CRITICA" };
  }

  get disponible() {
    return this._codebook !== null;
  }

  /**
   * Descarga el libro de códigos una única vez (idempotente y a prueba de carreras).
   */
  async cargar() {
    if (this._codebook) return this._codebook;
    if (this._cargando) return this._cargando;

    this._cargando = (async () => {
      const resp = await fetch("/api/v1/telemetria/codebook");
      if (!resp.ok) throw new Error(`Codebook HTTP ${resp.status}`);
      this._codebook = await resp.json();
      return this._codebook;
    })();

    try {
      return await this._cargando;
    } finally {
      this._cargando = null;
    }
  }

  /**
   * Sustituye los marcadores posicionales de una plantilla del libro de códigos.
   * Soporta `{0}`, `{0:.2f}` y el marcador nominal `{dia}`.
   */
  _formatear(plantilla, valor, dia) {
    return plantilla
      .replace(/\{0(?::\.(\d)f)?\}/g, (_, decimales) =>
        decimales === undefined ? String(valor) : Number(valor).toFixed(Number(decimales))
      )
      .replace(/\{dia\}/g, String(dia));
  }

  /**
   * Reconstruye el reporte consolidado completo a partir del registro compacto.
   *
   * @param {object} r Registro compacto recibido de /api/v1/telemetria/compacto
   * @returns {object|null} Reporte con la misma forma que /api/v1/fusion/resultado
   */
  expandir(r) {
    const cb = this._codebook;
    if (!cb || !r) return null;

    const met = r.met || [];
    const etiquetasAmbiental = [];
    const etiquetasBiometrico = [];

    // --- Cerebro 1: etiquetas ambientales ------------------------------------
    (r.amb || []).forEach((bandera, i) => {
      if (!bandera || i >= cb.ambiental.length) return;
      const e = cb.ambiental[i];
      if (e.codigo === "RAD_CRIT" && r.sol) {
        etiquetasAmbiental.push(e.plantilla_evento);
      } else {
        etiquetasAmbiental.push(this._formatear(e.plantilla, met[e.metrica] ?? 0, r.dia));
      }
    });

    // --- Cerebro 2: etiquetas biométricas ------------------------------------
    (r.bio || []).forEach((bandera, i) => {
      if (!bandera || i >= cb.biometrico.length) return;
      const e = cb.biometrico[i];
      const valor = e.metrica === null ? 0 : (met[e.metrica] ?? 0);
      etiquetasBiometrico.push(this._formatear(e.plantilla, valor, r.dia));
    });

    // El orden de consolidación replica al del motor: Cerebro 1, luego Cerebro 2.
    const evaluaciones = [...etiquetasAmbiental, ...etiquetasBiometrico];

    // --- Cerebro 3: arista dominante del grafo de Kronecker ------------------
    let aristaCritica = "ESTADO_NOMINAL_SIN_SINERGIAS_ADVERSAS";
    let textoFusion = cb.fusion_nominal.texto;
    if (r.kr >= 0 && cb.aristas_kronecker[r.kr]) {
      aristaCritica = cb.aristas_kronecker[r.kr].nombre;
      textoFusion = cb.plantilla_fusion
        .replace("{arista}", aristaCritica)
        .replace(/\{severidad(?::\.\df)?\}/, Number(r.krs).toFixed(1));
      if (r.krx) {
        textoFusion += cb.plantilla_fusion_severa;
        evaluaciones.push(textoFusion);
      }
    }

    // --- Cerebro 4: ASTRA ----------------------------------------------------
    const alertaAstra = r.inc ? cb.astra.texto : null;
    if (alertaAstra) evaluaciones.push(alertaAstra);

    // --- Matriz de decisiones ------------------------------------------------
    const mapaReglas = new Map(cb.reglas.map((x) => [x.codigo, x]));
    const alertas = [];
    const contramedidas = [];

    (r.rg || []).forEach((codigoBruto) => {
      const escalada = codigoBruto.endsWith("!");
      const codigo = escalada ? codigoBruto.slice(0, -1) : codigoBruto;
      const regla = mapaReglas.get(codigo);
      if (!regla) return;

      const nivel = escalada ? this._ESCALADO[regla.nivel] : regla.nivel;
      evaluaciones.push(`[${codigo} - ${nivel}] ${regla.evaluacion_preliminar}`);
      alertas.push({
        id_regla: codigo,
        dominio: regla.dominio,
        nivel,
        evaluacion_preliminar: regla.evaluacion_preliminar,
        contramedidas_sugeridas: regla.contramedidas,
        destinatarios: regla.destinatarios,
        estandar_base: regla.estandar_base,
        ventana_tiempo: regla.ventana_tiempo,
        escalada,
      });
      regla.contramedidas.forEach((accion) => {
        if (contramedidas.length < 3 && !contramedidas.includes(accion)) {
          contramedidas.push(accion);
        }
      });
    });

    // Reconstrucción con la forma exacta del reporte consolidado
    return {
      timestamp_inferencia: new Date(r.ts * 1000).toISOString(),
      id_mision: r.mis,
      dia_mision: r.dia,
      astronauta_id: r.ast,
      cerebro_1_ambiental: {
        vector_ambiental: r.amb,
        etiquetas_activadas: etiquetasAmbiental,
        co2_excedido: !!r.amb?.[0],
        radiacion_critica: !!r.amb?.[1],
        presion_anomala: !!r.amb?.[2],
      },
      cerebro_2_biometrico: {
        vector_biometrico: r.bio,
        etiquetas_activadas: etiquetasBiometrico,
        metricas_fisicas_normales: (r.bio || []).every((x) => !x),
        cuerpo_en_panico: !!r.bio?.[0],
      },
      cerebro_3_grafo_fusion: {
        vector_kronecker_dimension: 12,
        arista_sinergica_critica: aristaCritica,
        indice_argmax: r.kr,
        puntaje_severidad_maximo: r.krs,
        estres_fisiologico_severo: !!r.krx,
        evaluacion_preliminar_fusion: textoFusion,
      },
      cerebro_4_astra: {
        similitud_coseno_linea_base: r.cos,
        incongruencia_cognitiva_detectada: !!r.inc,
        alerta_astra: alertaAstra,
      },
      evaluaciones_preliminares_activas: evaluaciones,
      alertas_matriz_decisiones: alertas,
      contramedidas_priorizadas: contramedidas,
      tiempo_computo_ms: r.ms,
      metadatos_edge: cb.metadatos_edge,
      metricas_crudas: this._mapearMetricas(met),
    };
  }

  /** Reconstruye el diccionario de métricas a partir del array posicional. */
  _mapearMetricas(met) {
    const salida = {};
    (this._codebook?.orden_metricas || []).forEach((clave, i) => {
      salida[clave] = met[i];
    });
    return salida;
  }
}

window.codebookService = new CodebookService();
