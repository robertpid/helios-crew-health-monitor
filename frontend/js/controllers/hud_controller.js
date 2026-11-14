/**
 * ==============================================================================
 * CAPA DE CONTROLADORES (CONTROLLERS): HudController
 * Orquestador principal de la UI: vincula el Estado con el DOM y los Servicios.
 * ==============================================================================
 */

class HudController {
  constructor(stateManager, ecgService, telemetryService, soundService = null) {
    this._state = stateManager;
    this._ecg = ecgService;
    this._telemetry = telemetryService;
    this._sound = soundService || window.soundService;
    this._ultimoEstadoModal = false;

    this._nombresAristasKronecker = [
      "CO2xPulso", "CO2xSueño", "CO2xHueso", "CO2xSANS",
      "RadxPulso", "RadxSueño", "RadxHueso", "RadxSANS",
      "PresxPulso", "PresxSueño", "PresxHueso", "PresxSANS"
    ];
  }

  inicializar() {
    // 1. Suscribirse a cambios reactivos del Estado
    this._state.subscribe(state => this.renderizar(state));

    // 2. Iniciar polling asíncrono con el backend
    this._telemetry.iniciarPolling();

    // 3. Cargar tabla de la matriz de decisiones
    this._cargarCatalogoMatriz();
  }

  toggleAudio() {
    if (!this._sound && window.soundService) {
      this._sound = window.soundService;
    }
    if (this._sound) {
      const silenciado = this._sound.toggleSilencio();
      const btn = document.getElementById("btnAudioToggle");
      if (btn) {
        btn.innerText = silenciado ? "🔇 AUDIO: MUTE" : "🔊 AUDIO: ACTIVO";
        btn.style.color = silenciado ? "var(--text-muted)" : "var(--neon-cyan)";
      }
      if (!silenciado) {
        this._sound.reproducirClick();
      }
    }
  }

  cambiarVista(nombreVista) {
    if (this._sound) this._sound.reproducirClick();
    this._state.setVistaActiva(nombreVista);
  }

  cambiarHabitat(habitatKey) {
    this._state.setHabitat(habitatKey);
  }

  alternarModeloHabitat(tipo) {
    if (this._sound) this._sound.reproducirCambioHabitat();

    const orion = document.getElementById("habitatOrionGroup");
    const mars = document.getElementById("habitatMarsGroup");
    const iss = document.getElementById("habitatIssGroup");
    const btnOrion = document.getElementById("btnHabitatOrion");
    const btnMars = document.getElementById("btnHabitatMars");
    const btnIss = document.getElementById("btnHabitatIss");
    const sub = document.getElementById("habitatSubtitle");

    const lCo2 = document.getElementById("labelEnvCo2");
    const lRad = document.getElementById("labelEnvRad");
    const lTemp = document.getElementById("labelEnvTemp");
    const lPress = document.getElementById("labelEnvPress");
    const lHum = document.getElementById("labelEnvHum");

    if (tipo === "mars") {
      if (orion) orion.style.display = "none";
      if (mars) mars.style.display = "block";
      if (iss) iss.style.display = "none";
      if (btnOrion) btnOrion.classList.remove("active");
      if (btnMars) btnMars.classList.add("active");
      if (btnIss) btnIss.classList.remove("active");
      if (sub) sub.innerText = "BASE MARCIANA DE SUPERFICIE · DOMO DE REGOLITO & MOXIE (0.38g)";

      if (lCo2) lCo2.innerText = "BIORREACTOR MOXIE (ppCO₂)";
      if (lRad) lRad.innerText = "BLINDAJE DE REGOLITO (2m)";
      if (lTemp) lTemp.innerText = "CONTROL TÉRMICO DOMO";
      if (lPress) lPress.innerText = "PRESIÓN INTERIOR DOMO";
      if (lHum) lHum.innerText = "HUMEDAD INVERNADERO";

      this.cambiarHabitat("BASE_MARTE");
    } else if (tipo === "iss") {
      if (orion) orion.style.display = "none";
      if (mars) mars.style.display = "none";
      if (iss) iss.style.display = "block";
      if (btnOrion) btnOrion.classList.remove("active");
      if (btnMars) btnMars.classList.remove("active");
      if (btnIss) btnIss.classList.add("active");
      if (sub) sub.innerText = "ESTACIÓN ESPACIAL INTERNACIONAL · ÓRBITA LEO 400 KM (0.00g)";

      if (lCo2) lCo2.innerText = "SISTEMA CDRA (ppCO₂)";
      if (lRad) lRad.innerText = "BLINDAJE WHIPPLE (LEO)";
      if (lTemp) lTemp.innerText = "BUCLE TÉRMICO AMONIACO";
      if (lPress) lPress.innerText = "PRESIÓN MÓDULO NODE 2";
      if (lHum) lHum.innerText = "HUMEDAD HABITÁCULO";

      this.cambiarHabitat("ESTACION_ESPACIAL");
    } else {
      // NAVE ORION (Tránsito de espacio profundo)
      if (orion) orion.style.display = "block";
      if (mars) mars.style.display = "none";
      if (iss) iss.style.display = "none";
      if (btnOrion) btnOrion.classList.add("active");
      if (btnMars) btnMars.classList.remove("active");
      if (btnIss) btnIss.classList.remove("active");
      if (sub) sub.innerText = "ORION DEEP SPACE VEHICLE · TRÁNSITO INTERPLANETARIO (0.00g)";

      if (lCo2) lCo2.innerText = "ECLSS SCRUBBER (ppCO₂)";
      if (lRad) lRad.innerText = "BLINDAJE RADIACIÓN (SPE)";
      if (lTemp) lTemp.innerText = "CONTROL TÉRMICO (ATCS)";
      if (lPress) lPress.innerText = "PRESIÓN CASCO (HULL)";
      if (lHum) lHum.innerText = "HUMEDAD ATMOSFÉRICA";

      this.cambiarHabitat("TRANSITO_MARTE");
    }
  }

