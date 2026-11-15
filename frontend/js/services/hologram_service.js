/**
 * ==============================================================================
 * CAPA DE SERVICIOS: HologramRendererService (MODO LIVIANO PERMANENTE)
 * Optimizado para 0% de sobrecarga de GPU:
 * - Elimina bucles de física de partículas continuos.
 * - Mantiene interactividad SVG táctil y animaciones CSS nativas por hardware.
 * ==============================================================================
 */

class HologramRendererService {
  constructor(canvasId, svgId) {
    this._canvas = document.getElementById(canvasId);
    this._svg = document.getElementById(svgId);
  }

  inicializar() {
    // En modo liviano no se crean bucles de partículas por frame
    // El fondo utiliza cuadrículas vectoriales CSS de cero impacto en CPU/GPU
    if (this._canvas) {
      this._canvas.style.display = "none";
    }
    this._enlazarEventosOrganos();
  }

  redimensionar() {
    // En modo liviano no requiere repintado de canvas
  }

  pausar() {
    // No-op en modo liviano
  }

  reanudar() {
    // No-op en modo liviano
  }

  _enlazarEventosOrganos() {
    if (!this._svg) return;

    const nodosInteraccion = [
      { id: "nodeBrain", organo: "Cerebro" },
      { id: "nodeHeart", organo: "Corazón" },
      { id: "nodeLungs", organo: "Pulmones" },
      { id: "nodeKidneys", organo: "Riñones" },
      { id: "nodeBone", organo: "Masa Ósea" },
    ];

    nodosInteraccion.forEach(({ id, organo }) => {
      const el = document.getElementById(id);
      if (el) {
        el.style.cursor = "pointer";
        el.addEventListener("mouseenter", () => {
          el.style.filter = "brightness(1.5)";
        });
        el.addEventListener("mouseleave", () => {
          el.style.filter = "";
        });
        el.addEventListener("click", () => {
          if (window.stateManager) {
            window.stateManager.setOrganoSeleccionado(organo);
          }
          if (window.soundService) {
            window.soundService.reproducirClick();
          }
        });
      }
    });
  }
}

window.HologramRendererService = HologramRendererService;
