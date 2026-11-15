/**
 * CONTROLLERS LAYER: SurgeonController
 * Manages the Flight Surgeon's Specialized Console (Dr. Marcus Vance).
 * Strictly restricted to the FLIGHT_SURGEON role.
 * Synchronizes vital signs and exam results (SANS, Sonar/Voice, FIT and ASTRA)
 * for each astronaut (ASTRO-01 and ASTRO-02) and builds the comparison matrix.
 * Strictly under 400 lines (Clean Code & SRP).
 */

class SurgeonController {
  constructor(stateManager = null, soundService = null, authService = null) {
    this._state = stateManager || window.stateManager;
    this._sound = soundService || window.soundService;
    this._auth = authService || window.authService;
    this._activeCrewMember = "ASTRO-01";
    this._comparisonMode = false;

    this._patients = {
      "ASTRO-01": {
        id: "ASTRO-01",
        name: "Alex Mercer",
        rank: "Commander A01",
        mission: "ARES-VI · SOL 120 · REAL-TIME ASTROSKIN BIO-TELEMETRY",
        clinicalState: "COMPENSATED",
        physiology: {
          hr: 76, hrv: 42, bp: "118/76", map: 90, spo2: 98, rpm: 14,
          temp: 36.6, skinTemp: 34.8, boneLoss: -1.8, ared: 100,
          fluid: "2.20 / 2.2 L", sleep: "7.2 h (90%)"
        },
        exams: {
          sans: {
            state: "STABLE",
            summary: "20/20 Nominal",
            acuity: "20/20 (100%)",
            contrast: "100% (8/8)",
            amsler: "No distortion",
            ishihara: "7/7 plates"
          },
          sonar: {
            state: "NOMINAL",
            summary: "59.5 dBA OK",
            audiometry: "5/5 (No tinnitus)",
            leq16: "59.5 dBA",
            leq8: "48.5 dBA",
            voice: "F0 124 Hz · HNR 21.4 dB"
          },
          astra: {
            state: "COHERENT",
            summary: "Coherent (0.98)",
            wpm: "134 WPM",
            latency: "210 ms",
            density: "0.95",
            cosine: "0.985"
          }
        },
        alerts: [
          {
            level: "NOMINAL",
            title: "COMPENSATED CLINICAL SITUATION (SOL 120)",
            text: "Cardiovascular, ocular (SANS), auditory (LEQ16/LEQ8) and cognitive (ASTRA) parameters within the NASA-STD-3001 nominal range."
          }
        ]
      },
      "ASTRO-02": {
        id: "ASTRO-02",
        name: "Elena Rostova",
        rank: "Specialist A02",
        mission: "ARES-VI · SOL 120 · ACTIGRAPHIC MONITORING AND DOSIMETRY",
        clinicalState: "WATCH",
        physiology: {
          hr: 84, hrv: 34, bp: "124/82", map: 96, spo2: 97, rpm: 16,
          temp: 36.8, skinTemp: 35.1, boneLoss: -2.1, ared: 92,
          fluid: "1.85 / 2.2 L", sleep: "5.8 h (72%)"
        },
        exams: {
          sans: {
            state: "OBSERVATION",
            summary: "20/25 Mild",
            acuity: "20/25 (75%)",
            contrast: "88% (7/8)",
            amsler: "No metamorphopsia",
            ishihara: "7/7 plates"
          },
          sonar: {
            state: "CX-17 NOTICE",
            summary: "LEQ8 55.4 dBA",
            audiometry: "4/5 (Mild ringing)",
            leq16: "68.4 dBA",
            leq8: "55.4 dBA (>50)",
            voice: "F0 144 Hz · HNR 14.8 dB"
          },
          astra: {
            state: "MILD FATIGUE",
            summary: "Fatigue (0.86)",
            wpm: "104 WPM",
            latency: "490 ms",
            density: "0.81",
            cosine: "0.860"
          }
        },
        alerts: [
          {
            level: "NOTICE",
            title: "[CX-17] SLEEP DEGRADED BY CABIN NOISE (LEQ8 > 50 dBA)",
            text: "The dosimeter records 55.4 dBA overnight with 5.8 h of sleep and a drop in vocal HNR (14.8 dB). Suggested: earplugs and a fan inspection."
          },
          {
            level: "NOTICE",
            title: "[CX-03] PREVENTIVE SANS OCULAR FOLLOW-UP",
            text: "Near acuity at 20/25. Schedule a fundus check within 48 h and keep cabin CO2 below 2.5 mmHg."
          }
        ]
      }
    };
  }

