import React from 'react';
import { Gauge, Zap, TrendingUp, Layers } from 'lucide-react';
import { SourceMode } from '../types/twin';
import { ProvenanceBadge } from './ProvenanceBadge';

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
  // Determine overall corridor state per UI_UX_SPEC §7.6
  const corridorState = congestionIndex > 0.6
    ? { label: 'STRESSED', color: '#EF4444', bg: 'rgba(239, 68, 68, 0.12)' }
    : congestionIndex > 0.3
    ? { label: 'ELEVATED', color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.12)' }
    : { label: 'NOMINAL', color: '#10B981', bg: 'rgba(16, 185, 129, 0.12)' };

  return (
    <div className="corridor-metrics-card">
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="card-title">Corridor Telemetry</span>
          <span
            className="status-pill"
            style={{
              color: corridorState.color,
              background: corridorState.bg,
              border: `1px solid ${corridorState.color}40`,
              fontWeight: 700,
              fontSize: '12px'
            }}
          >
            {corridorState.label}
          </span>
        </div>
        <ProvenanceBadge mode={sourceMode} />
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

      {/* Telemetric Basis & Advisory Notice per UI_UX_SPEC §7.6 */}
      <div style={{
        marginTop: '8px',
        paddingTop: '6px',
        borderTop: '1px solid var(--border-color)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '12px',
        color: 'var(--text-muted)'
      }}>
        <span>Basis: {sourceMode === 'SIMULATION' ? 'Microscopic Simulation (SUMO)' : 'Replay Survey Telemetry'}</span>
        <span>Advisory Decision Support</span>
      </div>
    </div>
  );
};
