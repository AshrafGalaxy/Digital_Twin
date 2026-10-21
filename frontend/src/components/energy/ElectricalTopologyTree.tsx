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
      return <Zap size={14} color="#FCD34D" />;
    case 'FEEDER':
      return <GitFork size={14} color="#58A6FF" />;
    case 'SOLAR_PV':
      return <Sun size={14} color="#3FB950" />;
    case 'BESS':
      return <BatteryCharging size={14} color="#BC8CFF" />;
    case 'BUILDING_LOAD':
      return <Building2 size={14} color="#38BDF8" />;
    case 'EV_HUB':
      return <Car size={14} color="#E879F9" />;
    default:
      return <Layers size={14} color="var(--color-text-muted)" />;
  }
};

const getNodeTypeBadge = (type: EnergyNodeType) => {
  const badgeColors: Record<EnergyNodeType, { bg: string; border: string; text: string; label: string }> = {
    SUBSTATION: {
      bg: 'rgba(245, 158, 11, 0.14)',
      border: 'rgba(245, 158, 11, 0.35)',
      text: '#FCD34D',
      label: 'Substation'
    },
    FEEDER: {
      bg: 'rgba(47, 129, 247, 0.14)',
      border: 'rgba(47, 129, 247, 0.35)',
      text: '#58A6FF',
      label: '11kV Feeder'
    },
    SOLAR_PV: {
      bg: 'rgba(63, 185, 80, 0.14)',
      border: 'rgba(63, 185, 80, 0.35)',
      text: '#3FB950',
      label: 'Solar PV'
    },
    BESS: {
      bg: 'rgba(188, 140, 255, 0.14)',
      border: 'rgba(188, 140, 255, 0.35)',
      text: '#BC8CFF',
      label: 'BESS'
    },
    BUILDING_LOAD: {
      bg: 'rgba(56, 189, 248, 0.14)',
      border: 'rgba(56, 189, 248, 0.35)',
      text: '#38BDF8',
      label: 'Facility Load'
    },
    EV_HUB: {
      bg: 'rgba(217, 70, 239, 0.14)',
      border: 'rgba(217, 70, 239, 0.35)',
      text: '#E879F9',
      label: 'EV Plaza'
    }
  };

  const style = badgeColors[type] || {
    bg: 'rgba(139, 148, 158, 0.14)',
    border: 'rgba(139, 148, 158, 0.35)',
    text: 'var(--color-text-muted)',
    label: type
  };

  return (
    <span
      style={{
        fontSize: '10px',
        fontFamily: 'var(--font-mono)',
        textTransform: 'uppercase',
        padding: '2px 8px',
        borderRadius: '9999px',
        backgroundColor: style.bg,
        border: `1px solid ${style.border}`,
        color: style.text,
        fontWeight: 600,
        letterSpacing: '0.04em'
      }}
    >
      {style.label}
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
  const hasChildren = Boolean(node.children && node.children.length > 0);
  const isSelected = selectedNodeId === node.nodeId;

  const loadingPct = node.loadingPct || 0;
  const loadingColor =
    loadingPct > 80
      ? 'var(--color-danger, #F85149)'
      : loadingPct > 60
      ? 'var(--color-warning, #D29922)'
      : 'var(--color-success, #3FB950)';

  const activeKw = node.telemetry?.activePowerKw || 0;
  const isGeneration = node.nodeType === 'SOLAR_PV' || (node.nodeType === 'BESS' && activeKw > 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <div
        onClick={() => onSelectNode(node)}
        role="button"
        tabIndex={0}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 12px',
          borderRadius: 'var(--radius-sm, 6px)',
          border: isSelected
            ? '1px solid var(--color-primary, #2F81F7)'
            : '1px solid var(--color-border, #16171B)',
          backgroundColor: isSelected
            ? 'rgba(47, 129, 247, 0.12)'
            : 'var(--bg-surface-elevated, rgba(15, 15, 18, 0.6))',
          boxShadow: isSelected ? '0 0 10px rgba(47, 129, 247, 0.18)' : 'none',
          cursor: 'pointer',
          marginBottom: '6px',
          marginLeft: `${level * 16}px`,
          transition: 'all var(--transition-fast)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0, flex: 1 }}>
          {hasChildren ? (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setIsExpanded(!isExpanded);
              }}
              style={{
                border: 'none',
                background: 'transparent',
                color: 'var(--color-text-muted)',
                cursor: 'pointer',
                padding: '2px',
                display: 'flex',
                alignItems: 'center'
              }}
              title={isExpanded ? 'Collapse branch' : 'Expand branch'}
            >
              {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
          ) : (
            <div style={{ width: '18px' }} />
          )}

          <div
            style={{
              padding: '5px',
              borderRadius: 'var(--radius-sm, 4px)',
              backgroundColor: 'var(--bg-app, #000000)',
              border: '1px solid var(--color-border, #16171B)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}
          >
            {getNodeIcon(node.nodeType)}
          </div>

          <div style={{ minWidth: 0, flex: 1, paddingRight: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: 600,
                  color: isSelected ? 'var(--color-primary-hover, #58A6FF)' : 'var(--color-text, #F0F6FC)',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}
              >
                {node.name}
              </span>
              {getNodeTypeBadge(node.nodeType)}
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '11px',
                color: 'var(--color-text-muted)',
                fontFamily: 'var(--font-mono)',
                marginTop: '2px'
              }}
            >
              <span>{node.nominalVoltageKv} kV</span>
              <span>•</span>
              <span>{node.ratedCapacityKva.toLocaleString()} kVA</span>
              {node.nodeType === 'FEEDER' && (
                <>
                  <span>•</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Activity size={11} color="var(--color-primary)" />
                    Load: {loadingPct.toFixed(1)}%
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px', flexShrink: 0 }}>
          <span
            className="font-mono"
            style={{
              fontSize: '12px',
              fontWeight: 600,
              color: isGeneration
                ? 'var(--color-success, #3FB950)'
                : activeKw < 0
                ? '#818CF8'
                : 'var(--color-warning, #D29922)'
            }}
          >
            {activeKw > 0 && !isGeneration ? '+' : ''}
            {activeKw.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} kW
          </span>

          {node.nodeType === 'FEEDER' && (
            <div className="progress-bar-bg" style={{ width: '70px', height: '5px' }}>
              <div
                className="progress-bar-fill"
                style={{
                  width: `${Math.min(100, Math.max(2, loadingPct))}%`,
                  backgroundColor: loadingColor
                }}
              />
            </div>
          )}
        </div>
      </div>

      {hasChildren && isExpanded && (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
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
      <div className="analytics-card" style={{ padding: '40px', textAlign: 'center', height: '100%', justifyContent: 'center' }}>
        <Activity size={24} className="animate-spin text-muted" style={{ margin: '0 auto 10px' }} />
        <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
          Loading electrical network topology...
        </span>
      </div>
    );
  }

  if (!topology || !topology.substation) {
    return (
      <div className="analytics-card" style={{ padding: '30px', textAlign: 'center', height: '100%', justifyContent: 'center' }}>
        <Zap size={24} className="text-muted" style={{ margin: '0 auto 10px' }} />
        <p style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
          No electrical distribution topology available.
        </p>
      </div>
    );
  }

  return (
    <div className="analytics-card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="analytics-card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={16} color="var(--color-primary, #2F81F7)" />
          <span className="card-title">Electrical Single-Line Hierarchy</span>
        </div>
        <span className="analytics-meta-pill" style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', padding: '2px 8px' }}>
          {topology.totalNodes} Monitored Assets
        </span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }}>
        <TreeNodeItem
          node={topology.substation}
          level={0}
          selectedNodeId={selectedNodeId}
          onSelectNode={onSelectNode}
        />
      </div>

      <div
        style={{
          paddingTop: '10px',
          borderTop: '1px solid var(--color-border, #16171B)',
          marginTop: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '11px',
          color: 'var(--color-text-muted)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-success, #3FB950)' }} />
            &lt;60% Normal
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-warning, #D29922)' }} />
            60-80% Elevated
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-danger, #F85149)' }} />
            &gt;80% Critical
          </span>
        </div>
      </div>
    </div>
  );
};
