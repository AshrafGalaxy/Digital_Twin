import React from 'react';
import { X, Gauge, Car, ShieldAlert } from 'lucide-react';
import { EntityCurrentState, RoadSegmentAsset, IntersectionAsset } from '../types/twin';

import { ForecastPanel } from './ForecastPanel';

interface EntityDetailDrawerProps {
  entity: RoadSegmentAsset | IntersectionAsset | null;
  liveState: EntityCurrentState | null;
  onClose: () => void;
}

export const EntityDetailDrawer: React.FC<EntityDetailDrawerProps> = ({
  entity,
  liveState,
  onClose
}) => {
  if (!entity) return null;

  const isSegment = 'speedLimitKmh' in entity;
  const speed = liveState?.metrics.averageSpeedKmh;
  const flow = liveState?.metrics.vehicleFlowPerHour;
  const queue = liveState?.metrics.queueLengthMeters;
  const congestion = liveState?.metrics.congestionIndex;
  const sourceMode = liveState?.sourceMode || 'SIMULATION';

  return (
    <aside className="entity-drawer" aria-label="Entity Details">
      <div className="drawer-header">
        <div>
          <span style={{ fontSize: 11, color: 'var(--text-subtle)', textTransform: 'uppercase', fontWeight: 600 }}>
            {isSegment ? 'Road Segment' : 'Intersection'}
          </span>
          <h2 style={{ fontSize: 16, fontWeight: 700, marginTop: 2 }}>{entity.name}</h2>
          <code style={{ fontSize: 11, color: 'var(--text-muted)' }}>{entity.id}</code>
        </div>
        <button onClick={onClose} className="close-btn" aria-label="Close drawer">
          <X size={18} />
        </button>
      </div>

      <div className="drawer-body">
        {/* Provenance Badge & Honesty Disclosure */}
        <div className="drawer-section" style={{
          background: 'var(--bg-surface-elevated)',
          padding: 'var(--space-3)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 12, fontWeight: 600 }}>Data Provenance</span>
            <span className={`provenance-badge badge-${sourceMode.toLowerCase()}`}>
              {sourceMode}
            </span>
          </div>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.4 }}>
            {sourceMode === 'SIMULATION' && 'Metrics are generated via calibrated microscopic simulation (SUMO) and do not represent empirical field sensor measurements.'}
            {sourceMode === 'REPLAY' && 'Metrics are replayed from historical observation surveys.'}
            {sourceMode === 'LIVE' && 'Metrics ingested directly from active corridor virtual detectors.'}
          </p>
        </div>

        {/* Dynamic Telemetry */}
        {isSegment && (
          <div className="drawer-section">
            <span className="drawer-section-title">Current Operational State</span>
            <div className="metrics-grid" style={{ gridTemplateColumns: '1fr 1fr', marginTop: 4 }}>
              <div className="metric-item" style={{ background: 'var(--bg-surface-elevated)', padding: 8, borderRadius: 4 }}>
                <span className="metric-label"><Gauge size={11} /> Mean Speed</span>
                <div>
                  <span className="metric-value">{speed !== undefined ? speed.toFixed(1) : '--'}</span>
                  <span className="metric-unit">km/h</span>
                </div>
              </div>

              <div className="metric-item" style={{ background: 'var(--bg-surface-elevated)', padding: 8, borderRadius: 4 }}>
                <span className="metric-label"><Car size={11} /> Vehicle Flow</span>
                <div>
                  <span className="metric-value">{flow !== undefined ? flow.toFixed(0) : '--'}</span>
                  <span className="metric-unit">veh/h</span>
                </div>
              </div>

              <div className="metric-item" style={{ background: 'var(--bg-surface-elevated)', padding: 8, borderRadius: 4 }}>
                <span className="metric-label">Queue Length</span>
                <div>
                  <span className="metric-value">{queue !== undefined ? queue.toFixed(0) : '--'}</span>
                  <span className="metric-unit">m</span>
                </div>
              </div>

              <div className="metric-item" style={{ background: 'var(--bg-surface-elevated)', padding: 8, borderRadius: 4 }}>
                <span className="metric-label">Congestion</span>
                <div>
                  <span className="metric-value">{congestion !== undefined ? `${(congestion * 100).toFixed(0)}%` : '--'}</span>
                </div>
              </div>
            </div>

            {/* 15-Minute ML Forecast Component */}
            <div style={{ marginTop: 'var(--space-3)' }}>
              <ForecastPanel
                entityType="RoadSegment"
                entityId={entity.id}
                currentValue={speed}
              />
            </div>
          </div>
        )}

        {/* Static Asset Characteristics */}
        <div className="drawer-section">
          <span className="drawer-section-title">Physical Characteristics</span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12 }}>
            {isSegment ? (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-muted">Lanes:</span>
                  <span style={{ fontWeight: 600 }}>{(entity as RoadSegmentAsset).lanes} (Divided Arterial)</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-muted">Speed Limit:</span>
                  <span style={{ fontWeight: 600 }}>{(entity as RoadSegmentAsset).speedLimitKmh} km/h</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-muted">Direction:</span>
                  <span style={{ fontWeight: 600 }}>{(entity as RoadSegmentAsset).direction}</span>
                </div>
              </>
            ) : (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-muted">Control Type:</span>
                  <span style={{ fontWeight: 600 }}>{(entity as IntersectionAsset).controlType}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-muted">Cycle Time:</span>
                  <span style={{ fontWeight: 600 }}>{(entity as IntersectionAsset).cycleTimeSec} seconds</span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Safety & Advisory Notice */}
        <div style={{
          marginTop: 'auto',
          padding: 'var(--space-3)',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(239, 68, 68, 0.08)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          display: 'flex',
          gap: 'var(--space-2)'
        }}>
          <ShieldAlert size={16} color="#EF4444" style={{ flexShrink: 0, marginTop: 2 }} />
          <span style={{ fontSize: 11, color: '#FCA5A5', lineHeight: 1.4 }}>
            Digital Twin Advisory Notice: Platform outputs are advisory decision support. No automated actuation or physical signal modification is permitted.
          </span>
        </div>
      </div>
    </aside>
  );
};
