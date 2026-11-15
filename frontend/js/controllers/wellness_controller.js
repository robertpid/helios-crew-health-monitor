/**
 * CAPA DE CONTROLADORES: WellnessController
 * Maneja la interacción de la Ventana 3: Bienestar, Rutinas, Asistente y Gamificación.
 * Protocolo interactivo de Evaluación Psicológica y Cognitiva ASTRA (NASA BHP).
 * Rigurosamente bajo 400 líneas (Clean Code & SRP).
 */

class WellnessController {
  constructor(soundService = null) {
    this._sound = soundService || window.soundService;
    this._tareasEstado = { meditacion: 100, estiramiento: 100, ejercicio: 60, hidratacion: 80 };
    this._gamificacion = { nivel: 6, exp: 1320, expMax: 1500 };
    this._temporizadorRespiracion = null;
    this._respirando = false;

    this._preguntaActual = 1;
    this._tiempoInicioPregunta = performance.now();
    this._reconocimientoVoz = null;
    this._escuchandoVoz = false;
    this._evaluando = false;

    this._preguntasBHP = [
      {
        id: 1, cat: "Alerta & Fatiga",
        texto: "¿Cómo describirías tu nivel de concentración y energía para las operaciones de hoy?",
        chips: ["100% enfocado y despejado para la jornada.", "Normal, dentro de los parámetros habituales.", "He sentido lentitud mental y fatiga atencional hoy."]
      },
      {
        id: 2, cat: "Carga Cognitiva",
        texto: "¿Has experimentado sobrecarga o retraso en la resolución de tareas técnicas hoy?",
        chips: ["Cero sobrecarga, procedimientos en tiempo óptimo.", "Bien, carga operativa estándar.", "Las checklists me han tomado más tiempo del previsto."]
      },
      {
        id: 3, cat: "Estado Emocional Sol 120",
        texto: "Reporte Sol 120: ¿Cómo percibes el ambiente en cabina y la distancia con la Tierra?",
        chips: ["Excelente moral, comunicación fluida con Houston.", "Todo en orden en cabina, sin contratiempos.", "El aislamiento se hace notar hoy, requiero pausa breve."]
      }
    ];

    this._initVoz();
  }

  avanzarTarea(tipo) {
    this._sound?.reproducirClick?.();
    let act = (this._tareasEstado[tipo] || 0) + 20;
    if (act > 100) act = 20;
    this._tareasEstado[tipo] = act;

    const cap = tipo.charAt(0).toUpperCase() + tipo.slice(1);
    const tagVal = document.getElementById(`taskPercent${cap}`);
    const tagBar = document.getElementById(`taskBar${cap}`);
    if (tagVal) tagVal.innerText = `${act}%`;
    if (tagBar) tagBar.style.width = `${act}%`;
    this.sumarExp(25);
  }

  sumarExp(pts) {
    this._gamificacion.exp += pts;
    if (this._gamificacion.exp >= this._gamificacion.expMax) {
      this._gamificacion.nivel += 1;
      this._gamificacion.exp -= this._gamificacion.expMax;
      this._gamificacion.expMax = Math.round(this._gamificacion.expMax * 1.25);
      this._sound?.reproducirNominal?.();
    }
    const lvlTag = document.getElementById("userLevelTag");
    const expTag = document.getElementById("userExpTag");
    const expBar = document.getElementById("userExpBar");
    if (lvlTag) lvlTag.innerText = `NIVEL ${this._gamificacion.nivel}`;
    if (expTag) expTag.innerHTML = `EXP <strong style="color:var(--neon-green);">${this._gamificacion.exp}</strong> / ${this._gamificacion.expMax}`;
    if (expBar) expBar.style.width = `${Math.min(100, Math.round((this._gamificacion.exp / this._gamificacion.expMax) * 100))}%`;
  }

  iniciarExamenOftalmico() {
    this._sound?.reproducirClick?.();
    this._mostrarFeedback("👁️ <strong>EVALUACIÓN OFTÁLMICA (SANS TEST):</strong> Fondo de ojo nominal bilateral. Grado SANS: 0.");
  }

  iniciarExamenSonar() {
    this._sound?.reproducirClick?.();
    this._mostrarFeedback("👂 <strong>BARRIDO SONAR / AUDIOMETRÍA:</strong> 250-8000 Hz evaluadas. Ruido de cabina en 58 dBA nominal.");
  }

  _mostrarFeedback(html) {
    const fb = document.getElementById("examenExtraFeedback");
    if (!fb) return;
    fb.style.display = "block";
    fb.innerHTML = html;
    setTimeout(() => { if (fb) fb.style.display = "none"; }, 6000);
  }

