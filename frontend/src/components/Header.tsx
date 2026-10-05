import React, { useState, useRef, useEffect } from 'react';
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
  LogOut,
  LogIn,
  Settings,
  ChevronDown,
  Sparkles,
  Compass,
  KeyRound
} from 'lucide-react';
import { SourceMode, MunicipalRole, AuthUser } from '../types/twin';
import { ProvenanceBadge } from './ProvenanceBadge';
import { DigitalTwinLogo } from './common/DigitalTwinLogo';
import { SettingsModal } from './SettingsModal';

export type TabId =
  | 'landing'
  | 'provisioning'
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
  'Traffic Systems Engineer': ['landing', 'provisioning', 'auth', 'operations', 'traffic', 'scenarios', 'recommendations'],
  'Energy Grid Manager': ['landing', 'provisioning', 'auth', 'operations', 'energy', 'environment', 'recommendations'],
  'Executive Auditor': ['landing', 'provisioning', 'auth', 'recommendations', 'evaluation', 'health'],
  'Municipal Analyst': [
    'landing',
    'provisioning',
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
  const [isProfileOpen, setIsProfileOpen] = useState<boolean>(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
  const profileDropdownRef = useRef<HTMLDivElement>(null);

  // Close profile dropdown on outside click or Escape key
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        profileDropdownRef.current &&
        !profileDropdownRef.current.contains(event.target as Node)
      ) {
        setIsProfileOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsProfileOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

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

  // Determine role accent color
  const roleColor =
    userRole === 'Traffic Systems Engineer'
      ? '#F59E0B'
      : userRole === 'Energy Grid Manager'
      ? '#10B981'
      : userRole === 'Executive Auditor'
      ? '#38BDF8'
      : '#2F81F7';

  return (
    <>
      <header className="app-header">
        {/* Top Strip: Brand + Global Telemetry Badges + Corner Profile Menu */}
        <div className="header-top-row">
          {/* Brand Identity: strictly Digital Twin, no dual arterial corridor line */}
          <div className="brand-section">
            <div
              className="brand-clickable"
              onClick={() => onSelectTab('landing')}
              title="Return to Platform Overview & Landing Page"
              role="button"
              tabIndex={0}
              style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
            >
              <DigitalTwinLogo size={22} />
              <span className="brand-title">Digital Twin</span>
            </div>
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

          {/* Right Group: Telemetry Status Section + Corner Profile Dropdown */}
          <div className="header-right-group">
            {/* Status Section: Strictly telemetry signals (no officer chip in between) */}
            <div className="status-section">
              {/* Stream / WebSocket Health */}
              <div className="status-pill">
                <span
                  className={`dot ${wsConnected ? 'dot-live' : 'dot-stale'}`}
                  style={{ boxShadow: wsConnected ? '0 0 8px #10B981' : '0 0 8px #F59E0B' }}
                />
                <span>{wsConnected ? 'Stream Active' : 'Connecting...'}</span>
              </div>

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

            <div className="header-actions-divider" />

            {/* Corner Profile Menu Button & Dropdown */}
            <div className="corner-profile-container" ref={profileDropdownRef}>
              <button
                type="button"
                className={`corner-profile-btn ${isProfileOpen ? 'open' : ''} ${authUser ? 'authenticated' : 'guest'}`}
                onClick={() => setIsProfileOpen((prev) => !prev)}
                aria-haspopup="true"
                aria-expanded={isProfileOpen}
                title={authUser ? `Officer Profile: ${authUser.name} (${userRole})` : 'Officer Profile & Navigation'}
              >
                <div className="corner-avatar-gem">
                  <User size={13} color={authUser ? '#F0F6FC' : '#8B949E'} />
                  <span
                    className="corner-role-dot"
                    style={{
                      backgroundColor: roleColor,
                      boxShadow: `0 0 5px ${roleColor}`
                    }}
                  />
                </div>
                <div className="corner-profile-meta">
                  <span className="corner-profile-name">
                    {authUser?.name ? authUser.name.split(' ')[0] : 'Sign In'}
                  </span>
                  <span className="corner-profile-role">
                    {userRole.split(' ')[0]}
                  </span>
                </div>
                <ChevronDown size={12} className={`corner-chevron ${isProfileOpen ? 'rotated' : ''}`} />
              </button>

              {/* Popover Dropdown Menu */}
              {isProfileOpen && (
                <div className="corner-profile-dropdown" role="menu">
                  {/* Dropdown Header Card */}
                  <div className="dropdown-user-header">
                    <div
                      className="dropdown-avatar-circle"
                      style={{ borderColor: roleColor }}
                    >
                      <User size={18} color={roleColor} />
                    </div>
                    <div className="dropdown-user-details">
                      <span className="dropdown-user-name">
                        {authUser?.name || 'Municipal Officer Session'}
                      </span>
                      <span
                        className="dropdown-user-role-badge"
                        style={{
                          backgroundColor: `${roleColor}1A`,
                          borderColor: `${roleColor}4D`,
                          color: roleColor
                        }}
                      >
                        {userRole}
                      </span>
                      <span className="dropdown-session-status">
                        <span
                          className="dropdown-status-dot"
                          style={{
                            backgroundColor: authUser ? '#10B981' : '#F59E0B'
                          }}
                        />
                        {authUser ? 'Verified Authorization' : 'Guest Analyst Session'}
                      </span>
                    </div>
                  </div>

                  <div className="dropdown-divider" />

                  {/* Primary Account Action: Officer Sign In or Switch Role */}
                  <div className="dropdown-section">
                    <button
                      type="button"
                      className="dropdown-menu-item"
                      onClick={() => {
                        setIsProfileOpen(false);
                        onSelectTab('auth');
                      }}
                      role="menuitem"
                    >
                      {authUser ? (
                        <>
                          <KeyRound size={14} className="dropdown-item-icon" />
                          <div className="dropdown-item-text">
                            <span className="dropdown-item-title">Switch Role or Account</span>
                            <span className="dropdown-item-desc">Change authorized municipal role</span>
                          </div>
                        </>
                      ) : (
                        <>
                          <LogIn size={14} className="dropdown-item-icon text-primary" />
                          <div className="dropdown-item-text">
                            <span className="dropdown-item-title text-primary">Officer Sign In</span>
                            <span className="dropdown-item-desc">Authenticate with municipal credentials</span>
                          </div>
                        </>
                      )}
                    </button>
                  </div>

                  <div className="dropdown-divider" />

                  {/* Core Workspace & Platform Tools */}
                  <div className="dropdown-section">
                    <span className="dropdown-section-label">WORKSPACE & TOOLS</span>

                    <button
                      type="button"
                      className="dropdown-menu-item"
                      onClick={() => {
                        setIsProfileOpen(false);
                        setIsSettingsOpen(true);
                      }}
                      role="menuitem"
                    >
                      <Settings size={14} className="dropdown-item-icon" />
                      <div className="dropdown-item-text">
                        <span className="dropdown-item-title">Settings & Preferences</span>
                        <span className="dropdown-item-desc">Telemetry cadence, units, and alerts</span>
                      </div>
                    </button>

                    <button
                      type="button"
                      className="dropdown-menu-item"
                      onClick={() => {
                        setIsProfileOpen(false);
                        onSelectTab('provisioning');
                      }}
                      role="menuitem"
                    >
                      <Sparkles size={14} className="dropdown-item-icon" />
                      <div className="dropdown-item-text">
                        <span className="dropdown-item-title">Digital Twin Intake Portal</span>
                        <span className="dropdown-item-desc">Provision new corridor assets</span>
                      </div>
                    </button>

                    <button
                      type="button"
                      className="dropdown-menu-item"
                      onClick={() => {
                        setIsProfileOpen(false);
                        onSelectTab('health');
                      }}
                      role="menuitem"
                    >
                      <Server size={14} className="dropdown-item-icon" />
                      <div className="dropdown-item-text">
                        <span className="dropdown-item-title">System Health & Telemetry</span>
                        <span className="dropdown-item-desc">Data ingestion, feeds, and audits</span>
                      </div>
                    </button>

                    <button
                      type="button"
                      className="dropdown-menu-item"
                      onClick={() => {
                        setIsProfileOpen(false);
                        onSelectTab('evaluation');
                      }}
                      role="menuitem"
                    >
                      <FileText size={14} className="dropdown-item-icon" />
                      <div className="dropdown-item-text">
                        <span className="dropdown-item-title">Evaluation & Reports</span>
                        <span className="dropdown-item-desc">Corridor pilot verification</span>
                      </div>
                    </button>

                    <button
                      type="button"
                      className="dropdown-menu-item"
                      onClick={() => {
                        setIsProfileOpen(false);
                        onSelectTab('landing');
                      }}
                      role="menuitem"
                    >
                      <Compass size={14} className="dropdown-item-icon" />
                      <div className="dropdown-item-text">
                        <span className="dropdown-item-title">Platform Architecture Overview</span>
                        <span className="dropdown-item-desc">Return to system landing view</span>
                      </div>
                    </button>
                  </div>

                  {/* Sign Out (if authenticated) */}
                  {authUser && onSignOut && (
                    <>
                      <div className="dropdown-divider" />
                      <div className="dropdown-section">
                        <button
                          type="button"
                          className="dropdown-menu-item dropdown-signout-item"
                          onClick={() => {
                            setIsProfileOpen(false);
                            onSignOut();
                          }}
                          role="menuitem"
                        >
                          <LogOut size={14} className="dropdown-item-icon" />
                          <div className="dropdown-item-text">
                            <span className="dropdown-item-title">Sign Out of Session</span>
                            <span className="dropdown-item-desc">Revoke session authorization</span>
                          </div>
                        </button>
                      </div>
                    </>
                  )}
                </div>
              )}
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

      {/* Global Settings & Preferences Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </>
  );
};
