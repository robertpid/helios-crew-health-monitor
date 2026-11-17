/**
 * ==============================================================================
 * SERVICES LAYER (CLIENT SERVICES): TelemetryService
 * Responsible for decoupled network communication with the FastAPI backend.
 * ==============================================================================
 */

class TelemetryService {
  constructor(stateManager) {
    this._state = stateManager;
    this._intervalId = null;
    this._pollingMs = 2000;
  }

  startPolling() {
    if (this._intervalId) return;
    // The codebook is downloaded once; from then on the link carries only
    // codes and numbers.
    window.codebookService
      ?.load()
      .catch((err) => console.warn("CodebookService: falling back to the full report.", err))
      .finally(() => {
        this._getTelemetry();
        this._intervalId = setInterval(() => {
          this._getTelemetry();
        }, this._pollingMs);
      });
  }

  stopPolling() {
    if (this._intervalId) {
      clearInterval(this._intervalId);
      this._intervalId = null;
    }
  }

  async _getTelemetry() {
    try {
      // Nominal path: compact record + local translation through the codebook.
      if (window.codebookService?.available) {
        const resp = await fetch("/api/v1/telemetry/compact");
        if (resp.ok) {
          const record = await resp.json();
          const report = window.codebookService.expand(record);
          if (report) {
            this._state.updateFromBackend(report);
            return;
          }
        }
      }

      // Fallback: full report with text (debugging or codebook absent).
      const resp = await fetch("/api/v1/fusion/result");
      if (resp.ok) {
        const data = await resp.json();
        this._state.updateFromBackend(data);
      }
    } catch (err) {
      // Resilient link: do not block the UI if the backend is reconnecting
      console.debug("TelemetryService: link waiting or offline mode.");
    }
  }

  async getMatrixCatalog() {
    try {
      const resp = await fetch("/api/v1/decision-matrix");
      if (resp.ok) {
        return await resp.json();
      }
    } catch (err) {
      console.warn("TelemetryService: failed to fetch the matrix:", err);
    }
    return [];
  }

  async getActiveCountermeasures() {
    try {
      const resp = await fetch("/api/v1/countermeasures/active");
      if (resp.ok) {
        return await resp.json();
      }
    } catch (err) {
      console.warn("TelemetryService: failed to fetch countermeasures:", err);
    }
    return null;
  }

  async getPsychologicalQuestions() {
    try {
      const resp = await fetch("/api/v1/psychological/questions");
      if (resp.ok) {
        return await resp.json();
      }
    } catch (err) {
      console.warn("TelemetryService: failed to load the BHP questions:", err);
    }
    return null;
  }

  async evaluatePsychologicalResponse(payload) {
    try {
      const resp = await fetch("/api/v1/psychological/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (resp.ok) {
        return await resp.json();
      }
    } catch (err) {
      console.warn("TelemetryService: remote psychological assessment failed:", err);
    }
    return null;
  }
}

window.telemetryService = new TelemetryService(window.stateManager);
