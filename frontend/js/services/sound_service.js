/**
 * SoundService - Sistema de Audio Sintetizado Procedural (Web Audio API)
 * 
 * Genera efectos de sonido futuristas y de retroalimentación táctil-auditiva en tiempo real
 * sin descargar archivos pesados (0 KB de descargas externas, latencia < 2 ms).
 * Cumple con las restricciones de reproducción automática de los navegadores modernos.
 */
class SoundService {
  constructor() {
    this._audioCtx = null;
    this._muted = false;
    this._volumenGeneral = 0.08; // Volumen sutil y no invasivo
  }

  /**
   * Inicializa o reanuda el AudioContext tras la primera interacción del usuario.
   */
  _obtenerContexto() {
    if (this._muted) return null;
    if (!this._audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        this._audioCtx = new AudioContextClass();
      }
    }
    if (this._audioCtx && this._audioCtx.state === "suspended") {
      this._audioCtx.resume();
    }
    return this._audioCtx;
  }

  /**
   * Alterna entre sonido activado y silenciado.
   * @returns {boolean} Estado actual de silenciado.
   */
  toggleSilencio() {
    this._muted = !this._muted;
    return this._muted;
  }

  estaSilenciado() {
    return this._muted;
  }

  /**
   * Beep sutil de interfaz de usuario para botones y pestañas (40 ms).
   */
  reproducirClick() {
    const ctx = this._obtenerContexto();
    if (!ctx) return;

    try {
      const t = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(1100, t);
      osc.frequency.exponentialRampToValueAtTime(1600, t + 0.035);

      gain.gain.setValueAtTime(this._volumenGeneral * 0.7, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.04);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(t);
      osc.stop(t + 0.045);
    } catch (_) {}
  }

  /**
   * Resonancia holográfica al alternar entre hábitats espaciales (120 ms).
   */
  reproducirCambioHabitat() {
    const ctx = this._obtenerContexto();
    if (!ctx) return;

    try {
      const t = ctx.currentTime;
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();

      osc1.type = "sine";
      osc2.type = "triangle";

      osc1.frequency.setValueAtTime(520, t);
      osc1.frequency.exponentialRampToValueAtTime(1240, t + 0.10);

      osc2.frequency.setValueAtTime(780, t);
      osc2.frequency.exponentialRampToValueAtTime(1560, t + 0.10);

      gain.gain.setValueAtTime(this._volumenGeneral * 0.8, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.12);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ctx.destination);

      osc1.start(t);
      osc2.start(t);
      osc1.stop(t + 0.13);
      osc2.stop(t + 0.13);
    } catch (_) {}
  }

  /**
   * Alarma táctica para simulaciones de crisis o anomalías de soporte vital.
   */
  reproducirAlertaCrisis() {
    const ctx = this._obtenerContexto();
    if (!ctx) return;

    try {
      const t = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(880, t);
      osc.frequency.setValueAtTime(660, t + 0.08);
      osc.frequency.setValueAtTime(880, t + 0.16);

      // Filtro pasa-bajas para suavizar el tono militar
      const filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(1400, t);

      gain.gain.setValueAtTime(this._volumenGeneral * 1.2, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.28);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc.start(t);
      osc.stop(t + 0.30);
    } catch (_) {}
  }

  /**
   * Latido cardíaco sutil de baja frecuencia (60 Hz sub-bass, 80 ms).
   */
  reproducirLatido() {
    const ctx = this._obtenerContexto();
    if (!ctx) return;

    try {
      const t = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(65, t);
      osc.frequency.exponentialRampToValueAtTime(38, t + 0.08);

      gain.gain.setValueAtTime(this._volumenGeneral * 0.9, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.09);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(t);
      osc.stop(t + 0.10);
    } catch (_) {}
  }
}

window.soundService = new SoundService();