  activarModoCrisis() {
    this._state.activarModoCrisis();
    if (this._sound) this._sound.iniciarAlarmaEmergencia();
  }

  restablecerModoNominal() {
    if (this._sound) {
      this._sound.detenerAlarmaEmergencia();
      this._sound.reproducirClick();
    }
    this._state.restablecerModoNominal();
  }

  toggleModal() {
    if (this._sound) this._sound.reproducirClick();
    const actual = this._state.getState().modalAlertaAbierto;
    this._state.setModalAlerta(!actual);
  }

  renderizar(state) {
    const tel = state.telemetria;
    const fis = tel.fisiologia;
    const amb = tel.ambiente;
    const cog = tel.cognicion;
    const kron = tel.kronecker;

    // Control dinámico de Sirena de Emergencia / Alarma Sonora
    const hayEmergencia = state.modoCrisis ||
      kron.estres_severo ||
      amb.co2_mmHg > 3.0 ||
      amb.evento_solar_activo ||
      fis.ritmo_cardiaco_bpm > 100 ||
      fis.spo2_pct < 94.0;

    if (this._sound) {
      if (hayEmergencia) {
        this._sound.iniciarAlarmaEmergencia();
      } else {
        this._sound.detenerAlarmaEmergencia();
      }
    }

    // 1. Renderizar pestañas activas
    this._actualizarPestanas(state.vistaActiva);

    // 2. Renderizar Header y Badge de estado
    const statusPill = document.getElementById("statusPill");
    if (statusPill) {
      if (state.modoCrisis || kron.estres_severo) {
        statusPill.className = "badge-status status-critical alarm-flashing";
        statusPill.innerText = "CRÍTICO";
      } else {
        statusPill.className = "badge-status status-stable";
        statusPill.innerText = "ESTABLE";
      }
    }

    // 3. Sincronizar Frecuencia Cardíaca con el motor ECG
    if (this._ecg) {
      this._ecg.actualizarFrecuenciaCardiaca(fis.ritmo_cardiaco_bpm);
    }
    const ecgTag = document.getElementById("ecgHrTag");
    if (ecgTag) {
      ecgTag.innerText = `${Math.round(fis.ritmo_cardiaco_bpm)} BPM`;
      ecgTag.style.color = (fis.ritmo_cardiaco_bpm > 100) ? "var(--neon-red)" : "var(--neon-green)";
    }

    // 4. Actualizar Valores Numéricos Biomédicos (Ventana 1)
    this._actualizarElementoTexto("valHeart", Math.round(fis.ritmo_cardiaco_bpm));
    this._actualizarElementoTexto("valSpo2", Math.round(fis.spo2_pct));
    this._actualizarElementoTexto("valBp", `${fis.presion_sistolica}/${fis.presion_diastolica}`);
    this._actualizarElementoTexto("valTemp", fis.temperatura_corporal_c.toFixed(1));
    this._actualizarElementoTexto("valVoiceLatency", Math.round(cog.latencia_voz_ms));
    this._actualizarElementoTexto("valBone", `-${fis.perdida_osea_pct.toFixed(1)}`);

    // Modificadores de Alerta en Tiles
    this._toggleClase("cardHeart", "tile-danger", fis.ritmo_cardiaco_bpm > 100);
    this._toggleClase("cardSpo2", "tile-danger", fis.spo2_pct < 94.0);
    this._toggleClase("cardTemp", "tile-danger", fis.temperatura_corporal_c > 37.8);
    this._toggleClase("cardAstra", "tile-danger", cog.incongruencia_detectada);

    // 5. Actualizar Callouts del Holograma
    this._actualizarElementoTexto("calloutHeart", `${Math.round(fis.ritmo_cardiaco_bpm)} lpm`);
    this._actualizarElementoTexto("calloutSpo2", `${Math.round(fis.spo2_pct)} %`);
    this._actualizarElementoTexto("calloutBone", `-${fis.perdida_osea_pct.toFixed(1)}%`);
    this._actualizarElementoTexto("calloutFluid", `${fis.liquidos_litros_dia.toFixed(1)} L/d`);
    this._actualizarElementoTexto("calloutAstra", cog.incongruencia_detectada ? "FATIGA OCULTA" : "COHERENTE");

    // Pulso del corazón holográfico
    const heartNode = document.getElementById("nodeHeart");
    if (heartNode) {
      if (fis.ritmo_cardiaco_bpm > 100) {
        heartNode.classList.add("fast");
      } else {
        heartNode.classList.remove("fast");
      }
    }

    // 6. Actualizar Métricas Ambientales (Ventana 2)
    this._actualizarElementoTexto("valCo2", amb.co2_mmHg.toFixed(1));
    this._actualizarElementoTexto("valRad", amb.radiacion_acumulada_mSv.toFixed(1));
    this._actualizarElementoTexto("valPress", amb.presion_cabina_kpa.toFixed(1));
    this._actualizarElementoTexto("valCabinTemp", amb.temperatura_cabina_c.toFixed(1));
    this._actualizarElementoTexto("valHumidity", amb.humedad_relativa_pct.toFixed(1));
    this._actualizarElementoTexto("valSolarStatus", amb.evento_solar_activo ? "TORMENTA ACTIVA (SPE)" : "S0 QUIETO");
    this._actualizarElementoTexto("envGravity", `${amb.gravedad_g.toFixed(2)} g`);

    // Callouts Holográficos del Hábitat Espacial
    this._actualizarElementoTexto("calloutEnvCo2", `${amb.co2_mmHg.toFixed(1)} mmHg`);
    this._actualizarElementoTexto("calloutEnvRad", `${amb.radiacion_acumulada_mSv.toFixed(1)} mSv`);
    this._actualizarElementoTexto("calloutEnvPress", `${amb.presion_cabina_kpa.toFixed(1)} kPa`);
    this._actualizarElementoTexto("calloutEnvTemp", `${amb.temperatura_cabina_c.toFixed(1)} °C`);
    this._actualizarElementoTexto("calloutEnvHum", `${amb.humedad_relativa_pct.toFixed(1)} %`);

    this._toggleClase("cardCo2", "tile-danger", amb.co2_mmHg > 3.0);
    this._toggleClase("cardSolar", "tile-danger", amb.evento_solar_activo);

    // 7. Renderizar Matriz de Calor de Kronecker (R^12)
    this._renderizarMatrizKronecker(kron.indice_argmax, kron.severidad_maxima);

    // 8. Renderizar Banner de Contramedidas Ambientales (Máximo 3)
    const cmAmbiental = document.getElementById("ambientCountermeasuresList");
    if (cmAmbiental && tel.contramedidas_priorizadas) {
      cmAmbiental.innerHTML = tel.contramedidas_priorizadas
        .slice(0, 3)
        .map((accion, i) => `<div><strong>${i + 1}.</strong> ${accion}</div>`)
        .join("");
    }

    // 9. Sincronizar Modal de Alerta Crítica (Boceto Réplica)
    this._actualizarModalCritico(state);
  }

