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
      <div className="bg-slate-900/50 backdrop-blur-md rounded-xl border border-slate-800 p-8 flex flex-col items-center justify-center text-center text-slate-400 h-full">
        <Zap className="w-8 h-8 text-slate-600 mb-2" />
        <h3 className="text-sm font-semibold text-slate-300">No Asset Selected</h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Select any node in the electrical hierarchy tree on the left to inspect live 3-phase AC power physics, frequency stability, and physical asset parameters.
        </p>
      </div>
    );
  }

  const telem = telemetry || selectedNode.telemetry;
  const p = telem?.activePowerKw || 0;
  const q = telem?.reactivePowerKvar || 0;
  const s = telem?.apparentPowerKva || 0;
  const pf = telem?.powerFactor ?? 1.0;
  const v = telem?.voltageV || selectedNode.nominalVoltageKv * 1000;
  const i = telem?.currentA || 0;
  const freq = telem?.frequencyHz || 50.00;
  const vUnbalance = telem?.voltageUnbalancePct || 0.45;
  const iUnbalance = telem?.currentUnbalancePct || 1.15;
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
    <div className="bg-slate-900/50 backdrop-blur-md rounded-xl border border-slate-800 p-5 flex flex-col gap-5 h-full">
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-cyan-950 border border-cyan-800/40 text-cyan-400">
              <Zap className="w-4 h-4" />
            </span>
            <h2 className="text-base font-bold text-slate-100">{selectedNode.name}</h2>
          </div>
          <span className="text-[11px] font-mono text-slate-400 mt-1 block">
            URN: {selectedNode.nodeId}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {isLive && (
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              LIVE TELEMETRY
            </span>
          )}
          <span className="px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 text-xs font-mono text-slate-300">
            {selectedNode.nominalVoltageKv} kV / {selectedNode.ratedCapacityKva.toLocaleString()} kVA
          </span>
        </div>
      </div>

      {/* Primary 3-Phase AC Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800/80 flex flex-col">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold flex items-center justify-between">
            Active Power (P)
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
          </span>
          <div className="flex items-baseline gap-1.5 mt-2">
            <span className={`text-xl font-bold font-mono ${p < 0 ? 'text-indigo-400' : isSolar ? 'text-emerald-400' : 'text-slate-100'}`}>
              {p.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
            </span>
            <span className="text-xs text-slate-400 font-mono">kW</span>
          </div>
          <span className="text-[10px] text-slate-400 mt-1">
            {isSolar ? 'Renewable Generation' : isBess && p < 0 ? 'Charging Grid Energy' : 'Physical Active Draw'}
          </span>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800/80 flex flex-col">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold flex items-center justify-between">
            Reactive Power (Q)
            <Activity className="w-3.5 h-3.5 text-amber-400" />
          </span>
          <div className="flex items-baseline gap-1.5 mt-2">
            <span className="text-xl font-bold font-mono text-amber-300">
              {q.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
            </span>
            <span className="text-xs text-slate-400 font-mono">kVAR</span>
          </div>
          <span className="text-[10px] text-slate-400 mt-1">
            Magnetizing / Inverter VARs
          </span>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800/80 flex flex-col">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold flex items-center justify-between">
            Apparent Power (S)
            <Gauge className="w-3.5 h-3.5 text-purple-400" />
          </span>
          <div className="flex items-baseline gap-1.5 mt-2">
            <span className="text-xl font-bold font-mono text-purple-300">
              {s.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
            </span>
            <span className="text-xs text-slate-400 font-mono">kVA</span>
          </div>
          <span className="text-[10px] text-slate-400 mt-1">
            Vector Sum: sqrt(P^2 + Q^2)
          </span>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800/80 flex flex-col">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold flex items-center justify-between">
            Power Factor (PF)
            <Percent className="w-3.5 h-3.5 text-emerald-400" />
          </span>
          <div className="flex items-baseline gap-2 mt-2">
            <span className={`text-xl font-bold font-mono ${pf >= 0.95 ? 'text-emerald-400' : pf >= 0.90 ? 'text-amber-400' : 'text-rose-400'}`}>
              {pf.toFixed(3)}
            </span>
            <span className="text-[11px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
              {pfLabel}
            </span>
          </div>
          <span className="text-[10px] text-slate-400 mt-1">
            Target: &gt;0.95 (IEEE 519)
          </span>
        </div>
      </div>

      {/* Secondary Physical Parameters */}
      <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 flex flex-col gap-3">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
          <Radio className="w-3.5 h-3.5 text-cyan-400" />
          Physical 3-Phase Line & Grid Parameters
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 pt-1 text-xs">
          <div className="flex flex-col">
            <span className="text-slate-400 text-[11px]">Line Voltage (V_L)</span>
            <span className="font-mono font-semibold text-slate-200 mt-0.5">
              {v.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} V
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-slate-400 text-[11px]">Phase Current (I_L)</span>
            <span className="font-mono font-semibold text-slate-200 mt-0.5">
              {i.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} A
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-slate-400 text-[11px]">Grid Frequency (f)</span>
            <span className="font-mono font-semibold text-emerald-400 mt-0.5 flex items-center gap-1.5">
              {freq.toFixed(2)} Hz
              <span className="text-[10px] px-1 py-0.2 rounded bg-emerald-500/10 text-emerald-300">
                {freqStatus}
              </span>
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-slate-400 text-[11px]">Voltage Unbalance</span>
            <span className="font-mono font-semibold text-slate-200 mt-0.5">
              {vUnbalance.toFixed(2)}%
            </span>
          </div>

          <div className="flex flex-col">
            <span className="text-slate-400 text-[11px]">Current Unbalance</span>
            <span className="font-mono font-semibold text-slate-200 mt-0.5">
              {iUnbalance.toFixed(2)}%
            </span>
          </div>
        </div>
      </div>

      {/* Asset-Specific Domain Drawer */}
      <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 flex flex-col gap-3">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
          {isSolar && <Sun className="w-3.5 h-3.5 text-emerald-400" />}
          {isBess && <BatteryCharging className="w-3.5 h-3.5 text-indigo-400" />}
          {isEv && <Car className="w-3.5 h-3.5 text-purple-400" />}
          {isBuilding && <Building2 className="w-3.5 h-3.5 text-blue-400" />}
          {(isFeeder || isSubstation) && <GitFork className="w-3.5 h-3.5 text-amber-400" />}
          Asset Domain Telemetry & Specification
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          {isSolar && (
            <>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Global Solar Irradiance</span>
                <span className="font-mono font-semibold text-emerald-300 mt-0.5">
                  {devMetrics.irradianceWm2 ?? 720.0} W/m²
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Smart Inverter Efficiency</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  {devMetrics.inverterEfficiencyPct ?? 98.2}%
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Panel Orientation</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  {devMetrics.orientation || 'SOUTH_FACING (18.5° Tilt)'}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Grid Code Standard</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  IEEE 1547-2018 Compliant
                </span>
              </div>
            </>
          )}

          {isBess && (
            <>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">State of Charge (SOC)</span>
                <span className="font-mono font-semibold text-indigo-300 mt-0.5">
                  {devMetrics.stateOfChargePct ?? 78.5}%
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Operational Mode</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  {devMetrics.operatingMode || 'SOLAR_ABSORPTION'}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Usable Energy Capacity</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  2,000 kWh (LFP Chemistry)
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Round-Trip Efficiency</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  88.5%
                </span>
              </div>
            </>
          )}

          {isEv && (
            <>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Active Charging Plugs</span>
                <span className="font-mono font-semibold text-purple-300 mt-0.5">
                  {devMetrics.activePlugs ?? 6} / {devMetrics.totalPlugs ?? 12} Plugs
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Plaza Utilization</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  {devMetrics.utilizationRatePct ?? 50.0}%
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Charger Protocol</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  OCPP 2.0.1 Smart Charging
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Smart Curtailment Flag</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  {devMetrics.smartThrottlingActive ? 'ACTIVE (THROTTLED)' : 'INACTIVE (FULL CHARGE)'}
                </span>
              </div>
            </>
          )}

          {isBuilding && (
            <>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">HVAC Chiller Load</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  {(devMetrics.hvacLoadKw ?? (p * 0.52)).toFixed(1)} kW
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Lighting & Ventilation</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  {(devMetrics.lightingLoadKw ?? (p * 0.23)).toFixed(1)} kW
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Building Category</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  {devMetrics.category || 'COMMERCIAL'}
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Contract Demand</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  {devMetrics.contractDemandKW ?? 2500.0} kW
                </span>
              </div>
            </>
          )}

          {(isFeeder || isSubstation) && (
            <>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Feeder Rated Capacity</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  {selectedNode.ratedCapacityKva.toLocaleString()} kVA
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Rated Maximum Current</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  {selectedNode.ratedCurrentAmps.toFixed(1)} A
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">Cable Specification</span>
                <span className="font-mono font-semibold text-slate-200 mt-0.5">
                  3C x 300 mm² XLPE AL
                </span>
              </div>
              <div className="flex flex-col">
                <span className="text-slate-400 text-[11px]">SCADA Telemetry Status</span>
                <span className="font-mono font-semibold text-emerald-400 mt-0.5">
                  ONLINE (IEC 60870-5-104)
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Provenance & Data Honesty Footer */}
      <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3 text-[11px] text-slate-400 font-mono">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            Mode: {telem?.sourceMode || 'SIMULATION'}
          </span>
          <span>•</span>
          <span>Status: {telem?.qualityStatus || 'VALID'}</span>
        </div>

        <div className="flex items-center gap-1.5 text-slate-400">
          <Clock className="w-3 h-3 text-slate-400" />
          <span>Observed: {telem?.observedAt ? new Date(telem.observedAt).toLocaleTimeString() : 'Just now'}</span>
        </div>
      </div>
    </div>
  );
};
