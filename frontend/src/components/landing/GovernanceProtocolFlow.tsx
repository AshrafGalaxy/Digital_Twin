import React, { useState } from 'react';
import {
  Activity,
  Database,
  Sliders,
  ShieldCheck,
  CheckCircle2,
  Lock,
  ArrowRight,
  Terminal,
  FileCheck,
  Check
} from 'lucide-react';

interface ProtocolStage {
  step: string;
  stageCode: string;
  title: string;
  subtitle: string;
  statusBadge: string;
  accentColor: string;
  icon: 'ingest' | 'quarantine' | 'conformal' | 'human';
  details: {
    code: string;
    text: string;
  }[];
  invariantGuarantee: string;
  auditLogSample: string;
}

const PROTOCOL_STAGES: ProtocolStage[] = [
  {
    step: '01',
    stageCode: 'INGEST',
    title: 'Edge Ingestion & Clamping',
    subtitle: 'Physical Sensor Validation',
    statusBadge: 'VERIFIED',
    accentColor: '#38BDF8',
    icon: 'ingest',
    details: [
      { code: 'CHK-01', text: 'Hard velocity bounds clamp speed strictly to 0-120 km/h limits.' },
      { code: 'CHK-02', text: 'Negative readings, null payloads, and future timestamps quarantined.' },
      { code: 'CHK-03', text: 'Observations exceeding 180s automatically flagged as STALE.' }
    ],
    invariantGuarantee: 'Corrupted edge telemetry never enters model inference pipelines.',
    auditLogSample: '[16:54:01.002] STAGE 01 PASS : 100% telemetry records verified within physical bounds [0, 120 km/h]'
  },
  {
    step: '02',
    stageCode: 'QUARANTINE',
    title: 'Tri-State Schema Quarantine',
    subtitle: 'Authoritative Storage Isolation',
    statusBadge: 'ISOLATED',
    accentColor: '#10B981',
    icon: 'quarantine',
    details: [
      { code: 'CHK-01', text: 'Observed telemetry stored strictly in live time-series tables.' },
      { code: 'CHK-02', text: 'SUMO microscopic simulations isolated in ephemeral run tables.' },
      { code: 'CHK-03', text: 'Machine learning forecasts partitioned into distinct schema tables.' }
    ],
    invariantGuarantee: 'Synthetic simulations and predictions NEVER overwrite physical ground truth.',
    auditLogSample: '[16:54:01.120] STAGE 02 PASS : Observed, simulation, and predicted states isolated in distinct schemas'
  },
  {
    step: '03',
    stageCode: 'CONFORMAL',
    title: 'Conformal Inference & XAI',
    subtitle: 'Uncertainty & Attribution',
    statusBadge: '90% CALIBRATED',
    accentColor: '#F59E0B',
    icon: 'conformal',
    details: [
      { code: 'CHK-01', text: 'Conformal bands calculate rigorous 80% and 90% confidence bounds.' },
      { code: 'CHK-02', text: 'Top-5 TreeSHAP feature attributions calculate exact feature weights.' },
      { code: 'CHK-03', text: 'Population Stability Index (PSI) flags distribution drift (>=0.25).' }
    ],
    invariantGuarantee: 'Zero point predictions without conformal uncertainty confidence intervals.',
    auditLogSample: '[16:54:01.240] STAGE 03 PASS : Forecast generated with 90% confidence band [14.2, 18.6 km/h], PSI=0.04 (STABLE)'
  },
  {
    step: '04',
    stageCode: 'CLEARANCE',
    title: 'Human-in-the-Loop Delivery',
    subtitle: 'Non-Actuation Protocol',
    statusBadge: 'ADVISORY',
    accentColor: '#818CF8',
    icon: 'human',
    details: [
      { code: 'CHK-01', text: 'Platform provides read-only decision support for municipal operators.' },
      { code: 'CHK-02', text: 'Zero autonomous signal controller or grid actuation capability.' },
      { code: 'CHK-03', text: 'Immutable operator authorization audit trail with credential logs.' }
    ],
    invariantGuarantee: 'Physical field action requires certified municipal authorization outside twin.',
    auditLogSample: '[16:54:01.350] STAGE 04 PASS : Operator advisory queued in TMC console; 0 autonomous actuations executed'
  }
];

