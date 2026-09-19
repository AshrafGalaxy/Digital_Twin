import React from 'react';
import {
  Activity,
  Radio,
  ShieldCheck,
  Map,
  Car,
  Zap,
  CloudSun,
  Sliders,
  ShieldAlert,
  Server
} from 'lucide-react';
import { SourceMode } from '../types/twin';

export type TabId =
  | 'operations'
  | 'traffic'
  | 'energy'
  | 'environment'
  | 'scenarios'
  | 'recommendations'
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
    { id: 'operations', label: 'Operations', icon: <Map size={15} /> },
    { id: 'traffic', label: 'Traffic Analytics', icon: <Car size={15} /> },
    { id: 'energy', label: 'Energy Analytics', icon: <Zap size={15} /> },
    { id: 'environment', label: 'Environment Context', icon: <CloudSun size={15} /> },
    { id: 'scenarios', label: 'Scenario Studio', icon: <Sliders size={15} /> },
    {
      id: 'recommendations',
      label: 'Recommendations',
      icon: <ShieldAlert size={15} />,
      badge: activeAdvisoriesCount
    },
    { id: 'health', label: 'System & Data Health', icon: <Server size={15} /> }
  ];

  return (
    <header className="app-header">
      {/* Top Strip: Brand + Global Telemetry / Governance Badges */}
      <div className="header-top-row">
        <div className="brand-section">
          <Activity size={22} color="#0F4C5C" />
          <span className="brand-title">Digital Twin</span>
          <span className="brand-subtitle">Viman Nagar ↔ Somnath Nagar Corridor (Pune)</span>
        </div>

        <div className="status-section">
          {/* Stream / WebSocket Health */}
          <div className="status-pill">
            <span className={`dot ${wsConnected ? 'dot-live' : 'dot-stale'}`} />
            <span>{wsConnected ? 'Stream Active' : 'Connecting...'}</span>
          </div>

          {/* Source Mode Provenance Badge */}
          <div className="status-pill">
            <Radio size={14} className="text-muted" />
            <span className="text-muted">Source:</span>
            <span className={`provenance-badge badge-${currentMode.toLowerCase()}`}>
              {currentMode}
            </span>
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
            <ShieldCheck size={14} color="#10B981" />
            <span style={{ color: '#10B981', fontWeight: 600 }}>Advisory Only</span>
          </div>
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

