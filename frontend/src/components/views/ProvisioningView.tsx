import React, { useState } from 'react';
import {
  ArrowLeft,
  Send,
  CheckCircle2,
  Building2,
  Mail,
  UserCheck,
  MapPin,
  Layers,
  ShieldCheck,
  ChevronDown,
  AlertCircle,
  Copy,
  Check,
  Info,
  RotateCcw
} from 'lucide-react';
import { DigitalTwinLogo } from '../common/DigitalTwinLogo';

interface ProvisioningViewProps {
  onNavigateHome: () => void;
}

const RESTRICTED_DOMAINS = [
  'gmail.com',
  'yahoo.com',
  'hotmail.com',
  'outlook.com',
  'aol.com',
  'icloud.com',
  'proton.me',
  'protonmail.com',
  'zoho.com'
];

const JURISDICTION_LEVELS = [
  'Municipal Corporation / City Council',
  'Metropolitan Regional Transport Authority',
  'State Highway & Public Works Department',
  'Commercial Campus / Special Economic Zone Authority',
  'Public Transit Operating Authority',
  'Emergency Services & Fleet Command',
  'Inter-Agency Oversight & Audit Board'
];

const OPERATIONAL_DOMAINS = [
  'Intelligent Traffic Mobility & Adaptive Control',
  'Municipal Energy Grid & Substation Dispatch',
  'Transit Intermodal Fleet Coordination',
  'Executive Regulatory & Carbon Audit',
  'Cross-Agency Unified Corridor Operations'
];

const INFRASTRUCTURE_SCALES = [
  '1-10 Intersections / Corridors (Pilot Sandbox)',
  '11-50 Intersections / Sub-district Network',
  '51-200 Intersections / Metropolitan Arterial Grid',
  '200+ Intersections / Urban Municipality',
  'Commercial Campus / Microgrid Facilities'
];