  initialize() {
    if (this._state?.subscribe) {
      this._state.subscribe(() => this.render());
    }
    this.render();
  }

  logExamResult(type, data) {
    const usr = this._auth?.getCurrentUser();
    const targetId = usr?.id === "ASTRO-02" ? "ASTRO-02" : "ASTRO-01";
    const patient = this._patients[targetId];
    if (!patient) return;

    if (type === "sans") {
      patient.exams.sans = { ...patient.exams.sans, ...data };
    } else if (type === "sonar") {
      patient.exams.sonar = { ...patient.exams.sonar, ...data };
    } else if (type === "astra") {
      patient.exams.astra = { ...patient.exams.astra, ...data };
    }
    this.render();
  }

  changeCrewMember(crewMemberId) {
    this._sound?.playClick?.();
    this._comparisonMode = false;
    this._activeCrewMember = crewMemberId;

    const btn1 = document.getElementById("btnSurgeonAstro1");
    const btn2 = document.getElementById("btnSurgeonAstro2");
    const btnCompare = document.getElementById("btnSurgeonCompare");
    if (btn1) {
      btn1.style.borderColor = crewMemberId === "ASTRO-01" ? "var(--neon-cyan)" : "#64748b";
      btn1.style.background = crewMemberId === "ASTRO-01" ? "rgba(0,240,255,0.14)" : "transparent";
    }
    if (btn2) {
      btn2.style.borderColor = crewMemberId === "ASTRO-02" ? "var(--neon-cyan)" : "#64748b";
      btn2.style.background = crewMemberId === "ASTRO-02" ? "rgba(0,240,255,0.14)" : "transparent";
    }
    if (btnCompare) {
      btnCompare.style.background = "transparent";
    }
    this.render();
  }

  toggleComparisonMode() {
    this._sound?.playClick?.();
    this._comparisonMode = !this._comparisonMode;
    const btnCompare = document.getElementById("btnSurgeonCompare");
    if (btnCompare) {
      btnCompare.style.background = this._comparisonMode ? "rgba(192,132,252,0.22)" : "transparent";
    }
    this.render();
  }

  _syncWithLiveTelemetry() {
    const state = this._state?._state;
    if (!state?.telemetry) return;
    const { physiology: phys, cognition: cog } = state.telemetry;
    const p1 = this._patients["ASTRO-01"];
    if (phys) {
      p1.physiology.hr = Math.round(phys.heart_rate_bpm || 76);
      p1.physiology.spo2 = Math.round(phys.spo2_pct || 98);
      p1.physiology.temp = Number(phys.body_temperature_c || 36.6).toFixed(1);
      p1.physiology.boneLoss = -Math.abs(Number(phys.bone_loss_pct || 1.8)).toFixed(1);
      const fitVolume = window.fitService ? (window.fitService._volumeMl / 1000).toFixed(2) : Number(phys.fluids_liters_per_day || 2.2).toFixed(2);
      p1.physiology.fluid = `${fitVolume} / 2.2 L`;
    }
    if (cog) {
      p1.exams.astra.latency = `${Math.round(cog.voice_latency_ms || 210)} ms`;
      p1.exams.astra.density = Number(cog.lexical_density_score || 0.95).toFixed(2);
      p1.exams.astra.cosine = Number(cog.cosine_similarity || 0.985).toFixed(3);
      p1.exams.astra.state = cog.incongruence_detected ? "ATTENTION" : "COHERENT";
      p1.exams.astra.summary = cog.incongruence_detected ? "BHP attention" : `Coherent (${Number(cog.cosine_similarity || 0.98).toFixed(2)})`;
    }
    p1.clinicalState = state.crewStable === false ? "CRITICAL" : "COMPENSATED";
  }

