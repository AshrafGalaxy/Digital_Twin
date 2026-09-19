import React from 'react';
import { Gauge, Zap, TrendingUp, Layers } from 'lucide-react';
import { SourceMode } from '../types/twin';

interface CorridorMetricsCardProps {
  averageSpeed: number;
  congestionIndex: number;
  energyDemandKw: number;
  activeSensors: number;
  sourceMode: SourceMode;
}

export const CorridorMetricsCard: React.FC<CorridorMetricsCardProps> = ({
  averageSpeed,
  congestionIndex,
  energyDemandKw,
  activeSensors,
  sourceMode
}) => {
  return (
    <div className="corridor-metrics-card">
      <div className="card-header">
        <span className="card-title">Corridor Telemetry</span>
        <span className={`provenance-badge badge-${sourceMode.toLowerCase()}`}>
          {sourceMode}
        </span>
      </div>

      <div className="metrics-grid">
        <div className="metric-item">
          <span className="metric-label">
            <Gauge size={12} style={{ display: 'inline', marginRight: 4 }} />
            Avg Arterial Speed
          </span>
          <div>
            <span className="metric-value">{averageSpeed.toFixed(1)}</span>
            <span className="metric-unit">km/h</span>
          </div>
        </div>

        <div className="metric-item">
          <span className="metric-label">
            <TrendingUp size={12} style={{ display: 'inline', marginRight: 4 }} />
            Congestion Index
          </span>
          <div>
            <span className="metric-value" style={{
              color: congestionIndex > 0.6 ? '#EF4444' : congestionIndex > 0.3 ? '#F59E0B' : '#10B981'
            }}>
              {(congestionIndex * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        <div className="metric-item">
          <span className="metric-label">
            <Zap size={12} style={{ display: 'inline', marginRight: 4 }} />
            Commercial Energy
          </span>
          <div>
            <span className="metric-value">{energyDemandKw.toFixed(0)}</span>
            <span className="metric-unit">kW</span>
          </div>
        </div>

        <div className="metric-item">
          <span className="metric-label">
            <Layers size={12} style={{ display: 'inline', marginRight: 4 }} />
            Active Sensors
          </span>
          <div>
            <span className="metric-value">{activeSensors}</span>
            <span className="metric-unit">nodes</span>
          </div>
        </div>
      </div>
    </div>
  );
};