  _actualizarPestanas(vistaActiva) {
    const tabs = document.querySelectorAll(".nav-tab-btn");
    const vistas = document.querySelectorAll(".view-container");

    tabs.forEach(t => t.classList.remove("active"));
    vistas.forEach(v => {
      v.classList.remove("active-view");
      v.style.setProperty("display", "none", "important");
    });

    if (vistaActiva === "biomedical") {
      if (tabs[0]) tabs[0].classList.add("active");
      const v = document.getElementById("viewBiomedical");
      if (v) {
        v.classList.add("active-view");
        v.style.setProperty("display", "grid", "important");
      }
    } else if (vistaActiva === "environmental") {
      if (tabs[1]) tabs[1].classList.add("active");
      const v = document.getElementById("viewEnvironmental");
      if (v) {
        v.classList.add("active-view");
        v.style.setProperty("display", "grid", "important");
      }
      setTimeout(() => window.dispatchEvent(new Event("resize")), 60);
    } else if (vistaActiva === "matrix") {
      if (tabs[2]) tabs[2].classList.add("active");
      const v = document.getElementById("viewMatrix");
      if (v) {
        v.classList.add("active-view");
        v.style.setProperty("display", "block", "important");
      }
    }
  }

  _renderizarMatrizKronecker(indiceActivo, severidad) {
    const container = document.getElementById("kroneckerGrid");
    if (!container) return;

    container.innerHTML = "";
    for (let i = 0; i < 12; i++) {
      const celda = document.createElement("div");
      const esActiva = (i === indiceActivo);
      celda.className = "matrix-cell" + (esActiva ? " active-danger" : "");
      celda.innerHTML = `<strong>${this._nombresAristasKronecker[i]}</strong><br><small>${esActiva ? severidad.toFixed(1) : "0.0"}</small>`;
      container.appendChild(celda);
    }

    const tagSeveridad = document.getElementById("matrixMaxSeverity");
    if (tagSeveridad) {
      if (indiceActivo >= 0) {
        tagSeveridad.innerText = `Arista Crítica: ${this._nombresAristasKronecker[indiceActivo]} (${severidad.toFixed(1)}/10)`;
        tagSeveridad.style.color = "var(--neon-red)";
      } else {
        tagSeveridad.innerText = "Sin sinergias adversas (0.0/10)";
        tagSeveridad.style.color = "var(--neon-green)";
      }
    }
  }

