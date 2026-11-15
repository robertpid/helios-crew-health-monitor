/**
 * ==============================================================================
 * STATE LAYER (STATE MANAGEMENT): StateManager
 * Reactive Observer / Singleton pattern to synchronize the Cockpit HUD.
 * Kept strictly under 300 lines (Clean Code & SRP).
 * ==============================================================================
 */

class StateManager {
  constructor() {
    this._listeners = [];

    this._state = {
      activeHabitat: "MARS_TRANSIT",
      activeView: "biomedical",
      crisisMode: false,
      alertModalOpen: false,
      selectedOrgan: null,

      telemetry: {
        mission_id: "ARES-VI-MARS-EXPEDITION",
        mission_day: 120,
        astronaut_id: "ASTRO-HELIOS-01",
        physiology: {
          heart_rate_bpm: 76.0,
          spo2_pct: 98.0,
          systolic_pressure: 118,
          diastolic_pressure: 76,
          body_temperature_c: 36.6,
          skin_temperature_c: 34.8,
          hrv_ms: 42.0,
          respiratory_rate_rpm: 14.0,
          last_cycle_sleep_hours: 7.2,
          bone_loss_pct: 1.8,
          ared_activity_pct: 100.0,
          fluids_liters_per_day: 2.2,
        },
        environment: {
          co2_mmHg: 1.8,
          co2_ppm: 1200,
          cumulative_radiation_mSv: 85.0,
          daily_radiation_rate_mSv: 1.80,
          cabin_pressure_kpa: 101.3,
          cabin_temperature_c: 21.8,
          relative_humidity_pct: 45.0,
          solar_event_active: false,
          gravity_g: 0.0,
          noise_db: 58.0,
        },
        cognition: {
          voice_latency_ms: 210.0,
          lexical_density_score: 0.95,
          cosine_similarity: 0.985,
          incongruence_detected: false,
          astra_alert: null,
          sans_vision_symptom: false,
        },
        kronecker: {
          critical_edge: "NOMINAL_STATE_NO_SYNERGIES",
          max_severity: 0.0,
          severe_stress: false,
          argmax_index: -1,
        },
        prioritized_countermeasures: [
          "Maintain the daily hydration protocol (2.2 L/day).",
          "Complete the scheduled ARED squat and deadlift routine.",
          "Check the filters of the cabin life support system.",
        ],
        active_alerts: [],
      },
    };
  }

  subscribe(listener) {
    this._listeners.push(listener);
    listener(this._state);
    return () => {
      this._listeners = this._listeners.filter(l => l !== listener);
    };
  }

  notify() {
    for (const listener of this._listeners) {
      listener(this._state);
    }
  }

  getState() {
    return this._state;
  }

  setActiveView(view) {
    if (this._state.activeView !== view) {
      this._state.activeView = view;
      this.notify();
    }
  }

  setHabitat(habitatKey) {
    this._state.activeHabitat = habitatKey;
    const env = this._state.telemetry.environment;

    if (habitatKey === "MARS_BASE") {
      env.gravity_g = 0.38;
      env.cumulative_radiation_mSv = 42.0;
      env.daily_radiation_rate_mSv = 0.67;
      env.co2_mmHg = 1.6;
      env.co2_ppm = 710;
      env.cabin_pressure_kpa = 101.3;
      env.cabin_temperature_c = 22.4;
      env.relative_humidity_pct = 52.0;
      env.solar_event_active = false;
    } else if (habitatKey === "SPACE_STATION") {
      env.gravity_g = 0.0;
      env.cumulative_radiation_mSv = 22.5;
      env.daily_radiation_rate_mSv = 0.55;
      env.co2_mmHg = 2.1;
      env.co2_ppm = 1400;
      env.cabin_pressure_kpa = 101.3;
      env.cabin_temperature_c = 23.0;
      env.relative_humidity_pct = 42.0;
      env.solar_event_active = false;
    } else {
      env.gravity_g = 0.0;
      env.cumulative_radiation_mSv = 85.0;
      env.daily_radiation_rate_mSv = 1.80;
      env.co2_mmHg = 1.8;
      env.co2_ppm = 800;
      env.cabin_pressure_kpa = 101.3;
      env.cabin_temperature_c = 21.8;
      env.relative_humidity_pct = 45.0;
      env.solar_event_active = false;
    }
    this.notify();
  }

  setHabitatModel(model) {
    const map = {
      orion: "MARS_TRANSIT",
      mars: "MARS_BASE",
      iss: "SPACE_STATION"
    };
    this.setHabitat(map[model] || model);
  }

  setSelectedOrgan(organ) {
    this._state.selectedOrgan = organ;
    this.notify();
  }

  setAlertModal(open) {
    this._state.alertModalOpen = open;
    this.notify();
  }

  toggleAlertModal() {
    this.setAlertModal(!this._state.alertModalOpen);
  }

  setOperationMode(mode) {
    if (mode === "crisis") this.activateCrisisMode();
    else this.restoreNominalMode();
  }

