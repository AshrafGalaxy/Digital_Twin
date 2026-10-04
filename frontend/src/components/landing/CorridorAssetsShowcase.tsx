import React, { useState, useEffect } from 'react';
import {
  Waypoints,
  TrainFront,
  Route,
  Building2,
  ShieldCheck,
  Radio,
  Eye,
  Cpu,
  Clock,
  Database,
  CheckCircle2,
  Play,
  Pause,
  Layers
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
    role: 'Multi-phase signal progression, queue spillback monitoring, and dynamic arrival split balancing.',
    imageUrl: '/assets/images/corridor-int-01-gateway.png',
    accentColor: '#38BDF8',
    icon: 'intersection',
    scale: 'Arterial Junction',
    sensing: 'Loops & Radar',
    cadence: '1 Hz Real-Time',
    telemetryModalities: [
      'In-pavement inductive vehicle loops',
      'Virtual stop-line approach profilers',
      'Multi-directional Doppler radar'
    ],
    triStateIsolation: {
      live: 'Approach counts and signal phases stored immutably in TimescaleDB.',
      simulation: 'SUMO green-wave experiments isolated in sandbox scenario schemas.',
      predicted: '15-minute queue spillback forecasts bounded by conformal intervals.'
    },
    decisionSupport: 'Advises green-split adjustments to balance upstream arrivals and prevent crossroad gridlock.'
  },
  {
    id: 'TRN-01',
    category: 'TRANSIT INFRASTRUCTURE',
    title: 'Multimodal Transit Corridor Terminal',
    role: 'Dedicated transit right-of-way synchronization, headway reliability tracking, and signal preemption windowing.',
    imageUrl: '/assets/images/corridor-int-02-transit.png',
    accentColor: '#10B981',
    icon: 'transit',
    scale: 'Transit Link',
    sensing: 'Transit Beacons',
    cadence: 'Event-Triggered',
    telemetryModalities: [
      'Dedicated transit transponder beacons',
      'Directional approach velocity radar',
      'Virtual queue dissipation sensors'
    ],
    triStateIsolation: {
      live: 'Vehicle headway and transponder observations logged as ground truth.',
      simulation: 'Transit preemption trade-off experiments isolated in sandboxes.',
      predicted: 'Travel-time reliability projections calibrated with conformal bands.'
    },
    decisionSupport: 'Advises signal priority extensions for approaching transit vehicles during peak periods.'
  },
  {
    id: 'SEG-01',
    category: 'ROADWAY ARTERIAL',
    title: 'High-Capacity Arterial Highway',
    role: 'Continuous hydrodynamic velocity profiling, spatial density tracking, and bottleneck shockwave dissipation.',
    imageUrl: '/assets/images/corridor-seg-02-westbound.png',
    accentColor: '#818CF8',
    icon: 'corridor',
    scale: 'Express Arterial',
    sensing: 'Pavement Sensors',
    cadence: '30s Rolling',
    telemetryModalities: [
      'Sequential in-pavement loop arrays',
      'Continuous velocity radar stations',
      'Ambient weather and surface sensors'
    ],
    triStateIsolation: {
      live: 'Lane velocities clamped between 0 and 120 km/h and logged immutably.',
      simulation: 'Microscopic shockwave models evaluated in isolated run schemas.',
      predicted: 'Multi-horizon speed forecasts paired with TreeSHAP attributions.'
    },
    decisionSupport: 'Recommends dynamic variable advisory speeds before physical queue shockwaves form.'
  },
  {
    id: 'BLD-01',
    category: 'DISTRICT MICROGRID',
    title: 'Commercial Facility Microgrid',
    role: 'Commercial facility energy twin modeling, HVAC chiller pre-cooling dispatches, and peak tariff avoidance.',
    imageUrl: '/assets/images/twilight-glass-corporate-complex.png',
    accentColor: '#F59E0B',
    icon: 'microgrid',
    scale: 'District Microgrid',
    sensing: 'Fiscal Meters',
    cadence: '15-Min Intervals',
    telemetryModalities: [
      'Primary electrical grid ingress meters',
      '3-phase chiller plant sub-metering arrays',
      'Zonal indoor and outdoor ambient thermal probes'
    ],
    triStateIsolation: {
      live: 'Utility billing pulses and electrical loads committed as ground truth.',
      simulation: 'Thermodynamic cooling simulations isolated from operational metering.',
      predicted: 'Peak demand forecasts bounded by conformal intervals to avert penalties.'
    },
    decisionSupport: 'Recommends 15-minute predictive chiller pre-cooling dispatches to shave peak charges.'
  }
];

