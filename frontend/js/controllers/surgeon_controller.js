/**
 * CAPA DE CONTROLADORES: SurgeonController
 * Gestiona la Consola Especializada del Cirujano de Vuelo (Dr. Marcus Vance).
 * Restringido estrictamente al rol CIRUJANO_VUELO.
 * Sincroniza signos vitales y resultados de exámenes (SANS, Sonar/Voz, FIT y ASTRA)
 * de cada astronauta (ASTRO-01 y ASTRO-02) y genera la matriz comparativa.
 * Rigurosamente bajo 400 líneas (Clean Code & SRP).
 */

class SurgeonController {
  constructor(stateManager = null, soundService = null, authService = null) {
    this._state = stateManager || window.stateManager;
    this._sound = soundService || window.soundService;
    this._auth = authService || window.authService;
    this._tripulanteActivo = "ASTRO-01";
    this._modoComparativo = false;

    this._pacientes = {
      "ASTRO-01": {
        id: "ASTRO-01",
        nombre: "Alex Mercer",
        rango: "Comandante A01",
        mision: "ARES-VI · SOL 120 · BIO-TELEMETRÍA ASTROSKIN EN TIEMPO REAL",
        estadoClinico: "COMPENSADO",
        fisiologia: {
          hr: 76, hrv: 42, bp: "118/76", pam: 90, spo2: 98, rpm: 14,
          temp: 36.6, skinTemp: 34.8, boneLoss: -1.8, ared: 100,
          fluid: "2.20 / 2.2 L", sleep: "7.2 h (90%)"
        },
        examenes: {
          sans: {
            estado: "ESTABLE",
            resumen: "20/20 Nominal",
            agudeza: "20/20 (100%)",
            contraste: "100% (8/8)",
            amsler: "Sin distorsión",
            ishihara: "7/7 láminas"
          },
          sonar: {
            estado: "NOMINAL",
            resumen: "59.5 dBA OK",
            audiometria: "5/5 (Sin tinnitus)",
            leq16: "59.5 dBA",
            leq8: "48.5 dBA",
            voz: "F0 124 Hz · HNR 21.4 dB"
          },
          astra: {
            estado: "COHERENTE",
            resumen: "Coherente (0.98)",
            wpm: "134 WPM",
            latencia: "210 ms",
            densidad: "0.95",
            coseno: "0.985"
          }
        },
        alertas: [
          {
            nivel: "NOMINAL",
            titulo: "SITUACIÓN CLÍNICA COMPENSADA (SOL 120)",
            texto: "Parámetros cardiovasculares, oculares (SANS), auditivos (LEQ16/LEQ8) y cognitivos (ASTRA) en rango nominal NASA-STD-3001."
          }
        ]
      },
      "ASTRO-02": {
        id: "ASTRO-02",
        nombre: "Elena Rostova",
        rango: "Especialista A02",
        mision: "ARES-VI · SOL 120 · MONITOREO ACTIGRÁFICO Y DOSIMETRÍA",
        estadoClinico: "VIGILANCIA",
        fisiologia: {
          hr: 84, hrv: 34, bp: "124/82", pam: 96, spo2: 97, rpm: 16,
          temp: 36.8, skinTemp: 35.1, boneLoss: -2.1, ared: 92,
          fluid: "1.85 / 2.2 L", sleep: "5.8 h (72%)"
        },
        examenes: {
          sans: {
            estado: "OBSERVACIÓN",
            resumen: "20/25 Leve",
            agudeza: "20/25 (75%)",
            contraste: "88% (7/8)",
            amsler: "Sin metamorfopsia",
            ishihara: "7/7 láminas"
          },
          sonar: {
            estado: "AVISO CX-17",
            resumen: "LEQ8 55.4 dBA",
            audiometria: "4/5 (Zumbido leve)",
            leq16: "68.4 dBA",
            leq8: "55.4 dBA (>50)",
            voz: "F0 144 Hz · HNR 14.8 dB"
          },
          astra: {
            estado: "FATIGA LEVE",
            resumen: "Fatiga (0.86)",
            wpm: "104 WPM",
            latencia: "490 ms",
            densidad: "0.81",
            coseno: "0.860"
          }
        },
        alertas: [
          {
            nivel: "AVISO",
            titulo: "[CX-17] SUEÑO ALTERADO POR RUIDO EN CABINA (LEQ8 > 50 dBA)",
            texto: "Dosímetro registra 55.4 dBA nocturnos con 5.8 h de sueño y descenso en HNR vocal (14.8 dB). Sugerido: tapones auditivos y revisión de ventilador."
          },
          {
            nivel: "AVISO",
            titulo: "[CX-03] SEGUIMIENTO PREVENTIVO SANS OCULAR",
            texto: "Agudeza cercana en 20/25. Programar control de fondo de ojo en 48 h y mantener CO2 de cabina < 2.5 mmHg."
          }
        ]
      }
    };
  }

