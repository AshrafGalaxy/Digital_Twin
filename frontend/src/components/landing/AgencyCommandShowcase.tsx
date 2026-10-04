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
  Clock
} from 'lucide-react';
import { NumberTicker } from '../common/NumberTicker';

interface ScenarioDefinition {
  id: string;
  name: string;
  code: string;
  timeWindow: string;
  description: string;
  agencies: {
    traffic: {
      kpis: { label: string; value: number; prefix?: string; suffix?: string; description: string }[];
      advisoryTitle: string;
      urgency: 'HIGH' | 'MEDIUM' | 'OPTIMIZATION';
      recommendation: string;
      impact: string;
      statusPill: string;
    };
    energy: {
      kpis: { label: string; value: number; prefix?: string; suffix?: string; description: string }[];
      advisoryTitle: string;
      urgency: 'HIGH' | 'MEDIUM' | 'OPTIMIZATION';
      recommendation: string;
      impact: string;
      statusPill: string;
    };
    transit: {
      kpis: { label: string; value: number; prefix?: string; suffix?: string; description: string }[];
      advisoryTitle: string;
      urgency: 'HIGH' | 'MEDIUM' | 'OPTIMIZATION';
      recommendation: string;
      impact: string;
      statusPill: string;
    };
    governance: {
      kpis: { label: string; value: number; prefix?: string; suffix?: string; description: string }[];
      advisoryTitle: string;
      urgency: 'HIGH' | 'MEDIUM' | 'OPTIMIZATION';
      recommendation: string;
      impact: string;
      statusPill: string;
    };
  };
}

