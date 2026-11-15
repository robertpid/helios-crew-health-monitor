/**
 * ==============================================================================
 * CAPA DE CONTROLADORES: WellnessController
 * Maneja la interacción de la Ventana 3: Bienestar, Rutinas, Asistente y Gamificación.
 * ==============================================================================
 */

class WellnessController {
  constructor(soundService = null) {
    this._sound = soundService || window.soundService;
    this._tareasEstado = {
      meditacion: 100,
      estiramiento: 100,
      ejercicio: 60,
      hidratacion: 80
    };
    this._gamificacion = {
      nivel: 6,
      exp: 1320,
      expMax: 1500
    };
    this._temporizadorRespiracion = null;
    this._respirando = false;
  }

  avanzarTarea(tipo) {
    if (this._sound && this._sound.reproducirClick) {
      this._sound.reproducirClick();
    }
    let actual = this._tareasEstado[tipo] || 0;
    actual += 20;
    if (actual > 100) actual = 20;
    this._tareasEstado[tipo] = actual;

    const nombreCap = tipo.charAt(0).toUpperCase() + tipo.slice(1);
    const tagVal = document.getElementById(`taskPercent${nombreCap}`);
    const tagBar = document.getElementById(`taskBar${nombreCap}`);
    if (tagVal) tagVal.innerText = `${actual}%`;
    if (tagBar) tagBar.style.width = `${actual}%`;

    this.sumarExp(25);
  }

  sumarExp(puntos) {
    this._gamificacion.exp += puntos;
    if (this._gamificacion.exp >= this._gamificacion.expMax) {
      this._gamificacion.nivel += 1;
      this._gamificacion.exp -= this._gamificacion.expMax;
      this._gamificacion.expMax = Math.round(this._gamificacion.expMax * 1.25);
      if (this._sound && this._sound.reproducirNominal) {
        this._sound.reproducirNominal();
      }
    }

    const lvlTag = document.getElementById("gamificationLevelTag");
    const expTag = document.getElementById("gamificationExpTag");
    const expBar = document.getElementById("gamificationExpBar");

    if (lvlTag) lvlTag.innerText = `NIVEL ${this._gamificacion.nivel}`;
    if (expTag) expTag.innerHTML = `EXP <strong style="color:var(--neon-green);">${this._gamificacion.exp}</strong> / ${this._gamificacion.expMax}`;
    if (expBar) {
      const pct = Math.min(100, Math.round((this._gamificacion.exp / this._gamificacion.expMax) * 100));
      expBar.style.width = `${pct}%`;
    }
  }

  iniciarExamenOftalmico() {
    if (this._sound && this._sound.reproducirClick) this._sound.reproducirClick();
    const fb = document.getElementById("examenExtraFeedback");
    if (fb) {
      fb.style.display = "block";
      fb.innerHTML = "👁️ <strong>EVALUACIÓN OFTÁLMICA EN CURSO (SANS TEST):</strong> Evaluando fondo de ojo y refracción... Agudeza visual 20/20 nominal bilateral. Grado SANS: 0 (Sin edema papilar).";
      setTimeout(() => { if (fb) fb.style.display = "none"; }, 6000);
    }
  }

  iniciarExamenSonar() {
    if (this._sound && this._sound.reproducirClick) this._sound.reproducirClick();
    const fb = document.getElementById("examenExtraFeedback");
    if (fb) {
      fb.style.display = "block";
      fb.innerHTML = "👂 <strong>BARRIDO SONAR / AUDIOMETRÍA:</strong> Frecuencias 250 Hz - 8000 Hz evaluadas. Ruido de cabina en 58 dBA dentro de límites NASA STD-3001.";
      setTimeout(() => { if (fb) fb.style.display = "none"; }, 6000);
    }
  }

  sincronizarCorreo() {
    if (this._sound && this._sound.reproducirClick) this._sound.reproducirClick();
    alert("📡 SINCRONIZACIÓN DSN COMPLETADA: Enlace activo con Centro Espacial Johnson (Houston). 0 mensajes pendientes.");
  }

