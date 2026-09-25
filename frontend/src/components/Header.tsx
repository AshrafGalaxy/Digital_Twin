import React from 'react';
import {
  ShieldCheck,
  Map,
  Car,
  Zap,
  CloudSun,
  Sliders,
  ShieldAlert,
  Server,
  User,
  FileText,
  LogOut
} from 'lucide-react';
import { SourceMode, MunicipalRole, AuthUser } from '../types/twin';
import { ProvenanceBadge } from './ProvenanceBadge';
import { DigitalTwinLogo } from './common/DigitalTwinLogo';

export type TabId =
  | 'landing'
  | 'auth'
  | 'operations'
  | 'traffic'
  | 'energy'
  | 'environment'
  | 'scenarios'
  | 'recommendations'
  | 'evaluation'
  | 'health';

export const ROLE_ALLOWED_TABS: Record<MunicipalRole, TabId[]> = {
  'Traffic Systems Engineer': ['landing', 'auth', 'operations', 'traffic', 'scenarios', 'recommendations'],
  'Energy Grid Manager': ['landing', 'auth', 'operations', 'energy', 'environment', 'recommendations'],
  'Executive Auditor': ['landing', 'auth', 'recommendations', 'evaluation', 'health'],
  'Municipal Analyst': [
    'landing',
    'auth',
    'operations',
    'traffic',
    'energy',
    'environment',
    'scenarios',
    'recommendations',
    'evaluation',
    'health'
  ]
};

interface HeaderProps {
  wsConnected: boolean;
  currentMode: SourceMode;
  lastUpdated: string | null;
  activeTab: TabId;
  onSelectTab: (tab: TabId) => void;
  activeAdvisoriesCount?: number;
  userRole?: MunicipalRole;
  authUser?: AuthUser | null;
  onSignOut?: () => void;
  onOpenAuthModal?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  wsConnected,
  currentMode,
  lastUpdated,
  activeTab,
  onSelectTab,
  activeAdvisoriesCount,
  userRole = 'Municipal Analyst',
  authUser,
  onSignOut
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

  // Filter tabs dynamically based on authenticated municipal role
  const allowed = ROLE_ALLOWED_TABS[userRole] || ROLE_ALLOWED_TABS['Municipal Analyst'];
  const visibleTabs = navTabs.filter((tab) => allowed.includes(tab.id));

  return (
    <header className="app-header">
      {/* Top Strip: Brand + Global Telemetry / Governance Badges */}
      <div className="header-top-row">
        <div className="brand-section">
          <div
            className="brand-clickable"
            onClick={() => onSelectTab('landing')}
            title="Return to Platform Overview & Landing Page"
            role="button"
            tabIndex={0}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
          >
            <DigitalTwinLogo size={22} glow />
            <span className="brand-title">Digital Twin</span>
          </div>
          <span className="brand-subtitle">Dual Arterial Corridor Decision Support</span>
          <button
            className="brand-overview-btn"
            onClick={() => onSelectTab('landing')}
            title="Platform Overview & Architecture"
            style={{
              background: 'rgba(47, 129, 247, 0.12)',
              border: '1px solid rgba(47, 129, 247, 0.35)',
              color: 'var(--color-primary-hover)',
              padding: '2px 8px',
              borderRadius: '9999px',
              fontSize: '11px',
              fontWeight: 500,
              cursor: 'pointer',
              marginLeft: '4px'
            }}
          >
            Overview
          </button>
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

          {/* Authenticated Municipal Officer Profile Badge with Sign Out */}
          {authUser ? (
            <div
              className="status-pill user-profile-chip"
              title={`Authenticated Officer: ${authUser.name} (${userRole})`}
            >
              <span
                className="role-badge-dot"
                style={{
                  width: '7px',
                  height: '7px',
                  borderRadius: '50%',
                  flexShrink: 0,
                  backgroundColor:
                    userRole === 'Traffic Systems Engineer' ? '#F59E0B' :
                    userRole === 'Energy Grid Manager' ? '#10B981' :
                    userRole === 'Executive Auditor' ? '#38BDF8' : '#2F81F7',
                  boxShadow: `0 0 6px ${
                    userRole === 'Traffic Systems Engineer' ? '#F59E0B' :
                    userRole === 'Energy Grid Manager' ? '#10B981' :
                    userRole === 'Executive Auditor' ? '#38BDF8' : '#2F81F7'
                  }`
                }}
              />
              <User size={12} color="var(--color-primary-hover)" style={{ flexShrink: 0 }} />
              <span className="user-profile-title" style={{ fontWeight: 600, fontSize: '11.5px', color: '#F0F6FC' }}>
                {authUser.name && authUser.name !== userRole ? `${authUser.name} • ${userRole}` : (authUser.role || userRole)}
              </span>
              {onSignOut && (
                <button
                  type="button"
                  className="header-signout-btn"
                  onClick={onSignOut}
                  title="Sign out of municipal session"
                >
                  <LogOut size={11} />
                  <span>Sign Out</span>
                </button>
              )}
            </div>
          ) : (
            <button
              type="button"
              className="status-pill header-signin-btn"
              onClick={() => onSelectTab('auth')}
              title="Sign in with authorized municipal credentials"
              style={{ cursor: 'pointer', background: 'rgba(56, 139, 253, 0.15)', borderColor: 'rgba(56, 139, 253, 0.4)', color: '#58A6FF' }}
            >
              <User size={12} color="#58A6FF" />
              <span style={{ fontWeight: 600, fontSize: '11.5px' }}>Officer Sign In</span>
            </button>
          )}

          {/* Source Mode Provenance Pill */}
          <div
            className="status-pill status-pill-source"
            title={`Authoritative corridor telemetry provenance mode: ${currentMode}`}
          >
            <span className="text-muted" style={{ fontSize: '11px' }}>Source:</span>
            <ProvenanceBadge mode={currentMode} className="header-provenance-clean" />
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

      {/* Primary Navigation Bar: Standard Views filtered by Role */}
      <nav className="header-nav-tabs" aria-label="Primary Platform Views">
        {visibleTabs.map((tab) => (
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

