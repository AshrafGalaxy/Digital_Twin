import React, { useState } from 'react';
import {
  Zap,
  GitFork,
  Sun,
  BatteryCharging,
  Building2,
  Car,
  ChevronDown,
  ChevronRight,
  Activity,
  Layers
} from 'lucide-react';
import { EnergyNodeAsset, EnergyNodeType, EnergyTopologyTreeResponse } from '../../types/twin';

interface ElectricalTopologyTreeProps {
  topology: EnergyTopologyTreeResponse | null;
  selectedNodeId: string | null;
  onSelectNode: (node: EnergyNodeAsset) => void;
  isLoading?: boolean;
}

const getNodeIcon = (type: EnergyNodeType) => {
  switch (type) {
    case 'SUBSTATION':
      return <Zap className="w-4 h-4 text-amber-400" />;
    case 'FEEDER':
      return <GitFork className="w-4 h-4 text-cyan-400" />;
    case 'SOLAR_PV':
      return <Sun className="w-4 h-4 text-emerald-400" />;
    case 'BESS':
      return <BatteryCharging className="w-4 h-4 text-indigo-400" />;
    case 'BUILDING_LOAD':
      return <Building2 className="w-4 h-4 text-blue-400" />;
    case 'EV_HUB':
      return <Car className="w-4 h-4 text-purple-400" />;
    default:
      return <Layers className="w-4 h-4 text-slate-400" />;
  }
};

const getNodeTypeBadge = (type: EnergyNodeType) => {
  const styles: Record<EnergyNodeType, string> = {
    SUBSTATION: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
    FEEDER: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30',
    SOLAR_PV: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
    BESS: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30',
    BUILDING_LOAD: 'bg-blue-500/10 text-blue-300 border-blue-500/30',
    EV_HUB: 'bg-purple-500/10 text-purple-300 border-purple-500/30'
  };
  const labels: Record<EnergyNodeType, string> = {
    SUBSTATION: 'Substation',
    FEEDER: '11kV Feeder',
    SOLAR_PV: 'Solar PV',
    BESS: 'BESS',
    BUILDING_LOAD: 'Facility Load',
    EV_HUB: 'EV Plaza'
  };

  return (
    <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border ${styles[type] || 'bg-slate-500/10 text-slate-300 border-slate-500/30'}`}>
      {labels[type] || type}
    </span>
  );
};

interface TreeNodeItemProps {
  node: EnergyNodeAsset;
  level: number;
  selectedNodeId: string | null;
  onSelectNode: (node: EnergyNodeAsset) => void;
}

const TreeNodeItem: React.FC<TreeNodeItemProps> = ({
  node,
  level,
  selectedNodeId,
  onSelectNode
}) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedNodeId === node.nodeId;

  const loadingPct = node.loadingPct || 0;
  const loadingColor =
    loadingPct > 80
      ? 'bg-rose-500'
      : loadingPct > 60
      ? 'bg-amber-500'
      : 'bg-emerald-500';

  const activeKw = node.telemetry?.activePowerKw || 0;
  const isGeneration = node.nodeType === 'SOLAR_PV' || (node.nodeType === 'BESS' && activeKw > 0);

  return (
    <div className="flex flex-col">
      <div
        onClick={() => onSelectNode(node)}
        className={`group flex items-center justify-between p-2.5 rounded-lg border transition-all cursor-pointer select-none mb-1.5 ${
          isSelected
            ? 'bg-cyan-950/40 border-cyan-500/60 shadow-sm shadow-cyan-500/10'
            : 'bg-slate-900/60 hover:bg-slate-800/80 border-slate-800 hover:border-slate-700'
        }`}
        style={{ marginLeft: `${level * 16}px` }}
      >
        <div className="flex items-center gap-2 min-w-0 flex-1">
          {hasChildren ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsExpanded(!isExpanded);
              }}
              className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-slate-200 transition-colors"
              title={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? (
                <ChevronDown className="w-3.5 h-3.5" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5" />
              )}
            </button>
          ) : (
            <div className="w-5" />
          )}

          <div className="p-1.5 rounded-md bg-slate-950/80 border border-slate-800 flex-shrink-0">
            {getNodeIcon(node.nodeType)}
          </div>

          <div className="min-w-0 flex-1 pr-2">
            <div className="flex items-center gap-2">
              <span className={`text-xs font-semibold truncate ${isSelected ? 'text-cyan-200' : 'text-slate-200'}`}>
                {node.name}
              </span>
              {getNodeTypeBadge(node.nodeType)}
            </div>
            <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono mt-0.5">
              <span>{node.nominalVoltageKv} kV</span>
              <span>•</span>
              <span>{node.ratedCapacityKva.toLocaleString()} kVA</span>
              {node.nodeType === 'FEEDER' && (
                <>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Activity className="w-3 h-3 text-cyan-400" />
                    Load: {loadingPct.toFixed(1)}%
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-col items-end gap-1 flex-shrink-0">
          <span
            className={`text-xs font-mono font-medium ${
              isGeneration
                ? 'text-emerald-400'
                : activeKw < 0
                ? 'text-indigo-400'
                : 'text-amber-400'
            }`}
          >
            {activeKw > 0 && !isGeneration ? '+' : ''}
            {activeKw.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} kW
          </span>

          {node.nodeType === 'FEEDER' && (
            <div className="w-20 bg-slate-800 h-1.5 rounded-full overflow-hidden border border-slate-700/50">
              <div
                className={`h-full transition-all duration-500 ${loadingColor}`}
                style={{ width: `${Math.min(100, Math.max(2, loadingPct))}%` }}
              />
            </div>
          )}
        </div>
      </div>

      {hasChildren && isExpanded && (
        <div className="flex flex-col">
          {node.children!.map((child) => (
            <TreeNodeItem
              key={child.nodeId}
              node={child}
              level={level + 1}
              selectedNodeId={selectedNodeId}
              onSelectNode={onSelectNode}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const ElectricalTopologyTree: React.FC<ElectricalTopologyTreeProps> = ({
  topology,
  selectedNodeId,
  onSelectNode,
  isLoading = false
}) => {
  if (isLoading && !topology) {
    return (
      <div className="p-8 flex flex-col items-center justify-center text-center space-y-3 bg-slate-900/40 rounded-xl border border-slate-800">
        <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs text-slate-400">Loading electrical network topology...</span>
      </div>
    );
  }

  if (!topology || !topology.substation) {
    return (
      <div className="p-6 text-center text-xs text-slate-400 bg-slate-900/40 rounded-xl border border-slate-800">
        No electrical distribution topology available.
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 backdrop-blur-md rounded-xl border border-slate-800 p-4 flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
            Electrical Single-Line Hierarchy
          </h3>
        </div>
        <span className="text-[11px] font-mono text-slate-400">
          {topology.totalNodes} Monitored Assets
        </span>
      </div>

      <div className="flex-1 overflow-y-auto pr-1">
        <TreeNodeItem
          node={topology.substation}
          level={0}
          selectedNodeId={selectedNodeId}
          onSelectNode={onSelectNode}
        />
      </div>

      <div className="pt-3 border-t border-slate-800/80 mt-2 flex items-center justify-between text-[11px] text-slate-400">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500" /> &lt;60% Normal
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-500" /> 60-80% Elevated
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500" /> &gt;80% Critical
          </span>
        </div>
      </div>
    </div>
  );
};
