import React, { useState } from 'react';
import { MapPin, Cpu, Zap, Car, ShieldCheck, Layers } from 'lucide-react';

export interface AssetDetail {
  id: string;
  name: string;
  shortName?: string;
  imageUrl?: string;
  category: 'intersection' | 'segment' | 'building';
  categoryLabel: string;
  location: string;
  geometry: string;
  capacity: string;
  sensors: string[];
  decisionSupport: string;
  accentColor: string;
}

export const DEFAULT_CORRIDOR_ASSETS: AssetDetail[] = [
  {
    id: 'INT-01',
    name: 'Primary Arterial Gateway Junction',
    shortName: 'Gateway Junction',
    imageUrl: '/assets/images/corridor-int-01-gateway.png',
    category: 'intersection',
    categoryLabel: 'SIGNALIZED INTERSECTION',
    location: 'Western Arterial Ingress / Multimodal Crossroad Node',
    geometry: '4 Approach Legs • 12 Coordinated Phase Actuation',
    capacity: '4,200 PCU / hr Peak Throughput',
    sensors: ['8 Inductive In-Pavement Loops', 'Virtual Stop-Line Profilers', 'Multi-Leg Approach Radar'],
    decisionSupport: 'Automated green-split reallocation during downstream queue spillback.',
    accentColor: '#38BDF8'
  },
  {
    id: 'INT-02',
    name: 'Eastern Transit Terminal Junction',
    shortName: 'Transit Junction',
    imageUrl: '/assets/images/corridor-int-02-transit.png',
    category: 'intersection',
    categoryLabel: 'SIGNALIZED INTERSECTION',
    location: 'Eastern Arterial Flank / Transit Corridor Crossing',
    geometry: '3 Approach Legs • Transit Priority Dedicated Phase',
    capacity: '3,600 PCU / hr Peak Throughput',
    sensors: ['6 Directional Loop Arrays', 'Transit Priority Beacons', 'Continuous Velocity Radar'],
    decisionSupport: 'Dynamic queue dissipation pacing to prevent arterial gridlock back-propagation.',
    accentColor: '#10B981'
  },
  {
    id: 'SEG-01',
    name: 'Eastbound Arterial Mainline',
    shortName: 'Eastbound Corridor',
    imageUrl: '/assets/images/twilight-city-highway-light-trails.png',
    category: 'segment',
    categoryLabel: 'ARTERIAL ROADWAY SEGMENT',
    location: 'Western Gateway → Eastern Terminal (Eastbound Vector)',
    geometry: '3 Main Travel Lanes + Dedicated Service Flank',
    capacity: 'Design Velocity: 50 km/h • 2,400 veh/hr Free Flow',
    sensors: ['3 Sequential Loop Stations', 'Microscopic Kinematics Tracker', 'Arterial Radar Array'],
    decisionSupport: 'Conformal velocity forecast alerts identifying pre-congestion queue formation.',
    accentColor: '#58A6FF'
  },
  {
    id: 'SEG-02',
    name: 'Westbound Arterial Mainline',
    shortName: 'Westbound Corridor',
    imageUrl: '/assets/images/corridor-seg-02-westbound.png',
    category: 'segment',
    categoryLabel: 'ARTERIAL ROADWAY SEGMENT',
    location: 'Eastern Terminal → Western Gateway (Westbound Vector)',
    geometry: '3 Main Travel Lanes + Ingress Deceleration Buffer',
    capacity: 'Design Velocity: 50 km/h • Peak Surge: 3,100 veh/hr',
    sensors: ['Commercial Turning Ingress Loop Arrays', 'Deceleration Buffer Stations', 'Queue Spillback Monitor'],
    decisionSupport: 'Facility ingress buffer pacing during weekend commercial activity surges.',
    accentColor: '#818CF8'
  },
  {
    id: 'FAC-01',
    name: 'Central Commercial Microgrid Facility',
    shortName: 'Commercial Microgrid',
    imageUrl: '/assets/images/twilight-glass-corporate-complex.png',
    category: 'building',
    categoryLabel: 'COMMERCIAL FACILITY',
    location: 'Central Corridor Commercial Infrastructure Zone',
    geometry: '5 Commercial Levels • 120,000 m² Conditioned Footprint',
    capacity: 'Peak Electrical Demand: 4,862 kW • Contract Cap: 5,200 kW',
    sensors: ['Primary 11kV Grid Ingress Meter', 'Chiller Sub-Metering Plant (3 Units)', 'Zonal HVAC Thermal Telemetry'],
    decisionSupport: 'Automated 15-minute chiller pre-cooling advisory shaving 380 kW during peak tariff hours.',
    accentColor: '#F59E0B'
  }
];

