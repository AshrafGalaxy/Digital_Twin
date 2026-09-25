import React, { useState, useMemo } from 'react';
import {
  Zap,
  AlertTriangle,
  Clock,
  Building,
  HelpCircle,
  ShieldAlert,
  Gauge
} from 'lucide-react';
import { SourceMode, BuildingAsset, EntityCurrentState } from '../../types/twin';
import { ForecastPanel } from '../ForecastPanel';

interface EnergyAnalyticsViewProps {
  sourceMode: SourceMode;
  energyEntities?: BuildingAsset[];
  liveStates?: Record<string, EntityCurrentState>;
}

const DEFAULT_FACILITIES: BuildingAsset[] = [
  {
    id: 'urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01',
    name: 'Commercial Retail Complex & Zone',
    category: 'COMMERCIAL_RETAIL',
    grossFloorAreaSqMeters: 115000,
    electricalConnection: {
      substation: '22kV Primary Substation Feeder',
      sanctionedLoadKVA: 8500,
      contractDemandKW: 6800
    },
    baselineMetrics: {
      averageDaytimeDemandKW: 4200,
      peakEveningDemandKW: 5900,
      nightBaseDemandKW: 1100,
      powerFactor: 0.98
    },
    provenanceNotice: 'Building energy observations and profiles are calibrated synthetic/benchmark values modeled after commercial retail facilities.'
  },
  {
    id: 'urn:ngsi-ld:Building:PUNE:BLD-SOLITAIRE-01',
    name: 'Commercial Business & Tech Hub',
    category: 'COMMERCIAL_IT',
    grossFloorAreaSqMeters: 112690,
    electricalConnection: {
      substation: '22kV Primary Substation Feeder',
      sanctionedLoadKVA: 7500,
      contractDemandKW: 6010
    },
    baselineMetrics: {
      averageDaytimeDemandKW: 4800,
      peakEveningDemandKW: 3200,
      nightBaseDemandKW: 950,
      powerFactor: 0.97
    },
    provenanceNotice: 'Building energy observations and profiles are calibrated synthetic/benchmark values modeled after commercial IT facilities.'
  },
  {
    id: 'urn:ngsi-ld:Building:PUNE:BLD-HYATT-01',
    name: 'Hospitality & Convention Complex',
    category: 'HOSPITALITY_HOTEL',
    grossFloorAreaSqMeters: 93580,
    electricalConnection: {
      substation: '22kV Commercial Feeder B',
      sanctionedLoadKVA: 6250,
      contractDemandKW: 4990
    },
    baselineMetrics: {
      averageDaytimeDemandKW: 3100,
      peakEveningDemandKW: 4400,
      nightBaseDemandKW: 1800,
      powerFactor: 0.96
    },
    provenanceNotice: 'Building energy observations and profiles are calibrated synthetic/benchmark values modeled after hospitality hotel facilities.'
  },
  {
    id: 'urn:ngsi-ld:Building:PUNE:BLD-SOLITAIRE-03',
    name: 'Enterprise Office Center - Tower 3',
    category: 'COMMERCIAL_IT',
    grossFloorAreaSqMeters: 42000,
    electricalConnection: {
      substation: '22kV Distribution Feeder C',
      sanctionedLoadKVA: 3000,
      contractDemandKW: 2400
    },
    baselineMetrics: {
      averageDaytimeDemandKW: 1950,
      peakEveningDemandKW: 1400,
      nightBaseDemandKW: 450,
      powerFactor: 0.98
    },
    provenanceNotice: 'Building energy observations and profiles are calibrated synthetic/benchmark values modeled after corporate office facilities.'
  }
];

