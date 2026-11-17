/**
 * ==============================================================================
 * SERVICES LAYER: HologramRendererService (PERMANENT LIGHTWEIGHT MODE)
 *
 * Optimized for 0% GPU overhead: native SVG interactivity with hardware
 * acceleration, no particle canvas.
 *
 * TOUCH SUPPORT
 * -------------
 * The markup declares organ focus with onmouseenter/onmouseleave, events that
 * do NOT exist on a tablet. Without this, the hologram — the centerpiece of the
 * interface — stayed inert under the finger on the iPad, which is the target
 * device.
 *
 * On coarse pointers (pointer: coarse) the service replaces that model with a
 * toggle one: a tap focuses the organ, another tap on the same one releases it,
 * and a tap outside the stage deselects it. The mouse keeps the hover behavior
 * untouched.
 * ==============================================================================
 */

class HologramRendererService {
  constructor(canvasId, svgId) {
    this._canvas = document.getElementById(canvasId);
    this._svg = document.getElementById(svgId);
    this._isTouch = window.matchMedia?.("(pointer: coarse)")?.matches ?? false;
    this._selected = null;
  }

  initialize() {
    if (this._canvas) this._canvas.style.display = "none";
    if (!this._svg) return;
    this._bindOrganEvents();
    if (this._isTouch) this._enableTouchToggle();
  }

  resize() {}
  pause() {}
  resume() {}

  /** Interactive nodes of the stage, be they organs or habitat modules. */
  _nodes() {
    return Array.from(
      this._svg.querySelectorAll(".organ-node[data-organ], .habitat-module-node[data-habitat-module]")
    );
  }

  /**
   * Key and family of the element, be it a hologram node or a callout card.
   * Lets tapping the card light up its organ, just like tapping the organ.
   */
  _keyOf(el) {
    const organ = el.getAttribute("data-organ") || el.getAttribute("data-organ-card");
    if (organ) return { key: organ, habitat: false };
    const module = el.getAttribute("data-habitat-module") || el.getAttribute("data-habitat-card");
    return { key: module, habitat: true };
  }

  _focus(node) {
    const { key, habitat } = this._keyOf(node);
    const c = window.hudController;
    if (habitat) c?.focusHabitatModule?.(key);
    else c?.focusOrgan?.(key);
  }

  _unfocus(habitat) {
    const c = window.hudController;
    if (habitat) c?.unfocusHabitatModule?.();
    else c?.unfocusOrgan?.();
  }

  _bindOrganEvents() {
    const names = {
      brain: "Brain (ASTRA)",
      heart: "Heart (ECG)",
      lungs: "Lungs (SpO2)",
      hydration: "Hydration & Renal",
      bones: "Bone Shield",
    };

    this._nodes().forEach((node) => {
      node.style.cursor = "pointer";
      // Accessibility: keyboard reachable and announced by a screen reader
      const { key, habitat } = this._keyOf(node);
      node.setAttribute("tabindex", "0");
      node.setAttribute("role", "button");
      node.setAttribute("aria-label", node.getAttribute("aria-label") || names[key] || key || "Hologram node");

      node.addEventListener("click", () => {
        if (!habitat) window.stateManager?.setSelectedOrgan(names[key] || key);
        window.soundService?.playClick();
      });

      // The keyboard replicates focus without depending on the pointer
      node.addEventListener("focus", () => this._focus(node));
      node.addEventListener("blur", () => this._unfocus(habitat));
      node.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          node.dispatchEvent(new Event("click"));
        }
      });
    });
  }

  /**
   * Tap toggle model, only on coarse pointers.
   * It registers in the capture phase to get ahead of the onmouseenter events
   * iOS synthesizes on tap, preventing both models from competing.
   */
  _enableTouchToggle() {
    const stage = this._svg.closest(".hologram-stage-wrapper") || this._svg;
    const SELECTOR =
      ".organ-node[data-organ], .habitat-module-node[data-habitat-module]," +
      ".hologram-callout[data-organ-card], .hologram-callout[data-habitat-card]";

    // iOS synthesizes mouseenter on tap: if the inline handlers are left in
    // place, they refocus right after the tap has released the focus.
    // They are removed so the toggle model is the only active one.
    stage.querySelectorAll("[onmouseenter], [onmouseleave]").forEach((el) => {
      el.removeAttribute("onmouseenter");
      el.removeAttribute("onmouseleave");
      el.onmouseenter = null;
      el.onmouseleave = null;
    });

    stage.addEventListener(
      "pointerdown",
      (ev) => {
        if (ev.pointerType === "mouse") return;

        const node = ev.target.closest?.(SELECTOR);

        if (!node) {
          // Tap on empty space: release the current selection
          if (this._selected) {
            this._unfocus(this._keyOf(this._selected).habitat);
            this._selected = null;
          }
          return;
        }

        if (this._selected === node) {
          this._unfocus(this._keyOf(node).habitat);
          this._selected = null;
        } else {
          this._focus(node);
          this._selected = node;
        }
      },
      true
    );

    // A tap outside the stage also releases the focus
    document.addEventListener("pointerdown", (ev) => {
      if (ev.pointerType === "mouse" || !this._selected) return;
      if (!stage.contains(ev.target)) {
        this._unfocus(this._keyOf(this._selected).habitat);
        this._selected = null;
      }
    });
  }
}

window.HologramRendererService = HologramRendererService;
