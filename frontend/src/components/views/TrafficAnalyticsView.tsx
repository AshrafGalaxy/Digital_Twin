import React, { useState } from 'react';
import {
  TrendingUp,
  Car,
  Filter,
  Layers,
  HelpCircle
} from 'lucide-react';
import { RoadSegmentAsset, EntityCurrentState, SourceMode } from '../../types/twin';
import { ForecastPanel } from '../ForecastPanel';

interface TrafficAnalyticsViewProps {
  roadSegments: RoadSegmentAsset[];
  liveStates: Record<string, EntityCurrentState>;
  sourceMode: SourceMode;
}

export const TrafficAnalyticsView: React.FC<TrafficAnalyticsViewProps> = ({
  roadSegments,
  liveStates,
  sourceMode
}) => {
  const [selectedSegmentId, setSelectedSegmentId] = useState<string>(
    roadSegments[0]?.id || 'urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01'
  );

  const selectedSegment = roadSegments.find(s => s.id === selectedSegmentId) || roadSegments[0];
  const currentState = selectedSegment ? liveStates[selectedSegment.id] : null;
  const currentSpeed = currentState?.metrics?.averageSpeedKmh ?? 24.5;
  const congestionIdx = currentState?.metrics?.congestionIndex ?? 0.45;

  // Rank segments by congestion (lowest speed first)
  const rankedSegments = [...roadSegments].map(seg => {
    const s = liveStates[seg.id];
    const spd = s?.metrics?.averageSpeedKmh ?? seg.speedLimitKmh;
    const cong = s?.metrics?.congestionIndex ?? Math.max(0, 1 - spd / seg.speedLimitKmh);
    let los = 'A';
    if (spd < 18) los = 'F';
    else if (spd < 25) los = 'E';
    else if (spd < 32) los = 'D';
    else if (spd < 38) los = 'C';
    else if (spd < 42) los = 'B';

    return {
      ...seg,
      speed: spd,
      congestion: cong,
      los,
      quality: s?.qualityStatus || 'VALID'
    };
  }).sort((a, b) => a.speed - b.speed);

  return (
    <div className="view-container traffic-analytics-view">
      {/* View Header */}
      <div className="view-header">
        <div>
          <h1 className="view-title">Corridor Traffic Analytics & Mobility Forecasting</h1>
          <p className="view-subtitle">
            Near-term speed forecasting, diurnal trend analysis, and segment congestion rankings on Nagar Road (SH-27).
          </p>
        </div>
        <div className="view-header-badges">
          <span className={`provenance-badge badge-${sourceMode.toLowerCase()}`}>
            {sourceMode}
          </span>
          <span className="provenance-badge badge-predicted">15-MIN XGBOOST</span>
        </div>
      </div>

      {/* Segment Selector Bar */}
      <div className="analytics-filter-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={16} className="text-muted" />
          <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
            Selected Road Segment:
          </span>
          <select
            className="analytics-select"
            value={selectedSegmentId}
            onChange={(e) => setSelectedSegmentId(e.target.value)}
          >
            {roadSegments.map(seg => (
              <option key={seg.id} value={seg.id}>
                {seg.name} ({seg.direction}, {seg.lanes} lanes)
              </option>
            ))}
          </select>
        </div>

        <div className="analytics-meta-pill">
          <Layers size={14} className="text-muted" />
          <span>Speed Limit: {selectedSegment?.speedLimitKmh || 45} km/h</span>
        </div>
      </div>

      {/* Main Grid: Forecast & Overview */}
      <div className="analytics-grid-two-col">
        {/* Left Column: Current State & Forecast Panel */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Car size={18} color="#2DD4BF" />
              <span className="card-title">Live State & Predictive Inference</span>
            </div>
            <span className="provenance-badge badge-predicted">PREDICTED</span>
          </div>

          <div className="quick-metrics-row">
            <div className="metric-box">
              <span className="metric-box-label">Current Observed Speed</span>
              <span className="metric-box-val" style={{ color: currentSpeed < 20 ? '#EF4444' : '#10B981' }}>
                {currentSpeed.toFixed(1)} <small>km/h</small>
              </span>
            </div>
            <div className="metric-box">
              <span className="metric-box-label">Congestion Index</span>
              <span className="metric-box-val">
                {(congestionIdx * 100).toFixed(0)}%
              </span>
            </div>
            <div className="metric-box">
              <span className="metric-box-label">Level of Service (LOS)</span>
              <span className="metric-box-val" style={{ color: currentSpeed < 20 ? '#EF4444' : '#F59E0B' }}>
                {currentSpeed < 18 ? 'LOS F' : currentSpeed < 28 ? 'LOS D' : 'LOS B'}
              </span>
            </div>
          </div>

          {/* Integrated 15-Minute Forecast with Conformal & TreeSHAP */}
          {selectedSegment && (
            <ForecastPanel
              entityType="RoadSegment"
              entityId={selectedSegment.id}
              currentValue={currentSpeed}
            />
          )}
        </div>

        {/* Right Column: Corridor Congestion Rankings Table */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <TrendingUp size={18} color="#F59E0B" />
              <span className="card-title">Corridor Segment Health & Rankings</span>
            </div>
            <span className="text-muted" style={{ fontSize: '12px' }}>Sorted by Congestion</span>
          </div>

          <div className="table-responsive">
            <table className="analytics-table">
              <thead>
                <tr>
                  <th>Segment</th>
                  <th>Dir</th>
                  <th>Current Speed</th>
                  <th>LOS</th>
                  <th>Congestion</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {rankedSegments.map(seg => (
                  <tr
                    key={seg.id}
                    className={seg.id === selectedSegmentId ? 'row-selected' : ''}
                    onClick={() => setSelectedSegmentId(seg.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td>
                      <div style={{ fontWeight: 600 }}>{seg.name}</div>
                      <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>{seg.id.split(':').pop()}</div>
                    </td>
                    <td>
                      <span className="dir-tag">{seg.direction}</span>
                    </td>
                    <td>
                      <span style={{ fontWeight: 700, color: seg.speed < 20 ? '#EF4444' : seg.speed < 32 ? '#F59E0B' : '#10B981' }}>
                        {seg.speed.toFixed(1)} km/h
                      </span>
                    </td>
                    <td>
                      <span className={`los-badge los-${seg.los.toLowerCase()}`}>
                        {seg.los}
                      </span>
                    </td>
                    <td>
                      <div className="progress-bar-bg">
                        <div
                          className="progress-bar-fill"
                          style={{
                            width: `${Math.min(100, seg.congestion * 100)}%`,
                            backgroundColor: seg.congestion > 0.6 ? '#EF4444' : seg.congestion > 0.35 ? '#F59E0B' : '#10B981'
                          }}
                        />
                      </div>
                    </td>
                    <td>
                      <button
                        className="btn-select-sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedSegmentId(seg.id);
                        }}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="analytics-notice-box">
            <HelpCircle size={14} className="text-muted" />
            <span>
              <strong>Scientific Notice:</strong> Forecasts are produced by a calibrated gradient-boosted regressor (XGBoost) trained on cyclical temporal encodings. Does not imply physical actuation.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