  inicializar() {
    if (this._state?.subscribe) {
      this._state.subscribe(() => this.renderizar());
    }
    this.renderizar();
  }

  registrarResultadoExamen(tipo, datos) {
    const usr = this._auth?.obtenerUsuarioActual();
    const idTarget = usr?.id === "ASTRO-02" ? "ASTRO-02" : "ASTRO-01";
    const pac = this._pacientes[idTarget];
    if (!pac) return;

    if (tipo === "sans") {
      pac.examenes.sans = { ...pac.examenes.sans, ...datos };
    } else if (tipo === "sonar") {
      pac.examenes.sonar = { ...pac.examenes.sonar, ...datos };
    } else if (tipo === "astra") {
      pac.examenes.astra = { ...pac.examenes.astra, ...datos };
    }
    this.renderizar();
  }

  cambiarTripulante(idTripulante) {
    this._sound?.reproducirClick?.();
    this._modoComparativo = false;
    this._tripulanteActivo = idTripulante;


    const btn1 = document.getElementById("btnSurgeonAstro1");
    const btn2 = document.getElementById("btnSurgeonAstro2");
    const btnComp = document.getElementById("btnSurgeonCompare");
    if (btn1) {
      btn1.style.borderColor = idTripulante === "ASTRO-01" ? "var(--neon-cyan)" : "#64748b";
      btn1.style.background = idTripulante === "ASTRO-01" ? "rgba(0,240,255,0.14)" : "transparent";
    }
    if (btn2) {
      btn2.style.borderColor = idTripulante === "ASTRO-02" ? "var(--neon-cyan)" : "#64748b";
      btn2.style.background = idTripulante === "ASTRO-02" ? "rgba(0,240,255,0.14)" : "transparent";
    }
    if (btnComp) {
      btnComp.style.background = "transparent";
    }
    this.renderizar();
  }

  alternarModoComparativo() {
    this._sound?.reproducirClick?.();
    this._modoComparativo = !this._modoComparativo;
    const btnComp = document.getElementById("btnSurgeonCompare");
    if (btnComp) {
      btnComp.style.background = this._modoComparativo ? "rgba(192,132,252,0.22)" : "transparent";
    }
    this.renderizar();
  }

