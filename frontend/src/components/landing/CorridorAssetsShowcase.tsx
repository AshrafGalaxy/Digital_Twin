import React, { useState } from 'react';
import {
  GitMerge,
  Navigation,
  Car,
  Zap,
  ShieldCheck,
  Layers,
  Radio,
  Eye,
  Cpu,
  Clock,
  Database,
  CheckCircle2
} from 'lucide-react';

export interface InfrastructureAsset {
  id: string;
  category: string;
  title: string;
  role: string;
  imageUrl: string;
  accentColor: string;
  icon: 'intersection' | 'transit' | 'corridor' | 'microgrid';
  scale: string;
  sensing: string;
  cadence: string;
  telemetryModalities: string[];
  triStateIsolation: {
    live: string;
    simulation: string;
    predicted: string;
  };
  decisionSupport: string;
}

export const INFRASTRUCTURE_ASSETS: InfrastructureAsset[] = [
  {
    id: 'INT-01',
    category: 'SIGNALIZED ARTERIAL JUNCTION',
    title: 'Coordinated Multi-Leg Intersection',
    role: 'Multi-phase signal coordination with real-time green split balancing, kinematic approach monitoring, and queue spillback suppression.',
    imageUrl: '/assets/images/corridor-int-01-gateway.png',
    accentColor: '#38BDF8',
    icon: 'intersection',
    scale: 'Multi-Approach Arterial Crossroad',
    sensing: 'Inductive Loops & Doppler Radar',
    cadence: '1 Hz Stream (<180s Freshness)',
    telemetryModalities: [
      'In-pavement inductive vehicle loops',
      'Virtual stop-line approach profilers',
      'Multi-directional Doppler radar'
    ],
    triStateIsolation: {
      live: 'Observed approach vehicle counts and phase timings stored immutably in live telemetry tables.',
      simulation: 'SUMO corridor green-wave experiments isolated in sandbox scenario runs.',
      predicted: '15-minute queue spillback forecasts calculated with conformal uncertainty bounds.'
    },
    decisionSupport: 'Generates green-split adjustment advisories to balance upstream arrival waves and prevent downstream crossroad gridlock.'
  },
  {
    id: 'TRN-01',
    category: 'TRANSIT INFRASTRUCTURE',
    title: 'Multimodal Transit Corridor Terminal',
    role: 'Dedicated transit right-of-way synchronization, dynamic signal preemption windowing, and passenger throughput preservation.',
    imageUrl: '/assets/images/corridor-int-02-transit.png',
    accentColor: '#10B981',
    icon: 'transit',
    scale: 'High-Volume Transit Arterial Link',
    sensing: 'Priority Beacons & Speed Profilers',
    cadence: 'Continuous & Event-Triggered',
    telemetryModalities: [
      'Dedicated transit transponder beacons',
      'Directional approach velocity radar',
      'Virtual queue dissipation sensors'
    ],
    triStateIsolation: {
      live: 'Transit vehicle headway observations recorded directly as ground-truth telemetry.',
      simulation: 'Alternative preemption and lane-restriction scenarios modeled without impacting live signals.',
      predicted: 'Travel-time reliability projections tagged with calibrated confidence intervals.'
    },
    decisionSupport: 'Advises signal priority extensions for approaching transit vehicles while pacing cross-street pedestrian clearance intervals.'
  },
  {
    id: 'SEG-01',
    category: 'ROADWAY ARTERIAL',
    title: 'High-Capacity Arterial Highway',
    role: 'Continuous hydrodynamic velocity profiling, spatial density calculation, and bottleneck shockwave dissipation across mainline lanes.',
    imageUrl: '/assets/images/corridor-seg-02-westbound.png',
    accentColor: '#818CF8',
    icon: 'corridor',
    scale: 'Multi-Lane Express Arterial',
    sensing: 'Pavement Sensors & Spatial Arrays',
    cadence: '30s Rolling Windows',
    telemetryModalities: [
      'Sequential in-pavement loop arrays',
      'Continuous velocity radar stations',
      'Ambient weather and surface sensors'
    ],
    triStateIsolation: {
      live: 'Lane velocities clamped between 0 and 120 km/h and logged to PostgreSQL time-series tables.',
      simulation: 'Microscopic shockwave simulations evaluated strictly within isolated scenario schemas.',
      predicted: 'Multi-horizon corridor velocity forecasts paired with TreeSHAP feature attributions.'
    },
    decisionSupport: 'Recommends dynamic variable advisory speeds and ramp metering paces before physical queue shockwaves materialize.'
  },
  {
    id: 'BLD-01',
    category: 'DISTRICT MICROGRID',
    title: 'Commercial Facility Microgrid',
    role: 'High-capacity commercial building energy twin modeling, HVAC chiller plant pre-cooling scheduling, and regional peak tariff avoidance.',
    imageUrl: '/assets/images/twilight-glass-corporate-complex.png',
    accentColor: '#F59E0B',
    icon: 'microgrid',
    scale: 'Multi-Zone Commercial Complex',
    sensing: 'Fiscal Ingress & Chiller Sub-Meters',
    cadence: '15-Min Fiscal Intervals',
    telemetryModalities: [
      'Primary electrical grid ingress meters',
      '3-phase chiller plant sub-metering arrays',
      'Zonal indoor & outdoor ambient thermal probes'
    ],
    triStateIsolation: {
      live: 'Utility billing pulses and electrical loads committed as authoritative ground-truth measurements.',
      simulation: 'Thermodynamic building cooling simulations isolated from operational metering.',
      predicted: 'Peak demand forecasts projected with conformal bounds to avert contract demand penalties.'
    },
    decisionSupport: 'Recommends 15-minute predictive chiller pre-cooling dispatches to shave high-cost electrical peak demand periods.'
  }
];

