/**
 * CONTROLLERS LAYER: WellnessController
 * Handles the Wellbeing, Routines, Assistant and Gamification interaction.
 * ASTRA Psychological Assessment and Vocal Cadence Protocol (NASA-BHP).
 * Strictly under 400 lines (Clean Code & SRP).
 */

class WellnessController {
  constructor(soundService = null) {
    this._sound = soundService || window.soundService;
    this._taskState = { meditation: 100, stretching: 100, exercise: 60, hydration: 80 };
    this._gamification = { level: 6, xp: 1320, xpMax: 1500 };
    this._breathingTimer = null;
    this._breathing = false;

    this._currentQuestion = 1;
    this._firstCharacterTime = null;
    this._speechStartTime = null;
    this._computedWpm = null;
    this._speechRecognition = null;
    this._listeningToVoice = false;
    this._evaluating = false;
    this._protocolCompleted = false;
    this._inProgress = false;
    this._completionTimer = null;

    this._bhpQuestions = [
      {
        id: 1, cat: "Alertness & Fatigue",
        text: "How would you describe your concentration and energy level for today's operations?",
        chips: ["100% focused and clear for the shift.", "Normal, within the usual parameters.", "I have felt mental slowness and attentional fatigue today."]
      },
      {
        id: 2, cat: "Cognitive Load",
        text: "Have you experienced overload or delay in resolving technical tasks today?",
        chips: ["Zero overload, procedures in optimal time.", "Fine, standard operational load.", "The checklists have taken me more time than expected."]
      },
      {
        id: 3, cat: "Sol 120 Emotional State",
        text: "Sol 120 report: How do you perceive the cabin environment and the distance from Earth?",
        chips: ["Excellent morale, fluid communication with Houston.", "Fine, we are relaxed and in order here.", "The isolation is noticeable today, I need a short break."]
      }
    ];

    this._initVoice();
    setTimeout(() => this._prepareStart(), 200);
  }

  _prepareStart() {
    this._updateChips();
    const input = document.getElementById("inputPsychText");
    if (input) {
      input.addEventListener("input", () => {
        if (!this._firstCharacterTime) this._firstCharacterTime = performance.now();
      });
    }
  }

  advanceTask(type) {
    this._sound?.playClick?.();
    let current = (this._taskState[type] || 0) + 20;
    if (current > 100) current = 20;
    this._taskState[type] = current;
    const cap = type.charAt(0).toUpperCase() + type.slice(1);
    const valTag = document.getElementById(`taskPercent${cap}`), barTag = document.getElementById(`taskBar${cap}`);
    if (valTag) valTag.innerText = `${current}%`;
    if (barTag) barTag.style.width = `${current}%`;
    if (type === "exercise") window.fitService?.adjustExerciseGoal?.(current >= 100);
    this.addXp(25);
  }

  addXp(points) {
    this._gamification.xp += points;
    if (this._gamification.xp >= this._gamification.xpMax) {
      this._gamification.level += 1;
      this._gamification.xp -= this._gamification.xpMax;
      this._gamification.xpMax = Math.round(this._gamification.xpMax * 1.25);
      this._sound?.playNominal?.();
    }
    const lvlTag = document.getElementById("gamificationLevelTag"), xpTag = document.getElementById("gamificationExpTag"), xpBar = document.getElementById("gamificationExpBar");
    if (lvlTag) lvlTag.innerText = `LEVEL ${this._gamification.level}`;
    if (xpTag) xpTag.innerHTML = `XP <strong style="color:var(--neon-green);">${this._gamification.xp}</strong> / ${this._gamification.xpMax}`;
    if (xpBar) xpBar.style.width = `${Math.min(100, Math.round((this._gamification.xp / this._gamification.xpMax) * 100))}%`;
  }

