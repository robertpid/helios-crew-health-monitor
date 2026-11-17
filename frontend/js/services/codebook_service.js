/**
 * ==============================================================================
 * SERVICES LAYER: CodebookService
 *
 * Downloads the telemetry codebook ONCE and reconstructs on the client the
 * descriptive strings that used to travel in every cycle.
 *
 * The link carries only stable codes (CO2_ELEV, CX-03, KR03...) and numeric
 * values; the text is composed here. The output replicates exactly the shape of
 * the consolidated report, so the rest of the HUD needs no changes at all.
 *
 * This implementation is the JavaScript mirror of
 * `helios_inference/services/telemetry_compactor.expand()`: both must produce
 * identical strings.
 * ==============================================================================
 */

class CodebookService {
  constructor() {
    this._codebook = null;
    this._loading = null;
    this._ESCALATED = { CAUTION: "ALERT", ALERT: "CRITICAL", CRITICAL: "CRITICAL" };
  }

  get available() {
    return this._codebook !== null;
  }

  /**
   * Downloads the codebook exactly once (idempotent and race-safe).
   */
  async load() {
    if (this._codebook) return this._codebook;
    if (this._loading) return this._loading;

    this._loading = (async () => {
      const resp = await fetch("/api/v1/telemetry/codebook");
      if (!resp.ok) throw new Error(`Codebook HTTP ${resp.status}`);
      this._codebook = await resp.json();
      return this._codebook;
    })();

    try {
      return await this._loading;
    } finally {
      this._loading = null;
    }
  }

  /**
   * Substitutes the positional markers of a codebook template.
   * Supports `{0}`, `{0:.2f}` and the named marker `{day}`.
   */
  _format(template, value, day) {
    return template
      .replace(/\{0(?::\.(\d)f)?\}/g, (_, decimals) =>
        decimals === undefined ? String(value) : Number(value).toFixed(Number(decimals))
      )
      .replace(/\{day\}/g, String(day));
  }

  /**
   * Reconstructs the full consolidated report from the compact record.
   *
   * @param {object} r Compact record received from /api/v1/telemetry/compact
   * @returns {object|null} Report with the same shape as /api/v1/fusion/result
   */
  expand(r) {
    const cb = this._codebook;
    if (!cb || !r) return null;

    const met = r.met || [];
    const environmentalLabels = [];
    const biometricLabels = [];

    // --- Brain 1: environmental labels ---------------------------------------
    (r.amb || []).forEach((flag, i) => {
      if (!flag || i >= cb.environmental.length) return;
      const e = cb.environmental[i];
      if (e.code === "RAD_CRIT" && r.sol) {
        environmentalLabels.push(e.event_template);
      } else {
        environmentalLabels.push(this._format(e.template, met[e.metric] ?? 0, r.day));
      }
    });

    // --- Brain 2: biometric labels -------------------------------------------
    (r.bio || []).forEach((flag, i) => {
      if (!flag || i >= cb.biometric.length) return;
      const e = cb.biometric[i];
      const value = e.metric === null ? 0 : (met[e.metric] ?? 0);
      biometricLabels.push(this._format(e.template, value, r.day));
    });

    // The consolidation order mirrors the engine's: Brain 1, then Brain 2.
    const assessments = [...environmentalLabels, ...biometricLabels];

    // --- Brain 3: dominant edge of the Kronecker graph ------------------------
    let criticalEdge = "NOMINAL_STATE_NO_ADVERSE_SYNERGIES";
    let fusionText = cb.fusion_nominal.text;
    if (r.kr >= 0 && cb.kronecker_edges[r.kr]) {
      criticalEdge = cb.kronecker_edges[r.kr].name;
      fusionText = cb.fusion_template
        .replace("{edge}", criticalEdge)
        .replace(/\{severity(?::\.\df)?\}/, Number(r.krs).toFixed(1));
      if (r.krx) {
        fusionText += cb.severe_fusion_template;
        assessments.push(fusionText);
      }
    }

    // --- Brain 4: ASTRA -------------------------------------------------------
    const astraAlert = r.inc ? cb.astra.text : null;
    if (astraAlert) assessments.push(astraAlert);

    // --- Decision matrix ------------------------------------------------------
    const ruleMap = new Map(cb.rules.map((x) => [x.code, x]));
    const alerts = [];
    const countermeasures = [];

    (r.rg || []).forEach((rawCode) => {
      const escalation = rawCode.endsWith("!");
      const code = escalation ? rawCode.slice(0, -1) : rawCode;
      const rule = ruleMap.get(code);
      if (!rule) return;

      const level = escalation ? this._ESCALATED[rule.level] : rule.level;
      assessments.push(`[${code} - ${level}] ${rule.preliminary_assessment}`);
      alerts.push({
        rule_id: code,
        domain: rule.domain,
        level,
        preliminary_assessment: rule.preliminary_assessment,
        suggested_countermeasures: rule.countermeasures,
        recipients: rule.recipients,
        base_standard: rule.base_standard,
        time_window: rule.time_window,
        escalation,
      });
      rule.countermeasures.forEach((action) => {
        if (countermeasures.length < 3 && !countermeasures.includes(action)) {
          countermeasures.push(action);
        }
      });
    });

    // Reconstruction with the exact shape of the consolidated report
    return {
      inference_timestamp: new Date(r.ts * 1000).toISOString(),
      mission_id: r.mis,
      mission_day: r.day,
      astronaut_id: r.ast,
      brain_1_environmental: {
        environmental_vector: r.amb,
        activated_labels: environmentalLabels,
        co2_exceeded: !!r.amb?.[0],
        critical_radiation: !!r.amb?.[1],
        abnormal_pressure: !!r.amb?.[2],
      },
      brain_2_biometric: {
        biometric_vector: r.bio,
        activated_labels: biometricLabels,
        normal_physical_metrics: (r.bio || []).every((x) => !x),
        body_in_panic: !!r.bio?.[0],
      },
      brain_3_fusion_graph: {
        kronecker_vector_dimension: 12,
        critical_synergy_edge: criticalEdge,
        argmax_index: r.kr,
        max_severity_score: r.krs,
        severe_physiological_stress: !!r.krx,
        fusion_preliminary_assessment: fusionText,
      },
      brain_4_astra: {
        baseline_cosine_similarity: r.cos,
        cognitive_incongruence_detected: !!r.inc,
        astra_alert: astraAlert,
      },
      active_preliminary_assessments: assessments,
      decision_matrix_alerts: alerts,
      prioritized_countermeasures: countermeasures,
      compute_time_ms: r.ms,
      edge_metadata: cb.edge_metadata,
      raw_metrics: this._mapMetrics(met),
    };
  }

  /** Reconstructs the metrics dictionary from the positional array. */
  _mapMetrics(met) {
    const output = {};
    (this._codebook?.metric_order || []).forEach((key, i) => {
      output[key] = met[i];
    });
    return output;
  }
}

window.codebookService = new CodebookService();
