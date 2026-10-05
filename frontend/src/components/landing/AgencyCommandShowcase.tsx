import React, { useState } from 'react';
import {
  Car,
  Zap,
  Navigation,
  ShieldCheck,
  CheckCircle2,
  Database,
  ArrowRight,
  Radio,
  Layers,
  ChevronDown,
  Lock,
  Activity
} from 'lucide-react';
import { NumberTicker } from '../common/NumberTicker';

interface AgencyChannel {
  id: string;
  shortCode: string;
  departmentName: string;
  domainLabel: string;
  accentColor: string;
  icon: 'traffic' | 'energy' | 'transit' | 'governance';
  statusSummary: string;
  statusPill: string;
  pinCoordinates: { x: number; y: number }; // Percentage for positioning on tactical visual
  pinLabel: string;
  pinSub: string;
  calloutAlign: 'left' | 'right';
  kpis: {
    label: string;
    value: number;
    prefix?: string;
    suffix?: string;
    description: string;
  }[];
  activeAdvisory: {
    title: string;
    urgency: 'HIGH' | 'MEDIUM' | 'OPTIMIZATION';
    recommendation: string;
    estimatedImpact: string;
    clearanceStatus: string;
  };
}

const AGENCY_CHANNELS: AgencyChannel[] = [
  {
    id: 'traffic',
    shortCode: 'TMC-01',
    departmentName: 'Traffic Operations Center',
    domainLabel: 'ARTERIAL FLOW COMMAND',
    accentColor: '#38BDF8',
    icon: 'traffic',
    statusSummary: 'Arterial Flow Stable : 18.4% Efficiency Gain',
    statusPill: '1 Hz STREAM',
    pinCoordinates: { x: 30, y: 38 },
    pinLabel: 'INT-01 GATEWAY',
    pinSub: 'INDUCTIVE LOOPS',
    calloutAlign: 'right',
    kpis: [
      { label: 'Corridor Flow Gain', value: 18.4, suffix: '%', description: 'Peak travel time improvement' },
      { label: 'Downstream Queue Delay', value: 24.6, prefix: '-', suffix: '%', description: 'Bottleneck shockwave reduction' }
    ],
    activeAdvisory: {
      title: 'Arterial Phase Split Rebalance Advisory',
      urgency: 'HIGH',
      recommendation: 'Extend westbound phase split by +12s at Gateway Junction to clear downstream commercial ingress surge.',
      estimatedImpact: 'Dissipates 140m queue formation within 2 cycle lengths.',
      clearanceStatus: 'DISPATCHED TO TMC OPERATOR'
    }
  },
  {
    id: 'energy',
    shortCode: 'ENR-01',
    departmentName: 'District Energy & Microgrid',
    domainLabel: 'ELECTRICAL GRID COMMAND',
    accentColor: '#F59E0B',
    icon: 'energy',
    statusSummary: 'Peak Curtailment Ready : 380 kW Shaved',
    statusPill: 'GRID SYNCED',
    pinCoordinates: { x: 70, y: 26 },
    pinLabel: 'SUBSTATION NODE',
    pinSub: '15-MIN METERING',
    calloutAlign: 'left',
    kpis: [
      { label: 'Peak Demand Shaved', value: 380, suffix: ' kW', description: 'During afternoon tariff surge' },
      { label: 'Contract Breaches', value: 0, suffix: '%', description: 'Zero peak tariff exposure' }
    ],
    activeAdvisory: {
      title: 'Predictive Chiller Pre-Cooling Dispatch',
      urgency: 'OPTIMIZATION',
      recommendation: 'Pre-cool commercial chiller circuit 2 by 1.8°C prior to 17:00 high-tariff window.',
      estimatedImpact: 'Curtails 380 kW electrical surge during municipal peak demand grid strain.',
      clearanceStatus: 'DISPATCHED TO ENERGY DESK'
    }
  },
  {
    id: 'transit',
    shortCode: 'TRN-01',
    departmentName: 'Regional Transit Authority',
    domainLabel: 'MULTIMODAL RIGHT-OF-WAY',
    accentColor: '#10B981',
    icon: 'transit',
    statusSummary: 'Transit Priority Active : 94.2% Adherence',
    statusPill: 'BEACON ACTIVE',
    pinCoordinates: { x: 24, y: 70 },
    pinLabel: 'TRANSIT CORRIDOR',
    pinSub: 'GNSS TRANSPONDERS',
    calloutAlign: 'right',
    kpis: [
      { label: 'Headway Adherence', value: 94.2, suffix: '%', description: 'On-schedule transit cadence' },
      { label: 'Transit Crossing Delay', value: 16.5, prefix: '-', suffix: '%', description: 'Signal preemption saving' }
    ],
    activeAdvisory: {
      title: 'Transit Priority Green Window Request',
      urgency: 'MEDIUM',
      recommendation: 'Authorize 6s green extension for approaching transit cluster on eastern approach leg.',
      estimatedImpact: 'Clears 42 boarding passengers without disrupting cross-street pedestrian intervals.',
      clearanceStatus: 'DISPATCHED TO FLEET DESK'
    }
  },
  {
    id: 'governance',
    shortCode: 'AUD-01',
    departmentName: 'City Audit Commission',
    domainLabel: 'INDEPENDENT OVERSIGHT',
    accentColor: '#818CF8',
    icon: 'governance',
    statusSummary: 'Audit Ledger Verified : 0 Actuations',
    statusPill: 'IMMUTABLE STORE',
    pinCoordinates: { x: 66, y: 72 },
    pinLabel: 'AUDIT LEDGER',
    pinSub: 'TIMESCALEDB LOG',
    calloutAlign: 'left',
    kpis: [
      { label: 'Telemetry Bounds Validated', value: 100, suffix: '%', description: 'Speed clamped 0-120 km/h' },
      { label: 'Autonomous Actuations', value: 0, suffix: '', description: 'Human authorization required' }
    ],
    activeAdvisory: {
      title: 'Model Distribution Drift (PSI) Audit',
      urgency: 'OPTIMIZATION',
      recommendation: 'Certify Population Stability Index reports confirming velocity distribution stability.',
      estimatedImpact: 'Certifies machine learning models remain mathematically calibrated (PSI = 0.04).',
      clearanceStatus: 'LOGGED IN AUDIT LEDGER'
    }
  }
];

