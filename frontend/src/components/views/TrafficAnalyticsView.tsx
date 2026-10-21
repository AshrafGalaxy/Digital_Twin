import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Car,
  Filter,
  Layers,
  HelpCircle,
  Sliders,
  Activity,
  Radio,
  Clock,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { RoadSegmentAsset, EntityCurrentState, SourceMode, SPaTState } from '../../types/twin';
import { ForecastPanel } from '../ForecastPanel';
import { WebsterTimingModal } from '../traffic/WebsterTimingModal';
import {
  fetchCorridorLOS,
  CorridorLOSResponse,
  SegmentLOSRecord,
  fetchIntersectionSPaT
} from '../../services/api';

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
  const [selectedIntersectionId, setSelectedIntersectionId] = useState<string>(
    'urn:ngsi-ld:Intersection:PUNE:INT-VN-01'
  );
  const [showWebsterModal, setShowWebsterModal] = useState<boolean>(false);
  const [spatData, setSpatData] = useState<SPaTState | null>(null);
  const [loadingSpat, setLoadingSpat] = useState<boolean>(false);
  const [policyStandard, setPolicyStandard] = useState<'INDO_HCM' | 'US_HCM_6TH'>('INDO_HCM');
  const [corridorLosData, setCorridorLosData] = useState<CorridorLOSResponse | null>(null);
  const [loadingLos, setLoadingLos] = useState<boolean>(false);

  // Poll real-time Signal Phase and Timing (SPaT) telemetry
  useEffect(() => {
    let isMounted = true;
    const loadSPaT = async () => {
      try {
        setLoadingSpat(true);
        const data = await fetchIntersectionSPaT(selectedIntersectionId);
        if (isMounted) {
          setSpatData(data);
        }
      } catch (err) {
        console.debug('SPaT fetch notice:', err);
      } finally {
        if (isMounted) setLoadingSpat(false);
      }
    };

    loadSPaT();
    const interval = setInterval(loadSPaT, 2000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [selectedIntersectionId]);

  // Fetch canonical corridor LOS from backend engine
  useEffect(() => {
    let isMounted = true;
    const loadLOS = async () => {
      try {
        setLoadingLos(true);
        const data = await fetchCorridorLOS(policyStandard, sourceMode);
        if (isMounted) {
          setCorridorLosData(data);
        }
      } catch (err) {
        console.warn('Could not load canonical corridor LOS, using fallback:', err);
      } finally {
        if (isMounted) {
          setLoadingLos(false);
        }
      }
    };

    loadLOS();
    const interval = setInterval(loadLOS, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [policyStandard, sourceMode]);

  const selectedSegment = roadSegments.find(s => s.id === selectedSegmentId) || roadSegments[0];
  const currentState = selectedSegment ? liveStates[selectedSegment.id] : null;
  const currentSpeed = currentState?.metrics?.averageSpeedKmh ?? 24.5;
  const currentFlow = currentState?.metrics?.vehicleFlowPerHour ?? 1250;

  // Find canonical segment record if available
  const canonicalRecord: SegmentLOSRecord | undefined = corridorLosData?.segments?.find(
    s => s.segmentId === selectedSegmentId || s.segmentId.endsWith(selectedSegmentId)
  );

  const fallbackComputeLos = (spd: number): string => {
    if (spd >= 42) return 'A';
    if (spd >= 38) return 'B';
    if (spd >= 32) return 'C';
    if (spd >= 25) return 'D';
    if (spd >= 18) return 'E';
    return 'F';
  };

  const activeLosGrade = canonicalRecord?.levelOfService || fallbackComputeLos(currentSpeed);
  const activeVcRatio = canonicalRecord?.volumeCapacityRatio ?? (currentFlow / 2400);
  const activeDensity = canonicalRecord?.densityVehKm ?? (currentFlow / Math.max(currentSpeed, 1));
  const activeCondition = canonicalRecord?.operationalCondition || (
    currentSpeed < 20
      ? 'Forced or breakdown flow: severe queue spillback.'
      : currentSpeed < 32
      ? 'Approaching capacity: long signal delays.'
      : 'Stable flow: maneuvers unhindered.'
  );

  // Rank segments using canonical records if available, otherwise live telemetry
  const rankedSegments = [...roadSegments].map(seg => {
    const s = liveStates[seg.id];
    const rec = corridorLosData?.segments?.find(
      r => r.segmentId === seg.id || r.segmentId.endsWith(seg.id)
    );

    const spd = rec?.speedKmh ?? (s?.metrics?.averageSpeedKmh ?? seg.speedLimitKmh);
    const flow = rec?.flowVehHr ?? (s?.metrics?.vehicleFlowPerHour ?? 1200);
    const vc = rec?.volumeCapacityRatio ?? (flow / (seg.capacityVehPerHour || 2400));
    const density = rec?.densityVehKm ?? (flow / Math.max(spd, 1));
    const los = rec?.levelOfService || fallbackComputeLos(spd);
    const condition = rec?.operationalCondition || 'Nominal operational state.';

    return {
      ...seg,
      speed: spd,
      flow,
      vc,
      density,
      los,
      condition,
      quality: s?.qualityStatus || 'VALID'
    };
  }).sort((a, b) => b.vc - a.vc); // Sort by highest V/C ratio (most congested first)

  return (
    <div className="view-container traffic-analytics-view">
      {/* View Header */}
      <div className="view-header">
        <div>
          <h1 className="view-title">Corridor Traffic Analytics & Mobility Forecasting</h1>
          <p className="view-subtitle">
            Near-term speed forecasting, hydrodynamic state evaluation, and Level of Service (LOS) under canonical capacity standards.
          </p>
        </div>
        <div className="view-header-badges">
          <span className={`provenance-badge badge-${sourceMode.toLowerCase()}`}>
            {sourceMode}
          </span>
          <span className="provenance-badge badge-simulation">
            {policyStandard === 'INDO_HCM' ? 'IRC:106 PROFILE' : 'HCM 6TH PROFILE'}
          </span>
          <span className="provenance-badge badge-predicted">15-MIN XGBOOST</span>
        </div>
      </div>

      {/* Segment Selector & Policy Standard Bar */}
      <div className="analytics-filter-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
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

        {/* Policy Standard Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Sliders size={14} className="text-muted" />
            <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
              LOS Standard {loadingLos ? '(evaluating...)' : ''}:
            </span>
          </div>
          <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-surface-elevated)', padding: '2px', borderRadius: '4px' }}>
            <button
              onClick={() => setPolicyStandard('INDO_HCM')}
              style={{
                border: 'none',
                background: policyStandard === 'INDO_HCM' ? 'rgba(45, 212, 191, 0.2)' : 'transparent',
                color: policyStandard === 'INDO_HCM' ? '#2DD4BF' : 'var(--color-text-muted)',
                fontWeight: policyStandard === 'INDO_HCM' ? 600 : 400,
                fontSize: '11px',
                padding: '4px 8px',
                borderRadius: '3px',
                cursor: 'pointer'
              }}
              title="Indian Highway Capacity Manual (IRC:106 dual criteria)"
            >
              Indo-HCM (IRC:106)
            </button>
            <button
              onClick={() => setPolicyStandard('US_HCM_6TH')}
              style={{
                border: 'none',
                background: policyStandard === 'US_HCM_6TH' ? 'rgba(45, 212, 191, 0.2)' : 'transparent',
                color: policyStandard === 'US_HCM_6TH' ? '#2DD4BF' : 'var(--color-text-muted)',
                fontWeight: policyStandard === 'US_HCM_6TH' ? 600 : 400,
                fontSize: '11px',
                padding: '4px 8px',
                borderRadius: '3px',
                cursor: 'pointer'
              }}
              title="US Highway Capacity Manual 6th Edition"
            >
              US HCM 6th Ed
            </button>
          </div>

          <div className="analytics-meta-pill">
            <Layers size={14} className="text-muted" />
            <span>Speed Limit: {selectedSegment?.speedLimitKmh || 45} km/h</span>
          </div>
        </div>
      </div>

      {/* Corridor Summary Banner */}
      {corridorLosData?.corridorSummary && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          padding: '12px 16px',
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-sm)',
          marginTop: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Activity size={18} color="#2DD4BF" />
            <div>
              <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Corridor Aggregate Condition ({policyStandard === 'INDO_HCM' ? 'IRC:106' : 'US HCM'})
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '2px' }}>
                <span className={`los-badge los-${corridorLosData.corridorSummary.corridorLevelOfService.toLowerCase()}`}>
                  LOS {corridorLosData.corridorSummary.corridorLevelOfService}
                </span>
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-main)' }}>
                  Avg Speed: {corridorLosData.corridorSummary.averageSpeedKmh} km/h
                </span>
                <span style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>
                  | Avg V/C: {corridorLosData.corridorSummary.averageVolumeCapacityRatio.toFixed(2)}
                </span>
                <span style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>
                  | Avg Density: {corridorLosData.corridorSummary.averageDensityVehKm} veh/km
                </span>
              </div>
            </div>
          </div>

          {corridorLosData.corridorSummary.criticalSegmentId && (
            <div style={{ fontSize: '12px', color: '#F59E0B', background: 'rgba(245, 158, 11, 0.1)', padding: '6px 12px', borderRadius: '4px', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
              <strong>Critical Bottleneck:</strong> {corridorLosData.corridorSummary.criticalSegmentId.split(':').pop()}
            </div>
          )}
        </div>
      )}

      {/* Real-Time Signal Phase and Timing (SPaT) Controller Monitor */}
      <div className="analytics-card" style={{ marginTop: '12px' }}>
        <div className="analytics-card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Radio size={18} color="#10B981" />
            <span className="card-title">Real-Time Signal Phase and Timing (SPaT) Controller Monitor</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            {/* Intersection Selector */}
            <select
              style={{
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-color)',
                color: 'var(--color-text-main)',
                fontSize: '11px',
                padding: '4px 8px',
                borderRadius: '4px'
              }}
              value={selectedIntersectionId}
              onChange={(e) => setSelectedIntersectionId(e.target.value)}
            >
              <option value="urn:ngsi-ld:Intersection:PUNE:INT-VN-01">Viman Nagar Chowk (INT-VN-01)</option>
              <option value="urn:ngsi-ld:Intersection:PUNE:INT-SN-01">Somnath Nagar Chowk (INT-SN-01)</option>
            </select>

            <button
              type="button"
              onClick={() => setShowWebsterModal(true)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                background: 'rgba(59, 130, 246, 0.15)',
                border: '1px solid rgba(59, 130, 246, 0.4)',
                color: '#60A5FA',
                fontSize: '11px',
                fontWeight: 600,
                padding: '4px 8px',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
              title="Inspect Webster optimal cycle time and green splits"
            >
              <Sliders size={12} />
              Webster Plan
            </button>

            {/* Freshness SLA Badge */}
            {spatData && (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '11px',
                  fontWeight: 600,
                  padding: '3px 8px',
                  borderRadius: '12px',
                  border: `1px solid ${
                    spatData.freshnessStatus === 'VALID'
                      ? 'rgba(16, 185, 129, 0.4)'
                      : spatData.freshnessStatus === 'STALE'
                      ? 'rgba(245, 158, 11, 0.4)'
                      : 'rgba(239, 68, 68, 0.4)'
                  }`,
                  background:
                    spatData.freshnessStatus === 'VALID'
                      ? 'rgba(16, 185, 129, 0.1)'
                      : spatData.freshnessStatus === 'STALE'
                      ? 'rgba(245, 158, 11, 0.1)'
                      : 'rgba(239, 68, 68, 0.1)',
                  color:
                    spatData.freshnessStatus === 'VALID'
                      ? '#10B981'
                      : spatData.freshnessStatus === 'STALE'
                      ? '#F59E0B'
                      : '#EF4444'
                }}
              >
                {spatData.freshnessStatus === 'VALID' ? (
                  <CheckCircle2 size={12} />
                ) : (
                  <AlertTriangle size={12} />
                )}
                SLA: {spatData.freshnessStatus} ({spatData.freshnessSeconds.toFixed(1)}s)
              </span>
            )}
          </div>
        </div>

        {spatData ? (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '12px',
            alignItems: 'center',
            padding: '8px 0'
          }}>
            {/* Visual Signal Aspect */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '10px 14px',
              background: 'var(--bg-surface-elevated)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)'
            }}>
              {/* 3 Aspect Signal Head */}
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '5px',
                background: '#0F172A',
                padding: '6px',
                borderRadius: '12px',
                border: '2px solid #334155'
              }}>
                <div style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  background: spatData.phaseColor === 'RED' ? '#EF4444' : '#475569',
                  boxShadow: spatData.phaseColor === 'RED' ? '0 0 8px #EF4444' : 'none',
                  transition: 'background 0.2s ease'
                }} />
                <div style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  background: spatData.phaseColor === 'YELLOW' || spatData.phaseColor === 'FLASHING_YELLOW' ? '#F59E0B' : '#475569',
                  boxShadow: spatData.phaseColor === 'YELLOW' ? '0 0 8px #F59E0B' : 'none',
                  transition: 'background 0.2s ease'
                }} />
                <div style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  background: spatData.phaseColor === 'GREEN' ? '#10B981' : '#475569',
                  boxShadow: spatData.phaseColor === 'GREEN' ? '0 0 8px #10B981' : 'none',
                  transition: 'background 0.2s ease'
                }} />
              </div>

              <div>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                  Active Aspect
                </div>
                <div style={{
                  fontSize: '15px',
                  fontWeight: 700,
                  color: spatData.phaseColor === 'GREEN' ? '#10B981' : spatData.phaseColor === 'YELLOW' ? '#F59E0B' : '#EF4444',
                  marginTop: '2px'
                }}>
                  {spatData.phaseColor}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                  Phase {spatData.activePhase}
                </div>
              </div>
            </div>

            {/* Active Stage Name */}
            <div style={{
              padding: '10px 14px',
              background: 'var(--bg-surface-elevated)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)'
            }}>
              <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Controlled Movement
              </div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-main)', marginTop: '2px' }}>
                {spatData.activePhaseName}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                Controller: {spatData.controllerMode}
              </div>
            </div>

            {/* Countdown Timer */}
            <div style={{
              padding: '10px 14px',
              background: 'var(--bg-surface-elevated)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              <Clock size={20} color="#2DD4BF" />
              <div>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                  Stage Countdown
                </div>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#2DD4BF', marginTop: '1px' }}>
                  {spatData.timeToNextPhaseSec.toFixed(1)} <small style={{ fontSize: '12px', fontWeight: 400 }}>sec</small>
                </div>
              </div>
            </div>

            {/* Cycle Progress */}
            <div style={{
              padding: '10px 14px',
              background: 'var(--bg-surface-elevated)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-color)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--color-text-muted)' }}>
                <span>CYCLE ELAPSED</span>
                <span>{spatData.elapsedCycleSec.toFixed(0)}s / {spatData.cycleLengthSec}s</span>
              </div>
              <div style={{
                width: '100%',
                height: '6px',
                background: '#334155',
                borderRadius: '3px',
                marginTop: '6px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${Math.min(100, Math.max(0, (spatData.elapsedCycleSec / spatData.cycleLengthSec) * 100))}%`,
                  height: '100%',
                  background: '#2DD4BF',
                  transition: 'width 0.5s ease'
                }} />
              </div>
            </div>
          </div>
        ) : (
          <div style={{ padding: '16px', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '12px' }}>
            {loadingSpat ? 'Connecting to controller SPaT feed...' : 'No active SPaT controller telemetry available.'}
          </div>
        )}
      </div>

      {/* Main Grid: Forecast & Overview */}
      <div className="analytics-grid-two-col" style={{ marginTop: '12px' }}>
        {/* Left Column: Current State & Forecast Panel */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Car size={18} color="#2DD4BF" />
              <span className="card-title">Live State & Predictive Inference</span>
            </div>
            <span className="provenance-badge badge-predicted">PREDICTED</span>
          </div>

          <div className="quick-metrics-row" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
            <div className="metric-box">
              <span className="metric-box-label">Observed Speed</span>
              <span className="metric-box-val" style={{ color: currentSpeed < 20 ? '#EF4444' : '#10B981' }}>
                {currentSpeed.toFixed(1)} <small>km/h</small>
              </span>
            </div>
            <div className="metric-box">
              <span className="metric-box-label">Flow Rate</span>
              <span className="metric-box-val">
                {canonicalRecord?.flowVehHr ?? currentFlow} <small>vph</small>
              </span>
            </div>
            <div className="metric-box">
              <span className="metric-box-label">Density</span>
              <span className="metric-box-val">
                {activeDensity.toFixed(1)} <small>k</small>
              </span>
            </div>
            <div className="metric-box">
              <span className="metric-box-label">V/C Ratio</span>
              <span className="metric-box-val" style={{ color: activeVcRatio > 0.85 ? '#EF4444' : activeVcRatio > 0.7 ? '#F59E0B' : '#10B981' }}>
                {activeVcRatio.toFixed(2)}
              </span>
            </div>
            <div className="metric-box">
              <span className="metric-box-label">Level of Service</span>
              <span className="metric-box-val" style={{ color: activeLosGrade === 'F' || activeLosGrade === 'E' ? '#EF4444' : activeLosGrade === 'D' || activeLosGrade === 'C' ? '#F59E0B' : '#10B981' }}>
                LOS {activeLosGrade}
              </span>
            </div>
          </div>

          {/* Operational Condition Description */}
          <div style={{
            fontSize: '12px',
            color: 'var(--color-text-secondary)',
            background: 'var(--bg-surface-elevated)',
            padding: '8px 12px',
            borderRadius: 'var(--radius-sm)',
            borderLeft: `3px solid ${activeLosGrade === 'F' || activeLosGrade === 'E' ? '#EF4444' : activeLosGrade === 'D' || activeLosGrade === 'C' ? '#F59E0B' : '#10B981'}`,
            marginBottom: '12px'
          }}>
            <strong style={{ color: 'var(--color-text-main)' }}>Operational State:</strong> {activeCondition}
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
            <span className="text-muted" style={{ fontSize: '12px' }}>
              {policyStandard === 'INDO_HCM' ? 'Ranked by V/C (IRC:106)' : 'Ranked by V/C (US HCM)'}
            </span>
          </div>

          <div className="table-responsive">
            <table className="analytics-table">
              <thead>
                <tr>
                  <th>Segment</th>
                  <th>Dir</th>
                  <th>Speed</th>
                  <th>Flow</th>
                  <th>V/C</th>
                  <th>Density</th>
                  <th>LOS</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {rankedSegments.length === 0 && (
                  <tr>
                    <td colSpan={8} style={{ textAlign: 'center', padding: '24px', color: 'var(--color-text-muted)' }}>
                      No corridor road segments available in current telemetry mode.
                    </td>
                  </tr>
                )}
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
                      <span style={{ fontSize: '12px' }}>{Math.round(seg.flow)} vph</span>
                    </td>
                    <td>
                      <span style={{ fontWeight: 600, color: seg.vc > 0.85 ? '#EF4444' : seg.vc > 0.70 ? '#F59E0B' : '#10B981' }}>
                        {seg.vc.toFixed(2)}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '12px' }}>{seg.density.toFixed(1)} k</span>
                    </td>
                    <td>
                      <span className={`los-badge los-${seg.los.toLowerCase()}`}>
                        {seg.los}
                      </span>
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
              <strong>Scientific Notice:</strong> Level of Service is evaluated using the selected capacity standard ({policyStandard === 'INDO_HCM' ? 'IRC:106 Indian Highway Capacity Manual dual criteria' : 'TRB Highway Capacity Manual 6th Edition'}). Speed forecasts are produced by calibrated gradient-boosted models with conformal uncertainty bounds. Does not imply physical actuation.
            </span>
          </div>
        </div>
      </div>

      {/* Webster Delay-Minimizing Timing Plan Modal */}
      <WebsterTimingModal
        isOpen={showWebsterModal}
        intersectionId={selectedIntersectionId}
        onClose={() => setShowWebsterModal(false)}
      />
    </div>
  );
};