  render() {
    this._syncWithLiveTelemetry();
    const singleCont = document.getElementById("surgeonSingleContainer");
    const compareCont = document.getElementById("surgeonCompareContainer");
    if (singleCont && compareCont) {
      singleCont.style.display = this._comparisonMode ? "none" : "grid";
      compareCont.style.display = this._comparisonMode ? "block" : "none";
    }

    const p1 = this._patients["ASTRO-01"];
    const p2 = this._patients["ASTRO-02"];
    const patient = this._patients[this._activeCrewMember] || p1;
    const setEl = (id, txt, col) => {
      const el = document.getElementById(id);
      if (el) { el.innerText = txt; if (col) el.style.color = col; }
    };

    // Update the mini summary table (A01 vs A02)
    setEl("miniVitalA01", `${p1.physiology.hr} bpm · ${p1.physiology.spo2}%`);
    setEl("miniSansA01", p1.exams.sans.summary);
    setEl("miniSonarA01", p1.exams.sonar.summary);
    setEl("miniAstraA01", p1.exams.astra.summary);

    setEl("miniVitalA02", `${p2.physiology.hr} bpm · ${p2.physiology.spo2}%`);
    setEl("miniSansA02", p2.exams.sans.summary);
    setEl("miniSonarA02", p2.exams.sonar.summary);
    setEl("miniAstraA02", p2.exams.astra.summary);

    if (this._comparisonMode) {
      this._renderFullComparisonTable(p1, p2);
      return;
    }

    // Header and vital signs of the selected astronaut
    setEl("surgeonPatientName", `${patient.name.toUpperCase()} (${patient.rank.toUpperCase()})`);
    setEl("surgeonPatientMeta", patient.mission);
    const clinicalBadge = document.getElementById("surgeonClinicalStatusBadge");
    if (clinicalBadge) {
      clinicalBadge.innerText = `STATE: ${patient.clinicalState}`;
      clinicalBadge.className = `badge-status ${patient.clinicalState === "COMPENSATED" ? "status-stable" : (patient.clinicalState === "CRITICAL" ? "status-critical" : "status-warning")}`;
    }

    setEl("surgHrVal", patient.physiology.hr, patient.physiology.hr > 95 ? "var(--c-red)" : "var(--c-cyan-ink)");
    setEl("surgHrvVal", `${patient.physiology.hrv} ms`, patient.physiology.hrv < 35 ? "var(--neon-amber)" : "var(--c-green-ink)");
    setEl("surgBpVal", patient.physiology.bp);
    setEl("surgMapVal", `${patient.physiology.map} mmHg`);
    setEl("surgSpo2Val", `${patient.physiology.spo2}%`, patient.physiology.spo2 < 95 ? "var(--c-red)" : "var(--c-green-ink)");
    setEl("surgRpmVal", `${patient.physiology.rpm} rpm`);
    setEl("surgTempVal", `${patient.physiology.temp} °C`);
    setEl("surgSkinTempVal", `${patient.physiology.skinTemp} °C`);
    setEl("surgBoneVal", `${patient.physiology.boneLoss}%`);
    setEl("surgAredVal", `${patient.physiology.ared}%`);
    setEl("surgFluidVal", patient.physiology.fluid);
    setEl("surgSleepVal", patient.physiology.sleep);

    // Exam results of the selected astronaut
    const setBadge = (id, state, okVal) => {
      const b = document.getElementById(id);
      if (b) {
        b.innerText = state;
        b.className = `badge-status ${state === okVal ? "status-stable" : "status-warning"}`;
      }
    };
    setBadge("surgSansStatus", patient.exams.sans.state, "STABLE");
    setBadge("surgAudioStatus", patient.exams.sonar.state, "NOMINAL");
    setBadge("surgPsychStatus", patient.exams.astra.state, "COHERENT");

    const sansDetails = document.getElementById("surgSansDetails");
    if (sansDetails) {
      sansDetails.innerHTML = `• Acuity: <strong>${patient.exams.sans.acuity}</strong><br>• Contrast: <strong>${patient.exams.sans.contrast}</strong><br>• Amsler: <strong>${patient.exams.sans.amsler}</strong><br>• Ishihara: <strong>${patient.exams.sans.ishihara}</strong>`;
    }
    const audioDetails = document.getElementById("surgAudioDetails");
    if (audioDetails) {
      audioDetails.innerHTML = `• Audiometry: <strong>${patient.exams.sonar.audiometry}</strong><br>• Dosimetry: <strong>LEQ16 ${patient.exams.sonar.leq16}</strong><br>• Sleep LEQ8: <strong>${patient.exams.sonar.leq8}</strong><br>• Voice: <strong>${patient.exams.sonar.voice}</strong>`;
    }
    const psychDetails = document.getElementById("surgPsychDetails");
    if (psychDetails) {
      psychDetails.innerHTML = `• Cadence: <strong>${patient.exams.astra.wpm}</strong><br>• Latency: <strong>${patient.exams.astra.latency}</strong><br>• Density: <strong>${patient.exams.astra.density}</strong><br>• Cosine: <strong>${patient.exams.astra.cosine}</strong>`;
    }

    const alertsContainer = document.getElementById("surgeonAlertsContainer");
    if (alertsContainer) {
      alertsContainer.innerHTML = patient.alerts.map((a) => {
        const isNominal = a.level === "NOMINAL";
        const accent = isNominal ? "var(--c-green)" : "var(--neon-amber)";
        const titleColor = isNominal ? "var(--c-green-ink)" : "var(--neon-amber)";
        return `
        <div style="background:#081326; border-left:3px solid ${accent}; border-radius:0 6px 6px 0; padding:8px 12px; font-size:11px;">
          <strong style="color:${titleColor}; font-family:var(--font-hud);">${a.title}</strong>
          <p style="margin:3px 0 0 0; color:#cbd5e1; font-size:10.5px; line-height:1.35;">${a.text}</p>
        </div>`;
      }).join("");
    }
  }