  _sincronizarConTelemetriaViva() {
    const state = this._state?._state;
    if (!state?.telemetria) return;
    const { fisiologia: fis, cognicion: cog } = state.telemetria;
    const p1 = this._pacientes["ASTRO-01"];
    if (fis) {
      p1.fisiologia.hr = Math.round(fis.ritmo_cardiaco_bpm || 76);
      p1.fisiologia.spo2 = Math.round(fis.spo2_pct || 98);
      p1.fisiologia.temp = Number(fis.temperatura_corporal_c || 36.6).toFixed(1);
      p1.fisiologia.boneLoss = -Math.abs(Number(fis.perdida_osea_pct || 1.8)).toFixed(1);
      const volFit = window.fitService ? (window.fitService._volumenMl / 1000).toFixed(2) : Number(fis.liquidos_litros_dia || 2.2).toFixed(2);
      p1.fisiologia.fluid = `${volFit} / 2.2 L`;
    }
    if (cog) {
      p1.examenes.astra.latencia = `${Math.round(cog.latencia_voz_ms || 210)} ms`;
      p1.examenes.astra.densidad = Number(cog.densidad_lexica_score || 0.95).toFixed(2);
      p1.examenes.astra.coseno = Number(cog.similitud_coseno || 0.985).toFixed(3);
      p1.examenes.astra.estado = cog.incongruencia_detectada ? "ATENCIÓN" : "COHERENTE";
      p1.examenes.astra.resumen = cog.incongruencia_detectada ? "Atención BHP" : `Coherente (${Number(cog.similitud_coseno || 0.98).toFixed(2)})`;
    }
    p1.estadoClinico = state.tripulanteEstable === false ? "CRÍTICO" : "COMPENSADO";
  }

