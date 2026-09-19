import React from 'react';
import {
  Zap,
  AlertTriangle,
  Clock,
  Building,
  HelpCircle,
  ShieldAlert,
  Gauge
} from 'lucide-react';
import { SourceMode } from '../../types/twin';
import { ForecastPanel } from '../ForecastPanel';

interface EnergyAnalyticsViewProps {
  sourceMode: SourceMode;
}

export const EnergyAnalyticsView: React.FC<EnergyAnalyticsViewProps> = ({ sourceMode }) => {
  const currentKw = 5120.0;
  const contractLimitKw = 6800.0;
  const sanctionedKva = 8500.0;
  const headroomKw = contractLimitKw - currentKw;
  const loadFactor = (currentKw / contractLimitKw) * 100;
  const carbonRateKgPerKwh = 0.82; // Maharashtra State Grid average
  const currentCarbonHourlyKg = (currentKw * carbonRateKgPerKwh);

  const buildingId = 'urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01';

  return (
    <div className="view-container energy-analytics-view">
      {/* View Header */}
      <div className="view-header">
        <div>
          <h1 className="view-title">Corridor Energy Analytics & Commercial Load Forecasting</h1>
          <p className="view-subtitle">
            60-minute peak demand forecasting, diurnal commercial load profiles, and grid capacity risk assessment for Phoenix Marketcity zone.
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

      {/* Mandatory Data Integrity Banner per UI_UX_SPEC §10.3 */}
      <div className="integrity-caveat-banner">
        <AlertTriangle size={18} style={{ flexShrink: 0 }} />
        <div>
          <strong>Mandatory Data Integrity Caveat (UI_UX_SPEC §10.3):</strong> This pilot energy stream is replayed benchmark/synthetic data and is not a measured meter feed from the Pune pilot corridor. Commercial profiles are calibrated to typical Indian retail-commercial facilities.
        </div>
      </div>

      {/* Facility Selector & Capacity Strip */}
      <div className="analytics-filter-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Building size={16} className="text-muted" />
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
            Monitored Facility:
          </span>
          <select className="analytics-select" defaultValue={buildingId} disabled>
            <option value={buildingId}>
              Phoenix Marketcity Commercial Complex & Zone (115,000 m² GFA)
            </option>
          </select>
        </div>

        <div className="analytics-meta-pill">
          <Gauge size={14} className="text-muted" />
          <span>Contract Limit: {contractLimitKw.toLocaleString()} kW | Sanctioned: {sanctionedKva.toLocaleString()} kVA</span>
        </div>
      </div>

      {/* Quick Telemetry KPI Row */}
      <div className="quick-metrics-row-four">
        <div className="metric-box">
          <span className="metric-box-label">Current Active Demand</span>
          <span className="metric-box-val" style={{ color: currentKw > 5800 ? '#EF4444' : currentKw > 4800 ? '#F59E0B' : '#10B981' }}>
            {currentKw.toFixed(0)} <small>kW</small>
          </span>
          <span className="metric-box-sub">
            {loadFactor.toFixed(1)}% of contracted capacity
          </span>
        </div>

        <div className="metric-box">
          <span className="metric-box-label">Contract Headroom</span>
          <span className="metric-box-val" style={{ color: headroomKw < 1000 ? '#EF4444' : '#10B981' }}>
            {headroomKw.toFixed(0)} <small>kW</small>
          </span>
          <span className="metric-box-sub">
            {headroomKw > 1000 ? 'Safe operational buffer' : 'Peak threshold risk'}
          </span>
        </div>

        <div className="metric-box">
          <span className="metric-box-label">Hourly Carbon Footprint</span>
          <span className="metric-box-val" style={{ color: '#0F4C5C' }}>
            {(currentCarbonHourlyKg / 1000).toFixed(2)} <small>t CO₂e/h</small>
          </span>
          <span className="metric-box-sub">
            @ 0.82 kg CO₂/kWh grid factor
          </span>
        </div>

        <div className="metric-box">
          <span className="metric-box-label">Substation Feeder</span>
          <span className="metric-box-val" style={{ fontSize: '18px', color: '#1E293B' }}>
            22kV Viman Nagar
          </span>
          <span className="metric-box-sub">
            Power Factor: 0.98 lag (Commercial)
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
              entityType="Building"
              entityId={buildingId}
              currentValue={currentKw}
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
              <Clock size={18} color="#0F4C5C" />
              <span className="card-title">Diurnal Load Profiles & Threshold Rules</span>
            </div>
            <span className="text-muted" style={{ fontSize: '11px' }}>Standard Retail-Commercial Archetype</span>
          </div>

          <div className="diurnal-profile-list">
            <div className="diurnal-item">
              <div className="diurnal-item-header">
                <span className="diurnal-title">Night Base Load (00:00 – 08:00)</span>
                <span className="diurnal-val font-mono">1,100 kW</span>
              </div>
              <p className="diurnal-desc">
                Minimal ventilation, essential refrigeration, server rooms, and perimeter emergency security lighting.
              </p>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: '16%', backgroundColor: '#10B981' }} />
              </div>
            </div>

            <div className="diurnal-item">
              <div className="diurnal-item-header">
                <span className="diurnal-title">Daytime Business Operations (08:00 – 16:00)</span>
                <span className="diurnal-val font-mono">4,200 kW</span>
              </div>
              <p className="diurnal-desc">
                Central HVAC chillers, escalators, retail tenant display lighting, and food court commercial kitchens.
              </p>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: '62%', backgroundColor: '#0F4C5C' }} />
              </div>
            </div>

            <div className="diurnal-item">
              <div className="diurnal-item-header">
                <span className="diurnal-title">Evening Retail Peak (16:00 – 22:00)</span>
                <span className="diurnal-val font-mono">5,900 kW</span>
              </div>
              <p className="diurnal-desc">
                Full cinema complexes, peak footfall cooling loads, atrium illumination, and intensive kitchen utility usage.
              </p>
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: '87%', backgroundColor: '#F59E0B' }} />
              </div>
            </div>
          </div>

          <h4 style={{ fontSize: '13px', fontWeight: 600, marginTop: '20px', marginBottom: '10px', color: '#1E293B' }}>
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
                <td className="mono-cell">&lt; 4,800 kW</td>
                <td><span className="status-pill status-active">Optimal</span></td>
                <td>Standard grid supply; no intervention recommended</td>
              </tr>
              <tr>
                <td>Elevated Peak</td>
                <td className="mono-cell">4,800 – 5,800 kW</td>
                <td><span className="status-pill status-review">Warning</span></td>
                <td>Advisory recommendation: Pre-cool zones, stagger chiller cycles</td>
              </tr>
              <tr>
                <td>Contract Risk</td>
                <td className="mono-cell">&gt; 5,800 kW</td>
                <td><span className="status-pill status-dismissed" style={{ color: '#EF4444' }}>Critical</span></td>
                <td>Advisory recommendation: Dispatch on-site DG / solar BESS peak shaving</td>
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