export const GovernanceProtocolFlow: React.FC = () => {
  const [activeStageIdx, setActiveStageIdx] = useState<number>(0);

  const renderIcon = (type: ProtocolStage['icon'], color: string) => {
    switch (type) {
      case 'ingest':
        return <Activity size={18} color={color} strokeWidth={2.2} />;
      case 'quarantine':
        return <Database size={18} color={color} strokeWidth={2.2} />;
      case 'conformal':
        return <Sliders size={18} color={color} strokeWidth={2.2} />;
      case 'human':
        return <ShieldCheck size={18} color={color} strokeWidth={2.2} />;
    }
  };

  return (
    <section id="governance" className="landing-section governance-pipeline-section">
      <div className="section-header">
        <span className="section-eyebrow font-mono">Deterministic Integrity</span>
        <h2 className="section-title">The four-stage municipal decision delivery protocol</h2>
        <p className="section-subtitle">
          From edge sensor ingestion to certified operator clearance, our sequential architectural invariants eliminate synthetic contamination and prevent unvalidated autonomous actuation.
        </p>
      </div>

      {/* Sequential Pipeline Flow Board */}
      <div className="governance-pipeline-board">
        {/* Top Conduit Flow Navigator */}
        <div className="pipeline-conduit-track font-mono" role="tablist" aria-label="Governance Pipeline Sequence">
          {PROTOCOL_STAGES.map((stg, idx) => {
            const isSelected = activeStageIdx === idx;
            return (
              <React.Fragment key={stg.step}>
                <button
                  type="button"
                  role="tab"
                  aria-selected={isSelected}
                  className={`pipeline-conduit-node ${isSelected ? 'selected' : ''}`}
                  onClick={() => setActiveStageIdx(idx)}
                >
                  <span
                    className="conduit-node-bullet"
                    style={{
                      borderColor: isSelected ? stg.accentColor : 'rgba(255, 255, 255, 0.2)',
                      background: isSelected ? stg.accentColor : 'rgba(255, 255, 255, 0.05)'
                    }}
                  >
                    {isSelected ? <Check size={10} color="#000000" strokeWidth={3} /> : stg.step}
                  </span>
                  <div className="conduit-node-labels">
                    <span className="conduit-node-step" style={{ color: isSelected ? stg.accentColor : '#64748B' }}>
                      STAGE {stg.step}
                    </span>
                    <span className="conduit-node-name">{stg.stageCode}</span>
                  </div>
                </button>
                {idx < PROTOCOL_STAGES.length - 1 && (
                  <div className="pipeline-conduit-connector" aria-hidden="true">
                    <ArrowRight size={14} className="connector-arrow" />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* 4 Connected Sequential Stage Station Columns */}
        <div className="pipeline-stages-grid">
          {PROTOCOL_STAGES.map((stage, idx) => {
            const isSelected = activeStageIdx === idx;
            return (
              <div
                key={stage.step}
                className={`stage-station-column ${isSelected ? 'active-station' : ''}`}
                onClick={() => setActiveStageIdx(idx)}
              >
                {/* Stage Header */}
                <div className="station-top-meta">
                  <div className="station-index-group font-mono">
                    <span
                      className="station-step-num"
                      style={{
                        color: stage.accentColor,
                        background: `${stage.accentColor}18`,
                        borderColor: `${stage.accentColor}40`
                      }}
                    >
                      STAGE {stage.step}
                    </span>
                    <span className="station-stage-code">{stage.stageCode}</span>
                  </div>
                  <span
                    className="station-status-pill font-mono"
                    style={{
                      color: stage.accentColor,
                      borderColor: `${stage.accentColor}30`,
                      background: `${stage.accentColor}10`
                    }}
                  >
                    {stage.statusBadge}
                  </span>
                </div>

                {/* Station Title & Domain */}
                <div className="station-headline-wrap">
                  <div
                    className="station-icon-box"
                    style={{
                      background: `${stage.accentColor}15`,
                      borderColor: `${stage.accentColor}35`
                    }}
                  >
                    {renderIcon(stage.icon, stage.accentColor)}
                  </div>
                  <div className="station-headline-text">
                    <h3 className="station-title">{stage.title}</h3>
                    <span className="station-subtitle font-mono">{stage.subtitle}</span>
                  </div>
                </div>

                {/* Strict Engineering Checks List */}
                <div className="station-checks-wrap">
                  <span className="checks-label font-mono">STRICT OPERATING CHECKS</span>
                  <ul className="station-checks-list">
                    {stage.details.map((chk, cIdx) => (
                      <li key={cIdx} className="check-row">
                        <span className="check-code font-mono">{chk.code}</span>
                        <CheckCircle2 size={13} color={stage.accentColor} className="check-icon" />
                        <span className="check-text">{chk.text}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Station Invariant Contract Card */}
                <div className="station-contract-box">
                  <div className="contract-top-bar font-mono">
                    <Lock size={12} color="var(--color-success)" />
                    <span>ARCHITECTURAL INVARIANT</span>
                  </div>
                  <p className="contract-statement">{stage.invariantGuarantee}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Authoritative PostgreSQL Audit Ledger Feed (Bottom Terminal) */}
        <div className="pipeline-audit-terminal">
          <div className="audit-terminal-header font-mono">
            <div className="terminal-header-left">
              <Terminal size={14} color="var(--color-primary)" />
              <span className="terminal-title">AUTHORITATIVE POSTGRESQL / TIMESCALEDB INVARIANT LEDGER</span>
              <span className="terminal-live-badge">
                <span className="pulse-indicator" style={{ background: 'var(--color-success)' }} />
                <span>ACTIVE ENFORCEMENT</span>
              </span>
            </div>
            <div className="terminal-header-right">
              <FileCheck size={12} color="#64748B" />
              <span>SCHEMA TRIGGERS VERIFIED</span>
            </div>
          </div>

          <div className="audit-log-entries-list font-mono">
            {PROTOCOL_STAGES.map((stg, idx) => {
              const isHighlighted = activeStageIdx === idx;
              return (
                <div
                  key={stg.step}
                  className={`audit-log-row ${isHighlighted ? 'highlighted' : ''}`}
                  onClick={() => setActiveStageIdx(idx)}
                >
                  <span className="log-stage-tag" style={{ color: stg.accentColor }}>
                    [STAGE {stg.step}]
                  </span>
                  <span className="log-text">{stg.auditLogSample}</span>
                  <span className="log-status font-mono">ENFORCED</span>
                </div>
              );
            })}
          </div>

          <div className="audit-terminal-footer font-mono">
            <span>INVARIANT CONTRACT: All 4 stages must pass verification prior to human advisory presentation.</span>
            <span className="footer-system-note">POSTGRESQL SYSTEM OF RECORD : RESILIENT LOCAL SQLITE READY</span>
          </div>
        </div>
      </div>
    </section>
  );
};