  sincronizarCorreo() {
    this._sound?.reproducirClick?.();
    alert("📡 SINCRONIZACIÓN DSN COMPLETADA: Enlace activo con Houston. 0 mensajes pendientes.");
  }

  // ==============================================================================
  // PROTOCOLO DE EVALUACIÓN PSICOLÓGICA Y COGNITIVA (SISTEMA ASTRA)
  // ==============================================================================
  iniciarProtocoloPsicologico() {
    this._sound?.reproducirClick?.();
    this._preguntaActual = 1;
    this._actualizarBadgeEstado("EN EVALUACIÓN", "status-critical");
    const box = document.getElementById("assistantChatBox");
    if (box) {
      box.innerHTML = `<div style="padding:8px 12px; background:rgba(0,240,255,0.06); border-left:3px solid var(--neon-cyan); border-radius:0 6px 6px 0;"><strong style="color:var(--neon-cyan); font-family:var(--font-hud);">SISTEMA ASTRA:</strong> Chequeo psicológico y de fatiga Sol 120. Mediremos latencia verbal, vocabulario y coherencia fisiológica.</div>`;
    }
    this._presentarPregunta();
  }

  _presentarPregunta() {
    const item = this._preguntasBHP.find(p => p.id === this._preguntaActual);
    if (!item) return;
    this._tiempoInicioPregunta = performance.now();
    this._agregarMensaje("SISTEMA ASTRA", `<strong>Pregunta ${item.id}/3 (${item.cat}):</strong> ${item.texto}`, "astra");

    const cntChips = document.getElementById("psychSuggestionsContainer");
    if (cntChips) {
      cntChips.innerHTML = item.chips.map(c => `
        <button class="btn-hud" onclick="window.hudController.seleccionarChipSugerido('${c.replace(/'/g, "\\'")}')" style="font-size:10px; padding:4px 8px; text-transform:none;">${c}</button>
      `).join("");
    }
    const input = document.getElementById("inputPsychText");
    if (input) { input.value = ""; input.focus(); }
  }

  seleccionarChipSugerido(texto) {
    const input = document.getElementById("inputPsychText");
    if (input) input.value = texto;
    this.enviarRespuestaPsicologica();
  }

  async enviarRespuestaPsicologica() {
    if (this._evaluando) return;
    const input = document.getElementById("inputPsychText");
    const texto = input ? input.value.trim() : "";
    if (!texto) return;

    this._sound?.reproducirClick?.();
    const latenciaMs = Math.max(120, Math.round(performance.now() - this._tiempoInicioPregunta));
    this._evaluando = true;
    this._agregarMensaje("Astronauta", texto, "astronauta");
    if (input) input.value = "";

    const telemetria = window.stateManager?._state?.telemetria;
    const ritmoBpm = telemetria?.fisiologia?.ritmo_cardiaco_bpm || 72.0;

    let res = await window.telemetryService?.evaluarRespuestaPsicologica?.({
      id_pregunta: this._preguntaActual, texto_respuesta: texto,
      latencia_ms: latenciaMs, ritmo_cardiaco_bpm: ritmoBpm,
      cuerpo_en_panico: ritmoBpm > 95.0
    });

    if (!res) res = this._calcularMetricasLocal(texto, latenciaMs, ritmoBpm);
    this._actualizarBadgesTelemetria(res);

    window.stateManager?.actualizarCognicion?.({
      latencia_ms: res.latencia_ms, densidad_lexica: res.densidad_lexica,
      similitud_coseno: res.similitud_coseno, incongruencia_detectada: res.incongruencia_detectada,
      alerta_astra: res.incongruencia_detectada ? res.evaluacion_preliminar : null
    });

    setTimeout(() => {
      this._agregarMensaje("SISTEMA ASTRA", res.respuesta_asistente, res.incongruencia_detectada ? "alerta" : "nominal");
      this.sumarExp(25);
      this._evaluando = false;

      if (this._preguntaActual < 3) {
        this._preguntaActual += 1;
        setTimeout(() => this._presentarPregunta(), 900);
      } else {
        this._finalizarProtocolo();
      }
    }, 350);
  }

