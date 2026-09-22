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
    ? { label: 'STRESSED', color: '#F43F5E', bg: 'rgba(244, 63, 94, 0.15)' }
    : congestionIndex > 0.3
    ? { label: 'ELEVATED', color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.15)' }
    : { label: 'NOMINAL', color: '#10B981', bg: 'rgba(16, 185, 129, 0.15)' };

  return (
    <div className="corridor-metrics-card">
      <div className="card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {sourceMode !== 'REPLAY' && (
            <span className="live-dot-ping" title="Real-time live telemetry stream active" />
          )}
          <span className="card-title">Corridor Telemetry</span>
          <span
            className="status-pill"
            style={{
              color: corridorState.color,
              background: corridorState.bg,
              border: `1px solid ${corridorState.color}40`,
              fontWeight: 700,
              fontSize: '10.5px',
              padding: '1px 6px',
              letterSpacing: '0.4px'
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
            <Gauge size={11} style={{ display: 'inline', marginRight: 4, opacity: 0.8 }} />
            Avg Arterial Speed
          </span>
          <div>
            <span className="metric-value font-mono">{averageSpeed.toFixed(1)}</span>
            <span className="metric-unit">km/h</span>
          </div>
        </div>

        <div className="metric-item">
          <span className="metric-label">
            <TrendingUp size={11} style={{ display: 'inline', marginRight: 4, opacity: 0.8 }} />
            Congestion Index
          </span>
          <div>
            <span className="metric-value font-mono" style={{
              color: congestionIndex > 0.6 ? '#F43F5E' : congestionIndex > 0.3 ? '#F59E0B' : '#10B981'
            }}>
              {(congestionIndex * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        <div className="metric-item">
          <span className="metric-label">
            <Zap size={11} style={{ display: 'inline', marginRight: 4, opacity: 0.8 }} />
            Commercial Energy
          </span>
          <div>
            <span className="metric-value font-mono">{energyDemandKw.toFixed(0)}</span>
            <span className="metric-unit">kW</span>
          </div>
        </div>

        <div className="metric-item">
          <span className="metric-label">
            <Layers size={11} style={{ display: 'inline', marginRight: 4, opacity: 0.8 }} />
            Active Sensors
          </span>
          <div>
            <span className="metric-value font-mono">{activeSensors}</span>
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
        fontSize: '11px',
        color: 'var(--text-muted)'
      }}>
        <span>Basis: {sourceMode === 'SIMULATION' ? 'SUMO Physics' : 'Replay Telemetry'}</span>
        <span style={{ color: '#10B981', fontWeight: 500 }}>Advisory Only</span>
      </div>
    </div>
  );
};
