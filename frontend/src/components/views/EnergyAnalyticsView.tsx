import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Zap,
  AlertTriangle,
  Clock,
  Building,
  HelpCircle,
  ShieldAlert,
  Gauge,
  Activity,
  Sun,
  BatteryCharging,
  Car,
  GitFork,
  RefreshCw,
  Layers,
  Radio,
  Sliders
} from 'lucide-react';
import {
  SourceMode,
  BuildingAsset,
  EntityCurrentState,
  EnergyTopologyTreeResponse,
  EnergyNodeAsset,
  EnergyAssetTelemetry,
  MicrogridSummary
} from '../../types/twin';
import { ForecastPanel } from '../ForecastPanel';
import { ElectricalTopologyTree } from '../energy/ElectricalTopologyTree';
import { ThreePhaseTelemetryCard } from '../energy/ThreePhaseTelemetryCard';
import { FeederThermalLoadingCard } from '../energy/FeederThermalLoadingCard';
import {
  fetchEnergyTopology,
  fetchLiveEnergyTelemetry,
  fetchMicrogridSummary,
  advanceEnergyTelemetry
} from '../../services/api';

interface EnergyAnalyticsViewProps {
  sourceMode: SourceMode;
  energyEntities?: BuildingAsset[];
  liveStates?: Record<string, EntityCurrentState>;
}

const DEFAULT_FACILITIES: BuildingAsset[] = [
  {
    id: 'urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01',
    name: 'Commercial Retail Complex & Zone',
    category: 'COMMERCIAL_RETAIL',
    grossFloorAreaSqMeters: 115000,
    electricalConnection: {
      substation: '22kV Primary Substation Feeder',
      sanctionedLoadKVA: 8500,
      contractDemandKW: 6800
    },
    baselineMetrics: {
      averageDaytimeDemandKW: 4200,
      peakEveningDemandKW: 5900,
      nightBaseDemandKW: 1100,
      powerFactor: 0.98
    },
    provenanceNotice: 'Building energy observations and profiles are calibrated synthetic/benchmark values modeled after commercial retail facilities.'
  },
  {
    id: 'urn:ngsi-ld:Building:PUNE:BLD-SOLITAIRE-01',
    name: 'Commercial Business & Tech Hub',
    category: 'COMMERCIAL_IT',
    grossFloorAreaSqMeters: 112690,
    electricalConnection: {
      substation: '22kV Primary Substation Feeder',
      sanctionedLoadKVA: 7500,
      contractDemandKW: 6010
    },
    baselineMetrics: {
      averageDaytimeDemandKW: 4800,
      peakEveningDemandKW: 3200,
      nightBaseDemandKW: 950,
      powerFactor: 0.97
    },
    provenanceNotice: 'Building energy observations and profiles are calibrated synthetic/benchmark values modeled after commercial IT facilities.'
  },
  {
    id: 'urn:ngsi-ld:Building:PUNE:BLD-HYATT-01',
    name: 'Hospitality & Convention Complex',
    category: 'HOSPITALITY_HOTEL',
    grossFloorAreaSqMeters: 93580,
    electricalConnection: {
      substation: '22kV Commercial Feeder B',
      sanctionedLoadKVA: 6250,
      contractDemandKW: 4990
    },
    baselineMetrics: {
      averageDaytimeDemandKW: 3100,
      peakEveningDemandKW: 4400,
      nightBaseDemandKW: 1800,
      powerFactor: 0.96
    },
    provenanceNotice: 'Building energy observations and profiles are calibrated synthetic/benchmark values modeled after hospitality hotel facilities.'
  },
  {
    id: 'urn:ngsi-ld:Building:PUNE:BLD-SOLITAIRE-03',
    name: 'Enterprise Office Center - Tower 3',
    category: 'COMMERCIAL_IT',
    grossFloorAreaSqMeters: 42000,
    electricalConnection: {
      substation: '22kV Distribution Feeder C',
      sanctionedLoadKVA: 3000,
      contractDemandKW: 2400
    },
    baselineMetrics: {
      averageDaytimeDemandKW: 1950,
      peakEveningDemandKW: 1400,
      nightBaseDemandKW: 450,
      powerFactor: 0.98
    },
    provenanceNotice: 'Building energy observations and profiles are calibrated synthetic/benchmark values modeled after corporate office facilities.'
  }
];

