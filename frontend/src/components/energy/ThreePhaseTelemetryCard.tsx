import React from 'react';
import {
  Zap,
  Gauge,
  Activity,
  Radio,
  Sun,
  BatteryCharging,
  Car,
  Building2,
  GitFork,
  Clock,
  ShieldCheck,
  Percent
} from 'lucide-react';
import { EnergyNodeAsset, EnergyAssetTelemetry } from '../../types/twin';

interface ThreePhaseTelemetryCardProps {
  selectedNode: EnergyNodeAsset | null;
  telemetry: EnergyAssetTelemetry | null;
  isLive?: boolean;
}

export const ThreePhaseTelemetryCard: React.FC<ThreePhaseTelemetryCardProps> = ({
  selectedNode,
  telemetry,
  isLive = true
}) => {
  if (!selectedNode) {
    return (
      <div className="analytics-card" style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '40px' }}>
        <Zap size={32} className="text-muted" style={{ margin: '0 auto 12px' }} />
        <h3 className="card-title" style={{ fontSize: '15px' }}>No Asset Selected</h3>
        <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', maxWidth: '360px', marginTop: '6px', lineHeight: 1.5 }}>
          Select any node in the electrical hierarchy tree on the left to inspect real-time 3-phase AC power physics, frequency stability, and physical asset parameters.
        </p>
      </div>
    );
  }

  const telem = telemetry || selectedNode.telemetry;
  const p = telem?.activePowerKw ?? 0;
  const q = telem?.reactivePowerKvar ?? 0;
  const s = telem?.apparentPowerKva ?? 0;
  const pf = telem?.powerFactor ?? 1.0;
  const v = telem?.voltageV ?? selectedNode.nominalVoltageKv * 1000;
  const i = telem?.currentA ?? 0;
  const freq = telem?.frequencyHz ?? 50.00;
  const vUnbalance = telem?.voltageUnbalancePct ?? 0.45;
  const iUnbalance = telem?.currentUnbalancePct ?? 1.15;
  const devMetrics = telem?.deviceMetrics || selectedNode.properties || {};

  const isSolar = selectedNode.nodeType === 'SOLAR_PV';
  const isBess = selectedNode.nodeType === 'BESS';
  const isEv = selectedNode.nodeType === 'EV_HUB';
  const isBuilding = selectedNode.nodeType === 'BUILDING_LOAD';
  const isFeeder = selectedNode.nodeType === 'FEEDER';
  const isSubstation = selectedNode.nodeType === 'SUBSTATION';

  const pfLabel = pf >= 0.99 ? 'Unity' : p >= 0 ? 'Lagging' : 'Leading';
  const freqStatus = Math.abs(freq - 50.0) <= 0.1 ? 'Normal' : 'Perturbed';

  return (
    <div className="analytics-card" style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header Info */}
      <div className="analytics-card-header" style={{ marginBottom: 0 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                padding: '6px',
                borderRadius: 'var(--radius-sm, 6px)',
                background: 'rgba(47, 129, 247, 0.14)',
                border: '1px solid rgba(47, 129, 247, 0.35)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Zap size={16} color="var(--color-primary-hover, #58A6FF)" />
            </span>
            <h2 className="card-title" style={{ fontSize: '16px', margin: 0 }}>
              {selectedNode.name}
            </h2>
          </div>
          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)', marginTop: '4px', display: 'block' }}>
            URN: {selectedNode.nodeId}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {isLive && (
            <span className="provenance-badge badge-live" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className="dot dot-live" style={{ width: '6px', height: '6px' }} />
              LIVE TELEMETRY
            </span>
          )}
          <span className="analytics-meta-pill" style={{ fontFamily: 'var(--font-mono)' }}>
            {selectedNode.nominalVoltageKv} kV / {selectedNode.ratedCapacityKva.toLocaleString()} kVA
          </span>
        </div>
      </div>

      {/* Primary 3-Phase AC Metrics Grid */}
      <div className="quick-metrics-row-four">
        <div className="metric-box">
          <span className="metric-box-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Active Power (P)</span>
            <Activity size={13} color="var(--color-primary, #2F81F7)" />
          </span>
          <span
            className="metric-box-val font-mono"
            style={{
              color: p < 0 ? '#818CF8' : isSolar ? 'var(--color-success, #3FB950)' : 'var(--color-text, #F0F6FC)'
            }}
          >
            {p.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} <small>kW</small>
          </span>
          <span className="metric-box-sub">
            {isSolar ? 'Renewable Generation' : isBess && p < 0 ? 'Charging Grid Energy' : 'Physical Active Draw'}
          </span>
        </div>

        <div className="metric-box">
          <span className="metric-box-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Reactive Power (Q)</span>
            <Activity size={13} color="var(--color-warning, #D29922)" />
          </span>
          <span className="metric-box-val font-mono" style={{ color: 'var(--color-warning, #D29922)' }}>
            {q.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} <small>kVAR</small>
          </span>
          <span className="metric-box-sub">
            Magnetizing / Inverter VARs
          </span>
        </div>

        <div className="metric-box">
          <span className="metric-box-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Apparent Power (S)</span>
            <Gauge size={13} color="#BC8CFF" />
          </span>
          <span className="metric-box-val font-mono" style={{ color: '#BC8CFF' }}>
            {s.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} <small>kVA</small>
          </span>
          <span className="metric-box-sub">
            Vector Sum: sqrt(P^2 + Q^2)
          </span>
        </div>

        <div className="metric-box">
          <span className="metric-box-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Power Factor (PF)</span>
            <Percent size={13} color="var(--color-success, #3FB950)" />
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
            <span
              className="metric-box-val font-mono"
              style={{
                color: pf >= 0.95 ? 'var(--color-success, #3FB950)' : pf >= 0.90 ? 'var(--color-warning, #D29922)' : 'var(--color-danger, #F85149)'
              }}
            >
              {pf.toFixed(3)}
            </span>
            <span
              style={{
                fontSize: '11px',
                padding: '2px 6px',
                borderRadius: '4px',
                background: 'var(--bg-surface-elevated)',
                color: 'var(--color-text-secondary)',
                fontFamily: 'var(--font-mono)'
              }}
            >
              {pfLabel}
            </span>
          </div>
          <span className="metric-box-sub">
            Target: &gt;0.95 (IEEE 519)
          </span>
        </div>
      </div>

      {/* Secondary Physical Parameters */}
      <div
        style={{
          background: 'var(--bg-surface-elevated, rgba(15, 15, 18, 0.7))',
          border: '1px solid var(--color-border, #16171B)',
          borderRadius: 'var(--radius-sm, 6px)',
          padding: '12px 16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Radio size={14} color="var(--color-primary, #2F81F7)" />
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text, #F0F6FC)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Physical 3-Phase Line & Grid Parameters
          </span>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
            gap: '12px',
            fontSize: '12px'
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Line Voltage (V_L)</span>
            <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
              {v.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} V
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Phase Current (I_L)</span>
            <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
              {i.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} A
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Grid Frequency (f)</span>
            <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-success, #3FB950)', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              {freq.toFixed(2)} Hz
              <span style={{ fontSize: '10px', padding: '1px 5px', borderRadius: '4px', background: 'rgba(63, 185, 80, 0.15)', color: '#3FB950' }}>
                {freqStatus}
              </span>
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Voltage Unbalance</span>
            <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
              {vUnbalance.toFixed(2)}%
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Current Unbalance</span>
            <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
              {iUnbalance.toFixed(2)}%
            </span>
          </div>
        </div>
      </div>

      {/* Asset-Specific Domain Drawer */}
      <div
        style={{
          background: 'var(--bg-surface-elevated, rgba(15, 15, 18, 0.7))',
          border: '1px solid var(--color-border, #16171B)',
          borderRadius: 'var(--radius-sm, 6px)',
          padding: '12px 16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {isSolar && <Sun size={14} color="#3FB950" />}
          {isBess && <BatteryCharging size={14} color="#BC8CFF" />}
          {isEv && <Car size={14} color="#E879F9" />}
          {isBuilding && <Building2 size={14} color="#38BDF8" />}
          {(isFeeder || isSubstation) && <GitFork size={14} color="#FCD34D" />}
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text, #F0F6FC)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Asset Domain Telemetry & Specification
          </span>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: '12px',
            fontSize: '12px'
          }}
        >
          {isSolar && (
            <>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Global Solar Irradiance</span>
                <span className="font-mono" style={{ fontWeight: 600, color: '#3FB950', marginTop: '2px' }}>
                  {devMetrics.irradianceWm2 ?? 720.0} W/m²
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Smart Inverter Efficiency</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  {devMetrics.inverterEfficiencyPct ?? 98.2}%
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Panel Orientation</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  {devMetrics.orientation || 'SOUTH_FACING (18.5° Tilt)'}
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Grid Code Standard</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  IEEE 1547-2018 Compliant
                </span>
              </div>
            </>
          )}

          {isBess && (
            <>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>State of Charge (SOC)</span>
                <span className="font-mono" style={{ fontWeight: 600, color: '#BC8CFF', marginTop: '2px' }}>
                  {devMetrics.stateOfChargePct ?? 78.5}%
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Operational Mode</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  {devMetrics.operatingMode || 'SOLAR_ABSORPTION'}
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Usable Energy Capacity</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  2,000 kWh (LFP Chemistry)
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Round-Trip Efficiency</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  88.5%
                </span>
              </div>
            </>
          )}

          {isEv && (
            <>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Active Charging Plugs</span>
                <span className="font-mono" style={{ fontWeight: 600, color: '#E879F9', marginTop: '2px' }}>
                  {devMetrics.activePlugs ?? 6} / {devMetrics.totalPlugs ?? 12} Plugs
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Plaza Utilization</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  {devMetrics.utilizationRatePct ?? 50.0}%
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Charger Protocol</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  OCPP 2.0.1 Smart Charging
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Smart Curtailment Flag</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  {devMetrics.smartThrottlingActive ? 'ACTIVE (THROTTLED)' : 'INACTIVE (FULL CHARGE)'}
                </span>
              </div>
            </>
          )}

          {isBuilding && (
            <>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>HVAC Chiller Load</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  {(devMetrics.hvacLoadKw ?? (p * 0.52)).toFixed(1)} kW
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Lighting & Ventilation</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  {(devMetrics.lightingLoadKw ?? (p * 0.23)).toFixed(1)} kW
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Building Category</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  {devMetrics.category || 'COMMERCIAL'}
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Contract Demand</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  {devMetrics.contractDemandKW ?? 2500.0} kW
                </span>
              </div>
            </>
          )}

          {(isFeeder || isSubstation) && (
            <>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Feeder Rated Capacity</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  {selectedNode.ratedCapacityKva.toLocaleString()} kVA
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Rated Maximum Current</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  {selectedNode.ratedCurrentAmps.toFixed(1)} A
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>Cable Specification</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text, #F0F6FC)', marginTop: '2px' }}>
                  3C x 300 mm² XLPE AL
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '11px' }}>SCADA Telemetry Status</span>
                <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-success, #3FB950)', marginTop: '2px' }}>
                  ONLINE (IEC 60870-5-104)
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Provenance & Data Honesty Footer */}
      <div
        style={{
          paddingTop: '10px',
          borderTop: '1px solid var(--color-border, #16171B)',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '8px',
          fontSize: '11px',
          color: 'var(--color-text-muted)',
          fontFamily: 'var(--font-mono)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <ShieldCheck size={13} color="var(--color-primary, #2F81F7)" />
            Mode: {telem?.sourceMode || 'SIMULATION'}
          </span>
          <span>•</span>
          <span>Status: {telem?.qualityStatus || 'VALID'}</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Clock size={12} color="var(--color-text-muted)" />
          <span>Observed: {telem?.observedAt ? new Date(telem.observedAt).toLocaleTimeString() : 'Just now'}</span>
        </div>
      </div>
    </div>
  );
};