export const AgencyCommandShowcase: React.FC = () => {
  const [activeAgencyId, setActiveAgencyId] = useState<string>('traffic');
  const [activeLayerFilter, setActiveLayerFilter] = useState<string>('all');

  const activeChannel = AGENCY_CHANNELS.find((c) => c.id === activeAgencyId) || AGENCY_CHANNELS[0];

  const renderIcon = (type: AgencyChannel['icon'], color: string) => {
    switch (type) {
      case 'traffic':
        return <Car size={16} color={color} strokeWidth={2.2} />;
      case 'energy':
        return <Zap size={16} color={color} strokeWidth={2.2} />;
      case 'transit':
        return <Navigation size={16} color={color} strokeWidth={2.2} />;
      case 'governance':
        return <ShieldCheck size={16} color={color} strokeWidth={2.2} />;
    }
  };

  return (
    <section id="operations" className="landing-section agency-tactical-section">
      <div className="section-header">
        <span className="section-eyebrow font-mono">Multi-Agency Collaboration</span>
        <h2 className="section-title">One corridor twin across four municipal commands</h2>
        <p className="section-subtitle">
          Break departmental silos. Synchronize traffic engineers, energy managers, transit coordinators, and audit commissions on a unified system of record.
        </p>
      </div>

      {/* Panoramic Mission Control Incident Room */}
      <div className="tactical-mission-room">
        {/* Left Side: Panoramic Tactical Corridor Stage */}
        <div className="tactical-stage-panel">
          {/* Tactical HUD Header */}
          <div className="tactical-hud-topbar font-mono">
            <div className="hud-status-indicator">
              <span className="pulse-indicator" style={{ background: 'var(--color-success)' }} />
              <span className="hud-status-text">TACTICAL CORRIDOR SPATIAL GRID</span>
            </div>
            <div className="hud-metric-readout">
              <Activity size={12} color="#38BDF8" />
              <span>SYNCHRONIZED ARTERIAL CORRIDOR</span>
            </div>
          </div>

          {/* Tactical Visual Canvas with Embedded Spatial Pins */}
          <div className="tactical-canvas-wrap">
            <img
              src="/assets/images/twilight-city-highway-light-trails.png"
              alt="Tactical Urban Corridor Spatial Model"
              className="tactical-canvas-img"
            />
            <div className="tactical-grid-overlay" />

            {/* Spatial Reticle Corners */}
            <span className="canvas-reticle top-left font-mono">+</span>
            <span className="canvas-reticle top-right font-mono">+</span>
            <span className="canvas-reticle bottom-left font-mono">+</span>
            <span className="canvas-reticle bottom-right font-mono">+</span>

            {/* Interactive Spatial Agency Pins */}
            {AGENCY_CHANNELS.map((ch) => {
              const isSelected = ch.id === activeAgencyId;
              const isVisible = activeLayerFilter === 'all' || activeLayerFilter === ch.id;

              if (!isVisible) return null;

              return (
                <button
                  key={ch.id}
                  type="button"
                  aria-label={`${ch.departmentName} Tactical Pin`}
                  className={`spatial-agency-pin ${isSelected ? 'selected' : ''}`}
                  style={{
                    left: `${ch.pinCoordinates.x}%`,
                    top: `${ch.pinCoordinates.y}%`
                  }}
                  onClick={() => setActiveAgencyId(ch.id)}
                >
                  <div
                    className="pin-beacon-ring"
                    style={{ borderColor: ch.accentColor, background: `${ch.accentColor}25` }}
                  />
                  <div
                    className="pin-core-node"
                    style={{ background: ch.accentColor, boxShadow: `0 0 12px ${ch.accentColor}` }}
                  >
                    {renderIcon(ch.icon, '#000000')}
                  </div>

                  <div className={`pin-callout-card font-mono ${isSelected ? 'focused' : ''} ${ch.calloutAlign === 'left' ? 'align-left' : 'align-right'}`}>
                    <div className="callout-header">
                      <span className="callout-code" style={{ color: ch.accentColor }}>{ch.shortCode}</span>
                      <span className="callout-status">{ch.statusPill}</span>
                    </div>
                    <span className="callout-label">{ch.pinLabel}</span>
                    <span className="callout-sub">{ch.pinSub}</span>
                  </div>
                </button>
              );
            })}

            {/* Tactical Canvas Caption */}
            <div className="tactical-canvas-caption font-mono">
              <Radio size={11} color="var(--color-primary)" />
              <span>SYNCHRONIZED SENSOR MESH : ACTIVE FOCUS : {activeChannel.shortCode}</span>
            </div>
          </div>

          {/* Tactical Layer Filter Bar */}
          <div className="tactical-filter-bar font-mono" role="tablist" aria-label="Spatial Sensor Layers">
            <span className="filter-title">
              <Layers size={12} color="#94A3B8" />
              <span>LAYERS:</span>
            </span>
            <button
              type="button"
              role="tab"
              aria-selected={activeLayerFilter === 'all'}
              className={`layer-filter-btn ${activeLayerFilter === 'all' ? 'active' : ''}`}
              onClick={() => setActiveLayerFilter('all')}
            >
              ALL NODES (4)
            </button>
            {AGENCY_CHANNELS.map((ch) => (
              <button
                key={ch.id}
                type="button"
                role="tab"
                aria-selected={activeLayerFilter === ch.id}
                className={`layer-filter-btn ${activeLayerFilter === ch.id ? 'active' : ''}`}
                style={{
                  color: activeLayerFilter === ch.id ? ch.accentColor : undefined,
                  borderColor: activeLayerFilter === ch.id ? `${ch.accentColor}50` : undefined
                }}
                onClick={() => {
                  setActiveLayerFilter(ch.id);
                  setActiveAgencyId(ch.id);
                }}
              >
                {ch.shortCode}
              </button>
            ))}
          </div>
        </div>

        {/* Right Side: Multi-Agency Coordinated Dispatch Terminal */}
        <div className="tactical-dispatch-terminal">
          <div className="terminal-topbar">
            <div className="terminal-title-group">
              <Database size={14} color="var(--color-primary)" />
              <div>
                <h3 className="terminal-main-heading">Multi-Agency Coordinated Dispatch</h3>
                <span className="terminal-sub-heading font-mono">POSTGRESQL UNIFIED SYSTEM OF RECORD</span>
              </div>
            </div>
            <span className="terminal-audit-pill font-mono">
              <Lock size={11} color="var(--color-success)" />
              <span>READ-ONLY ADVISORY</span>
            </span>
          </div>

          {/* Interactive Stack of Agency Dispatch Channels */}
          <div className="agency-channels-stack" role="tablist" aria-label="Agency Command Channels">
            {AGENCY_CHANNELS.map((agency) => {
              const isExpanded = agency.id === activeAgencyId;

              return (
                <div
                  key={agency.id}
                  className={`agency-channel-strip ${isExpanded ? 'expanded' : 'collapsed'}`}
                  style={{
                    borderColor: isExpanded ? `${agency.accentColor}45` : 'rgba(255, 255, 255, 0.07)'
                  }}
                >
                  {/* Channel Header (Click to focus / expand) */}
                  <button
                    type="button"
                    role="tab"
                    aria-selected={isExpanded}
                    className="channel-header-btn"
                    onClick={() => setActiveAgencyId(agency.id)}
                  >
                    <div className="channel-id-row">
                      <div
                        className="channel-icon-container"
                        style={{
                          background: isExpanded ? `${agency.accentColor}18` : 'rgba(255, 255, 255, 0.04)',
                          borderColor: isExpanded ? `${agency.accentColor}40` : 'rgba(255, 255, 255, 0.08)'
                        }}
                      >
                        {renderIcon(agency.icon, isExpanded ? agency.accentColor : '#94A3B8')}
                      </div>
                      <div className="channel-labels">
                        <div className="code-domain-line font-mono">
                          <span className="code-tag" style={{ color: agency.accentColor }}>{agency.shortCode}</span>
                          <span className="domain-text">{agency.domainLabel}</span>
                        </div>
                        <h4 className="department-title">{agency.departmentName}</h4>
                      </div>
                    </div>

                    <div className="channel-header-right">
                      <span
                        className="channel-status-chip font-mono"
                        style={{
                          color: agency.accentColor,
                          borderColor: `${agency.accentColor}35`,
                          background: `${agency.accentColor}10`
                        }}
                      >
                        {agency.statusPill}
                      </span>
                      <ChevronDown
                        size={15}
                        className={`channel-chevron ${isExpanded ? 'rotated' : ''}`}
                        color="#94A3B8"
                      />
                    </div>
                  </button>

                  {/* Expanded Operational Readout */}
                  {isExpanded && (
                    <div className="channel-expanded-body">
                      {/* Real-time KPI Metric Gauges */}
                      <div className="channel-kpis-grid">
                        {agency.kpis.map((kpi, kIdx) => (
                          <div key={kIdx} className="channel-kpi-card">
                            <span className="kpi-label font-mono">{kpi.label}</span>
                            <span className="kpi-number font-mono" style={{ color: agency.accentColor }}>
                              <NumberTicker
                                value={kpi.value}
                                decimals={kpi.value % 1 !== 0 ? 1 : 0}
                                prefix={kpi.prefix}
                                suffix={kpi.suffix}
                              />
                            </span>
                            <span className="kpi-desc">{kpi.description}</span>
                          </div>
                        ))}
                      </div>

                      {/* Active Advisory & Municipal Impact */}
                      <div className="channel-advisory-box">
                        <div className="advisory-top-meta font-mono">
                          <span className={`urgency-badge ${agency.activeAdvisory.urgency.toLowerCase()}`}>
                            {agency.activeAdvisory.urgency} ADVISORY
                          </span>
                          <span className="advisory-heading">{agency.activeAdvisory.title}</span>
                        </div>
                        <p className="advisory-text">{agency.activeAdvisory.recommendation}</p>

                        <div className="impact-statement-row">
                          <CheckCircle2 size={13} color="var(--color-success)" className="impact-icon" />
                          <span className="impact-text">{agency.activeAdvisory.estimatedImpact}</span>
                        </div>
                      </div>

                      {/* Operator Sign-off Clearance Bar */}
                      <div className="channel-clearance-footer font-mono">
                        <div className="clearance-lock-info">
                          <ShieldCheck size={13} color="#10B981" />
                          <span>{agency.activeAdvisory.clearanceStatus}</span>
                        </div>
                        <span className="clearance-rule">HUMAN AUTHORIZATION REQUIRED</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Terminal Global Footer */}
          <div className="terminal-global-footer font-mono">
            <span className="system-note">AUTHORITATIVE TIMESCALEDB RECORD : 0 AUTONOMOUS ACTUATIONS</span>
            <button
              type="button"
              className="terminal-audit-cta"
              onClick={() => {
                const el = document.getElementById('contact');
                if (el) el.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              <span>AUDIT TRAIL</span>
              <ArrowRight size={11} />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};
