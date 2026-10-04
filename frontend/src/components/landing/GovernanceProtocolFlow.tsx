import React, { useState } from 'react';
import {
  ShieldCheck,
  Database,
  Lock,
  Sliders,
  CheckCircle2,
  FileCheck,
  Layers,
  Activity
} from 'lucide-react';

interface ProtocolStage {
  step: string;
  title: string;
  subtitle: string;
  badge: string;
  accentColor: string;
  icon: 'ingest' | 'quarantine' | 'conformal' | 'human';
  details: string[];
  invariantGuarantee: string;
}

const PROTOCOL_STAGES: ProtocolStage[] = [
  {
    step: '01',
    title: 'Sensor Ingestion & Bound Clamping',
    subtitle: 'Edge Telemetry Validation',
    badge: '1 Hz STREAM',
    accentColor: '#38BDF8',
    icon: 'ingest',
    details: [
      'Physical speed bounds enforce hard 0 to 120 km/h limits.',
      'Future timestamps and negative values automatically quarantined.',
      'Observations exceeding 180s automatically flagged as STALE.'
    ],
    invariantGuarantee: 'Guarantees corrupted edge telemetry never pollutes downstream models.'
  },
  {
    step: '02',
    title: 'Tri-State Schema Quarantine',
    subtitle: 'Authoritative Storage Isolation',
    badge: 'POSTGRESQL',
    accentColor: '#10B981',
    icon: 'quarantine',
    details: [
      'Observed telemetry stored strictly in live time-series tables.',
      'Microscopic SUMO simulations isolated in ephemeral scenario runs.',
      'Machine learning predictions stored in separate schema tables.'
    ],
    invariantGuarantee: 'Synthetic simulations and predictions NEVER overwrite physical ground truth.'
  },
  {
    step: '03',
    title: 'Conformal Inference & XAI',
    subtitle: 'Uncertainty & Explainability',
    badge: 'CONFORMAL 90%',
    accentColor: '#F59E0B',
    icon: 'conformal',
    details: [
      'Every prediction provides calibrated 80% and 90% confidence intervals.',
      'Top-5 TreeSHAP feature attributions calculate exact feature influence.',
      'Population Stability Index (PSI) monitors training distribution drift.'
    ],
    invariantGuarantee: 'Every forecast provides verifiable mathematical confidence boundaries.'
  },
  {
    step: '04',
    title: 'Human-in-the-Loop Advisory Delivery',
    subtitle: 'Non-Actuation Governance',
    badge: 'READ-ONLY CONTRACT',
    accentColor: '#818CF8',
    icon: 'human',
    details: [
      'Advisories are purely recommendations for municipal traffic engineers.',
      'Platform provides zero autonomous signal controller actuation.',
      'Complete operator audit trail logged with timestamp and user credential.'
    ],
    invariantGuarantee: 'All physical field changes require certified municipal human authorization.'
  }
];

