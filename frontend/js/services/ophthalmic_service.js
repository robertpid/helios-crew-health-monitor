/**
 * SERVICES LAYER: OphthalmicService
 * Preliminary Ophthalmological Assessment Engine and SANS Protocol (NASA JSC).
 * 5-stage battery: Acuity (Tumbling E), Astigmatism (Dial),
 * Contrast (Landolt C), Near Vision and Color Vision (Ishihara).
 * Anti-memorization random generation and keyboard shortcuts (Clean Code & SRP).
 * Strictly under 400 lines.
 */

class OphthalmicService {
  constructor(soundService = null) {
    this._sound = soundService || window.soundService;
    this._modalOpen = false;

    // Base catalog of Ishihara plates for Color Vision
    this._colorVisionCatalog = [
      { img: "/static/assets/ophthalmic/ishihara_1.webp", ans: "12", opts: ["12", "15", "17", "nothing"] },
      { img: "/static/assets/ophthalmic/ishihara_2.webp", ans: "29", opts: ["28", "29", "79", "nothing"] },
      { img: "/static/assets/ophthalmic/ishihara_3.webp", ans: "15", opts: ["15", "16", "45", "nothing"] },
      { img: "/static/assets/ophthalmic/ishihara_4.webp", ans: "97", opts: ["82", "91", "97", "nothing"] },
      { img: "/static/assets/ophthalmic/ishihara_5.webp", ans: "16", opts: ["10", "16", "48", "nothing"] },
      { img: "/static/assets/ophthalmic/ishihara_6.webp", ans: "nothing", opts: ["11", "20", "88", "nothing"] },
      { img: "/static/assets/ophthalmic/ishihara_7.webp", ans: "6", opts: ["5", "6", "8", "nothing"] }
    ];

    window.addEventListener("keydown", (e) => this._handleKeyboard(e));
    this._resetState();
  }