  _actualizarModalCritico(state) {
    const modalBackdrop = document.getElementById("modalAlerta");
    if (!modalBackdrop) return;

    if (state.modalAlertaAbierto) {
      if (!this._ultimoEstadoModal && this._sound) {
        this._sound.iniciarAlarmaEmergencia();
      }
      modalBackdrop.classList.add("open");
    } else {
      modalBackdrop.classList.remove("open");
    }
    this._ultimoEstadoModal = !!state.modalAlertaAbierto;

    const cmContainer = document.getElementById("modalCountermeasures");
    if (cmContainer && state.telemetria.contramedidas_priorizadas) {
      cmContainer.innerHTML = state.telemetria.contramedidas_priorizadas
        .slice(0, 3)
        .map((cm, idx) => `<div class="countermeasure-item">${idx + 1}. ${cm}</div>`)
        .join("");
    }
  }

  async _cargarCatalogoMatriz() {
    const tbody = document.getElementById("matrixTableBody");
    if (!tbody) return;

    const reglas = await this._telemetry.obtenerCatalogoMatriz();
    if (!reglas || reglas.length === 0) return;

    tbody.innerHTML = "";
    reglas.forEach(r => {
      const badgeClass = (r.nivel === "CRITICA") ? "badge-crit" : (r.nivel === "ALERTA") ? "badge-warn" : "badge-info";
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><strong>${r.id_regla}</strong></td>
        <td><span class="${badgeClass}">${r.nivel}</span></td>
        <td>${r.dominio}</td>
        <td><strong>${r.evaluacion_preliminar}</strong></td>
        <td>
          <ol style="padding-left:14px; margin:0;">
            ${r.contramedidas.map(c => `<li>${c}</li>`).join("")}
          </ol>
        </td>
        <td>${r.destinatarios.join(", ")}</td>
        <td><small>${r.base_evidencia}</small></td>
      `;
      tbody.appendChild(row);
    });
  }

  _actualizarElementoTexto(id, valor) {
    const el = document.getElementById(id);
    if (el) el.innerText = valor;
  }

  _toggleClase(id, clase, condicion) {
    const el = document.getElementById(id);
    if (el) {
      if (condicion) el.classList.add(clase);
      else el.classList.remove(clase);
    }
  }
}

window.HudController = HudController;
