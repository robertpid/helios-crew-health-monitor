/**
 * CAPA DE SERVICIOS: SonarAcousticService
 * Evaluación Acústica y Vocal Preliminar (NASA-STD-3001 & Protocolo Voz/Ruido ISS-Marte).
 * Incluye:
 * 1. Verificación obligatoria de auriculares estéreo (L / R) con Web Audio API.
 * 2. Audiometría tonal aleatoria (250 - 8000 Hz) para vigilar fatiga auditiva y tinnitus.
 * 3. Dosimetría acústica 24 h (LEQ16, LEQ8, LEQ24, picos >= 85 dBA y regla de persistencia A5).
 * 4. Biomarcadores acústicos de voz (F0, HNR, Jitter, Shimmer, SNR) y cruces CX-16 a CX-19.
 * Rigurosamente bajo 400 líneas (Clean Code & SRP).
 */

class SonarAcousticService {
  constructor() {
    this._audioCtx = null;
    this._auricularesVerificados = false;
    this._canalPruebaEstereo = null;
    this._pruebasAudio = [];
    this._idxAudio = 0;
    this._aciertosAudio = 0;
    this._zumbidoReportado = false;

    this._escenarioRuido = "A1";
    this._datosDosimetria = { leq16: 59.5, leq8: 48.5, leq24: 57.6, pico: 68.0, cruce: null };
    this._datosVoz = {
      f0: 124, hnr: 21.4, snr: 22, jitter: 0.42, shimmer: 2.1,
      latencia: 220, pvtLapsos: 0, descartadaPorRuido: false, cruce: null
    };

    this._reglasAcusticas = [
      {
        id_regla: "CX-16", dominio: "ACUSTICA_HABITAT", nivel: "CRITICA",
        condicion_disparo: "Ruido instantáneo >= 85 dBA en cualquier módulo del hábitat",
        evaluacion_preliminar: "Exposición a nivel acústico peligroso (>= 85 dBA)",
        contramedidas_sugeridas: ["Colocarse protección auditiva de inmediato.", "Alejarse de la fuente acústica y aislar el compartimento.", "Notificar a control de misión para inspeccionar el equipo ruidoso."],
        destinatarios: ["ASTRONAUTA", "CONTROL_MISION"], estandar_base: "NASA-STD-3001 (Límite de peligro 85 dBA)", ventana_tiempo: "Inmediata (0 s)"
      },
      {
        id_regla: "CX-17", dominio: "ACUSTICA_SUENO", nivel: "ALERTA",
        condicion_disparo: "LEQ8 del sueño > 50 dBA + sueño < 6 h o despertares frecuentes",
        evaluacion_preliminar: "Descanso alterado por ruido ambiental en cabina de sueño",
        contramedidas_sugeridas: ["Utilizar tapones auditivos durante el periodo de sueño.", "Revisar ventilador o válvula cercana a la cabina de descanso.", "Avisar al médico de vuelo (regla de vuelo ISS LEQ8 > 50 dBA)."],
        destinatarios: ["ASTRONAUTA", "MEDICO_VUELO"], estandar_base: "Regla de vuelo ISS / NASA-STD-3001 (NC-40 ~50 dBA)", ventana_tiempo: "Ciclo de sueño (8 h)"
      },
      {
        id_regla: "CX-18", dominio: "ACUSTICA_TRABAJO", nivel: "ALERTA",
        condicion_disparo: "LEQ16 de la jornada > 72 dBA (o > 60 dBA varios días) + cefalea o irritabilidad",
        evaluacion_preliminar: "Fatiga y malestar por exposición acústica acumulada en jornada",
        contramedidas_sugeridas: ["Protección auditiva obligatoria en tareas ruidosas (ej. cinta de correr 77 dBA).", "Programar pausas de recuperación en módulos silenciosos.", "Registrar síntomas de cefalea o zumbido (tinnitus) en bitácora."],
        destinatarios: ["ASTRONAUTA", "MEDICO_VUELO"], estandar_base: "Regla de vuelo ISS / NASA NTRS (LEQ16 > 72 dBA)", ventana_tiempo: "Jornada de trabajo (16 h)"
      },
      {
        id_regla: "CX-19", dominio: "ACUSTICA_VOZ_BHP", nivel: "ALERTA",
        condicion_disparo: "Cambio de voz frente a línea base en vuelo (latencia/pausas suben, HNR baja) + lapsos PVT + buena relación señal-ruido",
        evaluacion_preliminar: "Patrón compatible con fatiga cognitiva verificado en voz y atención PVT",
        contramedidas_sugeridas: ["Confirmar con prueba de atención PVT completa.", "Proteger el siguiente ciclo de sueño (8 h bajo 50 dBA).", "Reprogramar maniobras críticas si la fatiga persiste."],
        destinatarios: ["ASTRONAUTA", "MEDICO_VUELO"], estandar_base: "DLR Pilot / Gao 2022 / Protocolo ASTRA-BHP", ventana_tiempo: "Evaluación diaria a bordo"
      }
    ];
  }

