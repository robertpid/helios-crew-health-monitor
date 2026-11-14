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
    this._obtenerTelemetria();
    this._intervalId = setInterval(() => {
      this._obtenerTelemetria();
    }, this._pollingMs);
  }

  detenerPolling() {
    if (this._intervalId) {
      clearInterval(this._intervalId);
      this._intervalId = null;
    }
  }

  async _obtenerTelemetria() {
    try {
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
}

window.telemetryService = new TelemetryService(window.stateManager);
