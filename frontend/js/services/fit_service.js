/**
 * CAPA DE SERVICIOS: FitService
 * Subsistema de Monitoreo de Hidratación y Nutrición en Microgravedad.
 * Basado en la aplicación de vuelo de la NASA: ISS Food Intake Tracker (FIT - iPad).
 * Registra ingesta de bolsas de agua PWD, raciones de vuelo, sodio y electrolitos.
 * Rigurosamente bajo 400 líneas (Clean Code & SRP).
 */

class FitService {
  constructor(stateManager = null, soundService = null) {
    this._stateManager = stateManager || window.stateManager;
    this._sound = soundService || window.soundService;

    this._volumenMl = 1850;
    this._metaMl = 2200;
    this._calorias = 2150;
    this._sodioMg = 2100;
    this._ejercicioActivo = false;

    this._catalogoRaciones = {
      agua: { nombre: "Bolsa Agua PWD", ml: 250, kcal: 0, na: 5, icono: "💧" },
      electrolito: { nombre: "Bebida Sales Orales", ml: 300, kcal: 35, na: 180, icono: "⚡" },
      cafe: { nombre: "Café/Té Rehidratable", ml: 200, kcal: 20, na: 10, icono: "☕" },
      liofilizada: { nombre: "Ración Liofilizada", ml: 150, kcal: 450, na: 380, icono: "🍲" },
      proteina: { nombre: "Pack Proteína & Ca", ml: 50, kcal: 550, na: 250, icono: "🥫" }
    };

    if (this._stateManager?.subscribe) {
      this._stateManager.subscribe(state => this._sincronizarTelemetria(state?.telemetria));
    }
  }

  inicializar() {
    this.renderizar();
  }

  registrarRacion(tipo) {
    const item = this._catalogoRaciones[tipo];
    if (!item) return;

    this._sound?.reproducirClick?.();
    this._volumenMl += item.ml;
    this._calorias += item.kcal;
    this._sodioMg += item.na;

    // Actualizar telemetría de soporte vital en el StateManager
    const litros = Math.round((this._volumenMl / 1000) * 100) / 100;
    if (this._stateManager?._state?.telemetria?.fisiologia) {
      this._stateManager._state.telemetria.fisiologia.liquidos_litros_dia = litros;
      const elCallout = document.getElementById("calloutFluid");
      if (elCallout) elCallout.innerText = `${litros.toFixed(1)} L/d`;
    }

    // Sumar experiencia gamificada por cumplir protocolo de salud
    window.wellnessController?.sumarExp?.(15);

    // Mensaje de trazabilidad con Houston
    const logBox = document.getElementById("fitLogMsg");
    if (logBox) {
      logBox.innerHTML = `📡 <strong>Código escaneado:</strong> ${item.icono} ${item.nombre} (+${item.ml} mL · +${item.kcal} kcal). Transmitido a Houston BMed.`;
      logBox.style.color = "var(--neon-green)";
      setTimeout(() => { if (logBox) logBox.style.color = "#cbd5e1"; }, 3500);
    }

    this.renderizar();
  }

  ajustarMetaEjercicio(completado) {
    this._ejercicioActivo = completado;
    this._metaMl = completado ? 2700 : 2200;
    const logBox = document.getElementById("fitLogMsg");
    if (logBox) {
      logBox.innerHTML = `🏃 <strong>Ajuste FIT por Ejercicio ARED:</strong> Meta hídrica ampliada a ${this._metaMl} mL (+500 mL de reposición por transpiración).`;
    }
    this.renderizar();
  }

  _sincronizarTelemetria(telemetria) {
    if (!telemetria?.fisiologia?.liquidos_litros_dia) return;
    const l = telemetria.fisiologia.liquidos_litros_dia;
    // Si la telemetría externa cambia significativamente, actualizar
    if (Math.abs(this._volumenMl - l * 1000) > 300) {
      this._volumenMl = Math.round(l * 1000);
      this.renderizar();
    }
  }

  renderizar() {
    const pct = Math.round((this._volumenMl / this._metaMl) * 100);
    const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };

    setTxt("fitVolumeVal", `${this._volumenMl.toLocaleString()} mL`);
    setTxt("fitQuotaTag", `/ ${this._metaMl.toLocaleString()} mL (${pct}%)`);
    setTxt("fitNutriSummary", `Kcal: ${this._calorias} · Sodio (Na): ${this._sodioMg} mg · Ca/Vit D: Nominal`);

    // Estados del semáforo
    const semOpt = document.getElementById("semOptimo");
    const semAvi = document.getElementById("semAviso");
    const semCri = document.getElementById("semCritico");
    const lblOpt = document.getElementById("lblOptimo");
    const lblAvi = document.getElementById("lblAviso");
    const lblCri = document.getElementById("lblCritico");
    const statusTag = document.getElementById("fitStatusTag");

    let estado = "OPTIMO";
    if (this._volumenMl < 1200) estado = "CRITICO";
    else if (this._volumenMl < this._metaMl * 0.85) estado = "AVISO";

    if (semOpt && semAvi && semCri) {
      if (estado === "OPTIMO") {
        semOpt.style.background = "#00ff88";
        semOpt.style.opacity = "1";
        semOpt.style.boxShadow = "0 0 12px rgba(0, 255, 136, 0.7)";
        semAvi.style.opacity = "0.2";
        semCri.style.opacity = "0.2";
        if (lblOpt) { lblOpt.style.color = "var(--neon-green)"; lblOpt.style.fontWeight = "bold"; }
        if (lblAvi) { lblAvi.style.color = "#64748b"; lblAvi.style.fontWeight = "normal"; }
        if (lblCri) { lblCri.style.color = "#64748b"; lblCri.style.fontWeight = "normal"; }
        if (statusTag) { statusTag.innerText = "▲ ÓPTIMO"; statusTag.style.color = "var(--neon-green)"; }
      } else if (estado === "AVISO") {
        semOpt.style.opacity = "0.2";
        semAvi.style.background = "#f59e0b";
        semAvi.style.opacity = "1";
        semAvi.style.boxShadow = "0 0 12px rgba(245, 158, 11, 0.7)";
        semCri.style.opacity = "0.2";
        if (lblOpt) { lblOpt.style.color = "#64748b"; lblOpt.style.fontWeight = "normal"; }
        if (lblAvi) { lblAvi.style.color = "var(--neon-amber)"; lblAvi.style.fontWeight = "bold"; }
        if (lblCri) { lblCri.style.color = "#64748b"; lblCri.style.fontWeight = "normal"; }
        if (statusTag) { statusTag.innerText = "● AVISO (HIDRATAR)"; statusTag.style.color = "var(--neon-amber)"; }
      } else {
        semOpt.style.opacity = "0.2";
        semAvi.style.opacity = "0.2";
        semCri.style.background = "#ff2255";
        semCri.style.opacity = "1";
        semCri.style.boxShadow = "0 0 14px rgba(255, 34, 85, 0.8)";
        if (lblOpt) { lblOpt.style.color = "#64748b"; lblOpt.style.fontWeight = "normal"; }
        if (lblAvi) { lblAvi.style.color = "#64748b"; lblAvi.style.fontWeight = "normal"; }
        if (lblCri) { lblCri.style.color = "var(--neon-red)"; lblCri.style.fontWeight = "bold"; }
        if (statusTag) { statusTag.innerText = "▼ CRÍTICO (RIESGO LITIASIS)"; statusTag.style.color = "var(--neon-red)"; }
      }
    }
  }
}

window.fitService = new FitService(window.stateManager, window.soundService);