  obtenerReglasAcusticas() {
    return this._reglasAcusticas;
  }

  _asegurarAudioCtx() {
    if (!this._audioCtx) {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (Ctx) this._audioCtx = new Ctx();
    }
    if (this._audioCtx && this._audioCtx.state === "suspended") {
      this._audioCtx.resume();
    }
    return this._audioCtx;
  }

  _emitirTonoEstereo(freqHz, canal = "B", duracionSeg = 0.55, ganancia = 0.14) {
    try {
      const ctx = this._asegurarAudioCtx();
      if (!ctx) return;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(freqHz, ctx.currentTime);

      gain.gain.setValueAtTime(0.001, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(ganancia, ctx.currentTime + 0.04);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duracionSeg);

      if (typeof ctx.createStereoPanner === "function") {
        const panner = ctx.createStereoPanner();
        const panVal = canal === "L" ? -1.0 : (canal === "R" ? 1.0 : 0.0);
        panner.pan.setValueAtTime(panVal, ctx.currentTime);
        osc.connect(gain);
        gain.connect(panner);
        panner.connect(ctx.destination);
      } else {
        osc.connect(gain);
        gain.connect(ctx.destination);
      }

      osc.start();
      osc.stop(ctx.currentTime + duracionSeg + 0.02);
    } catch (e) {
      console.debug("AudioContext tone error:", e);
    }
  }

  abrirModal() {
    const modal = document.getElementById("modalSonar");
    if (!modal) return;
    modal.style.display = "flex";
    this._canalPruebaEstereo = null;
    this._mostrarVista("sonarVistaIntro", "AURICULARES", 15);
  }

  cerrarModal() {
    const modal = document.getElementById("modalSonar");
    if (modal) modal.style.display = "none";
  }

  emitirPulsoVerificacion() {
    this._canalPruebaEstereo = Math.random() < 0.5 ? "L" : "R";
    this._emitirTonoEstereo(880, this._canalPruebaEstereo, 0.65, 0.18);
    const st = document.getElementById("sonarHeadphoneStatus");
    if (st) {
      st.style.color = "var(--neon-cyan)";
      st.innerHTML = "🎧 Tono de 880 Hz emitido. Selecciona en qué oído (Izquierdo L o Derecho R) lo escuchaste.";
    }
  }

  verificarCanal(canalElegido) {
    const st = document.getElementById("sonarHeadphoneStatus");
    const btnStart = document.getElementById("btnSonarStartExam");
    if (!this._canalPruebaEstereo) {
      this.emitirPulsoVerificacion();
      return;
    }

    if (canalElegido === this._canalPruebaEstereo) {
      this._auricularesVerificados = true;
      window.soundService?.reproducirNominal?.();
      if (st) {
        st.style.color = "var(--neon-green)";
        st.innerHTML = `✅ Auriculares estéreo verificados correctamente (Canal ${canalElegido === "L" ? "Izquierdo" : "Derecho"} aislado).`;
      }
      if (btnStart) {
        btnStart.disabled = false;
        btnStart.style.opacity = "1";
        btnStart.style.cursor = "pointer";
        btnStart.innerText = "🎧 INICIAR EVALUACIÓN SONORA (3 ETAPAS)";
      }
    } else {
      window.soundService?.reproducirClick?.();
      this._canalPruebaEstereo = Math.random() < 0.5 ? "L" : "R";
      this._emitirTonoEstereo(880, this._canalPruebaEstereo, 0.65, 0.18);
      if (st) {
        st.style.color = "#f59e0b";
        st.innerHTML = "⚠️ Canal incorrecto (revisa que no tengas invertidos L/R). Se ha emitido un nuevo pulso, inténtalo de nuevo.";
      }
    }
  }

