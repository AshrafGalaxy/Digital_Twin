import React, { useEffect, useState, useMemo } from 'react';
import {
  Sun,
  Thermometer,
  Wind,
  Cloud,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  RefreshCw,
  Activity
} from 'lucide-react';
import {
  SolarPVArrayInfo,
  SolarPVForecastResponse,
  SolarPerformanceEvaluationResponse,
  fetchSolarArrays,
  fetchSolarPVForecast,
  evaluateSolarPerformance
} from '../../services/api';

interface SolarPVForecastPanelProps {
  activeFacilityId?: string;
}

export const SolarPVForecastPanel: React.FC<SolarPVForecastPanelProps> = ({
  activeFacilityId
}) => {
  const [arrays, setArrays] = useState<SolarPVArrayInfo[]>([]);
  const [selectedArrayId, setSelectedArrayId] = useState<string>('AST-PV-PHOENIX-01');
  const [cloudCoverPct, setCloudCoverPct] = useState<number>(10);
  const [windSpeedMs, setWindSpeedMs] = useState<number>(2.5);
  const [forecast, setForecast] = useState<SolarPVForecastResponse | null>(null);
  const [perfEval, setPerfEval] = useState<SolarPerformanceEvaluationResponse | null>(null);
  const [measuredSampleRatio, setMeasuredSampleRatio] = useState<number>(0.92);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  useEffect(() => {
    let mounted = true;
    fetchSolarArrays()
      .then((list) => {
        if (!mounted || list.length === 0) return;
        setArrays(list);
        if (activeFacilityId) {
          const matched = list.find((a) => a.facilityId === activeFacilityId);
          if (matched) {
            setSelectedArrayId(matched.arrayId);
            return;
          }
        }
        setSelectedArrayId(list[0].arrayId);
      })
      .catch(() => {
        // Fallback array ID remains usable when initial catalog query fails
      });
    return () => {
      mounted = false;
    };
  }, [activeFacilityId]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    const timer = setTimeout(() => {
      fetchSolarPVForecast(selectedArrayId, {
        horizonHours: 24,
        windSpeedMs,
        cloudCoverPct
      })
        .then((res) => {
          if (!active) return;
          setForecast(res);
          const daytimeSample = res.curve24h.find((pt) => pt.ghiWPerSqm >= 250) || res.curve24h[0];
          if (daytimeSample && daytimeSample.ghiWPerSqm >= 25) {
            const simMeasured = Number((daytimeSample.expectedPowerKw * measuredSampleRatio).toFixed(2));
            evaluateSolarPerformance(selectedArrayId, {
              measuredKw: simMeasured,
              ghiWPerSqm: daytimeSample.ghiWPerSqm,
              ambientTempC: daytimeSample.ambientTemperatureC,
              windSpeedMs
            })
              .then((evalRes) => {
                if (active) setPerfEval(evalRes);
              })
              .catch(() => {
                if (active) setPerfEval(null);
              });
          } else {
            setPerfEval(null);
          }
        })
        .catch((err) => {
          if (active) setError(err instanceof Error ? err.message : 'Failed loading solar forecast');
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    }, 180);

    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [selectedArrayId, cloudCoverPct, windSpeedMs, measuredSampleRatio]);

  const svgGeometry = useMemo(() => {
    if (!forecast || forecast.curve24h.length === 0) return null;
    const width = 680;
    const height = 220;
    const padL = 52;
    const padR = 48;
    const padT = 20;
    const padB = 34;
    const plotW = width - padL - padR;
    const plotH = height - padT - padB;

    const pts = forecast.curve24h;
    const maxKw = Math.max(forecast.ratedPeakPowerKw * 1.05, 100);
    const maxGhi = 1100;

    const toX = (i: number) => padL + (i / Math.max(1, pts.length - 1)) * plotW;
    const toYKw = (kw: number) => padT + plotH - (kw / maxKw) * plotH;
    const toYGhi = (ghi: number) => padT + plotH - (ghi / maxGhi) * plotH;

    const powerPath = pts
      .map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${toX(idx).toFixed(1)} ${toYKw(p.expectedPowerKw).toFixed(1)}`)
      .join(' ');
    const areaPath =
      `${powerPath} L ${toX(pts.length - 1).toFixed(1)} ${(padT + plotH).toFixed(1)} ` +
      `L ${toX(0).toFixed(1)} ${(padT + plotH).toFixed(1)} Z`;

    const ghiPath = pts
      .map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${toX(idx).toFixed(1)} ${toYGhi(p.ghiWPerSqm).toFixed(1)}`)
      .join(' ');

    return { width, height, padL, padR, padT, padB, plotW, plotH, maxKw, maxGhi, pts, toX, toYKw, toYGhi, powerPath, areaPath, ghiPath };
  }, [forecast]);

  const statusColor = (status?: string) => {
    if (status === 'NOMINAL') return 'var(--color-success, #3FB950)';
    if (status === 'SOILING_OR_DEGRADATION_WARNING') return 'var(--color-warning, #D29922)';
    if (status === 'INVERTER_OR_STRING_FAULT') return 'var(--color-danger, #F85149)';
    return 'var(--text-muted, #8B949E)';
  };

  const hoveredPoint =
    svgGeometry && hoverIdx !== null && svgGeometry.pts[hoverIdx] ? svgGeometry.pts[hoverIdx] : null;

  return (
    <div className="analytics-card" style={{ marginTop: '16px' }}>
      <div className="analytics-card-header" style={{ flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sun size={18} color="#F59E0B" />
          <span className="card-title">Solar PV Physical Generation & Sandia Thermal Derating (15m to 24h)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span className="provenance-badge badge-predicted">PREDICTED</span>
          <span className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted, #8B949E)' }}>
            King/Sandia Cell Model
          </span>
        </div>
      </div>

      {/* Controls */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '12px',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 12px',
          marginBottom: '14px',
          borderRadius: '8px',
          background: 'var(--color-surface-subtle, rgba(148, 163, 184, 0.06))',
          border: '1px solid var(--color-border, rgba(148, 163, 184, 0.2))'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <label className="text-muted" style={{ fontSize: '12px' }} htmlFor="solar-array-select">
            PV Array:
          </label>
          <select
            id="solar-array-select"
            value={selectedArrayId}
            onChange={(e) => setSelectedArrayId(e.target.value)}
            style={{
              background: 'var(--color-surface, #0D1117)',
              color: 'var(--color-text, #F0F6FC)',
              border: '1px solid var(--color-border, #30363D)',
              borderRadius: '6px',
              padding: '4px 8px',
              fontSize: '12px'
            }}
          >
            {(arrays.length > 0
              ? arrays
              : [
                  { arrayId: 'AST-PV-PHOENIX-01', ratedPeakPowerKw: 1200 },
                  { arrayId: 'AST-PV-SOLITAIRE-01', ratedPeakPowerKw: 800 },
                  { arrayId: 'AST-PV-HYATT-01', ratedPeakPowerKw: 450 }
                ]
            ).map((a) => (
              <option key={a.arrayId} value={a.arrayId}>
                {a.arrayId} ({a.ratedPeakPowerKw} kWp)
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap', fontSize: '12px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Cloud size={13} />
            <span>Cloud: {cloudCoverPct}%</span>
            <input
              type="range"
              min={0}
              max={90}
              step={5}
              value={cloudCoverPct}
              onChange={(e) => setCloudCoverPct(Number(e.target.value))}
            />
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Wind size={13} />
            <span>Wind: {windSpeedMs.toFixed(1)} m/s</span>
            <input
              type="range"
              min={0.5}
              max={8.0}
              step={0.5}
              value={windSpeedMs}
              onChange={(e) => setWindSpeedMs(Number(e.target.value))}
            />
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Activity size={13} />
            <span>PR Stress: {Math.round(measuredSampleRatio * 100)}%</span>
            <input
              type="range"
              min={0.45}
              max={1.0}
              step={0.05}
              value={measuredSampleRatio}
              onChange={(e) => setMeasuredSampleRatio(Number(e.target.value))}
            />
          </label>
        </div>
      </div>

      {loading && !forecast && (
        <div style={{ padding: '24px', textAlign: 'center', fontSize: '13px', color: 'var(--text-muted)' }}>
          <RefreshCw size={16} className="animate-spin" style={{ display: 'inline', marginRight: '8px' }} />
          Computing physical solar irradiance and Sandia thermal derating curve...
        </div>
      )}

      {error && (
        <div className="analytics-notice-box" style={{ borderColor: 'rgba(248, 81, 73, 0.4)' }}>
          <AlertTriangle size={14} color="#F85149" />
          <span>{error}</span>
        </div>
      )}

      {forecast && svgGeometry && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
          {/* Left: 24h Curve SVG */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', fontSize: '12px' }}>
              <span style={{ fontWeight: 600 }}>24-Hour Yield (kW) & GHI Irradiance (W/m2)</span>
              <span className="font-mono text-muted">
                Peak: {forecast.peakExpectedPowerKw.toLocaleString()} kW | Daily Yield: {forecast.dailyExpectedEnergyKwh.toLocaleString()} kWh
              </span>
            </div>

            <svg
              viewBox={`0 0 ${svgGeometry.width} ${svgGeometry.height}`}
              style={{ width: '100%', height: 'auto', display: 'block', overflow: 'visible' }}
              onMouseLeave={() => setHoverIdx(null)}
            >
              {/* Horizontal Gridlines */}
              {[0, 0.25, 0.5, 0.75, 1.0].map((frac) => {
                const y = svgGeometry.padT + svgGeometry.plotH * (1 - frac);
                const kwTick = Math.round(svgGeometry.maxKw * frac);
                return (
                  <g key={frac}>
                    <line
                      x1={svgGeometry.padL}
                      y1={y}
                      x2={svgGeometry.width - svgGeometry.padR}
                      y2={y}
                      stroke="var(--color-border, rgba(148, 163, 184, 0.2))"
                      strokeDasharray={frac > 0 ? '3 3' : undefined}
                    />
                    <text
                      x={svgGeometry.padL - 6}
                      y={y + 3}
                      textAnchor="end"
                      fontSize="10"
                      fill="var(--text-muted, #8B949E)"
                    >
                      {kwTick}
                    </text>
                  </g>
                );
              })}

              {/* Yield Fill & Curve */}
              <path d={svgGeometry.areaPath} fill="rgba(245, 158, 11, 0.16)" />
              <path d={svgGeometry.ghiPath} fill="none" stroke="#38BDF8" strokeWidth="1.5" strokeDasharray="4 3" />
              <path d={svgGeometry.powerPath} fill="none" stroke="#F59E0B" strokeWidth="2.4" />

              {/* Hover Scrub Targets */}
              {svgGeometry.pts.map((pt, i) => (
                <rect
                  key={pt.horizonMinutes}
                  x={svgGeometry.toX(i) - svgGeometry.plotW / (svgGeometry.pts.length * 2)}
                  y={svgGeometry.padT}
                  width={Math.max(4, svgGeometry.plotW / svgGeometry.pts.length)}
                  height={svgGeometry.plotH}
                  fill="transparent"
                  onMouseEnter={() => setHoverIdx(i)}
                />
              ))}

              {hoveredPoint && hoverIdx !== null && (
                <g>
                  <line
                    x1={svgGeometry.toX(hoverIdx)}
                    y1={svgGeometry.padT}
                    x2={svgGeometry.toX(hoverIdx)}
                    y2={svgGeometry.padT + svgGeometry.plotH}
                    stroke="#F59E0B"
                    strokeDasharray="2 2"
                  />
                  <circle
                    cx={svgGeometry.toX(hoverIdx)}
                    cy={svgGeometry.toYKw(hoveredPoint.expectedPowerKw)}
                    r="4"
                    fill="#F59E0B"
                  />
                </g>
              )}

              {/* X-Axis Hour Markers */}
              {[0, 23, 47, 71, svgGeometry.pts.length - 1].map((idx) => {
                const pt = svgGeometry.pts[idx];
                if (!pt) return null;
                return (
                  <text
                    key={idx}
                    x={svgGeometry.toX(idx)}
                    y={svgGeometry.height - 8}
                    textAnchor="middle"
                    fontSize="10"
                    fill="var(--text-muted, #8B949E)"
                  >
                    {`${String(Math.floor(pt.localHour)).padStart(2, '0')}:00`}
                  </text>
                );
              })}
            </svg>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginTop: '4px' }} className="text-muted">
              <span>Orange: PV Yield (kW) | Dashed Blue: GHI (W/m2)</span>
              {hoveredPoint ? (
                <span className="font-mono">
                  {String(Math.floor(hoveredPoint.localHour)).padStart(2, '0')}h: {hoveredPoint.expectedPowerKw} kW | GHI {hoveredPoint.ghiWPerSqm} W/m2 | Tcell {hoveredPoint.cellTemperatureC} C (-{hoveredPoint.thermalDeratingLossPct}%)
                </span>
              ) : (
                <span>Hover curve for T_cell and derating telemetry</span>
              )}
            </div>
          </div>

          {/* Right: Thermal Derating & Performance Ratio (PR) Anomaly Detector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div
              style={{
                padding: '12px',
                borderRadius: '8px',
                background: 'var(--color-surface-subtle, rgba(148, 163, 184, 0.06))',
                border: '1px solid var(--color-border, rgba(148, 163, 184, 0.2))'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontWeight: 600, fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Thermometer size={14} color="#F59E0B" />
                  <span>Performance Ratio (PR) Diagnostics</span>
                </span>
                {perfEval && (
                  <span
                    className="status-pill"
                    style={{
                      color: statusColor(perfEval.diagnosticStatus),
                      borderColor: statusColor(perfEval.diagnosticStatus),
                      fontSize: '10px'
                    }}
                  >
                    {perfEval.diagnosticStatus}
                  </span>
                )}
              </div>

              {perfEval ? (
                <div style={{ fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span className="text-muted">Measured vs Physical Expected:</span>
                    <span className="font-mono">
                      {perfEval.measuredPowerKw} / {perfEval.expectedPhysicalPowerKw} kW
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span className="text-muted">Cell Temp / Thermal Loss:</span>
                    <span className="font-mono">
                      {perfEval.cellTemperatureC} C (-{perfEval.thermalDeratingLossPct}%)
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span className="text-muted">Performance Ratio (PR):</span>
                    <span className="font-mono" style={{ fontWeight: 700, color: statusColor(perfEval.diagnosticStatus) }}>
                      {perfEval.performanceRatio !== null ? `${(perfEval.performanceRatio * 100).toFixed(1)}%` : 'N/A'}
                    </span>
                  </div>
                  <div style={{ marginTop: '4px', fontSize: '11px', display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
                    {perfEval.diagnosticStatus === 'NOMINAL' ? (
                      <CheckCircle2 size={14} color="#3FB950" style={{ flexShrink: 0, marginTop: '2px' }} />
                    ) : (
                      <AlertTriangle size={14} color={statusColor(perfEval.diagnosticStatus)} style={{ flexShrink: 0, marginTop: '2px' }} />
                    )}
                    <span>{perfEval.advisoryAction}</span>
                  </div>
                </div>
              ) : (
                <div style={{ fontSize: '12px' }} className="text-muted">
                  Irradiance sample below daytime PR evaluation threshold.
                </div>
              )}
            </div>

            <div className="analytics-notice-box">
              <ShieldAlert size={14} color="#F59E0B" />
              <span style={{ fontSize: '11px' }}>
                <strong>Governance Notice:</strong> {forecast.advisoryNotice}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