export const CorridorAssetsShowcase: React.FC = () => {
  const [selectedId, setSelectedId] = useState<string>('INT-01');
  const [viewMode, setViewMode] = useState<'visual' | 'telemetry'>('visual');
  const [imgErrorMap, setImgErrorMap] = useState<Record<string, boolean>>({});

  const activeAsset = INFRASTRUCTURE_ASSETS.find((a) => a.id === selectedId) || INFRASTRUCTURE_ASSETS[0];

  const renderIcon = (type: InfrastructureAsset['icon'], color: string) => {
    switch (type) {
      case 'intersection':
        return <GitMerge size={16} color={color} />;
      case 'transit':
        return <Navigation size={16} color={color} />;
      case 'corridor':
        return <Car size={16} color={color} />;
      case 'microgrid':
        return <Zap size={16} color={color} />;
      default:
        return <Layers size={16} color={color} />;
    }
  };

  return (
    <section id="assets-showcase" className="landing-section assets-showcase-section">
      <div className="section-header">
        <span className="section-eyebrow">Physical-to-Digital Mapping</span>
        <h2 className="section-title">Multi-asset urban infrastructure network</h2>
        <p className="section-subtitle">
          Synchronize heterogeneous urban physical infrastructure into an authoritative digital twin with strict mathematical provenance and zero autonomous field actuation.
        </p>
      </div>

      {/* Asset Navigation Selector */}
      <div className="infrastructure-nav-grid" role="tablist" aria-label="Infrastructure Assets">
        {INFRASTRUCTURE_ASSETS.map((asset) => {
          const isActive = selectedId === asset.id;
          return (
            <button
              key={asset.id}
              role="tab"
              aria-selected={isActive}
              className={`infrastructure-nav-card ${isActive ? 'active' : ''}`}
              onClick={() => setSelectedId(asset.id)}
              style={{
                borderColor: isActive ? asset.accentColor : undefined
              }}
            >
              <div
                className="nav-card-icon-badge"
                style={{
                  background: isActive ? `${asset.accentColor}18` : 'rgba(255, 255, 255, 0.03)',
                  borderColor: isActive ? `${asset.accentColor}40` : 'rgba(255, 255, 255, 0.08)'
                }}
              >
                {renderIcon(asset.icon, isActive ? asset.accentColor : '#8B949E')}
              </div>
              <div className="nav-card-text">
                <div className="nav-card-top">
                  <span
                    className="nav-card-id font-mono"
                    style={{ color: isActive ? asset.accentColor : '#8B949E' }}
                  >
                    {asset.id}
                  </span>
                  <span className="nav-card-category font-mono">{asset.category.split(' ')[0]}</span>
                </div>
                <span className="nav-card-title">{asset.title}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Main Asset Showcase Stage */}
      <div className="infrastructure-stage-panel">
        {/* Left Column: Visual Twin Photographic Frame */}
        <div className="stage-visual-column">
          <div className="visual-column-topbar">
            <div className="visual-topbar-left">
              <span className="pulse-indicator" style={{ background: activeAsset.accentColor }} />
              <span className="topbar-entity-id font-mono">
                TWIN ENTITY: {activeAsset.id}
              </span>
            </div>
            <div className="visual-mode-toggle">
              <button
                type="button"
                className={`toggle-option-btn ${viewMode === 'visual' ? 'active' : ''}`}
                onClick={() => setViewMode('visual')}
              >
                <Eye size={12} />
                <span>PHOTOGRAPHIC</span>
              </button>
              <button
                type="button"
                className={`toggle-option-btn ${viewMode === 'telemetry' ? 'active' : ''}`}
                onClick={() => setViewMode('telemetry')}
              >
                <Radio size={12} />
                <span>TELEMETRY</span>
              </button>
            </div>
          </div>

          <div className="visual-display-body">
            {viewMode === 'visual' && !imgErrorMap[activeAsset.id] ? (
              <div className="photographic-view-wrap">
                <img
                  src={activeAsset.imageUrl}
                  alt={activeAsset.title}
                  className="photographic-image"
                  onError={() => setImgErrorMap((prev) => ({ ...prev, [activeAsset.id]: true }))}
                />
                <div className="photographic-overlay" aria-hidden="true" />
                <div className="photographic-status-chip font-mono">
                  <span className="status-live-dot" />
                  <span>SYSTEM OF RECORD: POSTGRESQL</span>
                </div>
                <div className="photographic-cadence-chip font-mono">
                  <Clock size={11} />
                  <span>CADENCE: {activeAsset.cadence}</span>
                </div>
              </div>
            ) : (
              <div className="telemetry-view-wrap">
                <div className="telemetry-view-header">
                  <span className="telemetry-header-title font-mono">
                    VERIFIED SENSOR CHANNELS
                  </span>
                  <span className="telemetry-header-status font-mono">STATUS: HEALTHY</span>
                </div>
                <div className="telemetry-channels-list">
                  {activeAsset.telemetryModalities.map((sensor, idx) => (
                    <div key={idx} className="telemetry-channel-item">
                      <div className="channel-icon-wrap">
                        <Cpu size={14} color={activeAsset.accentColor} />
                      </div>
                      <div className="channel-info">
                        <span className="channel-name">{sensor}</span>
                        <span className="channel-status font-mono">
                          BOUNDS CHECKED • TIMESTAMP ORDERED • 100% INGESTION
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="telemetry-footer-note font-mono">
                  <ShieldCheck size={12} color="var(--color-success)" />
                  <span>Observed values exceeding freshness threshold automatically flag as STALE.</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Specifications, Tri-State Isolation & Decision Support */}
        <div className="stage-spec-column">
          {/* Header */}
          <div className="spec-column-header">
            <div className="spec-badges-row">
              <span
                className="spec-category-badge font-mono"
                style={{
                  color: activeAsset.accentColor,
                  background: `${activeAsset.accentColor}15`,
                  borderColor: `${activeAsset.accentColor}35`
                }}
              >
                {activeAsset.category}
              </span>
              <span className="spec-online-indicator font-mono">
                <span className="pulse-indicator" style={{ background: 'var(--color-success)' }} />
                <span>DECISION-SUPPORT READY</span>
              </span>
            </div>
            <h3 className="spec-asset-title">{activeAsset.title}</h3>
            <p className="spec-asset-role">{activeAsset.role}</p>
          </div>

          {/* Key Infrastructure Attributes */}
          <div className="spec-attributes-grid">
            <div className="spec-attr-card">
              <span className="attr-label font-mono">PHYSICAL DOMAIN</span>
              <span className="attr-value">{activeAsset.scale}</span>
            </div>
            <div className="spec-attr-card">
              <span className="attr-label font-mono">SENSOR SUITE</span>
              <span className="attr-value">{activeAsset.sensing}</span>
            </div>
            <div className="spec-attr-card">
              <span className="attr-label font-mono">TELEMETRY CADENCE</span>
              <span className="attr-value font-mono" style={{ color: activeAsset.accentColor }}>
                {activeAsset.cadence}
              </span>
            </div>
          </div>

          {/* Tri-State Architecture Separation Guarantee */}
          <div className="tri-state-card">
            <div className="tri-state-header font-mono">
              <Database size={13} color="var(--color-primary)" />
              <span>TRI-STATE ARCHITECTURAL ISOLATION CONTRACT</span>
            </div>
            <div className="tri-state-list">
              <div className="tri-state-item">
                <span className="tri-badge live font-mono">OBSERVED</span>
                <p className="tri-desc">{activeAsset.triStateIsolation.live}</p>
              </div>
              <div className="tri-state-item">
                <span className="tri-badge simulation font-mono">SIMULATION</span>
                <p className="tri-desc">{activeAsset.triStateIsolation.simulation}</p>
              </div>
              <div className="tri-state-item">
                <span className="tri-badge predicted font-mono">PREDICTED</span>
                <p className="tri-desc">{activeAsset.triStateIsolation.predicted}</p>
              </div>
            </div>
          </div>

          {/* Decision Support Application */}
          <div className="spec-decision-card">
            <div className="decision-header font-mono">
              <CheckCircle2 size={14} color="var(--color-success)" />
              <span>HUMAN-IN-THE-LOOP ADVISORY SCOPE</span>
            </div>
            <p className="decision-body">{activeAsset.decisionSupport}</p>
          </div>
        </div>
      </div>
    </section>
  );
};