  renderizar() {
    this._sincronizarConTelemetriaViva();
    const singleCont = document.getElementById("surgeonSingleContainer");
    const compCont = document.getElementById("surgeonCompareContainer");
    if (singleCont && compCont) {
      singleCont.style.display = this._modoComparativo ? "none" : "grid";
      compCont.style.display = this._modoComparativo ? "block" : "none";
    }

    const p1 = this._pacientes["ASTRO-01"];
    const p2 = this._pacientes["ASTRO-02"];
    const pac = this._pacientes[this._tripulanteActivo] || p1;
    const setEl = (id, txt, col) => {
      const el = document.getElementById(id);
      if (el) { el.innerText = txt; if (col) el.style.color = col; }
    };

    // Actualizar Resumen Mini-Tabla (A01 vs A02)
    setEl("miniVitalA01", `${p1.fisiologia.hr} lpm · ${p1.fisiologia.spo2}%`);
    setEl("miniSansA01", p1.examenes.sans.resumen);
    setEl("miniSonarA01", p1.examenes.sonar.resumen);
    setEl("miniAstraA01", p1.examenes.astra.resumen);

    setEl("miniVitalA02", `${p2.fisiologia.hr} lpm · ${p2.fisiologia.spo2}%`);
    setEl("miniSansA02", p2.examenes.sans.resumen);
    setEl("miniSonarA02", p2.examenes.sonar.resumen);
    setEl("miniAstraA02", p2.examenes.astra.resumen);

    if (this._modoComparativo) {
      this._renderizarTablaComparativaCompleta(p1, p2);
      return;
    }

      // Cabecera y Signos del Astronauta Seleccionado
      setEl("surgeonPatientName", `${pac.nombre.toUpperCase()} (${pac.rango.toUpperCase()})`);
      setEl("surgeonPatientMeta", pac.mision);
      const badgeClin = document.getElementById("surgeonClinicalStatusBadge");
      if (badgeClin) {
        badgeClin.innerText = `ESTADO: ${pac.estadoClinico}`;
        badgeClin.className = `badge-status ${pac.estadoClinico === "COMPENSADO" ? "status-stable" : (pac.estadoClinico === "CRÍTICO" ? "status-critical" : "status-warning")}`;
      }

        setEl("surgHrVal", pac.fisiologia.hr, pac.fisiologia.hr > 95 ? "var(--c-red)" : "var(--c-cyan-ink)");
        setEl("surgHrvVal", `${pac.fisiologia.hrv} ms`, pac.fisiologia.hrv < 35 ? "var(--neon-amber)" : "var(--c-green-ink)");
        setEl("surgBpVal", pac.fisiologia.bp);
        setEl("surgMapVal", `${pac.fisiologia.pam} mmHg`);
        setEl("surgSpo2Val", `${pac.fisiologia.spo2}%`, pac.fisiologia.spo2 < 95 ? "var(--c-red)" : "var(--c-green-ink)");
        setEl("surgRpmVal", `${pac.fisiologia.rpm} rpm`);
        setEl("surgTempVal", `${pac.fisiologia.temp} °C`);
        setEl("surgSkinTempVal", `${pac.fisiologia.skinTemp} °C`);
        setEl("surgBoneVal", `${pac.fisiologia.boneLoss}%`);
        setEl("surgAredVal", `${pac.fisiologia.ared}%`);
        setEl("surgFluidVal", pac.fisiologia.fluid);
        setEl("surgSleepVal", pac.fisiologia.sleep);

        // Resultados de Exámenes del Astronauta Seleccionado
        const setBadge = (id, estado, okVal) => {
          const b = document.getElementById(id);
          if (b) {
            b.innerText = estado;
            b.className = `badge-status ${estado === okVal ? "status-stable" : "status-warning"}`;
          }
        };
        setBadge("surgSansStatus", pac.examenes.sans.estado, "ESTABLE");
        setBadge("surgAudioStatus", pac.examenes.sonar.estado, "NOMINAL");
        setBadge("surgPsychStatus", pac.examenes.astra.estado, "COHERENTE");

        const sDet = document.getElementById("surgSansDetails");
        if (sDet) {
          sDet.innerHTML = `• Agudeza: <strong>${pac.examenes.sans.agudeza}</strong><br>• Contraste: <strong>${pac.examenes.sans.contraste}</strong><br>• Amsler: <strong>${pac.examenes.sans.amsler}</strong><br>• Ishihara: <strong>${pac.examenes.sans.ishihara}</strong>`;
        }
        const aDet = document.getElementById("surgAudioDetails");
        if (aDet) {
          aDet.innerHTML = `• Audiometría: <strong>${pac.examenes.sonar.audiometria}</strong><br>• Dosimetría: <strong>LEQ16 ${pac.examenes.sonar.leq16}</strong><br>• Sueño LEQ8: <strong>${pac.examenes.sonar.leq8}</strong><br>• Voz: <strong>${pac.examenes.sonar.voz}</strong>`;
        }
        const pDet = document.getElementById("surgPsychDetails");
        if (pDet) {
          pDet.innerHTML = `• Cadencia: <strong>${pac.examenes.astra.wpm}</strong><br>• Latencia: <strong>${pac.examenes.astra.latencia}</strong><br>• Densidad: <strong>${pac.examenes.astra.densidad}</strong><br>• Coseno: <strong>${pac.examenes.astra.coseno}</strong>`;
        }

        const contAlertas = document.getElementById("surgeonAlertsContainer");
        if (contAlertas) {
      contAlertas.innerHTML = pac.alertas.map((a) => `
            < div style = "background:#081326; border-left:3px solid ${a.nivel === "NOMINAL" ? "var(--c - green)" : "var(--neon - amber)"}; border-radius:0 6px 6px 0; padding:8px 12px; font-size:11px;" >
              <strong style="color:${a.nivel === " NOMINAL" ? "var(--c - green - ink)" : "var(--neon - amber)"}; font-family:var(--font-hud);" > ${ a.titulo }</strong >
                <p style="margin:3px 0 0 0; color:#cbd5e1; font-size:10.5px; line-height:1.35;">${a.texto}</p>
        </div >
            `).join("");
    }
  }

