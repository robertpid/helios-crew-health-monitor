/**
 * ==============================================================================
 * CAPA DE CONTROLADORES: HudController
 * Orquestador principal de la UI: vincula Estado con el DOM y Servicios.
 * Mantenido estrictamente bajo 320 líneas mediante delegación modular (SRP).
 * ==============================================================================
 */

class HudController {
  constructor(stateManager, ecgService, telemetryService, soundService = null, wellnessController = null, authService = null) {
    this._state = stateManager;
    this._ecg = ecgService;
    this._telemetry = telemetryService;
    this._sound = soundService || window.soundService;
    this._wellness = wellnessController || (window.WellnessController ? new window.WellnessController(this._sound) : null);
    this._auth = authService || window.authService;
    this._ultimoEstadoModal = false;

    this._nombresKronecker = [
      "CO2xPulso", "CO2xSueño", "CO2xHueso", "CO2xSANS",
      "RadxPulso", "RadxSueño", "RadxHueso", "RadxSANS",
      "PresxPulso", "PresxSueño", "PresxHueso", "PresxSANS"
    ];
  }

  inicializar() {
    this._state.subscribe(state => this.renderizar(state));
    this._telemetry.iniciarPolling();
    this._cargarCatalogoMatriz();
    if (this._auth) {
      this._auth.onCambioSesion(u => this._actualizarBadgeUsuario(u));
      this._actualizarBadgeUsuario(this._auth.obtenerUsuarioActual());
    }
  }

  // --- AUDIO Y VISTAS ---
  toggleAudio() {
    if (!this._sound && window.soundService) this._sound = window.soundService;
    if (this._sound) {
      const mute = this._sound.toggleSilencio();
      const btn = document.getElementById("btnAudioToggle");
      if (btn) {
        btn.innerText = mute ? "🔇 AUDIO: MUTE" : "🔊 AUDIO: ACTIVO";
        btn.style.color = mute ? "var(--text-muted)" : "var(--neon-cyan)";
      }
      if (!mute) this._sound.reproducirClick();
    }
  }

  cambiarVista(nombre) {
    if (this._sound) this._sound.reproducirClick();
    this._state.setVistaActiva(nombre);
  }

  enfocarOrgano(nombre) {
    if (this._sound?.reproducirHover) this._sound.reproducirHover();
    const stg = document.querySelector("#viewBiomedical .hologram-stage-wrapper");
    if (!stg) return;
    stg.classList.add("has-organ-focus");
    stg.querySelectorAll(".organ-node, .organ-connector-line, .hologram-callout").forEach(el => el.classList.remove("is-focused"));
    [`.organ-node[data-organ="${nombre}"]`, `.organ-connector-line[data-organ-line="${nombre}"]`, `.hologram-callout[data-organ-card="${nombre}"]`]
      .forEach(sel => stg.querySelector(sel)?.classList.add("is-focused"));
  }

  desenfocarOrgano() {
    const stg = document.querySelector("#viewBiomedical .hologram-stage-wrapper");
    if (!stg) return;
    stg.classList.remove("has-organ-focus");
    stg.querySelectorAll(".organ-node, .organ-connector-line, .hologram-callout").forEach(el => el.classList.remove("is-focused"));
  }

  enfocarModuloHabitat(modulo) {
    if (this._sound?.reproducirHover) this._sound.reproducirHover();
    const stg = document.querySelector("#viewEnvironmental .hologram-stage-wrapper");
    if (!stg) return;
    stg.classList.add("has-habitat-focus");
    stg.querySelectorAll(".habitat-module-node, .habitat-connector-line, .hologram-callout").forEach(el => el.classList.remove("is-focused"));
    [`.habitat-module-node[data-habitat-module="${modulo}"]`, `.habitat-connector-line[data-habitat-line="${modulo}"]`, `.hologram-callout[data-habitat-card="${modulo}"]`]
      .forEach(sel => stg.querySelector(sel)?.classList.add("is-focused"));
  }

  desenfocarModuloHabitat() {
    const stg = document.querySelector("#viewEnvironmental .hologram-stage-wrapper");
    if (!stg) return;
    stg.classList.remove("has-habitat-focus");
    stg.querySelectorAll(".habitat-module-node, .habitat-connector-line, .hologram-callout").forEach(el => el.classList.remove("is-focused"));
  }

