import React, { useState } from 'react';
import { MapPin, Cpu, Zap, Car, ShieldCheck, Layers } from 'lucide-react';

interface AssetDetail {
  id: string;
  name: string;
  category: 'intersection' | 'segment' | 'building';
  boundary: string;
  lanesOrFloors: string;
  sensors: string[];
  capacityOrPeak: string;
  coordinates: string;
  decisionSupport: string;
}

const CORRIDOR_ASSETS: AssetDetail[] = [
  {
    id: 'INT-VN-01',
    name: 'Viman Nagar Chowk',
    category: 'intersection',
    boundary: 'Nagar Road / Viman Nagar Road Crossing',
    lanesOrFloors: '4 Approach Legs • 12 Signal Phases',
    sensors: ['Inductive Loops (8)', 'Virtual Stop-Line Detectors', 'Radar Speed Profiler'],
    capacityOrPeak: 'Design Capacity: 4,200 PCU/hr',
    coordinates: '18.5679° N, 73.9143° E',
    decisionSupport: 'Advisory green split reallocation during arterial queue spillback.'
  },
  {
    id: 'INT-SN-01',
    name: 'Somnath Nagar Chowk',
    category: 'intersection',
    boundary: 'Nagar Road / Somnath Nagar Road Crossing',
    lanesOrFloors: '3 Approach Legs • Transit Priority Flank',
    sensors: ['Inductive Loops (6)', 'PMPML Transit Beacon Detectors'],
    capacityOrPeak: 'Design Capacity: 3,600 PCU/hr',
    coordinates: '18.5621° N, 73.9287° E',
    decisionSupport: 'Downstream queue dissipation pacing to avoid gridlock back-propagation.'
  },
  {
    id: 'SEG-NR-EB',
    name: 'Nagar Road Eastbound Corridor',
    category: 'segment',
    boundary: 'Viman Nagar Chowk → Somnath Nagar Chowk (1.8 km)',
    lanesOrFloors: '3 Main Lanes + Dedicated Service Flank',
    sensors: ['3 Sequential Loop Detector Stations', 'Synthetic Kinematics Micro-Feed'],
    capacityOrPeak: 'Design Speed: 45 km/h • 2,400 veh/hr',
    coordinates: 'SEG-NR-EB-01 .. 03',
    decisionSupport: 'Conformal speed forecast alerts for pre-congestion queue formation.'
  },
  {
    id: 'SEG-NR-WB',
    name: 'Nagar Road Westbound Corridor',
    category: 'segment',
    boundary: 'Somnath Nagar Chowk → Viman Nagar Chowk (1.8 km)',
    lanesOrFloors: '3 Main Lanes + Phoenix Commercial Ingress',
    sensors: ['Commercial Mall Turning Count Detectors', 'Loop Arrays IL-04..06'],
    capacityOrPeak: 'Design Speed: 45 km/h • Weekend Surge: 3,100 veh/hr',
    coordinates: 'SEG-NR-WB-01 .. 03',
    decisionSupport: 'Mall ingress deceleration buffer advisories for weekend shopping peaks.'
  },
  {
    id: 'BLD-PHOENIX-01',
    name: 'Phoenix Marketcity Commercial Zone',
    category: 'building',
    boundary: 'Nagar Road Central Commercial Zone',
    lanesOrFloors: '5 Commercial Levels • 120,000 m² Conditioned Space',
    sensors: ['Aggregate Main 11kV Feeder Meter', 'Chiller Plant Sub-Meters (3)'],
    capacityOrPeak: 'Peak Power: 4,862 kW • Contract Demand: 5,200 kW',
    coordinates: '18.5628° N, 73.9168° E',
    decisionSupport: 'Automated 15-minute chiller pre-cooling advisory to shave 380 kW during peak tariff.'
  }
];

export const CorridorAssetsShowcase: React.FC = () => {
  const [selectedId, setSelectedId] = useState<string>('INT-VN-01');
  const activeAsset = CORRIDOR_ASSETS.find((a) => a.id === selectedId) || CORRIDOR_ASSETS[0];

  return (
    <section className="corridor-assets-section" id="assets-showcase">
      <div className="section-header-centered">
        <div className="landing-badge font-mono">
          <Layers size={13} color="var(--color-primary)" />
          <span>PHYSICAL ASSET INVENTORY • PUNE NAGAR ROAD</span>
        </div>
        <h2 className="landing-section-title">
          Authoritative Physical Corridor Model
        </h2>
        <p className="landing-section-subtitle">
          Every telemetry signal, simulation particle, and conformal forecast maps to physically verified road segments and commercial entities.
        </p>
      </div>

      <div className="asset-showcase-container">
        {/* Rectangular Asset Selector Tabs */}
        <div className="asset-tabs-list" role="tablist">
          {CORRIDOR_ASSETS.map((asset) => (
            <button
              key={asset.id}
              role="tab"
              aria-selected={selectedId === asset.id}
              className={`asset-tab-btn ${selectedId === asset.id ? 'active' : ''}`}
              onClick={() => setSelectedId(asset.id)}
            >
              <div className="tab-left-indicator">
                {asset.category === 'intersection' && <MapPin size={14} />}
                {asset.category === 'segment' && <Car size={14} />}
                {asset.category === 'building' && <Zap size={14} />}
              </div>
              <div className="tab-text-block">
                <span className="tab-id font-mono">{asset.id}</span>
                <span className="tab-title">{asset.name}</span>
              </div>
            </button>
          ))}
        </div>

        {/* Detailed Rectangular Asset Card */}
        <div className="asset-detail-card">
          <div className="card-top-header">
            <div className="header-meta">
              <span className="asset-category-tag font-mono">
                {activeAsset.category.toUpperCase()} ASSET
              </span>
              <span className="asset-coords font-mono">{activeAsset.coordinates}</span>
            </div>
            <h3 className="asset-full-name">{activeAsset.name}</h3>
            <span className="asset-boundary font-mono">{activeAsset.boundary}</span>
          </div>

          <div className="asset-specs-grid">
            <div className="spec-card">
              <span className="spec-label font-mono">GEOMETRY & LAYOUT</span>
              <span className="spec-value">{activeAsset.lanesOrFloors}</span>
            </div>
            <div className="spec-card">
              <span className="spec-label font-mono">CAPACITY & PEAK THRESHOLD</span>
              <span className="spec-value text-accent">{activeAsset.capacityOrPeak}</span>
            </div>
          </div>

          <div className="asset-sensors-block">
            <span className="sensors-title font-mono">VERIFIED TELEMETRY MODALITIES</span>
            <div className="sensor-chips-list">
              {activeAsset.sensors.map((sensor, idx) => (
                <div key={idx} className="sensor-chip font-mono">
                  <Cpu size={12} color="var(--color-primary-hover)" />
                  <span>{sensor}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="asset-advisory-block">
            <div className="advisory-title-row">
              <ShieldCheck size={14} color="var(--color-success)" />
              <span className="font-mono">DECISION-SUPPORT APPLICATION</span>
            </div>
            <p className="advisory-text">{activeAsset.decisionSupport}</p>
          </div>
        </div>
      </div>
    </section>
  );
};
