import React, { useState } from 'react';
import { MapPin, Cpu, Zap, Car, ShieldCheck, Layers } from 'lucide-react';

interface AssetDetail {
  id: string;
  name: string;
  category: 'intersection' | 'segment' | 'building';
  categoryLabel: string;
  location: string;
  geometry: string;
  capacity: string;
  sensors: string[];
  decisionSupport: string;
  accentColor: string;
}

const CORRIDOR_ASSETS: AssetDetail[] = [
  {
    id: 'INT-VN-01',
    name: 'West Intersection Node',
    category: 'intersection',
    categoryLabel: 'SIGNALIZED INTERSECTION',
    location: 'Dual Arterial / West Crossroad Node',
    geometry: '4 Approach Legs • 12 Coordinated Phases',
    capacity: '4,200 PCU / hr Peak Capacity',
    sensors: ['8 Inductive Loop Sensors', 'Virtual Stop-Line Detectors', 'Radar Speed Profiler'],
    decisionSupport: 'Advisory green split reallocation during arterial queue spillback.',
    accentColor: '#38BDF8'
  },
  {
    id: 'INT-SN-01',
    name: 'East Intersection Node',
    category: 'intersection',
    categoryLabel: 'SIGNALIZED INTERSECTION',
    location: 'Dual Arterial / East Transit Flank Crossing',
    geometry: '3 Approach Legs • Transit Priority Flank',
    capacity: '3,600 PCU / hr Peak Capacity',
    sensors: ['6 Inductive Loop Detectors', 'Transit Beacon Detectors', 'Approach Radar Profiler'],
    decisionSupport: 'Downstream queue dissipation pacing to prevent arterial gridlock back-propagation.',
    accentColor: '#10B981'
  },
  {
    id: 'SEG-NR-EB',
    name: 'Eastbound Arterial Corridor',
    category: 'segment',
    categoryLabel: 'ARTERIAL ROAD SEGMENT',
    location: 'Node INT-VN-01 → Node INT-SN-01',
    geometry: '3 Main Travel Lanes + Dedicated Service Flank',
    capacity: 'Design Speed: 45 km/h • 2,400 veh/hr Flow',
    sensors: ['3 Sequential Loop Stations (IL-01..03)', 'Synthetic Kinematics Micro-Feed', 'Continuous Radar Profiler'],
    decisionSupport: 'Conformal speed forecast alerts for pre-congestion queue formation.',
    accentColor: '#58A6FF'
  },
  {
    id: 'SEG-NR-WB',
    name: 'Westbound Arterial Corridor',
    category: 'segment',
    categoryLabel: 'ARTERIAL ROAD SEGMENT',
    location: 'Node INT-SN-01 → Node INT-VN-01',
    geometry: '3 Main Travel Lanes + Ingress Deceleration Buffer',
    capacity: 'Design Speed: 45 km/h • Weekend Surge: 3,100 veh/hr',
    sensors: ['Commercial Facility Turning Detectors', 'Loop Arrays (IL-04..06)', 'Queue Spillback Monitor'],
    decisionSupport: 'Commercial ingress deceleration buffer advisories for weekend shopping peaks.',
    accentColor: '#818CF8'
  },
  {
    id: 'BLD-PHOENIX-01',
    name: 'Phoenix Commercial Complex',
    category: 'building',
    categoryLabel: 'COMMERCIAL FACILITY',
    location: 'Central Arterial Commercial Zone',
    geometry: '5 Commercial Levels • 120,000 m² Conditioned Area',
    capacity: 'Peak Power: 4,862 kW • Contract Demand: 5,200 kW',
    sensors: ['11kV Main Grid Feeder Meter', 'Chiller Plant Sub-Meters (3 Units)', 'HVAC Zone Thermosensors'],
    decisionSupport: 'Automated 15-minute chiller pre-cooling advisory to shave 380 kW during peak tariff.',
    accentColor: '#F59E0B'
  }
];