  _finalizarProtocolo() {
    this._actualizarBadgeEstado("COMPLETADO", "status-stable");
    const esCrit = window.stateManager?._state?.telemetria?.cognicion?.incongruencia_detectada;
    const banner = `<div style="padding:10px 14px; background:${esCrit ? "rgba(255,34,85,0.12)" : "rgba(0,255,136,0.1)"}; border:1px solid ${esCrit ? "var(--neon-red)" : "var(--neon-green)"}; border-radius:6px; margin-top:6px;"><strong style="color:${esCrit ? "var(--neon-red)" : "var(--neon-green)"}; font-family:var(--font-hud);">EVALUACIÓN PRELIMINAR FINALIZADA:</strong><br>${esCrit ? "⚠️ Incongruencia detectada. Sugerencia: Iniciar relajación 4-4-6 y reposo." : "✅ Coherencia cognitiva nominal. Apto para el programa del Sol 120."}</div>`;
    const box = document.getElementById("assistantChatBox");
    if (box) { box.insertAdjacentHTML("beforeend", banner); box.scrollTop = box.scrollHeight; }
  }

  _calcularMetricasLocal(texto, latenciaMs, ritmoBpm) {
    const pal = texto.toLowerCase().split(/\s+/).filter(Boolean);
    let den = pal.length > 0 ? (new Set(pal).size / pal.length) : 0.2;
    if (pal.length <= 2) den = Math.min(0.35, den * 0.4);
    den = Math.round(Math.min(1.0, Math.max(0.15, den)) * 100) / 100;

    const v = [latenciaMs / 200.0, den / 1.0];
    const dot = v[0] + v[1];
    const cosSim = Math.round((dot / (Math.sqrt(v[0] ** 2 + v[1] ** 2) * Math.SQRT2)) * 1000) / 1000;
    const inc = (cosSim < 0.88 || latenciaMs >= 500) || (ritmoBpm > 95 && den >= 0.75 && latenciaMs < 350);

    return {
      id_pregunta: this._preguntaActual, latencia_ms: latenciaMs, densidad_lexica: den,
      similitud_coseno: cosSim, incongruencia_detectada: inc,
      evaluacion_preliminar: inc ? (ritmoBpm > 95 ? "INCONGRUENCIA: DISCURSO CALMADO BAJO ESTRÉS" : "INCONGRUENCIA: FATIGA OCULTA") : (latenciaMs > 450 ? "FATIGA COGNITIVA LEVE" : "COHERENTE: ESTADO NOMINAL"),
      respuesta_asistente: inc ? "Comandante, detecto una discrepancia entre tus bioseñales y tu reporte. Tómate una pausa de relajación." : "Reporte asentado con éxito en la bitácora operativa de vuelo.",
      estado_cognitivo: inc ? "INCONGRUENCIA_CRITICA" : "NOMINAL"
    };
  }

  _actualizarBadgesTelemetria(res) {
    const s = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
    s("psychMetricLatency", `${Math.round(res.latencia_ms)} ms`);
    s("psychMetricDensity", res.densidad_lexica.toFixed(2));
    s("psychMetricCosSim", res.similitud_coseno.toFixed(3));
    const sum = document.getElementById("psychEvalSummary");
    if (sum) {
      sum.innerText = res.incongruencia_detectada ? "INCONGRUENCIA" : "COHERENTE";
      sum.style.color = res.incongruencia_detectada ? "var(--neon-red)" : "var(--neon-green)";
    }
  }

  _actualizarBadgeEstado(txt, cls) {
    const b = document.getElementById("psychStatusBadge");
    if (b) { b.innerText = txt; b.className = `badge-status ${cls}`; }
  }

  _agregarMensaje(remitente, contenido, estilo) {
    const box = document.getElementById("assistantChatBox");
    if (!box) return;
    const div = document.createElement("div");
    const color = estilo === "astronauta" ? "#ffffff" : (estilo === "alerta" ? "var(--neon-red)" : "var(--neon-cyan)");
    const bg = estilo === "astronauta" ? "rgba(255,255,255,0.06)" : (estilo === "alerta" ? "rgba(255,34,85,0.08)" : "rgba(0,240,255,0.06)");
    div.style.cssText = `padding:8px 12px; background:${bg}; border-left:3px solid ${color}; border-radius:0 6px 6px 0;`;
    div.innerHTML = `<strong style="color:${color}; font-family:var(--font-hud);">${remitente}:</strong> ${contenido}`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }

