import React, { useState, useEffect } from 'react';
import {
  Sliders,
  Play,
  CheckCircle2,
  AlertTriangle,
  TrendingDown,
  TrendingUp,
  X,
  Cpu,
  Info
} from 'lucide-react';
import { ScenarioTemplate, ScenarioRunResult } from '../types/twin';
import { fetchScenarioTemplates, runScenario } from '../services/api';

interface ScenarioStudioProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ScenarioStudio: React.FC<ScenarioStudioProps> = ({ isOpen, onClose }) => {
  const [templates, setTemplates] = useState<ScenarioTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('SCEN-INT-01');
  const [greenExtension, setGreenExtension] = useState<number>(15);
  const [demandMultiplier, setDemandMultiplier] = useState<number>(1.0);
  const [randomSeed, setRandomSeed] = useState<number>(42);

  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [runResult, setRunResult] = useState<ScenarioRunResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchScenarioTemplates()
        .then(setTemplates)
        .catch(err => console.error('Failed loading templates', err));
    }
  }, [isOpen]);

  if (!isOpen) return null;

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
    } catch (err: any) {
      setError(err.message || 'Failed to complete simulation run');
    } finally {
      setIsRunning(false);
    }
  };

  const selectedTemplate = templates.find(t => t.id === selectedTemplateId);

  return (
    <div className="scenario-modal-backdrop">
      <div className="scenario-modal-container">
        {/* Header */}
        <div className="scenario-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <div className="scenario-icon-badge">
              <Cpu size={20} color="#0F4C5C" />
            </div>
            <div>
              <h2 className="scenario-title">Scenario Studio — Microscopic Traffic Simulation</h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginTop: 'var(--space-1)' }}>
                <span className="provenance-badge badge-simulation">SIMULATION</span>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                  Corridor: Viman Nagar Chowk (VN-01) ↔ Somnath Nagar Chowk (SN-01)
                </span>
              </div>
            </div>
          </div>
          <button className="close-btn" onClick={onClose} aria-label="Close Scenario Studio">
            <X size={20} />
          </button>
        </div>

        {/* Advisory Governance Banner */}
        <div className="scenario-advisory-banner">
          <Info size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <strong>Advisory Decision Support Notice:</strong> All simulation models are mathematical approximations executed under calibrated baseline conditions. Outputs are strictly non-binding and do not actuate physical traffic infrastructure.
          </div>
        </div>

        <div className="scenario-body-grid">
          {/* Left Column: Configuration Controls */}
          <div className="scenario-controls-panel">
            <div className="panel-title">
              <Sliders size={16} />
              <span>Intervention Configuration</span>
            </div>

            {/* Template Selector */}
            <div className="control-group">
              <label className="control-label">Approved Scenario Template</label>
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
                <div className="template-desc">
                  {selectedTemplate.description}
                </div>
              )}
            </div>

            {/* Slider 1: Green Time Extension */}
            <div className="control-group">
              <div className="slider-label-row">
                <span className="control-label">Nagar Road EB Green Extension</span>
                <span className="slider-value">+{greenExtension}s (50s Green)</span>
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
                <span>+5s (Moderate)</span>
                <span>+15s (ADR-004 Target)</span>
                <span>+25s (High)</span>
              </div>
            </div>

            {/* Slider 2: Demand Multiplier */}
            <div className="control-group">
              <div className="slider-label-row">
                <span className="control-label">Peak Demand Multiplier</span>
                <span className="slider-value">{demandMultiplier.toFixed(2)}x ({(demandMultiplier * 2400).toFixed(0)} veh/hr)</span>
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
            <div className="control-group">
              <div className="slider-label-row">
                <span className="control-label">Random Seed (Reproducibility)</span>
                <span className="slider-value">Seed: {randomSeed}</span>
              </div>
              <input
                type="number"
                value={randomSeed}
                onChange={(e) => setRandomSeed(Number(e.target.value))}
                className="control-input"
              />
              <span className="control-caption">
                Identical seeds guarantee scientific comparability between runs.
              </span>
            </div>

            {/* Run Button */}
            <button
              className="run-scenario-btn"
              onClick={handleRunSimulation}
              disabled={isRunning}
            >
              {isRunning ? (
                <>
                  <span className="btn-spinner" />
                  <span>Simulating Corridor Micro-flows...</span>
                </>
              ) : (
                <>
                  <Play size={16} />
                  <span>Execute Comparative Simulation</span>
                </>
              )}
            </button>

            {error && (
              <div className="run-error-box">
                <AlertTriangle size={16} />
                <span>{error}</span>
              </div>
            )}
          </div>

          {/* Right Column: Comparative KPI Results */}
          <div className="scenario-results-panel">
            <div className="panel-title">
              <CheckCircle2 size={16} />
              <span>Comparative KPI Evaluation (Baseline vs. Intervention)</span>
            </div>

            {runResult ? (
              <div className="results-content">
                {/* Top Verdict Card */}
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
                    <span style={{ fontFamily: 'var(--font-mono)' }}>{new Date(runResult.executedAt).toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="empty-results-box">
                <Cpu size={36} color="var(--color-text-secondary)" />
                <p style={{ marginTop: 'var(--space-3)', fontWeight: 500 }}>
                  Ready to Simulate Mobility Intervention
                </p>
                <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', maxWidth: '340px', marginTop: 'var(--space-1)' }}>
                  Configure green split adjustment and demand parameters on the left, then click <strong>Execute Comparative Simulation</strong> to run the model.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
