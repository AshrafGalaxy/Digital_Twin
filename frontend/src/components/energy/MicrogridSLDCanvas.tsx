import React, { useEffect, useMemo, useState } from 'react';
import {
  Zap,
  Sun,
  BatteryCharging,
  Building2,
  Car,
  Activity,
  ShieldCheck,
  Flame
} from 'lucide-react';
import {
  EnergyNodeAsset,
  EnergyTopologyTreeResponse,
  EnergyAssetTelemetry,
  MicrogridSummary,
  SourceMode
} from '../../types/twin';
import { FeederThermalMargin } from '../../services/api';

export interface MicrogridSLDCanvasProps {
  topology: EnergyTopologyTreeResponse | null;
  liveTelemetryMap: Record<string, EnergyAssetTelemetry>;
  microgridSummary: MicrogridSummary | null;
  selectedNodeId: string | null;
  onSelectNode: (node: EnergyNodeAsset) => void;
  feederThermalMargins?: FeederThermalMargin[];
  sourceMode?: SourceMode;
}

export const MicrogridSLDCanvas: React.FC<MicrogridSLDCanvasProps> = ({
  topology,
  liveTelemetryMap,
  microgridSummary,
  selectedNodeId,
  onSelectNode,
  feederThermalMargins,
  sourceMode = 'SIMULATION'
}) => {
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [isLightTheme, setIsLightTheme] = useState<boolean>(() =>
    typeof document !== 'undefined' && document.documentElement.getAttribute('data-theme') === 'light'
  );

  useEffect(() => {
    if (typeof document === 'undefined') return;
    const root = document.documentElement;
    const syncTheme = () => setIsLightTheme(root.getAttribute('data-theme') === 'light');
    syncTheme();
    const observer = new MutationObserver(syncTheme);
    observer.observe(root, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  const sldPalette = useMemo(
    () =>
      isLightTheme
        ? {
            surfaceCanvas: '#F8FAFC',
            surfaceBar: '#FFFFFF',
            surfaceFooter: '#FFFFFF',
            border: '#E2E8F0',
            nodeFill: '#FFFFFF',
            nodeSelectedFill: '#EFF6FF',
            nodeStroke: '#CBD5E1',
            gridDot: '#CBD5E1',
            wireBase: '#94A3B8',
            wireSub: '#64748B',
            busbarLine: '#334155',
            busbarLabelBg: '#F1F5F9',
            busbarLabelStroke: '#94A3B8',
            textPrimary: '#0F172A',
            textSecondary: '#334155',
            textMuted: '#475569',
            blue: '#0284C7',
            green: '#047857',
            amber: '#B45309',
            amberFlow: '#D97706',
            purple: '#7E22CE',
            purpleIcon: '#9333EA',
            cyan: '#0E7490',
            gridFlow: '#4F46E5',
            socTrack: '#E2E8F0',
            cardShadow: '0 4px 16px rgba(15, 23, 42, 0.08)'
          }
        : {
            surfaceCanvas: '#020617',
            surfaceBar: 'rgba(15, 23, 42, 0.85)',
            surfaceFooter: 'rgba(15, 23, 42, 0.95)',
            border: '#1E293B',
            nodeFill: '#0F172A',
            nodeSelectedFill: '#1E293B',
            nodeStroke: '#334155',
            gridDot: '#1E293B',
            wireBase: '#334155',
            wireSub: '#64748B',
            busbarLine: '#E2E8F0',
            busbarLabelBg: '#0F172A',
            busbarLabelStroke: '#475569',
            textPrimary: '#F8FAFC',
            textSecondary: '#E2E8F0',
            textMuted: '#94A3B8',
            blue: '#38BDF8',
            green: '#34D399',
            amber: '#FCD34D',
            amberFlow: '#FBBF24',
            purple: '#C084FC',
            purpleIcon: '#E879F9',
            cyan: '#22D3EE',
            gridFlow: '#818CF8',
            socTrack: '#1E293B',
            cardShadow: '0 4px 20px rgba(0, 0, 0, 0.45)'
          },
    [isLightTheme]
  );

  // Flatten all nodes from topology for lookup
  const nodeMap = useMemo(() => {
    const map = new Map<string, EnergyNodeAsset>();
    const traverse = (node: EnergyNodeAsset | null) => {
      if (!node) return;
      map.set(node.nodeId, node);
      if (node.children) {
        for (const child of node.children) {
          traverse(child);
        }
      }
    };
    if (topology?.substation) {
      traverse(topology.substation);
    }
    return map;
  }, [topology]);

  // Find canonical assets by type or ID
  const substationNode = useMemo(() => {
    return topology?.substation || null;
  }, [topology]);

  const solarNode = useMemo(() => {
    for (const n of nodeMap.values()) {
      if (n.nodeType === 'SOLAR_PV') return n;
    }
    return null;
  }, [nodeMap]);

  const bessNode = useMemo(() => {
    for (const n of nodeMap.values()) {
      if (n.nodeType === 'BESS') return n;
    }
    return null;
  }, [nodeMap]);

  const evNode = useMemo(() => {
    for (const n of nodeMap.values()) {
      if (n.nodeType === 'EV_HUB') return n;
    }
    return null;
  }, [nodeMap]);

  const buildingNodes = useMemo(() => {
    const list: EnergyNodeAsset[] = [];
    for (const n of nodeMap.values()) {
      if (n.nodeType === 'BUILDING_LOAD') list.push(n);
    }
    return list;
  }, [nodeMap]);

  const feederNodes = useMemo(() => {
    const list: EnergyNodeAsset[] = [];
    for (const n of nodeMap.values()) {
      if (n.nodeType === 'FEEDER') list.push(n);
    }
    return list;
  }, [nodeMap]);

  // Telemetry values for canonical nodes
  const subTelem = substationNode ? (liveTelemetryMap[substationNode.nodeId] || substationNode.telemetry) : null;
  const solarTelem = solarNode ? (liveTelemetryMap[solarNode.nodeId] || solarNode.telemetry) : null;
  const bessTelem = bessNode ? (liveTelemetryMap[bessNode.nodeId] || bessNode.telemetry) : null;
  const evTelem = evNode ? (liveTelemetryMap[evNode.nodeId] || evNode.telemetry) : null;

  // Active power values
  const gridImportKw = microgridSummary?.gridImportKw ?? subTelem?.activePowerKw ?? 3120.0;
  const solarGenKw = microgridSummary?.solarGenerationKw ?? solarTelem?.activePowerKw ?? 740.0;
  const bessKw = microgridSummary?.bessPowerKw ?? bessTelem?.activePowerKw ?? -350.0;
  const bessSoCPct = microgridSummary?.bessStateOfChargePct ?? (bessTelem?.deviceMetrics?.stateOfChargePct ?? 72.0);
  const evLoadKw = microgridSummary?.evChargingLoadKw ?? evTelem?.activePowerKw ?? 410.0;

  // Feeder thermal loading map
  const feederMarginMap = useMemo(() => {
    const map = new Map<string, FeederThermalMargin>();
    if (feederThermalMargins) {
      for (const f of feederThermalMargins) {
        map.set(f.feederId, f);
      }
    }
    return map;
  }, [feederThermalMargins]);

  // Compute thermal loading ratio for branch lines
  const getFeederLoading = (feederId?: string, fallbackLoadingPct?: number) => {
    if (feederId && feederMarginMap.has(feederId)) {
      const margin = feederMarginMap.get(feederId)!;
      return {
        ratio: margin.thermalLoadingRatio,
        pct: margin.thermalLoadingPct,
        currentA: margin.currentAmps,
        status: margin.status
      };
    }
    const ratio = (fallbackLoadingPct ?? 65.0) / 100.0;
    return {
      ratio,
      pct: fallbackLoadingPct ?? 65.0,
      currentA: 260.0,
      status: ratio >= 0.85 ? 'CRITICAL_OVERLOAD_RISK' : ratio >= 0.70 ? 'WARNING' : 'NOMINAL'
    };
  };

  const feeder1 = feederNodes[0] || null;
  const feeder2 = feederNodes[1] || null;
  const feeder3 = feederNodes[2] || null;

  const f1Load = getFeederLoading(feeder1?.nodeId, feeder1?.loadingPct ?? 62.0);
  const f2Load = getFeederLoading(feeder2?.nodeId, feeder2?.loadingPct ?? 74.0);
  const f3Load = getFeederLoading(feeder3?.nodeId, feeder3?.loadingPct ?? 58.0);

  // Flow animation speeds (shorter duration = faster flow)
  const calculateSpeed = (kw: number, maxKw: number = 4000) => {
    const absKw = Math.abs(kw);
    if (absKw <= 5) return 0; // Stopped
    return Math.max(0.6, Math.min(3.5, 3.5 - (absKw / maxKw) * 2.5));
  };

  const gridSpeed = calculateSpeed(gridImportKw);
  const solarSpeed = calculateSpeed(solarGenKw, 1200);
  const bessSpeed = calculateSpeed(bessKw, 1000);
  const evSpeed = calculateSpeed(evLoadKw, 720);

  // BESS operational mode
  const bessMode = bessKw > 15 ? 'DISCHARGING' : bessKw < -15 ? 'CHARGING' : 'STANDBY';

  // Helper for thermal color
  const getThermalColor = (ratio: number) => {
    if (ratio >= 0.85) return '#F43F5E'; // Pulsing Rose Alert
    if (ratio >= 0.70) return '#F59E0B'; // Amber Warning
    return '#10B981'; // Emerald Nominal
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        background: sldPalette.surfaceCanvas,
        border: `1px solid ${sldPalette.border}`,
        borderRadius: '8px',
        overflow: 'hidden',
        boxShadow: sldPalette.cardShadow
      }}
    >
      {/* Canvas Top Bar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          padding: '12px 18px',
          borderBottom: `1px solid ${sldPalette.border}`,
          background: sldPalette.surfaceBar
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              backgroundColor: 'rgba(245, 158, 11, 0.15)',
              border: '1px solid rgba(245, 158, 11, 0.4)'
            }}
          >
            <Zap size={16} color={sldPalette.amber} />
          </div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, color: sldPalette.textPrimary, letterSpacing: '0.02em' }}>
              Microgrid Electrical Single-Line Diagram & Power Flow Canvas
            </div>
            <div style={{ fontSize: '11px', color: sldPalette.textMuted }}>
              IEC 60870-5-104 / IEEE 1547 Point of Common Coupling (PCC) & Feeder Hierarchy
            </div>
          </div>
        </div>

        {/* Status Badges & Non-Actuation Notice */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span
            style={{
              fontSize: '11px',
              fontFamily: 'monospace',
              padding: '2px 8px',
              borderRadius: '4px',
              backgroundColor: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.35)',
              color: sldPalette.blue,
              fontWeight: 600
            }}
          >
            {sourceMode} / 3-PHASE AC
          </span>

          <span
            style={{
              fontSize: '11px',
              fontFamily: 'monospace',
              padding: '2px 8px',
              borderRadius: '4px',
              backgroundColor: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid rgba(16, 185, 129, 0.35)',
              color: sldPalette.green,
              fontWeight: 600
            }}
          >
            ACTIVE DYNAMIC FLOW
          </span>

          <span
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '11px',
              padding: '2px 8px',
              borderRadius: '4px',
              backgroundColor: 'rgba(235, 169, 0, 0.1)',
              border: '1px solid rgba(235, 169, 0, 0.3)',
              color: sldPalette.amber
            }}
            title="Platform commands are non-actuating decision support only. Breaker actuation requires field personnel authorization."
          >
            <ShieldCheck size={12} color={sldPalette.amber} />
            <span>Advisory Only (Non-Actuating)</span>
          </span>
        </div>
      </div>

      {/* SVG Canvas Area */}
      <div style={{ position: 'relative', width: '100%', minHeight: '520px', backgroundColor: sldPalette.surfaceCanvas }}>
        <svg
          viewBox="0 0 1000 600"
          style={{
            width: '100%',
            height: '100%',
            display: 'block',
            userSelect: 'none'
          }}
        >
          <defs>
            {/* Grid dot pattern for technical aesthetic */}
            <pattern id="sld-grid-pattern" width="20" height="20" patternUnits="userSpaceOnUse">
              <circle cx="2" cy="2" r="1" fill={sldPalette.gridDot} opacity="0.6" />
            </pattern>

            {/* Glowing filter for selected nodes */}
            <filter id="sld-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* CSS Keyframes for directional power flow particles */}
            <style>
              {`
                @keyframes sldFlowDown {
                  from { stroke-dashoffset: 24; }
                  to { stroke-dashoffset: 0; }
                }
                @keyframes sldFlowUp {
                  from { stroke-dashoffset: 0; }
                  to { stroke-dashoffset: 24; }
                }
                @keyframes sldPulseAlarm {
                  0%, 100% { stroke-opacity: 0.6; stroke-width: 3; }
                  50% { stroke-opacity: 1.0; stroke-width: 5; }
                }
                .sld-flow-grid {
                  animation: sldFlowDown ${gridSpeed > 0 ? gridSpeed : 0}s linear infinite;
                }
                .sld-flow-solar {
                  animation: sldFlowUp ${solarSpeed > 0 ? solarSpeed : 0}s linear infinite;
                }
                .sld-flow-bess {
                  animation: ${bessKw > 0 ? 'sldFlowUp' : 'sldFlowDown'} ${bessSpeed > 0 ? bessSpeed : 0}s linear infinite;
                }
                .sld-flow-load {
                  animation: sldFlowDown 2.2s linear infinite;
                }
                .sld-flow-ev {
                  animation: sldFlowDown ${evSpeed > 0 ? evSpeed : 0}s linear infinite;
                }
              `}
            </style>
          </defs>

          {/* Background Grid */}
          <rect width="1000" height="600" fill="url(#sld-grid-pattern)" />

          {/* ========================================================================= */}
          {/* SECTION 1: POINT OF COMMON COUPLING (PCC) & 22kV UTILITY GRID             */}
          {/* ========================================================================= */}

          {/* Incoming 22kV Overhead Line */}
          <line x1="500" y1="0" x2="500" y2="25" stroke="#64748B" strokeWidth="2.5" />
          <text x="510" y="16" fill={sldPalette.textMuted} fontSize="10" fontFamily="monospace">
            22kV Utility Grid Feed
          </text>

          {/* PCC Substation Card */}
          <g
            onClick={() => substationNode && onSelectNode(substationNode)}
            onMouseEnter={() => setHoveredNodeId(substationNode?.nodeId || 'SUB')}
            onMouseLeave={() => setHoveredNodeId(null)}
            style={{ cursor: 'pointer' }}
          >
            <rect
              x="375"
              y="25"
              width="250"
              height="75"
              rx="8"
              fill={selectedNodeId === substationNode?.nodeId ? sldPalette.nodeSelectedFill : sldPalette.nodeFill}
              stroke={selectedNodeId === substationNode?.nodeId ? '#38BDF8' : sldPalette.nodeStroke}
              strokeWidth={selectedNodeId === substationNode?.nodeId ? 2 : 1}
              filter={selectedNodeId === substationNode?.nodeId ? 'url(#sld-glow)' : undefined}
            />
            {/* Header Badge */}
            <foreignObject x="387" y="37" width="18" height="18">
              <Zap size={16} color="#FCD34D" />
            </foreignObject>
            <text x="412" y="49" fill={sldPalette.textPrimary} fontSize="12" fontWeight="700">
              Primary Substation (PCC)
            </text>
            <rect x="548" y="37" width="65" height="16" rx="3" fill="#10B981" fillOpacity="0.15" stroke="#10B981" strokeWidth="0.8" />
            <text x="554" y="49" fill={sldPalette.green} fontSize="9" fontFamily="monospace" fontWeight="700">
              CB-01 CLOSED
            </text>

            {/* Metrics Row */}
            <text x="395" y="70" fill={sldPalette.textMuted} fontSize="10">
              Grid Import:
            </text>
            <text x="460" y="70" fill={sldPalette.blue} fontSize="11" fontFamily="monospace" fontWeight="700">
              {gridImportKw.toLocaleString(undefined, { maximumFractionDigits: 0 })} kW
            </text>

            <text x="395" y="86" fill={sldPalette.textMuted} fontSize="10">
              Bus Voltage:
            </text>
            <text x="460" y="86" fill={sldPalette.textPrimary} fontSize="10" fontFamily="monospace">
              415.0 V AC | 50.00 Hz
            </text>
          </g>

          {/* Line from Substation to Transformer */}
          <line x1="500" y1="100" x2="500" y2="124" stroke="#64748B" strokeWidth="2.5" />
          {/* Grid flow particles */}
          {gridSpeed > 0 && (
            <line
              x1="500"
              y1="100"
              x2="500"
              y2="124"
              stroke="#818CF8"
              strokeWidth="2.5"
              strokeDasharray="6 6"
              className="sld-flow-grid"
            />
          )}

          {/* 22kV / 415V Step-Down Transformer Symbol */}
          <g>
            <circle cx="500" cy="132" r="11" fill="none" stroke="#FCD34D" strokeWidth="2" />
            <circle cx="500" cy="144" r="11" fill="none" stroke="#38BDF8" strokeWidth="2" />
            <text x="522" y="136" fill="#E2E8F0" fontSize="10" fontWeight="600">
              Dyn11 Step-Down Trafo
            </text>
            <text x="522" y="148" fill={sldPalette.textMuted} fontSize="9" fontFamily="monospace">
              22kV / 415V (10 MVA, 2.5% loss)
            </text>
          </g>

          {/* Line from Transformer to Main Busbar */}
          <line x1="500" y1="156" x2="500" y2="180" stroke="#64748B" strokeWidth="2.5" />
          {gridSpeed > 0 && (
            <line
              x1="500"
              y1="156"
              x2="500"
              y2="180"
              stroke="#818CF8"
              strokeWidth="2.5"
              strokeDasharray="6 6"
              className="sld-flow-grid"
            />
          )}

          {/* ========================================================================= */}
          {/* SECTION 2: 415V THREE-PHASE LOW-VOLTAGE DISTRIBUTION BUSBAR              */}
          {/* ========================================================================= */}

          {/* Main Busbar Line */}
          <line x1="100" y1="180" x2="900" y2="180" stroke={sldPalette.busbarLine} strokeWidth="6" strokeLinecap="round" />
          <rect x="360" y="168" width="280" height="24" rx="4" fill={sldPalette.nodeFill} stroke="#475569" strokeWidth="1" />
          <text x="500" y="184" fill={sldPalette.textPrimary} fontSize="10" fontWeight="700" textAnchor="middle" letterSpacing="0.05em">
            415V AC THREE-PHASE LOW-VOLTAGE BUSBAR (BUS-01)
          </text>

          {/* ========================================================================= */}
          {/* SECTION 3: FEEDER BRANCHES & THERMAL LOADING INDICATORS                   */}
          {/* ========================================================================= */}

          {/* --- FEEDER 1: RETAIL & MIXED-USE (Left Drop, x=240) --- */}
          <line
            x1="240"
            y1="180"
            x2="240"
            y2="240"
            stroke={getThermalColor(f1Load.ratio)}
            strokeWidth="3"
            style={f1Load.ratio >= 0.85 ? { animation: 'sldPulseAlarm 1.5s infinite' } : undefined}
          />
          {/* Feeder 1 Tag */}
          <g
            onClick={() => feeder1 && onSelectNode(feeder1)}
            style={{ cursor: 'pointer' }}
          >
            <rect
              x="175"
              y="200"
              width="130"
              height="28"
              rx="4"
              fill={sldPalette.nodeFill}
              stroke={getThermalColor(f1Load.ratio)}
              strokeWidth="1"
            />
            <text x="183" y="214" fill={sldPalette.textPrimary} fontSize="10" fontWeight="600">
              Feeder 1 (Retail)
            </text>
            <text x="183" y="224" fill={getThermalColor(f1Load.ratio)} fontSize="8" fontFamily="monospace">
              {f1Load.pct.toFixed(0)}% Thermal ({f1Load.currentA.toFixed(0)}A)
            </text>
          </g>

          {/* Branch Lines from Feeder 1 to Solar PV and Commercial Retail */}
          <path
            d="M 240 240 L 120 240 L 120 295"
            fill="none"
            stroke={sldPalette.wireBase}
            strokeWidth="2"
          />
          {solarGenKw > 10 && (
            <path
              d="M 120 295 L 120 240 L 240 240 L 240 180"
              fill="none"
              stroke="#34D399"
              strokeWidth="2"
              strokeDasharray="6 6"
              className="sld-flow-solar"
            />
          )}

          <path
            d="M 240 240 L 240 465"
            fill="none"
            stroke={sldPalette.wireBase}
            strokeWidth="2"
          />
          <path
            d="M 240 240 L 240 465"
            fill="none"
            stroke="#38BDF8"
            strokeWidth="2"
            strokeDasharray="6 6"
            className="sld-flow-load"
          />

          {/* --- FEEDER 2: ENTERPRISE & STORAGE (Center Drop, x=500) --- */}
          <line
            x1="500"
            y1="180"
            x2="500"
            y2="240"
            stroke={getThermalColor(f2Load.ratio)}
            strokeWidth="3"
            style={f2Load.ratio >= 0.85 ? { animation: 'sldPulseAlarm 1.5s infinite' } : undefined}
          />
          {/* Feeder 2 Tag */}
          <g
            onClick={() => feeder2 && onSelectNode(feeder2)}
            style={{ cursor: 'pointer' }}
          >
            <rect
              x="435"
              y="200"
              width="130"
              height="28"
              rx="4"
              fill={sldPalette.nodeFill}
              stroke={getThermalColor(f2Load.ratio)}
              strokeWidth="1"
            />
            <text x="443" y="214" fill={sldPalette.textPrimary} fontSize="10" fontWeight="600">
              Feeder 2 (Enterprise)
            </text>
            <text x="443" y="224" fill={getThermalColor(f2Load.ratio)} fontSize="8" fontFamily="monospace">
              {f2Load.pct.toFixed(0)}% Thermal ({f2Load.currentA.toFixed(0)}A)
            </text>
          </g>

          {/* BESS Connection Path */}
          <line x1="500" y1="240" x2="500" y2="290" stroke={sldPalette.wireBase} strokeWidth="2" />
          {bessSpeed > 0 && (
            <line
              x1="500"
              y1="240"
              x2="500"
              y2="290"
              stroke={bessKw > 0 ? '#FBBF24' : '#22D3EE'}
              strokeWidth="2"
              strokeDasharray="6 6"
              className="sld-flow-bess"
            />
          )}

          {/* Line from BESS down to Enterprise Load */}
          <line x1="500" y1="395" x2="500" y2="465" stroke={sldPalette.wireBase} strokeWidth="2" />
          <line
            x1="500"
            y1="395"
            x2="500"
            y2="465"
            stroke="#38BDF8"
            strokeWidth="2"
            strokeDasharray="6 6"
            className="sld-flow-load"
          />

          {/* --- FEEDER 3: HOSPITALITY & TRANSIT (Right Drop, x=780) --- */}
          <line
            x1="780"
            y1="180"
            x2="780"
            y2="240"
            stroke={getThermalColor(f3Load.ratio)}
            strokeWidth="3"
            style={f3Load.ratio >= 0.85 ? { animation: 'sldPulseAlarm 1.5s infinite' } : undefined}
          />
          {/* Feeder 3 Tag */}
          <g
            onClick={() => feeder3 && onSelectNode(feeder3)}
            style={{ cursor: 'pointer' }}
          >
            <rect
              x="715"
              y="200"
              width="130"
              height="28"
              rx="4"
              fill={sldPalette.nodeFill}
              stroke={getThermalColor(f3Load.ratio)}
              strokeWidth="1"
            />
            <text x="723" y="214" fill={sldPalette.textPrimary} fontSize="10" fontWeight="600">
              Feeder 3 (Transit)
            </text>
            <text x="723" y="224" fill={getThermalColor(f3Load.ratio)} fontSize="8" fontFamily="monospace">
              {f3Load.pct.toFixed(0)}% Thermal ({f3Load.currentA.toFixed(0)}A)
            </text>
          </g>

          {/* Branch Lines from Feeder 3 to EV Hub and Hospitality Load */}
          <path
            d="M 780 240 L 710 240 L 710 465"
            fill="none"
            stroke={sldPalette.wireBase}
            strokeWidth="2"
          />
          {evLoadKw > 10 && (
            <path
              d="M 780 180 L 780 240 L 710 240 L 710 465"
              fill="none"
              stroke="#C084FC"
              strokeWidth="2"
              strokeDasharray="6 6"
              className="sld-flow-ev"
            />
          )}

          <path
            d="M 780 240 L 885 240 L 885 465"
            fill="none"
            stroke={sldPalette.wireBase}
            strokeWidth="2"
          />
          <path
            d="M 780 180 L 780 240 L 885 240 L 885 465"
            fill="none"
            stroke="#38BDF8"
            strokeWidth="2"
            strokeDasharray="6 6"
            className="sld-flow-load"
          />

          {/* ========================================================================= */}
          {/* SECTION 4: DISTRIBUTED ENERGY RESOURCE (DER) NODES                        */}
          {/* ========================================================================= */}

          {/* 1. ROOFTOP SOLAR PV NODE */}
          <g
            onClick={() => solarNode && onSelectNode(solarNode)}
            onMouseEnter={() => setHoveredNodeId(solarNode?.nodeId || 'SOLAR')}
            onMouseLeave={() => setHoveredNodeId(null)}
            style={{ cursor: 'pointer' }}
          >
            <rect
              x="35"
              y="295"
              width="170"
              height="95"
              rx="6"
              fill={selectedNodeId === solarNode?.nodeId ? sldPalette.nodeSelectedFill : sldPalette.nodeFill}
              stroke={selectedNodeId === solarNode?.nodeId ? '#34D399' : sldPalette.nodeStroke}
              strokeWidth={selectedNodeId === solarNode?.nodeId ? 2 : 1}
              filter={selectedNodeId === solarNode?.nodeId ? 'url(#sld-glow)' : undefined}
            />
            {/* Header */}
            <foreignObject x="47" y="307" width="18" height="18">
              <Sun size={16} color="#34D399" />
            </foreignObject>
            <text x="70" y="318" fill={sldPalette.textPrimary} fontSize="11" fontWeight="700">
              Rooftop Solar PV
            </text>
            <text x="70" y="329" fill={sldPalette.textMuted} fontSize="8" fontFamily="monospace">
              1.2 MWp Smart Inverter
            </text>

            {/* Metrics */}
            <text x="50" y="348" fill={sldPalette.textMuted} fontSize="9">
              Generation:
            </text>
            <text x="110" y="348" fill={sldPalette.green} fontSize="11" fontFamily="monospace" fontWeight="700">
              {solarGenKw.toFixed(0)} kW
            </text>

            <text x="50" y="364" fill={sldPalette.textMuted} fontSize="9">
              Irradiance:
            </text>
            <text x="110" y="364" fill={sldPalette.textPrimary} fontSize="10" fontFamily="monospace">
              {solarTelem?.deviceMetrics?.solarIrradianceWm2 ?? (solarGenKw > 50 ? 820 : 0)} W/m²
            </text>

            <text x="50" y="380" fill={sldPalette.textMuted} fontSize="9">
              Inverter:
            </text>
            <text x="110" y="380" fill={sldPalette.blue} fontSize="9" fontFamily="monospace">
              IEEE 1547 Mode
            </text>
          </g>

          {/* 2. BESS BATTERY ENERGY STORAGE NODE */}
          <g
            onClick={() => bessNode && onSelectNode(bessNode)}
            onMouseEnter={() => setHoveredNodeId(bessNode?.nodeId || 'BESS')}
            onMouseLeave={() => setHoveredNodeId(null)}
            style={{ cursor: 'pointer' }}
          >
            <rect
              x="400"
              y="290"
              width="200"
              height="105"
              rx="6"
              fill={selectedNodeId === bessNode?.nodeId ? sldPalette.nodeSelectedFill : sldPalette.nodeFill}
              stroke={selectedNodeId === bessNode?.nodeId ? '#BC8CFF' : sldPalette.nodeStroke}
              strokeWidth={selectedNodeId === bessNode?.nodeId ? 2 : 1}
              filter={selectedNodeId === bessNode?.nodeId ? 'url(#sld-glow)' : undefined}
            />
            {/* Header */}
            <foreignObject x="412" y="302" width="18" height="18">
              <BatteryCharging size={16} color="#BC8CFF" />
            </foreignObject>
            <text x="435" y="313" fill={sldPalette.textPrimary} fontSize="11" fontWeight="700">
              Substation Support BESS
            </text>
            <rect
              x="530"
              y="302"
              width="62"
              height="15"
              rx="3"
              fill={bessKw > 15 ? 'rgba(245, 158, 11, 0.2)' : bessKw < -15 ? 'rgba(34, 211, 238, 0.2)' : 'rgba(148, 163, 184, 0.2)'}
              stroke={bessKw > 15 ? '#FBBF24' : bessKw < -15 ? '#22D3EE' : '#94A3B8'}
              strokeWidth="0.8"
            />
            <text
              x="561"
              y="313"
              fill={bessKw > 15 ? '#FCD34D' : bessKw < -15 ? '#22D3EE' : '#CBD5E1'}
              fontSize="8"
              fontFamily="monospace"
              fontWeight="700"
              textAnchor="middle"
            >
              {bessMode}
            </text>

            {/* BESS Power & SoC */}
            <text x="420" y="333" fill={sldPalette.textMuted} fontSize="9">
              BESS Power:
            </text>
            <text
              x="490"
              y="333"
              fill={bessKw > 0 ? '#FBBF24' : bessKw < 0 ? '#22D3EE' : '#CBD5E1'}
              fontSize="11"
              fontFamily="monospace"
              fontWeight="700"
            >
              {Math.abs(bessKw).toFixed(0)} kW {bessKw > 0 ? '(Peak Shave)' : bessKw < 0 ? '(Charging)' : ''}
            </text>

            {/* State of Charge Bar */}
            <text x="420" y="352" fill={sldPalette.textMuted} fontSize="9">
              State of Charge:
            </text>
            <text x="500" y="352" fill={sldPalette.textPrimary} fontSize="10" fontFamily="monospace" fontWeight="600">
              {bessSoCPct.toFixed(1)}% ({(bessSoCPct * 20).toFixed(0)} kWh)
            </text>
            <rect x="420" y="358" width="160" height="7" rx="3.5" fill={sldPalette.socTrack} />
            <rect
              x="420"
              y="358"
              width={Math.max(4, Math.min(160, 160 * (bessSoCPct / 100)))}
              height="7"
              rx="3.5"
              fill={bessSoCPct < 20 ? '#F43F5E' : bessSoCPct > 85 ? '#34D399' : '#38BDF8'}
            />

            {/* Health & Safety */}
            <text x="420" y="382" fill={sldPalette.textMuted} fontSize="9">
              Interlocks:
            </text>
            <text x="475" y="382" fill={sldPalette.green} fontSize="9" fontFamily="monospace">
              Voltage/Slew OK (OpenADR 2.0b)
            </text>
          </g>

          {/* ========================================================================= */}
          {/* SECTION 5: COMMERCIAL LOADS & EV FAST-CHARGING PLAZA                      */}
          {/* ========================================================================= */}

          {/* 1. COMMERCIAL RETAIL LOAD NODE (Phoenix, x=150) */}
          <g
            onClick={() => buildingNodes[0] && onSelectNode(buildingNodes[0])}
            onMouseEnter={() => setHoveredNodeId(buildingNodes[0]?.nodeId || 'BLD-1')}
            onMouseLeave={() => setHoveredNodeId(null)}
            style={{ cursor: 'pointer' }}
          >
            <rect
              x="150"
              y="465"
              width="180"
              height="92"
              rx="6"
              fill={selectedNodeId === buildingNodes[0]?.nodeId ? sldPalette.nodeSelectedFill : sldPalette.nodeFill}
              stroke={selectedNodeId === buildingNodes[0]?.nodeId ? '#38BDF8' : sldPalette.nodeStroke}
              strokeWidth={selectedNodeId === buildingNodes[0]?.nodeId ? 2 : 1}
              filter={selectedNodeId === buildingNodes[0]?.nodeId ? 'url(#sld-glow)' : undefined}
            />
            <foreignObject x="162" y="477" width="18" height="18">
              <Building2 size={16} color="#38BDF8" />
            </foreignObject>
            <text x="185" y="488" fill={sldPalette.textPrimary} fontSize="11" fontWeight="700">
              Commercial Retail Zone
            </text>
            <text x="185" y="499" fill={sldPalette.textMuted} fontSize="8" fontFamily="monospace">
              Phoenix Retail & Mall Complex
            </text>

            <text x="165" y="518" fill={sldPalette.textMuted} fontSize="9">
              Active Demand:
            </text>
            <text x="245" y="518" fill={sldPalette.blue} fontSize="11" fontFamily="monospace" fontWeight="700">
              {(microgridSummary?.buildingLoadKw ? microgridSummary.buildingLoadKw * 0.45 : 2450).toFixed(0)} kW
            </text>

            <text x="165" y="534" fill={sldPalette.textMuted} fontSize="9">
              Contract Demand:
            </text>
            <text x="245" y="534" fill={sldPalette.textPrimary} fontSize="10" fontFamily="monospace">
              2,500 kW Limit
            </text>

            <text x="165" y="548" fill={sldPalette.textMuted} fontSize="9">
              Power Factor:
            </text>
            <text x="245" y="548" fill={sldPalette.green} fontSize="9" fontFamily="monospace">
              0.98 Lag
            </text>
          </g>

          {/* 2. COMMERCIAL ENTERPRISE LOAD NODE (Solitaire, x=410) */}
          <g
            onClick={() => buildingNodes[1] && onSelectNode(buildingNodes[1])}
            onMouseEnter={() => setHoveredNodeId(buildingNodes[1]?.nodeId || 'BLD-2')}
            onMouseLeave={() => setHoveredNodeId(null)}
            style={{ cursor: 'pointer' }}
          >
            <rect
              x="410"
              y="465"
              width="180"
              height="92"
              rx="6"
              fill={selectedNodeId === buildingNodes[1]?.nodeId ? sldPalette.nodeSelectedFill : sldPalette.nodeFill}
              stroke={selectedNodeId === buildingNodes[1]?.nodeId ? '#38BDF8' : sldPalette.nodeStroke}
              strokeWidth={selectedNodeId === buildingNodes[1]?.nodeId ? 2 : 1}
              filter={selectedNodeId === buildingNodes[1]?.nodeId ? 'url(#sld-glow)' : undefined}
            />
            <foreignObject x="422" y="477" width="18" height="18">
              <Building2 size={16} color="#38BDF8" />
            </foreignObject>
            <text x="445" y="488" fill={sldPalette.textPrimary} fontSize="11" fontWeight="700">
              Commercial Enterprise
            </text>
            <text x="445" y="499" fill={sldPalette.textMuted} fontSize="8" fontFamily="monospace">
              Solitaire Business Tech Hub
            </text>

            <text x="425" y="518" fill={sldPalette.textMuted} fontSize="9">
              Active Demand:
            </text>
            <text x="505" y="518" fill={sldPalette.blue} fontSize="11" fontFamily="monospace" fontWeight="700">
              {(microgridSummary?.buildingLoadKw ? microgridSummary.buildingLoadKw * 0.35 : 1820).toFixed(0)} kW
            </text>

            <text x="425" y="534" fill={sldPalette.textMuted} fontSize="9">
              Contract Demand:
            </text>
            <text x="505" y="534" fill={sldPalette.textPrimary} fontSize="10" fontFamily="monospace">
              3,000 kW Limit
            </text>

            <text x="425" y="548" fill={sldPalette.textMuted} fontSize="9">
              Power Factor:
            </text>
            <text x="505" y="548" fill={sldPalette.green} fontSize="9" fontFamily="monospace">
              0.99 Lag
            </text>
          </g>

          {/* 3. EV FAST-CHARGING PLAZA NODE (x=620) */}
          <g
            onClick={() => evNode && onSelectNode(evNode)}
            onMouseEnter={() => setHoveredNodeId(evNode?.nodeId || 'EV')}
            onMouseLeave={() => setHoveredNodeId(null)}
            style={{ cursor: 'pointer' }}
          >
            <rect
              x="620"
              y="465"
              width="175"
              height="92"
              rx="6"
              fill={selectedNodeId === evNode?.nodeId ? sldPalette.nodeSelectedFill : sldPalette.nodeFill}
              stroke={selectedNodeId === evNode?.nodeId ? '#E879F9' : sldPalette.nodeStroke}
              strokeWidth={selectedNodeId === evNode?.nodeId ? 2 : 1}
              filter={selectedNodeId === evNode?.nodeId ? 'url(#sld-glow)' : undefined}
            />
            <foreignObject x="632" y="477" width="18" height="18">
              <Car size={16} color="#E879F9" />
            </foreignObject>
            <text x="655" y="488" fill={sldPalette.textPrimary} fontSize="11" fontWeight="700">
              EV DC Fast Plaza
            </text>
            <text x="655" y="499" fill={sldPalette.textMuted} fontSize="8" fontFamily="monospace">
              12 Plugs (60 kW DC Fast)
            </text>

            <text x="635" y="518" fill={sldPalette.textMuted} fontSize="9">
              Charging Load:
            </text>
            <text x="715" y="518" fill="#C084FC" fontSize="11" fontFamily="monospace" fontWeight="700">
              {evLoadKw.toFixed(0)} kW
            </text>

            <text x="635" y="534" fill={sldPalette.textMuted} fontSize="9">
              Active Plugs:
            </text>
            <text x="715" y="534" fill={sldPalette.textPrimary} fontSize="10" fontFamily="monospace">
              {Math.min(12, Math.max(1, Math.round(evLoadKw / 50.0)))} / 12 Vehicles
            </text>

            <text x="635" y="548" fill={sldPalette.textMuted} fontSize="9">
              Protocol:
            </text>
            <text x="715" y="548" fill={sldPalette.blue} fontSize="9" fontFamily="monospace">
              OCPP 2.0.1 Smart
            </text>
          </g>

          {/* 4. COMMERCIAL HOSPITALITY LOAD NODE (Hyatt, x=805) */}
          <g
            onClick={() => buildingNodes[2] && onSelectNode(buildingNodes[2])}
            onMouseEnter={() => setHoveredNodeId(buildingNodes[2]?.nodeId || 'BLD-3')}
            onMouseLeave={() => setHoveredNodeId(null)}
            style={{ cursor: 'pointer' }}
          >
            <rect
              x="805"
              y="465"
              width="170"
              height="92"
              rx="6"
              fill={selectedNodeId === buildingNodes[2]?.nodeId ? sldPalette.nodeSelectedFill : sldPalette.nodeFill}
              stroke={selectedNodeId === buildingNodes[2]?.nodeId ? '#38BDF8' : sldPalette.nodeStroke}
              strokeWidth={selectedNodeId === buildingNodes[2]?.nodeId ? 2 : 1}
              filter={selectedNodeId === buildingNodes[2]?.nodeId ? 'url(#sld-glow)' : undefined}
            />
            <foreignObject x="817" y="477" width="18" height="18">
              <Building2 size={16} color="#38BDF8" />
            </foreignObject>
            <text x="840" y="488" fill={sldPalette.textPrimary} fontSize="11" fontWeight="700">
              Hospitality Zone
            </text>
            <text x="840" y="499" fill={sldPalette.textMuted} fontSize="8" fontFamily="monospace">
              Hyatt Regency Complex
            </text>

            <text x="820" y="518" fill={sldPalette.textMuted} fontSize="9">
              Active Demand:
            </text>
            <text x="900" y="518" fill={sldPalette.blue} fontSize="11" fontFamily="monospace" fontWeight="700">
              {(microgridSummary?.buildingLoadKw ? microgridSummary.buildingLoadKw * 0.20 : 1380).toFixed(0)} kW
            </text>

            <text x="820" y="534" fill={sldPalette.textMuted} fontSize="9">
              Contract Demand:
            </text>
            <text x="900" y="534" fill={sldPalette.textPrimary} fontSize="10" fontFamily="monospace">
              1,600 kW Limit
            </text>

            <text x="820" y="548" fill={sldPalette.textMuted} fontSize="9">
              Power Factor:
            </text>
            <text x="900" y="548" fill={sldPalette.green} fontSize="9" fontFamily="monospace">
              0.97 Lag
            </text>
          </g>
        </svg>
      </div>

      {/* Canvas Bottom Legend & Quick Guidance Strip */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          padding: '10px 18px',
          borderTop: `1px solid ${sldPalette.border}`,
          background: sldPalette.surfaceFooter,
          fontSize: '11px',
          color: sldPalette.textMuted
        }}
      >
        {/* Dynamic Energy Flow Color Legend */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontWeight: 600, color: sldPalette.textSecondary }}>
            <Activity size={13} color={sldPalette.blue} />
            <span>Dynamic Flow Vectors:</span>
          </span>

          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#818CF8' }} />
            <span>Grid Import</span>
          </span>

          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#34D399' }} />
            <span>Solar Generation</span>
          </span>

          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#FBBF24' }} />
            <span>BESS Discharge</span>
          </span>

          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#22D3EE' }} />
            <span>BESS Charge</span>
          </span>

          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#38BDF8' }} />
            <span>Commercial Load</span>
          </span>

          <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#C084FC' }} />
            <span>EV Fast Charging</span>
          </span>
        </div>

        {/* Hover Inspection Callout */}
        {hoveredNodeId && (
          <div style={{ color: '#38BDF8', fontSize: '11px', fontFamily: 'monospace' }}>
            Inspecting: {hoveredNodeId} (Click node to lock telemetry)
          </div>
        )}

        {/* Feeder Thermal Loading Scale */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontWeight: 600, color: '#E2E8F0' }}>
            <Flame size={13} color="#F59E0B" />
            <span>Feeder Ampacity:</span>
          </span>

          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '2px', backgroundColor: '#10B981' }} />
            <span>&lt; 70% Nominal</span>
          </span>

          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '2px', backgroundColor: '#F59E0B' }} />
            <span>70-85% Warning</span>
          </span>

          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '2px', backgroundColor: '#F43F5E' }} />
            <span>&ge; 85% Overload</span>
          </span>
        </div>
      </div>
    </div>
  );
};