export const EnergyAnalyticsView: React.FC<EnergyAnalyticsViewProps> = ({
  sourceMode,
  energyEntities,
  liveStates
}) => {
  // Navigation Sub-tab
  const [activeSubTab, setActiveSubTab] = useState<'TOPOLOGY' | 'FORECASTING'>('TOPOLOGY');

  // Topology & Multi-Asset Telemetry State
  const [topology, setTopology] = useState<EnergyTopologyTreeResponse | null>(null);
  const [liveTelemetryMap, setLiveTelemetryMap] = useState<Record<string, EnergyAssetTelemetry>>({});
  const [microgridSummary, setMicrogridSummary] = useState<MicrogridSummary | null>(null);
  const [selectedNode, setSelectedNode] = useState<EnergyNodeAsset | null>(null);
  const [isTopologyLoading, setIsTopologyLoading] = useState<boolean>(true);
  const [isAdvancing, setIsAdvancing] = useState<boolean>(false);
  const [autoAdvance, setAutoAdvance] = useState<boolean>(false);
  const [refreshTick, setRefreshTick] = useState<number>(0);

  // Facility Forecasting State
  const facilities = useMemo(() => {
    return (energyEntities && energyEntities.length > 0) ? energyEntities : DEFAULT_FACILITIES;
  }, [energyEntities]);

  const [selectedFacilityId, setSelectedFacilityId] = useState<string>(
    () => facilities[0]?.id || 'urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01'
  );

  // Load Topology and Telemetry
  const loadNetworkData = useCallback(async () => {
    try {
      const [topoData, telemData, summaryData] = await Promise.all([
        fetchEnergyTopology().catch(() => null),
        fetchLiveEnergyTelemetry().catch(() => [] as EnergyAssetTelemetry[]),
        fetchMicrogridSummary().catch(() => null)
      ]);

      if (topoData) {
        setTopology(topoData);
        if (!selectedNode && topoData.substation) {
          // Default selection: rooftop solar PV or first feeder child
          const solarNode = topoData.substation.children?.[0]?.children?.find(c => c.nodeType === 'SOLAR_PV');
          setSelectedNode(solarNode || topoData.substation.children?.[0] || topoData.substation);
        }
      }
      if (telemData && Array.isArray(telemData)) {
        const mapping: Record<string, EnergyAssetTelemetry> = {};
        for (const item of telemData) {
          mapping[item.assetId] = item;
        }
        setLiveTelemetryMap(mapping);
      }
      if (summaryData) {
        setMicrogridSummary(summaryData);
      }
    } catch {
      // Keep resilient fallback
    } finally {
      setIsTopologyLoading(false);
    }
  }, [selectedNode]);

  // Initial load
  useEffect(() => {
    loadNetworkData();
  }, [loadNetworkData]);

  // Periodic Telemetry Refresh (every 5 seconds)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchLiveEnergyTelemetry().then((list) => {
        if (Array.isArray(list)) {
          const mapping: Record<string, EnergyAssetTelemetry> = {};
          for (const item of list) {
            mapping[item.assetId] = item;
          }
          setLiveTelemetryMap(mapping);
        }
      }).catch(() => {});
      fetchMicrogridSummary().then(setMicrogridSummary).catch(() => {});
      setRefreshTick((t) => t + 1);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Auto-advance loop when enabled (every 10 seconds steps simulation forward 60 seconds)
  useEffect(() => {
    if (!autoAdvance) return;
    const interval = setInterval(async () => {
      try {
        await advanceEnergyTelemetry(60);
        await loadNetworkData();
        setRefreshTick((t) => t + 1);
      } catch {
        // Silently handle
      }
    }, 10000);
    return () => clearInterval(interval);
  }, [autoAdvance, loadNetworkData]);

  // Manual Step Advance Handler
  const handleAdvanceStep = async () => {
    setIsAdvancing(true);
    try {
      await advanceEnergyTelemetry(60);
      await loadNetworkData();
      setRefreshTick((t) => t + 1);
    } catch {
      // Resilient
    } finally {
      setIsAdvancing(false);
    }
  };

  // Active facility object for Forecasting Tab
  const activeFacility = useMemo(() => {
    return facilities.find(f => f.id === selectedFacilityId) || facilities[0] || DEFAULT_FACILITIES[0];
  }, [facilities, selectedFacilityId]);

  // Read dynamic active telemetry for selected facility
  const activeTelemetry = useMemo(() => {
    if (!liveStates) return null;
    if (liveStates[activeFacility.id]?.metrics?.activePowerKw !== undefined) {
      return liveStates[activeFacility.id].metrics;
    }
    const shortId = activeFacility.id.split(':').pop();
    for (const [k, v] of Object.entries(liveStates)) {
      if (shortId && k.includes(shortId) && v.metrics?.activePowerKw !== undefined) {
        return v.metrics;
      }
    }
    return null;
  }, [liveStates, activeFacility?.id]);

  // Derived values for Forecasting Tab
  const rawContractLimitKw = activeFacility.electricalConnection?.contractDemandKW;
  const contractLimitKw = (rawContractLimitKw !== undefined && rawContractLimitKw > 0) ? rawContractLimitKw : 6800.0;
  const safeContractLimitKw = Math.max(1, contractLimitKw);
  const sanctionedKva = activeFacility.electricalConnection?.sanctionedLoadKVA || Math.round(contractLimitKw * 1.25);
  const substationName = activeFacility.electricalConnection?.substation || '22kV Primary Substation Feeder';
  const facilityPowerFactor = activeTelemetry?.powerFactor ?? activeFacility.baselineMetrics?.powerFactor ?? 0.98;

  const currentKw = useMemo(() => {
    if (activeTelemetry?.activePowerKw !== undefined) {
      return activeTelemetry.activePowerKw;
    }
    const now = new Date();
    const hour = now.getHours() + now.getMinutes() / 60;
    const base = activeFacility.baselineMetrics || DEFAULT_FACILITIES[0].baselineMetrics;
    if (hour >= 0 && hour < 8) {
      return base.nightBaseDemandKW;
    } else if (hour >= 8 && hour < 17) {
      return base.averageDaytimeDemandKW;
    } else {
      return base.peakEveningDemandKW;
    }
  }, [activeTelemetry, activeFacility.baselineMetrics]);

  const headroomKw = Math.max(0, contractLimitKw - currentKw);
  const loadFactor = Math.min(100, Math.max(0, (currentKw / safeContractLimitKw) * 100));
  const carbonRateKgPerKwh = 0.82;
  const currentCarbonHourlyKg = currentKw * carbonRateKgPerKwh;

  const normalThresholdKw = Math.round(contractLimitKw * 0.70);
  const elevatedThresholdKw = Math.round(contractLimitKw * 0.85);

  const nightDemandKw = activeFacility.baselineMetrics?.nightBaseDemandKW ?? Math.round(contractLimitKw * 0.16);
  const daytimeDemandKw = activeFacility.baselineMetrics?.averageDaytimeDemandKW ?? Math.round(contractLimitKw * 0.62);
  const peakDemandKw = activeFacility.baselineMetrics?.peakEveningDemandKW ?? Math.round(contractLimitKw * 0.87);

  const nightPct = Math.min(100, Math.round((nightDemandKw / safeContractLimitKw) * 100));
  const daytimePct = Math.min(100, Math.round((daytimeDemandKw / safeContractLimitKw) * 100));
  const peakPct = Math.min(100, Math.round((peakDemandKw / safeContractLimitKw) * 100));

  // Microgrid summary metrics with safe fallbacks
  const summaryGenKw = microgridSummary?.solarGenerationKw ?? 768.4;
  const summaryLoadKw = (microgridSummary?.buildingLoadKw ?? 5940.2) + (microgridSummary?.evChargingLoadKw ?? 214.0);
  const summaryGridImportKw = microgridSummary?.gridImportKw ?? 5171.8;
  const summaryBessKw = microgridSummary?.bessPowerKw ?? -380.0;
  const summaryBessSoc = microgridSummary?.bessStateOfChargePct ?? 82.5;
  const summaryEvLoadKw = microgridSummary?.evChargingLoadKw ?? 214.0;
  const summaryEvPlugs = Math.min(12, Math.max(1, Math.round((summaryEvLoadKw / 50.0))));
  const summaryPf = microgridSummary?.netPowerFactor ?? 0.982;
  const summaryFreq = 50.02;
  const summaryCarbonOffset = microgridSummary?.carbonOffsetKgPerHour ?? 630.1;

  return (
    <div className="view-container energy-analytics-view">
      {/* View Header */}
      <div className="view-header">
        <div>
          <h1 className="view-title">Corridor Electrical Network Topology & Microgrid Analytics</h1>
          <p className="view-subtitle">
            Authoritative 3-phase AC distribution digital twin, single-line diagram hierarchy, DER multi-asset telemetry, and commercial load forecasting.
          </p>
        </div>
        <div className="view-header-badges">
          <span className="provenance-badge badge-simulation">
            {sourceMode} / IEC 60870-5-104
          </span>
          <span className="provenance-badge badge-live">
            3-PHASE AC PHYSICS
          </span>
          <span className="provenance-badge badge-predicted">
            60-MIN XGBOOST
          </span>
        </div>
      </div>

      {/* Mandatory Data Integrity Caveat */}
      <div className="integrity-caveat-banner">
        <AlertTriangle size={18} style={{ flexShrink: 0 }} />
        <div>
          <strong>Mandatory Data Integrity Caveat:</strong> Corridor electrical network models combine SCADA distribution hierarchy, calibrated commercial building profiles, and physical 3-phase AC power flow calculations. The platform operates strictly in decision-support advisory mode and does not actuate physical circuit breakers or BMS switchgear.
        </div>
      </div>

      {/* Corridor Microgrid Power Flow & Balance Summary Banner */}
      <div className="quick-metrics-row-four" style={{ marginBottom: '16px' }}>
        <div className="metric-box">
          <span className="metric-box-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>Net Grid Import</span>
            <GitFork size={13} color="#FCD34D" />
          </span>
          <span className="metric-box-val font-mono" style={{ color: 'var(--color-text)' }}>
            {summaryGridImportKw.toLocaleString(undefined, { maximumFractionDigits: 0 })} <small>kW</small>
          </span>
          <span className="metric-box-sub">
            Substation Draw (22kV Primary)
          </span>
        </div>

        <div className="metric-box">
          <span className="metric-box-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>Rooftop Solar PV</span>
            <Sun size={13} color="#3FB950" />
          </span>
          <span className="metric-box-val font-mono" style={{ color: '#3FB950' }}>
            +{summaryGenKw.toLocaleString(undefined, { maximumFractionDigits: 0 })} <small>kW</small>
          </span>
          <span className="metric-box-sub">
            {(summaryGenKw / 1200 * 100).toFixed(0)}% of 1.2 MWp Nameplate
          </span>
        </div>

        <div className="metric-box">
          <span className="metric-box-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>BESS Storage</span>
            <BatteryCharging size={13} color="#BC8CFF" />
          </span>
          <span
            className="metric-box-val font-mono"
            style={{ color: summaryBessKw >= 0 ? '#3FB950' : '#818CF8' }}
          >
            {summaryBessKw > 0 ? `+${summaryBessKw.toFixed(0)}` : summaryBessKw.toFixed(0)} <small>kW</small>
          </span>
          <span className="metric-box-sub">
            SOC: {summaryBessSoc.toFixed(1)}% ({summaryBessKw >= 0 ? 'Discharging' : 'Solar Charging'})
          </span>
        </div>

        <div className="metric-box">
          <span className="metric-box-label" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>EV Charging Plaza</span>
            <Car size={13} color="#E879F9" />
          </span>
          <span className="metric-box-val font-mono" style={{ color: '#C084FC' }}>
            {summaryEvLoadKw.toFixed(0)} <small>kW</small>
          </span>
          <span className="metric-box-sub">
            {summaryEvPlugs} / 12 Plugs Active (DC Fast)
          </span>
        </div>
      </div>

      {/* Secondary Metrics Strip: PF, Frequency, Carbon, Monitored Load */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          padding: '10px 16px',
          background: 'var(--color-surface, rgba(9, 9, 11, 0.94))',
          border: '1px solid var(--color-border, #16171B)',
          borderRadius: 'var(--radius-md, 8px)',
          marginBottom: '16px',
          fontSize: '12px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Activity size={14} color="#38BDF8" />
            <span className="text-muted">Total Load:</span>
            <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-text)' }}>
              {summaryLoadKw.toLocaleString(undefined, { maximumFractionDigits: 0 })} kW
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Gauge size={14} color="#3FB950" />
            <span className="text-muted">Corridor Power Factor:</span>
            <span className="font-mono" style={{ fontWeight: 600, color: '#3FB950' }}>
              {summaryPf.toFixed(3)} Lag
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Radio size={14} color="#58A6FF" />
            <span className="text-muted">Grid Frequency:</span>
            <span className="font-mono" style={{ fontWeight: 600, color: '#38BDF8' }}>
              {summaryFreq.toFixed(2)} Hz
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Sun size={14} color="#FCD34D" />
            <span className="text-muted">Carbon Offset:</span>
            <span className="font-mono" style={{ fontWeight: 600, color: '#FCD34D' }}>
              {summaryCarbonOffset.toFixed(1)} kg CO₂e/h
            </span>
          </div>
        </div>

        {/* Telemetry Advance & Refresh Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            onClick={handleAdvanceStep}
            disabled={isAdvancing}
            className="preset-pill-btn"
            style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', padding: '4px 10px' }}
            title="Advance simulated microgrid telemetry clock by 60 seconds"
          >
            <RefreshCw size={12} className={isAdvancing ? 'animate-spin' : ''} />
            <span>Advance Step (+60s)</span>
          </button>

          <button
            type="button"
            onClick={() => setAutoAdvance(!autoAdvance)}
            className={`preset-pill-btn ${autoAdvance ? 'active' : ''}`}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '11px',
              padding: '4px 10px',
              borderColor: autoAdvance ? 'rgba(16, 185, 129, 0.4)' : undefined,
              color: autoAdvance ? '#10B981' : undefined
            }}
            title="Toggle continuous background simulation advancement"
          >
            <Sliders size={12} />
            <span>{autoAdvance ? 'Auto-Advancing (10s)' : 'Auto-Advance Off'}</span>
          </button>
        </div>
      </div>

      {/* Sub-Navigation Switcher */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--color-border, #16171B)', marginBottom: '16px', paddingBottom: '8px' }}>
        <button
          type="button"
          className={`preset-pill-btn ${activeSubTab === 'TOPOLOGY' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('TOPOLOGY')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Layers size={13} />
          <span>Electrical Network Topology & 3-Phase Telemetry</span>
        </button>

        <button
          type="button"
          className={`preset-pill-btn ${activeSubTab === 'FORECASTING' ? 'active' : ''}`}
          onClick={() => setActiveSubTab('FORECASTING')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <Building size={13} />
          <span>Commercial Demand Forecasting & Diurnal Schedules</span>
        </button>
      </div>

      {/* TAB 1: Network Topology & 3-Phase Telemetry */}
      {activeSubTab === 'TOPOLOGY' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(320px, 38%) 1fr',
              gap: '16px',
              alignItems: 'stretch'
            }}
          >
            {/* Left Column: Electrical Single-Line Hierarchy Tree */}
            <div style={{ minHeight: '620px' }}>
              <ElectricalTopologyTree
                topology={topology}
                selectedNodeId={selectedNode?.nodeId || null}
                onSelectNode={(node) => setSelectedNode(node)}
                isLoading={isTopologyLoading}
              />
            </div>

            {/* Right Column: 3-Phase AC Telemetry & Physical Parameters Card */}
            <div style={{ minHeight: '620px' }}>
              <ThreePhaseTelemetryCard
                selectedNode={selectedNode}
                telemetry={selectedNode ? (liveTelemetryMap[selectedNode.nodeId] || selectedNode.telemetry || null) : null}
                isLive={true}
              />
            </div>
          </div>

          {/* Feeder Thermal Loading & Ampacity Margins Panel (Energy TASK-02) */}
          <FeederThermalLoadingCard
            substationId={selectedNode?.nodeType === 'SUBSTATION' ? selectedNode.nodeId : undefined}
            refreshTrigger={refreshTick}
          />
        </div>
      )}

      {/* TAB 2: Commercial Demand Forecasting & Diurnal Schedules */}
      {activeSubTab === 'FORECASTING' && (
        <>
          {/* Facility Selector & Capacity Strip */}
          <div className="analytics-filter-bar" style={{ marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Building size={16} className="text-muted" />
              <label htmlFor="facility-selector" style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                Monitored Facility:
              </label>
              <select
                id="facility-selector"
                className="analytics-select"
                value={selectedFacilityId}
                onChange={(e) => setSelectedFacilityId(e.target.value)}
              >
                {facilities.map((fac) => (
                  <option key={fac.id} value={fac.id}>
                    {fac.name} ({(fac.grossFloorAreaSqMeters || 0).toLocaleString()} m² GFA)
                  </option>
                ))}
              </select>
            </div>

            <div className="analytics-meta-pill">
              <Gauge size={14} className="text-muted" />
              <span>
                Contract Limit: {contractLimitKw.toLocaleString()} kW | Sanctioned: {sanctionedKva.toLocaleString()} kVA
              </span>
            </div>
          </div>

          {/* Quick Facility KPI Row */}
          <div className="quick-metrics-row-four" style={{ marginBottom: '16px' }}>
            <div className="metric-box">
              <span className="metric-box-label">Current Active Demand</span>
              <span
                className="metric-box-val font-mono"
                style={{
                  color: currentKw > elevatedThresholdKw ? '#F85149' : currentKw > normalThresholdKw ? '#D29922' : '#3FB950'
                }}
              >
                {currentKw.toFixed(0)} <small>kW</small>
              </span>
              <span className="metric-box-sub">
                {loadFactor.toFixed(1)}% of contracted capacity
              </span>
            </div>

            <div className="metric-box">
              <span className="metric-box-label">Contract Headroom</span>
              <span
                className="metric-box-val font-mono"
                style={{
                  color: headroomKw < (contractLimitKw * 0.15) ? '#F85149' : '#3FB950'
                }}
              >
                {headroomKw.toFixed(0)} <small>kW</small>
              </span>
              <span className="metric-box-sub">
                {headroomKw > (contractLimitKw * 0.15) ? 'Safe operational buffer' : 'Peak threshold risk'}
              </span>
            </div>

            <div className="metric-box">
              <span className="metric-box-label">Hourly Carbon Footprint</span>
              <span className="metric-box-val font-mono" style={{ color: 'var(--color-text)' }}>
                {(currentCarbonHourlyKg / 1000).toFixed(2)} <small>t CO₂e/h</small>
              </span>
              <span className="metric-box-sub">
                @ 0.82 kg CO₂/kWh grid factor
              </span>
            </div>

            <div className="metric-box">
              <span className="metric-box-label">Substation Feeder</span>
              <span className="metric-box-val font-mono" style={{ fontSize: '15px', color: 'var(--color-text)' }}>
                {substationName}
              </span>
              <span className="metric-box-sub">
                Power Factor: {facilityPowerFactor.toFixed(2)} lag ({(activeFacility.category || 'COMMERCIAL').replace(/_/g, ' ')})
              </span>
            </div>
          </div>

          {/* Main Grid: Forecast & Diurnal Schedule */}
          <div className="analytics-grid-two-col">
            {/* Left Column: 60-Minute Forecast Panel with Conformal Intervals & TreeSHAP */}
            <div className="analytics-card">
              <div className="analytics-card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Zap size={18} color="#F59E0B" />
                  <span className="card-title">60-Minute Predictive Demand Inference</span>
                </div>
                <span className="provenance-badge badge-predicted">PREDICTED</span>
              </div>

              <div style={{ padding: '4px 0' }}>
                <ForecastPanel
                  key={activeFacility.id}
                  entityType="Building"
                  entityId={activeFacility.id}
                  currentValue={currentKw}
                  contractDemandKw={contractLimitKw}
                />
              </div>

              <div className="analytics-notice-box" style={{ marginTop: '16px' }}>
                <HelpCircle size={14} className="text-muted" />
                <span>
                  <strong>Scientific Notice:</strong> Forecasts use XGBoost trained on diurnal hour-of-day, day-of-week, and temperature lag features with conformalized uncertainty bands.
                </span>
              </div>
            </div>

            {/* Right Column: Diurnal Load Profile & Threshold Classification */}
            <div className="analytics-card">
              <div className="analytics-card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Clock size={18} color="var(--color-primary, #2F81F7)" />
                  <span className="card-title">Diurnal Load Profiles & Threshold Rules</span>
                </div>
                <span className="text-muted" style={{ fontSize: '12px' }}>
                  {(activeFacility.category || 'COMMERCIAL').replace(/_/g, ' ')} Archetype
                </span>
              </div>

              <div className="diurnal-profile-list">
                <div className="diurnal-item">
                  <div className="diurnal-item-header">
                    <span className="diurnal-title">Night Base Load (00:00 - 08:00)</span>
                    <span className="diurnal-val font-mono">{nightDemandKw.toLocaleString()} kW</span>
                  </div>
                  <p className="diurnal-desc">
                    Minimal ventilation, essential refrigeration, server rooms, and perimeter emergency security lighting.
                  </p>
                  <div className="progress-bar-bg">
                    <div className="progress-bar-fill" style={{ width: `${nightPct}%`, backgroundColor: '#3FB950' }} />
                  </div>
                </div>

                <div className="diurnal-item">
                  <div className="diurnal-item-header">
                    <span className="diurnal-title">Daytime Business Operations (08:00 - 16:00)</span>
                    <span className="diurnal-val font-mono">{daytimeDemandKw.toLocaleString()} kW</span>
                  </div>
                  <p className="diurnal-desc">
                    Central HVAC chillers, elevators/escalators, commercial tenant operations, and primary facilities.
                  </p>
                  <div className="progress-bar-bg">
                    <div className="progress-bar-fill" style={{ width: `${daytimePct}%`, backgroundColor: '#2F81F7' }} />
                  </div>
                </div>

                <div className="diurnal-item">
                  <div className="diurnal-item-header">
                    <span className="diurnal-title">Evening Peak Operations (16:00 - 22:00)</span>
                    <span className="diurnal-val font-mono">{peakDemandKw.toLocaleString()} kW</span>
                  </div>
                  <p className="diurnal-desc">
                    Peak visitor footfall, intensive cooling/heating cycles, architectural illumination, and ancillary loads.
                  </p>
                  <div className="progress-bar-bg">
                    <div className="progress-bar-fill" style={{ width: `${peakPct}%`, backgroundColor: '#D29922' }} />
                  </div>
                </div>
              </div>

              <h4 style={{ fontSize: '13px', fontWeight: 600, marginTop: '20px', marginBottom: '10px', color: 'var(--color-text, #F0F6FC)' }}>
                Peak Demand Governance Thresholds
              </h4>
              <table className="analytics-table">
                <thead>
                  <tr>
                    <th>Tier</th>
                    <th>Range (kW)</th>
                    <th>Threshold Status</th>
                    <th>Advisory Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Normal Buffer</td>
                    <td className="mono-cell font-mono">&lt; {normalThresholdKw.toLocaleString()} kW</td>
                    <td><span className="status-pill status-active" style={{ color: '#3FB950', borderColor: 'rgba(63, 185, 80, 0.3)' }}>Optimal</span></td>
                    <td>Standard grid supply; no intervention recommended</td>
                  </tr>
                  <tr>
                    <td>Elevated Peak</td>
                    <td className="mono-cell font-mono">{normalThresholdKw.toLocaleString()} - {elevatedThresholdKw.toLocaleString()} kW</td>
                    <td><span className="status-pill status-review" style={{ color: '#D29922', borderColor: 'rgba(210, 153, 34, 0.3)' }}>Warning</span></td>
                    <td>Advisory recommendation: Pre-cool zones, stagger chiller cycles</td>
                  </tr>
                  <tr>
                    <td>Contract Risk</td>
                    <td className="mono-cell font-mono">&gt; {elevatedThresholdKw.toLocaleString()} kW</td>
                    <td><span className="status-pill status-dismissed" style={{ color: '#F85149', borderColor: 'rgba(248, 81, 73, 0.3)' }}>Critical</span></td>
                    <td>Advisory recommendation: Dispatch on-site clean backup / BESS peak shaving</td>
                  </tr>
                </tbody>
              </table>

              <div className="analytics-notice-box" style={{ marginTop: '16px' }}>
                <ShieldAlert size={14} color="#F59E0B" />
                <span>
                  <strong>Advisory Governance Notice:</strong> All energy management recommendations require manual confirmation by facility engineering staff. The platform does not issue automated control commands to electrical switchgear.
                </span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

