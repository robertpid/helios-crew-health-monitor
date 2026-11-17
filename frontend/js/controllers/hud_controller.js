/**
 * CONTROLLERS LAYER: HudController
 * Main UI orchestrator: binds State to the DOM and Services.
 * Kept strictly under 330 lines (Clean Code & SRP).
 */
class HudController {
  constructor(stateManager, ecgService, telemetryService, soundService = null, wellnessController = null, authService = null) {
    this._state = stateManager;
    this._ecg = ecgService;
    this._telemetry = telemetryService;
    this._sound = soundService || window.soundService;
    this._wellness = wellnessController || (window.WellnessController ? new window.WellnessController(this._sound) : null);
    this._auth = authService || window.authService;
    this._lastModalState = false;
    this._kroneckerNames = [
      "CO2xPulse", "CO2xSleep", "CO2xBone", "CO2xSANS",
      "RadxPulse", "RadxSleep", "RadxBone", "RadxSANS",
      "PresxPulse", "PresxSleep", "PresxBone", "PresxSANS"
    ];
  }

  initialize() {
    this._state.subscribe(state => this.render(state));
    this._telemetry.startPolling();
    this._loadMatrixCatalog();
    if (this._auth) {
      this._auth.onSessionChange(u => this._updateUserBadge(u));
      const user = this._auth.getCurrentUser();
      if (user) {
        document.body.classList.remove("locked");
        this._updateUserBadge(user);
        this.closeLoginModal();
      } else {
        document.body.classList.add("locked");
        this.openLoginModal();
      }
    }
  }

  toggleAudio() {
    if (!this._sound && window.soundService) this._sound = window.soundService;
    if (this._sound) {
      const mute = this._sound.toggleMute();
      const btn = document.getElementById("btnAudioToggle");
      if (btn) {
        btn.innerText = mute ? "🔇 AUDIO: MUTE" : "🔊 AUDIO: ON";
        btn.style.color = mute ? "var(--text-muted)" : "var(--neon-cyan)";
      }
      if (!mute) this._sound.playClick();
    }
  }

  changeView(name) {
    if (name === "surgeon" && this._auth?.getCurrentUser()?.role !== "FLIGHT_SURGEON") {
      alert("🔒 RESTRICTED ACCESS: The Medical Console requires Flight Surgeon credentials (Dr. Marcus Vance).");
      this.openLoginModal();
      return;
    }
    if (this._sound) this._sound.playClick();
    this.unfocusOrgan();
    this.unfocusHabitatModule();
    this._state.setActiveView(name);
  }

  focusOrgan(name) {
    if (this._sound?.playHover) this._sound.playHover();
    const stg = document.querySelector("#viewBiomedical .hologram-stage-wrapper");
    if (!stg) return;
    stg.classList.add("has-organ-focus");
    stg.querySelectorAll(".organ-node, .organ-connector-line, .hologram-callout").forEach(el => el.classList.remove("is-focused"));
    [`.organ-node[data-organ="${name}"]`, `.organ-connector-line[data-organ-line="${name}"]`, `.hologram-callout[data-organ-card="${name}"]`]
      .forEach(sel => stg.querySelectorAll(sel).forEach(el => el.classList.add("is-focused")));
  }

  unfocusOrgan() {
    const stg = document.querySelector("#viewBiomedical .hologram-stage-wrapper");
    if (!stg) return;
    stg.classList.remove("has-organ-focus");
    stg.querySelectorAll(".organ-node, .organ-connector-line, .hologram-callout").forEach(el => el.classList.remove("is-focused"));
  }

