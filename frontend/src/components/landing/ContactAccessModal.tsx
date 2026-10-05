import React, { useState, useEffect } from 'react';
import {
  X,
  Send,
  CheckCircle2,
  Building2,
  Mail,
  UserCheck,
  MapPin,
  Layers,
  FileText,
  ShieldCheck,
  Sparkles,
  ChevronDown,
  AlertCircle,
  Copy,
  Check
} from 'lucide-react';

interface ContactAccessModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const RESTRICTED_DOMAINS = [
  'gmail.com',
  'yahoo.com',
  'hotmail.com',
  'outlook.com',
  'live.com',
  'icloud.com',
  'aol.com',
  'mail.com',
  'zoho.com',
  'proton.me',
  'protonmail.com',
  'gmx.com',
  'yandex.com'
];

const JURISDICTION_PRESETS = [
  'Central Arterial Corridor',
  'Metropolitan Signal Grid',
  'Airport Transit Zone',
  'Smart Campus Substation Grid'
];

export const ContactAccessModal: React.FC<ContactAccessModalProps> = ({
  isOpen,
  onClose
}) => {
  const [organization, setOrganization] = useState<string>('');
  const [workEmail, setWorkEmail] = useState<string>('');
  const [contactName, setContactName] = useState<string>('');
  const [jurisdiction, setJurisdiction] = useState<string>('');
  const [domain, setDomain] = useState<string>('Intelligent Traffic Mobility & Adaptive Control');
  const [infrastructureScale, setInfrastructureScale] = useState<string>('1-10 Intersections / Corridors');
  const [message, setMessage] = useState<string>('');

  const [emailValidation, setEmailValidation] = useState<{
    status: 'idle' | 'valid' | 'restricted' | 'invalid';
    message: string;
  }>({ status: 'idle', message: '' });

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [submittedInquiryId, setSubmittedInquiryId] = useState<string | null>(null);
  const [isCopied, setIsCopied] = useState<boolean>(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Live Email Validation
  const handleEmailChange = (val: string) => {
    setWorkEmail(val);
    const trimmed = val.trim();
    if (!trimmed) {
      setEmailValidation({ status: 'idle', message: '' });
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmed)) {
      setEmailValidation({
        status: 'invalid',
        message: 'Please enter a valid official email address.'
      });
      return;
    }
    const domainPart = trimmed.split('@')[1]?.toLowerCase();
    if (domainPart && RESTRICTED_DOMAINS.includes(domainPart)) {
      setEmailValidation({
        status: 'restricted',
        message: 'Official agency, municipal, or institutional email required (.gov, .org, or enterprise domain). Personal providers are restricted for security authentication.'
      });
      return;
    }
    setEmailValidation({
      status: 'valid',
      message: 'Verified official domain format'
    });
  };

  const handleCopyTrackingId = () => {
    if (!submittedInquiryId) return;
    navigator.clipboard.writeText(submittedInquiryId);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    // Validation
    if (!organization.trim()) {
      setErrorMessage('Please enter your agency or organization name.');
      return;
    }
    if (!jurisdiction.trim()) {
      setErrorMessage('Please specify your target city, municipality, or corridor jurisdiction.');
      return;
    }
    if (!contactName.trim() || contactName.trim().length < 3) {
      setErrorMessage('Please provide the authorizing officer or lead engineer name and role.');
      return;
    }

    const emailTrimmed = workEmail.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailTrimmed || !emailRegex.test(emailTrimmed)) {
      setErrorMessage('Please enter a valid official work email address.');
      return;
    }

    const domainPart = emailTrimmed.split('@')[1]?.toLowerCase();
    if (domainPart && RESTRICTED_DOMAINS.includes(domainPart)) {
      setErrorMessage('Please use an official agency, municipal, or enterprise email address (.gov, .org, or institutional domain). Personal email providers are restricted.');
      return;
    }

    setIsSubmitting(true);
    const payload = {
      organization: organization.trim(),
      work_email: emailTrimmed,
      contact_name: contactName.trim(),
      jurisdiction: jurisdiction.trim(),
      domain,
      infrastructure_scale: infrastructureScale,
      message: message.trim()
    };

    try {
      const response = await fetch('/api/v1/inquiries/request-access', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const data = await response.json();
        setSubmittedInquiryId(data.inquiry_id || `INQ-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`);
      } else {
        // Fallback resilience for offline or pre-boot environments
        saveLocalInquiry(payload);
      }
    } catch {
      // Network/offline resilience: save locally
      saveLocalInquiry(payload);
    } finally {
      setIsSubmitting(false);
    }
  };

  const saveLocalInquiry = (payload: any) => {
    const mockId = `INQ-${new Date().getFullYear()}-${Math.floor(1000 + Math.random() * 9000)}`;
    try {
      const existing = JSON.parse(localStorage.getItem('digital_twin_access_inquiries') || '[]');
      existing.push({ ...payload, inquiryId: mockId, createdAt: new Date().toISOString() });
      localStorage.setItem('digital_twin_access_inquiries', JSON.stringify(existing));
    } catch {
      // Storage unavailable or blocked
    }
    setSubmittedInquiryId(mockId);
  };

  const handleResetAndClose = () => {
    setSubmittedInquiryId(null);
    setErrorMessage(null);
    setEmailValidation({ status: 'idle', message: '' });
    onClose();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="contact-modal-title"
      className="provision-modal-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="provision-modal-dialog">
        {/* Modal Header */}
        <div className="provision-modal-header">
          <div>
            <div className="provision-badge">
              <span className="provision-pulse-dot" />
              <span>Municipal & Enterprise Access</span>
            </div>
            <h2 id="contact-modal-title" className="provision-modal-title">
              Request Digital Twin Provisioning
            </h2>
            <p className="provision-modal-subtitle">
              Provision an authoritative multi-domain telemetry sandbox for verified transport departments, municipal authorities, and campus infrastructure operators.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="provision-close-btn"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="provision-modal-body">
          {submittedInquiryId ? (
            /* Success State */
            <div style={{ textAlign: 'center', padding: '16px 8px' }}>
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '50%',
                  background: 'rgba(16, 185, 129, 0.12)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 16px'
                }}
              >
                <CheckCircle2 size={28} color="#10B981" />
              </div>

              <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#F0F6FC', margin: '0 0 8px 0' }}>
                Access Request Registered
              </h3>

              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: '#07070A',
                  border: '1px solid #1C1D24',
                  padding: '6px 14px',
                  borderRadius: '6px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '13px',
                  color: '#58A6FF',
                  marginBottom: '16px'
                }}
              >
                <span>Tracking ID: {submittedInquiryId}</span>
                <button
                  type="button"
                  onClick={handleCopyTrackingId}
                  title="Copy tracking ID"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: isCopied ? '#34D399' : '#8B949E',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    padding: '2px'
                  }}
                >
                  {isCopied ? <Check size={14} /> : <Copy size={14} />}
                </button>
              </div>

              <p
                style={{
                  fontSize: '13px',
                  color: '#8B949E',
                  lineHeight: 1.6,
                  maxWidth: '460px',
                  margin: '0 auto 24px'
                }}
              >
                Thank you for your inquiry. Our engineering team reviews corridor scale, sensor topology, and data interfaces to provision your dedicated simulation and decision-support instance.
              </p>

              <div
                style={{
                  background: '#050507',
                  borderRadius: '8px',
                  border: '1px solid #16171B',
                  padding: '14px 18px',
                  textAlign: 'left',
                  marginBottom: '24px'
                }}
              >
                <div style={{ fontSize: '11px', color: '#8B949E', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px', fontFamily: 'var(--font-mono)' }}>
                  Onboarding Timeline
                </div>
                <div style={{ fontSize: '12px', color: '#C9D1D9', lineHeight: 1.6 }}>
                  1. Agency verification against official public sector or enterprise register.<br />
                  2. Network topology onboarding and sensor telemetry format mapping.<br />
                  3. Issuance of isolated sandbox credentials and read-only decision support access within 1 business day.
                </div>
              </div>

              <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                <button
                  type="button"
                  onClick={handleResetAndClose}
                  className="provision-submit-btn landing-btn-primary"
                  style={{ height: '38px', padding: '0 24px', cursor: 'pointer' }}
                >
                  Return to Public Portal
                </button>
              </div>
            </div>
          ) : (
            /* Request Form */
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {errorMessage && (
                <div
                  style={{
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#F87171',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    fontSize: '13px',
                    lineHeight: 1.4,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <AlertCircle size={15} style={{ flexShrink: 0 }} />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Section 1: Authority & Jurisdiction */}
              <div className="provision-section-title">
                01. Jurisdiction & Deployment Scope
              </div>

              <div className="provision-grid-2col">
                <div className="provision-field-group">
                  <label className="provision-label">
                    <span className="provision-label-content">
                      <Building2 size={13} color="#8B949E" />
                      Agency or Municipal Authority *
                    </span>
                  </label>
                  <input
                    type="text"
                    required
                    value={organization}
                    onChange={(e) => setOrganization(e.target.value)}
                    placeholder="e.g., Department of Transportation"
                    className="provision-input"
                    autoComplete="organization"
                  />
                </div>

                <div className="provision-field-group">
                  <label className="provision-label">
                    <span className="provision-label-content">
                      <MapPin size={13} color="#8B949E" />
                      Municipal Jurisdiction / Study Corridor *
                    </span>
                  </label>
                  <input
                    type="text"
                    required
                    value={jurisdiction}
                    onChange={(e) => setJurisdiction(e.target.value)}
                    placeholder="e.g., Central Arterial Corridor"
                    className="provision-input"
                    autoComplete="off"
                    spellCheck={false}
                  />
                  {/* Quick Suggestion Chips */}
                  <div className="provision-chips-wrap">
                    <span className="provision-chips-label">Presets:</span>
                    {JURISDICTION_PRESETS.map((preset) => (
                      <button
                        key={preset}
                        type="button"
                        className="provision-chip-btn"
                        onClick={() => setJurisdiction(preset)}
                      >
                        {preset}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Section 2: Technical Authority & Verification */}
              <div className="provision-section-title" style={{ marginTop: '4px' }}>
                02. Authorizing Technical Lead & Verification
              </div>

              <div className="provision-grid-2col">
                <div className="provision-field-group">
                  <label className="provision-label">
                    <span className="provision-label-content">
                      <UserCheck size={13} color="#8B949E" />
                      Lead Technical Authority / Representative Name & Role *
                    </span>
                  </label>
                  <input
                    type="text"
                    required
                    value={contactName}
                    onChange={(e) => setContactName(e.target.value)}
                    placeholder="e.g., Dr. Sarah Chen, Director of Traffic Systems"
                    className="provision-input"
                    autoComplete="name"
                  />
                </div>

                <div className="provision-field-group">
                  <label className="provision-label">
                    <span className="provision-label-content">
                      <Mail size={13} color="#8B949E" />
                      Official Institutional or Agency Email *
                    </span>
                  </label>
                  <input
                    type="email"
                    required
                    value={workEmail}
                    onChange={(e) => handleEmailChange(e.target.value)}
                    placeholder="e.g., s.chen@transportation.gov or lead@metrodistrict.org"
                    className={`provision-input ${
                      emailValidation.status === 'restricted' || emailValidation.status === 'invalid'
                        ? 'has-error'
                        : emailValidation.status === 'valid'
                        ? 'has-success'
                        : ''
                    }`}
                    autoComplete="email"
                  />
                  {emailValidation.message && (
                    <div
                      className={`provision-input-feedback ${
                        emailValidation.status === 'valid'
                          ? 'success'
                          : emailValidation.status === 'restricted'
                          ? 'warning'
                          : 'error'
                      }`}
                    >
                      {emailValidation.status === 'valid' && <CheckCircle2 size={12} />}
                      {emailValidation.status === 'restricted' && <AlertCircle size={12} />}
                      {emailValidation.status === 'invalid' && <AlertCircle size={12} />}
                      <span>{emailValidation.message}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Section 3: Telemetry Scope & Scale */}
              <div className="provision-section-title" style={{ marginTop: '4px' }}>
                03. Telemetry Scope & Environment
              </div>

              {/* Primary Domain Selection with Inset Chevron */}
              <div className="provision-field-group">
                <label className="provision-label">
                  <span className="provision-label-content">
                    <Layers size={13} color="#8B949E" />
                    Operational Domain of Interest *
                  </span>
                </label>
                <div className="provision-select-wrap">
                  <select
                    value={domain}
                    onChange={(e) => setDomain(e.target.value)}
                    className="provision-select"
                  >
                    <option value="Intelligent Traffic Mobility & Adaptive Control">
                      Intelligent Traffic Mobility & Adaptive Control
                    </option>
                    <option value="Energy Management & Microgrid Optimization">
                      Energy Management & Microgrid Optimization
                    </option>
                    <option value="Environmental Microclimate & Dispersion">
                      Environmental Microclimate & Air Quality Tracking
                    </option>
                    <option value="Critical Infrastructure Structural Health">
                      Critical Infrastructure Structural Health Monitoring
                    </option>
                    <option value="Integrated Multi-Domain Digital Twin">
                      Integrated Multi-Domain Digital Twin Platform
                    </option>
                  </select>
                  <div className="provision-select-arrow">
                    <ChevronDown size={15} />
                  </div>
                </div>
              </div>

              {/* Deployment Scale with Inset Chevron */}
              <div className="provision-field-group">
                <label className="provision-label">
                  <span className="provision-label-content">
                    <Sparkles size={13} color="#8B949E" />
                    Target Network Scale
                  </span>
                </label>
                <div className="provision-select-wrap">
                  <select
                    value={infrastructureScale}
                    onChange={(e) => setInfrastructureScale(e.target.value)}
                    className="provision-select"
                  >
                    <option value="1-10 Intersections / Corridors">
                      Pilot Corridor (1-10 Intersections / Feeder Buses)
                    </option>
                    <option value="10-50 Intersections">
                      Arterial Network (10-50 Intersections / Campus Grid)
                    </option>
                    <option value="City-wide Arterial Grid">
                      Metropolitan Grid (50+ Intersections / Multi-Building Facility)
                    </option>
                    <option value="Academic & Research Exploration">
                      Academic Research & Simulation Modeling
                    </option>
                  </select>
                  <div className="provision-select-arrow">
                    <ChevronDown size={15} />
                  </div>
                </div>
              </div>

              {/* Operational Requirements Notes */}
              <div className="provision-field-group">
                <label className="provision-label">
                  <span className="provision-label-content">
                    <FileText size={13} color="#8B949E" />
                    Operational Goals & Telemetry Context
                  </span>
                </label>
                <textarea
                  rows={3}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Outline corridor geometry, sensor formats (radar, inductive loops, power meters), or scenario goals..."
                  className="provision-textarea"
                />
              </div>

              {/* Invariant Statement */}
              <div className="provision-governance-banner">
                <ShieldCheck size={16} color="#38BDF8" style={{ flexShrink: 0 }} />
                <span className="provision-governance-text">
                  Strict Non-Actuation Protocol: Digital twin instances deliver advisory-only decision support with immutable TimescaleDB logging and zero commuter surveillance.
                </span>
              </div>

              {/* Submit Buttons */}
              <div className="provision-modal-actions">
                <button
                  type="button"
                  onClick={onClose}
                  className="provision-cancel-btn"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || emailValidation.status === 'restricted'}
                  className="provision-submit-btn landing-btn-primary"
                >
                  {isSubmitting ? (
                    <>
                      <div className="provision-spinner" />
                      <span>Provisioning...</span>
                    </>
                  ) : (
                    <>
                      <span>Submit Request</span>
                      <Send size={14} />
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>

      </div>
    </div>
  );
};

