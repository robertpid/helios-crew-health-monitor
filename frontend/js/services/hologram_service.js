/**
 * ==============================================================================
 * CAPA DE SERVICIOS (CLIENT SERVICES): HologramRendererService
 * Gestiona el sistema de partículas cuánticas y la interactividad del holograma.
 * ==============================================================================
 */

class HologramRendererService {
  constructor(particlesCanvasId, svgBodyId) {
    this._canvas = document.getElementById(particlesCanvasId);
    this._ctx = this._canvas ? this._canvas.getContext("2d") : null;
    this._svg = document.getElementById(svgBodyId);
    this._particles = [];
    this._animId = null;
    this._numParticles = 45;
  }

  inicializar() {
    if (this._canvas && this._ctx) {
      this.redimensionar();
      window.addEventListener("resize", () => this.redimensionar());
      this._crearParticulas();
      this._iniciarBucleParticulas();
    }
    this._enlazarEventosOrganos();
  }

  redimensionar() {
    if (!this._canvas) return;
    const parent = this._canvas.parentElement;
    if (parent && parent.clientWidth > 0 && parent.clientHeight > 0) {
      this._canvas.width = parent.clientWidth;
      this._canvas.height = parent.clientHeight;
    } else {
      this._canvas.width = 320;
      this._canvas.height = 510;
    }
  }

  _crearParticulas() {
    this._particles = [];
    const w = this._canvas.width;
    const h = this._canvas.height;
    for (let i = 0; i < this._numParticles; i++) {
      this._particles.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.45,
        vy: (Math.random() - 0.5) * 0.45,
        radius: Math.random() * 1.8 + 0.6,
        alpha: Math.random() * 0.6 + 0.2,
      });
    }
  }

  _iniciarBucleParticulas() {
    const loop = () => {
      this._dibujarParticulas();
      this._animId = requestAnimationFrame(loop);
    };
    this._animId = requestAnimationFrame(loop);
  }

  _dibujarParticulas() {
    if (!this._ctx) return;
    const w = this._canvas.width;
    const h = this._canvas.height;
    this._ctx.clearRect(0, 0, w, h);

    // Mover y dibujar cada partícula holográfica
    for (let i = 0; i < this._particles.length; i++) {
      const p = this._particles[i];
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0) p.x = w;
      if (p.x > w) p.x = 0;
      if (p.y < 0) p.y = h;
      if (p.y > h) p.y = 0;

      this._ctx.beginPath();
      this._ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      this._ctx.fillStyle = `rgba(0, 240, 255, ${p.alpha})`;
      this._ctx.shadowColor = "#00f0ff";
      this._ctx.shadowBlur = 4;
      this._ctx.fill();
      this._ctx.shadowBlur = 0;

      // Unir partículas cercanas con filamentos tenues de luz
      for (let j = i + 1; j < this._particles.length; j++) {
        const p2 = this._particles[j];
        const dx = p.x - p2.x;
        const dy = p.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 65) {
          this._ctx.beginPath();
          this._ctx.strokeStyle = `rgba(0, 240, 255, ${0.15 * (1 - dist / 65)})`;
          this._ctx.lineWidth = 0.6;
          this._ctx.moveTo(p.x, p.y);
          this._ctx.lineTo(p2.x, p2.y);
          this._ctx.stroke();
        }
      }
    }
  }

  _enlazarEventosOrganos() {
    if (!this._svg) return;
    const organos = this._svg.querySelectorAll(".organ-node");
    organos.forEach(nodo => {
      nodo.addEventListener("click", e => {
        const target = e.currentTarget;
        const organId = target.getAttribute("data-organ");
        this.dispararOndaOcular(target);
        if (window.stateManager) {
          window.stateManager.setOrganoSeleccionado(organId);
        }
      });
    });
  }

  dispararOndaOcular(element) {
    const bbox = element.getBBox();
    const cx = bbox.x + bbox.width / 2;
    const cy = bbox.y + bbox.height / 2;

    const ripple = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    ripple.setAttribute("cx", cx);
    ripple.setAttribute("cy", cy);
    ripple.setAttribute("class", "ripple-circle");

    this._svg.appendChild(ripple);
    setTimeout(() => {
      if (ripple.parentNode) {
        ripple.parentNode.removeChild(ripple);
      }
    }, 1600);
  }

  destruir() {
    if (this._animId) {
      cancelAnimationFrame(this._animId);
      this._animId = null;
    }
  }
}

window.HologramRendererService = HologramRendererService;
