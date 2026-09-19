import React, { useEffect, useState } from 'react';
import {
  X,
  Gauge,
  Car,
  ShieldAlert,
  ArrowRightLeft,
  GitCompare,
  TrendingDown,
  TrendingUp,
  Minus,
  Layers,
  ChevronRight
} from 'lucide-react';
import { EntityCurrentState, RoadSegmentAsset, IntersectionAsset } from '../types/twin';
import { ForecastPanel } from './ForecastPanel';
import { fetchSegmentComparison, SegmentComparisonResult } from '../services/api';

interface EntityDetailDrawerProps {
  entity: RoadSegmentAsset | IntersectionAsset | null;
  compareEntity?: RoadSegmentAsset | null;
  availableSegments?: RoadSegmentAsset[];
  liveStates?: Record<string, EntityCurrentState>;
  onClose: () => void;
  onSelectCompareEntity?: (segment: RoadSegmentAsset | null) => void;
}

export const EntityDetailDrawer: React.FC<EntityDetailDrawerProps> = ({
  entity,
  compareEntity,
  availableSegments = [],
  liveStates = {},
  onClose,
  onSelectCompareEntity
}) => {
  const [comparisonResult, setComparisonResult] = useState<SegmentComparisonResult | null>(null);
  const [loadingCompare, setLoadingCompare] = useState<boolean>(false);

  if (!entity) return null;

  const isSegment = 'speedLimitKmh' in entity;
  const isComparing = isSegment && !!compareEntity;

  const liveStateA = liveStates[entity.id] || null;
  const speedA = liveStateA?.metrics.averageSpeedKmh;
  const flowA = liveStateA?.metrics.vehicleFlowPerHour;
  const queueA = liveStateA?.metrics.queueLengthMeters;
  const congestionA = liveStateA?.metrics.congestionIndex;
  const sourceModeA = liveStateA?.sourceMode || 'SIMULATION';

  const liveStateB = compareEntity ? liveStates[compareEntity.id] || null : null;
  const speedB = liveStateB?.metrics.averageSpeedKmh;
  const flowB = liveStateB?.metrics.vehicleFlowPerHour;
  const queueB = liveStateB?.metrics.queueLengthMeters;
  const congestionB = liveStateB?.metrics.congestionIndex;

  // Fetch backend comparison whenever compareEntity changes
  useEffect(() => {
    if (isSegment && compareEntity) {
      setLoadingCompare(true);
      fetchSegmentComparison(entity.id, compareEntity.id)
        .then((res) => setComparisonResult(res))
        .catch(() => setComparisonResult(null))
        .finally(() => setLoadingCompare(false));
    } else {
      setComparisonResult(null);
    }
  }, [entity.id, compareEntity, isSegment]);

  // Find opposing bound segment for quick toggle shortcut
  const opposingSegment = isSegment
    ? availableSegments.find(s => {
        if (s.id === entity.id) return false;
        const dirA = (entity as RoadSegmentAsset).direction;
        if (dirA === 'EASTBOUND') return s.direction === 'WESTBOUND';
        if (dirA === 'WESTBOUND') return s.direction === 'EASTBOUND';
        if (dirA === 'NORTHBOUND') return s.direction === 'SOUTHBOUND';
        if (dirA === 'SOUTHBOUND') return s.direction === 'NORTHBOUND';
        return false;
      })
    : null;

  // Helper for LOS calculation
  const getLos = (spd?: number) => {
    if (spd === undefined) return '--';
    if (spd >= 42) return 'A';
    if (spd >= 38) return 'B';
    if (spd >= 32) return 'C';
    if (spd >= 25) return 'D';
    if (spd >= 18) return 'E';
    return 'F';
  };

  const losA = getLos(speedA);
  const losB = getLos(speedB);

  // Computed live deltas (A - B)
  const speedDelta = speedA !== undefined && speedB !== undefined ? speedA - speedB : null;
  const queueDelta = queueA !== undefined && queueB !== undefined ? queueA - queueB : null;
  const flowDelta = flowA !== undefined && flowB !== undefined ? flowA - flowB : null;

  return (
    <aside className={`entity-drawer ${isComparing ? 'comparison-mode' : ''}`} aria-label="Entity Details">
      {/* Drawer Header */}
      <div className="drawer-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 11, color: 'var(--text-subtle)', textTransform: 'uppercase', fontWeight: 600 }}>
              {isComparing ? 'Multi-Segment Comparative Analysis' : isSegment ? 'Road Segment' : 'Intersection'}
            </span>
            {isComparing && (
              <span className="provenance-badge badge-replay" style={{ fontSize: 10, padding: '1px 6px' }}>
                COMPARISON MODE
              </span>
            )}
          </div>
          <h2 style={{ fontSize: 16, fontWeight: 700, marginTop: 2 }}>
            {isComparing ? `${entity.name} vs ${compareEntity.name}` : entity.name}
          </h2>
          <code style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            {isComparing ? `${entity.id} ↔ ${compareEntity.id}` : entity.id}
          </code>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {isComparing && onSelectCompareEntity && (
            <button
              onClick={() => onSelectCompareEntity(null)}
              className="comparison-clear-btn"
              title="Exit comparison and return to single entity view"
            >
              Exit Compare
            </button>
          )}
          <button onClick={onClose} className="close-btn" aria-label="Close drawer">
            <X size={18} />
          </button>
        </div>
      </div>

      <div className="drawer-body">
        {/* Road Segment Comparison Selector Toolbar */}
        {isSegment && onSelectCompareEntity && (
          <div className="drawer-section comparison-toolbar-section">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <span style={{ fontSize: 12, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4 }}>
                <GitCompare size={14} color="#22D3EE" />
                <span>Corridor Comparison</span>
              </span>
              {opposingSegment && !isComparing && (
                <button
                  type="button"
                  className="comparison-quick-btn"
                  onClick={() => onSelectCompareEntity(opposingSegment)}
                  title={`Quick-compare with opposite direction: ${opposingSegment.name}`}
                >
                  <ArrowRightLeft size={12} />
                  <span>Compare Opposing Bound</span>
                </button>
              )}
            </div>

            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <select
                className="comparison-selector-select"
                value={compareEntity?.id || ''}
                onChange={(e) => {
                  const val = e.target.value;
                  if (!val) {
                    onSelectCompareEntity(null);
                  } else {
                    const found = availableSegments.find(s => s.id === val);
                    if (found) onSelectCompareEntity(found);
                  }
                }}
                aria-label="Select corridor segment to compare against"
              >
                <option value="">-- Select segment to compare side-by-side --</option>
                {availableSegments
                  .filter(s => s.id !== entity.id)
                  .map(s => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.direction}) - {s.speedLimitKmh} km/h
                    </option>
                  ))}
              </select>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* COMPARISON MODE LAYOUT (P1-C) */}
        {/* ============================================================ */}
        {isComparing && compareEntity ? (
          <>
            {/* Directional Imbalance Banner */}
            {loadingCompare && (
              <div style={{ fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic', padding: '2px 0' }}>
                Analyzing comparative corridor telemetry...
              </div>
            )}
            {comparisonResult?.directionalImbalance && (
              <div className={`imbalance-banner imbalance-${comparisonResult.directionalImbalance.severity.toLowerCase()}`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                    Directional Imbalance: {comparisonResult.directionalImbalance.severity}
                  </span>
                  {comparisonResult.directionalImbalance.dominantCongestionDirection && (
                    <span className="provenance-badge" style={{ background: 'rgba(0,0,0,0.3)', color: '#FFF' }}>
                      Bottleneck: {comparisonResult.directionalImbalance.dominantCongestionDirection}
                    </span>
                  )}
                </div>
                <p style={{ fontSize: 11.5, marginTop: 4, lineHeight: 1.45 }}>
                  {comparisonResult.directionalImbalance.summary}
                </p>
              </div>
            )}

            {/* Side-by-Side Comparison Grid */}
            <div className="comparison-grid-side-by-side">
              {/* Column A: Primary Selected Segment */}
              <div className="comparison-col-card segment-a">
                <div className="comp-card-header">
                  <span className="comp-tag tag-a">SEGMENT A</span>
                  <span className="comp-name">{entity.name}</span>
                  <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
                    <span className="badge-subtle">{(entity as RoadSegmentAsset).direction}</span>
                    <span className="badge-subtle">{(entity as RoadSegmentAsset).speedLimitKmh} km/h limit</span>
                  </div>
                </div>

                {/* Metrics Breakdown */}
                <div className="comp-metric-row">
                  <span className="text-muted">Mean Speed:</span>
                  <span className="font-mono font-bold" style={{ fontSize: 15, color: speedA !== undefined && speedA < 25 ? '#EF4444' : '#10B981' }}>
                    {speedA !== undefined ? `${speedA.toFixed(1)} km/h` : '--'}
                  </span>
                </div>

                <div className="comp-metric-row">
                  <span className="text-muted">Level of Service:</span>
                  <span className={`los-pill los-${losA.toLowerCase()}`}>LOS {losA}</span>
                </div>

                <div className="comp-metric-row">
                  <span className="text-muted">Queue Length:</span>
                  <span className="font-mono">{queueA !== undefined ? `${queueA.toFixed(0)} m` : '--'}</span>
                </div>

                <div className="comp-metric-row">
                  <span className="text-muted">Congestion:</span>
                  <span className="font-mono">{congestionA !== undefined ? `${(congestionA * 100).toFixed(0)}%` : '--'}</span>
                </div>

                <div className="comp-metric-row">
                  <span className="text-muted">Vehicle Flow:</span>
                  <span className="font-mono">{flowA !== undefined ? `${flowA.toFixed(0)} veh/h` : '--'}</span>
                </div>
              </div>

              {/* Column B: Comparison Target Segment */}
              <div className="comparison-col-card segment-b">
                <div className="comp-card-header">
                  <span className="comp-tag tag-b">SEGMENT B</span>
                  <span className="comp-name">{compareEntity.name}</span>
                  <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
                    <span className="badge-subtle">{compareEntity.direction}</span>
                    <span className="badge-subtle">{compareEntity.speedLimitKmh} km/h limit</span>
                  </div>
                </div>

                {/* Metrics Breakdown */}
                <div className="comp-metric-row">
                  <span className="text-muted">Mean Speed:</span>
                  <span className="font-mono font-bold" style={{ fontSize: 15, color: speedB !== undefined && speedB < 25 ? '#EF4444' : '#10B981' }}>
                    {speedB !== undefined ? `${speedB.toFixed(1)} km/h` : '--'}
                  </span>
                </div>

                <div className="comp-metric-row">
                  <span className="text-muted">Level of Service:</span>
                  <span className={`los-pill los-${losB.toLowerCase()}`}>LOS {losB}</span>
                </div>

                <div className="comp-metric-row">
                  <span className="text-muted">Queue Length:</span>
                  <span className="font-mono">{queueB !== undefined ? `${queueB.toFixed(0)} m` : '--'}</span>
                </div>

                <div className="comp-metric-row">
                  <span className="text-muted">Congestion:</span>
                  <span className="font-mono">{congestionB !== undefined ? `${(congestionB * 100).toFixed(0)}%` : '--'}</span>
                </div>

                <div className="comp-metric-row">
                  <span className="text-muted">Vehicle Flow:</span>
                  <span className="font-mono">{flowB !== undefined ? `${flowB.toFixed(0)} veh/h` : '--'}</span>
                </div>
              </div>
            </div>

            {/* Differential Variance Table (A vs B) */}
            <div className="drawer-section" style={{ background: 'var(--bg-surface-elevated)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)' }}>
              <span className="drawer-section-title" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Layers size={13} />
                <span>Directional Variance Deltas (A − B)</span>
              </span>

              <div className="deltas-table" style={{ marginTop: 8 }}>
                <div className="delta-row">
                  <span className="delta-label">Speed Variance:</span>
                  <span className={`delta-badge ${speedDelta !== null && speedDelta > 0 ? 'delta-positive' : speedDelta !== null && speedDelta < 0 ? 'delta-negative' : 'delta-neutral'}`}>
                    {speedDelta !== null && speedDelta > 0 ? <TrendingUp size={11} /> : speedDelta !== null && speedDelta < 0 ? <TrendingDown size={11} /> : <Minus size={11} />}
                    {speedDelta !== null ? `${speedDelta > 0 ? '+' : ''}${speedDelta.toFixed(1)} km/h` : '--'}
                  </span>
                </div>

                <div className="delta-row">
                  <span className="delta-label">Queue Disparity:</span>
                  <span className={`delta-badge ${queueDelta !== null && queueDelta > 0 ? 'delta-negative' : queueDelta !== null && queueDelta < 0 ? 'delta-positive' : 'delta-neutral'}`}>
                    {queueDelta !== null ? `${queueDelta > 0 ? '+' : ''}${queueDelta.toFixed(0)} m` : '--'}
                  </span>
                </div>

                <div className="delta-row">
                  <span className="delta-label">Flow Differential:</span>
                  <span className="delta-badge delta-neutral font-mono">
                    {flowDelta !== null ? `${flowDelta > 0 ? '+' : ''}${flowDelta.toFixed(0)} veh/h` : '--'}
                  </span>
                </div>
              </div>
            </div>

            {/* Dual 15-Minute ML Near-Term Forecasts */}
            <div className="drawer-section">
              <span className="drawer-section-title">Segment A 15-Min Forecast ({entity.name})</span>
              <ForecastPanel
                entityType="RoadSegment"
                entityId={entity.id}
                currentValue={speedA}
              />
            </div>

            <div className="drawer-section" style={{ marginTop: 'var(--space-3)' }}>
              <span className="drawer-section-title">Segment B 15-Min Forecast ({compareEntity.name})</span>
              <ForecastPanel
                entityType="RoadSegment"
                entityId={compareEntity.id}
                currentValue={speedB}
              />
            </div>
          </>
        ) : (
          /* ============================================================ */
          /* SINGLE ENTITY DETAIL MODE */
          /* ============================================================ */
          <>
            {/* Provenance Badge & Honesty Disclosure */}
            <div className="drawer-section" style={{
              background: 'var(--bg-surface-elevated)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-color)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 12, fontWeight: 600 }}>Data Provenance</span>
                <span className={`provenance-badge badge-${sourceModeA.toLowerCase()}`}>
                  {sourceModeA}
                </span>
              </div>
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.4 }}>
                {sourceModeA === 'SIMULATION' && 'Metrics are generated via calibrated microscopic simulation (SUMO) and do not represent empirical field sensor measurements.'}
                {sourceModeA === 'REPLAY' && 'Metrics are replayed from historical observation surveys.'}
                {sourceModeA === 'LIVE' && 'Metrics ingested directly from active corridor virtual detectors.'}
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
                      <span className="metric-value">{speedA !== undefined ? speedA.toFixed(1) : '--'}</span>
                      <span className="metric-unit">km/h</span>
                    </div>
                  </div>

                  <div className="metric-item" style={{ background: 'var(--bg-surface-elevated)', padding: 8, borderRadius: 4 }}>
                    <span className="metric-label"><Car size={11} /> Vehicle Flow</span>
                    <div>
                      <span className="metric-value">{flowA !== undefined ? flowA.toFixed(0) : '--'}</span>
                      <span className="metric-unit">veh/h</span>
                    </div>
                  </div>

                  <div className="metric-item" style={{ background: 'var(--bg-surface-elevated)', padding: 8, borderRadius: 4 }}>
                    <span className="metric-label">Queue Length</span>
                    <div>
                      <span className="metric-value">{queueA !== undefined ? queueA.toFixed(0) : '--'}</span>
                      <span className="metric-unit">m</span>
                    </div>
                  </div>

                  <div className="metric-item" style={{ background: 'var(--bg-surface-elevated)', padding: 8, borderRadius: 4 }}>
                    <span className="metric-label">Congestion</span>
                    <div>
                      <span className="metric-value">{congestionA !== undefined ? `${(congestionA * 100).toFixed(0)}%` : '--'}</span>
                    </div>
                  </div>
                </div>

                {/* 15-Minute ML Forecast Component */}
                <div style={{ marginTop: 'var(--space-3)' }}>
                  <ForecastPanel
                    entityType="RoadSegment"
                    entityId={entity.id}
                    currentValue={speedA}
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
                    {(entity as IntersectionAsset).connectedSegments && (
                      <div style={{ marginTop: 4 }}>
                        <span className="text-muted">Connected Segments:</span>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 3, marginTop: 4 }}>
                          {(entity as IntersectionAsset).connectedSegments?.map((segId: string) => (
                            <div key={segId} style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--text-main)', fontSize: 11 }}>
                              <ChevronRight size={11} color="#22D3EE" />
                              <code>{segId}</code>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </>
        )}

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
