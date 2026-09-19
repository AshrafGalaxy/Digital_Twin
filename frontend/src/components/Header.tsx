import React from 'react';
import { Activity, Radio, ShieldCheck } from 'lucide-react';
import { SourceMode } from '../types/twin';

interface HeaderProps {
  wsConnected: boolean;
  currentMode: SourceMode;
  lastUpdated: string | null;
  onOpenScenarios?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ wsConnected, currentMode, lastUpdated, onOpenScenarios }) => {
  return (
    <header className="app-header">
      <div className="brand-section">
        <Activity size={22} color="#0F4C5C" />
        <span className="brand-title">Digital Twin</span>
        <span className="brand-subtitle">Viman Nagar ↔ Somnath Nagar Corridor (Pune)</span>
      </div>

      <div className="status-section">
        {/* Scenario Studio Launcher */}
        {onOpenScenarios && (
          <button
            className="header-scenario-btn"
            onClick={onOpenScenarios}
            title="Open Microscopic Traffic Simulation Studio"
          >
            <span>Scenario Studio</span>
          </button>
        )}

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
          <span style={{ color: '#10B981' }}>Advisory Mode</span>
        </div>
      </div>
    </header>
  );
};
