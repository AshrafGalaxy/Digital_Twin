import React, { useState } from 'react';
import { ShieldCheck, Database, CheckCircle, Clock } from 'lucide-react';

export type ProvenanceMode = 'LIVE' | 'REPLAY' | 'SIMULATION' | 'PREDICTED' | 'STALE';

interface ModeDetails {
  mode: ProvenanceMode;
  badgeClass: string;
  accentColor: string;
  tagline: string;
  payload: {
    entityId: string;
    metric: string;
    value: string;
    unit: string;
    sourceMode: ProvenanceMode;
    observedAtOrGeneratedAt: string;
    qualityStatus: string;
    uncertaintyOrEngine?: string;
  };
  contractRule: string;
  architecturalInvariant: string;
}

const PROVENANCE_DETAILS: Record<ProvenanceMode, ModeDetails> = {
  LIVE: {
    mode: 'LIVE',
    badgeClass: 'live',
    accentColor: '#38BDF8',
    tagline: 'Direct, unmanipulated telemetry from physical corridor sensor arrays.',
    payload: {
      entityId: 'urn:ngsi-ld:RoadSegment:SEG-NR-EB-01',
      metric: 'averageVelocity',
      value: '34.2',
      unit: 'km/h',
      sourceMode: 'LIVE',
      observedAtOrGeneratedAt: '2026-10-03T14:48:12.418Z',
      qualityStatus: 'VERIFIED_FRESH (heartbeat 28s < 180s threshold)'
    },
    contractRule: 'Verified direct physical observation from corridor loop detector station. Admitted directly into operational state.',
    architecturalInvariant: 'Authoritative PostgreSQL state record. Cannot be overwritten by simulation or forecast runs.'
  },
  REPLAY: {
    mode: 'REPLAY',
    badgeClass: 'replay',
    accentColor: '#818CF8',
    tagline: 'Historical telemetry played back chronologically from authoritative archives.',
    payload: {
      entityId: 'urn:ngsi-ld:RoadSegment:SEG-NR-EB-01',
      metric: 'averageVelocity',
      value: '41.8',
      unit: 'km/h',
      sourceMode: 'REPLAY',
      observedAtOrGeneratedAt: '2026-09-14T17:30:00.000Z',
      qualityStatus: 'HISTORICAL_ARCHIVE (playback rate: 1.0x realtime)'
    },
    contractRule: 'Never labeled as live. Preserves original sensor timeline for post-incident audits and model back-testing.',
    architecturalInvariant: 'Tagged with historical replay epoch to preserve state separation from live operational feeds.'
  },
  SIMULATION: {
    mode: 'SIMULATION',
    badgeClass: 'simulation',
    accentColor: '#A78BFA',
    tagline: 'Output of microscopic behavioral physics engines under scenario parameters.',
    payload: {
      entityId: 'urn:ngsi-ld:Intersection:INT-VN-01',
      metric: 'simulatedQueueLength',
      value: '14.2',
      unit: 'vehicles',
      sourceMode: 'SIMULATION',
      observedAtOrGeneratedAt: '2026-10-03T14:48:00.000Z',
      uncertaintyOrEngine: 'SUMO v1.20 (Krauss CF + LC2013 lane change)',
      qualityStatus: 'SYNTHETIC_SCENARIO (Rain Deluge Template)'
    },
    contractRule: 'Never claimed as observed reality. Synthetic kinematics strictly isolated in scenario sandbox schemas.',
    architecturalInvariant: 'Written strictly to simulation_runs schema. Blocked by database schema from polluting observed tables.'
  },
  PREDICTED: {
    mode: 'PREDICTED',
    badgeClass: 'predicted',
    accentColor: '#F59E0B',
    tagline: 'Machine learning forecast accompanied by conformal uncertainty envelopes.',
    payload: {
      entityId: 'urn:ngsi-ld:RoadSegment:SEG-NR-WB-02',
      metric: 'predictedVelocity (+15m horizon)',
      value: '28.6',
      unit: 'km/h',
      sourceMode: 'PREDICTED',
      observedAtOrGeneratedAt: '2026-10-03T15:03:00.000Z',
      uncertaintyOrEngine: 'Conformal bounds: 80% [24.1–32.8], 90% [21.5–35.4] km/h',
      qualityStatus: 'CALIBRATED_SPLIT (Top-1 SHAP: IngressSurge -4.1 km/h)'
    },
    contractRule: 'Never called a measurement. Forecasts without conformal coverage intervals and TreeSHAP attributions are rejected.',
    architecturalInvariant: 'Stored in isolated model_forecasts schema with Population Stability Index (PSI) drift tracking.'
  },
  STALE: {
    mode: 'STALE',
    badgeClass: 'stale',
    accentColor: '#EF4444',
    tagline: 'Sensor feed exceeding maximum allowable freshness threshold.',
    payload: {
      entityId: 'urn:ngsi-ld:Building:BLD-PHOENIX-01',
      metric: 'activePowerDemand',
      value: '4,862',
      unit: 'kW',
      sourceMode: 'STALE',
      observedAtOrGeneratedAt: '2026-10-03T14:32:00.000Z',
      qualityStatus: 'QUARANTINE_TRIGGERED (Age: 972s > 900s allowed energy threshold)'
    },
    contractRule: 'Automatically flagged in amber/red. Stale feeds are blocked by the rule engine from generating automated advisories.',
    architecturalInvariant: 'Marked with status: STALE in state store; advisory pipeline automatically falls back to safe persistence baseline.'
  }
};