  _renderFullComparisonTable(p1, p2) {
    const tbody = document.getElementById("surgeonFullCompareBody");
    if (!tbody) return;
    const rows = [
      ["Heart Rate / HRV", `${p1.physiology.hr} bpm · HRV ${p1.physiology.hrv} ms`, `${p2.physiology.hr} bpm · HRV ${p2.physiology.hrv} ms`, "55–90 bpm · HRV > 35 ms"],
      ["Blood Pressure / SpO₂", `${p1.physiology.bp} mmHg · ${p1.physiology.spo2}%`, `${p2.physiology.bp} mmHg · ${p2.physiology.spo2}%`, "< 130/85 mmHg · SpO₂ ≥ 95%"],
      ["Last Sleep Cycle (8h Goal)", p1.physiology.sleep, p2.physiology.sleep, "≥ 6.5 h/night (NASA-STD-3001)"],
      ["NASA ISS FIT Hydration", p1.physiology.fluid, p2.physiology.fluid, "Base goal 2.20 L/day"],
      ["BMD Bone Loss / ARED", `${p1.physiology.boneLoss}% (ARED ${p1.physiology.ared}%)`, `${p2.physiology.boneLoss}% (ARED ${p2.physiology.ared}%)`, "Loss < 2.5% · ARED ≥ 90%"],
      ["SANS Ophthalmic Exam", `${p1.exams.sans.acuity} · ${p1.exams.sans.amsler} · Ishihara ${p1.exams.sans.ishihara}`, `${p2.exams.sans.acuity} · ${p2.exams.sans.amsler} · Ishihara ${p2.exams.sans.ishihara}`, "20/20 · Normal Amsler · 7/7"],
      ["Stereo Audiometry (250–8000 Hz)", p1.exams.sonar.audiometry, p2.exams.sonar.audiometry, "100% channels · No tinnitus"],
      ["Acoustic Dosimetry (LEQ16 / LEQ8)", `Work ${p1.exams.sonar.leq16} · Sleep ${p1.exams.sonar.leq8}`, `Work ${p2.exams.sonar.leq16} · Sleep ${p2.exams.sonar.leq8}`, "LEQ16 ≤ 72 dBA · LEQ8 ≤ 50 dBA"],
      ["Voice Biomarkers (F0 / HNR)", p1.exams.sonar.voice, p2.exams.sonar.voice, "HNR > 16 dB · SNR > 15 dB"],
      ["ASTRA-BHP Cognitive Assessment", `${p1.exams.astra.state} · ${p1.exams.astra.wpm} · Cosine ${p1.exams.astra.cosine}`, `${p2.exams.astra.state} · ${p2.exams.astra.wpm} · Cosine ${p2.exams.astra.cosine}`, "Cosine ≥ 0.88 · Latency < 450 ms"]
    ];
    tbody.innerHTML = rows.map(([param, v1, v2, ref]) => `
      <tr style="border-bottom:1px solid rgba(255,255,255,0.07);">
        <td style="padding:8px 10px; font-weight:bold; color:#e2e8f0;">${param}</td>
        <td style="padding:8px 10px; color:var(--c-cyan-ink);">${v1}</td>
        <td style="padding:8px 10px; color:#f8fafc;">${v2}</td>
        <td style="padding:8px 10px; color:#94a3b8; font-size:10.5px;">${ref}</td>
      </tr>`).join("");
  }

  prescribe(action) {
    this._sound?.playNominal?.();
    const fb = document.getElementById("surgeonActionFeedback");
    const patient = this._patients[this._activeCrewMember] || this._patients["ASTRO-01"];
    if (fb) {
      fb.style.display = "block";
      fb.innerHTML = `🩺 <strong>MEDICAL ORDER TRANSMITTED TO ${patient.name.toUpperCase()}:</strong> "${action}". Logged in the BMed record.`;
      setTimeout(() => { if (fb) fb.style.display = "none"; }, 5000);
    }
  }
}

window.SurgeonController = SurgeonController;
window.surgeonController = new SurgeonController();