export const CorridorAssetsShowcase: React.FC = () => {
  const [selectedId, setSelectedId] = useState<string>('INT-01');
  const [viewMode, setViewMode] = useState<'visual' | 'telemetry'>('visual');
  const [imgErrorMap, setImgErrorMap] = useState<Record<string, boolean>>({});
  const [isAutoCycling, setIsAutoCycling] = useState<boolean>(true);
  const [progress, setProgress] = useState<number>(0);

  // Smooth, deterministic auto-cycle: 5000ms duration per slide, updated at 50ms ticks
  useEffect(() => {
    if (!isAutoCycling) return;

    const intervalMs = 50;
    const totalDurationMs = 5000;
    const step = (intervalMs / totalDurationMs) * 100;

    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev + step >= 100) {
          setSelectedId((currentId) => {
            const currentIndex = INFRASTRUCTURE_ASSETS.findIndex((a) => a.id === currentId);
            const nextIndex = (currentIndex + 1) % INFRASTRUCTURE_ASSETS.length;
            return INFRASTRUCTURE_ASSETS[nextIndex].id;
          });
          return 0;
        }
        return prev + step;
      });
    }, intervalMs);

    return () => clearInterval(timer);
  }, [isAutoCycling]);

  const handleSelectAsset = (id: string) => {
    setSelectedId(id);
    setProgress(0);
  };

  const toggleAutoCycling = () => {
    setIsAutoCycling((prev) => !prev);
  };

  const activeAsset = INFRASTRUCTURE_ASSETS.find((a) => a.id === selectedId) || INFRASTRUCTURE_ASSETS[0];

  const renderIcon = (type: InfrastructureAsset['icon'], color: string) => {
    switch (type) {
      case 'intersection':
        return <Waypoints size={20} strokeWidth={2.2} color={color} />;
      case 'transit':
        return <TrainFront size={20} strokeWidth={2.2} color={color} />;
      case 'corridor':
        return <Route size={20} strokeWidth={2.2} color={color} />;
      case 'microgrid':
        return <Building2 size={20} strokeWidth={2.2} color={color} />;
      default:
        return <Layers size={20} strokeWidth={2.2} color={color} />;
    }
  };

  return (
    <section id="assets-showcase" className="landing-section assets-showcase-section">
      <div className="section-header">
        <span className="section-eyebrow font-mono">Physical-to-Digital Mapping</span>
        <h2 className="section-title">Multi-asset urban infrastructure network</h2>
        <p className="section-subtitle">
          Synchronize heterogeneous urban physical infrastructure into an authoritative digital twin with strict mathematical provenance and zero autonomous field actuation.
        </p>
      </div>

      {/* Sleek Minimalist Controls Row */}
      <div className="showcase-controls-bar">
        <button
          type="button"
          className={`cycle-control-btn ${isAutoCycling ? 'active' : ''}`}
          onClick={toggleAutoCycling}
          aria-label={isAutoCycling ? 'Pause automated rotation' : 'Resume automated rotation'}
          title={isAutoCycling ? 'Pause automated rotation' : 'Resume automated rotation'}
        >
          {isAutoCycling ? <Pause size={13} /> : <Play size={13} />}
        </button>
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
              onClick={() => handleSelectAsset(asset.id)}
            >
              <div className="nav-card-inner">
                <div
                  className="nav-card-icon-badge"
                  style={{
                    color: isActive ? asset.accentColor : '#94A3B8',
                    background: isActive ? `${asset.accentColor}18` : 'rgba(255, 255, 255, 0.03)',
                    borderColor: isActive ? `${asset.accentColor}45` : 'rgba(255, 255, 255, 0.08)'
                  }}
                >
                  {renderIcon(asset.icon, isActive ? asset.accentColor : '#94A3B8')}
                </div>
                <div className="nav-card-text">
                  <div className="nav-card-top-row">
                    <span
                      className="nav-card-id font-mono"
                      style={{ color: isActive ? asset.accentColor : '#64748B' }}
                    >
                      {asset.id}
                    </span>
                    <span className="nav-card-category font-mono">
                      {asset.category.split(' ')[0]}
                    </span>
                  </div>
                  <span className="nav-card-title">{asset.title}</span>
                </div>
              </div>

              {/* Recessed Progress Bar with matching rounded bottom corners */}
              <div className="nav-card-progress-track">
                <div
                  className="nav-card-progress-fill"
                  style={{
                    width: isActive ? `${progress}%` : '0%',
                    background: asset.accentColor,
                    boxShadow: `0 0 10px ${asset.accentColor}`
                  }}
                />
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
              <div className="photographic-view-wrap" key={activeAsset.id}>
                <img
                  src={activeAsset.imageUrl}
                  alt={activeAsset.title}
                  className="photographic-image"
                  onError={() => setImgErrorMap((prev) => ({ ...prev, [activeAsset.id]: true }))}
                />
                <div className="photographic-overlay" aria-hidden="true" />
                <div className="photographic-hud-reticle top-left font-mono">+</div>
                <div className="photographic-hud-reticle top-right font-mono">+</div>
                <div className="photographic-hud-reticle bottom-left font-mono">+</div>
                <div className="photographic-hud-reticle bottom-right font-mono">+</div>

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
              <div className="telemetry-view-wrap" key={`${activeAsset.id}-telem`}>
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
