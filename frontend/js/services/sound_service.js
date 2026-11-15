/**
 * SoundService - Procedural Synthesized Audio System (Web Audio API)
 *
 * Generates futuristic sound effects and the emergency alarm siren in real time
 * without downloading external files (0 KB of downloads, latency < 2 ms).
 * Complies with the Master Alarm standard of crewed deep space missions.
 */
class SoundService {
  constructor() {
    this._audioCtx = null;
    this._muted = false;
    this._masterVolume = 0.09; // Level calibrated to be clear but not deafening
    this._alarmActive = false;
    this._alarmLoopId = null;

    // Unlock the AudioContext on the user's first interaction with the DOM
    this._bindInteractionUnlock();
  }

  _bindInteractionUnlock() {
    const unlock = () => {
      this._getContext();
      window.removeEventListener("click", unlock);
      window.removeEventListener("keydown", unlock);
      window.removeEventListener("touchstart", unlock);
    };
    window.addEventListener("click", unlock, { once: true });
    window.addEventListener("keydown", unlock, { once: true });
    window.addEventListener("touchstart", unlock, { once: true });
  }

  /**
   * Gets or resumes the active AudioContext.
   */
  _getContext() {
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
   * Toggles between sound enabled and muted.
   * @returns {boolean} Current muted state.
   */
  toggleMute() {
    this._muted = !this._muted;
    if (this._muted && this._audioCtx && this._audioCtx.state === "running") {
      this._audioCtx.suspend();
    } else if (!this._muted && this._audioCtx && this._audioCtx.state === "suspended") {
      this._audioCtx.resume();
    }
    return this._muted;
  }

  isMuted() {
    return this._muted;
  }

  isAlarmActive() {
    return this._alarmActive;
  }

  /**
   * Starts the cyclic emergency alarm siren in a loop.
   * It keeps sounding rhythmically until the emergency resolves or the user mutes the audio.
   */
  startEmergencyAlarm() {
    if (this._alarmActive) return;
    this._alarmActive = true;

    // Run the first alarm cycle immediately
    this._runAlarmPulse();

    // Rhythmic periodic repetition every 1300 ms (standard aerospace contingency cadence)
    if (this._alarmLoopId) clearInterval(this._alarmLoopId);
    this._alarmLoopId = setInterval(() => {
      if (this._alarmActive && !this._muted) {
        this._runAlarmPulse();
      }
    }, 1300);
  }

  /**
   * Immediately stops the emergency siren.
   */
  stopEmergencyAlarm() {
    this._alarmActive = false;
    if (this._alarmLoopId) {
      clearInterval(this._alarmLoopId);
      this._alarmLoopId = null;
    }
  }

  /**
   * Generates a bitonal cabin tactical alarm pulse (NASA Master Alarm style).
   * Tone 1: 940 Hz (high urgency, 140 ms)
   * Tone 2: 720 Hz (contingency notice, 140 ms)
   * Tone 3: 940 Hz (impact restatement, 140 ms)
   */
  _runAlarmPulse() {
    const ctx = this._getContext();
    if (!ctx) return;

    try {
      const t = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const filter = ctx.createBiquadFilter();

      // Sawtooth waveform with a low-pass filter for a pressurized cabin sound
      osc.type = "sawtooth";
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(1700, t);

      // Urgent bitonality: 940 Hz -> 720 Hz -> 940 Hz
      osc.frequency.setValueAtTime(940, t);
      osc.frequency.setValueAtTime(720, t + 0.12);
      osc.frequency.setValueAtTime(940, t + 0.24);

      // Volume envelope (immediate attack, sustained with exponential decay)
      gain.gain.setValueAtTime(this._masterVolume * 1.4, t);
      gain.gain.setValueAtTime(this._masterVolume * 1.2, t + 0.12);
      gain.gain.setValueAtTime(this._masterVolume * 1.4, t + 0.24);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.42);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc.start(t);
      osc.stop(t + 0.45);
    } catch (_) {}
  }

  /**
   * Subtle user interface beep for buttons and tabs (40 ms).
   */
  playClick() {
    const ctx = this._getContext();
    if (!ctx) return;

    try {
      const t = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(1100, t);
      osc.frequency.exponentialRampToValueAtTime(1600, t + 0.035);

      gain.gain.setValueAtTime(this._masterVolume * 0.7, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.04);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(t);
      osc.stop(t + 0.045);
    } catch (_) {}
  }

  /**
   * Very subtle ultrasonic pulse (25 ms) when hovering a holographic organ.
   */
  playHover() {
    const ctx = this._getContext();
    if (!ctx) return;

    try {
      const t = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(1400, t);
      osc.frequency.exponentialRampToValueAtTime(2200, t + 0.022);

      gain.gain.setValueAtTime(this._masterVolume * 0.35, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.025);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(t);
      osc.stop(t + 0.03);
    } catch (_) {}
  }

  /**
   * Holographic resonance when switching between space habitats (120 ms).
   */
  playHabitatChange() {
    const ctx = this._getContext();
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

      gain.gain.setValueAtTime(this._masterVolume * 0.8, t);
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
   * Ascending harmonic chord for confirmation and nominal state (180 ms).
   */
  playNominal() {
    this.stopEmergencyAlarm();
    const ctx = this._getContext();
    if (!ctx) return;
    try {
      const t = ctx.currentTime;
      [523.25, 659.25, 783.99].forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(freq, t + i * 0.05);
        gain.gain.setValueAtTime(this._masterVolume * 0.7, t + i * 0.05);
        gain.gain.exponentialRampToValueAtTime(0.0001, t + i * 0.05 + 0.12);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(t + i * 0.05);
        osc.stop(t + i * 0.05 + 0.13);
      });
    } catch (_) {}
  }

  /**
   * Triggers the space crisis sound protocol (Master Alarm).
   */
  playCrisis() {
    this.startEmergencyAlarm();
  }

  /**
   * Brief tactical alert tone for wrong credentials or a warning (120 ms).
   */
  playAlert() {
    const ctx = this._getContext();
    if (!ctx) return;
    try {
      const t = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(440, t);
      osc.frequency.setValueAtTime(330, t + 0.06);
      gain.gain.setValueAtTime(this._masterVolume * 0.9, t);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.12);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + 0.13);
    } catch (_) {}
  }
}

window.soundService = new SoundService();
