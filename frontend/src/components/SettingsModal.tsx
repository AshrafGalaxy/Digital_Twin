import React, { useState, useEffect } from 'react';
import {
  X,
  Settings,
  Bell,
  Gauge,
  Activity,
  Check,
  RotateCcw,
  ShieldCheck,
  Sun,
  Moon
} from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export interface PlatformPreferences {
  theme: 'dark' | 'light';
  telemetryIntervalSeconds: number;
  enableAlertChimes: boolean;
  speedUnit: 'kmh' | 'mph';
  highContrastMap: boolean;
  strictProvenancePills: boolean;
}

export const DEFAULT_PREFERENCES: PlatformPreferences = {
  theme: 'dark',
  telemetryIntervalSeconds: 2,
  enableAlertChimes: true,
  speedUnit: 'kmh',
  highContrastMap: false,
  strictProvenancePills: true
};

export const STORAGE_KEY = 'digital_twin_platform_preferences';

export const applyTheme = (theme: 'dark' | 'light') => {
  document.documentElement.setAttribute('data-theme', theme);
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    const parsed = saved ? JSON.parse(saved) : DEFAULT_PREFERENCES;
    parsed.theme = theme;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(parsed));
  } catch {
    // Fallback ignore
  }
  window.dispatchEvent(new CustomEvent('platform-theme-change', { detail: { theme } }));
};

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [preferences, setPreferences] = useState<PlatformPreferences>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return { ...DEFAULT_PREFERENCES, ...JSON.parse(saved) };
      }
    } catch {
      // Fallback to default
    }
    return DEFAULT_PREFERENCES;
  });

  const [savedFeedback, setSavedFeedback] = useState<boolean>(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSave = () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
    applyTheme(preferences.theme);
    setSavedFeedback(true);
    setTimeout(() => {
      setSavedFeedback(false);
      onClose();
    }, 600);
  };

  const handleReset = () => {
    setPreferences(DEFAULT_PREFERENCES);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_PREFERENCES));
    applyTheme(DEFAULT_PREFERENCES.theme);
  };

  return (
    <div
      className="settings-modal-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="settings-modal-title"
    >
      <div className="settings-modal-card">
        {/* Header */}
        <div className="settings-modal-header">
          <div className="settings-header-title-group">
            <div className="settings-icon-badge">
              <Settings size={18} color="#58A6FF" />
            </div>
            <div>
              <h2 id="settings-modal-title" className="settings-title">
                Platform Preferences & Controls
              </h2>
              <p className="settings-description">
                Configure municipal telemetry rates, visualization thresholds, and alerts.
              </p>
            </div>
          </div>
          <button
            type="button"
            className="settings-close-btn"
            onClick={onClose}
            aria-label="Close settings"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="settings-modal-body">
          {/* Section 0: Theme & Cartographic Appearance */}
          <div className="settings-section">
            <div className="settings-section-header">
              {preferences.theme === 'light' ? (
                <Sun size={15} color="#F59E0B" />
              ) : (
                <Moon size={15} color="#58A6FF" />
              )}
              <span>Theme & Cartographic Appearance</span>
            </div>
            <div className="settings-control-row">
              <div className="settings-control-info">
                <label className="settings-control-label">Workspace Color Theme</label>
                <span className="settings-control-help">
                  Toggle between Dark (Operations Console) and Light (Civic Cartography).
                </span>
              </div>
              <div className="settings-segmented-group">
                <button
                  type="button"
                  className={`settings-segmented-btn ${preferences.theme === 'dark' ? 'active' : ''}`}
                  onClick={() => {
                    const next = { ...preferences, theme: 'dark' as const };
                    setPreferences(next);
                    applyTheme('dark');
                  }}
                >
                  <Moon size={12} style={{ marginRight: '4px' }} />
                  Dark Console
                </button>
                <button
                  type="button"
                  className={`settings-segmented-btn ${preferences.theme === 'light' ? 'active' : ''}`}
                  onClick={() => {
                    const next = { ...preferences, theme: 'light' as const };
                    setPreferences(next);
                    applyTheme('light');
                  }}
                >
                  <Sun size={12} style={{ marginRight: '4px' }} />
                  Light Civic
                </button>
              </div>
            </div>
          </div>

          {/* Section 1: Telemetry & Streaming */}
          <div className="settings-section">
            <div className="settings-section-header">
              <Activity size={15} color="#38BDF8" />
              <span>Telemetry Ingestion & Cadence</span>
            </div>
            <div className="settings-control-row">
              <div className="settings-control-info">
                <label className="settings-control-label">Update Refresh Interval</label>
                <span className="settings-control-help">
                  Controls polling fallback and telemetry heartbeat stepping frequency.
                </span>
              </div>
              <div className="settings-segmented-group">
                {[1, 2, 5].map((sec) => (
                  <button
                    key={sec}
                    type="button"
                    className={`settings-segmented-btn ${preferences.telemetryIntervalSeconds === sec ? 'active' : ''}`}
                    onClick={() => setPreferences({ ...preferences, telemetryIntervalSeconds: sec })}
                  >
                    {sec}s
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Section 2: Display & Metrics */}
          <div className="settings-section">
            <div className="settings-section-header">
              <Gauge size={15} color="#10B981" />
              <span>Units & Localization</span>
            </div>
            <div className="settings-control-row">
              <div className="settings-control-info">
                <label className="settings-control-label">Speed & Velocity Units</label>
                <span className="settings-control-help">
                  Primary metric displayed across corridor segments and intersection approaches.
                </span>
              </div>
              <div className="settings-segmented-group">
                <button
                  type="button"
                  className={`settings-segmented-btn ${preferences.speedUnit === 'kmh' ? 'active' : ''}`}
                  onClick={() => setPreferences({ ...preferences, speedUnit: 'kmh' })}
                >
                  km/h (Metric)
                </button>
                <button
                  type="button"
                  className={`settings-segmented-btn ${preferences.speedUnit === 'mph' ? 'active' : ''}`}
                  onClick={() => setPreferences({ ...preferences, speedUnit: 'mph' })}
                >
                  mph (Imperial)
                </button>
              </div>
            </div>
          </div>

          {/* Section 3: Audio & Alerts */}
          <div className="settings-section">
            <div className="settings-section-header">
              <Bell size={15} color="#F59E0B" />
              <span>Advisory & Incident Alerts</span>
            </div>
            <div className="settings-control-row">
              <div className="settings-control-info">
                <label className="settings-control-label">Audible Advisory Chimes</label>
                <span className="settings-control-help">
                  Play subtle alert tones when high-urgency corridor advisories are generated.
                </span>
              </div>
              <button
                type="button"
                className={`settings-toggle-switch ${preferences.enableAlertChimes ? 'checked' : ''}`}
                onClick={() => setPreferences({ ...preferences, enableAlertChimes: !preferences.enableAlertChimes })}
                role="switch"
                aria-checked={preferences.enableAlertChimes}
              >
                <span className="settings-toggle-knob" />
              </button>
            </div>
          </div>

          {/* Section 4: Provenance & Governance */}
          <div className="settings-section">
            <div className="settings-section-header">
              <ShieldCheck size={15} color="#A78BFA" />
              <span>Governance & Provenance Integrity</span>
            </div>
            <div className="settings-control-row">
              <div className="settings-control-info">
                <label className="settings-control-label">Strict Provenance Enforcement</label>
                <span className="settings-control-help">
                  Display sourceMode pills on every sensor metric and model prediction card.
                </span>
              </div>
              <button
                type="button"
                className={`settings-toggle-switch ${preferences.strictProvenancePills ? 'checked' : ''}`}
                onClick={() => setPreferences({ ...preferences, strictProvenancePills: !preferences.strictProvenancePills })}
                role="switch"
                aria-checked={preferences.strictProvenancePills}
              >
                <span className="settings-toggle-knob" />
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="settings-modal-footer">
          <button
            type="button"
            className="settings-reset-btn"
            onClick={handleReset}
            title="Reset to default preferences"
          >
            <RotateCcw size={13} />
            <span>Reset Defaults</span>
          </button>
          <div className="settings-action-buttons">
            <button
              type="button"
              className="settings-cancel-btn"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="button"
              className="settings-save-btn"
              onClick={handleSave}
            >
              {savedFeedback ? (
                <>
                  <Check size={14} />
                  <span>Saved</span>
                </>
              ) : (
                <span>Save Preferences</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
