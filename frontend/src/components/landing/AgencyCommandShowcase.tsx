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
  tabLabel: string;
  agencyName: string;
  roleDescription: string;
  accentColor: string;
  imageUrl?: string;
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
    tabLabel: 'Traffic Management Center',
    agencyName: 'Municipal Traffic Operations Center (TMC)',
    roleDescription: 'Arterial corridor hydrodynamic monitoring, coordinated green wave phase balancing, and rapid bottleneck shockwave dissipation.',
    accentColor: '#38BDF8',
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
    tabLabel: 'District Energy & Microgrid',
    agencyName: 'Municipal Energy & District Facilities Bureau',
    roleDescription: 'Commercial district electrical microgrid synchronization, chiller plant pre-cooling scheduling, and regional peak tariff avoidance.',
    accentColor: '#F59E0B',
    imageUrl: '/assets/images/tech-campus-substation-grid.png',
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
    tabLabel: 'Transit Fleet Authority',
    agencyName: 'Regional Multimodal Transit Authority',
    roleDescription: 'Dedicated transit right-of-way synchronization, headway spacing, priority signal preemption, and bus schedule reliability.',
    accentColor: '#10B981',
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
    tabLabel: 'Municipal Audit & Commission',
    agencyName: 'City Council & Municipal Audit Oversight',
    roleDescription: 'Transparent algorithm governance, immutable TimescaleDB audit records, feature drift monitoring, and strict non-actuation verification.',
    accentColor: '#818CF8',
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
        return <Car size={16} color={color} />;
      case 'energy':
        return <Zap size={16} color={color} />;
      case 'transit':
        return <Navigation size={16} color={color} />;
      case 'governance':
        return <ShieldCheck size={16} color={color} />;
      default:
        return <Layers size={16} color={color} />;
    }
  };

  return (
    <section id="operations" className="landing-section agency-command-section">
      <div className="section-header">
        <span className="section-eyebrow">Multi-Agency Collaboration</span>
        <h2 className="section-title">One corridor twin across four municipal commands</h2>
        <p className="section-subtitle">
          Break departmental silos. Synchronize traffic engineers, energy managers, transit coordinators, and audit commissions on a unified system of record.
        </p>
      </div>

      {/* Modern Tabs Navigation Bar */}
      <div className="agency-tabs-nav" role="tablist">
        {AGENCY_ROLES.map((role) => {
          const isActive = role.id === activeTabId;
          return (
            <button
              key={role.id}
              role="tab"
              aria-selected={isActive}
              className={`agency-tab-btn ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTabId(role.id)}
              style={{
                borderColor: isActive ? role.accentColor : undefined,
                boxShadow: isActive ? `0 0 16px ${role.accentColor}25` : undefined
              }}
            >
              <div
                className="agency-tab-icon"
                style={{
                  background: isActive ? `${role.accentColor}20` : 'rgba(255, 255, 255, 0.04)',
                  borderColor: isActive ? `${role.accentColor}50` : 'rgba(255, 255, 255, 0.08)'
                }}
              >
                {renderRoleIcon(role.icon, isActive ? role.accentColor : '#8B949E')}
              </div>
              <span className="agency-tab-label">{role.tabLabel}</span>
            </button>
          );
        })}
      </div>

      {/* Active Agency Command Panel */}
      <div className="agency-display-card">
        {/* Top Info Banner */}
        <div className="agency-card-topbar">
          <div className="agency-title-group">
            <div className="agency-badge font-mono" style={{ color: activeRole.accentColor, borderColor: `${activeRole.accentColor}40` }}>
              {activeRole.tabLabel.toUpperCase()}
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

            {/* Optional Feature Asset Banner if image present */}
            {activeRole.imageUrl && (
              <div className="agency-preview-asset">
                <img src={activeRole.imageUrl} alt={activeRole.agencyName} className="asset-cover-img" />
                <div className="asset-caption font-mono">
                  <Cpu size={12} color="#F59E0B" />
                  <span>DISTRICT COMMERCIAL SUBSTATION & MICROGRID TWIN</span>
                </div>
              </div>
            )}
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
