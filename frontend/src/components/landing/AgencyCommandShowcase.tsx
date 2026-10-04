import React, { useState } from 'react';
import {
  Car,
  Zap,
  Navigation,
  ShieldCheck,
  CheckCircle2,
  Database,
  Layers,
  Cpu,
  ArrowRight
} from 'lucide-react';
import { NumberTicker } from '../common/NumberTicker';

interface AgencyRole {
  id: string;
  shortCode: string;
  category: string;
  tabLabel: string;
  agencyName: string;
  roleDescription: string;
  accentColor: string;
  imageUrl: string;
  imageCaption: string;
  icon: 'traffic' | 'energy' | 'transit' | 'governance';
  kpis: {
    label: string;
    value: number;
    suffix?: string;
    prefix?: string;
    description: string;
  }[];
  activeAdvisory: {
    title: string;
    urgency: 'HIGH' | 'MEDIUM' | 'OPTIMIZATION';
    recommendation: string;
    estimatedImpact: string;
    provenanceTag: string;
  };
}

const AGENCY_ROLES: AgencyRole[] = [
  {
    id: 'traffic',
    shortCode: 'TMC-01',
    category: 'TRAFFIC COMMAND',
    tabLabel: 'Traffic Management Center',
    agencyName: 'Municipal Traffic Operations Center (TMC)',
    roleDescription: 'Arterial corridor hydrodynamic monitoring, coordinated green wave phase balancing, and rapid bottleneck shockwave dissipation.',
    accentColor: '#38BDF8',
    imageUrl: '/assets/images/twilight-city-highway-light-trails.png',
    imageCaption: 'ARTERIAL FLOW HYDRODYNAMIC TWIN',
    icon: 'traffic',
    kpis: [
      { label: 'Corridor Flow Efficiency', value: 18.4, suffix: '%', description: 'Peak travel time improvement' },
      { label: 'Loop Sensor Ingestion', value: 100, suffix: '%', description: 'Continuous 1 Hz stream' },
      { label: 'Downstream Queue Delay', value: 24.6, prefix: '-', suffix: '%', description: 'Queue back-propagation reduction' }
    ],
    activeAdvisory: {
      title: 'Arterial Phase Split Rebalance Advisory',
      urgency: 'HIGH',
      recommendation: 'Extend westbound phase split by +12s at Gateway Junction to clear downstream commercial ingress surge.',
      estimatedImpact: 'Dissipates 140m queue formation within 2 cycle lengths.',
      provenanceTag: 'CONFORMAL PREDICTED (90% CONFIDENCE)'
    }
  },
  {
    id: 'energy',
    shortCode: 'ENR-01',
    category: 'DISTRICT MICROGRID',
    tabLabel: 'District Energy & Microgrid',
    agencyName: 'Municipal Energy & District Facilities Bureau',
    roleDescription: 'Commercial district electrical microgrid synchronization, chiller plant pre-cooling scheduling, and regional peak tariff avoidance.',
    accentColor: '#F59E0B',
    imageUrl: '/assets/images/tech-campus-substation-grid.png',
    imageCaption: 'DISTRICT COMMERCIAL SUBSTATION & MICROGRID TWIN',
    icon: 'energy',
    kpis: [
      { label: 'Peak Demand Shaved', value: 380, suffix: ' kW', description: 'During afternoon tariff surge' },
      { label: 'Fiscal Meter Cadence', value: 15, suffix: ' min', description: 'Utility pulse interval' },
      { label: 'Tariff Penalty Avoidance', value: 100, suffix: '%', description: 'Zero contract cap breaches' }
    ],
    activeAdvisory: {
      title: 'Predictive 15-Minute Pre-Cooling Dispatch',
      urgency: 'OPTIMIZATION',
      recommendation: 'Pre-cool commercial chiller circuit 2 by 1.8°C prior to 17:00 high-tariff window.',
      estimatedImpact: 'Curtails 380 kW electrical surge during municipal peak demand grid strain.',
      provenanceTag: 'THERMODYNAMIC SIMULATION RUN'
    }
  },
  {
    id: 'transit',
    shortCode: 'TRN-01',
    category: 'MULTIMODAL TRANSIT',
    tabLabel: 'Transit Fleet Authority',
    agencyName: 'Regional Multimodal Transit Authority',
    roleDescription: 'Dedicated transit right-of-way synchronization, headway spacing, priority signal preemption, and bus schedule reliability.',
    accentColor: '#10B981',
    imageUrl: '/assets/images/corridor-int-02-transit.png',
    imageCaption: 'REGIONAL MULTIMODAL TRANSIT CORRIDOR TWIN',
    icon: 'transit',
    kpis: [
      { label: 'Headway Reliability', value: 94.2, suffix: '%', description: 'On-schedule transit adherence' },
      { label: 'Transit Delay Reduced', value: 16.5, prefix: '-', suffix: '%', description: 'At signalized crossings' },
      { label: 'Priority Beacons Active', value: 12, suffix: ' Nodes', description: 'Continuous transponder tracking' }
    ],
    activeAdvisory: {
      title: 'Transit Priority Green Extension Request',
      urgency: 'MEDIUM',
      recommendation: 'Authorize 6s green extension for approaching transit cluster on eastern terminal approach.',
      estimatedImpact: 'Clears 42 boarding passengers without disrupting cross-street pedestrian intervals.',
      provenanceTag: 'GROUND TRUTH LIVE BEACON'
    }
  },
  {
    id: 'governance',
    shortCode: 'AUD-01',
    category: 'AUDIT OVERSIGHT',
    tabLabel: 'Municipal Audit & Commission',
    agencyName: 'City Council & Municipal Audit Oversight',
    roleDescription: 'Transparent algorithm governance, immutable TimescaleDB audit records, feature drift monitoring, and strict non-actuation verification.',
    accentColor: '#818CF8',
    imageUrl: '/assets/images/cinematic-illuminated-urban-model.png',
    imageCaption: 'AUTHORITATIVE SYSTEM OF RECORD & AUDIT TWIN',
    icon: 'governance',
    kpis: [
      { label: 'Telemetry Validation Rate', value: 100, suffix: '%', description: 'Physical bounds checked' },
      { label: 'Autonomous Actuations', value: 0, suffix: '', description: 'Human authorization required' },
      { label: 'Audit Trail Retention', value: 365, suffix: ' Days', description: 'Immutable TimescaleDB logs' }
    ],
    activeAdvisory: {
      title: 'Monthly Model Drift (PSI) Audit Certification',
      urgency: 'OPTIMIZATION',
      recommendation: 'Review Population Stability Index reports confirming velocity distribution stability (<0.10 PSI).',
      estimatedImpact: 'Certifies machine learning models remain mathematically calibrated to observed telemetry.',
      provenanceTag: 'SYSTEM OF RECORD VERIFIED'
    }
  }
];

