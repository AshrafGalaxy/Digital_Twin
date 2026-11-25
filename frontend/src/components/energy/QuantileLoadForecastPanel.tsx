import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  RefreshCw,
  ShieldAlert,
  TrendingUp
} from 'lucide-react';
import {
  fetchMultiHorizonLoadForecast,
  MultiHorizonLoadForecastResponse,
  QuantileHorizonForecast
} from '../../services/api';

export interface QuantileLoadForecastPanelProps {
  buildingId: string;
  currentKw?: number;
  contractDemandKw?: number;
}

function formatHorizonShort(minutes: number): string {
  if (minutes === 15) return '15m';
  if (minutes === 60) return '60m';
  if (minutes === 240) return '4h';
  if (minutes === 1440) return '24h';
  if (minutes >= 60 && minutes % 60 === 0) return `${minutes / 60}h`;
  return `${minutes}m`;
}

function formatHorizonFull(minutes: number): string {
  if (minutes === 15) return '15m';
  if (minutes === 60) return '60m';
  if (minutes === 240) return '4h (240m)';
  if (minutes === 1440) return '24h (1440m)';
  if (minutes >= 60 && minutes % 60 === 0) return `${minutes / 60}h (${minutes}m)`;
  return `${minutes}m`;
}

function formatTargetTime(iso: string): string {
  if (!iso) return '--:--';
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return '--:--';
  return parsed.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatShapValue(val: number): string {
  const prefix = val >= 0 ? '+' : '';
  if (Math.abs(val) >= 10) {
    return `${prefix}${val.toFixed(1)}`;
  }
  return `${prefix}${val.toFixed(3)}`;
}

export const QuantileLoadForecastPanel: React.FC<QuantileLoadForecastPanelProps> = ({
  buildingId,
  currentKw,
  contractDemandKw
}) => {
  const [forecast, setForecast] = useState<MultiHorizonLoadForecastResponse | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [hoveredHorizon, setHoveredHorizon] = useState<number | null>(null);
  const [refreshToken, setRefreshToken] = useState<number>(0);

  const prevBuildingRef = useRef<string>(buildingId);

  useEffect(() => {
    let isActive = true;

    if (prevBuildingRef.current !== buildingId) {
      prevBuildingRef.current = buildingId;
      setForecast(null);
      setIsInitialLoading(true);
      setHoveredHorizon(null);
    } else if (forecast !== null) {
      setIsRefreshing(true);
    }
    setError(null);

    const timer = setTimeout(() => {
      fetchMultiHorizonLoadForecast(buildingId, {
        currentKw,
        contractKw: contractDemandKw
      })
        .then((res) => {
          if (!isActive) return;
          setForecast(res);
          setError(null);
        })
        .catch((err: unknown) => {
          if (!isActive) return;
          const msg = err instanceof Error ? err.message : 'Unable to load multi-horizon quantile forecast';
          setError(msg);
        })
        .finally(() => {
          if (!isActive) return;
          setIsInitialLoading(false);
          setIsRefreshing(false);
        });
    }, 250);

    return () => {
      isActive = false;
      clearTimeout(timer);
    };
  }, [buildingId, currentKw, contractDemandKw, refreshToken]);

  const sortedHorizons = useMemo<QuantileHorizonForecast[]>(() => {
    if (!forecast?.horizons) return [];
    return [...forecast.horizons].sort((a, b) => a.horizonMinutes - b.horizonMinutes);
  }, [forecast]);

  const effectiveContractKw = useMemo(() => {
    if (typeof contractDemandKw === 'number' && contractDemandKw > 0) {
      return contractDemandKw;
    }
    if (forecast && typeof forecast.capacityKw === 'number' && forecast.capacityKw > 0) {
      return forecast.capacityKw;
    }
    return undefined;
  }, [contractDemandKw, forecast]);

  const peakP90Kw = useMemo(() => {
    if (sortedHorizons.length === 0) return 0;
    return Math.max(...sortedHorizons.map((h) => h.p90Kw));
  }, [sortedHorizons]);

  const peakHorizon = useMemo(() => {
    if (sortedHorizons.length === 0) return null;
    return sortedHorizons.reduce((best, item) => (item.p90Kw > best.p90Kw ? item : best), sortedHorizons[0]);
  }, [sortedHorizons]);

  const hasContractExceedance =
    effectiveContractKw !== undefined && sortedHorizons.some((h) => h.p90Kw > effectiveContractKw);

  const topFeatures = useMemo(() => {
    if (!forecast?.topFeatures) return [];
    return forecast.topFeatures.slice(0, 5);
  }, [forecast]);

  const maxAbsShap = useMemo(() => {
    if (topFeatures.length === 0) return 1;
    return Math.max(...topFeatures.map((f) => Math.abs(f.shapValue)), 1e-6);
  }, [topFeatures]);

  const chartGeometry = useMemo(() => {
    const width = 760;
    const height = 270;
    const padLeft = 64;
    const padRight = 28;
    const padTop = 26;
    const padBottom = 48;
    const plotW = width - padLeft - padRight;
    const plotH = height - padTop - padBottom;

    const values: number[] = [];
    for (const h of sortedHorizons) {
      values.push(h.p10Kw, h.p50Kw, h.p90Kw);
      if (Array.isArray(h.conformalInterval90) && h.conformalInterval90.length >= 2) {
        values.push(h.conformalInterval90[0], h.conformalInterval90[1]);
      }
    }
    if (typeof currentKw === 'number' && Number.isFinite(currentKw)) {
      values.push(currentKw);
    }
    if (typeof effectiveContractKw === 'number' && Number.isFinite(effectiveContractKw)) {
      values.push(effectiveContractKw);
    }

    const rawMin = values.length > 0 ? Math.min(...values) : 0;
    const rawMax = values.length > 0 ? Math.max(...values) : 1000;
    const span = Math.max(rawMax - rawMin, 100);
    const yMin = Math.max(0, Math.floor((rawMin - span * 0.12) / 50) * 50);
    const yMax = Math.ceil((rawMax + span * 0.14) / 50) * 50;
    const ySpan = Math.max(yMax - yMin, 1);

    const toY = (val: number) => padTop + plotH - ((val - yMin) / ySpan) * plotH;

    const hasNowAnchor = typeof currentKw === 'number' && Number.isFinite(currentKw);
    const totalSlots = sortedHorizons.length + (hasNowAnchor ? 1 : 0);
    const xForIndex = (slotIdx: number) => {
      if (totalSlots <= 1) return padLeft + plotW / 2;
      return padLeft + (slotIdx / (totalSlots - 1)) * plotW;
    };

    const nowX = hasNowAnchor ? xForIndex(0) : null;
    const nowY = hasNowAnchor && currentKw !== undefined ? toY(currentKw) : null;

    const points = sortedHorizons.map((h, idx) => {
      const slotIdx = hasNowAnchor ? idx + 1 : idx;
      const x = xForIndex(slotIdx);
      const confLow = Array.isArray(h.conformalInterval90) ? h.conformalInterval90[0] : h.p10Kw;
      const confHigh = Array.isArray(h.conformalInterval90) ? h.conformalInterval90[1] : h.p90Kw;
      return {
        horizon: h,
        x,
        yP10: toY(h.p10Kw),
        yP50: toY(h.p50Kw),
        yP90: toY(h.p90Kw),
        yConfLow: toY(confLow),
        yConfHigh: toY(confHigh)
      };
    });

    const yTicks = [0, 0.25, 0.5, 0.75, 1].map((t) => {
      const val = yMin + t * ySpan;
      return {
        val,
        y: toY(val)
      };
    });

    const conformalPolygon =
      points.length > 0
        ? [
            ...points.map((p) => `${p.x.toFixed(1)},${p.yConfHigh.toFixed(1)}`),
            ...[...points].reverse().map((p) => `${p.x.toFixed(1)},${p.yConfLow.toFixed(1)}`)
          ].join(' ')
        : '';

    const quantilePolygon =
      points.length > 0
        ? [
            ...points.map((p) => `${p.x.toFixed(1)},${p.yP90.toFixed(1)}`),
            ...[...points].reverse().map((p) => `${p.x.toFixed(1)},${p.yP10.toFixed(1)}`)
          ].join(' ')
        : '';

    const p50Polyline = points.map((p) => `${p.x.toFixed(1)},${p.yP50.toFixed(1)}`).join(' ');
    const contractY = effectiveContractKw !== undefined ? toY(effectiveContractKw) : null;

    return {
      width,
      height,
      padLeft,
      padRight,
      padTop,
      padBottom,
      plotW,
      plotH,
      nowX,
      nowY,
      points,
      yTicks,
      conformalPolygon,
      quantilePolygon,
      p50Polyline,
      contractY
    };
  }, [sortedHorizons, currentKw, effectiveContractKw]);

  const activeHoverPoint = useMemo(() => {
    if (hoveredHorizon === null) return null;
    return chartGeometry.points.find((p) => p.horizon.horizonMinutes === hoveredHorizon) || null;
  }, [hoveredHorizon, chartGeometry.points]);

  const qualityStatus = forecast?.provenance?.qualityStatus || 'VALID';
  const qualityColor =
    qualityStatus === 'VALID'
      ? 'var(--color-success)'
      : qualityStatus === 'STALE'
        ? 'var(--color-warning)'
        : 'var(--color-danger)';
  const qualitySubtle =
    qualityStatus === 'VALID'
      ? 'var(--color-success-subtle)'
      : qualityStatus === 'STALE'
        ? 'var(--color-warning-subtle)'
        : 'var(--color-danger-subtle)';

  const modelVersion = forecast?.provenance?.modelVersion || 'energy-quantile-xgb-v2';
  const sourceMode = forecast?.provenance?.sourceMode || 'PREDICTED';

  return (
    <div className="analytics-card" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Header */}
      <div
        className="analytics-card-header"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '10px',
          marginBottom: 0
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <TrendingUp size={18} color="var(--color-predicted)" />
          <div>
            <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>Multi-Horizon Quantile Load Forecast (15m - 24h)</span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
              Conformalized p10 / p50 / p90 demand envelope and TreeSHAP feature attribution
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span className="provenance-badge badge-predicted">{sourceMode}</span>
          <span
            className="status-pill"
            style={{
              backgroundColor: qualitySubtle,
              color: qualityColor,
              border: `1px solid ${qualityColor}`,
              fontSize: '11px',
              fontWeight: 700
            }}
          >
            {qualityStatus}
          </span>
          <code
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              padding: '2px 8px',
              borderRadius: '4px',
              backgroundColor: 'var(--color-surface-subtle)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-secondary)'
            }}
          >
            {modelVersion}
          </code>
          <button
            type="button"
            onClick={() => setRefreshToken((v) => v + 1)}
            disabled={isInitialLoading || isRefreshing}
            title="Refresh multi-horizon quantile forecast"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: '4px 8px',
              borderRadius: '4px',
              border: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-surface-subtle)',
              color: 'var(--color-text-secondary)',
              fontSize: '11px',
              cursor: 'pointer'
            }}
          >
            <RefreshCw size={12} className={isInitialLoading || isRefreshing ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Loading State */}
      {isInitialLoading && !forecast && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: '28px 16px',
            borderRadius: '6px',
            backgroundColor: 'var(--color-surface-subtle)',
            border: '1px solid var(--color-border)',
            color: 'var(--color-text-secondary)',
            fontSize: '12px'
          }}
        >
          <Activity size={16} className="animate-spin" />
          <span>Computing 15m, 60m, 4h, and 24h quantile forecasts...</span>
        </div>
      )}

      {/* Error State */}
      {error && !forecast && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            padding: '12px 14px',
            borderRadius: '6px',
            backgroundColor: 'var(--color-danger-subtle)',
            border: '1px solid var(--color-danger)',
            color: 'var(--color-danger)',
            fontSize: '12px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={15} />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={() => setRefreshToken((v) => v + 1)}
            style={{
              padding: '4px 10px',
              borderRadius: '4px',
              border: '1px solid var(--color-danger)',
              backgroundColor: 'var(--color-surface)',
              color: 'var(--color-danger)',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Main Content */}
      {forecast && (
        <>
          {/* Non-blocking warning if refresh failed while cached forecast is visible */}
          {error && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                borderRadius: '6px',
                backgroundColor: 'var(--color-warning-subtle)',
                border: '1px solid var(--color-warning)',
                color: 'var(--color-warning)',
                fontSize: '11px'
              }}
            >
              <AlertTriangle size={13} />
              <span>Latest refresh failed ({error}); showing previous forecast snapshot.</span>
            </div>
          )}

          {/* Summary Strip */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
              gap: '10px'
            }}
          >
            <div
              style={{
                padding: '10px 12px',
                borderRadius: '6px',
                backgroundColor: 'var(--color-surface-subtle)',
                border: '1px solid var(--color-border)'
              }}
            >
              <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Peak p90 Envelope
              </div>
              <div
                className="font-mono"
                style={{
                  fontSize: '18px',
                  fontWeight: 700,
                  marginTop: '2px',
                  color: hasContractExceedance ? 'var(--color-danger)' : 'var(--color-text)'
                }}
              >
                {peakP90Kw.toFixed(0)} <span style={{ fontSize: '11px', fontWeight: 500, color: 'var(--color-text-muted)' }}>kW</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                {peakHorizon ? `Horizon: ${formatHorizonFull(peakHorizon.horizonMinutes)}` : 'No horizon data'}
              </div>
            </div>

            <div
              style={{
                padding: '10px 12px',
                borderRadius: '6px',
                backgroundColor: 'var(--color-surface-subtle)',
                border: '1px solid var(--color-border)'
              }}
            >
              <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Contract Demand Limit
              </div>
              <div className="font-mono" style={{ fontSize: '18px', fontWeight: 700, marginTop: '2px', color: 'var(--color-text)' }}>
                {effectiveContractKw !== undefined ? effectiveContractKw.toLocaleString() : '--'}{' '}
                <span style={{ fontSize: '11px', fontWeight: 500, color: 'var(--color-text-muted)' }}>kW</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                Reference ceiling threshold
              </div>
            </div>

            <div
              style={{
                padding: '10px 12px',
                borderRadius: '6px',
                backgroundColor: hasContractExceedance ? 'var(--color-danger-subtle)' : 'var(--color-success-subtle)',
                border: `1px solid ${hasContractExceedance ? 'var(--color-danger)' : 'var(--color-success)'}`
              }}
            >
              <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                24h Contract Risk Status
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  fontSize: '13px',
                  fontWeight: 700,
                  marginTop: '4px',
                  color: hasContractExceedance ? 'var(--color-danger)' : 'var(--color-success)'
                }}
              >
                {hasContractExceedance ? <AlertTriangle size={15} /> : <CheckCircle2 size={15} />}
                <span>{hasContractExceedance ? 'p90 Exceeds Contract Limit' : 'Within Contract Envelope'}</span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '3px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={11} />
                <span>Generated: {formatTargetTime(forecast.forecastGeneratedAt)}</span>
              </div>
            </div>
          </div>

          {/* Multi-Horizon Fan Chart */}
          <div
            style={{
              padding: '12px',
              borderRadius: '8px',
              backgroundColor: 'var(--color-surface-subtle)',
              border: '1px solid var(--color-border)'
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '8px',
                marginBottom: '8px'
              }}
            >
              <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text)' }}>
                Multi-Horizon Conformal Fan Chart (kW)
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                  <span
                    style={{
                      width: '12px',
                      height: '10px',
                      borderRadius: '2px',
                      backgroundColor: 'var(--color-predicted-subtle)',
                      border: '1px solid var(--color-predicted)'
                    }}
                  />
                  90% Conformal Band
                </span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                  <span
                    style={{
                      width: '10px',
                      height: '2px',
                      backgroundColor: 'var(--color-info)'
                    }}
                  />
                  p10 - p90 Whiskers
                </span>
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                  <span
                    style={{
                      width: '12px',
                      height: '3px',
                      borderRadius: '2px',
                      backgroundColor: 'var(--color-predicted)'
                    }}
                  />
                  p50 Median
                </span>
                {effectiveContractKw !== undefined && (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                    <span
                      style={{
                        width: '14px',
                        height: 0,
                        borderTop: '2px dashed var(--color-danger)'
                      }}
                    />
                    Contract Limit
                  </span>
                )}
              </div>
            </div>

            {sortedHorizons.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', fontSize: '12px', color: 'var(--color-text-muted)' }}>
                No quantile horizons returned for this facility.
              </div>
            ) : (
              <div style={{ position: 'relative', width: '100%' }}>
                <svg
                  viewBox={`0 0 ${chartGeometry.width} ${chartGeometry.height}`}
                  style={{ width: '100%', height: 'auto', display: 'block' }}
                  role="img"
                  aria-label="Multi-horizon quantile load forecast fan chart"
                >
                  {/* Horizontal Gridlines & Y-Axis Ticks */}
                  {chartGeometry.yTicks.map((tick, idx) => (
                    <g key={idx}>
                      <line
                        x1={chartGeometry.padLeft}
                        x2={chartGeometry.width - chartGeometry.padRight}
                        y1={tick.y}
                        y2={tick.y}
                        stroke="var(--color-border)"
                        strokeDasharray="3 3"
                        strokeWidth={1}
                      />
                      <text
                        x={chartGeometry.padLeft - 8}
                        y={tick.y + 4}
                        textAnchor="end"
                        fill="var(--color-text-muted)"
                        fontSize="10"
                        fontFamily="var(--font-mono)"
                      >
                        {Math.round(tick.val).toLocaleString()}
                      </text>
                    </g>
                  ))}

                  {/* Y-Axis Unit Label */}
                  <text
                    x={14}
                    y={chartGeometry.padTop + chartGeometry.plotH / 2}
                    textAnchor="middle"
                    fill="var(--color-text-muted)"
                    fontSize="10"
                    fontWeight={600}
                    transform={`rotate(-90 14 ${chartGeometry.padTop + chartGeometry.plotH / 2})`}
                  >
                    Demand (kW)
                  </text>

                  {/* 90% Conformal Band Polygon */}
                  {chartGeometry.conformalPolygon && (
                    <polygon
                      points={chartGeometry.conformalPolygon}
                      fill="var(--color-predicted)"
                      fillOpacity={0.14}
                      stroke="var(--color-predicted)"
                      strokeOpacity={0.35}
                      strokeWidth={1}
                    />
                  )}

                  {/* p10-p90 Inner Quantile Band */}
                  {chartGeometry.quantilePolygon && (
                    <polygon
                      points={chartGeometry.quantilePolygon}
                      fill="var(--color-info)"
                      fillOpacity={0.16}
                    />
                  )}

                  {/* Contract Demand Limit Reference Line */}
                  {chartGeometry.contractY !== null && effectiveContractKw !== undefined && (
                    <g>
                      <line
                        x1={chartGeometry.padLeft}
                        x2={chartGeometry.width - chartGeometry.padRight}
                        y1={chartGeometry.contractY}
                        y2={chartGeometry.contractY}
                        stroke="var(--color-danger)"
                        strokeWidth={1.75}
                        strokeDasharray="6 4"
                      />
                      <rect
                        x={chartGeometry.width - chartGeometry.padRight - 154}
                        y={Math.max(4, chartGeometry.contractY - 19)}
                        width={150}
                        height={16}
                        rx={3}
                        fill="var(--color-surface)"
                        stroke="var(--color-danger)"
                        strokeWidth={0.75}
                      />
                      <text
                        x={chartGeometry.width - chartGeometry.padRight - 79}
                        y={Math.max(15, chartGeometry.contractY - 8)}
                        textAnchor="middle"
                        fill="var(--color-danger)"
                        fontSize="10"
                        fontWeight={700}
                        fontFamily="var(--font-mono)"
                      >
                        Limit: {effectiveContractKw.toLocaleString()} kW
                      </text>
                    </g>
                  )}

                  {/* Connector from Current Anchor to First Horizon p50 */}
                  {chartGeometry.nowX !== null && chartGeometry.nowY !== null && chartGeometry.points.length > 0 && (
                    <g>
                      <line
                        x1={chartGeometry.nowX}
                        y1={chartGeometry.nowY}
                        x2={chartGeometry.points[0].x}
                        y2={chartGeometry.points[0].yP50}
                        stroke="var(--color-text-muted)"
                        strokeWidth={1.5}
                        strokeDasharray="4 3"
                      />
                      <circle
                        cx={chartGeometry.nowX}
                        cy={chartGeometry.nowY}
                        r={4.5}
                        fill="var(--color-surface)"
                        stroke="var(--color-text-secondary)"
                        strokeWidth={2}
                      />
                      <text
                        x={chartGeometry.nowX}
                        y={chartGeometry.height - 22}
                        textAnchor="middle"
                        fill="var(--color-text-secondary)"
                        fontSize="11"
                        fontWeight={600}
                      >
                        Now
                      </text>
                      <text
                        x={chartGeometry.nowX}
                        y={chartGeometry.height - 8}
                        textAnchor="middle"
                        fill="var(--color-text-muted)"
                        fontSize="9.5"
                        fontFamily="var(--font-mono)"
                      >
                        {currentKw !== undefined ? `${currentKw.toFixed(0)} kW` : '--'}
                      </text>
                    </g>
                  )}

                  {/* p50 Median Trajectory Line */}
                  {chartGeometry.p50Polyline && (
                    <polyline
                      points={chartGeometry.p50Polyline}
                      fill="none"
                      stroke="var(--color-predicted)"
                      strokeWidth={2.5}
                      strokeLinejoin="round"
                      strokeLinecap="round"
                    />
                  )}

                  {/* Horizon Whiskers, Conformal Bounds & Nodes */}
                  {chartGeometry.points.map((pt) => {
                    const isHovered = hoveredHorizon === pt.horizon.horizonMinutes;
                    const exceedsLimit =
                      effectiveContractKw !== undefined && pt.horizon.p90Kw > effectiveContractKw;
                    const whiskerColor = exceedsLimit ? 'var(--color-warning)' : 'var(--color-predicted)';

                    return (
                      <g
                        key={pt.horizon.horizonMinutes}
                        onMouseEnter={() => setHoveredHorizon(pt.horizon.horizonMinutes)}
                        onMouseLeave={() => setHoveredHorizon(null)}
                        style={{ cursor: 'pointer' }}
                      >
                        {/* Subtle column guide on hover */}
                        {isHovered && (
                          <line
                            x1={pt.x}
                            x2={pt.x}
                            y1={chartGeometry.padTop}
                            y2={chartGeometry.padTop + chartGeometry.plotH}
                            stroke="var(--color-border-strong)"
                            strokeWidth={1}
                            strokeDasharray="2 2"
                          />
                        )}

                        {/* Conformal 90% thin range tick */}
                        <line
                          x1={pt.x}
                          x2={pt.x}
                          y1={pt.yConfHigh}
                          y2={pt.yConfLow}
                          stroke="var(--color-predicted)"
                          strokeOpacity={0.55}
                          strokeWidth={1.5}
                          strokeDasharray="2 2"
                        />

                        {/* p10 - p90 Quantile Whisker Stem */}
                        <line
                          x1={pt.x}
                          x2={pt.x}
                          y1={pt.yP90}
                          y2={pt.yP10}
                          stroke={whiskerColor}
                          strokeWidth={isHovered ? 4 : 3}
                          strokeLinecap="round"
                        />

                        {/* p90 Upper Cap */}
                        <line
                          x1={pt.x - 8}
                          x2={pt.x + 8}
                          y1={pt.yP90}
                          y2={pt.yP90}
                          stroke={whiskerColor}
                          strokeWidth={2}
                          strokeLinecap="round"
                        />

                        {/* p10 Lower Cap */}
                        <line
                          x1={pt.x - 8}
                          x2={pt.x + 8}
                          y1={pt.yP10}
                          y2={pt.yP10}
                          stroke={whiskerColor}
                          strokeWidth={2}
                          strokeLinecap="round"
                        />

                        {/* p50 Median Circle */}
                        <circle
                          cx={pt.x}
                          cy={pt.yP50}
                          r={isHovered ? 6.5 : 5}
                          fill="var(--color-predicted)"
                          stroke="var(--color-surface)"
                          strokeWidth={2}
                        />

                        {/* p50 Value Callout */}
                        <text
                          x={pt.x}
                          y={Math.max(chartGeometry.padTop + 10, pt.yP90 - 8)}
                          textAnchor="middle"
                          fill={exceedsLimit ? 'var(--color-danger)' : 'var(--color-text)'}
                          fontSize="10"
                          fontWeight={700}
                          fontFamily="var(--font-mono)"
                        >
                          {pt.horizon.p50Kw.toFixed(0)} kW
                        </text>

                        {/* X-Axis Horizon Labels */}
                        <text
                          x={pt.x}
                          y={chartGeometry.height - 22}
                          textAnchor="middle"
                          fill={isHovered ? 'var(--color-primary)' : 'var(--color-text)'}
                          fontSize="11"
                          fontWeight={700}
                        >
                          +{formatHorizonShort(pt.horizon.horizonMinutes)}
                        </text>
                        <text
                          x={pt.x}
                          y={chartGeometry.height - 8}
                          textAnchor="middle"
                          fill="var(--color-text-muted)"
                          fontSize="9.5"
                          fontFamily="var(--font-mono)"
                        >
                          {formatTargetTime(pt.horizon.targetTimestamp)}
                        </text>

                        {/* Wide transparent hover target */}
                        <rect
                          x={pt.x - 42}
                          y={chartGeometry.padTop}
                          width={84}
                          height={chartGeometry.plotH + 38}
                          fill="transparent"
                        />
                      </g>
                    );
                  })}
                </svg>

                {/* Active Hover Readout Strip */}
                {activeHoverPoint && (
                  <div
                    style={{
                      marginTop: '6px',
                      padding: '6px 10px',
                      borderRadius: '4px',
                      backgroundColor: 'var(--color-surface)',
                      border: '1px solid var(--color-border-strong)',
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '14px',
                      alignItems: 'center',
                      fontSize: '11px',
                      color: 'var(--color-text-secondary)'
                    }}
                  >
                    <strong style={{ color: 'var(--color-text)' }}>
                      Horizon +{formatHorizonFull(activeHoverPoint.horizon.horizonMinutes)}
                    </strong>
                    <span className="font-mono">
                      p10: {activeHoverPoint.horizon.p10Kw.toFixed(0)} kW
                    </span>
                    <span className="font-mono" style={{ color: 'var(--color-predicted)', fontWeight: 700 }}>
                      p50: {activeHoverPoint.horizon.p50Kw.toFixed(0)} kW
                    </span>
                    <span className="font-mono">
                      p90: {activeHoverPoint.horizon.p90Kw.toFixed(0)} kW
                    </span>
                    <span className="font-mono">
                      90% Conformal: [{activeHoverPoint.horizon.conformalInterval90[0].toFixed(0)} -{' '}
                      {activeHoverPoint.horizon.conformalInterval90[1].toFixed(0)} kW]
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Horizon Matrix Table & Top-5 TreeSHAP Attributions */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '16px',
              alignItems: 'start'
            }}
          >
            {/* Compact Horizon Matrix Table */}
            <div
              style={{
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-surface)',
                overflowX: 'auto'
              }}
            >
              <div
                style={{
                  padding: '10px 12px',
                  borderBottom: '1px solid var(--color-border)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text)' }}>
                  Quantile Horizon Matrix
                </span>
                <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  Calibrated 90% Intervals
                </span>
              </div>

              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Horizon</th>
                    <th>p10</th>
                    <th>p50 Median</th>
                    <th>p90 Peak Risk</th>
                    <th>90% Conformal Interval</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedHorizons.map((h) => {
                    const isHovered = hoveredHorizon === h.horizonMinutes;
                    const p90Risk = effectiveContractKw !== undefined && h.p90Kw > effectiveContractKw;
                    const confLo = Array.isArray(h.conformalInterval90) ? h.conformalInterval90[0] : h.p10Kw;
                    const confHi = Array.isArray(h.conformalInterval90) ? h.conformalInterval90[1] : h.p90Kw;
                    return (
                      <tr
                        key={h.horizonMinutes}
                        onMouseEnter={() => setHoveredHorizon(h.horizonMinutes)}
                        onMouseLeave={() => setHoveredHorizon(null)}
                        style={{
                          backgroundColor: isHovered ? 'var(--color-surface-selected)' : undefined,
                          cursor: 'pointer'
                        }}
                      >
                        <td>
                          <div style={{ fontWeight: 700, color: 'var(--color-text)' }}>
                            {formatHorizonFull(h.horizonMinutes)}
                          </div>
                          <div className="font-mono" style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>
                            {formatTargetTime(h.targetTimestamp)}
                          </div>
                        </td>
                        <td className="mono-cell">{h.p10Kw.toFixed(0)} kW</td>
                        <td className="mono-cell" style={{ color: 'var(--color-predicted)', fontWeight: 700 }}>
                          {h.p50Kw.toFixed(0)} kW
                        </td>
                        <td
                          className="mono-cell"
                          style={{
                            color: p90Risk ? 'var(--color-danger)' : 'var(--color-text)',
                            fontWeight: p90Risk ? 700 : 500
                          }}
                        >
                          {h.p90Kw.toFixed(0)} kW
                        </td>
                        <td className="mono-cell">
                          [{confLo.toFixed(0)} - {confHi.toFixed(0)}] kW
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Top-5 TreeSHAP Feature Attributions */}
            <div
              style={{
                borderRadius: '8px',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-surface)',
                padding: '12px'
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '10px',
                  paddingBottom: '8px',
                  borderBottom: '1px solid var(--color-border)'
                }}
              >
                <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--color-text)' }}>
                  Top-5 TreeSHAP Feature Attributions
                </span>
                <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  Signed Driver Impact
                </span>
              </div>

              {topFeatures.length === 0 ? (
                <div style={{ padding: '18px 8px', textAlign: 'center', fontSize: '12px', color: 'var(--color-text-muted)' }}>
                  Feature attributions unavailable for this inference step.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {topFeatures.map((feat, idx) => {
                    const impactUpper = feat.impact ? feat.impact.toUpperCase() : '';
                    const isIncrease = impactUpper
                      ? impactUpper.includes('INCREASE')
                      : feat.shapValue >= 0;
                    const directionLabel = isIncrease ? 'INCREASES' : 'DECREASES';
                    const barColor = isIncrease ? 'var(--color-warning)' : 'var(--color-success)';
                    const badgeBg = isIncrease ? 'var(--color-warning-subtle)' : 'var(--color-success-subtle)';
                    const widthPct = Math.min(100, Math.max(6, (Math.abs(feat.shapValue) / maxAbsShap) * 100));

                    return (
                      <div key={`${feat.feature}-${idx}`} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <div
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            gap: '8px',
                            fontSize: '12px'
                          }}
                        >
                          <span style={{ fontWeight: 600, color: 'var(--color-text)' }}>
                            {feat.displayName || feat.feature}
                          </span>
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                            <span
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '3px',
                                padding: '1px 6px',
                                borderRadius: '4px',
                                fontSize: '10px',
                                fontWeight: 700,
                                backgroundColor: badgeBg,
                                color: barColor
                              }}
                            >
                              {isIncrease ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
                              {directionLabel}
                            </span>
                            <span
                              className="font-mono"
                              style={{ fontSize: '11px', fontWeight: 700, color: barColor, minWidth: '58px', textAlign: 'right' }}
                            >
                              {formatShapValue(feat.shapValue)}
                            </span>
                          </div>
                        </div>

                        <div
                          style={{
                            width: '100%',
                            height: '6px',
                            borderRadius: '9999px',
                            backgroundColor: 'var(--color-surface-subtle)',
                            border: '1px solid var(--color-border)',
                            overflow: 'hidden'
                          }}
                        >
                          <div
                            style={{
                              width: `${widthPct}%`,
                              height: '100%',
                              borderRadius: '9999px',
                              backgroundColor: barColor,
                              transition: 'width 200ms ease'
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Non-Actuation Advisory Notice */}
          <div className="analytics-notice-box">
            <ShieldAlert size={14} color="var(--color-warning)" style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>
              <strong>Advisory Governance Notice:</strong>{' '}
              {forecast.advisoryNotice ||
                'Multi-horizon quantile demand forecasts are advisory predictions only. Human engineering authorization is required outside the platform before any switchgear or load-management action.'}
            </span>
          </div>
        </>
      )}
    </div>
  );
};