  _shuffleArray(array) {
    const copy = [...array];
    for (let i = copy.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  }

  _generateRandomTrials() {
    const DIRS = [
      { dir: "up", rot: 270 },
      { dir: "down", rot: 90 },
      { dir: "left", rot: 180 },
      { dir: "right", rot: 0 }
    ];

    // 1. Acuity: 10 sizes with 100% random orientation to avoid memorization bias
    const sizes = [68, 60, 52, 44, 38, 32, 28, 24, 20, 16];
    this._acuityPlates = sizes.map(sz => {
      const p = DIRS[Math.floor(Math.random() * DIRS.length)];
      return { dir: p.dir, rot: p.rot, sz };
    });

    // 2. Contrast: 8 levels with 100% random gap orientation
    const opacities = [1.0, 0.8, 0.65, 0.5, 0.38, 0.28, 0.20, 0.12];
    this._contrastPlates = opacities.map(op => {
      const p = DIRS[Math.floor(Math.random() * DIRS.length)];
      return { dir: p.dir, rot: p.rot, op };
    });

    // 3. Ishihara: random order of plates and of their option buttons
    this._colorVisionPlates = this._shuffleArray(this._colorVisionCatalog).map(item => ({
      ...item,
      opts: this._shuffleArray(item.opts)
    }));
  }

  _handleKeyboard(e) {
    if (!this._modalOpen) return;
    const map = {
      ArrowUp: "up",
      ArrowDown: "down",
      ArrowLeft: "left",
      ArrowRight: "right"
    };
    const dir = map[e.key];
    if (!dir) return;

    if (this._stage === 1) {
      e.preventDefault();
      this.answerAcuity(dir);
    } else if (this._stage === 3) {
      e.preventDefault();
      this.answerContrast(dir);
    }
  }

  _resetState() {
    this._stage = 0;
    this._subIndex = 0;
    this._acuityHits = 0;
    this._astigmatismRightEye = false;
    this._astigmatismLeftEye = false;
    this._contrastHits = 0;
    this._nearVisionResult = "full";
    this._colorVisionHits = 0;
    this._generateRandomTrials();
  }

  openModal() {
    this._sound?.playClick?.();
    this._modalOpen = true;
    this._resetState();
    const modal = document.getElementById("modalOphthalmic");
    if (modal) modal.style.display = "flex";
    this._showView("ophthStepIntro");
    this._updateProgress("INSPECTION", 0);
  }

  closeModal() {
    this._sound?.playClick?.();
    this._modalOpen = false;
    const modal = document.getElementById("modalOphthalmic");
    if (modal) modal.style.display = "none";
  }

  startStage1() {
    this._sound?.playClick?.();
    this._stage = 1;
    this._subIndex = 0;
    this._acuityHits = 0;
    this._showView("ophthStepAcuity");
    this._renderTumblingE();
    this._updateProgress("STAGE 1/5", 15);
  }

  _renderTumblingE() {
    const item = this._acuityPlates[this._subIndex];
    const el = document.getElementById("ophthTumblingE");
    const tag = document.getElementById("ophthAcuityIndex");
    const eyeTag = document.getElementById("ophthAcuityEyeTag");
    if (tag) tag.innerText = this._subIndex + 1;
    if (eyeTag) {
      eyeTag.innerText = this._subIndex < 5
        ? "RIGHT EYE (Cover your left eye)"
        : "LEFT EYE (Cover your right eye)";
    }
    if (el && item) {
      el.style.transform = `rotate(${item.rot}deg)`;
      el.style.fontSize = `${item.sz}px`;
    }
  }

  answerAcuity(direction) {
    this._sound?.playClick?.();
    const item = this._acuityPlates[this._subIndex];
    if (item && item.dir === direction) this._acuityHits++;

    this._subIndex++;
    if (this._subIndex < this._acuityPlates.length) {
      this._renderTumblingE();
    } else {
      this._startStage2();
    }
  }

  _startStage2() {
    this._stage = 2;
    this._subIndex = 0; // 0: right eye, 1: left eye
    this._showView("ophthStepAstigmatism");
    this._updateProgress("STAGE 2/5", 35);
    const eyeTag = document.getElementById("ophthAstigEyeTag");
    if (eyeTag) eyeTag.innerText = "RIGHT EYE (Cover your left eye)";
  }

  answerAstigmatism(seesDarkLine) {
    this._sound?.playClick?.();
    if (this._subIndex === 0) {
      this._astigmatismRightEye = seesDarkLine;
      this._subIndex = 1;
      const eyeTag = document.getElementById("ophthAstigEyeTag");
      if (eyeTag) eyeTag.innerText = "LEFT EYE (Cover your right eye)";
    } else {
      this._astigmatismLeftEye = seesDarkLine;
      this._startStage3();
    }
  }

  _startStage3() {
    this._stage = 3;
    this._subIndex = 0;
    this._contrastHits = 0;
    this._showView("ophthStepContrast");
    this._renderLandoltC();
    this._updateProgress("STAGE 3/5", 55);
  }

  _renderLandoltC() {
    const item = this._contrastPlates[this._subIndex];
    const el = document.getElementById("ophthLandoltSvg");
    const tag = document.getElementById("ophthContrastIndex");
    if (tag) tag.innerText = this._subIndex + 1;
    if (el && item) {
      el.style.transform = `rotate(${item.rot}deg)`;
      el.style.opacity = item.op;
    }
  }

  answerContrast(direction) {
    this._sound?.playClick?.();
    const item = this._contrastPlates[this._subIndex];
    if (item && item.dir === direction) this._contrastHits++;

    this._subIndex++;
    if (this._subIndex < this._contrastPlates.length) {
      this._renderLandoltC();
    } else {
      this._startStage4();
    }
  }

  _startStage4() {
    this._stage = 4;
    this._showView("ophthStepNearVision");
    this._updateProgress("STAGE 4/5", 75);
  }

  answerNearVision(result) {
    this._sound?.playClick?.();
    this._nearVisionResult = result;
    this._startStage5();
  }

  _startStage5() {
    this._stage = 5;
    this._subIndex = 0;
    this._colorVisionHits = 0;
    this._showView("ophthStepColorVision");
    this._renderIshihara();
    this._updateProgress("STAGE 5/5", 90);
  }

  _renderIshihara() {
    const item = this._colorVisionPlates[this._subIndex];
    const imgEl = document.getElementById("ophthIshiharaImg");
    const idxEl = document.getElementById("ophthColorIndex");
    const optsContainer = document.getElementById("ophthIshiharaOptions");
    if (idxEl) idxEl.innerText = this._subIndex + 1;
    if (imgEl && item) imgEl.src = item.img;

    if (optsContainer && item) {
      optsContainer.innerHTML = item.opts.map(opt => `
        <button class="btn-hud" onclick="window.ophthalmicService?.answerColorVision('${opt}')" style="padding:10px 14px; font-size:13px; font-weight:600;">
          ${opt === "nothing" ? "None / Nothing" : opt}
        </button>
      `).join("");
    }
  }

  answerColorVision(selection) {
    this._sound?.playClick?.();
    const item = this._colorVisionPlates[this._subIndex];
    if (item && item.ans === selection) this._colorVisionHits++;

    this._subIndex++;
    if (this._subIndex < this._colorVisionPlates.length) {
      this._renderIshihara();
    } else {
      this._showResults();
    }
  }

  _showResults() {
    this._stage = 6;
    this._showView("ophthStepResults");
    this._updateProgress("COMPLETED", 100);

    const setBadge = (idVal, idBadge, valTxt, state) => {
      const elVal = document.getElementById(idVal), elB = document.getElementById(idBadge);
      if (elVal) elVal.innerText = valTxt;
      if (elB) {
        elB.innerText = state;
        if (state === "Stable") {
          elB.style.background = "rgba(0, 255, 136, 0.15)";
          elB.style.color = "var(--neon-green)";
        } else if (state === "Caution") {
          elB.style.background = "rgba(245, 158, 11, 0.15)";
          elB.style.color = "#f59e0b";
        } else {
          elB.style.background = "rgba(255, 34, 85, 0.15)";
          elB.style.color = "var(--neon-red)";
        }
      }
    };

    // 1. Visual acuity (8-10 Stable, 6-7 Caution, 0-5 Review)
    const acuityState = this._acuityHits >= 8 ? "Stable" : (this._acuityHits >= 6 ? "Caution" : "Review");
    setBadge("resAcuityVal", "resAcuityBadge", `${this._acuityHits}/10`, acuityState);

    // 2. Astigmatism (both no = Stable, 1 yes = Caution, both yes = Review)
    let astigState = "Stable";
    if (this._astigmatismRightEye && this._astigmatismLeftEye) astigState = "Review";
    else if (this._astigmatismRightEye || this._astigmatismLeftEye) astigState = "Caution";
    const astigTxt = `${this._astigmatismRightEye ? "OD(+)" : "OD(-)"} / ${this._astigmatismLeftEye ? "OS(+)" : "OS(-)"}`;
    setBadge("resAstigVal", "resAstigBadge", astigTxt, astigState);

    // 3. Contrast vision (7-8 Stable, 5-6 Caution, 0-4 Review)
    const contrastState = this._contrastHits >= 7 ? "Stable" : (this._contrastHits >= 5 ? "Caution" : "Review");
    setBadge("resContrastVal", "resContrastBadge", `${this._contrastHits}/8`, contrastState);

    // 4. Near vision (full=Stable, partial=Caution, hard=Review)
    const nearState = this._nearVisionResult === "full" ? "Stable" : (this._nearVisionResult === "partial" ? "Caution" : "Review");
    const nearTxt = this._nearVisionResult === "full" ? "Full" : (this._nearVisionResult === "partial" ? "Partial" : "Reduced");
    setBadge("resNearVisionVal", "resNearVisionBadge", nearTxt, nearState);

    // 5. Color vision (6-7 Stable, 4-5 Caution, 0-3 Review)
    const colorState = this._colorVisionHits >= 6 ? "Stable" : (this._colorVisionHits >= 4 ? "Caution" : "Review");
    setBadge("resColorVisionVal", "resColorVisionBadge", `${this._colorVisionHits}/7`, colorState);
  }

  saveAndTransmit() {
    this._sound?.playClick?.();
    window.wellnessController?.addXp?.(50);
    const acuityPct = Math.round((this._acuityHits / 10) * 100);
    const contrastPct = Math.round((this._contrastHits / 8) * 100);
    window.surgeonController?.logExamResult?.("sans", {
      state: this._acuityHits >= 8 && this._contrastHits >= 7 ? "STABLE" : "OBSERVATION",
      summary: `${this._acuityHits}/10 (${acuityPct}%)`,
      acuity: `${this._acuityHits}/10 (${acuityPct}%)`,
      contrast: `${contrastPct}% (${this._contrastHits}/8)`,
      amsler: (this._astigmatismRightEye || this._astigmatismLeftEye) ? "Radial asymmetry" : "No distortion",
      ishihara: `${this._colorVisionHits}/7 plates`
    });
    this.closeModal();

    const msg = `📡 <strong>SANS OPHTHALMOLOGICAL ASSESSMENT:</strong> Sol 120 battery completed. Acuity: ${this._acuityHits}/10 · Contrast: ${this._contrastHits}/8. Data transmitted to the Houston Flight Surgeon.`;
    window.wellnessController?._showFeedback?.(msg);
  }

  _showView(viewId) {
    const views = [
      "ophthStepIntro", "ophthStepAcuity", "ophthStepAstigmatism",
      "ophthStepContrast", "ophthStepNearVision", "ophthStepColorVision", "ophthStepResults"
    ];
    views.forEach(v => {
      const el = document.getElementById(v);
      if (el) el.style.display = (v === viewId) ? "block" : "none";
    });
  }

  _updateProgress(label, pct) {
    const tag = document.getElementById("ophthProgressTag");
    const bar = document.getElementById("ophthProgressBar");
    if (tag) tag.innerText = label;
    if (bar) bar.style.width = `${pct}%`;
  }
}

window.ophthalmicService = new OphthalmicService(window.soundService);
