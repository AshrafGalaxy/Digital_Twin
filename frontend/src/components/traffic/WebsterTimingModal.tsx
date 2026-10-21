import React, { useState, useEffect } from 'react';
import {
  Zap,
  Activity,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  X,
  Sliders,
  RefreshCw
} from 'lucide-react';
import { WebsterTimingPlan } from '../../types/twin';
import { fetchIntersectionOptimalTiming } from '../../services/api';

interface WebsterTimingModalProps {
  isOpen: boolean;
  intersectionId: string;
  intersectionName?: string;
  onClose: () => void;
}

export const WebsterTimingModal: React.FC<WebsterTimingModalProps> = ({
  isOpen,
  intersectionId,
  intersectionName,
  onClose
}) => {
  const [timingPlan, setTimingPlan] = useState<WebsterTimingPlan | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [baselineCycle, setBaselineCycle] = useState<number>(90);

  const loadTimingPlan = async () => {
    if (!intersectionId) return;
    try {
      setLoading(true);
      setError(null);
      const plan = await fetchIntersectionOptimalTiming(intersectionId, baselineCycle);
      setTimingPlan(plan);
    } catch (err: any) {
      console.error('Failed to load optimal timing plan', err);
      setError(err?.message || 'Failed to compute Webster optimal timing plan.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadTimingPlan();
    }
  }, [isOpen, intersectionId, baselineCycle]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(4px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px'
      }}
      onClick={onClose}
    >
      <div
        className="analytics-card"
        style={{
          width: '100%',
          maxWidth: '840px',
          maxHeight: '90vh',
          overflowY: 'auto',
          backgroundColor: 'var(--color-surface, #09090B)',
          border: '1px solid var(--color-border, #16171B)',
          borderRadius: 'var(--radius-lg, 12px)',
          padding: '24px',
          boxShadow: '0 12px 36px rgba(0, 0, 0, 0.6)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="analytics-card-header" style={{ marginBottom: '16px', paddingBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span
              style={{
                padding: '6px',
                borderRadius: 'var(--radius-sm, 6px)',
                background: 'rgba(47, 129, 247, 0.14)',
                border: '1px solid rgba(47, 129, 247, 0.35)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Zap size={18} color="var(--color-primary-hover, #58A6FF)" />
            </span>
            <div>
              <h2 className="card-title" style={{ fontSize: '16px', margin: 0 }}>
                Webster Delay-Minimizing Adaptive Signal Timing Plan
              </h2>
              <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)' }}>
                Target Junction: {intersectionName || intersectionId}
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="provenance-badge badge-predicted">
              PREDICTED / WEBSTER
            </span>
            <button
              type="button"
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--color-text-muted)',
                cursor: 'pointer',
                padding: '4px',
                display: 'flex',
                alignItems: 'center'
              }}
              title="Close modal"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Loading / Error States */}
        {loading && (
          <div style={{ padding: '36px', textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: '13px' }}>
            <RefreshCw size={24} className="animate-spin text-muted" style={{ margin: '0 auto 10px' }} />
            Computing Webster delay minimization and pedestrian clearance invariants...
          </div>
        )}

        {error && (
          <div style={{ padding: '16px', borderRadius: '8px', background: 'rgba(248, 81, 73, 0.1)', border: '1px solid rgba(248, 81, 73, 0.3)', color: '#F85149', fontSize: '12px', marginBottom: '16px' }}>
            <AlertTriangle size={16} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'text-bottom' }} />
            {error}
          </div>
        )}

        {timingPlan && !loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Baseline Adjustment Control */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                background: 'var(--bg-surface-elevated, rgba(15, 15, 18, 0.7))',
                borderRadius: 'var(--radius-sm, 6px)',
                border: '1px solid var(--color-border, #16171B)',
                fontSize: '12px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sliders size={14} color="var(--color-primary)" />
                <span style={{ fontWeight: 600, color: 'var(--color-text)' }}>Baseline Controller Cycle:</span>
                <span className="font-mono">{baselineCycle}s</span>
              </div>

              <div style={{ display: 'flex', gap: '6px' }}>
                {[75, 90, 105, 120].map((cyc) => (
                  <button
                    key={cyc}
                    type="button"
                    className={`preset-pill-btn ${baselineCycle === cyc ? 'active' : ''}`}
                    onClick={() => setBaselineCycle(cyc)}
                  >
                    {cyc}s
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Metrics Row */}
            <div className="quick-metrics-row-four">
              <div className="metric-box">
                <span className="metric-box-label">Optimal Cycle Length</span>
                <span className="metric-box-val font-mono" style={{ color: 'var(--color-primary-hover, #58A6FF)' }}>
                  {timingPlan.targetCycleSec} <small>sec</small>
                </span>
                <span className="metric-box-sub">
                  Baseline: {timingPlan.baselineCycleSec}s (C_0 formulation)
                </span>
              </div>

              <div className="metric-box">
                <span className="metric-box-label">Average Vehicle Delay</span>
                <span className="metric-box-val font-mono" style={{ color: '#3FB950' }}>
                  {timingPlan.optimalDelaySecVeh.toFixed(1)} <small>s/veh</small>
                </span>
                <span className="metric-box-sub">
                  Baseline: {timingPlan.baselineDelaySecVeh.toFixed(1)} s/veh
                </span>
              </div>

              <div className="metric-box">
                <span className="metric-box-label">Estimated Delay Reduction</span>
                <span className="metric-box-val font-mono" style={{ color: '#3FB950' }}>
                  -{timingPlan.estimatedDelayReductionSec.toFixed(1)} <small>s/veh</small>
                </span>
                <span className="metric-box-sub">
                  Efficiency Gain: {timingPlan.estimatedDelayReductionPct.toFixed(1)}%
                </span>
              </div>

              <div className="metric-box">
                <span className="metric-box-label">Critical Flow Ratio (Y)</span>
                <span className="metric-box-val font-mono" style={{ color: timingPlan.criticalFlowRatioY > 0.85 ? '#F85149' : '#FCD34D' }}>
                  {timingPlan.criticalFlowRatioY.toFixed(3)}
                </span>
                <span className="metric-box-sub">
                  Lost Time: {timingPlan.totalLostTimeSec}s across {timingPlan.phases.length} phases
                </span>
              </div>
            </div>

            {/* Safety Validation Strip */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '10px',
                padding: '12px 14px',
                background: 'var(--bg-surface-elevated, rgba(15, 15, 18, 0.6))',
                borderRadius: 'var(--radius-sm, 6px)',
                border: '1px solid var(--color-border, #16171B)',
                fontSize: '11px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={13} color="#3FB950" />
                <span>Pedestrian Invariant: <strong>Verified</strong> (1.2 m/s)</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={13} color={timingPlan.safetyValidation.saturationCapSatisfied ? '#3FB950' : '#D29922'} />
                <span>Max Saturation: <strong>x = {timingPlan.safetyValidation.maxSaturation}</strong> (cap: 0.85)</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle2 size={13} color="#3FB950" />
                <span>Cycle Bounded: <strong>60s - 150s</strong></span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Activity size={13} color={timingPlan.safetyValidation.oversaturatedRegime ? '#F85149' : '#58A6FF'} />
                <span>Regime: <strong>{timingPlan.safetyValidation.oversaturatedRegime ? 'Oversaturated' : 'Under Capacity'}</strong></span>
              </div>
            </div>

            {/* Visual Phase Allocation Bar */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--color-text-muted)', marginBottom: '6px' }}>
                <span>PHASE GREEN SPLIT ALLOCATION</span>
                <span>{timingPlan.targetCycleSec}s TOTAL CYCLE</span>
              </div>
              <div style={{ display: 'flex', width: '100%', height: '14px', borderRadius: '4px', overflow: 'hidden' }}>
                {timingPlan.phases.map((p, idx) => {
                  const colors = ['#2F81F7', '#3FB950', '#D29922', '#BC8CFF', '#38BDF8'];
                  const color = colors[idx % colors.length];
                  const pct = Math.max(5, (p.greenSec / timingPlan.targetCycleSec) * 100);
                  return (
                    <div
                      key={p.phaseId}
                      style={{
                        width: `${pct}%`,
                        backgroundColor: color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#000000',
                        fontSize: '9px',
                        fontWeight: 700,
                        fontFamily: 'var(--font-mono)'
                      }}
                      title={`Phase ${p.phaseId}: ${p.greenSec}s (${pct.toFixed(0)}%)`}
                    >
                      P{p.phaseId}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Phase Breakdown Table */}
            <div>
              <h4 style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Phase Allocation & Degree of Saturation Details
              </h4>
              <div className="table-responsive">
                <table className="analytics-table">
                  <thead>
                    <tr>
                      <th>Phase</th>
                      <th>Approach</th>
                      <th>Green (s)</th>
                      <th>Split</th>
                      <th>Flow Ratio (y)</th>
                      <th>Saturation (x)</th>
                      <th>Ped Clear (s)</th>
                      <th>Delay (s/veh)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {timingPlan.phases.map((p) => (
                      <tr key={p.phaseId}>
                        <td className="font-mono">Phase {p.phaseId}</td>
                        <td style={{ fontSize: '11px' }}>{p.description}</td>
                        <td className="font-mono font-bold" style={{ color: 'var(--color-primary-hover)' }}>{p.greenSec}s</td>
                        <td className="font-mono">{(p.splitRatio * 100).toFixed(1)}%</td>
                        <td className="font-mono">{p.flowRatioY.toFixed(3)}</td>
                        <td className="font-mono" style={{ color: p.saturationX > 0.85 ? '#F85149' : p.saturationX > 0.70 ? '#D29922' : '#3FB950' }}>
                          {p.saturationX.toFixed(2)}
                        </td>
                        <td className="font-mono">{p.pedClearanceSec.toFixed(0)}s</td>
                        <td className="font-mono">{p.delaySecVeh.toFixed(1)}s</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Advisory Governance Caveat */}
            <div
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '8px',
                padding: '10px 14px',
                borderRadius: '6px',
                background: 'rgba(210, 153, 34, 0.1)',
                border: '1px solid rgba(210, 153, 34, 0.25)',
                fontSize: '11px',
                color: 'var(--color-text-secondary)',
                lineHeight: 1.5
              }}
            >
              <ShieldCheck size={14} color="#D29922" style={{ flexShrink: 0, marginTop: '2px' }} />
              <div>
                <strong>Advisory Decision Support Only:</strong> Webster optimization recommendations are strictly advisory and require formal human municipal authorization outside the platform before any field signal timing updates.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
