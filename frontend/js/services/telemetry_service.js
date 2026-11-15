/**
 * ==============================================================================
 * CAPA DE SERVICIOS (CLIENT SERVICES): TelemetryService
 * Responsable de la comunicación de red desacoplada con el backend FastAPI.
 * ==============================================================================
 */

class TelemetryService {
  constructor(stateManager) {
    this._state = stateManager;
    this._intervalId = null;
    this._pollingMs = 2000;
  }

  iniciarPolling() {
    if (this._intervalId) return;
    // El libro de códigos se descarga una sola vez; a partir de ahí el enlace
    // transporta únicamente códigos y números.
    window.codebookService
      ?.cargar()
      .catch((err) => console.warn("CodebookService: usando reporte completo.", err))
      .finally(() => {
        this._obtenerTelemetria();
        this._intervalId = setInterval(() => {
          this._obtenerTelemetria();
        }, this._pollingMs);
      });
  }

  detenerPolling() {
    if (this._intervalId) {
      clearInterval(this._intervalId);
      this._intervalId = null;
    }
  }

  async _obtenerTelemetria() {
    try {
      // Ruta nominal: registro compacto + traducción local mediante el codebook.
      if (window.codebookService?.disponible) {
        const resp = await fetch("/api/v1/telemetria/compacto");
        if (resp.ok) {
          const registro = await resp.json();
          const reporte = window.codebookService.expandir(registro);
          if (reporte) {
            this._state.actualizarDesdeBackend(reporte);
            return;
          }
        }
      }

      // Repliegue: reporte completo con texto (depuración o codebook ausente).
      const resp = await fetch("/api/v1/fusion/resultado");
      if (resp.ok) {
        const datos = await resp.json();
        this._state.actualizarDesdeBackend(datos);
      }
    } catch (err) {
      // Enlace resiliente: no bloquear UI si el backend está en reconexión
      console.debug("TelemetryService: Enlace en espera o modo offline.");
    }
  }

  async obtenerCatalogoMatriz() {
    try {
      const resp = await fetch("/api/v1/matriz-decisiones");
      if (resp.ok) {
        return await resp.json();
      }
    } catch (err) {
      console.warn("TelemetryService: Fallo al obtener matriz:", err);
    }
    return [];
  }

  async obtenerContramedidasActivas() {
    try {
      const resp = await fetch("/api/v1/contramedidas/activas");
      if (resp.ok) {
        return await resp.json();
      }
    } catch (err) {
      console.warn("TelemetryService: Fallo al obtener contramedidas:", err);
    }
    return null;
  }

  async obtenerPreguntasPsicologicas() {
    try {
      const resp = await fetch("/api/v1/psicologico/preguntas");
      if (resp.ok) {
        return await resp.json();
      }
    } catch (err) {
      console.warn("TelemetryService: Fallo al cargar preguntas BHP:", err);
    }
    return null;
  }

  async evaluarRespuestaPsicologica(payload) {
    try {
      const resp = await fetch("/api/v1/psicologico/evaluar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (resp.ok) {
        return await resp.json();
      }
    } catch (err) {
      console.warn("TelemetryService: Fallo en evaluación psicológica remota:", err);
    }
    return null;
  }
}

window.telemetryService = new TelemetryService(window.stateManager);
