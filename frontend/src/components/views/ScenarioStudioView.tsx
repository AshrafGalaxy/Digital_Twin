import React, { useState, useEffect } from 'react';
import {
  Sliders,
  Play,
  CheckCircle2,
  AlertTriangle,
  TrendingDown,
  TrendingUp,
  Cpu,
  Info,
  History,
  HelpCircle
} from 'lucide-react';
import { ScenarioTemplate, ScenarioRunResult } from '../../types/twin';
import { fetchScenarioTemplates, runScenario, fetchRecentScenarioRuns } from '../../services/api';

export const ScenarioStudioView: React.FC = () => {
  const [templates, setTemplates] = useState<ScenarioTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('SCEN-INT-01');
  const [greenExtension, setGreenExtension] = useState<number>(15);
  const [demandMultiplier, setDemandMultiplier] = useState<number>(1.0);
  const [randomSeed, setRandomSeed] = useState<number>(42);

  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [runResult, setRunResult] = useState<ScenarioRunResult | null>(null);
  const [recentRuns, setRecentRuns] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchScenarioTemplates()
      .then(setTemplates)
      .catch(err => console.error('Failed loading templates', err));

    fetchRecentScenarioRuns()
      .then(setRecentRuns)
      .catch(err => console.error('Failed loading recent runs', err));
  }, []);

  const handleRunSimulation = async () => {
    setIsRunning(true);
    setError(null);
    try {
      const result = await runScenario({
        templateId: selectedTemplateId,
        greenExtensionSec: greenExtension,
        demandMultiplier: demandMultiplier,
        randomSeed: randomSeed
      });
      setRunResult(result);
      fetchRecentScenarioRuns().then(setRecentRuns).catch(() => null);
    } catch (err: any) {
      setError(err.message || 'Failed to complete simulation run');
    } finally {
      setIsRunning(false);
    }
  };

  const selectedTemplate = templates.find(t => t.id === selectedTemplateId);

  return (
    <div className="view-container scenario-studio-view">
      {/* View Header */}
      <div className="view-header">
        <div>
          <h1 className="view-title">Scenario Studio — Microscopic Traffic Simulation Sandbox</h1>
          <p className="view-subtitle">
            Controlled baseline vs. intervention simulation on Viman Nagar Chowk (VN-01) ↔ Somnath Nagar Chowk (SN-01) corridor using Eclipse SUMO.
          </p>
        </div>
        <div className="view-header-badges">
          <span className="provenance-badge badge-simulation">SIMULATION ONLY</span>
          <span className="provenance-badge badge-live">SUMO 1.18+ / TRACI</span>
        </div>
      </div>

      {/* Mandatory Advisory Notice Banner */}
      <div className="integrity-caveat-banner">
        <Info size={18} style={{ flexShrink: 0 }} />
        <div>
          <strong>Advisory Decision Support Notice (UI_UX_SPEC §12):</strong> All simulation models are mathematical approximations executed under calibrated baseline conditions. Outputs are strictly non-binding evidence and do not actuate physical traffic controllers or signals.
        </div>
      </div>

      {/* Main Grid: Controls + Comparative Results */}
      <div className="analytics-grid-two-col">
        {/* Left Column: Intervention Configuration Sandbox */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sliders size={18} color="#0F4C5C" />
              <span className="card-title">Intervention Configuration Sandbox</span>
            </div>
            <span className="text-muted" style={{ fontSize: '12px' }}>Predefined Safe Parameters</span>
          </div>

          {/* Template Selector */}
          <div className="control-group" style={{ marginBottom: '16px' }}>
            <label className="control-label">Approved Intervention Template</label>
            <select
              className="control-select"
              value={selectedTemplateId}
              onChange={(e) => setSelectedTemplateId(e.target.value)}
            >
              {templates.map(t => (
                <option key={t.id} value={t.id}>
                  {t.id}: {t.name}
                </option>
              ))}
            </select>
            {selectedTemplate && (
              <div className="template-desc" style={{ marginTop: '8px' }}>
                {selectedTemplate.description}
              </div>
            )}
          </div>

          {/* Slider 1: Green Time Extension */}
          <div className="control-group" style={{ marginBottom: '16px' }}>
            <div className="slider-label-row">
              <span className="control-label">Nagar Road EB Green Extension</span>
              <span className="slider-value font-mono">+{greenExtension}s (50s Green Split)</span>
            </div>
            <input
              type="range"
              min="5"
              max="25"
              step="1"
              value={greenExtension}
              onChange={(e) => setGreenExtension(Number(e.target.value))}
              className="control-slider"
            />
            <div className="slider-hints">
              <span>+5s (Conservative)</span>
              <span>+15s (Calibrated ADR-004)</span>
              <span>+25s (Aggressive)</span>
            </div>
          </div>

          {/* Slider 2: Demand Multiplier */}
          <div className="control-group" style={{ marginBottom: '16px' }}>
            <div className="slider-label-row">
              <span className="control-label">Peak Demand Multiplier</span>
              <span className="slider-value font-mono">{demandMultiplier.toFixed(2)}x ({(demandMultiplier * 2400).toFixed(0)} veh/hr)</span>
            </div>
            <input
              type="range"
              min="0.8"
              max="1.5"
              step="0.05"
              value={demandMultiplier}
              onChange={(e) => setDemandMultiplier(Number(e.target.value))}
              className="control-slider"
            />
            <div className="slider-hints">
              <span>0.80x (Off-Peak)</span>
              <span>1.00x (Evening Rush)</span>
              <span>1.50x (Severe Congestion)</span>
            </div>
          </div>

          {/* Number Input: Random Seed */}
          <div className="control-group" style={{ marginBottom: '20px' }}>
            <div className="slider-label-row">
              <span className="control-label">Random Seed (Reproducibility)</span>
              <span className="slider-value font-mono">Seed: {randomSeed}</span>
            </div>
            <input
              type="number"
              value={randomSeed}
              onChange={(e) => setRandomSeed(Number(e.target.value))}
              className="control-input"
            />
            <span className="control-caption" style={{ display: 'block', marginTop: '4px' }}>
              Identical seeds guarantee scientific pairwise comparability between baseline and intervention.
            </span>
          </div>

          {/* Run Button */}
          <button
            className="run-scenario-btn"
            onClick={handleRunSimulation}
            disabled={isRunning}
            style={{ width: '100%' }}
          >
            {isRunning ? (
              <>
                <span className="btn-spinner" />
                <span>Simulating Corridor Micro-flows...</span>
              </>
            ) : (
              <>
                <Play size={16} />
                <span>Execute Comparative SUMO Simulation</span>
              </>
            )}
          </button>

          {error && (
            <div className="run-error-box" style={{ marginTop: '12px' }}>
              <AlertTriangle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* Recent Runs History Subpanel */}
          {recentRuns.length > 0 && (
            <div style={{ marginTop: '24px', borderTop: '1px solid var(--color-border)', paddingTop: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
                <History size={15} className="text-muted" />
                <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                  Audit Trail of Recent Simulation Runs ({recentRuns.length})
                </span>
              </div>
              <div className="recent-runs-list" style={{ maxHeight: '140px', overflowY: 'auto' }}>
                {recentRuns.map((r, idx) => (
                  <div key={idx} className="recent-run-item">
                    <span className="mono-cell" style={{ fontSize: '12px' }}>{r.runId || `RUN-${idx + 1}`}</span>
                    <span className="provenance-badge badge-simulation" style={{ fontSize: '12px' }}>
                      {r.templateId || 'SCEN-INT-01'}
                    </span>
                    <span style={{ fontSize: '12px', color: '#10B981', fontWeight: 600 }}>
                      {r.deltas?.travel_time_saved_sec ? `-${r.deltas.travel_time_saved_sec}s delay` : 'Completed'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Comparative KPI Evaluation */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={18} color="#10B981" />
              <span className="card-title">Comparative KPI Evaluation (Baseline vs. Intervention)</span>
            </div>
            <span className="provenance-badge badge-simulation">SIMULATION RESULT</span>
          </div>

          {runResult ? (
            <div className="results-content">
              {/* Top Verdict Banner */}
              <div className="verdict-banner">
                <div>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                    EVALUATION VERDICT
                  </div>
                  <div style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'bold', color: '#0F4C5C' }}>
                    {runResult.deltas.overall_verdict.replace(/_/g, ' ')}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                    RANDOM SEED
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontWeight: '600' }}>
                    {runResult.randomSeed}
                  </div>
                </div>
              </div>

              {/* Side-by-Side KPI Cards Table */}
              <table className="kpi-compare-table">
                <thead>
                  <tr>
                    <th>Key Metric</th>
                    <th>Baseline (SCEN-BASE-01)</th>
                    <th>Intervention ({runResult.templateId})</th>
                    <th>Delta Impact</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Average Travel Time */}
                  <tr>
                    <td>
                      <div className="metric-row-name">Arterial Travel Time</div>
                      <div className="metric-row-sub">1.25 km Centerline Corridor</div>
                    </td>
                    <td className="mono-cell">
                      {runResult.baseline.kpis.average_travel_time_sec.toFixed(1)} s
                    </td>
                    <td className="mono-cell">
                      {runResult.intervention.kpis.average_travel_time_sec.toFixed(1)} s
                    </td>
                    <td>
                      <span className="delta-badge delta-positive">
                        <TrendingDown size={14} />
                        {runResult.deltas.travel_time_delta_pct}% ({runResult.deltas.travel_time_saved_sec}s saved)
                      </span>
                    </td>
                  </tr>

                  {/* Average Delay */}
                  <tr>
                    <td>
                      <div className="metric-row-name">Average Delay</div>
                      <div className="metric-row-sub">Per vehicle delay at junctions</div>
                    </td>
                    <td className="mono-cell">
                      {runResult.baseline.kpis.average_delay_sec.toFixed(1)} s
                    </td>
                    <td className="mono-cell">
                      {runResult.intervention.kpis.average_delay_sec.toFixed(1)} s
                    </td>
                    <td>
                      <span className="delta-badge delta-positive">
                        <TrendingDown size={14} />
                        {runResult.deltas.delay_delta_pct}% ({runResult.deltas.delay_saved_sec}s saved)
                      </span>
                    </td>
                  </tr>

                  {/* 95th Percentile Queue Length */}
                  <tr>
                    <td>
                      <div className="metric-row-name">p95 Queue Length</div>
                      <div className="metric-row-sub">Nagar Road EB Approach (SEG-NR-EB-01)</div>
                    </td>
                    <td className="mono-cell">
                      {runResult.baseline.kpis.p95_queue_length_meters.toFixed(1)} m
                    </td>
                    <td className="mono-cell">
                      {runResult.intervention.kpis.p95_queue_length_meters.toFixed(1)} m
                    </td>
                    <td>
                      <span className="delta-badge delta-positive">
                        <TrendingDown size={14} />
                        {runResult.deltas.queue_length_delta_pct}% ({runResult.deltas.queue_reduced_meters}m clear)
                      </span>
                    </td>
                  </tr>

                  {/* Corridor Throughput */}
                  <tr>
                    <td>
                      <div className="metric-row-name">Corridor Throughput</div>
                      <div className="metric-row-sub">Completed vehicles / hour</div>
                    </td>
                    <td className="mono-cell">
                      {runResult.baseline.kpis.throughput_veh_per_hour.toFixed(0)} vph
                    </td>
                    <td className="mono-cell">
                      {runResult.intervention.kpis.throughput_veh_per_hour.toFixed(0)} vph
                    </td>
                    <td>
                      <span className="delta-badge delta-positive">
                        <TrendingUp size={14} />
                        +{runResult.deltas.throughput_delta_pct}% (+{runResult.deltas.additional_throughput_vph} vph)
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>

              {/* Run Metadata Footer */}
              <div className="run-metadata-footer">
                <div>
                  <span className="text-muted">Run ID: </span>
                  <span style={{ fontFamily: 'var(--font-mono)' }}>{runResult.runId}</span>
                </div>
                <div>
                  <span className="text-muted">Executed At: </span>
                  <span style={{ fontFamily: 'var(--font-mono)' }}>
                    {new Date(runResult.executedAt).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-results-box" style={{ padding: '48px 24px' }}>
              <Cpu size={42} color="var(--color-text-secondary)" />
              <p style={{ marginTop: 'var(--space-3)', fontWeight: 600, fontSize: '15px' }}>
                Ready to Simulate Mobility Intervention
              </p>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', maxWidth: '380px', marginTop: 'var(--space-1)', lineHeight: 1.5 }}>
                Configure the green split extension and traffic volume multiplier on the left panel, then click <strong>Execute Comparative SUMO Simulation</strong>.
              </p>
            </div>
          )}

          <div className="analytics-notice-box" style={{ marginTop: '16px' }}>
            <HelpCircle size={14} className="text-muted" />
            <span>
              <strong>Scientific Notice:</strong> Simulated performance reflects microscopic car-following behavior within the specified Viman Nagar network model. Real-world commuter route diversion and driver non-compliance are not fully captured.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