export const ProvenanceSandbox: React.FC = () => {
  const [selectedMode, setSelectedMode] = useState<ProvenanceMode>('LIVE');
  const details = PROVENANCE_DETAILS[selectedMode];

  return (
    <div className="provenance-sandbox-card">
      <div className="sandbox-header">
        <div className="sandbox-title-group">
          <div className="sandbox-icon-box">
            <ShieldCheck size={18} color="var(--color-primary)" />
          </div>
          <div>
            <h3 className="sandbox-title">Interactive Provenance Mode Simulator</h3>
            <span className="sandbox-subtitle font-mono">
              Click a source mode to inspect its live data contract and schema validation invariants
            </span>
          </div>
        </div>

        {/* Mode Selector Chips */}
        <div className="sandbox-mode-chips" role="tablist" aria-label="Provenance Modes">
          {(['LIVE', 'REPLAY', 'SIMULATION', 'PREDICTED', 'STALE'] as ProvenanceMode[]).map((mode) => {
            const isActive = selectedMode === mode;
            return (
              <button
                key={mode}
                type="button"
                role="tab"
                aria-selected={isActive}
                className={`sandbox-chip-btn ${PROVENANCE_DETAILS[mode].badgeClass} ${isActive ? 'active' : ''}`}
                onClick={() => setSelectedMode(mode)}
              >
                <span className="chip-dot" />
                <span className="font-mono">{mode}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="sandbox-body">
        {/* Left: Live Validated Telemetry Record */}
        <div className="sandbox-record-pane">
          <div className="record-pane-topbar">
            <div className="record-pane-tag font-mono">
              <span className={`status-pill ${details.badgeClass}`}>{details.mode}</span>
              <span className="record-freshness font-mono">STANDARDS CONTRACT</span>
            </div>
            <span className="record-schema-tag font-mono">ETSI NGSI-LD SCHEMA</span>
          </div>

          <div className="record-code-wrap">
            <pre className="record-code-block font-mono">
              <code>{JSON.stringify(details.payload, null, 2)}</code>
            </pre>
          </div>
        </div>

        {/* Right: Operational Guarantee & Architectural Rules */}
        <div className="sandbox-rules-pane">
          <div className="rules-section">
            <div className="rules-header">
              <CheckCircle size={14} color={details.accentColor} />
              <span className="rules-title font-mono" style={{ color: details.accentColor }}>
                DATA HONESTY CONTRACT
              </span>
            </div>
            <p className="rules-text">{details.contractRule}</p>
          </div>

          <div className="rules-section">
            <div className="rules-header">
              <Database size={14} color="#8B949E" />
              <span className="rules-title font-mono">STORAGE SEPARATION INVARIANT</span>
            </div>
            <p className="rules-text">{details.architecturalInvariant}</p>
          </div>

          <div className="rules-footer">
            <div className="rules-footer-badge font-mono">
              <Clock size={12} />
              <span>IMMUTABLE PROVENANCE GUARANTEE</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