  toggleGuiaRespiracion() {
    if (this._sound && this._sound.reproducirClick) this._sound.reproducirClick();
    const circle = document.getElementById("breathingPacerCircle");
    const text = document.getElementById("breathingPacerText");
    const btn = document.getElementById("btnBreathingPacer");

    if (this._respirando) {
      clearInterval(this._temporizadorRespiracion);
      this._respirando = false;
      if (circle) {
        circle.innerText = "4s";
        circle.style.transform = "scale(1)";
      }
      if (text) text.innerHTML = '<span style="color:var(--neon-cyan); font-weight:bold;">GUÍA 4-4-6 EN ESPERA</span><br>Inhala 4s · Sostén 4s · Exhala 6s';
      if (btn) btn.innerText = "🧘 INICIAR RELAJACIÓN";
      return;
    }

    this._respirando = true;
    if (btn) btn.innerText = "⏸️ PAUSAR GUÍA";

    let segRestantes = 4;
    let fase = "inhala";

    const paso = () => {
      if (!this._respirando) return;
      if (circle) circle.innerText = `${segRestantes}s`;

      if (fase === "inhala") {
        if (text) text.innerHTML = '<strong style="color:var(--neon-cyan);">INHALA PROFUNDO...</strong><br>Llena tus pulmones con calma';
        if (circle) {
          const factor = 1 + (4 - segRestantes) * 0.08;
          circle.style.transform = `scale(${factor})`;
        }
        if (segRestantes <= 0) {
          fase = "sosten";
          segRestantes = 4;
        }
      } else if (fase === "sosten") {
        if (text) text.innerHTML = '<strong style="color:var(--neon-amber);">SOSTÉN EL AIRE...</strong><br>Mantén la serenidad';
        if (circle) circle.style.transform = "scale(1.32)";
        if (segRestantes <= 0) {
          fase = "exhala";
          segRestantes = 6;
        }
      } else if (fase === "exhala") {
        if (text) text.innerHTML = '<strong style="color:var(--neon-green);">EXHALA LENTAMENTE...</strong><br>Libera tensión muscular';
        if (circle) {
          const factor = 1.32 - (6 - segRestantes) * 0.053;
          circle.style.transform = `scale(${Math.max(1, factor)})`;
        }
        if (segRestantes <= 0) {
          fase = "inhala";
          segRestantes = 4;
          this.sumarExp(15);
        }
      }
      segRestantes--;
    };

    paso();
    this._temporizadorRespiracion = setInterval(paso, 1000);
  }

  responderAsistente(tipo) {
    if (this._sound && this._sound.reproducirClick) this._sound.reproducirClick();
    const box = document.getElementById("assistantChatBox");
    if (!box) return;

    const respuestaAstronauta = document.createElement("div");
    respuestaAstronauta.style.cssText = "padding:8px 12px; background:rgba(255,255,255,0.06); border-left:3px solid #ffffff; border-radius:0 6px 6px 0;";
    respuestaAstronauta.innerHTML = '<strong style="color:#ffffff; font-family:var(--font-hud);">Astronauta:</strong> Todo en orden en cabina. Me encuentro en control operativo y enfocado.';
    box.appendChild(respuestaAstronauta);

    setTimeout(() => {
      const respuestaHelios = document.createElement("div");
      respuestaHelios.style.cssText = "padding:8px 12px; background:rgba(0,255,136,0.08); border-left:3px solid var(--neon-green); border-radius:0 6px 6px 0;";
      respuestaHelios.innerHTML = '<strong style="color:var(--neon-green); font-family:var(--font-hud);">H.E.L.I.O.S.:</strong> Entendido, Comandante. Registro asentado en el diario de vuelo. Sus bioseñales se mantienen estables.';
      box.appendChild(respuestaHelios);
    }, 600);
  }

  toggleMatrizTecnica() {
    if (this._sound && this._sound.reproducirClick) this._sound.reproducirClick();
    const drawer = document.getElementById("martinaMatrixDrawer");
    const btnText = document.getElementById("btnTextMartinaToggle");
    if (!drawer) return;

    const visible = drawer.style.display === "block";
    drawer.style.display = visible ? "none" : "block";
    if (btnText) {
      btnText.innerText = visible
        ? "VER MATRIZ TÉCNICA DE DECISIÓN (15 CRUCES MARTINA)"
        : "OCULTAR MATRIZ TÉCNICA DE DECISIÓN";
    }
  }

  actualizarHidratacion(esCrisis) {
    const segOpt = document.getElementById("hydroSegOptimo");
    const segCrit = document.getElementById("hydroSegCritico");
    const tagOpt = document.getElementById("hydroTagOptimo");
    const tagCrit = document.getElementById("hydroTagCritico");

    if (segOpt && segCrit) {
      if (esCrisis) {
        segOpt.style.background = "rgba(0, 255, 136, 0.25)";
        segOpt.style.border = "1px solid rgba(0, 255, 136, 0.3)";
        segOpt.style.boxShadow = "none";

        segCrit.style.background = "#ff2255";
        segCrit.style.border = "1.5px solid #ffffff";
        segCrit.style.boxShadow = "0 0 14px rgba(255, 34, 85, 0.8)";

        if (tagOpt) { tagOpt.innerText = "Óptimo"; tagOpt.style.color = "#94a3b8"; tagOpt.style.fontWeight = "600"; }
        if (tagCrit) { tagCrit.innerText = "▲ Crítico"; tagCrit.style.color = "var(--neon-red)"; tagCrit.style.fontWeight = "800"; }
      } else {
        segOpt.style.background = "#00ff88";
        segOpt.style.border = "1.5px solid #ffffff";
        segOpt.style.boxShadow = "0 0 12px rgba(0, 255, 136, 0.6)";

        segCrit.style.background = "rgba(255, 34, 85, 0.25)";
        segCrit.style.border = "1px solid rgba(255, 34, 85, 0.4)";
        segCrit.style.boxShadow = "none";

        if (tagOpt) { tagOpt.innerText = "▲ Óptimo"; tagOpt.style.color = "var(--neon-green)"; tagOpt.style.fontWeight = "800"; }
        if (tagCrit) { tagCrit.innerText = "Crítico"; tagCrit.style.color = "#94a3b8"; tagCrit.style.fontWeight = "600"; }
      }
    }
  }
}

window.WellnessController = WellnessController;
