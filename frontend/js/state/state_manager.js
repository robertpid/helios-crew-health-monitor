/**
 * ==============================================================================
 * CAPA DE ESTADO (STATE MANAGEMENT): StateManager
 * Patrón Observer / Singleton reactivo para sincronizar el Cockpit HUD.
 * ==============================================================================
 */

class StateManager {
  constructor() {
    this._listeners = [];

    // Estado centralizado inmutable por mutadores controlados
    this._state = {
      habitatActivo: "TRANSITO_MARTE",
      vistaActiva: "biomedical", // 'biomedical' | 'environmental' | 'matrix'
      modoCrisis: false,
      modalAlertaAbierto: false,
      organoSeleccionado: null,
      
      // Datos de telemetría nominales por defecto
      telemetria: {
        id_mision: "ARES-VI-MARS-EXPEDITION",
        dia_mision: 120,
        astronauta_id: "ASTRO-HELIOS-01",
        fisiologia: {
          ritmo_cardiaco_bpm: 76.0,
          spo2_pct: 98.0,
          presion_sistolica: 118,
          presion_diastolica: 76,
          temperatura_corporal_c: 36.6,
          temperatura_piel_c: 34.8,
          variabilidad_hrv_ms: 42.0,
          frecuencia_respiratoria_rpm: 14.0,
          horas_sueno_ultimo_ciclo: 7.2,
          perdida_osea_pct: 1.8,
          actividad_ared_pct: 100.0,
          liquidos_litros_dia: 2.2,
        },
        ambiente: {
          co2_mmHg: 1.8,
          co2_ppm: 1200,
          radiacion_acumulada_mSv: 85.0,
          radiacion_tasa_diaria_mSv: 1.80,
          presion_cabina_kpa: 101.3,
          temperatura_cabina_c: 21.8,
          humedad_relativa_pct: 45.0,
          evento_solar_activo: false,
          gravedad_g: 0.0,
          ruido_db: 58.0,
        },
        cognicion: {
          latencia_voz_ms: 210.0,
          densidad_lexica_score: 0.95,
          similitud_coseno: 0.985,
          incongruencia_detectada: false,
          alerta_astra: null,
          sans_sintoma_vision: false,
        },
        kronecker: {
          arista_critica: "ESTADO_NOMINAL_SIN_SINERGIAS",
          severidad_maxima: 0.0,
          estres_severo: false,
          indice_argmax: -1,
        },
        contramedidas_priorizadas: [
          "Mantener protocolo de hidratación diaria (2.2 L/día).",
          "Cumplir rutina de sentadilla y peso muerto en ARED programada.",
          "Verificar filtros del sistema de soporte vital de cabina.",
        ],
        alertas_activas: [],
      },
    };
  }