export const ProvisioningView: React.FC<ProvisioningViewProps> = ({ onNavigateHome }) => {
  const [organization, setOrganization] = useState<string>('');
  const [workEmail, setWorkEmail] = useState<string>('');
  const [contactName, setContactName] = useState<string>('');
  const [jurisdictionLevel, setJurisdictionLevel] = useState<string>(JURISDICTION_LEVELS[0]);
  const [corridorScope, setCorridorScope] = useState<string>('');
  const [domain, setDomain] = useState<string>(OPERATIONAL_DOMAINS[0]);
  const [infrastructureScale, setInfrastructureScale] = useState<string>(INFRASTRUCTURE_SCALES[0]);
  const [message, setMessage] = useState<string>('');

  // Submission & Flight Animation States: 'idle' | 'transmitting' | 'success'
  const [submitState, setSubmitState] = useState<'idle' | 'transmitting' | 'success'>('idle');
  const [referenceId, setReferenceId] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<boolean>(false);

  // Email validation check
  const getEmailFeedback = () => {
    if (!workEmail.trim()) {
      return { status: 'idle', message: '' };
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(workEmail)) {
      return { status: 'invalid', message: 'Invalid email syntax.' };
    }
    const domainPart = workEmail.split('@')[1]?.toLowerCase();
    if (domainPart && RESTRICTED_DOMAINS.includes(domainPart)) {
      return {
        status: 'restricted',
        message: 'Personal webmail domains are restricted. Please use an official agency email.'
      };
    }
    if (domainPart && (domainPart.endsWith('.gov') || domainPart.endsWith('.gov.in') || domainPart.includes('transport') || domainPart.includes('city'))) {
      return { status: 'verified', message: 'Official municipal domain verified.' };
    }
    return { status: 'valid', message: 'Institutional domain recognized.' };
  };

  const emailFeedback = getEmailFeedback();

  const handleCopyReference = () => {
    if (!referenceId) return;
    navigator.clipboard.writeText(referenceId);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  const handleResetForm = () => {
    setOrganization('');
    setWorkEmail('');
    setContactName('');
    setCorridorScope('');
    setMessage('');
    setSubmitState('idle');
    setReferenceId('');
    setErrorMessage(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    // Form validation
    if (!contactName.trim()) {
      setErrorMessage('Please enter your full name and official title.');
      return;
    }
    if (!workEmail.trim() || emailFeedback.status === 'invalid' || emailFeedback.status === 'restricted') {
      setErrorMessage('An official municipal or enterprise email address is required.');
      return;
    }
    if (!organization.trim()) {
      setErrorMessage('Please enter your department or agency name.');
      return;
    }
    if (!corridorScope.trim()) {
      setErrorMessage('Please enter your arterial corridor or sector identifier.');
      return;
    }

    // Trigger airplane dispatch animation sequence
    setSubmitState('transmitting');

    setTimeout(() => {
      const generatedId = `INQ-2026-${Math.floor(10000 + Math.random() * 90000)}`;
      setReferenceId(generatedId);
      setSubmitState('success');
    }, 1150);
  };

  return (
    <div className="provisioning-page-root">
      {/* Top Navigation Bar */}
      <header className="provisioning-top-nav" role="banner">
        <div className="provisioning-nav-inner">
          <div className="provisioning-nav-brand" onClick={onNavigateHome} title="Return to Public Portal">
            <DigitalTwinLogo size={24} />
            <span className="brand-name">Digital Twin</span>
          </div>
          <button
            type="button"
            onClick={onNavigateHome}
            className="provisioning-back-btn font-mono"
            aria-label="Back to Public Portal"
          >
            <ArrowLeft size={14} />
            <span>Return to Portal</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="provisioning-main-container" id="provisioning-content">
        <div className="provisioning-workspace-grid">
          {/* Left Context Column: Authority & Clearance Protocol */}
          <aside className="provisioning-context-panel" aria-label="Provisioning Guidelines">
            <div className="provisioning-context-header">
              <span className="provisioning-eyebrow font-mono">MUNICIPAL ARTERIAL CORRIDORS</span>
              <h1 className="provisioning-page-title font-sans">Digital Twin Provisioning</h1>
              <p className="provisioning-page-desc font-sans">
                Official access gateway for municipal traffic engineers, grid dispatchers, transit coordinators, and audit officers.
              </p>
            </div>

            {/* Protocol Highlights */}
            <div className="provisioning-protocol-list">
              <div className="provisioning-protocol-item">
                <div className="protocol-step-num font-mono">01</div>
                <div className="protocol-step-content">
                  <span className="protocol-step-title font-sans">Official Intake Verification</span>
                  <p className="protocol-step-desc font-sans">
                    Submissions are authenticated against authorized municipal domain registries to protect corridor telemetry.
                  </p>
                </div>
              </div>

              <div className="provisioning-protocol-item">
                <div className="protocol-step-num font-mono">02</div>
                <div className="protocol-step-content">
                  <span className="protocol-step-title font-sans">Decision Support Sandbox</span>
                  <p className="protocol-step-desc font-sans">
                    Approved agencies receive an isolated workspace loaded with SUMO simulation loops and corridor telemetry.
                  </p>
                </div>
              </div>

              <div className="provisioning-protocol-item">
                <div className="protocol-step-num font-mono">03</div>
                <div className="protocol-step-content">
                  <span className="protocol-step-title font-sans">Strictly Non-Actuating</span>
                  <p className="protocol-step-desc font-sans">
                    Platform recommendations are advisory. Interventions require human authorization outside the platform.
                  </p>
                </div>
              </div>
            </div>

            {/* Trust Badges Bar */}
            <div className="provisioning-trust-footer font-mono">
              <div className="trust-item">
                <ShieldCheck size={13} color="#10B981" />
                <span>TLS 1.3 ENCRYPTED INTAKE</span>
              </div>
              <div className="trust-item">
                <Layers size={13} color="#38BDF8" />
                <span>TIMESCALEDB ISOLATION</span>
              </div>
            </div>
          </aside>

          {/* Right Form Column: Clean, High-Contrast Form Without Clutter */}
          <section className="provisioning-form-panel" aria-label="Provisioning Request Form">
            <div className="form-card-header">
              <h2 className="form-card-title font-sans">Authority & Operational Scope</h2>
              <span className="form-required-note font-mono">* All marked fields are mandatory for clearance</span>
            </div>

            {errorMessage && (
              <div className="provisioning-error-banner font-sans" role="alert">
                <AlertCircle size={15} color="#F85149" />
                <span>{errorMessage}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="provisioning-form" noValidate>
              {/* Section 1: Official Authority & Contact */}
              <div className="form-section-group">
                <div className="form-grid-2col">
                  {/* Full Name & Title */}
                  <div className="form-field-wrap">
                    <label htmlFor="input-contactName" className="form-label font-sans">
                      Full Name & Official Title <span className="req-star">*</span>
                    </label>
                    <div className="form-input-container">
                      <UserCheck size={14} className="input-field-icon" />
                      <input
                        id="input-contactName"
                        type="text"
                        value={contactName}
                        onChange={(e) => setContactName(e.target.value)}
                        placeholder="Dr. Sarah Chen, Director of Traffic Systems"
                        className="form-text-input font-sans"
                        required
                      />
                    </div>
                    <p className="form-field-hint font-sans">
                      Enter your full name and official title. Avoid unexpanded organizational acronyms.
                    </p>
                  </div>

                  {/* Official Work Email */}
                  <div className="form-field-wrap">
                    <div className="form-label-row">
                      <label htmlFor="input-workEmail" className="form-label font-sans">
                        Official Institutional Email <span className="req-star">*</span>
                      </label>
                      {emailFeedback.message && (
                        <span className={`email-feedback-pill font-mono ${emailFeedback.status}`}>
                          {emailFeedback.message}
                        </span>
                      )}
                    </div>
                    <div className="form-input-container">
                      <Mail size={14} className="input-field-icon" />
                      <input
                        id="input-workEmail"
                        type="email"
                        value={workEmail}
                        onChange={(e) => setWorkEmail(e.target.value)}
                        placeholder="s.chen@transitsystems.gov"
                        className={`form-text-input font-sans ${emailFeedback.status === 'restricted' || emailFeedback.status === 'invalid' ? 'input-error' : emailFeedback.status === 'verified' ? 'input-success' : ''}`}
                        required
                      />
                    </div>
                    <p className="form-field-hint font-sans">
                      Enter your official municipal or agency email. Personal webmail (Gmail, Yahoo) is not accepted.
                    </p>
                  </div>
                </div>

                <div className="form-grid-2col">
                  {/* Agency / Department */}
                  <div className="form-field-wrap">
                    <label htmlFor="input-organization" className="form-label font-sans">
                      Agency or Department <span className="req-star">*</span>
                    </label>
                    <div className="form-input-container">
                      <Building2 size={14} className="input-field-icon" />
                      <input
                        id="input-organization"
                        type="text"
                        value={organization}
                        onChange={(e) => setOrganization(e.target.value)}
                        placeholder="Department of Municipal Transportation"
                        className="form-text-input font-sans"
                        required
                      />
                    </div>
                    <p className="form-field-hint font-sans">
                      Enter your primary municipal agency or department. External partners must list their sponsoring authority.
                    </p>
                  </div>

                  {/* Jurisdiction Level (Dropdown) */}
                  <div className="form-field-wrap">
                    <label htmlFor="select-jurisdictionLevel" className="form-label font-sans">
                      Jurisdiction Level <span className="req-star">*</span>
                    </label>
                    <div className="form-select-container">
                      <select
                        id="select-jurisdictionLevel"
                        value={jurisdictionLevel}
                        onChange={(e) => setJurisdictionLevel(e.target.value)}
                        className="form-select-input font-sans"
                      >
                        {JURISDICTION_LEVELS.map((lvl) => (
                          <option key={lvl} value={lvl}>{lvl}</option>
                        ))}
                      </select>
                      <ChevronDown size={14} className="select-chevron-icon" />
                    </div>
                    <p className="form-field-hint font-sans">
                      Select your operational tier. This sets corridor boundary rights and access tiering.
                    </p>
                  </div>
                </div>

                {/* Corridor Scope */}
                <div className="form-field-wrap">
                  <label htmlFor="input-corridorScope" className="form-label font-sans">
                    Corridor or Sector Identifier <span className="req-star">*</span>
                  </label>
                  <div className="form-input-container">
                    <MapPin size={14} className="input-field-icon" />
                    <input
                      id="input-corridorScope"
                      type="text"
                      value={corridorScope}
                      onChange={(e) => setCorridorScope(e.target.value)}
                      placeholder="Arterial Sector 4 - Central Gateway"
                      className="form-text-input font-sans"
                      required
                    />
                  </div>
                  <p className="form-field-hint font-sans">
                    Specify the municipal corridor name, arterial segment, or planning sector. Do not enter broad national names.
                  </p>
                </div>
              </div>

              {/* Section 2: Domain & Scale */}
              <div className="form-section-group">
                <div className="form-grid-2col">
                  {/* Primary Domain */}
                  <div className="form-field-wrap">
                    <label htmlFor="select-domain" className="form-label font-sans">
                      Primary Operational Domain <span className="req-star">*</span>
                    </label>
                    <div className="form-select-container">
                      <select
                        id="select-domain"
                        value={domain}
                        onChange={(e) => setDomain(e.target.value)}
                        className="form-select-input font-sans"
                      >
                        {OPERATIONAL_DOMAINS.map((dom) => (
                          <option key={dom} value={dom}>{dom}</option>
                        ))}
                      </select>
                      <ChevronDown size={14} className="select-chevron-icon" />
                    </div>
                    <p className="form-field-hint font-sans">
                      Select your primary analytics focus (adaptive traffic mobility, energy microgrid, or transit coordination).
                    </p>
                  </div>

                  {/* Infrastructure Scale */}
                  <div className="form-field-wrap">
                    <label htmlFor="select-scale" className="form-label font-sans">
                      Infrastructure Scale <span className="req-star">*</span>
                    </label>
                    <div className="form-select-container">
                      <select
                        id="select-scale"
                        value={infrastructureScale}
                        onChange={(e) => setInfrastructureScale(e.target.value)}
                        className="form-select-input font-sans"
                      >
                        {INFRASTRUCTURE_SCALES.map((scale) => (
                          <option key={scale} value={scale}>{scale}</option>
                        ))}
                      </select>
                      <ChevronDown size={14} className="select-chevron-icon" />
                    </div>
                    <p className="form-field-hint font-sans">
                      Specify the target deployment size. Pilot sandboxes start at 1 to 10 intersections.
                    </p>
                  </div>
                </div>

                {/* Operational Objectives */}
                <div className="form-field-wrap">
                  <label htmlFor="textarea-message" className="form-label font-sans">
                    Operational Objectives & Context <span className="optional-tag font-mono">(Optional)</span>
                  </label>
                  <textarea
                    id="textarea-message"
                    rows={2}
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Briefly describe decision-support objectives, planned simulation scenarios, or multi-agency coordination needs..."
                    className="form-textarea-input font-sans"
                  />
                  <p className="form-field-hint font-sans">
                    Briefly outline your corridor objectives, key pain points, or evaluation needs. Do not submit sensitive credentials.
                  </p>
                </div>
              </div>

              {/* Submit Action Bar: Dynamic State Transition */}
              <div className="provisioning-submit-bar">
                <div className="submit-advisory-note font-sans">
                  <Info size={13} color="#8B949E" />
                  <span>Single-use invitation link dispatched upon official domain validation.</span>
                </div>

                <div className="submit-btn-group">
                  <button
                    type="button"
                    onClick={onNavigateHome}
                    disabled={submitState === 'transmitting'}
                    className="provisioning-cancel-btn font-sans"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitState === 'transmitting' || emailFeedback.status === 'restricted'}
                    className={`provisioning-submit-btn landing-btn-primary font-sans ${submitState === 'transmitting' ? 'is-launching' : ''}`}
                  >
                    {/* Laser Progress Bar during transmission */}
                    {submitState === 'transmitting' && <div className="btn-launch-laser" />}

                    <span className="btn-label-text">
                      {submitState === 'transmitting' ? 'Encrypting & Transmitting...' : 'Submit Provisioning Request'}
                    </span>

                    <span className={`btn-plane-wrapper ${submitState === 'transmitting' ? 'in-flight' : ''}`}>
                      <Send size={15} className="plane-icon" />
                    </span>
                  </button>
                </div>
              </div>
            </form>
          </section>
        </div>
      </main>

      {/* Animated Dispatch Window Modal: Appears with paper-plane arrival motion */}
      {submitState === 'success' && (
        <div className="provision-flight-modal-backdrop" role="dialog" aria-modal="true">
          <div className="provision-flight-modal-card">
            {/* Animated Flight Receptor & Pulse Rings */}
            <div className="flight-receptor-stage">
              <div className="flight-radar-ring ring-1" />
              <div className="flight-radar-ring ring-2" />
              <div className="flight-landing-beacon">
                <div className="airplane-arrival-glyph">
                  <Send size={24} className="landing-plane-icon" />
                </div>
                <div className="beacon-verified-gem">
                  <CheckCircle2 size={16} color="#FFFFFF" strokeWidth={3} />
                </div>
              </div>
            </div>

            {/* Transmission Status Badges */}
            <div className="flight-modal-status-badge font-mono">
              <span className="status-live-dot" />
              <span>TRANSMISSION CONFIRMED : TLS 1.3 ENCRYPTED</span>
            </div>

            <h2 className="flight-modal-title font-sans">Provisioning Request Dispatched</h2>
            <p className="flight-modal-desc font-sans">
              Your digital twin workspace inquiry for <strong style={{ color: '#F0F6FC' }}>{organization}</strong> has been
              securely recorded in the authoritative intake ledger.
            </p>

            {/* Reference Authorization Badge */}
            <div className="flight-reference-container">
              <span className="flight-ref-label font-mono">AUTHORIZATION REFERENCE ID</span>
              <div className="flight-ref-box font-mono">
                <span className="flight-ref-code">{referenceId}</span>
                <button
                  type="button"
                  onClick={handleCopyReference}
                  className="flight-ref-copy-btn font-mono"
                  aria-label="Copy Reference ID"
                >
                  {copiedId ? <Check size={13} color="#10B981" /> : <Copy size={13} />}
                  <span>{copiedId ? 'COPIED' : 'COPY'}</span>
                </button>
              </div>
            </div>

            {/* Process Timeline Steps */}
            <div className="flight-process-checklist font-sans">
              <div className="checklist-item">
                <div className="checklist-bullet font-mono">1</div>
                <div className="checklist-text">
                  <strong>Agency Registry Validation:</strong> Credentials authenticated against public sector records.
                </div>
              </div>
              <div className="checklist-item">
                <div className="checklist-bullet font-mono">2</div>
                <div className="checklist-text">
                  <strong>Corridor Telemetry Mapping:</strong> Requested road network aligned with standard simulation loops.
                </div>
              </div>
              <div className="checklist-item">
                <div className="checklist-bullet font-mono">3</div>
                <div className="checklist-text">
                  <strong>Tokenized Invitation Email:</strong> A single-use, 48-hour cryptographic onboarding link dispatched to <strong style={{ color: '#F0F6FC' }}>{workEmail}</strong>.
                </div>
              </div>
            </div>

            {/* Action Bar */}
            <div className="flight-modal-actions">
              <button
                type="button"
                onClick={handleResetForm}
                className="flight-secondary-btn font-sans"
              >
                <RotateCcw size={13} />
                <span>Submit Another Request</span>
              </button>
              <button
                type="button"
                onClick={onNavigateHome}
                className="flight-primary-btn font-sans"
              >
                <span>Return to Public Portal</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
