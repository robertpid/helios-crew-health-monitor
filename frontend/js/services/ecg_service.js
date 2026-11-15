/**
 * ==============================================================================
 * SERVICES LAYER: EcgOscilloscopeService (PERMANENT LIGHTWEIGHT MODE)
 * Optimized P-Q-R-S-T medical oscilloscope:
 * - Pauses automatically when the Biomedical tab is not active.
 * - Removes the heavy compositing of continuous shadowBlur.
 * ==============================================================================
 */

class EcgOscilloscopeService {
  constructor(canvasId) {
    this._canvas = document.getElementById(canvasId);
    this._ctx = this._canvas ? this._canvas.getContext("2d", { alpha: false }) : null;
    this._heartRate = 76;
    this._sweepX = 0;
    this._lastY = 45;
    this._phase = 0;
    this._animId = null;
    this._step = 2.4;
    this._isPaused = false;
  }

  initialize() {
    if (!this._canvas || !this._ctx) return;
    this.resize();
    window.addEventListener("resize", () => this.resize());
    window.addEventListener("helios:layout", () => this.resize());
    this._startLoop();
  }

  pause() {
    if (this._animId) {
      cancelAnimationFrame(this._animId);
      this._animId = null;
    }
    this._isPaused = true;
  }

  resume() {
    if (this._isPaused) {
      this._isPaused = false;
      this._startLoop();
    }
  }

  resize() {
    if (!this._canvas || !this._ctx) return;
    const parent = this._canvas.parentElement;
    this._canvas.width = parent ? parent.clientWidth - 28 : 550;
    this._canvas.height = Math.max(60, this._canvas.clientHeight || 95);
    this._sweepX = 0;
    this._lastY = this._canvas.height / 2;
    this._clearFullBackground();
  }

  updateHeartRate(bpm) {
    this._heartRate = Math.max(40, Math.min(220, bpm));
  }

  _clearFullBackground() {
    if (!this._ctx) return;
    this._ctx.fillStyle = "#020409";
    this._ctx.fillRect(0, 0, this._canvas.width, this._canvas.height);
    this._drawMillimeterGrid();
  }

  _drawMillimeterGrid() {
    if (!this._ctx) return;
    this._ctx.strokeStyle = "rgba(0, 240, 255, 0.05)";
    this._ctx.lineWidth = 1;
    for (let x = 0; x < this._canvas.width; x += 22) {
      this._ctx.beginPath();
      this._ctx.moveTo(x, 0);
      this._ctx.lineTo(x, this._canvas.height);
      this._ctx.stroke();
    }
    for (let y = 0; y < this._canvas.height; y += 22) {
      this._ctx.beginPath();
      this._ctx.moveTo(0, y);
      this._ctx.lineTo(this._canvas.width, y);
      this._ctx.stroke();
    }
  }

  _startLoop() {
    if (this._animId) return;
    const render = () => {
      if (!this._isPaused) {
        this._drawStep();
        this._animId = requestAnimationFrame(render);
      }
    };
    this._animId = requestAnimationFrame(render);
  }

  _drawStep() {
    if (!this._ctx) return;

    // Angular speed based on the heart rate
    const speed = (this._heartRate / 60.0) * 0.048;
    this._phase += speed;
    if (this._phase > Math.PI * 2) {
      this._phase -= Math.PI * 2;
    }

    let deflection = 0;
    const p = this._phase;

    // P-Q-R-S-T mathematical modeling
    if (p > 0.4 && p < 0.7) {
      deflection = -Math.sin((p - 0.4) / 0.3 * Math.PI) * 7.0; // P wave
    } else if (p > 0.95 && p < 1.05) {
      deflection = 6.0; // Q wave
    } else if (p > 1.05 && p < 1.22) {
      deflection = -44.0; // R wave
    } else if (p > 1.22 && p < 1.35) {
      deflection = 14.0; // S wave
    } else if (p > 1.75 && p < 2.25) {
      deflection = -Math.sin((p - 1.75) / 0.5 * Math.PI) * 10.0; // T wave
    }

    deflection += (Math.random() - 0.5) * 1.5;

    const baseline = this._canvas.height / 2;
    const currentY = baseline + deflection;

    // Clean erase of the leading band
    this._ctx.fillStyle = "#020409";
    this._ctx.fillRect(this._sweepX, 0, 18, this._canvas.height);

    // Trace color: sinus green at rest, neon red on tachycardia/crisis
    const isTachycardia = this._heartRate > 100;
    const traceColor = isTachycardia ? "#ff2255" : "#00ff88";

    this._ctx.beginPath();
    this._ctx.strokeStyle = traceColor;
    this._ctx.lineWidth = 2.0;
    this._ctx.moveTo(this._sweepX, this._lastY);
    this._ctx.lineTo(this._sweepX + this._step, currentY);
    this._ctx.stroke();

    this._lastY = currentY;
    this._sweepX += this._step;
    if (this._sweepX >= this._canvas.width) {
      this._sweepX = 0;
    }
  }

  destroy() {
    this.pause();
  }
}

window.EcgOscilloscopeService = EcgOscilloscopeService;