  // Patrón Observer
  subscribe(listener) {
    this._listeners.push(listener);
    // Ejecutar inmediatamente con el estado actual
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

  setVistaActiva(vista) {
    if (this._state.vistaActiva !== vista) {
      this._state.vistaActiva = vista;
      this.notify();
    }
  }

  setHabitat(habitatKey) {
    this._state.habitatActivo = habitatKey;
    const amb = this._state.telemetria.ambiente;

    if (habitatKey === "BASE_MARTE") {
      amb.gravedad_g = 0.38;
      amb.radiacion_acumulada_mSv = 42.0;
      amb.radiacion_tasa_diaria_mSv = 0.67;
      amb.co2_mmHg = 1.6;
      amb.co2_ppm = 710;
      amb.presion_cabina_kpa = 101.3;
      amb.temperatura_cabina_c = 22.4;
      amb.humedad_relativa_pct = 52.0;
      amb.evento_solar_activo = false;
    } else if (habitatKey === "ESTACION_ESPACIAL") {
      amb.gravedad_g = 0.0;
      amb.radiacion_acumulada_mSv = 22.5;
      amb.radiacion_tasa_diaria_mSv = 0.55;
      amb.co2_mmHg = 2.1;
      amb.co2_ppm = 1400;
      amb.presion_cabina_kpa = 101.3;
      amb.temperatura_cabina_c = 23.0;
      amb.humedad_relativa_pct = 42.0;
      amb.evento_solar_activo = false;
    } else {
      // TRANSITO_MARTE / NAVE ESPACIAL ORION
      amb.gravedad_g = 0.0;
      amb.radiacion_acumulada_mSv = 85.0;
      amb.radiacion_tasa_diaria_mSv = 1.80;
      amb.co2_mmHg = 1.8;
      amb.co2_ppm = 800;
      amb.presion_cabina_kpa = 101.3;
      amb.temperatura_cabina_c = 21.8;
      amb.humedad_relativa_pct = 45.0;
      amb.evento_solar_activo = false;
    }
    this.notify();
  }

  setOrganoSeleccionado(organo) {
    this._state.organoSeleccionado = organo;
    this.notify();
  }

  setModalAlerta(abierto) {
    this._state.modalAlertaAbierto = abierto;
    this.notify();
  }

  activarModoCrisis() {
    this._state.modoCrisis = true;
    this._state.modalAlertaAbierto = true;

    // Mutar telemetría hacia el escenario crítico del boceto
    this._state.telemetria.fisiologia.ritmo_cardiaco_bpm = 132.0;
    this._state.telemetria.fisiologia.spo2_pct = 88.0;
    this._state.telemetria.fisiologia.temperatura_corporal_c = 38.4;
    this._state.telemetria.fisiologia.variabilidad_hrv_ms = 18.0;
    this._state.telemetria.fisiologia.presion_sistolica = 145;
    this._state.telemetria.fisiologia.presion_diastolica = 95;

    this._state.telemetria.ambiente.co2_mmHg = 3.8;
    this._state.telemetria.ambiente.co2_ppm = 3200;
    this._state.telemetria.ambiente.evento_solar_activo = true;

    this._state.telemetria.cognicion.latencia_voz_ms = 850.0;
    this._state.telemetria.cognicion.densidad_lexica_score = 0.45;
    this._state.telemetria.cognicion.similitud_coseno = 0.72;
    this._state.telemetria.cognicion.incongruencia_detectada = true;
    this._state.telemetria.cognicion.alerta_astra =
      "Incongruencia Cognitiva Detectada. Evaluación preliminar: Posible ocultamiento de fatiga.";

    this._state.telemetria.kronecker.arista_critica = "CO2_CON_HIPERTENSION_INTRACRANEAL_SANS";
    this._state.telemetria.kronecker.severidad_maxima = 9.2;
    this._state.telemetria.kronecker.estres_severo = true;
    this._state.telemetria.kronecker.indice_argmax = 3;

    this._state.telemetria.contramedidas_priorizadas = [
      "1. Colocación inmediata de mascarilla de O₂ y posición de reposo.",
      "2. Elevar ciclo forzado de remoción de CO₂ en módulo de cabina (ECLSS).",
      "3. Notificar al médico de vuelo y transmitir telemetría en ventana DSN.",
    ];

    this.notify();
  }

  restablecerModoNominal() {
    this._state.modoCrisis = false;
    this._state.modalAlertaAbierto = false;

    this._state.telemetria.fisiologia.ritmo_cardiaco_bpm = 76.0;
    this._state.telemetria.fisiologia.spo2_pct = 98.0;
    this._state.telemetria.fisiologia.temperatura_corporal_c = 36.6;
    this._state.telemetria.fisiologia.variabilidad_hrv_ms = 42.0;
    this._state.telemetria.fisiologia.presion_sistolica = 118;
    this._state.telemetria.fisiologia.presion_diastolica = 76;

    this._state.telemetria.ambiente.co2_mmHg = 1.8;
    this._state.telemetria.ambiente.co2_ppm = 1200;
    this._state.telemetria.ambiente.evento_solar_activo = false;

    this._state.telemetria.cognicion.latencia_voz_ms = 210.0;
    this._state.telemetria.cognicion.densidad_lexica_score = 0.95;
    this._state.telemetria.cognicion.similitud_coseno = 0.985;
    this._state.telemetria.cognicion.incongruencia_detectada = false;
    this._state.telemetria.cognicion.alerta_astra = null;

    this._state.telemetria.kronecker.arista_critica = "ESTADO_NOMINAL_SIN_SINERGIAS";
    this._state.telemetria.kronecker.severidad_maxima = 0.0;
    this._state.telemetria.kronecker.estres_severo = false;
    this._state.telemetria.kronecker.indice_argmax = -1;

    this._state.telemetria.contramedidas_priorizadas = [
      "Mantener protocolo de hidratación diaria (2.2 L/día).",
      "Cumplir rutina de sentadilla y peso muerto en ARED programada.",
      "Verificar filtros del sistema de soporte vital de cabina.",
    ];

    this.notify();
  }

  actualizarDesdeBackend(reporteConsolidado) {
    if (this._state.modoCrisis) return; // No sobreescribir si el usuario está en demo de crisis

    if (!reporteConsolidado) return;
    const c1 = reporteConsolidado.cerebro_1_ambiental;
    const c2 = reporteConsolidado.cerebro_2_biometrico;
    const c3 = reporteConsolidado.cerebro_3_grafo_fusion;
    const c4 = reporteConsolidado.cerebro_4_astra;

    if (c3) {
      this._state.telemetria.kronecker.arista_critica = c3.arista_sinergica_critica;
      this._state.telemetria.kronecker.severidad_maxima = c3.puntaje_severidad_maximo;
      this._state.telemetria.kronecker.estres_severo = c3.estres_fisiologico_severo;
      this._state.telemetria.kronecker.indice_argmax = c3.indice_argmax;
    }

    if (c4) {
      this._state.telemetria.cognicion.similitud_coseno = c4.similitud_coseno_linea_base;
      this._state.telemetria.cognicion.incongruencia_detectada = c4.incongruencia_cognitiva_detectada;
      this._state.telemetria.cognicion.alerta_astra = c4.alerta_astra;
    }

    if (reporteConsolidado.contramedidas_priorizadas && reporteConsolidado.contramedidas_priorizadas.length > 0) {
      this._state.telemetria.contramedidas_priorizadas = reporteConsolidado.contramedidas_priorizadas;
    }

    this.notify();
  }
}

// Instancia global compartida (Singleton)
window.stateManager = new StateManager();