export const EnergyAnalyticsView: React.FC<EnergyAnalyticsViewProps> = ({
  sourceMode,
  energyEntities,
  liveStates
}) => {
  const facilities = useMemo(() => {
    return (energyEntities && energyEntities.length > 0) ? energyEntities : DEFAULT_FACILITIES;
  }, [energyEntities]);

  const [selectedFacilityId, setSelectedFacilityId] = useState<string>(
    () => facilities[0]?.id || 'urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01'
  );

  // Active facility object
  const activeFacility = useMemo(() => {
    return facilities.find(f => f.id === selectedFacilityId) || facilities[0] || DEFAULT_FACILITIES[0];
  }, [facilities, selectedFacilityId]);

  // Read dynamic active telemetry for selected facility
  const activeTelemetry = useMemo(() => {
    if (!liveStates) return null;
    if (liveStates[activeFacility.id]?.metrics?.activePowerKw !== undefined) {
      return liveStates[activeFacility.id].metrics;
    }
    const shortId = activeFacility.id.split(':').pop();
    for (const [k, v] of Object.entries(liveStates)) {
      if (shortId && k.includes(shortId) && v.metrics?.activePowerKw !== undefined) {
        return v.metrics;
      }
    }
    return null;
  }, [liveStates, activeFacility.id]);

  const contractLimitKw = activeFacility.electricalConnection?.contractDemandKW || 6800.0;
  const sanctionedKva = activeFacility.electricalConnection?.sanctionedLoadKVA || Math.round(contractLimitKw * 1.25);
  const substationName = activeFacility.electricalConnection?.substation || '22kV Primary Substation Feeder';
  const powerFactor = activeTelemetry?.powerFactor ?? activeFacility.baselineMetrics?.powerFactor ?? 0.98;

  // Active power: prefer dynamic telemetry, fallback gracefully to diurnal hour model
  const currentKw = useMemo(() => {
    if (activeTelemetry?.activePowerKw !== undefined) {
      return activeTelemetry.activePowerKw;
    }
    const now = new Date();
    const hour = now.getHours() + now.getMinutes() / 60;
    const base = activeFacility.baselineMetrics || DEFAULT_FACILITIES[0].baselineMetrics;
    if (hour >= 0 && hour < 8) {
      return base.nightBaseDemandKW;
    } else if (hour >= 8 && hour < 17) {
      return base.averageDaytimeDemandKW;
    } else {
      return base.peakEveningDemandKW;
    }
  }, [activeTelemetry, activeFacility.baselineMetrics]);

  const headroomKw = Math.max(0, contractLimitKw - currentKw);
  const loadFactor = Math.min(100, Math.max(0, (currentKw / contractLimitKw) * 100));
  const carbonRateKgPerKwh = 0.82; // Regional Grid average
  const currentCarbonHourlyKg = currentKw * carbonRateKgPerKwh;

  // Dynamic capacity thresholds
  const normalThresholdKw = Math.round(contractLimitKw * 0.70);
  const elevatedThresholdKw = Math.round(contractLimitKw * 0.85);

  const nightDemandKw = activeFacility.baselineMetrics?.nightBaseDemandKW || Math.round(contractLimitKw * 0.16);
  const daytimeDemandKw = activeFacility.baselineMetrics?.averageDaytimeDemandKW || Math.round(contractLimitKw * 0.62);
  const peakDemandKw = activeFacility.baselineMetrics?.peakEveningDemandKW || Math.round(contractLimitKw * 0.87);

  const nightPct = Math.min(100, Math.round((nightDemandKw / contractLimitKw) * 100));
  const daytimePct = Math.min(100, Math.round((daytimeDemandKw / contractLimitKw) * 100));
  const peakPct = Math.min(100, Math.round((peakDemandKw / contractLimitKw) * 100));

  return (
    <div className="view-container energy-analytics-view">
      {/* View Header */}
      <div className="view-header">
        <div>
          <h1 className="view-title">Corridor Energy Analytics & Commercial Load Forecasting</h1>
          <p className="view-subtitle">
            60-minute peak demand forecasting, diurnal commercial load profiles, and grid capacity risk assessment for {activeFacility.name}.
          </p>
        </div>
        <div className="view-header-badges">
          <span className="provenance-badge badge-simulation">
            {sourceMode} / BENCHMARK
          </span>
          <span className="provenance-badge badge-predicted">
            60-MIN XGBOOST
          </span>
        </div>
      </div>

      {/* Mandatory Data Integrity Banner */}
      <div className="integrity-caveat-banner">
        <AlertTriangle size={18} style={{ flexShrink: 0 }} />
        <div>
          <strong>Mandatory Data Integrity Caveat:</strong> This pilot energy stream is replayed benchmark/synthetic data and is not a measured meter feed from the municipal corridor. Commercial profiles are calibrated to typical Indian commercial facilities.
        </div>
      </div>

      {/* Facility Selector & Capacity Strip */}
      <div className="analytics-filter-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Building size={16} className="text-muted" />
          <label htmlFor="facility-selector" style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
            Monitored Facility:
          </label>
          <select
            id="facility-selector"
            className="analytics-select"
            value={selectedFacilityId}
            onChange={(e) => setSelectedFacilityId(e.target.value)}
          >
            {facilities.map((fac) => (
              <option key={fac.id} value={fac.id}>
                {fac.name} ({fac.grossFloorAreaSqMeters.toLocaleString()} m² GFA)
              </option>
            ))}
          </select>
        </div>

        <div className="analytics-meta-pill">
          <Gauge size={14} className="text-muted" />
          <span>
            Contract Limit: {contractLimitKw.toLocaleString()} kW | Sanctioned: {sanctionedKva.toLocaleString()} kVA
          </span>
        </div>
      </div>

      {/* Quick Telemetry KPI Row */}
      <div className="quick-metrics-row-four">
        <div className="metric-box">
          <span className="metric-box-label">Current Active Demand</span>
          <span
            className="metric-box-val font-mono"
            style={{
              color: currentKw > elevatedThresholdKw ? '#F85149' : currentKw > normalThresholdKw ? '#D29922' : '#3FB950'
            }}
          >
            {currentKw.toFixed(0)} <small>kW</small>
          </span>
          <span className="metric-box-sub">
            {loadFactor.toFixed(1)}% of contracted capacity
          </span>
        </div>

        <div className="metric-box">
          <span className="metric-box-label">Contract Headroom</span>
          <span
            className="metric-box-val font-mono"
            style={{
              color: headroomKw < (contractLimitKw * 0.15) ? '#F85149' : '#3FB950'
            }}
          >
            {headroomKw.toFixed(0)} <small>kW</small>
          </span>
          <span className="metric-box-sub">
            {headroomKw > (contractLimitKw * 0.15) ? 'Safe operational buffer' : 'Peak threshold risk'}
          </span>
        </div>

        <div className="metric-box">
          <span className="metric-box-label">Hourly Carbon Footprint</span>
          <span className="metric-box-val font-mono" style={{ color: '#F0F6FC' }}>
            {(currentCarbonHourlyKg / 1000).toFixed(2)} <small>t CO₂e/h</small>
          </span>
          <span className="metric-box-sub">
            @ 0.82 kg CO₂/kWh grid factor
          </span>
        </div>

        <div className="metric-box">
          <span className="metric-box-label">Substation Feeder</span>
          <span className="metric-box-val font-mono" style={{ fontSize: '15px', color: '#F0F6FC' }}>
            {substationName}
          </span>
          <span className="metric-box-sub">
            Power Factor: {powerFactor.toFixed(2)} lag ({activeFacility.category.replace('_', ' ')})
          </span>
        </div>
      </div>

      {/* Main Grid: Forecast & Diurnal Schedule */}
      <div className="analytics-grid-two-col">
        {/* Left Column: 60-Minute Forecast Panel with Conformal Intervals & TreeSHAP */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Zap size={18} color="#F59E0B" />
              <span className="card-title">60-Minute Predictive Demand Inference</span>
            </div>
            <span className="provenance-badge badge-predicted">PREDICTED</span>
          </div>

          <div style={{ padding: '4px 0' }}>
            <ForecastPanel
              key={activeFacility.id}
              entityType="Building"
              entityId={activeFacility.id}
              currentValue={currentKw}
              contractDemandKw={contractLimitKw}
            />
          </div>

          <div className="analytics-notice-box" style={{ marginTop: '16px' }}>
            <HelpCircle size={14} className="text-muted" />
            <span>
              <strong>Scientific Notice:</strong> Forecasts use XGBoost trained on diurnal hour-of-day, day-of-week, and temperature lag features with conformalized uncertainty bands.
            </span>
          </div>
        </div>

        {/* Right Column: Diurnal Load Profile & Threshold Classification */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock size={18} color="var(--color-primary, #2F81F7)" />
              <span className="card-title">Diurnal Load Profiles & Threshold Rules</span>
            </div>
            <span className="text-muted" style={{ fontSize: '12px' }}>
              {activeFacility.category.replace('_', ' ')} Archetype
            </span>
          </div>

          <div className="diurnal-profile-list">
            <div className="diurnal-item">
              <div className="diurnal-item-header">
                <span className="diurnal-title">Night Base Load (00:00 – 08:00)</span>
                <span className="diurnal-val font-mono">{nightDemandKw.toLocaleString()} kW</span>
              </div>
              <p className="diurnal-desc">
                Minimal ventilation, essential refrigeration, server rooms, and perimeter emergency security lighting.
              </p>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: `${nightPct}%`, backgroundColor: '#3FB950' }} />
              </div>
            </div>

            <div className="diurnal-item">
              <div className="diurnal-item-header">
                <span className="diurnal-title">Daytime Business Operations (08:00 – 16:00)</span>
                <span className="diurnal-val font-mono">{daytimeDemandKw.toLocaleString()} kW</span>
              </div>
              <p className="diurnal-desc">
                Central HVAC chillers, elevators/escalators, commercial tenant operations, and primary facilities.
              </p>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: `${daytimePct}%`, backgroundColor: '#2F81F7' }} />
              </div>
            </div>

            <div className="diurnal-item">
              <div className="diurnal-item-header">
                <span className="diurnal-title">Evening Peak Operations (16:00 – 22:00)</span>
                <span className="diurnal-val font-mono">{peakDemandKw.toLocaleString()} kW</span>
              </div>
              <p className="diurnal-desc">
                Peak visitor footfall, intensive cooling/heating cycles, architectural illumination, and ancillary loads.
              </p>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: `${peakPct}%`, backgroundColor: '#D29922' }} />
              </div>
            </div>
          </div>

          <h4 style={{ fontSize: '13px', fontWeight: 600, marginTop: '20px', marginBottom: '10px', color: 'var(--color-text, #F0F6FC)' }}>
            Peak Demand Governance Thresholds
          </h4>
          <table className="analytics-table">
            <thead>
              <tr>
                <th>Tier</th>
                <th>Range (kW)</th>
                <th>Threshold Status</th>
                <th>Advisory Action</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Normal Buffer</td>
                <td className="mono-cell font-mono">&lt; {normalThresholdKw.toLocaleString()} kW</td>
                <td><span className="status-pill status-active" style={{ color: '#3FB950', borderColor: 'rgba(63, 185, 80, 0.3)' }}>Optimal</span></td>
                <td>Standard grid supply; no intervention recommended</td>
              </tr>
              <tr>
                <td>Elevated Peak</td>
                <td className="mono-cell font-mono">{normalThresholdKw.toLocaleString()} – {elevatedThresholdKw.toLocaleString()} kW</td>
                <td><span className="status-pill status-review" style={{ color: '#D29922', borderColor: 'rgba(210, 153, 34, 0.3)' }}>Warning</span></td>
                <td>Advisory recommendation: Pre-cool zones, stagger chiller cycles</td>
              </tr>
              <tr>
                <td>Contract Risk</td>
                <td className="mono-cell font-mono">&gt; {elevatedThresholdKw.toLocaleString()} kW</td>
                <td><span className="status-pill status-dismissed" style={{ color: '#F85149', borderColor: 'rgba(248, 81, 73, 0.3)' }}>Critical</span></td>
                <td>Advisory recommendation: Dispatch on-site clean backup / BESS peak shaving</td>
              </tr>
            </tbody>
          </table>

          <div className="analytics-notice-box" style={{ marginTop: '16px' }}>
            <ShieldAlert size={14} color="#F59E0B" />
            <span>
              <strong>Advisory Governance Notice:</strong> All energy management recommendations require manual confirmation by facility engineering staff. The platform does not issue automated control commands to electrical switchgear.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