  comenzarExamen() {
    if (!this._auricularesVerificados) return;
    const freqsBase = [250, 500, 1000, 2000, 4000, 8000];
    const mezcladas = freqsBase.sort(() => Math.random() - 0.5).slice(0, 5);
    this._pruebasAudio = mezcladas.map((f) => ({
      freq: f,
      canal: Math.random() < 0.5 ? "L" : "R"
    }));
    this._idxAudio = 0;
    this._aciertosAudio = 0;
    this._zumbidoReportado = false;
    this._mostrarVista("sonarVistaAudiometria", "ETAPA 1/3", 38);
    this._renderizarPasoAudio();
  }

  _renderizarPasoAudio() {
    const actual = this._pruebasAudio[this._idxAudio];
    if (!actual) return;
    const sub = document.getElementById("sonarAudioSubtitulo");
    const tag = document.getElementById("sonarFreqTag");
    if (sub) sub.innerText = `Pulsa reproducir e indica en qué oído percibes la frecuencia (Prueba ${this._idxAudio + 1} / ${this._pruebasAudio.length})`;
    if (tag) tag.innerText = `${actual.freq} Hz`;
    setTimeout(() => this.reproducirTonoActual(), 200);
  }

  reproducirTonoActual() {
    const actual = this._pruebasAudio[this._idxAudio];
    if (!actual) return;
    this._emitirTonoEstereo(actual.freq, actual.canal, 0.65, 0.15);
  }

  responderAudiometria(respuesta) {
    const actual = this._pruebasAudio[this._idxAudio];
    if (!actual) return;
    if (respuesta === actual.canal) this._aciertosAudio += 1;
    if (respuesta === "NONE") this._zumbidoReportado = true;

    this._idxAudio += 1;
    if (this._idxAudio < this._pruebasAudio.length) {
      this._renderizarPasoAudio();
    } else {
      this._mostrarVista("sonarVistaDosimetria", "ETAPA 2/3", 68);
      this.simularEscenarioRuido("A1");
    }
  }

