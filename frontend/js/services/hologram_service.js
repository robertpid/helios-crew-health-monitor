/**
 * ==============================================================================
 * CAPA DE SERVICIOS: HologramRendererService (MODO LIVIANO PERMANENTE)
 *
 * Optimizado para 0% de sobrecarga de GPU: interactividad SVG nativa con
 * aceleración por hardware, sin lienzo de partículas.
 *
 * SOPORTE TÁCTIL
 * --------------
 * El marcado declara el foco de órganos con onmouseenter/onmouseleave, eventos
 * que NO existen en una tableta. Sin esto, el holograma — el elemento central
 * de la interfaz — quedaba inerte bajo el dedo en el iPad, que es el
 * dispositivo de destino.
 *
 * En punteros gruesos (pointer: coarse) el servicio sustituye ese modelo por
 * uno de alternancia: un toque enfoca el órgano, otro toque sobre el mismo lo
 * libera, y un toque fuera del escenario lo deselecciona. El ratón conserva
 * intacto el comportamiento de hover.
 * ==============================================================================
 */

class HologramRendererService {
  constructor(canvasId, svgId) {
    this._canvas = document.getElementById(canvasId);
    this._svg = document.getElementById(svgId);
    this._esTactil = window.matchMedia?.("(pointer: coarse)")?.matches ?? false;
    this._seleccionado = null;
  }

  inicializar() {
    if (this._canvas) this._canvas.style.display = "none";
    if (!this._svg) return;
    this._enlazarEventosOrganos();
    if (this._esTactil) this._habilitarAlternanciaTactil();
  }

  redimensionar() {}
  pausar() {}
  reanudar() {}

  /** Nodos interactivos del escenario, sean órganos o módulos del hábitat. */
  _nodos() {
    return Array.from(
      this._svg.querySelectorAll(".organ-node[data-organ], .habitat-module-node[data-habitat-module]")
    );
  }

  /**
   * Clave y familia del elemento, sea nodo del holograma o tarjeta de rótulo.
   * Permite que tocar la tarjeta ilumine su órgano, igual que tocar el órgano.
   */
  _claveDe(el) {
    const organo = el.getAttribute("data-organ") || el.getAttribute("data-organ-card");
    if (organo) return { clave: organo, habitat: false };
    const modulo = el.getAttribute("data-habitat-module") || el.getAttribute("data-habitat-card");
    return { clave: modulo, habitat: true };
  }

  _enfocar(nodo) {
    const { clave, habitat } = this._claveDe(nodo);
    const c = window.hudController;
    if (habitat) c?.enfocarModuloHabitat?.(clave);
    else c?.enfocarOrgano?.(clave);
  }

  _desenfocar(habitat) {
    const c = window.hudController;
    if (habitat) c?.desenfocarModuloHabitat?.();
    else c?.desenfocarOrgano?.();
  }

  _enlazarEventosOrganos() {
    const nombres = {
      cerebro: "Cerebro (ASTRA)",
      corazon: "Corazón (ECG)",
      pulmones: "Pulmones (SpO2)",
      hidratacion: "Hidratación & Renal",
      huesos: "Escudo Óseo",
    };

    this._nodos().forEach((nodo) => {
      nodo.style.cursor = "pointer";
      // Accesibilidad: alcanzable por teclado y anunciado por lector de pantalla
      const { clave, habitat } = this._claveDe(nodo);
      nodo.setAttribute("tabindex", "0");
      nodo.setAttribute("role", "button");
      nodo.setAttribute("aria-label", nombres[clave] || clave || "Nodo del holograma");

      nodo.addEventListener("click", () => {
        if (!habitat) window.stateManager?.setOrganoSeleccionado(nombres[clave] || clave);
        window.soundService?.reproducirClick();
      });

      // El teclado replica el foco sin depender del puntero
      nodo.addEventListener("focus", () => this._enfocar(nodo));
      nodo.addEventListener("blur", () => this._desenfocar(habitat));
      nodo.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          nodo.dispatchEvent(new Event("click"));
        }
      });
    });
  }

  /**
   * Modelo de alternancia por toque, sólo en punteros gruesos.
   * Se registra en fase de captura para adelantarse a los onmouseenter que
   * iOS sintetiza al tocar, evitando que ambos modelos compitan.
   */
  _habilitarAlternanciaTactil() {
    const escenario = this._svg.closest(".hologram-stage-wrapper") || this._svg;
    const SELECTOR =
      ".organ-node[data-organ], .habitat-module-node[data-habitat-module]," +
      ".hologram-callout[data-organ-card], .hologram-callout[data-habitat-card]";

    // iOS sintetiza mouseenter al tocar: si se dejan los manejadores en línea,
    // vuelven a enfocar justo después de que el toque haya liberado el foco.
    // Se retiran para que el modelo de alternancia sea el único activo.
    escenario.querySelectorAll("[onmouseenter], [onmouseleave]").forEach((el) => {
      el.removeAttribute("onmouseenter");
      el.removeAttribute("onmouseleave");
      el.onmouseenter = null;
      el.onmouseleave = null;
    });

    escenario.addEventListener(
      "pointerdown",
      (ev) => {
        if (ev.pointerType === "mouse") return;

        const nodo = ev.target.closest?.(SELECTOR);

        if (!nodo) {
          // Toque en vacío: liberar la selección vigente
          if (this._seleccionado) {
            this._desenfocar(this._claveDe(this._seleccionado).habitat);
            this._seleccionado = null;
          }
          return;
        }

        if (this._seleccionado === nodo) {
          this._desenfocar(this._claveDe(nodo).habitat);
          this._seleccionado = null;
        } else {
          this._enfocar(nodo);
          this._seleccionado = nodo;
        }
      },
      true
    );

    // Un toque fuera del escenario también libera el foco
    document.addEventListener("pointerdown", (ev) => {
      if (ev.pointerType === "mouse" || !this._seleccionado) return;
      if (!escenario.contains(ev.target)) {
        this._desenfocar(this._claveDe(this._seleccionado).habitat);
        this._seleccionado = null;
      }
    });
  }
}

window.HologramRendererService = HologramRendererService;