  startOphthalmicExam() {
    this._sound?.playClick?.();
    if (window.ophthalmicService?.openModal) {
      window.ophthalmicService.openModal();
    } else {
      this._showFeedback("👁️ <strong>OPHTHALMIC ASSESSMENT:</strong> Opening the SANS module...");
    }
  }
  startSonarExam() { this._sound?.playClick?.(); window.sonarService?.openModal ? window.sonarService.openModal() : this._showFeedback("👂 <strong>SONAR SWEEP / AUDIOMETRY:</strong> 250-8000 Hz evaluated. Cabin noise at a nominal 58 dBA."); }
  _showFeedback(html) { const fb = document.getElementById("extraExamFeedback"); if (!fb) return; fb.style.display = "block"; fb.innerHTML = html; setTimeout(() => { if (fb) fb.style.display = "none"; }, 6000); }
  syncMail() { this._sound?.playClick?.(); alert("📡 DSN SYNCHRONIZATION COMPLETE: Link active with Houston. 0 pending messages."); }

  // ==============================================================================
  // PSYCHOLOGICAL ASSESSMENT AND VOCAL CADENCE PROTOCOL (ASTRA SYSTEM)
  // ==============================================================================
  startPsychologicalProtocol() {
    this._sound?.playClick?.();
    if (this._inProgress) {
      this._finishProtocol();
      return;
    }
    this._inProgress = true;
    this._currentQuestion = 1;
    this._protocolCompleted = false;
    this._firstCharacterTime = null;
    this._updateProtocolButton(true);
    const box = document.getElementById("assistantChatBox");
    if (box) {
      box.innerHTML = `<div style="padding:8px 12px; background:rgba(0,240,255,0.06); border-left:3px solid var(--neon-cyan); border-radius:0 6px 6px 0;"><strong style="color:var(--neon-cyan); font-family:var(--font-hud);">ASTRA SYSTEM:</strong> NASA-BHP Sol 120 protocol started. Please answer the following routine queries for the cabin record.</div>`;
    }
    this._presentQuestion();
  }

  _updateProtocolButton(active) {
    const btn = document.getElementById("btnStartPsychProtocol");
    if (btn) {
      btn.innerText = active ? "⏹️ FINISH" : "📋 BHP PROTOCOL";
      btn.className = active ? "btn-hud btn-hud-danger" : "btn-hud";
    }
  }

  _presentQuestion() {
    const item = this._bhpQuestions.find(q => q.id === this._currentQuestion);
    if (!item) return;
    this._firstCharacterTime = null;
    this._updateStatusBadge(`STEP ${item.id}/3`, "status-stable");
    this._appendMessage("ASTRA SYSTEM", `<strong>Question ${item.id}/3 (${item.cat}):</strong> ${item.text}`, "astra");
    this._updateChips();
    const input = document.getElementById("inputPsychText");
    if (input) { input.value = ""; input.focus(); }
  }

  _updateChips() {
    const item = this._bhpQuestions.find(q => q.id === this._currentQuestion) || this._bhpQuestions[0];
    const chipsContainer = document.getElementById("psychSuggestionsContainer");
    if (chipsContainer && item) {
      const chipsHtml = item.chips.map(c => `
        <button class="btn-hud" onclick="window.hudController.selectSuggestedChip('${c.replace(/'/g, "\\'")}')" style="font-size:10px; padding:4px 8px; text-transform:none;">${c}</button>
      `).join("");
      const finishHtml = `<button class="btn-hud" onclick="window.hudController.startPsychologicalProtocol()" style="font-size:10px; padding:4px 8px; color:#94a3b8; border-color:#475569;" title="Close and finish the assessment">⏹️ Finish</button>`;
      chipsContainer.innerHTML = chipsHtml + finishHtml;
    }
  }

  selectSuggestedChip(text) {
    const input = document.getElementById("inputPsychText");
    if (input) input.value = text;
    this._computedWpm = Math.round(132 + Math.random() * 14);
    this.sendPsychologicalResponse();
  }