const SCENARIOS: ScenarioDefinition[] = [
  {
    id: 'peak-ingress',
    name: 'Evening Peak Surge & Tariff Window',
    code: 'SCN-01',
    timeWindow: '17:00 - 18:30 PEAK',
    description: 'Arterial commercial ingress surge co-occurring with regional utility peak tariff pricing.',
    agencies: {
      traffic: {
        kpis: [
          { label: 'Corridor Flow Gain', value: 18.4, suffix: '%', description: 'Peak travel time saving' },
          { label: 'Downstream Queue', value: 24.6, prefix: '-', suffix: '%', description: 'Queue shockwave reduction' }
        ],
        advisoryTitle: 'Arterial Phase Split Extension',
        urgency: 'HIGH',
        recommendation: 'Extend westbound phase split by +12s at Gateway Junction to clear downstream bottleneck.',
        impact: 'Dissipates 140m queue formation within 2 cycle lengths.',
        statusPill: '1 Hz STREAM VERIFIED'
      },
      energy: {
        kpis: [
          { label: 'Peak Demand Shaved', value: 380, suffix: ' kW', description: 'Afternoon tariff avoidance' },
          { label: 'Contract Cap Breaches', value: 0, suffix: '%', description: 'Zero penalty exposure' }
        ],
        advisoryTitle: 'Pre-Cooling Chiller Dispatch',
        urgency: 'OPTIMIZATION',
        recommendation: 'Pre-cool commercial chiller circuit 2 by 1.8°C prior to 17:00 high-tariff window.',
        impact: 'Curtails 380 kW electrical surge during municipal peak demand grid strain.',
        statusPill: 'CURTAILMENT ARMED'
      },
      transit: {
        kpis: [
          { label: 'Headway Adherence', value: 94.2, suffix: '%', description: 'On-schedule transit cadence' },
          { label: 'Crossing Delay', value: 16.5, prefix: '-', suffix: '%', description: 'At signalized approaches' }
        ],
        advisoryTitle: 'Transit Priority Green Window',
        urgency: 'MEDIUM',
        recommendation: 'Authorize 6s green extension for approaching transit cluster on eastern approach leg.',
        impact: 'Clears 42 boarding commuters without disrupting cross-street intervals.',
        statusPill: 'BEACON SYNCHRONIZED'
      },
      governance: {
        kpis: [
          { label: 'Telemetry Checked', value: 100, suffix: '%', description: 'Physical bounds clamped' },
          { label: 'Auto-Actuations', value: 0, suffix: '', description: 'Operator sign-off enforced' }
        ],
        advisoryTitle: 'Distribution Drift (PSI) Audit',
        urgency: 'OPTIMIZATION',
        recommendation: 'Certify Population Stability Index reports confirming velocity distribution stability.',
        impact: 'Certifies machine learning models remain mathematically calibrated (PSI = 0.04).',
        statusPill: 'TIMESCALEDB IMMUTABLE'
      }
    }
  },
  {
    id: 'transit-priority',
    name: 'Multimodal Transit Priority Rush',
    code: 'SCN-02',
    timeWindow: '08:00 - 09:30 MORNING',
    description: 'High-frequency rapid transit coordination with arterial corridor cross-street balancing.',
    agencies: {
      traffic: {
        kpis: [
          { label: 'Corridor Flow Gain', value: 21.2, suffix: '%', description: 'Coordinated wave progress' },
          { label: 'Downstream Queue', value: 19.8, prefix: '-', suffix: '%', description: 'Bottleneck clearance' }
        ],
        advisoryTitle: 'Transit Wave Progression Hold',
        urgency: 'HIGH',
        recommendation: 'Hold downstream signal green window for 8s to establish bidirectional progression.',
        impact: 'Prevents platoon stranding across intermediate arterial cross-streets.',
        statusPill: 'GREEN WAVE ACTIVE'
      },
      energy: {
        kpis: [
          { label: 'Peak Demand Shaved', value: 240, suffix: ' kW', description: 'Substation load balancing' },
          { label: 'Contract Cap Breaches', value: 0, suffix: '%', description: 'Contract buffer maintained' }
        ],
        advisoryTitle: 'Substation Thermal Storage Shift',
        urgency: 'OPTIMIZATION',
        recommendation: 'Shift primary district chilled water pumps to storage reservoir circuit.',
        impact: 'Stabilizes commercial grid draw during morning elevator bank startup.',
        statusPill: 'THERMAL STORAGE SYNCED'
      },
      transit: {
        kpis: [
          { label: 'Headway Adherence', value: 97.8, suffix: '%', description: 'Peak schedule accuracy' },
          { label: 'Crossing Delay', value: 28.4, prefix: '-', suffix: '%', description: 'Rapid bus preemption' }
        ],
        advisoryTitle: 'Platoon Preemption Authorization',
        urgency: 'HIGH',
        recommendation: 'Preempt westbound signal cycle for approaching two-bus rapid transit platoon.',
        impact: 'Saves 3.4 minutes transit passenger trip duration per corridor run.',
        statusPill: 'PREEMPTION AUTHORIZED'
      },
      governance: {
        kpis: [
          { label: 'Telemetry Checked', value: 100, suffix: '%', description: 'Hard speed bounds 0-120' },
          { label: 'Auto-Actuations', value: 0, suffix: '', description: 'Human operator certified' }
        ],
        advisoryTitle: 'Preemption Safety Logging',
        urgency: 'OPTIMIZATION',
        recommendation: 'Audit transit transponder timestamps against signal controller phase transitions.',
        impact: 'Verifies safety clearance minimums were strictly respected during preemption.',
        statusPill: 'SAFETY AUDITED'
      }
    }
  },
  {
    id: 'grid-strain',
    name: 'District Grid Curtailment Event',
    code: 'SCN-03',
    timeWindow: '14:00 - 15:30 MIDDAY',
    description: 'Municipal utility demand-response event triggering coordinated commercial load curtailment.',
    agencies: {
      traffic: {
        kpis: [
          { label: 'Corridor Flow Gain', value: 15.6, suffix: '%', description: 'Steady hydrodynamic state' },
          { label: 'Downstream Queue', value: 17.2, prefix: '-', suffix: '%', description: 'Spillback prevention' }
        ],
        advisoryTitle: 'Signal Cadence Micro-Adjust',
        urgency: 'MEDIUM',
        recommendation: 'Trim north-south pedestrian lead interval by 2s to preserve arterial cycle momentum.',
        impact: 'Maintains steady flow while commercial district operates under curtailment.',
        statusPill: 'CADENCE STABLE'
      },
      energy: {
        kpis: [
          { label: 'Peak Demand Shaved', value: 520, suffix: ' kW', description: 'Demand response execution' },
          { label: 'Contract Cap Breaches', value: 0, suffix: '%', description: 'Avoided peak tier penalty' }
        ],
        advisoryTitle: 'Deep Demand Response Curtailment',
        urgency: 'HIGH',
        recommendation: 'Ramp down commercial chiller bank 1 and deploy district battery storage buffer.',
        impact: 'Sheds 520 kW electrical demand to protect municipal feeder substation.',
        statusPill: 'DEMAND RESPONSE ACTIVE'
      },
      transit: {
        kpis: [
          { label: 'Headway Adherence', value: 95.1, suffix: '%', description: 'Midday schedule accuracy' },
          { label: 'Crossing Delay', value: 14.8, prefix: '-', suffix: '%', description: 'Approach clearance' }
        ],
        advisoryTitle: 'Corridor Transit Fleet Balancing',
        urgency: 'OPTIMIZATION',
        recommendation: 'Maintain standard transit dwell times at mid-corridor intermodal stations.',
        impact: 'Preserves consistent passenger throughput during electrical grid curtailment.',
        statusPill: 'FLEET SYNCHRONIZED'
      },
      governance: {
        kpis: [
          { label: 'Telemetry Checked', value: 100, suffix: '%', description: 'Fiscal meters validated' },
          { label: 'Auto-Actuations', value: 0, suffix: '', description: 'Operator approval verified' }
        ],
        advisoryTitle: 'Tariff Audit Trail Generation',
        urgency: 'OPTIMIZATION',
        recommendation: 'Compile cryptographic proof of load reduction for utility capacity credit settlement.',
        impact: 'Guarantees municipal credit verification with immutable 15-minute intervals.',
        statusPill: 'CREDIT AUDIT READY'
      }
    }
  }
];