  activateCrisisMode() {
    this._state.crisisMode = true;
    this._state.alertModalOpen = true;

    this._state.telemetry.physiology.heart_rate_bpm = 132.0;
    this._state.telemetry.physiology.spo2_pct = 88.0;
    this._state.telemetry.physiology.body_temperature_c = 38.4;
    this._state.telemetry.physiology.hrv_ms = 18.0;
    this._state.telemetry.physiology.systolic_pressure = 145;
    this._state.telemetry.physiology.diastolic_pressure = 95;

    this._state.telemetry.environment.co2_mmHg = 3.8;
    this._state.telemetry.environment.co2_ppm = 3200;
    this._state.telemetry.environment.solar_event_active = true;

    this._state.telemetry.cognition.voice_latency_ms = 850.0;
    this._state.telemetry.cognition.lexical_density_score = 0.45;
    this._state.telemetry.cognition.cosine_similarity = 0.72;
    this._state.telemetry.cognition.incongruence_detected = true;
    this._state.telemetry.cognition.astra_alert =
      "Cognitive Incongruence Detected. Preliminary assessment: Possible fatigue masking.";

    this._state.telemetry.kronecker.critical_edge = "CO2_WITH_SANS_INTRACRANIAL_HYPERTENSION";
    this._state.telemetry.kronecker.max_severity = 9.2;
    this._state.telemetry.kronecker.severe_stress = true;
    this._state.telemetry.kronecker.argmax_index = 3;

    this._state.telemetry.prioritized_countermeasures = [
      "1. Immediately don the O₂ mask and assume a resting position.",
      "2. Raise the forced CO₂ removal cycle in the cabin module (ECLSS).",
      "3. Notify the flight surgeon and transmit telemetry in the DSN window.",
    ];

    this.notify();
  }

  restoreNominalMode() {
    this._state.crisisMode = false;
    this._state.alertModalOpen = false;

    this._state.telemetry.physiology.heart_rate_bpm = 76.0;
    this._state.telemetry.physiology.spo2_pct = 98.0;
    this._state.telemetry.physiology.body_temperature_c = 36.6;
    this._state.telemetry.physiology.hrv_ms = 42.0;
    this._state.telemetry.physiology.systolic_pressure = 118;
    this._state.telemetry.physiology.diastolic_pressure = 76;

    this._state.telemetry.environment.co2_mmHg = 1.8;
    this._state.telemetry.environment.co2_ppm = 1200;
    this._state.telemetry.environment.solar_event_active = false;

    this._state.telemetry.cognition.voice_latency_ms = 210.0;
    this._state.telemetry.cognition.lexical_density_score = 0.95;
    this._state.telemetry.cognition.cosine_similarity = 0.985;
    this._state.telemetry.cognition.incongruence_detected = false;
    this._state.telemetry.cognition.astra_alert = null;

    this._state.telemetry.kronecker.critical_edge = "NOMINAL_STATE_NO_SYNERGIES";
    this._state.telemetry.kronecker.max_severity = 0.0;
    this._state.telemetry.kronecker.severe_stress = false;
    this._state.telemetry.kronecker.argmax_index = -1;

    this._state.telemetry.prioritized_countermeasures = [
      "Maintain the daily hydration protocol (2.2 L/day).",
      "Complete the scheduled ARED squat and deadlift routine.",
      "Check the filters of the cabin life support system.",
    ];

    this.notify();
  }

  updateFromBackend(consolidatedReport) {
    if (this._state.crisisMode) return;

    if (!consolidatedReport) return;
    const b3 = consolidatedReport.brain_3_fusion_graph;
    const b4 = consolidatedReport.brain_4_astra;

    if (b3) {
      this._state.telemetry.kronecker.critical_edge = b3.critical_synergy_edge;
      this._state.telemetry.kronecker.max_severity = b3.max_severity_score;
      this._state.telemetry.kronecker.severe_stress = b3.severe_physiological_stress;
      this._state.telemetry.kronecker.argmax_index = b3.argmax_index;
    }

    if (b4) {
      this._state.telemetry.cognition.cosine_similarity = b4.baseline_cosine_similarity;
      this._state.telemetry.cognition.incongruence_detected = b4.cognitive_incongruence_detected;
      this._state.telemetry.cognition.astra_alert = b4.astra_alert;
    }

    if (consolidatedReport.prioritized_countermeasures?.length > 0) {
      this._state.telemetry.prioritized_countermeasures = consolidatedReport.prioritized_countermeasures;
    }

    this.notify();
  }

  updateCognition(cognitiveData) {
    if (!cognitiveData) return;
    const cog = this._state.telemetry.cognition;
    if (cognitiveData.latency_ms !== undefined) {
      cog.voice_latency_ms = Number(cognitiveData.latency_ms);
    }
    if (cognitiveData.lexical_density !== undefined) {
      cog.lexical_density_score = Number(cognitiveData.lexical_density);
    }
    if (cognitiveData.cosine_similarity !== undefined) {
      cog.cosine_similarity = Number(cognitiveData.cosine_similarity);
    }
    if (cognitiveData.incongruence_detected !== undefined) {
      cog.incongruence_detected = Boolean(cognitiveData.incongruence_detected);
    }
    if (cognitiveData.astra_alert !== undefined) {
      cog.astra_alert = cognitiveData.astra_alert;
    }
    this.notify();
  }
}

window.stateManager = new StateManager();
