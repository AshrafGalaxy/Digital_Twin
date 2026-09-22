import React from 'react';
import {
  Activity,
  ShieldCheck,
  Map,
  Car,
  Zap,
  CloudSun,
  Sliders,
  ShieldAlert,
  Server,
  User,
  FileText
} from 'lucide-react';
import { SourceMode } from '../types/twin';
import { ProvenanceBadge } from './ProvenanceBadge';

export type TabId =
  | 'operations'
  | 'traffic'
  | 'energy'
  | 'environment'
  | 'scenarios'
  | 'recommendations'
  | 'evaluation'
  | 'health';

interface HeaderProps {
  wsConnected: boolean;
  currentMode: SourceMode;
  lastUpdated: string | null;
  activeTab: TabId;
  onSelectTab: (tab: TabId) => void;
  activeAdvisoriesCount?: number;
}

export const Header: React.FC<HeaderProps> = ({
  wsConnected,
  currentMode,
  lastUpdated,
  activeTab,
  onSelectTab,
  activeAdvisoriesCount
}) => {
  const navTabs: { id: TabId; label: string; icon: React.ReactNode; badge?: number }[] = [
    { id: 'operations', label: 'Operations', icon: <Map size={14} /> },
    { id: 'traffic', label: 'Traffic Analytics', icon: <Car size={14} /> },
    { id: 'energy', label: 'Energy Analytics', icon: <Zap size={14} /> },
    { id: 'environment', label: 'Environment Context', icon: <CloudSun size={14} /> },
    { id: 'scenarios', label: 'Scenario Studio', icon: <Sliders size={14} /> },
    {
      id: 'recommendations',
      label: 'Recommendations',
      icon: <ShieldAlert size={14} />,
      badge: activeAdvisoriesCount
    },
    { id: 'evaluation', label: 'Evaluation & Reports', icon: <FileText size={14} /> },
    { id: 'health', label: 'System & Data Health', icon: <Server size={14} /> }
  ];

  return (
    <header className="app-header">
      {/* Top Strip: Brand + Global Telemetry / Governance Badges + Theme Switcher (UI_UX_SPEC §6.1) */}
      <div className="header-top-row">
        <div className="brand-section">
          <Activity size={20} color="var(--color-primary)" style={{ filter: 'drop-shadow(0 0 8px rgba(47, 129, 247, 0.6))' }} />
          <span className="brand-title">Digital Twin</span>
          <span className="brand-subtitle">Viman Nagar ↔ Somnath Nagar Corridor (Pune)</span>
        </div>

        <div className="status-section">
          {/* Stream / WebSocket Health */}
          <div className="status-pill">
            <span
              className={`dot ${wsConnected ? 'dot-live' : 'dot-stale'}`}
              style={{ boxShadow: wsConnected ? '0 0 8px #10B981' : '0 0 8px #F59E0B' }}
            />
            <span>{wsConnected ? 'Stream Active' : 'Connecting...'}</span>
          </div>

          {/* User Role Indicator (UI_UX_SPEC §6.1) */}
          <div className="status-pill" title="Current session authorization role">
            <User size={12} color="var(--text-muted)" />
            <span className="text-muted">Role:</span>
            <span style={{ fontWeight: 600 }}>Municipal Analyst</span>
          </div>

          {/* Source Mode Provenance Badge */}
          <div className="status-pill">
            <span className="text-muted">Source:</span>
            <ProvenanceBadge mode={currentMode} />
          </div>

          {/* Freshness Timestamp */}
          <div className="status-pill">
            <span className="text-muted">Updated:</span>
            <span style={{ fontFamily: 'var(--font-mono)' }}>
              {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'Awaiting data'}
            </span>
          </div>

          {/* Human Governance / Advisory Badge */}
          <div className="status-pill" title="Advisory platform: all decisions require human approval">
            <ShieldCheck size={13} color="#10B981" />
            <span style={{ color: '#10B981', fontWeight: 600 }}>Advisory Only</span>
          </div>
        </div>
      </div>

      {/* Global Status Bar per UI_UX_SPEC §6.2 */}
      <div className="global-status-bar" aria-label="Global System and Model Status">
        <div className="status-bar-item">
          <span className="text-muted">Data Freshness:</span>
          <span className="font-mono">
            {lastUpdated ? `Updated ${new Date(lastUpdated).toLocaleTimeString()}` : 'Real-time telemetry stream'}
          </span>
        </div>
        <div className="status-bar-item">
          <span className="text-muted">Source Mode:</span>
          <span style={{ fontWeight: 600 }}>{currentMode} + BENCHMARK</span>
        </div>
        <div className="status-bar-item">
          <span className="text-muted">Traffic Model:</span>
          <code style={{ fontSize: '12px' }}>traffic-xgb-v1 (15m)</code>
        </div>
        <div className="status-bar-item">
          <span className="text-muted">Energy Model:</span>
          <code style={{ fontSize: '12px' }}>energy-xgb-v1 (60m)</code>
        </div>
        <div className="status-bar-item">
          <span className="text-muted">Scenario Service:</span>
          <span style={{ color: '#10B981', fontWeight: 500 }}>SUMO 1.18+ (Available)</span>
        </div>
        <div className="status-bar-item status-bar-governance" style={{ marginLeft: 'auto', color: 'var(--text-muted)' }}>
          <span>Advisory Only • Human Approval Required</span>
        </div>
      </div>

      {/* Primary Navigation Bar: 7 Standard Views per UI_UX_SPEC §5.1 */}
      <nav className="header-nav-tabs" aria-label="Primary Platform Views">
        {navTabs.map((tab) => (
          <button
            key={tab.id}
            className={`nav-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => onSelectTab(tab.id)}
            aria-current={activeTab === tab.id ? 'page' : undefined}
          >
            <span className="nav-tab-icon">{tab.icon}</span>
            <span className="nav-tab-label">{tab.label}</span>
            {tab.badge !== undefined && tab.badge > 0 && (
              <span className="nav-tab-badge">{tab.badge}</span>
            )}
          </button>
        ))}
      </nav>
    </header>
  );
};