export const AgencyCommandShowcase: React.FC = () => {
  const [activeScenarioId, setActiveScenarioId] = useState<string>('peak-ingress');

  const currentScenario = SCENARIOS.find((s) => s.id === activeScenarioId) || SCENARIOS[0];

  return (
    <section id="operations" className="landing-section agency-matrix-section">
      <div className="section-header">
        <span className="section-eyebrow font-mono">Multi-Agency Collaboration</span>
        <h2 className="section-title">One corridor twin across four municipal commands</h2>
        <p className="section-subtitle">
          Break departmental silos. Synchronize traffic engineers, energy managers, transit coordinators, and audit commissions on a unified system of record.
        </p>
      </div>

      {/* Synchronized Multi-Agency Operations Deck */}
      <div className="agency-matrix-deck">
        {/* Top Scenario Synchronizer Bar */}
        <div className="scenario-synchronizer-bar">
          <div className="synchronizer-info">
            <div className="sync-status-row font-mono">
              <span className="pulse-indicator" style={{ background: 'var(--color-success)' }} />
              <span className="sync-status-title">CROSS-AGENCY SYNCHRONIZATION BUS</span>
              <span className="sync-pill font-mono">{currentScenario.timeWindow}</span>
            </div>
            <p className="synchronizer-desc">{currentScenario.description}</p>
          </div>

          <div className="scenario-selector-pills font-mono" role="tablist" aria-label="Operational Scenarios">
            {SCENARIOS.map((sc) => {
              const isSelected = sc.id === activeScenarioId;
              return (
                <button
                  key={sc.id}
                  type="button"
                  role="tab"
                  aria-selected={isSelected}
                  className={`scenario-pill-btn ${isSelected ? 'active' : ''}`}
                  onClick={() => setActiveScenarioId(sc.id)}
                >
                  <Clock size={11} className="pill-icon" />
                  <span className="pill-code">{sc.code}</span>
                  <span className="pill-name">{sc.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 2x2 Coordinated Agency Command Matrix */}
        <div className="agency-quadrant-grid">
          {/* Quadrant 1: Traffic Operations Center */}
          <div className="agency-quadrant-card traffic-quadrant">
            <div className="quadrant-topbar">
              <div className="quadrant-identity">
                <div className="quadrant-icon-box" style={{ background: 'rgba(56, 189, 248, 0.12)', borderColor: 'rgba(56, 189, 248, 0.35)' }}>
                  <Car size={17} color="#38BDF8" strokeWidth={2.2} />
                </div>
                <div>
                  <div className="agency-code-row font-mono">
                    <span className="agency-code-tag" style={{ color: '#38BDF8' }}>TMC-01</span>
                    <span className="agency-domain-label">TRAFFIC OPERATIONS</span>
                  </div>
                  <h3 className="agency-quadrant-title">Traffic Operations Center</h3>
                </div>
              </div>
              <span className="quadrant-status-badge font-mono" style={{ color: '#38BDF8', borderColor: 'rgba(56, 189, 248, 0.3)', background: 'rgba(56, 189, 248, 0.08)' }}>
                {currentScenario.agencies.traffic.statusPill}
              </span>
            </div>

            <div className="quadrant-body-split">
              <div className="quadrant-visual-frame">
                <img
                  src="/assets/images/twilight-city-highway-light-trails.png"
                  alt="Arterial Traffic Flow"
                  className="quadrant-visual-img"
                />
                <div className="visual-reticle top-left font-mono">+</div>
                <div className="visual-reticle top-right font-mono">+</div>
                <div className="visual-caption font-mono">
                  <Radio size={11} color="#38BDF8" />
                  <span>ARTERIAL RADAR & LOOPS</span>
                </div>
              </div>

              <div className="quadrant-metrics-column">
                {currentScenario.agencies.traffic.kpis.map((kpi, kIdx) => (
                  <div key={kIdx} className="quadrant-kpi-box">
                    <span className="quadrant-kpi-label font-mono">{kpi.label}</span>
                    <span className="quadrant-kpi-val font-mono" style={{ color: '#38BDF8' }}>
                      <NumberTicker
                        value={kpi.value}
                        decimals={kpi.value % 1 !== 0 ? 1 : 0}
                        prefix={kpi.prefix}
                        suffix={kpi.suffix}
                      />
                    </span>
                    <span className="quadrant-kpi-desc">{kpi.description}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="quadrant-advisory-panel">
              <div className="advisory-meta-line font-mono">
                <span className={`advisory-urgency-tag ${currentScenario.agencies.traffic.urgency.toLowerCase()}`}>
                  {currentScenario.agencies.traffic.urgency} ADVISORY
                </span>
                <span className="advisory-title-text">{currentScenario.agencies.traffic.advisoryTitle}</span>
              </div>
              <p className="advisory-action-statement">{currentScenario.agencies.traffic.recommendation}</p>
              <div className="advisory-impact-line">
                <CheckCircle2 size={13} color="var(--color-success)" className="impact-check-icon" />
                <span className="impact-statement-text">{currentScenario.agencies.traffic.impact}</span>
              </div>
            </div>

            <div className="quadrant-footer-bar font-mono">
              <ShieldCheck size={13} color="#10B981" />
              <span>DISPATCHED TO TMC OPERATOR : APPROVAL REQUIRED</span>
            </div>
          </div>

          {/* Quadrant 2: District Energy & Microgrid */}
          <div className="agency-quadrant-card energy-quadrant">
            <div className="quadrant-topbar">
              <div className="quadrant-identity">
                <div className="quadrant-icon-box" style={{ background: 'rgba(245, 158, 11, 0.12)', borderColor: 'rgba(245, 158, 11, 0.35)' }}>
                  <Zap size={17} color="#F59E0B" strokeWidth={2.2} />
                </div>
                <div>
                  <div className="agency-code-row font-mono">
                    <span className="agency-code-tag" style={{ color: '#F59E0B' }}>ENR-01</span>
                    <span className="agency-domain-label">DISTRICT MICROGRID</span>
                  </div>
                  <h3 className="agency-quadrant-title">Energy & Facilities Bureau</h3>
                </div>
              </div>
              <span className="quadrant-status-badge font-mono" style={{ color: '#F59E0B', borderColor: 'rgba(245, 158, 11, 0.3)', background: 'rgba(245, 158, 11, 0.08)' }}>
                {currentScenario.agencies.energy.statusPill}
              </span>
            </div>

            <div className="quadrant-body-split">
              <div className="quadrant-visual-frame">
                <img
                  src="/assets/images/tech-campus-substation-grid.png"
                  alt="District Substation & Microgrid"
                  className="quadrant-visual-img"
                />
                <div className="visual-reticle top-left font-mono">+</div>
                <div className="visual-reticle top-right font-mono">+</div>
                <div className="visual-caption font-mono">
                  <Radio size={11} color="#F59E0B" />
                  <span>DISTRICT 15-MIN METERS</span>
                </div>
              </div>

              <div className="quadrant-metrics-column">
                {currentScenario.agencies.energy.kpis.map((kpi, kIdx) => (
                  <div key={kIdx} className="quadrant-kpi-box">
                    <span className="quadrant-kpi-label font-mono">{kpi.label}</span>
                    <span className="quadrant-kpi-val font-mono" style={{ color: '#F59E0B' }}>
                      <NumberTicker
                        value={kpi.value}
                        decimals={kpi.value % 1 !== 0 ? 1 : 0}
                        prefix={kpi.prefix}
                        suffix={kpi.suffix}
                      />
                    </span>
                    <span className="quadrant-kpi-desc">{kpi.description}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="quadrant-advisory-panel">
              <div className="advisory-meta-line font-mono">
                <span className={`advisory-urgency-tag ${currentScenario.agencies.energy.urgency.toLowerCase()}`}>
                  {currentScenario.agencies.energy.urgency} ADVISORY
                </span>
                <span className="advisory-title-text">{currentScenario.agencies.energy.advisoryTitle}</span>
              </div>
              <p className="advisory-action-statement">{currentScenario.agencies.energy.recommendation}</p>
              <div className="advisory-impact-line">
                <CheckCircle2 size={13} color="var(--color-success)" className="impact-check-icon" />
                <span className="impact-statement-text">{currentScenario.agencies.energy.impact}</span>
              </div>
            </div>

            <div className="quadrant-footer-bar font-mono">
              <ShieldCheck size={13} color="#10B981" />
              <span>DISPATCHED TO ENERGY DESK : APPROVAL REQUIRED</span>
            </div>
          </div>

          {/* Quadrant 3: Multimodal Transit Authority */}
          <div className="agency-quadrant-card transit-quadrant">
            <div className="quadrant-topbar">
              <div className="quadrant-identity">
                <div className="quadrant-icon-box" style={{ background: 'rgba(16, 185, 129, 0.12)', borderColor: 'rgba(16, 185, 129, 0.35)' }}>
                  <Navigation size={17} color="#10B981" strokeWidth={2.2} />
                </div>
                <div>
                  <div className="agency-code-row font-mono">
                    <span className="agency-code-tag" style={{ color: '#10B981' }}>TRN-01</span>
                    <span className="agency-domain-label">MULTIMODAL TRANSIT</span>
                  </div>
                  <h3 className="agency-quadrant-title">Regional Transit Authority</h3>
                </div>
              </div>
              <span className="quadrant-status-badge font-mono" style={{ color: '#10B981', borderColor: 'rgba(16, 185, 129, 0.3)', background: 'rgba(16, 185, 129, 0.08)' }}>
                {currentScenario.agencies.transit.statusPill}
              </span>
            </div>

            <div className="quadrant-body-split">
              <div className="quadrant-visual-frame">
                <img
                  src="/assets/images/corridor-int-02-transit.png"
                  alt="Transit Corridor Fleet"
                  className="quadrant-visual-img"
                />
                <div className="visual-reticle top-left font-mono">+</div>
                <div className="visual-reticle top-right font-mono">+</div>
                <div className="visual-caption font-mono">
                  <Radio size={11} color="#10B981" />
                  <span>TRANSIT FLEET BEACONS</span>
                </div>
              </div>

              <div className="quadrant-metrics-column">
                {currentScenario.agencies.transit.kpis.map((kpi, kIdx) => (
                  <div key={kIdx} className="quadrant-kpi-box">
                    <span className="quadrant-kpi-label font-mono">{kpi.label}</span>
                    <span className="quadrant-kpi-val font-mono" style={{ color: '#10B981' }}>
                      <NumberTicker
                        value={kpi.value}
                        decimals={kpi.value % 1 !== 0 ? 1 : 0}
                        prefix={kpi.prefix}
                        suffix={kpi.suffix}
                      />
                    </span>
                    <span className="quadrant-kpi-desc">{kpi.description}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="quadrant-advisory-panel">
              <div className="advisory-meta-line font-mono">
                <span className={`advisory-urgency-tag ${currentScenario.agencies.transit.urgency.toLowerCase()}`}>
                  {currentScenario.agencies.transit.urgency} ADVISORY
                </span>
                <span className="advisory-title-text">{currentScenario.agencies.transit.advisoryTitle}</span>
              </div>
              <p className="advisory-action-statement">{currentScenario.agencies.transit.recommendation}</p>
              <div className="advisory-impact-line">
                <CheckCircle2 size={13} color="var(--color-success)" className="impact-check-icon" />
                <span className="impact-statement-text">{currentScenario.agencies.transit.impact}</span>
              </div>
            </div>

            <div className="quadrant-footer-bar font-mono">
              <ShieldCheck size={13} color="#10B981" />
              <span>DISPATCHED TO FLEET DESK : APPROVAL REQUIRED</span>
            </div>
          </div>

          {/* Quadrant 4: City Audit Commission */}
          <div className="agency-quadrant-card audit-quadrant">
            <div className="quadrant-topbar">
              <div className="quadrant-identity">
                <div className="quadrant-icon-box" style={{ background: 'rgba(129, 140, 248, 0.12)', borderColor: 'rgba(129, 140, 248, 0.35)' }}>
                  <ShieldCheck size={17} color="#818CF8" strokeWidth={2.2} />
                </div>
                <div>
                  <div className="agency-code-row font-mono">
                    <span className="agency-code-tag" style={{ color: '#818CF8' }}>AUD-01</span>
                    <span className="agency-domain-label">AUDIT OVERSIGHT</span>
                  </div>
                  <h3 className="agency-quadrant-title">City Audit Commission</h3>
                </div>
              </div>
              <span className="quadrant-status-badge font-mono" style={{ color: '#818CF8', borderColor: 'rgba(129, 140, 248, 0.3)', background: 'rgba(129, 140, 248, 0.08)' }}>
                {currentScenario.agencies.governance.statusPill}
              </span>
            </div>

            <div className="quadrant-body-split">
              <div className="quadrant-visual-frame">
                <img
                  src="/assets/images/cinematic-illuminated-urban-model.png"
                  alt="City Audit Ledger"
                  className="quadrant-visual-img"
                />
                <div className="visual-reticle top-left font-mono">+</div>
                <div className="visual-reticle top-right font-mono">+</div>
                <div className="visual-caption font-mono">
                  <Radio size={11} color="#818CF8" />
                  <span>AUTHORITATIVE AUDIT REPO</span>
                </div>
              </div>

              <div className="quadrant-metrics-column">
                {currentScenario.agencies.governance.kpis.map((kpi, kIdx) => (
                  <div key={kIdx} className="quadrant-kpi-box">
                    <span className="quadrant-kpi-label font-mono">{kpi.label}</span>
                    <span className="quadrant-kpi-val font-mono" style={{ color: '#818CF8' }}>
                      <NumberTicker
                        value={kpi.value}
                        decimals={kpi.value % 1 !== 0 ? 1 : 0}
                        prefix={kpi.prefix}
                        suffix={kpi.suffix}
                      />
                    </span>
                    <span className="quadrant-kpi-desc">{kpi.description}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="quadrant-advisory-panel">
              <div className="advisory-meta-line font-mono">
                <span className={`advisory-urgency-tag ${currentScenario.agencies.governance.urgency.toLowerCase()}`}>
                  {currentScenario.agencies.governance.urgency} ADVISORY
                </span>
                <span className="advisory-title-text">{currentScenario.agencies.governance.advisoryTitle}</span>
              </div>
              <p className="advisory-action-statement">{currentScenario.agencies.governance.recommendation}</p>
              <div className="advisory-impact-line">
                <CheckCircle2 size={13} color="var(--color-success)" className="impact-check-icon" />
                <span className="impact-statement-text">{currentScenario.agencies.governance.impact}</span>
              </div>
            </div>

            <div className="quadrant-footer-bar font-mono">
              <ShieldCheck size={13} color="#10B981" />
              <span>RECORDED IN TIMESCALEDB : ZERO PHYSICAL ACTUATION</span>
            </div>
          </div>
        </div>

        {/* Global Synchronized Data Bus Footer */}
        <div className="matrix-global-footer font-mono">
          <div className="footer-invariant-left">
            <Database size={13} color="var(--color-primary)" />
            <span>AUTHORITATIVE TIMESCALEDB BACKBONE : ALL 4 AGENCIES SYNCHRONIZED ON IDENTICAL PHYSICAL STATE</span>
          </div>
          <button
            type="button"
            className="matrix-audit-review-btn"
            onClick={() => {
              const el = document.getElementById('contact');
              if (el) el.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            <span>REVIEW FULL AUDIT LEDGER</span>
            <ArrowRight size={12} />
          </button>
        </div>
      </div>
    </section>
  );
};
