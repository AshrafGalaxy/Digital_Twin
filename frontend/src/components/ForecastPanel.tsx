import React, { useEffect, useState, useRef } from 'react';
import {
  TrendingUp,
  Zap,
  Activity,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  Clock,
  ShieldAlert
} from 'lucide-react';
import { TrafficForecast, EnergyForecast } from '../types/twin';
import { fetchTrafficForecast, fetchEnergyForecast } from '../services/api';

interface ForecastPanelProps {
  entityType: 'RoadSegment' | 'Building';
  entityId: string;
  currentValue?: number;
  contractDemandKw?: number;
}

export const ForecastPanel: React.FC<ForecastPanelProps> = ({
  entityType,
  entityId,
  currentValue,
  contractDemandKw
}) => {
  const [trafficForecast, setTrafficForecast] = useState<TrafficForecast | null>(null);
  const [energyForecast, setEnergyForecast] = useState<EnergyForecast | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState<boolean>(true);
  const [isPulsing, setIsPulsing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const prevEntityIdRef = useRef<string>(entityId);
  const prevPredictedRef = useRef<number | null>(null);

  useEffect(() => {
    let isSubscribed = true;

    // Reset initial loading only if the selected entity changed
    if (prevEntityIdRef.current !== entityId) {
      prevEntityIdRef.current = entityId;
      prevPredictedRef.current = null;
      setIsInitialLoading(true);
      setTrafficForecast(null);
      setEnergyForecast(null);
    }
    setError(null);

    const debounceTimer = setTimeout(() => {
      if (entityType === 'RoadSegment') {
        fetchTrafficForecast(entityId, currentValue)
          .then((data) => {
            if (!isSubscribed) return;
            setTrafficForecast(data);
            if (prevPredictedRef.current !== null && prevPredictedRef.current !== data.predictedValue) {
              setIsPulsing(true);
              setTimeout(() => setIsPulsing(false), 700);
            }
            prevPredictedRef.current = data.predictedValue;
          })
          .catch((err) => {
            if (isSubscribed) setError(err.message || 'Failed loading traffic forecast');
          })
          .finally(() => {
            if (isSubscribed) setIsInitialLoading(false);
          });
      } else if (entityType === 'Building') {
        fetchEnergyForecast(entityId, currentValue)
          .then((data) => {
            if (!isSubscribed) return;
            setEnergyForecast(data);
            if (prevPredictedRef.current !== null && prevPredictedRef.current !== data.predictedValue) {
              setIsPulsing(true);
              setTimeout(() => setIsPulsing(false), 700);
            }
            prevPredictedRef.current = data.predictedValue;
          })
          .catch((err) => {
            if (isSubscribed) setError(err.message || 'Failed loading energy forecast');
          })
          .finally(() => {
            if (isSubscribed) setIsInitialLoading(false);
          });
      }
    }, 250);

    return () => {
      isSubscribed = false;
      clearTimeout(debounceTimer);
    };
  }, [entityType, entityId, currentValue]);

  if (isInitialLoading && !trafficForecast && !energyForecast) {
    return (
      <div className="forecast-panel-loading">
        <Activity size={18} className="animate-spin text-muted" />
        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
          Computing 15m/60m predictive inference...
        </span>
      </div>
    );
  }

  if (error && !trafficForecast && !energyForecast) {
    return (
      <div className="forecast-error-box">
        <AlertTriangle size={14} />
        <span>{error}</span>
      </div>
    );
  }

  // Road Segment Traffic Speed Forecast View
  if (entityType === 'RoadSegment' && trafficForecast) {
    const delta = currentValue !== undefined
      ? trafficForecast.predictedValue - currentValue
      : 0;

    return (
      <div className="forecast-container">
        {/* Header */}
        <div className="forecast-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <TrendingUp size={16} color="#2DD4BF" />
            <span className="forecast-title">15-Min Speed Forecast</span>
          </div>
          <span className="provenance-badge badge-predicted">PREDICTED</span>
        </div>

        {/* Prediction Hero Card */}
        <div className="forecast-hero-card">
          <div className="forecast-metric-row">
            <div>
              <div className="forecast-label">Projected Speed (t + 15m)</div>
              <div className={`forecast-main-val ${isPulsing ? 'metric-pulse' : ''}`}>
                {trafficForecast.predictedValue.toFixed(1)}
                <span className="forecast-unit"> km/h</span>
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div className="forecast-label">80% Interval</div>
              <div className="forecast-interval-val">
                [{trafficForecast.confidenceLower.toFixed(1)} – {trafficForecast.confidenceUpper.toFixed(1)}]
                <span className="forecast-unit"> km/h</span>
              </div>
            </div>
          </div>

          <div className="forecast-sub-meta">
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <Clock size={12} /> Target: {new Date(trafficForecast.targetTimestamp).toLocaleTimeString()}
            </span>
            {currentValue !== undefined && (
              <span className={`forecast-delta ${delta >= 0 ? 'text-positive' : 'text-negative'}`}>
                {delta >= 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1)} km/h vs. current
              </span>
            )}
          </div>
        </div>

        {/* Conformal Prediction Uncertainty Calibration */}
        {trafficForecast.conformalIntervals && (
          <div className="forecast-conformal-box">
            <div className="conformal-header">
              <span className="conformal-badge">CONFORMAL CALIBRATION</span>
              <span className="conformal-target">90% Coverage Guarantee</span>
            </div>
            <div className="conformal-range">
              [{trafficForecast.conformalIntervals.interval90.lower.toFixed(1)} – {trafficForecast.conformalIntervals.interval90.upper.toFixed(1)} km/h]
              <span className="conformal-margin"> (±{trafficForecast.conformalIntervals.interval90.margin} km/h, { (trafficForecast.conformalIntervals.interval90.empiricalTestCoverage * 100).toFixed(1) }% test coverage)</span>
            </div>
          </div>
        )}

        {/* TreeSHAP Local Feature Explainability */}
        {trafficForecast.explanation?.topContributors && trafficForecast.explanation.topContributors.length > 0 && (
          <div className="forecast-explanation-box">
            <div className="explanation-header">
              <span className="explanation-title">Local Feature Attributions (TreeSHAP)</span>
              <span className="explanation-subtitle font-mono">Top contributors</span>
            </div>
            <div className="explanation-chips">
              {trafficForecast.explanation.topContributors.map((c, i) => (
                <div key={i} className={`explanation-chip ${c.contribution >= 0 ? 'contrib-pos' : 'contrib-neg'}`}>
                  <div className="chip-left">
                    <span className="chip-indicator" />
                    <span className="chip-name">{c.displayName}</span>
                  </div>
                  <span className="chip-val font-mono">{c.contribution >= 0 ? `+${c.contribution.toFixed(1)}` : c.contribution.toFixed(1)} km/h</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Baseline vs Model Comparison */}
        {trafficForecast.baselineComparison && (
          <div className="forecast-baseline-box">
            <div className="baseline-header">
              <CheckCircle size={12} color="#10B981" />
              <span>Model vs. Baseline Evaluation</span>
            </div>
            <div className="baseline-grid">
              <div className="baseline-item">
                <span className="baseline-label">Persistence MAE</span>
                <span className="baseline-val">{trafficForecast.baselineComparison.persistenceMae} km/h</span>
              </div>
              <div className="baseline-item">
                <span className="baseline-label">XGBoost MAE</span>
                <span className="baseline-val">{trafficForecast.baselineComparison.modelTestMae} km/h</span>
              </div>
              <div className="baseline-item">
                <span className="baseline-label">Accuracy Gain</span>
                <span className="baseline-gain">+{trafficForecast.baselineComparison.accuracyGainPct}%</span>
              </div>
            </div>
          </div>
        )}

        {/* Model Version & Locality Caveat */}
        <div className="forecast-footer-info">
          <div className="model-tag">
            <span>Model: </span>
            <code>{trafficForecast.modelVersion}</code>
          </div>
          <div className="locality-caveat">
            <HelpCircle size={12} style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{trafficForecast.localityNotice}</span>
          </div>
        </div>
      </div>
    );
  }

  // Commercial Building Energy Demand Forecast View
  if (entityType === 'Building' && energyForecast) {
    return (
      <div className="forecast-container">
        {/* Header */}
        <div className="forecast-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <Zap size={16} color="#FBBF24" />
            <span className="forecast-title">60-Min Demand Forecast</span>
          </div>
          <span className="provenance-badge badge-predicted">PREDICTED</span>
        </div>

        {/* Peak Demand Advisory Alert if applicable */}
        {energyForecast.isPeakDemandAlert && (
          <div className="peak-alert-banner">
            <ShieldAlert size={16} />
            <div>
              <strong>Peak Load Advisory:</strong> Projected demand exceeds {energyForecast.peakThresholdKw} kW threshold. Recommend precooling HVAC staging.
            </div>
          </div>
        )}

        {/* Prediction Hero Card */}
        <div className="forecast-hero-card">
          <div className="forecast-metric-row">
            <div>
              <div className="forecast-label">Projected Demand (t + 60m)</div>
              <div className={`forecast-main-val ${isPulsing ? 'metric-pulse' : ''}`}>
                {energyForecast.predictedValue.toFixed(0)}
                <span className="forecast-unit"> kW</span>
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div className="forecast-label">80% Confidence Interval</div>
              <div className="forecast-interval-val">
                [{energyForecast.confidenceLower.toFixed(0)} – {energyForecast.confidenceUpper.toFixed(0)}]
                <span className="forecast-unit"> kW</span>
              </div>
            </div>
          </div>

          <div className="forecast-sub-meta">
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              <Clock size={12} /> Target: {new Date(energyForecast.targetTimestamp).toLocaleTimeString()}
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: '#10B981' }}>
              Contracted: {((contractDemandKw ?? energyForecast.contractDemandKw ?? 6800) as number).toLocaleString()} kW
            </span>
          </div>
        </div>

        {/* Conformal Prediction Uncertainty Calibration */}
        {energyForecast.conformalIntervals && (
          <div className="forecast-conformal-box">
            <div className="conformal-header">
              <span className="conformal-badge">CONFORMAL CALIBRATION</span>
              <span className="conformal-target">90% Coverage Guarantee</span>
            </div>
            <div className="conformal-range">
              [{energyForecast.conformalIntervals.interval90.lower.toFixed(0)} – {energyForecast.conformalIntervals.interval90.upper.toFixed(0)} kW]
              <span className="conformal-margin"> (±{energyForecast.conformalIntervals.interval90.margin.toFixed(0)} kW, { (energyForecast.conformalIntervals.interval90.empiricalTestCoverage * 100).toFixed(1) }% test coverage)</span>
            </div>
          </div>
        )}

        {/* TreeSHAP Local Feature Explainability */}
        {energyForecast.explanation?.topContributors && energyForecast.explanation.topContributors.length > 0 && (
          <div className="forecast-explanation-box">
            <div className="explanation-header">
              <span className="explanation-title">Local Feature Attributions (TreeSHAP)</span>
              <span className="explanation-subtitle font-mono">Top contributors</span>
            </div>
            <div className="explanation-chips">
              {energyForecast.explanation.topContributors.map((c, i) => (
                <div key={i} className={`explanation-chip ${c.contribution >= 0 ? 'contrib-pos' : 'contrib-neg'}`}>
                  <div className="chip-left">
                    <span className="chip-indicator" />
                    <span className="chip-name">{c.displayName}</span>
                  </div>
                  <span className="chip-val font-mono">{c.contribution >= 0 ? `+${c.contribution.toFixed(0)}` : c.contribution.toFixed(0)} kW</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Baseline Comparison */}
        {energyForecast.baselineComparison && (
          <div className="forecast-baseline-box">
            <div className="baseline-header">
              <CheckCircle size={12} color="#10B981" />
              <span>Model vs. Baseline Evaluation</span>
            </div>
            <div className="baseline-grid">
              <div className="baseline-item">
                <span className="baseline-label">Persistence MAE</span>
                <span className="baseline-val">{energyForecast.baselineComparison.persistenceMae} kW</span>
              </div>
              <div className="baseline-item">
                <span className="baseline-label">XGBoost MAE</span>
                <span className="baseline-val">{energyForecast.baselineComparison.modelTestMae} kW</span>
              </div>
              <div className="baseline-item">
                <span className="baseline-label">Accuracy Gain</span>
                <span className="baseline-gain">+{energyForecast.baselineComparison.accuracyGainPct}%</span>
              </div>
            </div>
          </div>
        )}

        {/* Source Limitation Footer */}
        <div className="forecast-footer-info">
          <div className="model-tag">
            <span>Model: </span>
            <code>{energyForecast.modelVersion}</code>
          </div>
          <div className="locality-caveat">
            <HelpCircle size={12} style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>{energyForecast.sourceLimitation}</span>
          </div>
        </div>
      </div>
    );
  }

  return null;
};