  _initVoz() {
    const Sp = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Sp) return;
    try {
      this._reconocimientoVoz = new Sp();
      this._reconocimientoVoz.lang = "es-ES";
      this._reconocimientoVoz.onresult = (e) => {
        const inp = document.getElementById("inputPsychText");
        if (inp) inp.value = e.results[0][0].transcript;
        this.enviarRespuestaPsicologica();
      };
      this._reconocimientoVoz.onend = () => this._setMicState(false);
      this._reconocimientoVoz.onerror = () => this._setMicState(false);
    } catch (e) { console.debug("Speech not initialized:", e); }
  }

  _setMicState(activo) {
    this._escuchandoVoz = activo;
    const btn = document.getElementById("btnPsychMic");
    if (btn) btn.innerText = activo ? "🔴" : "🎙️";
  }

  activarDictadoVoz() {
    this._sound?.reproducirClick?.();
    if (!this._reconocimientoVoz) {
      alert("🎙️ Dictado por voz no disponible en este navegador. Utiliza el teclado o los botones de opción.");
      return;
    }
    if (this._escuchandoVoz) {
      this._reconocimientoVoz.stop();
      this._setMicState(false);
    } else {
      try {
        this._reconocimientoVoz.start();
        this._setMicState(true);
      } catch (e) { this._setMicState(false); }
    }
  }

  toggleGuiaRespiracion() {
    this._sound?.reproducirClick?.();
    const circle = document.getElementById("breathingPacerCircle");
    const text = document.getElementById("breathingPacerText");
    const btn = document.getElementById("btnBreathingPacer");

    if (this._respirando) {
      clearInterval(this._temporizadorRespiracion);
      this._respirando = false;
      if (circle) { circle.innerText = "4s"; circle.style.transform = "scale(1)"; }
      if (text) text.innerHTML = '<span style="color:var(--neon-cyan); font-weight:bold;">GUÍA 4-4-6 EN ESPERA</span><br>Inhala 4s · Sostén 4s · Exhala 6s';
      if (btn) btn.innerText = "🧘 INICIAR RELAJACIÓN";
      return;
    }

    this._respirando = true;
    if (btn) btn.innerText = "⏸️ PAUSAR GUÍA";
    let seg = 4, fase = "inhala";

    const paso = () => {
      if (!this._respirando) return;
      if (circle) circle.innerText = `${seg}s`;

      if (fase === "inhala") {
        if (text) text.innerHTML = '<strong style="color:var(--neon-cyan);">INHALA PROFUNDO...</strong><br>Llena tus pulmones con calma';
        if (circle) circle.style.transform = `scale(${1 + (4 - seg) * 0.08})`;
        if (seg <= 0) { fase = "sosten"; seg = 4; }
      } else if (fase === "sosten") {
        if (text) text.innerHTML = '<strong style="color:var(--neon-amber);">SOSTÉN EL AIRE...</strong><br>Mantén la serenidad';
        if (circle) circle.style.transform = "scale(1.32)";
        if (seg <= 0) { fase = "exhala"; seg = 6; }
      } else if (fase === "exhala") {
        if (text) text.innerHTML = '<strong style="color:var(--neon-green);">EXHALA LENTAMENTE...</strong><br>Libera tensión muscular';
        if (circle) circle.style.transform = `scale(${Math.max(1, 1.32 - (6 - seg) * 0.053)})`;
        if (seg <= 0) { fase = "inhala"; seg = 4; this.sumarExp(15); }
      }
      seg--;
    };
    paso();
    this._temporizadorRespiracion = setInterval(paso, 1000);
  }

  toggleMatrizTecnica() {
    this._sound?.reproducirClick?.();
    window.viewportController?.mostrarReglas();
  }

  actualizarHidratacion(esCrisis) {
    const opt = document.getElementById("hydroSegOptimo");
    const crit = document.getElementById("hydroSegCritico");
    const tOpt = document.getElementById("hydroTagOptimo");
    const tCrit = document.getElementById("hydroTagCritico");
    if (!opt || !crit) return;

    opt.style.background = esCrisis ? "rgba(0, 255, 136, 0.25)" : "#00ff88";
    opt.style.boxShadow = esCrisis ? "none" : "0 0 12px rgba(0, 255, 136, 0.6)";
    crit.style.background = esCrisis ? "#ff2255" : "rgba(255, 34, 85, 0.25)";
    crit.style.boxShadow = esCrisis ? "0 0 14px rgba(255, 34, 85, 0.8)" : "none";
    if (tOpt) { tOpt.innerText = esCrisis ? "Óptimo" : "▲ Óptimo"; tOpt.style.color = esCrisis ? "#94a3b8" : "var(--neon-green)"; }
    if (tCrit) { tCrit.innerText = esCrisis ? "▲ Crítico" : "Crítico"; tCrit.style.color = esCrisis ? "var(--neon-red)" : "#94a3b8"; }
  }
}

window.WellnessController = WellnessController;