  alternarModeloHabitat(modelo) {
    if (this._sound) this._sound.reproducirClick();
    this._state.setModeloHabitat(modelo);
    ["orion", "mars", "iss"].forEach(m => {
      const cap = m.charAt(0).toUpperCase() + m.slice(1);
      document.getElementById(`btnHabitat${cap}`)?.classList.toggle("active", m === modelo);
      const grp = document.getElementById(`habitat${cap}Group`);
      if (grp) grp.style.display = (m === modelo) ? "block" : "none";
    });
    const sub = document.getElementById("habitatSubtitle");
    if (sub) {
      const titulos = {
        orion: "ORION DEEP SPACE VEHICLE · TRÁNSITO INTERPLANETARIO (0.00g)",
        mars: "BASE ARCADIA PLANITIA (MARTE) · DOMO PRESURIZADO (0.38g)",
        iss: "ESTACIÓN ESPACIAL INTERNACIONAL · ORBITAL LEO (0.00g)"
      };
      sub.innerText = titulos[modelo] || "";
    }
  }

  restablecerModoNominal() {
    if (this._sound) this._sound.reproducirNominal();
    this._state.setModoOperacion("nominal");
  }

  activarModoCrisis() {
    if (this._sound) this._sound.reproducirCrisis();
    this._state.setModoOperacion("crisis");
  }

  toggleModal() {
    if (this._sound) this._sound.reproducirClick();
    this._state.toggleModalAlerta();
  }

  // --- LOGIN Y AUTENTICACIÓN ---
  abrirModalLogin() {
    if (this._sound) this._sound.reproducirClick();
    const modal = document.getElementById("modalLogin");
    const btnCerrar = document.getElementById("btnCloseLoginModal");
    if (modal) modal.style.display = "flex";
    if (btnCerrar) btnCerrar.style.display = this._auth?.obtenerUsuarioActual() ? "block" : "none";
    const err = document.getElementById("loginErrorMsg");
    if (err) err.style.display = "none";
  }

  cerrarModalLogin() {
    if (this._sound) this._sound.reproducirClick();
    const modal = document.getElementById("modalLogin");
    if (modal) modal.style.display = "none";
  }

  seleccionarUsuarioDemo(usuario, pin) {
    const inU = document.getElementById("inputLoginUsuario");
    const inP = document.getElementById("inputLoginPin");
    if (inU) inU.value = usuario;
    if (inP) inP.value = pin;
    this.ejecutarLogin();
  }

  ejecutarLogin() {
    const inU = document.getElementById("inputLoginUsuario");
    const inP = document.getElementById("inputLoginPin");
    const err = document.getElementById("loginErrorMsg");
    if (!inU || !inP || !this._auth) return;

    const res = this._auth.autenticar(inU.value, inP.value);
    if (res.exito) {
      if (this._sound) this._sound.reproducirNominal();
      this.cerrarModalLogin();
      if (res.usuario.rol === "CIRUJANO_VUELO") {
        alert("🩺 BIENVENIDO, CIRUJANO DE VUELO (Dr. Marcus Vance).\nMonitor médico especializado en preparación. Acceso a telemetría de soporte vital concedido.");
      }
    } else {
      if (this._sound) this._sound.reproducirAlerta();
      if (err) { err.innerText = res.error; err.style.display = "block"; }
    }
  }

  _actualizarBadgeUsuario(usuario) {
    if (!usuario) return;
    this._setTxt("userAvatarTag", usuario.avatar || "👨‍🚀");
    this._setTxt("userIdentTag", usuario.rango || usuario.nombre);
    this._setTxt("userRoleTag", `(${usuario.nombre})`);
  }

  // --- DELEGACIÓN WELLNESS ---
  avanzarTarea(t) { this._wellness?.avanzarTarea(t); }
  iniciarExamenOftalmico() { this._wellness?.iniciarExamenOftalmico(); }
  iniciarExamenSonar() { this._wellness?.iniciarExamenSonar(); }
  sincronizarCorreo() { this._wellness?.sincronizarCorreo(); }
  toggleGuiaRespiracion() { this._wellness?.toggleGuiaRespiracion(); }
  responderAsistente(t) { this._wellness?.responderAsistente(t); }
  toggleMatrizTecnica() { this._wellness?.toggleMatrizTecnica(); }

  // --- RENDERIZADO REACTIVO ---
  renderizar(state) {
    this._actualizarPestanas(state.vistaActiva);
    this._actualizarValoresDashboard(state);
  }