  focusHabitatModule(module) {
    if (this._sound?.playHover) this._sound.playHover();
    const stg = document.querySelector("#viewEnvironmental .hologram-stage-wrapper");
    if (!stg) return;
    stg.classList.add("has-habitat-focus");
    stg.querySelectorAll(".habitat-module-node, .habitat-connector-line, .hologram-callout").forEach(el => el.classList.remove("is-focused"));
    [`.habitat-module-node[data-habitat-module="${module}"]`, `.habitat-connector-line[data-habitat-line="${module}"]`, `.hologram-callout[data-habitat-card="${module}"]`]
      .forEach(sel => stg.querySelectorAll(sel).forEach(el => el.classList.add("is-focused")));
    stg.querySelectorAll('button[data-habitat-module]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.habitatModule === module)));
  }

  unfocusHabitatModule() {
    const stg = document.querySelector("#viewEnvironmental .hologram-stage-wrapper");
    if (!stg) return;
    stg.classList.remove("has-habitat-focus");
    stg.querySelectorAll(".habitat-module-node, .habitat-connector-line, .hologram-callout").forEach(el => el.classList.remove("is-focused"));
    stg.querySelectorAll('button[data-habitat-module]').forEach(button => button.setAttribute('aria-pressed', 'false'));
  }

  changeHabitatDetail(detail) {
    if (!['image', 'sensors'].includes(detail)) return;
    this.unfocusHabitatModule();
    document.querySelector('[data-panel="habitat"]').dataset.habitatTab = detail;
    document.getElementById('habitatIllustration').dataset.habitatTab = detail;
    document.querySelectorAll('[data-habitat-tab-button]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.habitatTabButton === detail)));
  }

  switchHabitatModel(model) {
    const illustrations = {
      orion: { file: 'orion-transparent.png', title: 'Spacecraft', alt: 'Illustration of a crewed spacecraft with a cabin cutaway, service module and solar panels.' },
      mars: { file: 'mars-base-transparent.png', title: 'Mars base', alt: 'Illustration of a Mars base with habitation modules, laboratory, life support and solar panels on reddish terrain.' },
      iss: { file: 'iss-transparent.png', title: 'Space station', alt: 'Illustration of a modular space station with large solar panels and an open module showing its interior.' }
    };
    const illustration = illustrations[model];
    if (!illustration) return;
    this.changeHabitatDetail('image');
    if (this._sound?.playHabitatChange) this._sound.playHabitatChange();
    else this._sound?.playClick?.();
    this.unfocusHabitatModule();
    if (this._state?.setHabitatModel) this._state.setHabitatModel(model);
    ["orion", "mars", "iss"].forEach(m => {
      const cap = m.charAt(0).toUpperCase() + m.slice(1);
      const btn = document.getElementById(`btnHabitat${cap}`);
      if (btn) { btn.classList.toggle("active", m === model); btn.setAttribute('aria-pressed', String(m === model)); }
    });
    const image = document.getElementById('habitatImage');
    if (image) {
      image.src = `/static/assets/habitats/${illustration.file}?v=20261115_alpha`;
      image.alt = illustration.alt;
      image.dataset.habitat = model;
    }
    window.habitatDiagramService?.update(model);
    this._setTxt('habitatImageCaption', `${illustration.title} · Concept illustration`);
    const sub = document.getElementById("habitatSubtitle");
    if (sub) {
      const titles = {
        orion: "ORION DEEP SPACE VEHICLE · INTERPLANETARY TRANSIT (0.00g)",
        mars: "ARCADIA PLANITIA BASE (MARS) · PRESSURIZED DOME (0.38g)",
        iss: "INTERNATIONAL SPACE STATION · LEO ORBITAL (0.00g)"
      };
      sub.innerText = titles[model] || "";
    }
    const labels = {
      orion: { co2: "ECLSS SCRUBBER (ppCO2)", rad: "RADIATION SHIELDING (SPE)", temp: "THERMAL CONTROL (ATCS)", press: "HULL PRESSURE", hum: "ATMOSPHERIC HUMIDITY" },
      mars: { co2: "MOXIE / MARS O₂ SUPPORT", rad: "REGOLITH SHIELDING (MARS)", temp: "MARS DOME CLIMATE CONTROL", press: "PRESSURIZED DOME PRESSURE", hum: "BIOMARS GREENHOUSE" },
      iss: { co2: "CDRA ECLSS (ISS STATION)", rad: "SHIELDED DESTINY MODULES", temp: "EXTERNAL THERMAL LOOP", press: "HARMONY MODULE PRESSURE", hum: "CABIN CONDENSER" }
    };
    const lb = labels[model] || labels.orion;
    this._setTxt("labelEnvCo2", lb.co2);
    this._setTxt("labelEnvRad", lb.rad);
    this._setTxt("labelEnvTemp", lb.temp);
    this._setTxt("labelEnvPress", lb.press);
    this._setTxt("labelEnvHum", lb.hum);
  }

  restoreNominalMode() {
    this._sound?.playNominal?.();
    this._state.setOperationMode("nominal");
  }

  activateCrisisMode() {
    this._sound?.playCrisis?.();
    this._state.setOperationMode("crisis");
  }

  toggleModal() {
    this._sound?.playClick?.();
    this._state.toggleAlertModal();
  }

  openLoginModal() {
    this._sound?.playClick?.();
    const modal = document.getElementById("modalLogin");
    const btnClose = document.getElementById("btnCloseLoginModal");
    const isAuthenticated = !!this._auth?.getCurrentUser();
    if (modal) modal.style.display = "flex";
    if (btnClose) btnClose.style.display = isAuthenticated ? "block" : "none";
    if (!isAuthenticated) document.body.classList.add("locked");
    const err = document.getElementById("loginErrorMsg");
    if (err) err.style.display = "none";
  }

  closeLoginModal() {
    if (!this._auth?.getCurrentUser()) return;
    this._sound?.playClick?.();
    document.body.classList.remove("locked");
    const modal = document.getElementById("modalLogin");
    if (modal) modal.style.display = "none";
  }

  selectDemoUser(username) {
    this._sound?.playClick?.();
    const inU = document.getElementById("inputLoginUser");
    const inP = document.getElementById("inputLoginPin");
    const err = document.getElementById("loginErrorMsg");
    if (inU) inU.value = username;
    if (inP) { inP.value = ""; inP.focus(); }
    if (err) err.style.display = "none";
  }

  runLogin() {
    const inU = document.getElementById("inputLoginUser");
    const inP = document.getElementById("inputLoginPin");
    const err = document.getElementById("loginErrorMsg");
    if (!inU || !inP || !this._auth) return;
    const res = this._auth.authenticate(inU.value, inP.value);
    if (res.success) {
      inP.value = "";
      this._sound?.playNominal?.();
      this.closeLoginModal();
    } else {
      this._sound?.playAlert?.();
      inP.value = "";
      inP.focus();
      if (err) { err.innerText = res.error; err.style.display = "block"; }
    }
  }

  _updateUserBadge(user) {
    if (!user) return;
    this._setTxt("userAvatarTag", user.avatar || "👨‍🚀");
    this._setTxt("userIdentTag", user.rank || user.name);
    this._setTxt("userRoleTag", `(${user.name})`);

    const isSurgeon = user.role === "FLIGHT_SURGEON";
    const tabSurgeon = document.getElementById("navTabSurgeon");
    if (tabSurgeon) {
      tabSurgeon.style.display = isSurgeon ? "inline-flex" : "none";
    }

    if (isSurgeon) {
      window.surgeonController?.render();
      this.changeView("surgeon");
    } else {
      if (this._state?._state?.activeView === "surgeon") {
        this.changeView("biomedical");
      }
    }
  }

  advanceTask(t) { this._wellness?.advanceTask(t); }
  startOphthalmicExam() { this._wellness?.startOphthalmicExam(); }
  startSonarExam() { this._wellness?.startSonarExam(); }
  syncMail() { window.mailService ? window.mailService.syncMailbox() : this._wellness?.syncMail(); }
  toggleBreathingGuide() { this._wellness?.toggleBreathingGuide(); }
  startPsychologicalProtocol() {
    this._wellness?.startPsychologicalProtocol();
    window.viewportController?.showAssistant();
  }
  sendPsychologicalResponse() { this._wellness?.sendPsychologicalResponse(); }
  selectSuggestedChip(t) { this._wellness?.selectSuggestedChip(t); }
  startVoiceDictation() { this._wellness?.startVoiceDictation(); }
  toggleTechnicalMatrix() { this._wellness?.toggleTechnicalMatrix(); }

  render(state) {
    this._updateTabs(state.activeView);
    this._updateDashboardValues(state);
  }

  _updateDashboardValues(state) {
    const { physiology: phys, environment: env, cognition: cog, kronecker: kron } = state.telemetry;
    const pill = document.getElementById("statusPill");
    if (pill) {
      pill.innerText = state.crewStable ? "STABLE" : "CRITICAL";
      pill.className = `badge-status ${state.crewStable ? "status-stable" : "status-critical"}`;
    }

    this._setTxt("valHeart", Math.round(phys.heart_rate_bpm));
    this._ecg?.updateHeartRate?.(phys.heart_rate_bpm);
    this._setTxt("valSpo2", Math.round(phys.spo2_pct));
    this._setTxt("valTemp", phys.body_temperature_c.toFixed(1));
    this._setTxt("valVoiceLatency", Math.round(cog.voice_latency_ms));
    this._setTxt("valBone", `-${phys.bone_loss_pct.toFixed(1)}`);

    this._toggleClass("cardHeart", "tile-danger", phys.heart_rate_bpm > 100);
    this._toggleClass("cardSpo2", "tile-danger", phys.spo2_pct < 94.0);
    this._toggleClass("cardTemp", "tile-danger", phys.body_temperature_c > 37.8);
    this._toggleClass("cardAstra", "tile-danger", cog.incongruence_detected);

    this._setTxt("calloutHeart", `${Math.round(phys.heart_rate_bpm)} bpm`);
    this._setTxt("calloutSpo2", `${Math.round(phys.spo2_pct)} %`);
    this._setTxt("calloutBone", `-${phys.bone_loss_pct.toFixed(1)}%`);
    this._setTxt("calloutFluid", `${phys.fluids_liters_per_day.toFixed(1)} L/d`);
    this._setTxt("calloutAstra", cog.incongruence_detected ? "HIDDEN FATIGUE" : "COHERENT");
    document.getElementById("nodeHeart")?.classList.toggle("fast", phys.heart_rate_bpm > 100);

    this._setTxt("valCo2", env.co2_mmHg.toFixed(1));
    this._setTxt("valRad", env.cumulative_radiation_mSv.toFixed(1));
    this._setTxt("valPress", env.cabin_pressure_kpa.toFixed(1));
    this._setTxt("valCabinTemp", env.cabin_temperature_c.toFixed(1));
    this._setTxt("valHumidity", env.relative_humidity_pct.toFixed(1));
    this._setTxt("valSolarStatus", env.solar_event_active ? "STORM ACTIVE (SPE)" : "S0 QUIET");
    this._setTxt("envGravity", `${env.gravity_g.toFixed(2)} g`);

    this._setTxt("calloutEnvCo2", `${env.co2_mmHg.toFixed(1)} mmHg`);
    this._setTxt("calloutEnvRad", `${env.cumulative_radiation_mSv.toFixed(1)} mSv`);
    this._setTxt("calloutEnvPress", `${env.cabin_pressure_kpa.toFixed(1)} kPa`);
    this._setTxt("calloutEnvTemp", `${env.cabin_temperature_c.toFixed(1)} °C`);
    this._setTxt("calloutEnvHum", `${env.relative_humidity_pct.toFixed(1)} %`);

    this._toggleClass("cardCo2", "tile-danger", env.co2_mmHg > 3.0);
    this._toggleClass("cardSolar", "tile-danger", env.solar_event_active);

    this._renderKroneckerMatrix(kron.argmax_index, kron.max_severity);

    const cm = document.getElementById("ambientCountermeasuresList");
    if (cm && state.telemetry.prioritized_countermeasures) {
      cm.innerHTML = state.telemetry.prioritized_countermeasures.slice(0, 3).map((a, i) => `<div><strong>${i + 1}.</strong> ${a}</div>`).join("");
    }

    this._updateCriticalModal(state);
    this._wellness?.updateHydration(state.operationMode === "crisis" || (phys.fluids_liters_per_day < 1.5));
  }

  _updateTabs(active) {
    this.unfocusOrgan();
    this.unfocusHabitatModule();
    const tabs = document.querySelectorAll(".nav-tab-btn");
    const views = document.querySelectorAll(".view-container");
    tabs.forEach(t => t.classList.remove("active"));
    views.forEach(v => {
      v.classList.remove("active-view");
      v.style.setProperty("display", "none", "important");
    });

    const map = {
      biomedical: { tab: tabs[0], view: "viewBiomedical" },
      environmental: { tab: tabs[1], view: "viewEnvironmental" },
      matrix: { tab: tabs[2], view: "viewMatrix" },
      support: { tab: tabs[3], view: "viewSupport" },
      surgeon: { tab: document.getElementById("navTabSurgeon") || tabs[4], view: "viewSurgeon" }
    };
    if (active === "biomedical") this._ecg?.resume?.();
    else this._ecg?.pause?.();

    const tgt = map[active];
    if (tgt) {
      tgt.tab?.classList.add("active");
      tabs.forEach(tab => tab.setAttribute("aria-pressed", String(tab === tgt.tab)));
      const v = document.getElementById(tgt.view);
      if (v) { v.classList.add("active-view"); v.style.setProperty("display", "grid", "important"); }
      window.viewportController?.updateView(active);
      if (active === "environmental") setTimeout(() => window.dispatchEvent(new Event("resize")), 60);
    }
  }

  _renderKroneckerMatrix(idx, sev) {
    const cnt = document.getElementById("kroneckerGrid");
    if (!cnt) return;
    cnt.innerHTML = "";
    for (let i = 0; i < 12; i++) {
      const cell = document.createElement("div");
      const act = (i === idx);
      cell.className = "matrix-cell" + (act ? " active-danger" : "");
      cell.innerHTML = `<strong>${this._kroneckerNames[i]}</strong><br><small>${act ? sev.toFixed(1) : "0.0"}</small>`;
      cnt.appendChild(cell);
    }
    const tag = document.getElementById("matrixMaxSeverity");
    if (tag) {
      tag.innerText = (idx >= 0) ? `Critical Edge: ${this._kroneckerNames[idx]} (${sev.toFixed(1)}/10)` : "No adverse synergies (0.0/10)";
      tag.style.color = (idx >= 0) ? "var(--neon-red)" : "var(--neon-green)";
    }
  }

  _updateCriticalModal(state) {
    const modal = document.getElementById("modalAlert");
    if (!modal) return;
    if (state.alertModalOpen) {
      modal.style.setProperty("display", "flex", "important");
      modal.classList.add("open");
      if (!this._lastModalState && this._sound) this._sound.startEmergencyAlarm();
    } else {
      modal.style.setProperty("display", "none", "important");
      modal.classList.remove("open");
    }
    this._lastModalState = !!state.alertModalOpen;

    const { physiology: phys, environment: env } = state.telemetry;
    this._setTxt("modalHrVal", Math.round(phys.heart_rate_bpm));
    this._setTxt("modalSpo2Val", Math.round(phys.spo2_pct));
    this._setTxt("modalCo2Val", env.co2_mmHg.toFixed(1));
    this._setTxt("modalTempVal", phys.body_temperature_c.toFixed(1));
    const cm = document.getElementById("modalCountermeasures");
    if (cm && state.telemetry.prioritized_countermeasures) {
      cm.innerHTML = state.telemetry.prioritized_countermeasures.slice(0, 3).map((c, i) => `<div class="countermeasure-item" style="margin-bottom:4px;"><strong>${i + 1}.</strong> ${c}</div>`).join("");
    }
  }
  async _loadMatrixCatalog() {
    const rules = await this._telemetry.getMatrixCatalog();
    const extras = window.sonarService?.getAcousticRules?.() || [];
    window.viewportController?.setRules([...(rules || []), ...extras]);
  }
  _setTxt(id, val) { const el = document.getElementById(id); if (el) el.innerText = val; }
  _toggleClass(id, cls, cond) { document.getElementById(id)?.classList.toggle(cls, !!cond); }
}

window.HudController = HudController;