  async sendPsychologicalResponse() {
    if (this._evaluating) return;
    const input = document.getElementById("inputPsychText");
    const text = input ? input.value.trim() : "";
    if (!text) return;

    if (this._protocolCompleted) {
      this._currentQuestion = 1;
      this._protocolCompleted = false;
      this._inProgress = true;
      this._updateProtocolButton(true);
    }

    this._sound?.playClick?.();
    const words = text.split(/\s+/).filter(Boolean);
    const wordCount = Math.max(1, words.length);

    let wpm = this._computedWpm;
    this._computedWpm = null;
    if (!wpm) {
      if (this._firstCharacterTime) {
        const seconds = Math.max(0.6, (performance.now() - this._firstCharacterTime) / 1000);
        wpm = Math.min(185, Math.max(65, Math.round((wordCount / seconds) * 60 * 1.6)));
        this._firstCharacterTime = null;
      } else {
        wpm = Math.round(128 + Math.random() * 14);
      }
    }

    this._evaluating = true;
    this._appendMessage("Astronaut", text, "astronaut");
    if (input) input.value = "";

    const telemetry = window.stateManager?._state?.telemetry;
    const rateBpm = telemetry?.physiology?.heart_rate_bpm || 72.0;

    let res = await window.telemetryService?.evaluatePsychologicalResponse?.({
      question_id: this._currentQuestion, response_text: text,
      latency_ms: 2000.0, words_per_minute: wpm,
      heart_rate_bpm: rateBpm, body_in_panic: rateBpm > 95.0
    });

    if (!res) res = this._computeLocalMetrics(text, wpm, rateBpm);
    this._updateTelemetryBadges(res);

    window.stateManager?.updateCognition?.({
      latency_ms: res.cadence_ms_per_word || 440, lexical_density: res.lexical_density,
      cosine_similarity: res.cosine_similarity,
      incongruence_detected: Boolean(res.incongruence_detected),
      astra_alert: res.incongruence_detected ? res.preliminary_assessment : null
    });

    setTimeout(() => {
      this._appendMessage("ASTRA SYSTEM", res.assistant_response, res.incongruence_detected ? "alert" : "nominal");
      this.addXp(25);
      this._evaluating = false;

      if (this._inProgress && this._currentQuestion < 3) {
        this._currentQuestion += 1;
        setTimeout(() => this._presentQuestion(), 900);
      } else {
        this._finishProtocol();
      }
    }, 350);
  }

  _finishProtocol() {
    this._inProgress = false;
    this._protocolCompleted = true;
    this._updateProtocolButton(false);
    this._updateStatusBadge("COMPLETED", "status-stable");
    const isCritical = window.stateManager?._state?.telemetry?.cognition?.incongruence_detected;
    const banner = `<div style="padding:10px 14px; background:${isCritical ? "rgba(255,34,85,0.12)" : "rgba(0,255,136,0.1)"}; border:1px solid ${isCritical ? "var(--neon-red)" : "var(--neon-green)"}; border-radius:6px; margin-top:6px;"><strong style="color:${isCritical ? "var(--neon-red)" : "var(--neon-green)"}; font-family:var(--font-hud);">OPERATIONAL RECORD COMPLETED:</strong><br>${isCritical ? "⚠️ Parameters require attention. Suggestion: start the 4-4-6 relaxation and a preventive break." : "✅ Nominal operational state. Fit for the Sol 120 activity program."}</div>`;
    const box = document.getElementById("assistantChatBox");
    if (box) { box.insertAdjacentHTML("beforeend", banner); box.scrollTop = box.scrollHeight; }

    const chipsContainer = document.getElementById("psychSuggestionsContainer");
    if (chipsContainer) {
      chipsContainer.innerHTML = `<button class="btn-hud" onclick="window.hudController.startPsychologicalProtocol()" style="font-size:10px; padding:4px 10px;">🔄 Start a new BHP check</button>`;
    }

    if (this._completionTimer) clearTimeout(this._completionTimer);
    this._completionTimer = setTimeout(() => {
      this._updateStatusBadge("READY", "status-stable");
    }, 3500);
  }