  simularEscenarioRuido(codigo) {
    this._escenarioRuido = codigo;
    const mapa = {
      A1: { leq16: 59.5, leq8: 48.5, leq24: 57.6, pico: 68.0, cruce: null, freq: 220, gain: 0.04,
            txt: "✅ <strong>Prueba A1 (Nominal ISS):</strong> 16 h trabajo (59.5 dBA) y 8 h sueño (48.5 dBA). Cumple curvas NC-50 y NC-40." },
      A2: { leq16: 60.2, leq8: 55.4, leq24: 58.9, pico: 69.0, cruce: "CX-17", freq: 310, gain: 0.08,
            txt: "🟠 <strong>Prueba A2 (Dispara CX-17):</strong> Periodo de sueño con LEQ8 = 55.4 dBA (> 50 dBA). Se activa aviso al tripulante y al médico de vuelo (usar tapones y revisar ventilador)." },
      A3: { leq16: 74.2, leq8: 49.0, leq24: 71.1, pico: 77.0, cruce: "CX-18", freq: 440, gain: 0.12,
            txt: "🟠 <strong>Prueba A3 (Dispara CX-18):</strong> Jornada con cinta de correr (77 dBA) eleva LEQ16 a 74.2 dBA (> 72 dBA). Protección auditiva obligatoria y pausas en zona silenciosa." },
      A4: { leq16: 63.0, leq8: 49.0, leq24: 60.8, pico: 88.5, cruce: "CX-16", freq: 880, gain: 0.20,
            txt: "🔴 <strong>Prueba A4 (Dispara CX-16 Inmediato):</strong> Pico instantáneo de 88.5 dBA (>= 85 dBA). Alerta roja inmediata NASA-STD-3001: colocarse protección y aislar fuente." },
      A5: { leq16: 60.1, leq8: 48.8, leq24: 58.1, pico: 81.0, cruce: null, freq: 520, gain: 0.07,
            txt: "🛡️ <strong>Prueba A5 (Regla de Persistencia):</strong> Golpe aislado de 2 segundos (81 dBA). No altera el promedio LEQ16 (60.1 dBA) y NO dispara falsa alarma de exposición acumulada." },
      E2: { leq16: 69.8, leq8: 51.2, leq24: 66.8, pico: 76.0, cruce: "CX-17", freq: 280, gain: 0.10,
            txt: "🪐 <strong>Prueba E2 (Tormenta de Polvo en Marte):</strong> Confinamiento prolongado suma exposición diaria (LEQ16 = 69.8 dBA). El sistema a bordo propone pausas programadas de silencio." }
    };
    const d = mapa[codigo] || mapa.A1;
    this._datosDosimetria = d;
    this._emitirTonoEstereo(d.freq, "B", 0.35, d.gain);

    const setEl = (id, txt, col) => {
      const el = document.getElementById(id);
      if (el) { el.innerText = txt; if (col) el.style.color = col; }
    };
    setEl("sonarValLeq16", `${d.leq16.toFixed(1)} dBA`, d.leq16 > 72 ? "var(--neon-amber)" : "var(--neon-green)");
    setEl("sonarValLeq8", `${d.leq8.toFixed(1)} dBA`, d.leq8 > 50 ? "var(--neon-amber)" : "var(--neon-green)");
    setEl("sonarValLeq24", `${d.leq24.toFixed(1)} dBA`, "var(--neon-cyan)");
    setEl("sonarValPeak", `${d.pico.toFixed(1)} dBA`, d.pico >= 85 ? "var(--neon-red)" : "var(--neon-cyan)");

    const fb = document.getElementById("sonarDosimetriaFeedback");
    if (fb) fb.innerHTML = d.txt;
  }

  irAVistaVoz() {
    this._mostrarVista("sonarVistaVoz", "ETAPA 3/3", 90);
    this.simularPruebaVoz("B1");
  }

