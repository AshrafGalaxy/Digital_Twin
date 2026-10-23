import React, { useState, useEffect } from 'react';
import {
  Flame,
  RefreshCw,
  Zap
} from 'lucide-react';
import {
  fetchPowerBalance,
  PowerBalanceResponse
} from '../../services/api';

interface FeederThermalLoadingCardProps {
  substationId?: string;
  refreshTrigger?: number;
  onOpenDemandResponse?: () => void;
}

export const FeederThermalLoadingCard: React.FC<FeederThermalLoadingCardProps> = ({
  substationId,
  refreshTrigger,
  onOpenDemandResponse
}) => {
  const [data, setData] = useState<PowerBalanceResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchPowerBalance(substationId);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch feeder thermal loading metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [substationId, refreshTrigger]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'CRITICAL_OVERLOAD_RISK':
        return (
          <span
            className="status-pill"
            style={{
              backgroundColor: 'var(--color-danger-subtle)',
              color: 'var(--color-danger)',
              border: '1px solid var(--color-danger)',
              fontWeight: 700
            }}
          >
            CRITICAL OVERLOAD RISK
          </span>
        );
      case 'WARNING':
        return (
          <span
            className="status-pill"
            style={{
              backgroundColor: 'var(--color-warning-subtle)',
              color: 'var(--color-warning)',
              border: '1px solid var(--color-warning)',
              fontWeight: 700
            }}
          >
            ELEVATED THERMAL LOAD
          </span>
        );
      default:
        return (
          <span
            className="status-pill"
            style={{
              backgroundColor: 'var(--color-success-subtle)',
              color: 'var(--color-success)',
              border: '1px solid var(--color-success)'
            }}
          >
            NOMINAL AMPACITY
          </span>
        );
    }
  };

  const getProgressBarColor = (ratio: number) => {
    if (ratio >= 0.90) return 'var(--color-danger)';
    if (ratio >= 0.75) return 'var(--color-warning)';
    return 'var(--color-success)';
  };

  return (
    <div className="analytics-card" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      {/* Header */}
      <div className="analytics-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="settings-icon-badge" style={{ backgroundColor: 'rgba(210, 153, 34, 0.15)' }}>
            <Flame size={16} color="#D29922" />
          </div>
          <div>
            <h3 className="card-title" style={{ margin: 0, fontSize: '13px', fontWeight: 700 }}>
              Feeder Thermal Loading & Ampacity Margins
            </h3>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
              Branch Line Ampacity (I / I_rated) &middot; Technical Losses (3 * I^2 * R) &middot; Kirchhoff Conservation
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {data && getStatusBadge(data.thermalAlertStatus)}
          {onOpenDemandResponse && (
            <button
              type="button"
              onClick={onOpenDemandResponse}
              style={{
                background: 'rgba(235, 169, 0, 0.12)',
                border: '1px solid rgba(235, 169, 0, 0.4)',
                borderRadius: '4px',
                padding: '4px 10px',
                color: 'var(--color-warning, #EBA900)',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                fontSize: '11px',
                fontWeight: 600
              }}
              title="Review Demand-Response Advisory Dossier and Dispatch Work Order"
            >
              <Zap size={12} />
              <span>Demand-Response Dossier</span>
            </button>
          )}
          <button
            type="button"
            onClick={loadData}
            disabled={loading}
            style={{
              background: 'transparent',
              border: '1px solid var(--color-border)',
              borderRadius: '4px',
              padding: '4px 8px',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '11px'
            }}
            title="Refresh power balance calculations"
          >
            <RefreshCw size={12} className={loading ? 'spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error ? (
        <div style={{ padding: '12px', borderRadius: '4px', backgroundColor: 'var(--color-danger-subtle)', color: 'var(--color-danger)', fontSize: '12px' }}>
          {error}
        </div>
      ) : !data ? (
        <div style={{ padding: '20px', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '12px' }}>
          Computing live Kirchhoff power conservation and branch thermal margins...
        </div>
      ) : (
        <>
          {/* Kirchhoff Power Balance Summary Strip */}
          <div
            style={{
              padding: '12px 14px',
              borderRadius: '6px',
              backgroundColor: 'var(--color-surface-subtle)',
              border: '1px solid var(--color-border)',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Kirchhoff Active Power Conservation Balance
              </span>
              <span
                style={{
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  padding: '2px 8px',
                  borderRadius: '10px',
                  backgroundColor: data.powerBalanceResidualKw <= 0.05 ? 'var(--color-success-subtle)' : 'var(--color-warning-subtle)',
                  color: data.powerBalanceResidualKw <= 0.05 ? 'var(--color-success)' : 'var(--color-warning)',
                  fontWeight: 600
                }}
              >
                Residual Closure: {data.powerBalanceResidualKw.toFixed(2)} kW ({data.powerBalanceResidualKw <= 0.05 ? 'Balanced' : 'Compensating'})
              </span>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                gap: '8px',
                fontFamily: 'var(--font-mono)'
              }}
            >
              <div className="metric-box" style={{ padding: '8px 10px' }}>
                <span className="metric-label" style={{ fontSize: '10px' }}>PCC Grid Import</span>
                <span className="metric-value" style={{ fontSize: '14px', color: 'var(--color-primary)' }}>
                  {data.pccGridImportKw.toLocaleString()} <span style={{ fontSize: '10px' }}>kW</span>
                </span>
              </div>

              <div className="metric-box" style={{ padding: '8px 10px' }}>
                <span className="metric-label" style={{ fontSize: '10px' }}>Solar Generation</span>
                <span className="metric-value" style={{ fontSize: '14px', color: '#3FB950' }}>
                  +{data.solarGenerationKw.toLocaleString()} <span style={{ fontSize: '10px' }}>kW</span>
                </span>
              </div>

              <div className="metric-box" style={{ padding: '8px 10px' }}>
                <span className="metric-label" style={{ fontSize: '10px' }}>BESS Net Power</span>
                <span
                  className="metric-value"
                  style={{
                    fontSize: '14px',
                    color: data.bessNetPowerKw > 0 ? '#3FB950' : data.bessNetPowerKw < 0 ? 'var(--color-primary)' : 'var(--color-text-muted)'
                  }}
                >
                  {data.bessNetPowerKw > 0 ? `+${data.bessNetPowerKw}` : data.bessNetPowerKw} <span style={{ fontSize: '10px' }}>kW</span>
                </span>
              </div>

              <div className="metric-box" style={{ padding: '8px 10px' }}>
                <span className="metric-label" style={{ fontSize: '10px' }}>Facility Total Load</span>
                <span className="metric-value" style={{ fontSize: '14px', color: 'var(--color-text)' }}>
                  -{data.facilityTotalLoadKw.toLocaleString()} <span style={{ fontSize: '10px' }}>kW</span>
                </span>
              </div>

              <div className="metric-box" style={{ padding: '8px 10px' }}>
                <span className="metric-label" style={{ fontSize: '10px' }}>Technical Losses</span>
                <span className="metric-value" style={{ fontSize: '14px', color: 'var(--color-warning)' }}>
                  -{data.technicalLossesKw.toFixed(1)} <span style={{ fontSize: '10px' }}>kW</span>
                </span>
              </div>
            </div>
          </div>

          {/* Feeder Thermal Loading Breakdown Table/Cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Distribution Branches &middot; Continuous Ampacity Status
            </span>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {data.feeders.map((feeder) => {
                const color = getProgressBarColor(feeder.thermalLoadingRatio);
                return (
                  <div
                    key={feeder.feederId}
                    style={{
                      padding: '12px 14px',
                      borderRadius: '6px',
                      backgroundColor: 'var(--color-surface)',
                      border: feeder.status === 'CRITICAL_OVERLOAD_RISK'
                        ? '1px solid var(--color-danger)'
                        : feeder.status === 'WARNING'
                        ? '1px solid var(--color-warning)'
                        : '1px solid var(--color-border)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px'
                    }}
                  >
                    {/* Feeder Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '6px' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '12px', color: 'var(--color-primary)' }}>
                            {feeder.feederId}
                          </span>
                          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text)' }}>
                            {feeder.name}
                          </span>
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                          Rated Voltage: {feeder.voltageKv} kV &bull; Cable: {feeder.cableLengthMeters}m (R: {feeder.conductorResistanceOhm} &Omega;)
                        </div>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {getStatusBadge(feeder.status)}
                        <span
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: '13px',
                            fontWeight: 700,
                            color: color
                          }}
                        >
                          {feeder.thermalLoadingPct.toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    {/* Progress Bar Track */}
                    <div className="progress-bar-bg" style={{ height: '8px', width: '100%' }}>
                      <div
                        className="progress-bar-fill"
                        style={{
                          width: `${Math.min(100, feeder.thermalLoadingPct)}%`,
                          backgroundColor: color
                        }}
                      />
                    </div>

                    {/* Numerical Metric Highlights */}
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                        gap: '6px',
                        fontSize: '11px',
                        fontFamily: 'var(--font-mono)',
                        color: 'var(--color-text-secondary)',
                        backgroundColor: 'var(--color-surface-subtle)',
                        padding: '6px 10px',
                        borderRadius: '4px'
                      }}
                    >
                      <div>
                        <span style={{ color: 'var(--color-text-muted)' }}>Current: </span>
                        <strong>{feeder.currentAmps.toFixed(1)} A</strong> / {feeder.ratedCurrentAmps.toFixed(0)} A
                      </div>
                      <div>
                        <span style={{ color: 'var(--color-text-muted)' }}>Headroom: </span>
                        <strong style={{ color: feeder.availableHeadroomKw > 100 ? '#3FB950' : 'var(--color-warning)' }}>
                          +{feeder.availableHeadroomKw.toFixed(1)} kW
                        </strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--color-text-muted)' }}>Active / Apparent: </span>
                        <strong>{feeder.activePowerKw.toFixed(0)} kW</strong> / {feeder.apparentPowerKva.toFixed(0)} kVA
                      </div>
                      <div>
                        <span style={{ color: 'var(--color-text-muted)' }}>Branch Loss: </span>
                        <strong>{feeder.branchLossKw.toFixed(1)} kW</strong> (PF {feeder.powerFactor.toFixed(2)})
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