  _computeLocalMetrics(text, wpm, rateBpm) {
    const words = text.toLowerCase().split(/\s+/).filter(Boolean);
    const isFatigue = ["sleep", "sleepy", "tired", "fatigue", "slow", "delay", "overload", "isolation", "exhausted"].some(k => text.toLowerCase().includes(k));
    const isNominal = ["fine", "good", "order", "normal", "control", "focused", "clear", "optimal", "excellent", "zero", "steady", "no", "relaxed"].some(k => text.toLowerCase().includes(k));
    let density = Math.round(Math.min(1.0, Math.max(0.35, isNominal ? 0.92 : (isFatigue ? 0.78 : (words.length > 0 ? (new Set(words).size / words.length) : 0.4)))) * 100) / 100;
    const v = [wpm / 135.0, density], dot = v[0] + v[1];
    const cosSim = Math.round((dot / (Math.sqrt(v[0] ** 2 + v[1] ** 2) * Math.SQRT2)) * 1000) / 1000;
    const incongruence = (rateBpm > 95 && isNominal) || wpm < 85;

    let assessment = "COHERENT: NOMINAL OPERATIONAL STATE", response = "Copy that, Commander. Report logged in the cabin operational record.";
    if (incongruence) {
      assessment = rateBpm > 95 ? "INCONGRUENCE: CALM SPEECH UNDER PHYSIOLOGICAL ACTIVATION" : "OPERATIONAL FATIGUE DETECTED";
      response = rateBpm > 95
        ? "Commander, the cabin physiological records show stress activation during your report. We recommend taking a short active break and the 4-4-6 breathing guide."
        : "Commander, we are recording signs of fatigue and cumulative attentional wear in this report. Cabin hydration and a preventive 15-minute break are suggested.";
    } else if (isFatigue) {
      assessment = "OPERATIONAL FATIGUE REPORTED";
      response = "Fatigue report logged in the operational record. Hydrate with 500 ml and take a preventive 15-minute break.";
    } else {
      const responseMap = {
        1: "Copy that, Commander. Clear communication and optimal state for flight operations.",
        2: "Excellent. Responses recorded within the expected nominal margins of the mission.",
        3: "Sol 120 report logged successfully. Balanced state and steady crew morale."
      };
      response = responseMap[this._currentQuestion] || response;
    }
    return {
      question_id: this._currentQuestion, words_per_minute: Math.round(wpm),
      cadence_ms_per_word: Math.round(60000 / wpm), lexical_density: density,
      cosine_similarity: cosSim, incongruence_detected: incongruence,
      preliminary_assessment: assessment, assistant_response: response,
      cognitive_state: incongruence ? "CRITICAL_INCONGRUENCE" : (isFatigue ? "MILD_FATIGUE" : "NOMINAL")
    };
  }

  _updateTelemetryBadges(res) {
    const s = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
    const wpm = res.words_per_minute || 135;
    const rateTxt = wpm < 85 ? "SLOW" : (wpm > 175 ? "FAST" : "NOMINAL");
    s("psychMetricLatency", rateTxt);
    s("psychMetricDensity", (res.lexical_density || 0.95) >= 0.85 ? "OPTIMAL" : "STABLE");
    s("psychMetricCosSim", (res.cosine_similarity || 0.98) >= 0.85 ? "NOMINAL" : "UNDER ATTENTION");
    const sum = document.getElementById("psychEvalSummary");
    if (sum) {
      sum.innerText = res.incongruence_detected ? "OBSERVATION" : (res.cognitive_state === "MILD_FATIGUE" ? "MILD FATIGUE" : "NOMINAL");
      sum.style.color = res.incongruence_detected ? "var(--neon-red)" : (res.cognitive_state === "MILD_FATIGUE" ? "var(--neon-amber)" : "var(--neon-green)");
    }
  }

  _updateStatusBadge(txt, cls) { const b = document.getElementById("psychStatusBadge"); if (b) { b.innerText = txt; b.className = `badge-status ${cls}`; } }

  _appendMessage(sender, content, style) {
    const box = document.getElementById("assistantChatBox");
    if (!box) return;
    const div = document.createElement("div");
    const color = style === "astronaut" ? "#ffffff" : (style === "alert" ? "var(--neon-red)" : "var(--neon-cyan)");
    const bg = style === "astronaut" ? "rgba(255,255,255,0.06)" : (style === "alert" ? "rgba(255,34,85,0.08)" : "rgba(0,240,255,0.06)");
    div.style.cssText = `padding:8px 12px; background:${bg}; border-left:3px solid ${color}; border-radius:0 6px 6px 0;`;
    div.innerHTML = `<strong style="color:${color}; font-family:var(--font-hud);">${sender}:</strong> ${content}`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }

  _initVoice() {
    const Sp = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Sp) return;
    try {
      this._speechRecognition = new Sp();
      this._speechRecognition.lang = "en-US";
      this._speechRecognition.onspeechstart = () => { this._speechStartTime = performance.now(); };
      this._speechRecognition.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        const durationSec = Math.max(0.6, (performance.now() - (this._speechStartTime || performance.now() - 1500)) / 1000);
        const wordCount = transcript.trim().split(/\s+/).filter(Boolean).length;
        this._computedWpm = Math.min(200, Math.max(60, Math.round((wordCount / durationSec) * 60)));
        const inp = document.getElementById("inputPsychText");
        if (inp) inp.value = transcript;
        this.sendPsychologicalResponse();
      };
      this._speechRecognition.onend = () => this._setMicState(false);
      this._speechRecognition.onerror = () => this._setMicState(false);
    } catch (e) { console.debug("Speech not initialized:", e); }
  }

  _setMicState(active) {
    this._listeningToVoice = active;
    const btn = document.getElementById("btnPsychMic");
    if (btn) btn.innerText = active ? "🔴" : "🎙️";
  }

  startVoiceDictation() {
    this._sound?.playClick?.();
    if (!this._speechRecognition) {
      alert("🎙️ Voice dictation is not available in this browser. Use the keyboard or the option buttons.");
      return;
    }
    if (this._listeningToVoice) {
      this._speechRecognition.stop();
      this._setMicState(false);
    } else {
      try { this._speechStartTime = performance.now(); this._speechRecognition.start(); this._setMicState(true); } catch (e) { this._setMicState(false); }
    }
  }

  toggleBreathingGuide() {
    this._sound?.playClick?.();
    const circle = document.getElementById("breathingPacerCircle"), text = document.getElementById("breathingPacerText"), btn = document.getElementById("btnBreathingPacer");
    if (this._breathing) {
      clearInterval(this._breathingTimer);
      this._breathing = false;
      if (circle) { circle.innerText = "4s"; circle.style.transform = "scale(1)"; }
      if (text) text.innerHTML = '<span style="color:var(--neon-cyan); font-weight:bold;">4-4-6 GUIDE ON STANDBY</span><br>Inhale 4s · Hold 4s · Exhale 6s';
      if (btn) btn.innerText = "🧘 START RELAXATION";
      return;
    }
    this._breathing = true;
    if (btn) btn.innerText = "⏸️ PAUSE GUIDE";
    let seconds = 4, phase = "inhale";
    const step = () => {
      if (!this._breathing) return;
      if (circle) circle.innerText = `${seconds}s`;
      if (phase === "inhale") {
        if (text) text.innerHTML = '<strong style="color:var(--neon-cyan);">INHALE DEEPLY...</strong><br>Fill your lungs calmly';
        if (circle) circle.style.transform = `scale(${1 + (4 - seconds) * 0.08})`;
        if (seconds <= 0) { phase = "hold"; seconds = 4; }
      } else if (phase === "hold") {
        if (text) text.innerHTML = '<strong style="color:var(--neon-amber);">HOLD YOUR BREATH...</strong><br>Keep your composure';
        if (circle) circle.style.transform = "scale(1.32)";
        if (seconds <= 0) { phase = "exhale"; seconds = 6; }
      } else if (phase === "exhale") {
        if (text) text.innerHTML = '<strong style="color:var(--neon-green);">EXHALE SLOWLY...</strong><br>Release muscular tension';
        if (circle) circle.style.transform = `scale(${Math.max(1, 1.32 - (6 - seconds) * 0.053)})`;
        if (seconds <= 0) { phase = "inhale"; seconds = 4; this.addXp(15); }
      }
      seconds--;
    };
    step();
    this._breathingTimer = setInterval(step, 1000);
  }

  toggleTechnicalMatrix() {
    this._sound?.playClick?.();
    window.viewportController?.showRules();
  }

  updateHydration(isCrisis) {
    if (window.fitService) {
      window.fitService._volumeMl = isCrisis ? 900 : 2200;
      window.fitService.render();
    }
  }
}

window.WellnessController = WellnessController;
