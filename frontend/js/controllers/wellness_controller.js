/**
 * CAPA DE CONTROLADORES: WellnessController
 * Maneja la interacción de Bienestar, Rutinas, Asistente y Gamificación.
 * Protocolo de Evaluación Psicológica y Cadencia Vocal ASTRA (NASA-BHP).
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
    this._tiempoPrimerCaracter = null;
    this._tiempoInicioLocucion = null;
    this._wpmCalculado = null;
    this._reconocimientoVoz = null;
    this._escuchandoVoz = false;
    this._evaluando = false;
    this._protocoloCompletado = false;
    this._enCurso = false;
    this._timerCompletado = null;

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
        chips: ["Excelente moral, comunicación fluida con Houston.", "Bien, aquí estamos relajados y en orden.", "El aislamiento se hace notar hoy, requiero pausa breve."]
      }
    ];

    this._initVoz();
    setTimeout(() => this._prepararInicio(), 200);
  }

  _prepararInicio() {
    this._actualizarChips();
    const input = document.getElementById("inputPsychText");
    if (input) {
      input.addEventListener("input", () => {
        if (!this._tiempoPrimerCaracter) this._tiempoPrimerCaracter = performance.now();
      });
    }
  }

  avanzarTarea(tipo) {
    this._sound?.reproducirClick?.();
    let act = (this._tareasEstado[tipo] || 0) + 20;
    if (act > 100) act = 20;
    this._tareasEstado[tipo] = act;
    const cap = tipo.charAt(0).toUpperCase() + tipo.slice(1);
    const tagVal = document.getElementById(`taskPercent${cap}`), tagBar = document.getElementById(`taskBar${cap}`);
    if (tagVal) tagVal.innerText = `${act}%`;
    if (tagBar) tagBar.style.width = `${act}%`;
    if (tipo === "ejercicio") window.fitService?.ajustarMetaEjercicio?.(act >= 100);
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
    const lvlTag = document.getElementById("gamificationLevelTag"), expTag = document.getElementById("gamificationExpTag"), expBar = document.getElementById("gamificationExpBar");
    if (lvlTag) lvlTag.innerText = `NIVEL ${this._gamificacion.nivel}`;
    if (expTag) expTag.innerHTML = `EXP <strong style="color:var(--neon-green);">${this._gamificacion.exp}</strong> / ${this._gamificacion.expMax}`;
    if (expBar) expBar.style.width = `${Math.min(100, Math.round((this._gamificacion.exp / this._gamificacion.expMax) * 100))}%`;
  }

  iniciarExamenOftalmico() {
    this._sound?.reproducirClick?.();
    if (window.oftalmicoService?.abrirModal) {
      window.oftalmicoService.abrirModal();
    } else {
      this._mostrarFeedback("👁️ <strong>EVALUACIÓN OFTÁLMICA:</strong> Abriendo módulo SANS...");
    }
  }
  iniciarExamenSonar() { this._sound?.reproducirClick?.(); this._mostrarFeedback("👂 <strong>BARRIDO SONAR / AUDIOMETRÍA:</strong> 250-8000 Hz evaluadas. Ruido de cabina en 58 dBA nominal."); }
  _mostrarFeedback(html) { const fb = document.getElementById("examenExtraFeedback"); if (!fb) return; fb.style.display = "block"; fb.innerHTML = html; setTimeout(() => { if (fb) fb.style.display = "none"; }, 6000); }
  sincronizarCorreo() { this._sound?.reproducirClick?.(); alert("📡 SINCRONIZACIÓN DSN COMPLETADA: Enlace activo con Houston. 0 mensajes pendientes."); }

  // ==============================================================================
  // PROTOCOLO DE EVALUACIÓN PSICOLÓGICA Y CADENCIA VOCAL (SISTEMA ASTRA)
  // ==============================================================================
  iniciarProtocoloPsicologico() {
    this._sound?.reproducirClick?.();
    if (this._enCurso) {
      this._finalizarProtocolo();
      return;
    }
    this._enCurso = true;
    this._preguntaActual = 1;
    this._protocoloCompletado = false;
    this._tiempoPrimerCaracter = null;
    this._actualizarBotonProtocolo(true);
    const box = document.getElementById("assistantChatBox");
    if (box) {
      box.innerHTML = `<div style="padding:8px 12px; background:rgba(0,240,255,0.06); border-left:3px solid var(--neon-cyan); border-radius:0 6px 6px 0;"><strong style="color:var(--neon-cyan); font-family:var(--font-hud);">SISTEMA ASTRA:</strong> Protocolo NASA-BHP Sol 120 iniciado. Por favor responde a las siguientes consultas de rutina para el registro de cabina.</div>`;
    }
    this._presentarPregunta();
  }

  _actualizarBotonProtocolo(activo) {
    const btn = document.getElementById("btnStartPsychProtocol");
    if (btn) {
      btn.innerText = activo ? "⏹️ FINALIZAR" : "📋 PROTOCOLO BHP";
      btn.className = activo ? "btn-hud btn-hud-danger" : "btn-hud";
    }
  }

  _presentarPregunta() {
    const item = this._preguntasBHP.find(p => p.id === this._preguntaActual);
    if (!item) return;
    this._tiempoPrimerCaracter = null;
    this._actualizarBadgeEstado(`PASO ${item.id}/3`, "status-stable");
    this._agregarMensaje("SISTEMA ASTRA", `<strong>Pregunta ${item.id}/3 (${item.cat}):</strong> ${item.texto}`, "astra");
    this._actualizarChips();
    const input = document.getElementById("inputPsychText");
    if (input) { input.value = ""; input.focus(); }
  }

  _actualizarChips() {
    const item = this._preguntasBHP.find(p => p.id === this._preguntaActual) || this._preguntasBHP[0];
    const cntChips = document.getElementById("psychSuggestionsContainer");
    if (cntChips && item) {
      const chipsHtml = item.chips.map(c => `
        <button class="btn-hud" onclick="window.hudController.seleccionarChipSugerido('${c.replace(/'/g, "\\'")}')" style="font-size:10px; padding:4px 8px; text-transform:none;">${c}</button>
      `).join("");
      const finHtml = `<button class="btn-hud" onclick="window.hudController.iniciarProtocoloPsicologico()" style="font-size:10px; padding:4px 8px; color:#94a3b8; border-color:#475569;" title="Cerrar y finalizar evaluación">⏹️ Finalizar</button>`;
      cntChips.innerHTML = chipsHtml + finHtml;
    }
  }

  seleccionarChipSugerido(texto) {
    const input = document.getElementById("inputPsychText");
    if (input) input.value = texto;
    this._wpmCalculado = Math.round(132 + Math.random() * 14);
    this.enviarRespuestaPsicologica();
  }

  async enviarRespuestaPsicologica() {
    if (this._evaluando) return;
    const input = document.getElementById("inputPsychText");
    const texto = input ? input.value.trim() : "";
    if (!texto) return;

    if (this._protocoloCompletado) {
      this._preguntaActual = 1;
      this._protocoloCompletado = false;
      this._enCurso = true;
      this._actualizarBotonProtocolo(true);
    }

    this._sound?.reproducirClick?.();
    const palabras = texto.split(/\s+/).filter(Boolean);
    const numPal = Math.max(1, palabras.length);

    let wpm = this._wpmCalculado;
    this._wpmCalculado = null;
    if (!wpm) {
      if (this._tiempoPrimerCaracter) {
        const seg = Math.max(0.6, (performance.now() - this._tiempoPrimerCaracter) / 1000);
        wpm = Math.min(185, Math.max(65, Math.round((numPal / seg) * 60 * 1.6)));
        this._tiempoPrimerCaracter = null;
      } else {
        wpm = Math.round(128 + Math.random() * 14);
      }
    }

    this._evaluando = true;
    this._agregarMensaje("Astronauta", texto, "astronauta");
    if (input) input.value = "";

    const telemetria = window.stateManager?._state?.telemetria;
    const ritmoBpm = telemetria?.fisiologia?.ritmo_cardiaco_bpm || 72.0;

    let res = await window.telemetryService?.evaluarRespuestaPsicologica?.({
      id_pregunta: this._preguntaActual, texto_respuesta: texto,
      latencia_ms: 2000.0, palabras_por_minuto: wpm,
      ritmo_cardiaco_bpm: ritmoBpm, cuerpo_en_panico: ritmoBpm > 95.0
    });

    if (!res) res = this._calcularMetricasLocal(texto, wpm, ritmoBpm);
    this._actualizarBadgesTelemetria(res);

    window.stateManager?.actualizarCognicion?.({
      latencia_ms: res.cadencia_ms_palabra || 440, densidad_lexica: res.densidad_lexica,
      similitud_coseno: res.similitud_coseno,
      incongruencia_detectada: Boolean(res.incongruencia_detectada),
      alerta_astra: res.incongruencia_detectada ? res.evaluacion_preliminar : null
    });

    setTimeout(() => {
      this._agregarMensaje("SISTEMA ASTRA", res.respuesta_asistente, res.incongruencia_detectada ? "alerta" : "nominal");
      this.sumarExp(25);
      this._evaluando = false;

      if (this._enCurso && this._preguntaActual < 3) {
        this._preguntaActual += 1;
        setTimeout(() => this._presentarPregunta(), 900);
      } else {
        this._finalizarProtocolo();
      }
    }, 350);
  }

  _finalizarProtocolo() {
    this._enCurso = false;
    this._protocoloCompletado = true;
    this._actualizarBotonProtocolo(false);
    this._actualizarBadgeEstado("COMPLETADO", "status-stable");
    const esCrit = window.stateManager?._state?.telemetria?.cognicion?.incongruencia_detectada;
    const banner = `<div style="padding:10px 14px; background:${esCrit ? "rgba(255,34,85,0.12)" : "rgba(0,255,136,0.1)"}; border:1px solid ${esCrit ? "var(--neon-red)" : "var(--neon-green)"}; border-radius:6px; margin-top:6px;"><strong style="color:${esCrit ? "var(--neon-red)" : "var(--neon-green)"}; font-family:var(--font-hud);">REGISTRO OPERACIONAL COMPLETADO:</strong><br>${esCrit ? "⚠️ Parámetros requieren atención. Sugerencia: Iniciar relajación 4-4-6 y pausa preventiva." : "✅ Estado operacional nominal. Apto para el programa de actividades del Sol 120."}</div>`;
    const box = document.getElementById("assistantChatBox");
    if (box) { box.insertAdjacentHTML("beforeend", banner); box.scrollTop = box.scrollHeight; }

    const cntChips = document.getElementById("psychSuggestionsContainer");
    if (cntChips) {
      cntChips.innerHTML = `<button class="btn-hud" onclick="window.hudController.iniciarProtocoloPsicologico()" style="font-size:10px; padding:4px 10px;">🔄 Iniciar nuevo chequeo BHP</button>`;
    }

    if (this._timerCompletado) clearTimeout(this._timerCompletado);
    this._timerCompletado = setTimeout(() => {
      this._actualizarBadgeEstado("LISTO", "status-stable");
    }, 3500);
  }

  _calcularMetricasLocal(texto, wpm, ritmoBpm) {
    const pal = texto.toLowerCase().split(/\s+/).filter(Boolean);
    const esFatiga = ["sueno", "sueño", "cansado", "fatiga", "lento", "retraso", "sobrecarga", "aislamiento"].some(k => texto.toLowerCase().includes(k));
    const esNominal = ["bien", "orden", "normal", "control", "enfocado", "despejado", "optimo", "óptimo", "excelente", "cero", "firme", "sin", "relajados", "relajado"].some(k => texto.toLowerCase().includes(k));
    let den = Math.round(Math.min(1.0, Math.max(0.35, esNominal ? 0.92 : (esFatiga ? 0.78 : (pal.length > 0 ? (new Set(pal).size / pal.length) : 0.4)))) * 100) / 100;
    const v = [wpm / 135.0, den], dot = v[0] + v[1];
    const cosSim = Math.round((dot / (Math.sqrt(v[0] ** 2 + v[1] ** 2) * Math.SQRT2)) * 1000) / 1000;
    const inc = (ritmoBpm > 95 && esNominal) || wpm < 85;

    let evalPrelim = "COHERENTE: ESTADO OPERACIONAL NOMINAL", respuesta = "Recibido, Comandante. Reporte asentado en la bitácora operacional de cabina.";
    if (inc) {
      evalPrelim = ritmoBpm > 95 ? "INCONGRUENCIA: DISCURSO EN CALMA BAJO ACTIVACIÓN FISIOLÓGICA" : "FATIGA OPERACIONAL DETECTADA";
      respuesta = ritmoBpm > 95
        ? "Comandante, los registros fisiológicos de cabina muestran activación de estrés durante tu reporte. Te recomendamos realizar una breve pausa activa y la guía de respiración 4-4-6."
        : "Comandante, registramos signos de fatiga y desgaste atencional acumulado en este reporte. Se sugiere hidratación de cabina y un receso preventivo de 15 minutos.";
    } else if (esFatiga) {
      evalPrelim = "FATIGA OPERACIONAL REPORTADA";
      respuesta = "Reporte de fatiga asentado en la bitácora operacional. Hidrátate con 500 ml y realiza una pausa preventiva de 15 minutos.";
    } else {
      const respMap = {
        1: "Recibido, Comandante. Comunicación clara y estado óptimo para las operaciones de vuelo.",
        2: "Excelente. Respuestas registradas dentro de los márgenes nominales esperados de la misión.",
        3: "Reporte Sol 120 asentado con éxito. Estado equilibrado y moral firme de la tripulación."
      };
      respuesta = respMap[this._preguntaActual] || respuesta;
    }
    return {
      id_pregunta: this._preguntaActual, palabras_por_minuto: Math.round(wpm),
      cadencia_ms_palabra: Math.round(60000 / wpm), densidad_lexica: den,
      similitud_coseno: cosSim, incongruencia_detectada: inc,
      evaluacion_preliminar: evalPrelim, respuesta_asistente: respuesta,
      estado_cognitivo: inc ? "INCONGRUENCIA_CRITICA" : (esFatiga ? "FATIGA_LEVE" : "NOMINAL")
    };
  }

  _actualizarBadgesTelemetria(res) {
    const s = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
    const wpm = res.palabras_por_minuto || 135;
    const ritmoTxt = wpm < 85 ? "LENTO" : (wpm > 175 ? "RÁPIDO" : "NOMINAL");
    s("psychMetricLatency", ritmoTxt);
    s("psychMetricDensity", (res.densidad_lexica || 0.95) >= 0.85 ? "ÓPTIMA" : "ESTABLE");
    s("psychMetricCosSim", (res.similitud_coseno || 0.98) >= 0.85 ? "NOMINAL" : "EN ATENCIÓN");
    const sum = document.getElementById("psychEvalSummary");
    if (sum) {
      sum.innerText = res.incongruencia_detectada ? "OBSERVACIÓN" : (res.estado_cognitivo === "FATIGA_LEVE" ? "FATIGA LEVE" : "NOMINAL");
      sum.style.color = res.incongruencia_detectada ? "var(--neon-red)" : (res.estado_cognitivo === "FATIGA_LEVE" ? "var(--neon-amber)" : "var(--neon-green)");
    }
  }

  _actualizarBadgeEstado(txt, cls) { const b = document.getElementById("psychStatusBadge"); if (b) { b.innerText = txt; b.className = `badge-status ${cls}`; } }

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
      this._reconocimientoVoz.onspeechstart = () => { this._tiempoInicioLocucion = performance.now(); };
      this._reconocimientoVoz.onresult = (e) => {
        const trans = e.results[0][0].transcript;
        const durSeg = Math.max(0.6, (performance.now() - (this._tiempoInicioLocucion || performance.now() - 1500)) / 1000);
        const nPal = trans.trim().split(/\s+/).filter(Boolean).length;
        this._wpmCalculado = Math.min(200, Math.max(60, Math.round((nPal / durSeg) * 60)));
        const inp = document.getElementById("inputPsychText");
        if (inp) inp.value = trans;
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
      try { this._tiempoInicioLocucion = performance.now(); this._reconocimientoVoz.start(); this._setMicState(true); } catch (e) { this._setMicState(false); }
    }
  }

  toggleGuiaRespiracion() {
    this._sound?.reproducirClick?.();
    const circle = document.getElementById("breathingPacerCircle"), text = document.getElementById("breathingPacerText"), btn = document.getElementById("btnBreathingPacer");
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
    if (window.fitService) {
      window.fitService._volumenMl = esCrisis ? 900 : 2200;
      window.fitService.renderizar();
    }
  }
}

window.WellnessController = WellnessController;
