/**
 * ==============================================================================
 * CAPA DE SERVICIOS (CLIENT SERVICES): EcgOscilloscopeService
 * Motor de renderizado en Canvas HTML5 para trazo de ECG médico continuo a 60 FPS.
 * ==============================================================================
 */

class EcgOscilloscopeService {
  constructor(canvasId) {
    this._canvas = document.getElementById(canvasId);
    this._ctx = this._canvas ? this._canvas.getContext("2d") : null;
    this._heartRate = 76;
    this._sweepX = 0;
    this._lastY = 45;
    this._phase = 0;
    this._animId = null;
    this._step = 2.4;
  }

  inicializar() {
    if (!this._canvas || !this._ctx) return;
    this.redimensionar();
    window.addEventListener("resize", () => this.redimensionar());
    this._iniciarBucle();
  }

  redimensionar() {
    if (!this._canvas || !this._ctx) return;
    const parent = this._canvas.parentElement;
    this._canvas.width = parent ? parent.clientWidth - 28 : 550;
    this._canvas.height = 95;
    this._sweepX = 0;
    this._lastY = this._canvas.height / 2;
    this._limpiarFondoCompleto();
  }

  actualizarFrecuenciaCardiaca(bpm) {
    this._heartRate = Math.max(40, Math.min(220, bpm));
  }

  _limpiarFondoCompleto() {
    if (!this._ctx) return;
    this._ctx.fillStyle = "#020409";
    this._ctx.fillRect(0, 0, this._canvas.width, this._canvas.height);
    this._dibujarCuadriculaMilimetrica();
  }

  _dibujarCuadriculaMilimetrica() {
    if (!this._ctx) return;
    this._ctx.strokeStyle = "rgba(0, 240, 255, 0.05)";
    this._ctx.lineWidth = 1;
    for (let x = 0; x < this._canvas.width; x += 18) {
      this._ctx.beginPath();
      this._ctx.moveTo(x, 0);
      this._ctx.lineTo(x, this._canvas.height);
      this._ctx.stroke();
    }
    for (let y = 0; y < this._canvas.height; y += 18) {
      this._ctx.beginPath();
      this._ctx.moveTo(0, y);
      this._ctx.lineTo(this._canvas.width, y);
      this._ctx.stroke();
    }
  }

  _iniciarBucle() {
    const render = () => {
      this._dibujarPaso();
      this._animId = requestAnimationFrame(render);
    };
    this._animId = requestAnimationFrame(render);
  }

  _dibujarPaso() {
    if (!this._ctx) return;

    // Calcular velocidad angular en función de la frecuencia cardíaca
    const velocidad = (this._heartRate / 60.0) * 0.048;
    this._phase += velocidad;
    if (this._phase > Math.PI * 2) {
      this._phase -= Math.PI * 2;
    }

    let deflexion = 0;
    const p = this._phase;

    // Modelado matemático P-Q-R-S-T
    if (p > 0.4 && p < 0.7) {
      deflexion = -Math.sin((p - 0.4) / 0.3 * Math.PI) * 7.0; // Onda P
    } else if (p > 0.95 && p < 1.05) {
      deflexion = 6.0; // Onda Q (negativa)
    } else if (p > 1.05 && p < 1.22) {
      deflexion = -44.0; // Onda R (pico agudo positivo despolarización ventricular)
    } else if (p > 1.22 && p < 1.35) {
      deflexion = 14.0; // Onda S (negativa)
    } else if (p > 1.75 && p < 2.25) {
      deflexion = -Math.sin((p - 1.75) / 0.5 * Math.PI) * 10.0; // Onda T (repolarización)
    }

    // Micro-ruido biomédico natural
    deflexion += (Math.random() - 0.5) * 1.8;

    const lineaBase = this._canvas.height / 2;
    const currentY = lineaBase + deflexion;

    // Efecto barrido de haz de fósforo (borrar franja frontal)
    this._ctx.fillStyle = "#020409";
    this._ctx.fillRect(this._sweepX, 0, 18, this._canvas.height);

    // Redibujar cuadrícula sobre la franja borrada
    this._ctx.strokeStyle = "rgba(0, 240, 255, 0.05)";
    this._ctx.strokeRect(this._sweepX, 0, 18, this._canvas.height);

    // Color del trazo: verde sinusal en reposo, rojo neón en taquicardia/crisis
    const esTaquicardia = this._heartRate > 100;
    const colorTrazo = esTaquicardia ? "#ff2255" : "#00ff88";

    this._ctx.beginPath();
    this._ctx.strokeStyle = colorTrazo;
    this._ctx.lineWidth = 2.2;
    this._ctx.shadowColor = colorTrazo;
    this._ctx.shadowBlur = esTaquicardia ? 10 : 6;
    this._ctx.moveTo(this._sweepX, this._lastY);
    this._ctx.lineTo(this._sweepX + this._step, currentY);
    this._ctx.stroke();
    this._ctx.shadowBlur = 0;

    this._lastY = currentY;
    this._sweepX += this._step;
    if (this._sweepX >= this._canvas.width) {
      this._sweepX = 0;
    }
  }

  destruir() {
    if (this._animId) {
      cancelAnimationFrame(this._animId);
      this._animId = null;
    }
  }
}

window.EcgOscilloscopeService = EcgOscilloscopeService;