export const CorridorAssetsShowcase: React.FC = () => {
  const [selectedId, setSelectedId] = useState<string>('INT-VN-01');
  const activeAsset = CORRIDOR_ASSETS.find((a) => a.id === selectedId) || CORRIDOR_ASSETS[0];

  const renderAssetBlueprint = (id: string) => {
    switch (id) {
      case 'INT-VN-01':
        return (
          <svg viewBox="0 0 460 260" className="showcase-blueprint-svg" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="vnBeamH" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#10B981" stopOpacity="0.1" />
                <stop offset="50%" stopColor="#10B981" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#10B981" stopOpacity="0.1" />
              </linearGradient>
              <radialGradient id="vnRadarPulse" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.0" />
              </radialGradient>
            </defs>
            {/* Background Grid Pattern */}
            <rect width="460" height="260" fill="#0A0E17" />
            <circle cx="230" cy="130" r="110" fill="url(#vnRadarPulse)" pointerEvents="none" />

            {/* 4-Way Intersection Roadbeds */}
            {/* East-West Arterial (Nagar Road) */}
            <rect x="20" y="100" width="420" height="60" rx="4" fill="#161B22" stroke="#30363D" strokeWidth="1" />
            <line x1="20" y1="130" x2="440" y2="130" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1.5" strokeDasharray="8 6" />

            {/* North-South Crossing (Viman Nagar Road) */}
            <rect x="200" y="20" width="60" height="220" rx="4" fill="#161B22" stroke="#30363D" strokeWidth="1" />
            <line x1="230" y1="20" x2="230" y2="240" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1.5" strokeDasharray="8 6" />

            {/* Center Intersection Box */}
            <rect x="200" y="100" width="60" height="60" fill="#1C2128" stroke="#38BDF8" strokeWidth="1.2" />

            {/* Coordinated Signal Phases (Green on East-West Arterial) */}
            <line x1="25" y1="130" x2="195" y2="130" stroke="url(#vnBeamH)" strokeWidth="3" strokeLinecap="round" />
            <line x1="265" y1="130" x2="435" y2="130" stroke="url(#vnBeamH)" strokeWidth="3" strokeLinecap="round" />

            {/* Stop-Line Inductive Loops */}
            <rect x="180" y="104" width="12" height="22" rx="2" fill="rgba(56, 189, 248, 0.2)" stroke="#38BDF8" strokeWidth="1" />
            <rect x="180" y="134" width="12" height="22" rx="2" fill="rgba(56, 189, 248, 0.2)" stroke="#38BDF8" strokeWidth="1" />
            <rect x="268" y="104" width="12" height="22" rx="2" fill="rgba(56, 189, 248, 0.2)" stroke="#38BDF8" strokeWidth="1" />
            <rect x="268" y="134" width="12" height="22" rx="2" fill="rgba(56, 189, 248, 0.2)" stroke="#38BDF8" strokeWidth="1" />

            {/* Central Signal Controller Node with Pulse Rings */}
            <circle cx="230" cy="130" r="38" fill="none" stroke="#38BDF8" strokeWidth="1" opacity="0.3" strokeDasharray="4 4">
              <animateTransform attributeName="transform" type="rotate" from="0 230 130" to="360 230 130" dur="16s" repeatCount="indefinite" />
            </circle>
            <circle cx="230" cy="130" r="18" fill="none" stroke="#38BDF8" strokeWidth="1.5" opacity="0.6" />
            <circle cx="230" cy="130" r="6" fill="#38BDF8" />

            {/* Signal Indicator Beacons */}
            <circle cx="195" cy="95" r="4" fill="#10B981" />
            <circle cx="265" cy="95" r="4" fill="#EF4444" />
            <circle cx="195" cy="165" r="4" fill="#EF4444" />
            <circle cx="265" cy="165" r="4" fill="#10B981" />
          </svg>
        );

      case 'INT-SN-01':
        return (
          <svg viewBox="0 0 460 260" className="showcase-blueprint-svg" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="snTransitGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#10B981" stopOpacity="0.1" />
                <stop offset="60%" stopColor="#10B981" stopOpacity="0.85" />
                <stop offset="100%" stopColor="#10B981" stopOpacity="0.1" />
              </linearGradient>
            </defs>
            <rect width="460" height="260" fill="#0A0E17" />

            {/* East-West Arterial Roadway */}
            <rect x="20" y="90" width="420" height="66" rx="4" fill="#161B22" stroke="#30363D" strokeWidth="1" />
            <line x1="20" y1="123" x2="440" y2="123" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1.5" strokeDasharray="8 6" />

            {/* Somnath Nagar Road Crossing Leg */}
            <rect x="250" y="156" width="60" height="84" rx="3" fill="#161B22" stroke="#30363D" strokeWidth="1" />
            <line x1="280" y1="156" x2="280" y2="240" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1.5" strokeDasharray="6 6" />

            {/* Dedicated BRTS Transit Priority Flank */}
            <rect x="20" y="60" width="420" height="24" rx="3" fill="rgba(16, 185, 129, 0.08)" stroke="#10B981" strokeWidth="1" strokeDasharray="4 3" />
            <line x1="20" y1="72" x2="440" y2="72" stroke="url(#snTransitGrad)" strokeWidth="2.5" />

            {/* PMPML Transit Detection Beacons */}
            <circle cx="120" cy="72" r="5" fill="#10B981" />
            <circle cx="120" cy="72" r="14" fill="none" stroke="#10B981" strokeWidth="1" opacity="0.4" />
            <circle cx="340" cy="72" r="5" fill="#10B981" />
            <circle cx="340" cy="72" r="14" fill="none" stroke="#10B981" strokeWidth="1" opacity="0.4" />

            {/* Intersection Junction Core */}
            <g transform="translate(280, 123)">
              <circle r="36" fill="none" stroke="#10B981" strokeWidth="1" opacity="0.25" strokeDasharray="4 4" />
              <circle r="16" fill="none" stroke="#10B981" strokeWidth="1.2" opacity="0.5" />
              <circle r="6" fill="#10B981" />
            </g>

            {/* Inductive Loop Array IL-SN */}
            <rect x="220" y="96" width="12" height="22" rx="2" fill="rgba(16, 185, 129, 0.2)" stroke="#10B981" strokeWidth="1" />
            <rect x="220" y="128" width="12" height="22" rx="2" fill="rgba(16, 185, 129, 0.2)" stroke="#10B981" strokeWidth="1" />
          </svg>
        );

      case 'SEG-NR-EB':
        return (
          <svg viewBox="0 0 460 260" className="showcase-blueprint-svg" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="segEbFlow" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#38BDF8" />
                <stop offset="50%" stopColor="#2F81F7" />
                <stop offset="100%" stopColor="#10B981" />
              </linearGradient>
            </defs>
            <rect width="460" height="260" fill="#0A0E17" />

            {/* 3 Main Travel Lanes */}
            <rect x="20" y="60" width="420" height="100" rx="6" fill="#161B22" stroke="#30363D" strokeWidth="1" />
            <line x1="20" y1="93" x2="440" y2="93" stroke="rgba(255, 255, 255, 0.16)" strokeWidth="1.2" strokeDasharray="10 8" />
            <line x1="20" y1="126" x2="440" y2="126" stroke="rgba(255, 255, 255, 0.16)" strokeWidth="1.2" strokeDasharray="10 8" />

            {/* Dedicated Service Road Flank */}
            <rect x="20" y="174" width="420" height="32" rx="4" fill="rgba(30, 41, 59, 0.5)" stroke="#334155" strokeWidth="1" />
            <line x1="20" y1="190" x2="440" y2="190" stroke="rgba(255, 255, 255, 0.1)" strokeWidth="1" strokeDasharray="6 6" />

            {/* 3 Sequential Loop Detector Stations */}
            {/* Station IL-01 */}
            <g transform="translate(100, 60)">
              <rect width="8" height="100" fill="rgba(56, 189, 248, 0.15)" stroke="#38BDF8" strokeWidth="1" />
              <circle cx="4" cy="0" r="3.5" fill="#38BDF8" />
            </g>
            {/* Station IL-02 */}
            <g transform="translate(230, 60)">
              <rect width="8" height="100" fill="rgba(56, 189, 248, 0.15)" stroke="#38BDF8" strokeWidth="1" />
              <circle cx="4" cy="0" r="3.5" fill="#38BDF8" />
            </g>
            {/* Station IL-03 */}
            <g transform="translate(360, 60)">
              <rect width="8" height="100" fill="rgba(16, 185, 129, 0.15)" stroke="#10B981" strokeWidth="1" />
              <circle cx="4" cy="0" r="3.5" fill="#10B981" />
            </g>

            {/* High-Speed Velocity Wave Spline */}
            <path
              d="M 20 76 C 90 76, 160 110, 230 110 C 300 110, 370 76, 440 76"
              fill="none"
              stroke="url(#segEbFlow)"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
            {/* Vehicle Pods */}
            <circle cx="80" cy="76" r="4.5" fill="#38BDF8" />
            <circle cx="210" cy="110" r="4.5" fill="#2F81F7" />
            <circle cx="340" cy="85" r="4.5" fill="#10B981" />
          </svg>
        );

      case 'SEG-NR-WB':
        return (
          <svg viewBox="0 0 460 260" className="showcase-blueprint-svg" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="segWbFlow" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#818CF8" />
                <stop offset="50%" stopColor="#F59E0B" />
                <stop offset="100%" stopColor="#38BDF8" />
              </linearGradient>
            </defs>
            <rect width="460" height="260" fill="#0A0E17" />

            {/* Westbound Main Travel Roadway */}
            <rect x="20" y="90" width="420" height="100" rx="6" fill="#161B22" stroke="#30363D" strokeWidth="1" />
            <line x1="20" y1="123" x2="440" y2="123" stroke="rgba(255, 255, 255, 0.16)" strokeWidth="1.2" strokeDasharray="10 8" />
            <line x1="20" y1="156" x2="440" y2="156" stroke="rgba(255, 255, 255, 0.16)" strokeWidth="1.2" strokeDasharray="10 8" />

            {/* Commercial Mall Turning Ingress Leg */}
            <path
              d="M 220 90 C 230 40, 270 25, 330 25 L 440 25"
              fill="none"
              stroke="rgba(245, 158, 11, 0.4)"
              strokeWidth="28"
              strokeLinecap="round"
            />
            <path
              d="M 220 90 C 230 40, 270 25, 330 25 L 440 25"
              fill="none"
              stroke="#F59E0B"
              strokeWidth="1.5"
              strokeDasharray="4 4"
            />

            {/* Ingress Deceleration Buffer Zone */}
            <rect x="160" y="86" width="90" height="40" rx="4" fill="rgba(245, 158, 11, 0.12)" stroke="#F59E0B" strokeWidth="1" strokeDasharray="3 3" />

            {/* Loop Detectors IL-04..06 */}
            <g transform="translate(130, 90)">
              <rect width="8" height="100" fill="rgba(129, 140, 248, 0.15)" stroke="#818CF8" strokeWidth="1" />
              <circle cx="4" cy="0" r="3.5" fill="#818CF8" />
            </g>
            <g transform="translate(300, 90)">
              <rect width="8" height="100" fill="rgba(56, 189, 248, 0.15)" stroke="#38BDF8" strokeWidth="1" />
              <circle cx="4" cy="0" r="3.5" fill="#38BDF8" />
            </g>

            {/* Vehicle Trajectories with Mall Turning Curve */}
            <circle cx="360" cy="140" r="4.5" fill="#818CF8" />
            <circle cx="200" cy="105" r="4.5" fill="#F59E0B" />
            <circle cx="280" cy="40" r="4" fill="#F59E0B" />
          </svg>
        );

      case 'BLD-PHOENIX-01':
        return (
          <svg viewBox="0 0 460 260" className="showcase-blueprint-svg" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="bldFacadeGlow" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="rgba(245, 158, 11, 0.35)" />
                <stop offset="100%" stopColor="rgba(15, 23, 42, 0.9)" />
              </linearGradient>
            </defs>
            <rect width="460" height="260" fill="#0A0E17" />

            {/* Main Commercial Complex 3D Isometric Architecture */}
            <g transform="translate(140, 45)">
              {/* Podium Base Facet */}
              <polygon points="90,40 190,0 190,110 90,150" fill="url(#bldFacadeGlow)" stroke="#F59E0B" strokeWidth="1.2" />
              <polygon points="0,75 90,40 90,150 0,185" fill="rgba(15, 23, 42, 0.95)" stroke="#D97706" strokeWidth="1" />
              <polygon points="90,40 0,75 100,35 190,0" fill="rgba(245, 158, 11, 0.2)" stroke="#F59E0B" strokeWidth="1" />

              {/* Floor Plates (5 Levels) */}
              <line x1="90" y1="62" x2="190" y2="22" stroke="rgba(245, 158, 11, 0.45)" strokeWidth="1" />
              <line x1="90" y1="84" x2="190" y2="44" stroke="rgba(245, 158, 11, 0.45)" strokeWidth="1" />
              <line x1="90" y1="106" x2="190" y2="66" stroke="rgba(245, 158, 11, 0.45)" strokeWidth="1" />
              <line x1="90" y1="128" x2="190" y2="88" stroke="rgba(245, 158, 11, 0.45)" strokeWidth="1" />

              {/* 3 Rooftop Chiller Sub-Stations with Thermal Glow */}
              <g transform="translate(100, 30)">
                <circle cx="15" cy="0" r="10" fill="none" stroke="#10B981" strokeWidth="1" opacity="0.5" />
                <circle cx="15" cy="0" r="4" fill="#10B981" />
                <circle cx="45" cy="-8" r="10" fill="none" stroke="#10B981" strokeWidth="1" opacity="0.5" />
                <circle cx="45" cy="-8" r="4" fill="#10B981" />
                <circle cx="75" cy="-16" r="10" fill="none" stroke="#10B981" strokeWidth="1" opacity="0.5" />
                <circle cx="75" cy="-16" r="4" fill="#10B981" />
              </g>

              {/* 11kV Electrical Main Ingress Feed Line */}
              <path d="M -90 160 L -30 160 L 0 170" fill="none" stroke="#EF4444" strokeWidth="2" strokeDasharray="4 3" />
              <circle cx="-90" cy="160" r="5" fill="#EF4444" />
            </g>
          </svg>
        );

      default:
        return null;
    }
  };

  return (
    <section className="corridor-assets-section" id="assets-showcase">
      {/* Centered Modern Section Header (No mention of 1.8 km) */}
      <div className="section-header-centered">
        <div className="landing-badge font-mono">
          <Layers size={13} color="var(--color-primary)" />
          <span>SPATIAL INFRASTRUCTURE TWIN • DUAL ARTERIAL</span>
        </div>
        <h2 className="landing-section-title">
          Authoritative Physical Corridor Model
        </h2>
        <p className="landing-section-subtitle">
          Direct physical twin mappings for signalized intersections, arterial travel segments, and commercial energy infrastructure across the dual arterial corridor.
        </p>
      </div>

      {/* Modern Segmented Navigation Bar */}
      <div className="corridor-asset-nav" role="tablist">
        {CORRIDOR_ASSETS.map((asset) => {
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
                <span className="nav-tab-title">{asset.name}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* High-Fidelity Showcase Stage */}
      <div className="corridor-showcase-stage">
        {/* Left: Bespoke Interactive Vector Blueprint */}
        <div className="showcase-vector-pane">
          <div className="vector-pane-header">
            <div className="vector-pane-indicator" style={{ background: activeAsset.accentColor }} />
            <span className="vector-pane-title font-mono">{activeAsset.id} SCHEMATIC</span>
          </div>
          <div className="vector-canvas-wrap">
            {renderAssetBlueprint(activeAsset.id)}
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
