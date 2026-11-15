/**
 * ==============================================================================
 * CAPA DE SERVICIOS: HologramRendererService (MODO LIVIANO PERMANENTE)
 * Optimizado para 0% de sobrecarga de GPU:
 * - Interactividad SVG nativa con aceleración por hardware.
 * ==============================================================================
 */

class HologramRendererService {
  constructor(canvasId, svgId) {
    this._canvas = document.getElementById(canvasId);
    this._svg = document.getElementById(svgId);
  }

  inicializar() {
    if (this._canvas) this._canvas.style.display = "none";
    this._enlazarEventosOrganos();
  }

  redimensionar() {}
  pausar() {}
  reanudar() {}

  _enlazarEventosOrganos() {
    if (!this._svg) return;

    // Vincular clics de selección táctil en los nodos de órganos
    const mapaOrganos = [
      { sel: '.organ-node[data-organ="cerebro"]', nombre: "Cerebro (ASTRA)" },
      { sel: '.organ-node[data-organ="corazon"]', nombre: "Corazón (ECG)" },
      { sel: '.organ-node[data-organ="pulmones"]', nombre: "Pulmones (SpO2)" },
      { sel: '.organ-node[data-organ="hidratacion"]', nombre: "Hidratación & Renal" },
      { sel: '.organ-node[data-organ="huesos"]', nombre: "Escudo Óseo" },
    ];

    mapaOrganos.forEach(({ sel, nombre }) => {
      const el = this._svg.querySelector(sel);
      if (el) {
        el.style.cursor = "pointer";
        el.addEventListener("click", () => {
          window.stateManager?.setOrganoSeleccionado(nombre);
          window.soundService?.reproducirClick();
        });
      }
    });
  }
}

window.HologramRendererService = HologramRendererService;