  _actualizarValoresDashboard(state) {
    const { fisiologia: fis, ambiente: amb, cognicion: cog, kronecker: kron } = state.telemetria;
    const pill = document.getElementById("statusPill");
    if (pill) {
      pill.innerText = state.tripulanteEstable ? "ESTABLE" : "CRÍTICO";
      pill.className = `badge-status ${state.tripulanteEstable ? "status-stable" : "status-critical"}`;
    }

    // Fisiología
    this._setTxt("valHeart", Math.round(fis.ritmo_cardiaco_bpm));
    this._setTxt("valSpo2", Math.round(fis.spo2_pct));
    this._setTxt("valTemp", fis.temperatura_corporal_c.toFixed(1));
    this._setTxt("valVoiceLatency", Math.round(cog.latencia_voz_ms));
    this._setTxt("valBone", `-${fis.perdida_osea_pct.toFixed(1)}`);

    this._toggleClase("cardHeart", "tile-danger", fis.ritmo_cardiaco_bpm > 100);
    this._toggleClase("cardSpo2", "tile-danger", fis.spo2_pct < 94.0);
    this._toggleClase("cardTemp", "tile-danger", fis.temperatura_corporal_c > 37.8);
    this._toggleClase("cardAstra", "tile-danger", cog.incongruencia_detectada);

    this._setTxt("calloutHeart", `${Math.round(fis.ritmo_cardiaco_bpm)} lpm`);
    this._setTxt("calloutSpo2", `${Math.round(fis.spo2_pct)} %`);
    this._setTxt("calloutBone", `-${fis.perdida_osea_pct.toFixed(1)}%`);
    this._setTxt("calloutFluid", `${fis.liquidos_litros_dia.toFixed(1)} L/d`);
    this._setTxt("calloutAstra", cog.incongruencia_detectada ? "FATIGA OCULTA" : "COHERENTE");
    document.getElementById("nodeHeart")?.classList.toggle("fast", fis.ritmo_cardiaco_bpm > 100);

    // Ambiente
    this._setTxt("valCo2", amb.co2_mmHg.toFixed(1));
    this._setTxt("valRad", amb.radiacion_acumulada_mSv.toFixed(1));
    this._setTxt("valPress", amb.presion_cabina_kpa.toFixed(1));
    this._setTxt("valCabinTemp", amb.temperatura_cabina_c.toFixed(1));
    this._setTxt("valHumidity", amb.humedad_relativa_pct.toFixed(1));
    this._setTxt("valSolarStatus", amb.evento_solar_activo ? "TORMENTA ACTIVA (SPE)" : "S0 QUIETO");
    this._setTxt("envGravity", `${amb.gravedad_g.toFixed(2)} g`);

    this._setTxt("calloutEnvCo2", `${amb.co2_mmHg.toFixed(1)} mmHg`);
    this._setTxt("calloutEnvRad", `${amb.radiacion_acumulada_mSv.toFixed(1)} mSv`);
    this._setTxt("calloutEnvPress", `${amb.presion_cabina_kpa.toFixed(1)} kPa`);
    this._setTxt("calloutEnvTemp", `${amb.temperatura_cabina_c.toFixed(1)} °C`);
    this._setTxt("calloutEnvHum", `${amb.humedad_relativa_pct.toFixed(1)} %`);

    this._toggleClase("cardCo2", "tile-danger", amb.co2_mmHg > 3.0);
    this._toggleClase("cardSolar", "tile-danger", amb.evento_solar_activo);

    this._renderizarMatrizKronecker(kron.indice_argmax, kron.severidad_maxima);

    const cm = document.getElementById("ambientCountermeasuresList");
    if (cm && state.telemetria.contramedidas_priorizadas) {
      cm.innerHTML = state.telemetria.contramedidas_priorizadas.slice(0, 3).map((a, i) => `<div><strong>${i + 1}.</strong> ${a}</div>`).join("");
    }

    this._actualizarModalCritico(state);
    this._wellness?.actualizarHidratacion(state.modoOperacion === "crisis" || (fis.liquidos_litros_dia < 1.5));
  }