export interface CorridorAssetsShowcaseProps {
  assets?: AssetDetail[];
  initialAssetId?: string;
  title?: string;
  subtitle?: string;
}

export const CorridorAssetsShowcase: React.FC<CorridorAssetsShowcaseProps> = ({
  assets = DEFAULT_CORRIDOR_ASSETS,
  initialAssetId,
  title = 'Authoritative Physical Corridor Model',
  subtitle = 'Direct physical twin mappings for signalized intersections, arterial travel segments, and commercial energy infrastructure across the multimodal corridor.'
}) => {
  const [selectedId, setSelectedId] = useState<string>(() => {
    if (initialAssetId && assets.some((a) => a.id === initialAssetId)) {
      return initialAssetId;
    }
    return assets[0]?.id || '';
  });

  const [viewMode, setViewMode] = useState<'visual' | 'blueprint'>('visual');
  const [imgErrorMap, setImgErrorMap] = useState<Record<string, boolean>>({});

  const activeAsset = assets.find((a) => a.id === selectedId) || assets[0];

  if (!activeAsset) {
    return null;
  }

  const renderAssetBlueprint = (asset: AssetDetail) => {
    const { category, accentColor, id, name, geometry, capacity, sensors } = asset;

    if (category === 'intersection') {
      const approachMatch = geometry.match(/(\d+)\s*Approach/i);
      const isFourWay = approachMatch ? parseInt(approachMatch[1], 10) >= 4 : true;

      return (
        <svg viewBox="0 0 460 260" className="showcase-blueprint-svg" xmlns="http://www.w3.org/2000/svg" style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}>
          <defs>
            <radialGradient id={`glow-${id}`} cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor={accentColor} stopOpacity="0.15" />
              <stop offset="100%" stopColor={accentColor} stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Clean Dark Canvas Bed */}
          <rect width="460" height="260" fill="#07070A" />
          <circle cx="230" cy="125" r="110" fill={`url(#glow-${id})`} pointerEvents="none" />

          {/* East-West Arterial Roadbed */}
          <rect x="24" y="95" width="412" height="60" rx="6" fill="#101014" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" />
          <line x1="24" y1="125" x2="436" y2="125" stroke="rgba(255, 255, 255, 0.15)" strokeWidth="1.2" strokeDasharray="8 6" />

          {/* North-South Crossroad Leg(s) */}
          {isFourWay ? (
            <>
              <rect x="200" y="16" width="60" height="218" rx="6" fill="#101014" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" />
              <line x1="230" y1="16" x2="230" y2="234" stroke="rgba(255, 255, 255, 0.15)" strokeWidth="1.2" strokeDasharray="8 6" />
            </>
          ) : (
            <>
              <rect x="200" y="95" width="60" height="139" rx="6" fill="#101014" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" />
              <line x1="230" y1="125" x2="230" y2="234" stroke="rgba(255, 255, 255, 0.15)" strokeWidth="1.2" strokeDasharray="8 6" />
            </>
          )}

          {/* Intersection Box */}
          <rect x="200" y="95" width="60" height="60" fill="#15151B" stroke={accentColor} strokeWidth="1.2" />

          {/* Signal Indicator Beacons */}
          <circle cx="194" cy="90" r="3.5" fill="#10B981" />
          <circle cx="266" cy="90" r="3.5" fill="#EF4444" />
          <circle cx="194" cy="160" r="3.5" fill="#EF4444" />
          <circle cx="266" cy="160" r="3.5" fill="#10B981" />

          {/* Controller Node Center Hub */}
          <circle cx="230" cy="125" r="28" fill="none" stroke={accentColor} strokeWidth="1" opacity="0.3" strokeDasharray="3 3" />
          <circle cx="230" cy="125" r="14" fill="none" stroke={accentColor} strokeWidth="1.5" opacity="0.6" />
          <circle cx="230" cy="125" r="5" fill={accentColor} />

          {/* Top Identifier Header */}
          <g transform="translate(28, 24)">
            <text x="0" y="12" fill={accentColor} fontSize="11" fontWeight="600" letterSpacing="0.04em">
              {id} • {name.toUpperCase()}
            </text>
          </g>

          {/* Bottom Telemetry HUD */}
          <g transform="translate(28, 226)">
            <rect width="404" height="22" rx="4" fill="rgba(255, 255, 255, 0.03)" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" />
            <text x="12" y="15" fill="#94A3B8" fontSize="9" fontWeight="500">
              CAPACITY: <tspan fill="#FFFFFF">{capacity}</tspan>
            </text>
            <text x="235" y="15" fill={accentColor} fontSize="9" fontWeight="600" letterSpacing="0.03em">
              {sensors.length} ACTIVE SENSOR CHANNELS
            </text>
          </g>
        </svg>
      );
    }

    if (category === 'segment') {
      const isWestbound = id.toLowerCase().includes('02') || name.toLowerCase().includes('westbound');
      const dirLabel = isWestbound ? 'WESTBOUND ARTERIAL VECTOR' : 'EASTBOUND ARTERIAL VECTOR';

      return (
        <svg viewBox="0 0 460 260" className="showcase-blueprint-svg" xmlns="http://www.w3.org/2000/svg" style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}>
          <defs>
            <linearGradient id={`flow-${id}`} x1={isWestbound ? '100%' : '0%'} y1="0%" x2={isWestbound ? '0%' : '100%'} y2="0%">
              <stop offset="0%" stopColor={accentColor} />
              <stop offset="60%" stopColor="#38BDF8" />
              <stop offset="100%" stopColor="#10B981" />
            </linearGradient>
          </defs>

          {/* Clean Dark Canvas Bed */}
          <rect width="460" height="260" fill="#07070A" />

          {/* Roadway Surface */}
          <rect x="24" y="64" width="412" height="96" rx="8" fill="#101014" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" />
          <line x1="24" y1="96" x2="436" y2="96" stroke="rgba(255, 255, 255, 0.12)" strokeWidth="1.2" strokeDasharray="10 8" />
          <line x1="24" y1="128" x2="436" y2="128" stroke="rgba(255, 255, 255, 0.12)" strokeWidth="1.2" strokeDasharray="10 8" />

          {/* Service Buffer Flank */}
          <rect x="24" y="168" width="412" height="28" rx="4" fill="rgba(255, 255, 255, 0.02)" stroke="rgba(255, 255, 255, 0.06)" strokeWidth="1" />

          {/* Velocity Progression Vector */}
          <path
            d={isWestbound
              ? "M 436 80 C 350 80, 290 112, 230 112 C 170 112, 110 80, 24 80"
              : "M 24 80 C 110 80, 170 112, 230 112 C 290 112, 350 80, 436 80"}
            fill="none"
            stroke={`url(#flow-${id})`}
            strokeWidth="2.5"
            strokeLinecap="round"
          />

          {/* Vehicle Pods */}
          <circle cx={isWestbound ? 350 : 90} cy="80" r="4.5" fill={accentColor} />
          <circle cx="230" cy="112" r="4.5" fill="#38BDF8" />
          <circle cx={isWestbound ? 90 : 350} cy="88" r="4.5" fill="#10B981" />

          {/* Top Header */}
          <g transform="translate(28, 24)">
            <text x="0" y="12" fill={accentColor} fontSize="11" fontWeight="600" letterSpacing="0.04em">
              {id} • {dirLabel}
            </text>
          </g>

          {/* Bottom Telemetry HUD */}
          <g transform="translate(28, 226)">
            <rect width="404" height="22" rx="4" fill="rgba(255, 255, 255, 0.03)" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" />
            <text x="12" y="15" fill="#94A3B8" fontSize="9" fontWeight="500">
              OPERATIONAL RATING: <tspan fill="#FFFFFF">{capacity}</tspan>
            </text>
          </g>
        </svg>
      );
    }

    if (category === 'building') {
      return (
        <svg viewBox="0 0 460 260" className="showcase-blueprint-svg" xmlns="http://www.w3.org/2000/svg" style={{ fontFamily: 'Inter, system-ui, -apple-system, sans-serif' }}>
          <defs>
            <linearGradient id={`bldFac-${id}`} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={`${accentColor}30`} />
              <stop offset="100%" stopColor="rgba(10, 10, 14, 0.95)" />
            </linearGradient>
          </defs>

          {/* Clean Dark Canvas Bed */}
          <rect width="460" height="260" fill="#07070A" />

          {/* Isometric Building Facility */}
          <g transform="translate(130, 36)">
            <polygon points="100,45 200,0 200,120 100,165" fill={`url(#bldFac-${id})`} stroke={accentColor} strokeWidth="1.2" />
            <polygon points="0,85 100,45 100,165 0,205" fill="rgba(16, 16, 22, 0.95)" stroke={accentColor} strokeWidth="1" opacity="0.8" />
            <polygon points="100,45 0,85 105,40 200,0" fill={`${accentColor}20`} stroke={accentColor} strokeWidth="1" />

            {/* Floor Plates */}
            {[70, 94, 118, 142].map((yOffset, idx) => (
              <line key={idx} x1="100" y1={yOffset} x2="200" y2={yOffset - 45} stroke={`${accentColor}35`} strokeWidth="1" />
            ))}

            {/* Rooftop Sub-Metering Array */}
            <g transform="translate(110, 30)">
              <circle cx="20" cy="0" r="3.5" fill="#10B981" />
              <circle cx="50" cy="-8" r="3.5" fill="#10B981" />
              <circle cx="80" cy="-16" r="3.5" fill="#10B981" />
            </g>

            {/* 11kV Feeder Ingress */}
            <path d="M -80 165 L -20 165 L 0 180" fill="none" stroke="#EF4444" strokeWidth="1.5" strokeDasharray="4 3" />
            <circle cx="-80" cy="165" r="4" fill="#EF4444" />
            <text x="-80" y="155" fill="#EF4444" fontSize="8" fontWeight="600" letterSpacing="0.05em">
              11kV SUBSTATION FEEDER
            </text>
          </g>

          {/* Top Header */}
          <g transform="translate(28, 24)">
            <text x="0" y="12" fill={accentColor} fontSize="11" fontWeight="600" letterSpacing="0.04em">
              {id} • {name.toUpperCase()}
            </text>
          </g>

          {/* Bottom Telemetry HUD */}
          <g transform="translate(28, 226)">
            <rect width="404" height="22" rx="4" fill="rgba(255, 255, 255, 0.03)" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" />
            <text x="12" y="15" fill="#94A3B8" fontSize="9" fontWeight="500">
              DEMAND CAP: <tspan fill="#FFFFFF">{capacity}</tspan>
            </text>
            <text x="245" y="15" fill={accentColor} fontSize="9" fontWeight="600" letterSpacing="0.03em">
              {sensors.length} VERIFIED METER FEEDS
            </text>
          </g>
        </svg>
      );
    }

    return null;
  };

  return (
    <section className="corridor-assets-section" id="assets-showcase">
      {/* Centered Modern Section Header */}
      <div className="section-header-centered">
        <div className="landing-badge font-mono">
          <Layers size={13} color="var(--color-primary)" />
          <span>SPATIAL INFRASTRUCTURE TWIN • ARTERIAL CORRIDOR</span>
        </div>
        <h2 className="landing-section-title">
          {title}
        </h2>
        <p className="landing-section-subtitle">
          {subtitle}
        </p>
      </div>

      {/* Modern Segmented Navigation Bar */}
      <div className="corridor-asset-nav" role="tablist">
        {assets.map((asset) => {
          const isActive = selectedId === asset.id;
          return (
            <button
              key={asset.id}
              role="tab"
              aria-selected={isActive}
              className={`corridor-nav-tab ${isActive ? 'active' : ''}`}
              onClick={() => setSelectedId(asset.id)}
              style={{
                borderColor: isActive ? asset.accentColor : undefined,
                boxShadow: isActive ? `0 0 16px ${asset.accentColor}25` : undefined
              }}
            >
              <div
                className="nav-tab-icon"
                style={{
                  color: isActive ? asset.accentColor : '#8B949E',
                  background: isActive ? `${asset.accentColor}18` : 'rgba(22, 27, 34, 0.6)'
                }}
              >
                {asset.category === 'intersection' && <MapPin size={14} />}
                {asset.category === 'segment' && <Car size={14} />}
                {asset.category === 'building' && <Zap size={14} />}
              </div>
              <div className="nav-tab-info">
                <span className="nav-tab-id font-mono">{asset.id}</span>
                <span className="nav-tab-title">{asset.shortName || asset.name}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* High-Fidelity Showcase Stage */}
      <div className="corridor-showcase-stage">
        {/* Left: Bespoke Interactive Photographic Twin & Vector Blueprint */}
        <div className="showcase-vector-pane">
          <div className="vector-pane-header">
            <div className="vector-pane-title-group">
              <div className="vector-pane-indicator" style={{ background: activeAsset.accentColor }} />
              <span className="vector-pane-title font-mono">
                {activeAsset.id} {viewMode === 'visual' && activeAsset.imageUrl && !imgErrorMap[activeAsset.id] ? 'PHOTOGRAPHIC TWIN' : 'SCHEMATIC BLUEPRINT'}
              </span>
            </div>
            {activeAsset.imageUrl && !imgErrorMap[activeAsset.id] && (
              <div className="showcase-view-toggle">
                <button
                  type="button"
                  className={`showcase-toggle-btn ${viewMode === 'visual' ? 'active' : ''}`}
                  onClick={() => setViewMode('visual')}
                >
                  PHOTO
                </button>
                <button
                  type="button"
                  className={`showcase-toggle-btn ${viewMode === 'blueprint' ? 'active' : ''}`}
                  onClick={() => setViewMode('blueprint')}
                >
                  SCHEMATIC
                </button>
              </div>
            )}
          </div>
          <div className="vector-canvas-wrap">
            {viewMode === 'visual' && activeAsset.imageUrl && !imgErrorMap[activeAsset.id] ? (
              <div className="showcase-photo-frame">
                <img
                  src={activeAsset.imageUrl}
                  alt={activeAsset.name}
                  className="showcase-photo-img"
                  onError={() => setImgErrorMap((prev) => ({ ...prev, [activeAsset.id]: true }))}
                />
                <div className="showcase-photo-overlay" aria-hidden="true" />
              </div>
            ) : (
              renderAssetBlueprint(activeAsset)
            )}
          </div>
        </div>

        {/* Right: Clean, High-Fidelity Specs & Intelligence Breakdown */}
        <div className="showcase-info-pane">
          {/* Header Meta */}
          <div className="showcase-info-header">
            <div className="info-meta-row">
              <span
                className="asset-category-pill font-mono"
                style={{
                  color: activeAsset.accentColor,
                  background: `${activeAsset.accentColor}15`,
                  borderColor: `${activeAsset.accentColor}35`
                }}
              >
                {activeAsset.categoryLabel}
              </span>
              <span className="info-live-status font-mono">
                <span className="status-dot-pulse" style={{ background: activeAsset.accentColor }} />
                <span>ONLINE TWIN</span>
              </span>
            </div>
            <h3 className="asset-display-title">{activeAsset.name}</h3>
            <span className="asset-display-location">{activeAsset.location}</span>
          </div>

          {/* Key Engineering Specifications */}
          <div className="showcase-specs-grid">
            <div className="showcase-spec-box">
              <span className="spec-label-clean font-mono">PHYSICAL GEOMETRY</span>
              <span className="spec-value-clean">{activeAsset.geometry}</span>
            </div>
            <div className="showcase-spec-box">
              <span className="spec-label-clean font-mono">OPERATIONAL CAPACITY</span>
              <span className="spec-value-clean" style={{ color: activeAsset.accentColor }}>
                {activeAsset.capacity}
              </span>
            </div>
          </div>

          {/* Verified Sensing Modalities */}
          <div className="showcase-sensors-group">
            <span className="group-label-clean font-mono">VERIFIED TELEMETRY MODALITIES</span>
            <div className="sensors-chips-wrap">
              {activeAsset.sensors.map((sensor, idx) => (
                <div key={idx} className="sensor-pill-clean font-mono">
                  <Cpu size={12} color={activeAsset.accentColor} />
                  <span>{sensor}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Advisory Decision Support Scope */}
          <div className="showcase-advisory-card">
            <div className="advisory-card-header">
              <ShieldCheck size={14} color="var(--color-success)" />
              <span className="font-mono">ADVISORY DECISION SUPPORT APPLICATION</span>
            </div>
            <p className="advisory-card-text">{activeAsset.decisionSupport}</p>
          </div>
        </div>
      </div>
    </section>
  );
};


