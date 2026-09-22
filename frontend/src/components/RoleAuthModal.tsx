import React, { useState } from 'react';
import {
  ShieldCheck,
  Car,
  Zap,
  FileCheck2,
  Activity,
  ArrowRight,
  Lock,
  Building2,
  X
} from 'lucide-react';
import { MunicipalRole } from '../types/twin';

interface RoleAuthModalProps {
  isOpen: boolean;
  currentRole: MunicipalRole;
  onClose: () => void;
  onAuthenticate: (role: MunicipalRole) => void;
}

interface RoleOption {
  role: MunicipalRole;
  title: string;
  badge: string;
  color: string;
  bgSubtle: string;
  icon: React.ReactNode;
  clearance: string;
  scope: string;
  workspaces: string[];
}

export const RoleAuthModal: React.FC<RoleAuthModalProps> = ({
  isOpen,
  currentRole,
  onClose,
  onAuthenticate
}) => {
  const [selectedRole, setSelectedRole] = useState<MunicipalRole>(currentRole);

  if (!isOpen) return null;

  const roleOptions: RoleOption[] = [
    {
      role: 'Traffic Systems Engineer',
      title: 'Traffic Systems Engineer',
      badge: 'TRAFFIC COMMAND',
      color: '#F59E0B',
      bgSubtle: 'rgba(245, 158, 11, 0.12)',
      icon: <Car size={22} color="#F59E0B" />,
      clearance: 'Level 2 • Operational Kinematics & Signal Control',
      scope: 'Supervise signal progression offsets, queue lengths, Level of Service (LOS), and SUMO microscopic scenario simulations on Viman Nagar (VN-01) ↔ Somnath Nagar (SN-01).',
      workspaces: ['Operations Map', 'Traffic Analytics', 'Scenario Studio', 'Traffic Recommendations']
    },
    {
      role: 'Energy Grid Manager',
      title: 'Energy Grid Manager',
      badge: 'GRID UTILITY',
      color: '#10B981',
      bgSubtle: 'rgba(16, 185, 129, 0.12)',
      icon: <Zap size={22} color="#10B981" />,
      clearance: 'Level 2 • Substation Feeder & Peak Governance',
      scope: 'Inspect commercial building demand, hourly carbon emissions, diurnal solar variations, and peak demand charge mitigation for Phoenix Marketcity zone.',
      workspaces: ['Operations Map', 'Energy Analytics', 'Environment Context', 'Energy Recommendations']
    },
    {
      role: 'Executive Auditor',
      title: 'Executive Auditor',
      badge: 'ALGORITHMIC GOVERNANCE',
      color: '#38BDF8',
      bgSubtle: 'rgba(56, 189, 248, 0.12)',
      icon: <FileCheck2 size={22} color="#38BDF8" />,
      clearance: 'Level 3 • Independent Audit & Compliance Verification',
      scope: 'Verify distribution-free conformal prediction bounds, TreeSHAP feature attributions, model version provenance, dataset manifests, and municipal decision briefings.',
      workspaces: ['Evaluation & Reports', 'System & Data Health', 'Advisory Governance']
    },
    {
      role: 'Municipal Analyst',
      title: 'Municipal Analyst',
      badge: 'CROSS-DOMAIN COMMAND',
      color: '#2F81F7',
      bgSubtle: 'rgba(47, 129, 247, 0.12)',
      icon: <Activity size={22} color="#2F81F7" />,
      clearance: 'Level 1 • Comprehensive Master Command',
      scope: 'Corridor-wide operational intelligence across arterial mobility, electrical power grids, ambient air quality indexes, and multi-horizon decision support.',
      workspaces: ['All 8 Workspaces (Full Master Console)']
    }
  ];

  const handleConfirm = () => {
    onAuthenticate(selectedRole);
    onClose();
  };

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="role-auth-title"
      onClick={onClose}
    >
      <div
        className="role-auth-modal"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '740px',
          maxWidth: '94vw',
          maxHeight: '92vh',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: '#0D1117',
          border: '1px solid #30363D',
          borderRadius: '12px',
          boxShadow: '0 24px 64px rgba(0, 0, 0, 0.8), 0 0 1px rgba(255, 255, 255, 0.2)',
          overflow: 'hidden'
        }}
      >
        {/* Header Strip */}
        <div
          style={{
            padding: '20px 24px',
            borderBottom: '1px solid #21262D',
            background: 'linear-gradient(180deg, rgba(22, 27, 34, 0.9) 0%, rgba(13, 17, 23, 0.9) 100%)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start'
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <Building2 size={16} color="var(--color-primary, #2F81F7)" />
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: 'var(--text-muted)'
                }}
              >
                PUNE MUNICIPAL CORPORATION • URBAN DIGITAL TWIN
              </span>
            </div>
            <h2
              id="role-auth-title"
              style={{
                fontSize: '20px',
                fontWeight: 700,
                color: '#F0F6FC',
                margin: 0,
                letterSpacing: '-0.02em'
              }}
            >
              Municipal Role Authentication Gateway
            </h2>
            <p
              style={{
                fontSize: '12.5px',
                color: '#8B949E',
                margin: '4px 0 0 0',
                lineHeight: 1.45
              }}
            >
              Select your authenticated municipal persona to tailor views, permissions, and domain decision-support tools.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#8B949E',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '6px',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
            title="Close Authentication Dialog"
            aria-label="Close Authentication Dialog"
          >
            <X size={18} />
          </button>
        </div>

        {/* Security Notice Banner */}
        <div
          style={{
            padding: '10px 24px',
            background: 'rgba(47, 129, 247, 0.08)',
            borderBottom: '1px solid rgba(47, 129, 247, 0.2)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '12px',
            color: '#79C0FF'
          }}
        >
          <Lock size={14} style={{ flexShrink: 0 }} />
          <span>
            <strong>Read-Only Advisory Guardrail:</strong> The platform operates in decision-support mode. Physical traffic signal actuation is strictly prevented by municipal charter.
          </span>
        </div>

        {/* Role Cards List */}
        <div
          style={{
            padding: '20px 24px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            flex: 1
          }}
        >
          {roleOptions.map((opt) => {
            const isSelected = selectedRole === opt.role;
            return (
              <div
                key={opt.role}
                onClick={() => setSelectedRole(opt.role)}
                style={{
                  padding: '16px',
                  borderRadius: '10px',
                  border: isSelected
                    ? `1.5px solid ${opt.color}`
                    : '1px solid #21262D',
                  background: isSelected
                    ? 'rgba(22, 27, 34, 0.95)'
                    : 'rgba(22, 27, 34, 0.5)',
                  boxShadow: isSelected
                    ? `0 0 16px ${opt.color}25, inset 0 0 0 1px ${opt.color}30`
                    : 'none',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  position: 'relative'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
                  {/* Icon Avatar */}
                  <div
                    style={{
                      width: '42px',
                      height: '42px',
                      borderRadius: '8px',
                      background: opt.bgSubtle,
                      border: `1px solid ${opt.color}40`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0
                    }}
                  >
                    {opt.icon}
                  </div>

                  {/* Role Content */}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span
                          style={{
                            fontSize: '15px',
                            fontWeight: 700,
                            color: isSelected ? '#FFFFFF' : '#E6EDF3'
                          }}
                        >
                          {opt.title}
                        </span>
                        <span
                          style={{
                            fontSize: '10px',
                            fontWeight: 700,
                            letterSpacing: '0.04em',
                            color: opt.color,
                            background: opt.bgSubtle,
                            border: `1px solid ${opt.color}40`,
                            padding: '2px 7px',
                            borderRadius: '9999px'
                          }}
                        >
                          {opt.badge}
                        </span>
                      </div>

                      {/* Selection Radio Circle */}
                      <div
                        style={{
                          width: '18px',
                          height: '18px',
                          borderRadius: '50%',
                          border: isSelected ? `5px solid ${opt.color}` : '2px solid #484F58',
                          background: isSelected ? '#FFFFFF' : 'transparent',
                          flexShrink: 0,
                          transition: 'all 0.15s ease'
                        }}
                      />
                    </div>

                    <div
                      style={{
                        fontSize: '11.5px',
                        color: opt.color,
                        fontWeight: 600,
                        marginTop: '3px'
                      }}
                    >
                      {opt.clearance}
                    </div>

                    <p
                      style={{
                        fontSize: '12px',
                        color: '#8B949E',
                        margin: '6px 0 10px 0',
                        lineHeight: 1.45
                      }}
                    >
                      {opt.scope}
                    </p>

                    {/* Authorized Workspace Badges */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '11px', color: '#6E7681', fontWeight: 600 }}>
                        Authorized Workspaces:
                      </span>
                      {opt.workspaces.map((ws, i) => (
                        <span
                          key={i}
                          style={{
                            fontSize: '11px',
                            fontWeight: 500,
                            color: '#C9D1D9',
                            background: 'rgba(255, 255, 255, 0.06)',
                            border: '1px solid rgba(255, 255, 255, 0.08)',
                            padding: '1px 7px',
                            borderRadius: '4px'
                          }}
                        >
                          {ws}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer Actions */}
        <div
          style={{
            padding: '16px 24px',
            borderTop: '1px solid #21262D',
            background: 'rgba(13, 17, 23, 0.95)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={16} color="#10B981" />
            <span style={{ fontSize: '12px', color: '#8B949E' }}>
              Authenticated for Nagar Road Arterial Corridor
            </span>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={onClose}
              style={{ padding: '8px 14px' }}
            >
              Cancel
            </button>
            <button
              type="button"
              className="run-scenario-btn"
              onClick={handleConfirm}
              style={{
                margin: 0,
                padding: '8px 18px',
                fontSize: '13px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <span>Authorize & Enter Workspace</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