  _actualizarPestanas(activa) {
    const tabs = document.querySelectorAll(".nav-tab-btn");
    const vistas = document.querySelectorAll(".view-container");
    tabs.forEach(t => t.classList.remove("active"));
    vistas.forEach(v => {
      v.classList.remove("active-view");
      v.style.setProperty("display", "none", "important");
    });

    const mapa = {
      biomedical: { tab: tabs[0], view: "viewBiomedical" },
      environmental: { tab: tabs[1], view: "viewEnvironmental" },
      matrix: { tab: tabs[2], view: "viewMatrix" }
    };
    if (activa === "biomedical") this._ecg?.reanudar?.();
    else this._ecg?.pausar?.();

    const tgt = mapa[activa];
    if (tgt) {
      tgt.tab?.classList.add("active");
      const v = document.getElementById(tgt.view);
      if (v) { v.classList.add("active-view"); v.style.setProperty("display", "grid", "important"); }
      if (activa === "environmental") setTimeout(() => window.dispatchEvent(new Event("resize")), 60);
    }
  }

  _renderizarMatrizKronecker(idx, sev) {
    const cnt = document.getElementById("kroneckerGrid");
    if (!cnt) return;
    cnt.innerHTML = "";
    for (let i = 0; i < 12; i++) {
      const cel = document.createElement("div");
      const act = (i === idx);
      cel.className = "matrix-cell" + (act ? " active-danger" : "");
      cel.innerHTML = `<strong>${this._nombresKronecker[i]}</strong><br><small>${act ? sev.toFixed(1) : "0.0"}</small>`;
      cnt.appendChild(cel);
    }
    const tag = document.getElementById("matrixMaxSeverity");
    if (tag) {
      tag.innerText = (idx >= 0) ? `Arista Crítica: ${this._nombresKronecker[idx]} (${sev.toFixed(1)}/10)` : "Sin sinergias adversas (0.0/10)";
      tag.style.color = (idx >= 0) ? "var(--neon-red)" : "var(--neon-green)";
    }
  }

  _actualizarModalCritico(state) {
    const modal = document.getElementById("modalAlerta");
    if (!modal) return;
    if (state.modalAlertaAbierto) {
      modal.style.setProperty("display", "flex", "important");
      modal.classList.add("open");
      if (!this._ultimoEstadoModal && this._sound) this._sound.iniciarAlarmaEmergencia();
    } else {
      modal.style.setProperty("display", "none", "important");
      modal.classList.remove("open");
    }
    this._ultimoEstadoModal = !!state.modalAlertaAbierto;

    const { fisiologia: fis, ambiente: amb } = state.telemetria;
    this._setTxt("modalHrVal", Math.round(fis.ritmo_cardiaco_bpm));
    this._setTxt("modalSpo2Val", Math.round(fis.spo2_pct));
    this._setTxt("modalCo2Val", amb.co2_mmHg.toFixed(1));
    this._setTxt("modalTempVal", fis.temperatura_corporal_c.toFixed(1));

    const cm = document.getElementById("modalCountermeasures");
    if (cm && state.telemetria.contramedidas_priorizadas) {
      cm.innerHTML = state.telemetria.contramedidas_priorizadas.slice(0, 3).map((c, i) => `<div class="countermeasure-item" style="margin-bottom:4px;"><strong>${i + 1}.</strong> ${c}</div>`).join("");
    }
  }

  async _cargarCatalogoMatriz() {
    const tbody = document.getElementById("matrixTableBody");
    if (!tbody) return;
    const reglas = await this._telemetry.obtenerCatalogoMatriz();
    if (!reglas?.length) return;
    tbody.innerHTML = "";
    reglas.forEach(r => {
      const cls = (r.nivel === "CRITICA") ? "badge-crit" : (r.nivel === "ALERTA") ? "badge-warn" : "badge-info";
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><strong>${r.id_regla}</strong></td><td><span class="${cls}">${r.nivel}</span></td>
        <td>${r.dominio}</td><td><strong>${r.evaluacion_preliminar}</strong></td>
        <td><ol style="padding-left:14px; margin:0;">${r.contramedidas.map(c => `<li>${c}</li>`).join("")}</ol></td>
        <td>${r.destinatarios.join(", ")}</td><td><small>${r.base_evidencia}</small></td>
      `;
      tbody.appendChild(row);
    });
  }

  _setTxt(id, val) { const el = document.getElementById(id); if (el) el.innerText = val; }
  _toggleClase(id, cls, cond) { document.getElementById(id)?.classList.toggle(cls, !!cond); }
}

window.HudController = HudController;
