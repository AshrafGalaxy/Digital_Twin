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
  HelpCircle,
  Sparkles,
  RefreshCw,
  Check,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import { ScenarioTemplate, ScenarioRunResult } from '../../types/twin';
import {
  fetchScenarioTemplates,
  runScenario,
  fetchRecentScenarioRuns,
  proposeAdvisoryFromScenarioRun
} from '../../services/api';

export const ScenarioStudioView: React.FC = () => {
  const [templates, setTemplates] = useState<ScenarioTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('SCEN-INT-01');
  const [greenExtension, setGreenExtension] = useState<number>(15);
  const [coordinationOffset, setCoordinationOffset] = useState<number>(35);
  const [demandMultiplier, setDemandMultiplier] = useState<number>(1.0);
  const [randomSeed, setRandomSeed] = useState<number>(42);

  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [runResult, setRunResult] = useState<ScenarioRunResult | null>(null);
  const [recentRuns, setRecentRuns] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Advisory Proposal State
  const [showProposeModal, setShowProposeModal] = useState<boolean>(false);
  const [reviewerName, setReviewerName] = useState<string>('Municipal Traffic Cell Officer');
  const [proposalNotes, setProposalNotes] = useState<string>('');
  const [isSubmittingAdvisory, setIsSubmittingAdvisory] = useState<boolean>(false);
  const [advisorySuccess, setAdvisorySuccess] = useState<any | null>(null);

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
    setAdvisorySuccess(null);
    try {
      const result = await runScenario({
        templateId: selectedTemplateId,
        greenExtensionSec: greenExtension,
        coordinationOffsetSec: coordinationOffset,
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

  const handleProposeAdvisory = async () => {
    if (!runResult) return;
    setIsSubmittingAdvisory(true);
    try {
      const res = await proposeAdvisoryFromScenarioRun(
        runResult.runId,
        reviewerName,
        proposalNotes
      );
      setAdvisorySuccess(res);
      setShowProposeModal(false);
    } catch (err: any) {
      setError(err.message || 'Failed to submit advisory recommendation');
    } finally {
      setIsSubmittingAdvisory(false);
    }
  };

  const selectedTemplate = templates.find(t => t.id === selectedTemplateId);

  return (
    <div className="view-container scenario-studio-view">
      {/* View Header */}
      <div className="view-header">
        <div>
          <h1 className="view-title">Scenario Studio — Microscopic Simulation Sandbox</h1>
          <p className="view-subtitle">
            Controlled baseline vs. intervention simulation on Viman Nagar Chowk (VN-01) ↔ Somnath Nagar Chowk (SN-01) corridor using calibrated SUMO kinematics.
          </p>
        </div>
        <div className="view-header-badges">
          <span className="provenance-badge badge-simulation">SIMULATION ONLY</span>
          <span className="provenance-badge badge-live">SUMO / TRACI PHYSICS</span>
        </div>
      </div>

      {/* Mandatory Advisory Notice Banner */}
      <div className="integrity-caveat-banner">
        <Info size={18} style={{ flexShrink: 0, color: 'var(--color-primary)' }} />
        <div>
          <strong>Advisory Decision Support Notice:</strong> All simulation models are mathematical approximations executed under calibrated arterial conditions. Outputs are strictly non-binding evidence and do not actuate physical traffic controllers or signals.
        </div>
      </div>

      {/* Main Grid: Controls + Comparative Results */}
      <div className="analytics-grid-two-col">
        {/* Left Column: Intervention Configuration Sandbox */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sliders size={18} color="var(--color-primary)" />
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
              onChange={(e) => {
                setSelectedTemplateId(e.target.value);
                setRunResult(null);
                setAdvisorySuccess(null);
              }}
            >
              {templates.map(t => (
                <option key={t.id} value={t.id}>
                  {t.id}: {t.name}
                </option>
              ))}
            </select>
            {selectedTemplate && (
              <div className="template-desc" style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                {selectedTemplate.description}
              </div>
            )}
          </div>

          {/* Dynamic Control depending on template */}
          {selectedTemplateId === 'SCEN-INT-01' ? (
            <div className="control-group" style={{ marginBottom: '16px' }}>
              <div className="slider-label-row">
                <span className="control-label">Nagar Road EB Green Extension</span>
                <span className="slider-value font-mono">+{greenExtension}s ({35 + greenExtension}s Green Split)</span>
              </div>
              <input
                type="range"
                min="5"
                max="25"
                step="1"
                value={greenExtension}
                onChange={(e) => setGreenExtension(Number(e.target.value))}
                className="control-slider"
                style={{
                  background: `linear-gradient(to right, #2F81F7 0%, #2F81F7 ${((greenExtension - 5) / 20) * 100}%, rgba(255, 255, 255, 0.12) ${((greenExtension - 5) / 20) * 100}%, rgba(255, 255, 255, 0.12) 100%)`
                }}
                aria-label="Nagar Road EB Green Extension"
              />
              <div className="preset-pills-row">
                <button
                  type="button"
                  className={`preset-pill-btn ${greenExtension === 5 ? 'active' : ''}`}
                  onClick={() => setGreenExtension(5)}
                >
                  +5s Conservative
                </button>
                <button
                  type="button"
                  className={`preset-pill-btn ${greenExtension === 15 ? 'active' : ''}`}
                  onClick={() => setGreenExtension(15)}
                >
                  +15s Calibrated
                </button>
                <button
                  type="button"
                  className={`preset-pill-btn ${greenExtension === 25 ? 'active' : ''}`}
                  onClick={() => setGreenExtension(25)}
                >
                  +25s Aggressive
                </button>
              </div>
            </div>
          ) : (
            <div className="control-group" style={{ marginBottom: '16px' }}>
              <div className="slider-label-row">
                <span className="control-label">Arterial Progression Offset (VN-01 ↔ SN-01)</span>
                <span className="slider-value font-mono">{coordinationOffset}s Offset</span>
              </div>
              <input
                type="range"
                min="10"
                max="60"
                step="1"
                value={coordinationOffset}
                onChange={(e) => setCoordinationOffset(Number(e.target.value))}
                className="control-slider"
                style={{
                  background: `linear-gradient(to right, #2F81F7 0%, #2F81F7 ${((coordinationOffset - 10) / 50) * 100}%, rgba(255, 255, 255, 0.12) ${((coordinationOffset - 10) / 50) * 100}%, rgba(255, 255, 255, 0.12) 100%)`
                }}
                aria-label="Arterial Progression Offset"
              />
              <div className="preset-pills-row">
                <button
                  type="button"
                  className={`preset-pill-btn ${coordinationOffset === 25 ? 'active' : ''}`}
                  onClick={() => setCoordinationOffset(25)}
                >
                  25s Tight
                </button>
                <button
                  type="button"
                  className={`preset-pill-btn ${coordinationOffset === 35 ? 'active' : ''}`}
                  onClick={() => setCoordinationOffset(35)}
                >
                  35s Optimal Wave
                </button>
                <button
                  type="button"
                  className={`preset-pill-btn ${coordinationOffset === 50 ? 'active' : ''}`}
                  onClick={() => setCoordinationOffset(50)}
                >
                  50s Wide
                </button>
              </div>
            </div>
          )}

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
              style={{
                background: `linear-gradient(to right, #2F81F7 0%, #2F81F7 ${((demandMultiplier - 0.8) / 0.7) * 100}%, rgba(255, 255, 255, 0.12) ${((demandMultiplier - 0.8) / 0.7) * 100}%, rgba(255, 255, 255, 0.12) 100%)`
              }}
              aria-label="Peak Demand Multiplier"
            />
            <div className="preset-pills-row">
              <button
                type="button"
                className={`preset-pill-btn ${demandMultiplier === 0.8 ? 'active' : ''}`}
                onClick={() => setDemandMultiplier(0.8)}
              >
                0.80x Off-Peak
              </button>
              <button
                type="button"
                className={`preset-pill-btn ${demandMultiplier === 1.0 ? 'active' : ''}`}
                onClick={() => setDemandMultiplier(1.0)}
              >
                1.00x Evening Peak
              </button>
              <button
                type="button"
                className={`preset-pill-btn ${demandMultiplier === 1.3 ? 'active' : ''}`}
                onClick={() => setDemandMultiplier(1.3)}
              >
                1.30x Severe Surge
              </button>
            </div>
          </div>

          {/* Random Seed */}
          <div className="control-group" style={{ marginBottom: '20px' }}>
            <div className="slider-label-row">
              <span className="control-label">Random Seed (Pairwise Reproducibility)</span>
              <span className="slider-value font-mono">Seed: {randomSeed}</span>
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="number"
                value={randomSeed}
                onChange={(e) => setRandomSeed(Number(e.target.value))}
                className="control-input"
                style={{ flex: 1 }}
              />
              <button
                type="button"
                className="preset-pill-btn"
                style={{ padding: '0 12px', display: 'flex', alignItems: 'center', gap: '4px' }}
                onClick={() => setRandomSeed(Math.floor(Math.random() * 900) + 100)}
                title="Randomize Seed"
              >
                <RefreshCw size={13} />
                <span>Random</span>
              </button>
            </div>
            <span className="control-caption" style={{ display: 'block', marginTop: '6px' }}>
              Identical seeds ensure pairwise mathematical comparability between baseline and intervention.
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
            <div style={{ marginTop: '24px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '10px' }}>
                <History size={14} className="text-muted" />
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-muted)' }}>
                  Audit Trail of Recent Runs ({recentRuns.length})
                </span>
              </div>
              <div className="recent-runs-list" style={{ maxHeight: '140px', overflowY: 'auto' }}>
                {recentRuns.map((r, idx) => (
                  <div key={idx} className="recent-run-item" style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.04)', fontSize: '12px' }}>
                    <span className="mono-cell" style={{ fontSize: '11px' }}>{r.runId ? r.runId.split(':').pop() : `RUN-${idx + 1}`}</span>
                    <span className="provenance-badge badge-simulation" style={{ fontSize: '10px' }}>
                      {r.templateId || 'SCEN-INT-01'}
                    </span>
                    <span style={{ fontSize: '11px', color: '#34D399', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      {r.deltas?.delay_saved_sec ? `-${r.deltas.delay_saved_sec}s delay` : 'Completed'}
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
              <span className="card-title">Comparative KPI Evaluation</span>
            </div>
            <span className="provenance-badge badge-simulation">SIMULATION RESULT</span>
          </div>

          {runResult ? (
            <div className="results-content">
              {/* Top Verdict Banner */}
              <div className="verdict-banner">
                <div>
                  <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                    EVALUATION VERDICT
                  </div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-primary)', marginTop: '2px' }}>
                    {runResult.deltas.overall_verdict.replace(/_/g, ' ')}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                    SEED / NETWORK
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '13px', color: 'var(--text-main)', marginTop: '2px' }}>
                    {runResult.randomSeed} • v1.0
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
                      <div className="metric-row-sub">1.25 km Nagar Road EB Corridor</div>
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
                      <div className="metric-row-sub">Per vehicle stopping delay at junctions</div>
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
                      <div className="metric-row-sub">Discharged vehicles / hour</div>
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

              {/* Advisory Proposal Flow */}
              <div style={{ marginTop: '20px' }}>
                {advisorySuccess ? (
                  <div className="advisory-success-banner">
                    <Check size={18} color="#34D399" style={{ flexShrink: 0 }} />
                    <div style={{ flex: 1 }}>
                      <strong>Intervention Advisory Registered: </strong>
                      <span style={{ fontFamily: 'var(--font-mono)' }}>{advisorySuccess.recommendationId}</span>
                      <p style={{ margin: '4px 0 0 0', fontSize: '11px', color: 'var(--text-secondary)' }}>
                        Logged to audit trail. Queued in Advisory Center for municipal officer authorization. Zero external actuation performed.
                      </p>
                    </div>
                  </div>
                ) : !showProposeModal ? (
                  <button
                    type="button"
                    className="propose-advisory-btn"
                    style={{ width: '100%' }}
                    onClick={() => setShowProposeModal(true)}
                  >
                    <Sparkles size={15} />
                    <span>Propose Advisory Intervention from this Simulation</span>
                    <ArrowRight size={14} />
                  </button>
                ) : (
                  <div style={{
                    background: 'rgba(47, 129, 247, 0.08)',
                    border: '1px solid rgba(47, 129, 247, 0.3)',
                    borderRadius: 'var(--radius-md)',
                    padding: '16px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                      <ShieldAlert size={18} color="#2F81F7" />
                      <span style={{ fontSize: '13px', fontWeight: 700, color: '#58A6FF' }}>
                        Propose Operational Intervention to Municipal Advisory Center
                      </span>
                    </div>

                    <div style={{ marginBottom: '12px' }}>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                        Authorized Reviewer Name / Identity
                      </label>
                      <input
                        type="text"
                        className="control-input"
                        value={reviewerName}
                        onChange={(e) => setReviewerName(e.target.value)}
                        placeholder="e.g. Traffic Cell Officer"
                        style={{ width: '100%', fontSize: '12px' }}
                      />
                    </div>

                    <div style={{ marginBottom: '12px' }}>
                      <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
                        Operational Justification Notes
                      </label>
                      <textarea
                        className="control-input"
                        value={proposalNotes}
                        onChange={(e) => setProposalNotes(e.target.value)}
                        placeholder="e.g. Validated against 18:30 queue spillback telemetry. Delay reduction confirmed."
                        rows={2}
                        style={{ width: '100%', fontSize: '12px', resize: 'vertical' }}
                      />
                    </div>

                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '14px', lineHeight: 1.4 }}>
                      <strong>Strict Non-Actuation Invariant:</strong> Platform recommendations are advisory decision-support only. Physical traffic controllers are not actuated.
                    </div>

                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        type="button"
                        className="run-scenario-btn"
                        style={{ flex: 1, padding: '8px 14px', fontSize: '12px', background: 'var(--color-primary)', color: '#FFFFFF' }}
                        onClick={handleProposeAdvisory}
                        disabled={isSubmittingAdvisory}
                      >
                        {isSubmittingAdvisory ? 'Submitting Advisory...' : 'Submit to Advisory Center'}
                      </button>
                      <button
                        type="button"
                        className="preset-pill-btn"
                        style={{ padding: '8px 14px', borderRadius: 'var(--radius-md)' }}
                        onClick={() => setShowProposeModal(false)}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>

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
              <Cpu size={42} color="var(--text-muted)" />
              <p style={{ marginTop: 'var(--space-3)', fontWeight: 600, fontSize: '15px' }}>
                Ready to Simulate Mobility Intervention
              </p>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)', maxWidth: '380px', marginTop: 'var(--space-1)', lineHeight: 1.5 }}>
                Configure parameters on the left panel, then click <strong>Execute Comparative SUMO Simulation</strong>.
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