  _renderizarTablaComparativaCompleta(p1, p2) {
    const tbody = document.getElementById("surgeonFullCompareBody");
    if (!tbody) return;
    const filas = [
      ["Frecuencia Cardíaca / HRV", `${ p1.fisiologia.hr } lpm · HRV ${ p1.fisiologia.hrv } ms`, `${ p2.fisiologia.hr } lpm · HRV ${ p2.fisiologia.hrv } ms`, "55–90 lpm · HRV > 35 ms"],
      ["Presión Arterial / SpO₂", `${ p1.fisiologia.bp } mmHg · ${ p1.fisiologia.spo2 }% `, `${ p2.fisiologia.bp } mmHg · ${ p2.fisiologia.spo2 }% `, "< 130/85 mmHg · SpO₂ ≥ 95%"],
      ["Sueño Último Ciclo (8h Meta)", p1.fisiologia.sleep, p2.fisiologia.sleep, "≥ 6.5 h/noche (NASA-STD-3001)"],
      ["Hidratación NASA ISS FIT", p1.fisiologia.fluid, p2.fisiologia.fluid, "Meta base 2.20 L/día"],
      ["Pérdida Ósea BMD / ARED", `${ p1.fisiologia.boneLoss }% (ARED ${ p1.fisiologia.ared }%)`, `${ p2.fisiologia.boneLoss }% (ARED ${ p2.fisiologia.ared }%)`, "Pérdida < 2.5% · ARED ≥ 90%"],
      ["Examen Oftálmico SANS", `${ p1.examenes.sans.agudeza } · ${ p1.examenes.sans.amsler } · Ishihara ${ p1.examenes.sans.ishihara } `, `${ p2.examenes.sans.agudeza } · ${ p2.examenes.sans.amsler } · Ishihara ${ p2.examenes.sans.ishihara } `, "20/20 · Amsler normal · 7/7"],
      ["Audiometría Estéreo (250–8000 Hz)", p1.examenes.sonar.audiometria, p2.examenes.sonar.audiometria, "100% canales · Sin tinnitus"],
      ["Dosimetría Acústica (LEQ16 / LEQ8)", `Trabajo ${ p1.examenes.sonar.leq16 } · Sueño ${ p1.examenes.sonar.leq8 } `, `Trabajo ${ p2.examenes.sonar.leq16 } · Sueño ${ p2.examenes.sonar.leq8 } `, "LEQ16 ≤ 72 dBA · LEQ8 ≤ 50 dBA"],
      ["Biomarcadores de Voz (F0 / HNR)", p1.examenes.sonar.voz, p2.examenes.sonar.voz, "HNR > 16 dB · SNR > 15 dB"],
      ["Evaluación Cognitiva ASTRA-BHP", `${ p1.examenes.astra.estado } · ${ p1.examenes.astra.wpm } · Coseno ${ p1.examenes.astra.coseno } `, `${ p2.examenes.astra.estado } · ${ p2.examenes.astra.wpm } · Coseno ${ p2.examenes.astra.coseno } `, "Coseno ≥ 0.88 · Latencia < 450 ms"]
    ];
    tbody.innerHTML = filas.map(([param, v1, v2, ref]) => `
            < tr style = "border-bottom:1px solid rgba(255,255,255,0.07);" >
        <td style="padding:8px 10px; font-weight:bold; color:#e2e8f0;">${param}</td>
        <td style="padding:8px 10px; color:var(--c-cyan-ink);">${v1}</td>
        <td style="padding:8px 10px; color:#f8fafc;">${v2}</td>
        <td style="padding:8px 10px; color:#94a3b8; font-size:10.5px;">${ref}</td>
      </tr >
            `).join("");
  }

  prescribir(accion) {
    this._sound?.reproducirNominal?.();
    const fb = document.getElementById("surgeonActionFeedback");
    const pac = this._pacientes[this._tripulanteActivo] || this._pacientes["ASTRO-01"];
    if (fb) {
      fb.style.display = "block";
      fb.innerHTML = `🩺 <strong>ORDEN MÉDICA TRANSMITIDA A ${pac.nombre.toUpperCase()}:</strong> "${accion}".Registrado en bitácora BMed.`;
      setTimeout(() => { if (fb) fb.style.display = "none"; }, 5000);
    }
  }
}

window.SurgeonController = SurgeonController;
window.surgeonController = new SurgeonController();