export const GovernanceProtocolFlow: React.FC = () => {
  const [activeStep, setActiveStep] = useState<number>(0);

  const renderIcon = (type: ProtocolStage['icon'], color: string) => {
    switch (type) {
      case 'ingest':
        return <Activity size={18} color={color} />;
      case 'quarantine':
        return <Database size={18} color={color} />;
      case 'conformal':
        return <Sliders size={18} color={color} />;
      case 'human':
        return <ShieldCheck size={18} color={color} />;
      default:
        return <Layers size={18} color={color} />;
    }
  };

  return (
    <section id="governance" className="landing-section governance-protocol-section">
      <div className="section-header">
        <span className="section-eyebrow font-mono">Deterministic Integrity</span>
        <h2 className="section-title">The four-stage municipal decision delivery protocol</h2>
        <p className="section-subtitle">
          From edge sensor ingestion to certified operator review, explore how our architectural invariants prevent unvalidated autonomous actuation.
        </p>
      </div>

      {/* Protocol Stage Selector Grid */}
      <div className="protocol-nav-grid" role="tablist" aria-label="Governance Protocol Stages">
        {PROTOCOL_STAGES.map((stage, idx) => {
          const isActive = idx === activeStep;
          return (
            <button
              key={stage.step}
              role="tab"
              aria-selected={isActive}
              className={`protocol-nav-card ${isActive ? 'active' : ''}`}
              onClick={() => setActiveStep(idx)}
            >
              <div className="nav-card-inner">
                <div
                  className="nav-card-icon-badge"
                  style={{
                    color: isActive ? stage.accentColor : '#94A3B8',
                    background: isActive ? `${stage.accentColor}18` : 'rgba(255, 255, 255, 0.03)',
                    borderColor: isActive ? `${stage.accentColor}45` : 'rgba(255, 255, 255, 0.08)'
                  }}
                >
                  {renderIcon(stage.icon, isActive ? stage.accentColor : '#94A3B8')}
                </div>
                <div className="nav-card-text">
                  <div className="nav-card-top-row">
                    <span
                      className="nav-card-id font-mono"
                      style={{ color: isActive ? stage.accentColor : '#64748B' }}
                    >
                      STAGE {stage.step}
                    </span>
                    <span className="nav-card-category font-mono">
                      {stage.badge}
                    </span>
                  </div>
                  <span className="nav-card-title">{stage.title}</span>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Stage Detailed Spotlight */}
      <div className="protocol-spotlight-card">
        <div className="spotlight-topbar">
          <div className="spotlight-title-group">
            <div
              className="spotlight-icon-box"
              style={{
                background: `${PROTOCOL_STAGES[activeStep].accentColor}18`,
                borderColor: `${PROTOCOL_STAGES[activeStep].accentColor}40`
              }}
            >
              {renderIcon(PROTOCOL_STAGES[activeStep].icon, PROTOCOL_STAGES[activeStep].accentColor)}
            </div>
            <div>
              <span className="spotlight-step-tag font-mono" style={{ color: PROTOCOL_STAGES[activeStep].accentColor }}>
                STAGE {PROTOCOL_STAGES[activeStep].step} PROTOCOL SPECIFICATION
              </span>
              <h3 className="spotlight-heading">{PROTOCOL_STAGES[activeStep].title}</h3>
            </div>
          </div>
          <div className="spec-meta-row font-mono">
            <span
              className="spec-category-badge"
              style={{
                color: PROTOCOL_STAGES[activeStep].accentColor,
                borderColor: `${PROTOCOL_STAGES[activeStep].accentColor}40`,
                background: `${PROTOCOL_STAGES[activeStep].accentColor}15`
              }}
            >
              {PROTOCOL_STAGES[activeStep].badge}
            </span>
            <span className="spec-online-indicator font-mono">
              <span className="pulse-indicator" style={{ background: 'var(--color-success)' }} />
              <span>INVARIANT ENFORCED</span>
            </span>
          </div>
        </div>

        <div className="spotlight-grid">
          {/* Rules & Validation Checks */}
          <div className="spotlight-details-pane">
            <span className="pane-label font-mono">STRICT OPERATING CHECKS</span>
            <ul className="spotlight-rules-list">
              {PROTOCOL_STAGES[activeStep].details.map((detail, idx) => (
                <li key={idx} className="rule-item">
                  <span className="rule-item-badge font-mono">CHK-0{idx + 1}</span>
                  <CheckCircle2 size={15} color={PROTOCOL_STAGES[activeStep].accentColor} className="rule-icon" />
                  <span className="rule-item-text">{detail}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Invariant Architectural Guarantee */}
          <div className="spotlight-guarantee-pane">
            <span className="pane-label font-mono">NON-NEGOTIABLE ARCHITECTURAL INVARIANT</span>
            <div className="guarantee-quote-box">
              <div className="quote-header">
                <Lock size={14} color="var(--color-success)" />
                <span className="quote-tag font-mono">GOVERNANCE CONTRACT</span>
              </div>
              <p className="quote-text">{PROTOCOL_STAGES[activeStep].invariantGuarantee}</p>
            </div>
            <div className="guarantee-footer">
              <FileCheck size={13} color="#8B949E" />
              <span>Auditable via PostgreSQL schema constraints and TimescaleDB triggers.</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