export const AgencyCommandShowcase: React.FC = () => {
  const [activeTabId, setActiveTabId] = useState<string>('traffic');

  const activeRole = AGENCY_ROLES.find((r) => r.id === activeTabId) || AGENCY_ROLES[0];

  const renderRoleIcon = (icon: AgencyRole['icon'], color: string) => {
    switch (icon) {
      case 'traffic':
        return <Car size={18} strokeWidth={2.2} color={color} />;
      case 'energy':
        return <Zap size={18} strokeWidth={2.2} color={color} />;
      case 'transit':
        return <Navigation size={18} strokeWidth={2.2} color={color} />;
      case 'governance':
        return <ShieldCheck size={18} strokeWidth={2.2} color={color} />;
      default:
        return <Layers size={18} strokeWidth={2.2} color={color} />;
    }
  };

  return (
    <section id="operations" className="landing-section agency-command-section">
      <div className="section-header">
        <span className="section-eyebrow font-mono">Multi-Agency Collaboration</span>
        <h2 className="section-title">One corridor twin across four municipal commands</h2>
        <p className="section-subtitle">
          Break departmental silos. Synchronize traffic engineers, energy managers, transit coordinators, and audit commissions on a unified system of record.
        </p>
      </div>

      {/* Agency Command Selector Grid */}
      <div className="agency-nav-grid" role="tablist" aria-label="Municipal Agency Commands">
        {AGENCY_ROLES.map((role) => {
          const isActive = role.id === activeTabId;
          return (
            <button
              key={role.id}
              role="tab"
              aria-selected={isActive}
              className={`agency-nav-card ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTabId(role.id)}
            >
              <div className="nav-card-inner">
                <div
                  className="nav-card-icon-badge"
                  style={{
                    color: isActive ? role.accentColor : '#94A3B8',
                    background: isActive ? `${role.accentColor}18` : 'rgba(255, 255, 255, 0.03)',
                    borderColor: isActive ? `${role.accentColor}45` : 'rgba(255, 255, 255, 0.08)'
                  }}
                >
                  {renderRoleIcon(role.icon, isActive ? role.accentColor : '#94A3B8')}
                </div>
                <div className="nav-card-text">
                  <div className="nav-card-top-row">
                    <span
                      className="nav-card-id font-mono"
                      style={{ color: isActive ? role.accentColor : '#64748B' }}
                    >
                      {role.shortCode}
                    </span>
                    <span className="nav-card-category font-mono">
                      {role.category}
                    </span>
                  </div>
                  <span className="nav-card-title">{role.tabLabel}</span>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Agency Command Panel */}
      <div className="agency-display-card">
        {/* Top Info Banner */}
        <div className="agency-card-topbar">
          <div className="agency-title-group">
            <div className="spec-meta-row font-mono">
              <span
                className="spec-category-badge"
                style={{
                  color: activeRole.accentColor,
                  background: `${activeRole.accentColor}15`,
                  borderColor: `${activeRole.accentColor}40`
                }}
              >
                {activeRole.shortCode} : {activeRole.category}
              </span>
              <span className="spec-online-indicator font-mono">
                <span className="pulse-indicator" style={{ background: 'var(--color-success)' }} />
                <span>DECISION-SUPPORT READY</span>
              </span>
            </div>
            <h3 className="agency-name">{activeRole.agencyName}</h3>
            <p className="agency-role-desc">{activeRole.roleDescription}</p>
          </div>
          <div className="agency-governance-tag font-mono">
            <Database size={13} color="var(--color-primary)" />
            <span>AUTHORITATIVE POSTGRESQL STORE</span>
          </div>
        </div>

        {/* Dynamic Agency Stage Content */}
        <div className="agency-grid-layout">
          {/* Left Column: KPI Cards with Number Ticker */}
          <div className="agency-kpis-column">
            <span className="column-label font-mono">SYNCHRONIZED TELEMETRY METRICS</span>
            <div className="agency-kpis-grid">
              {activeRole.kpis.map((kpi, idx) => (
                <div key={idx} className="agency-kpi-card">
                  <span className="kpi-label font-mono">{kpi.label}</span>
                  <div className="kpi-value-row">
                    <span className="kpi-number font-mono" style={{ color: activeRole.accentColor }}>
                      <NumberTicker
                        value={kpi.value}
                        decimals={kpi.value % 1 !== 0 ? 1 : 0}
                        prefix={kpi.prefix}
                        suffix={kpi.suffix}
                      />
                    </span>
                  </div>
                  <span className="kpi-desc">{kpi.description}</span>
                </div>
              ))}
            </div>

            {/* Feature Asset Banner with dynamic image & caption */}
            <div className="agency-preview-asset">
              <img src={activeRole.imageUrl} alt={activeRole.agencyName} className="asset-cover-img" />
              <div className="asset-caption font-mono">
                <Cpu size={12} color={activeRole.accentColor} />
                <span>{activeRole.imageCaption}</span>
              </div>
            </div>
          </div>

          {/* Right Column: Active Decision Advisory Workflow Card */}
          <div className="agency-advisory-column">
            <span className="column-label font-mono">HUMAN-IN-THE-LOOP ADVISORY PIPELINE</span>
            <div className="agency-advisory-card">
              <div className="advisory-top-meta">
                <span className={`advisory-urgency-badge ${activeRole.activeAdvisory.urgency.toLowerCase()} font-mono`}>
                  {activeRole.activeAdvisory.urgency} ADVISORY
                </span>
                <span className="advisory-provenance-tag font-mono">
                  {activeRole.activeAdvisory.provenanceTag}
                </span>
              </div>

              <h4 className="advisory-headline">{activeRole.activeAdvisory.title}</h4>
              <p className="advisory-action-text">{activeRole.activeAdvisory.recommendation}</p>

              <div className="advisory-impact-box">
                <div className="impact-header font-mono">
                  <CheckCircle2 size={13} color="var(--color-success)" />
                  <span>MUNICIPAL IMPACT ESTIMATE</span>
                </div>
                <p className="impact-text">{activeRole.activeAdvisory.estimatedImpact}</p>
              </div>

              <div className="advisory-authorization-footer">
                <div className="auth-lock-info font-mono">
                  <ShieldCheck size={14} color="#10B981" />
                  <span>REQUIRES OPERATOR CLEARANCE PRIOR TO FIELD ACTUATION</span>
                </div>
                <button
                  type="button"
                  className="agency-review-btn font-mono"
                  onClick={() => {
                    const el = document.getElementById('contact');
                    if (el) el.scrollIntoView({ behavior: 'smooth' });
                  }}
                >
                  <span>REVIEW AUDIT TRAIL</span>
                  <ArrowRight size={13} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
