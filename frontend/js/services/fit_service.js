/**
 * SERVICES LAYER: FitService
 * Hydration and Nutrition Monitoring Subsystem in Microgravity.
 * Based on the NASA flight application: ISS Food Intake Tracker (FIT - iPad).
 * Logs PWD water bag intake, flight rations, sodium and electrolytes.
 * Strictly under 400 lines (Clean Code & SRP).
 */

class FitService {
  constructor(stateManager = null, soundService = null) {
    this._stateManager = stateManager || window.stateManager;
    this._sound = soundService || window.soundService;

    this._volumeMl = 1850;
    this._goalMl = 2200;
    this._calories = 2150;
    this._sodiumMg = 2100;
    this._exerciseActive = false;

    this._rationCatalog = {
      water: { name: "PWD Water Bag", ml: 250, kcal: 0, na: 5, icon: "💧" },
      electrolyte: { name: "Oral Salts Drink", ml: 300, kcal: 35, na: 180, icon: "⚡" },
      coffee: { name: "Rehydratable Coffee/Tea", ml: 200, kcal: 20, na: 10, icon: "☕" },
      freezeDried: { name: "Freeze-Dried Ration", ml: 150, kcal: 450, na: 380, icon: "🍲" },
      protein: { name: "Protein & Ca Pack", ml: 50, kcal: 550, na: 250, icon: "🥫" }
    };

    if (this._stateManager?.subscribe) {
      this._stateManager.subscribe(state => this._syncTelemetry(state?.telemetry));
    }
  }

  initialize() {
    this.render();
  }

  logServing(type) {
    const item = this._rationCatalog[type];
    if (!item) return;

    this._sound?.playClick?.();
    this._volumeMl += item.ml;
    this._calories += item.kcal;
    this._sodiumMg += item.na;

    // Update the life support telemetry in the StateManager
    const liters = Math.round((this._volumeMl / 1000) * 100) / 100;
    if (this._stateManager?._state?.telemetry?.physiology) {
      this._stateManager._state.telemetry.physiology.fluids_liters_per_day = liters;
      const calloutEl = document.getElementById("calloutFluid");
      if (calloutEl) calloutEl.innerText = `${liters.toFixed(1)} L/d`;
    }

    // Add gamified experience for following the health protocol
    window.wellnessController?.addXp?.(15);

    // Traceability message with Houston
    const logBox = document.getElementById("fitLogMsg");
    if (logBox) {
      logBox.innerHTML = `📡 <strong>Code scanned:</strong> ${item.icon} ${item.name} (+${item.ml} mL · +${item.kcal} kcal). Transmitted to Houston BMed.`;
      logBox.style.color = "var(--neon-green)";
      setTimeout(() => { if (logBox) logBox.style.color = "#cbd5e1"; }, 3500);
    }

    this.render();
  }

  adjustExerciseGoal(completed) {
    this._exerciseActive = completed;
    this._goalMl = completed ? 2700 : 2200;
    const logBox = document.getElementById("fitLogMsg");
    if (logBox) {
      logBox.innerHTML = `🏃 <strong>FIT adjustment for ARED exercise:</strong> Fluid goal raised to ${this._goalMl} mL (+500 mL to replace perspiration).`;
    }
    this.render();
  }

  _syncTelemetry(telemetry) {
    if (!telemetry?.physiology?.fluids_liters_per_day) return;
    const l = telemetry.physiology.fluids_liters_per_day;
    // If the external telemetry changes significantly, update
    if (Math.abs(this._volumeMl - l * 1000) > 300) {
      this._volumeMl = Math.round(l * 1000);
      this.render();
    }
  }

  render() {
    const pct = Math.round((this._volumeMl / this._goalMl) * 100);
    const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };

    setTxt("fitVolumeVal", `${this._volumeMl.toLocaleString()} mL`);
    setTxt("fitQuotaTag", `/ ${this._goalMl.toLocaleString()} mL (${pct}%)`);
    setTxt("fitNutriSummary", `Kcal: ${this._calories} · Sodium (Na): ${this._sodiumMg} mg · Ca/Vit D: Nominal`);

    // Traffic light states
    const semOpt = document.getElementById("semOptimal");
    const semWarn = document.getElementById("semWarning");
    const semCrit = document.getElementById("semCritical");
    const lblOpt = document.getElementById("lblOptimal");
    const lblWarn = document.getElementById("lblWarning");
    const lblCrit = document.getElementById("lblCritical");
    const statusTag = document.getElementById("fitStatusTag");

    let state = "OPTIMAL";
    if (this._volumeMl < 1200) state = "CRITICAL";
    else if (this._volumeMl < this._goalMl * 0.85) state = "WARNING";

    if (semOpt && semWarn && semCrit) {
      if (state === "OPTIMAL") {
        semOpt.style.background = "#00ff88";
        semOpt.style.opacity = "1";
        semOpt.style.boxShadow = "0 0 12px rgba(0, 255, 136, 0.7)";
        semWarn.style.opacity = "0.2";
        semCrit.style.opacity = "0.2";
        if (lblOpt) { lblOpt.style.color = "var(--neon-green)"; lblOpt.style.fontWeight = "bold"; }
        if (lblWarn) { lblWarn.style.color = "#64748b"; lblWarn.style.fontWeight = "normal"; }
        if (lblCrit) { lblCrit.style.color = "#64748b"; lblCrit.style.fontWeight = "normal"; }
        if (statusTag) { statusTag.innerText = "▲ OPTIMAL"; statusTag.style.color = "var(--neon-green)"; }
      } else if (state === "WARNING") {
        semOpt.style.opacity = "0.2";
        semWarn.style.background = "#f59e0b";
        semWarn.style.opacity = "1";
        semWarn.style.boxShadow = "0 0 12px rgba(245, 158, 11, 0.7)";
        semCrit.style.opacity = "0.2";
        if (lblOpt) { lblOpt.style.color = "#64748b"; lblOpt.style.fontWeight = "normal"; }
        if (lblWarn) { lblWarn.style.color = "var(--neon-amber)"; lblWarn.style.fontWeight = "bold"; }
        if (lblCrit) { lblCrit.style.color = "#64748b"; lblCrit.style.fontWeight = "normal"; }
        if (statusTag) { statusTag.innerText = "● WARNING (HYDRATE)"; statusTag.style.color = "var(--neon-amber)"; }
      } else {
        semOpt.style.opacity = "0.2";
        semWarn.style.opacity = "0.2";
        semCrit.style.background = "#ff2255";
        semCrit.style.opacity = "1";
        semCrit.style.boxShadow = "0 0 14px rgba(255, 34, 85, 0.8)";
        if (lblOpt) { lblOpt.style.color = "#64748b"; lblOpt.style.fontWeight = "normal"; }
        if (lblWarn) { lblWarn.style.color = "#64748b"; lblWarn.style.fontWeight = "normal"; }
        if (lblCrit) { lblCrit.style.color = "var(--neon-red)"; lblCrit.style.fontWeight = "bold"; }
        if (statusTag) { statusTag.innerText = "▼ CRITICAL (STONE RISK)"; statusTag.style.color = "var(--neon-red)"; }
      }
    }
  }
}

window.fitService = new FitService(window.stateManager, window.soundService);