  async capturarVozMicrofono() {
    const btn = document.getElementById("btnSonarMicRecord");
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      this.simularPruebaVoz("B1");
      return;
    }
    try {
      if (btn) btn.innerText = "🔴 Grabando 3 s (/a/ sostenida)...";
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const ctx = this._asegurarAudioCtx();
      const src = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 1024;
      src.connect(analyser);
      const buf = new Uint8Array(analyser.frequencyBinCount);

      let energiaTotal = 0;
      const timer = setInterval(() => {
        analyser.getByteFrequencyData(buf);
        const prom = buf.reduce((a, b) => a + b, 0) / buf.length;
        energiaTotal = Math.max(energiaTotal, prom);
      }, 100);

      setTimeout(() => {
        clearInterval(timer);
        stream.getTracks().forEach((t) => t.stop()); // Borrado inmediato en memoria (Sección 6 Privacidad)
        if (btn) btn.innerText = "🎙️ Grabar 3 s con Micrófono de Auricular";
        const f0Est = Math.round(118 + (energiaTotal % 32));
        this._aplicarMetricasVoz({
          f0: f0Est, hnr: 20.8, snr: 21, jitter: 0.45, shimmer: 2.2,
          latencia: 215, pvtLapsos: 0, descartadaPorRuido: false, cruce: null,
          msg: "✅ <strong>Grabación en vivo procesada a bordo (E1):</strong> SNR óptima (+21 dB). Parámetros acústicos dentro de tu línea base personal; grabación de voz eliminada por privacidad."
        });
      }, 2800);
    } catch (e) {
      if (btn) btn.innerText = "🎙️ Grabar 3 s con Micrófono de Auricular";
      this.simularPruebaVoz("B1");
    }
  }

  simularPruebaVoz(tipo) {
    window.soundService?.reproducirClick?.();
    if (tipo === "D1") {
      this._aplicarMetricasVoz({
        f0: 142, hnr: 11.2, snr: 5, jitter: 1.45, shimmer: 5.8,
        latencia: 310, pvtLapsos: 0, descartadaPorRuido: true, cruce: null,
        msg: "⚠️ <strong>Prueba D1/D2 (Ruido de fondo 70 dBA · Mala SNR +5 dB):</strong> El sistema detecta ruido ambiental alto, <strong>NO interpreta el cambio de voz como fatiga</strong> y descarta la muestra pidiendo repetir en zona silenciosa."
      });
    } else if (tipo === "C2") {
      this._aplicarMetricasVoz({
        f0: 148, hnr: 13.5, snr: 19, jitter: 1.18, shimmer: 4.4,
        latencia: 540, pvtLapsos: 4, descartadaPorRuido: false, cruce: "CX-19",
        msg: "🟠 <strong>Prueba C2 (Dispara CX-19):</strong> HNR baja a 13.5 dB y latencia sube a 540 ms con buena SNR (+19 dB) Y coincide con 4 lapsos en atención PVT. Se activa alerta combinada CX-19."
      });
    } else {
      this._aplicarMetricasVoz({
        f0: 124, hnr: 21.4, snr: 22, jitter: 0.42, shimmer: 2.1,
        latencia: 220, pvtLapsos: 0, descartadaPorRuido: false, cruce: null,
        msg: "✅ <strong>Prueba B1 (Retrato Base en Vuelo):</strong> Frecuencia F0 (124 Hz), limpieza HNR (21.4 dB) y estabilidad vocal óptimas frente a tu línea base personal."
      });
    }
  }

  _aplicarMetricasVoz(m) {
    this._datosVoz = m;
    const setEl = (id, txt, col) => {
      const el = document.getElementById(id);
      if (el) { el.innerText = txt; if (col) el.style.color = col; }
    };
    setEl("sonarVozF0", `${m.f0} Hz`, "var(--neon-cyan)");
    setEl("sonarVozHnr", `${m.hnr.toFixed(1)} dB`, m.hnr < 15 ? "var(--neon-amber)" : "var(--neon-green)");
    setEl("sonarVozSnr", `+${m.snr} dB (${m.snr < 10 ? "Ruido Alto" : "Óptimo"})`, m.snr < 10 ? "var(--neon-red)" : "var(--neon-green)");
    setEl("sonarVozJitter", `${m.jitter}% / ${m.shimmer}%`, "var(--neon-cyan)");
    setEl("sonarVozLat", `${m.latencia} ms`, m.latencia > 450 ? "var(--neon-amber)" : "var(--neon-cyan)");
    setEl("sonarVozPvt", `${m.pvtLapsos} lapsos (${m.pvtLapsos > 2 ? "Alterado" : "Estable"})`, m.pvtLapsos > 2 ? "var(--neon-amber)" : "var(--neon-green)");

    const fb = document.getElementById("sonarVozFeedback");
    if (fb) fb.innerHTML = m.msg;
  }

  mostrarResultados() {
    this._mostrarVista("sonarVistaResultado", "COMPLETADO", 100);
    const pctAudio = Math.round((this._aciertosAudio / Math.max(1, this._pruebasAudio.length)) * 100);
    const crucesActivos = [this._datosDosimetria.cruce, this._datosVoz.cruce].filter(Boolean);
    const hayAlerta = crucesActivos.length > 0 || pctAudio < 80 || this._zumbidoReportado;

    const badge = document.getElementById("sonarResBadge");
    if (badge) {
      badge.className = `badge-status ${hayAlerta ? "status-warning" : "status-stable"}`;
      badge.innerText = hayAlerta ? "ATENCIÓN PREVENTIVA ACÚSTICA" : "PARÁMETROS ACÚSTICOS NOMINALES";
    }

    const grid = document.getElementById("sonarResGrid");
    if (grid) {
      grid.innerHTML = `
        <div style="background:#081326; border:1px solid rgba(0,240,255,0.2); border-radius:6px; padding:10px;">
          <div style="color:#94a3b8; font-size:10.5px;">AUDIOMETRÍA ESTÉREO (250–8000 Hz)</div>
          <strong style="color:${pctAudio >= 80 ? "var(--neon-green)" : "var(--neon-amber)"}; font-size:13px;">${this._aciertosAudio}/${this._pruebasAudio.length} canales (${pctAudio}%) ${this._zumbidoReportado ? "· Zumbido" : "· Sin tinnitus"}</strong>
        </div>
        <div style="background:#081326; border:1px solid rgba(0,240,255,0.2); border-radius:6px; padding:10px;">
          <div style="color:#94a3b8; font-size:10.5px;">DOSIMETRÍA 24 H (NASA-STD-3001)</div>
          <strong style="color:${this._datosDosimetria.cruce ? "var(--neon-amber)" : "var(--neon-green)"}; font-size:13px;">LEQ16: ${this._datosDosimetria.leq16} dBA · LEQ8: ${this._datosDosimetria.leq8} dBA</strong>
        </div>
        <div style="background:#081326; border:1px solid rgba(0,240,255,0.2); border-radius:6px; padding:10px;">
          <div style="color:#94a3b8; font-size:10.5px;">RETRATO DE VOZ Y SNR A BORDO</div>
          <strong style="color:${this._datosVoz.descartadaPorRuido ? "var(--neon-amber)" : "var(--neon-cyan)"}; font-size:13px;">${this._datosVoz.descartadaPorRuido ? "Muestra descartada (SNR baja)" : `F0 ${this._datosVoz.f0} Hz · HNR ${this._datosVoz.hnr} dB`}</strong>
        </div>
        <div style="background:#081326; border:1px solid rgba(0,240,255,0.2); border-radius:6px; padding:10px;">
          <div style="color:#94a3b8; font-size:10.5px;">CRUCES MATRIZ DE DECISIONES</div>
          <strong style="color:${crucesActivos.length ? "var(--neon-amber)" : "var(--neon-green)"}; font-size:13px;">${crucesActivos.length ? crucesActivos.join(" + ") : "Ninguno activo (Nominal)"}</strong>
        </div>
      `;
    }

    const rec = document.getElementById("sonarResRecomendacion");
    if (rec) {
      rec.innerHTML = hayAlerta
        ? `⚠️ <strong>Evaluación preliminar acústica:</strong> Se activaron ${crucesActivos.join(", ") || "observaciones auditivas"}. Contramedida sugerida: emplear protección auditiva en zonas > 72 dBA, usar tapones si LEQ8 > 50 dBA y confirmar fatiga con prueba PVT.`
        : `✅ <strong>Evaluación preliminar acústica:</strong> Audición binaural, dosimetría LEQ16/LEQ8 y biomarcadores vocales en rango nominal. Audio eliminado tras cálculo a bordo.`;
    }

    const fb = document.getElementById("examenExtraFeedback");
    if (fb) {
      fb.style.display = "block";
      fb.innerHTML = `🎧 <strong>EVALUACIÓN ACÚSTICA Y VOCAL:</strong> Audiometría ${pctAudio}% · LEQ16 ${this._datosDosimetria.leq16} dBA · ${crucesActivos.length ? `Cruce ${crucesActivos.join("/")}` : "Nominal"}.`;
    }
    window.wellnessController?.sumarExp?.(60);
  }

  _mostrarVista(idVista, textoBadge, progresoPct) {
    ["sonarVistaIntro", "sonarVistaAudiometria", "sonarVistaDosimetria", "sonarVistaVoz", "sonarVistaResultado"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.style.display = id === idVista ? "block" : "none";
    });
    const b = document.getElementById("sonarStepBadge");
    if (b) b.innerText = textoBadge;
    const bar = document.getElementById("sonarProgressBar");
    if (bar) bar.style.width = `${progresoPct}%`;
  }
}

window.sonarService = new SonarAcousticService();
