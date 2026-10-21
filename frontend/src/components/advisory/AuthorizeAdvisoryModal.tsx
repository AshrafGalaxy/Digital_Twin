import React, { useState } from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Download,
  Printer,
  Copy,
  Check,
  X,
  FileCheck,
  Hash
} from 'lucide-react';
import {
  AdvisoryRecommendation,
  AuthorizeAdvisoryPayload,
  DispatchWorkOrder,
  RecommendationStatus
} from '../../types/twin';
import { authorizeAdvisory } from '../../services/api';

interface AuthorizeAdvisoryModalProps {
  advisory: AdvisoryRecommendation;
  initialReviewerName?: string;
  onClose: () => void;
  onAuthorized: (workOrder: DispatchWorkOrder) => void;
}

export const AuthorizeAdvisoryModal: React.FC<AuthorizeAdvisoryModalProps> = ({
  advisory,
  initialReviewerName = 'Municipal Analyst',
  onClose,
  onAuthorized
}) => {
  const [badgeId, setBadgeId] = useState<string>('MCC-OPS-4091');
  const [shiftId, setShiftId] = useState<string>('SHIFT-EVENING-B');
  const [reviewer, setReviewer] = useState<string>(initialReviewerName);
  const [decision, setDecision] = useState<RecommendationStatus>('ACKNOWLEDGED');
  const [notes, setNotes] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [issuedOrder, setIssuedOrder] = useState<DispatchWorkOrder | null>(null);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!badgeId.trim()) {
      setError('Dispatcher Badge ID is mandatory for municipal audit logging.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const payload: AuthorizeAdvisoryPayload = {
        badgeId: badgeId.trim(),
        shiftId: shiftId.trim(),
        reviewer: reviewer.trim(),
        decision,
        notes: notes.trim() || undefined
      };
      const order = await authorizeAdvisory(advisory.recommendationId, payload);
      setIssuedOrder(order);
      onAuthorized(order);
    } catch (err: any) {
      console.error('Authorization dispatch error', err);
      setError(err?.message || 'Failed to authorize advisory and generate municipal dispatch order.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopyHash = () => {
    if (!issuedOrder) return;
    navigator.clipboard.writeText(issuedOrder.tamperEvidentHash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleDownloadJson = () => {
    if (!issuedOrder) return;
    const blob = new Blob([JSON.stringify(issuedOrder, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${issuedOrder.dispatchOrderId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="modal-backdrop" style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.82)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1050,
      padding: '16px'
    }}>
      <div className="modal-container" style={{
        background: 'var(--color-surface, #09090B)',
        border: '1px solid var(--color-border-strong, #222329)',
        borderRadius: 'var(--radius-lg, 12px)',
        width: '100%',
        maxWidth: '640px',
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.65)',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Modal Header */}
        <div style={{
          padding: '18px 24px',
          borderBottom: '1px solid var(--color-border, #16171B)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(15, 15, 18, 0.8)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'rgba(47, 129, 247, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <ShieldCheck size={18} color="var(--color-primary, #2F81F7)" />
            </div>
            <div>
              <h2 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: 'var(--color-text, #F0F6FC)' }}>
                {issuedOrder ? 'Municipal Dispatch Order Issued' : 'Operator Authorization & Dispatch Workflow'}
              </h2>
              <span style={{ fontSize: '11px', color: 'var(--color-text-secondary, #C9D1D9)' }}>
                {advisory.recommendationId} : {(advisory.targetEntityId || '').split(':').pop()}
              </span>
            </div>
          </div>
          <button
            type="button"
            className="btn-link"
            onClick={onClose}
            style={{ color: 'var(--color-text-muted)', cursor: 'pointer', padding: '4px' }}
            aria-label="Close dialog"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '20px 24px' }}>
          {/* Non-Actuation Disclaimer Banner */}
          <div style={{
            background: 'rgba(210, 153, 34, 0.08)',
            border: '1px solid rgba(210, 153, 34, 0.3)',
            borderRadius: 'var(--radius-md, 8px)',
            padding: '12px 14px',
            marginBottom: '18px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px'
          }}>
            <AlertTriangle size={18} color="#D29922" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div style={{ fontSize: '12px', color: '#F0F6FC', lineHeight: '1.5' }}>
              <strong>Mandatory Non-Actuation Governance:</strong> The digital twin platform is strictly read-only decision support. Authorizing this recommendation generates an immutable dispatch work order with a cryptographic SHA-256 hash. No direct physical actuator signal is emitted. Field implementation requires authorization outside the platform.
            </div>
          </div>

          {error && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              borderRadius: 'var(--radius-md, 8px)',
              padding: '10px 14px',
              marginBottom: '16px',
              fontSize: '12px',
              color: '#FF7B72'
            }}>
              {error}
            </div>
          )}

          {!issuedOrder ? (
            /* Authorization Form */
            <form onSubmit={handleSubmit}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
                    Dispatcher Badge ID *
                  </label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    value={badgeId}
                    onChange={(e) => setBadgeId(e.target.value)}
                    placeholder="e.g. MCC-OPS-4091"
                    style={{ width: '100%', fontFamily: 'var(--font-mono)' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
                    Operating Shift ID *
                  </label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    value={shiftId}
                    onChange={(e) => setShiftId(e.target.value)}
                    placeholder="e.g. SHIFT-EVENING-B"
                    style={{ width: '100%', fontFamily: 'var(--font-mono)' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
                    Reviewer Name & Role
                  </label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    value={reviewer}
                    onChange={(e) => setReviewer(e.target.value)}
                    placeholder="e.g. Municipal Traffic Officer"
                    style={{ width: '100%' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
                    Authorization Decision
                  </label>
                  <select
                    className="form-select"
                    value={decision}
                    onChange={(e) => setDecision(e.target.value as RecommendationStatus)}
                    style={{ width: '100%' }}
                  >
                    <option value="ACKNOWLEDGED">ACKNOWLEDGED (Authorize Municipal Dispatch Order)</option>
                    <option value="UNDER_REVIEW">UNDER_REVIEW (Pending Field Observation)</option>
                    <option value="DISMISSED">DISMISSED (Rejected / Operational Infeasible)</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
                  Operational Notes & Field Verification Justification
                </label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Document observations regarding queued vehicle demand, safety compliance, or coordination with traffic wardens..."
                  style={{ width: '100%', resize: 'vertical' }}
                />
              </div>

              {/* Action Proposal Review Card */}
              <div style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--color-border, #16171B)',
                borderRadius: 'var(--radius-md, 8px)',
                padding: '12px 14px',
                marginBottom: '20px'
              }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                  Work Order Scope Summary:
                </span>
                <p style={{ fontSize: '12px', color: '#F0F6FC', margin: '4px 0 0' }}>
                  {advisory.suggestedAction}
                </p>
              </div>

              {/* Modal Buttons */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={onClose}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary btn-sm"
                  disabled={submitting || !badgeId.trim()}
                  style={{ minWidth: '220px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
                >
                  <FileCheck size={15} />
                  <span>{submitting ? 'Generating Cryptographic Order...' : 'Generate Municipal Dispatch Order'}</span>
                </button>
              </div>
            </form>
          ) : (
            /* Issued Dispatch Order Ticket */
            <div>
              <div style={{
                background: 'rgba(63, 185, 80, 0.08)',
                border: '1px solid rgba(63, 185, 80, 0.3)',
                borderRadius: 'var(--radius-md, 8px)',
                padding: '14px 16px',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px'
              }}>
                <CheckCircle2 size={24} color="#3FB950" style={{ flexShrink: 0 }} />
                <div>
                  <span style={{ fontSize: '11px', fontWeight: 600, color: '#3FB950', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Municipal Work Order Generated & Authenticated
                  </span>
                  <div style={{ fontSize: '18px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#F0F6FC', marginTop: '2px' }}>
                    {issuedOrder.dispatchOrderId}
                  </div>
                </div>
              </div>

              {/* SHA-256 Tamper-Evident Hash Box */}
              <div style={{
                background: 'rgba(0, 0, 0, 0.5)',
                border: '1px solid var(--color-border-strong, #222329)',
                borderRadius: 'var(--radius-md, 8px)',
                padding: '10px 14px',
                marginBottom: '16px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Hash size={13} color="var(--color-primary)" />
                    <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                      Cryptographic SHA-256 Audit Hash
                    </span>
                  </div>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={handleCopyHash}
                    style={{ height: '22px', padding: '0 8px', fontSize: '10px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                  >
                    {copiedHash ? <Check size={11} color="#3FB950" /> : <Copy size={11} />}
                    <span>{copiedHash ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
                <div style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  color: '#58A6FF',
                  wordBreak: 'break-all',
                  background: 'rgba(47, 129, 247, 0.06)',
                  padding: '6px 8px',
                  borderRadius: '4px'
                }}>
                  {issuedOrder.tamperEvidentHash}
                </div>
              </div>

              {/* Dispatch Details Grid */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '10px',
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid var(--color-border, #16171B)',
                borderRadius: 'var(--radius-md, 8px)',
                padding: '12px 14px',
                fontSize: '12px',
                marginBottom: '18px'
              }}>
                <div>
                  <span style={{ color: 'var(--color-text-muted)', display: 'block', fontSize: '10px' }}>Target Asset:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: '#F0F6FC' }}>{issuedOrder.targetEntityId}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--color-text-muted)', display: 'block', fontSize: '10px' }}>Authorized By:</span>
                  <span style={{ color: '#F0F6FC' }}>{issuedOrder.authorizedBy} (Badge: {issuedOrder.badgeId})</span>
                </div>
                <div>
                  <span style={{ color: 'var(--color-text-muted)', display: 'block', fontSize: '10px' }}>Duty Shift:</span>
                  <span style={{ color: '#F0F6FC' }}>{issuedOrder.shiftId}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--color-text-muted)', display: 'block', fontSize: '10px' }}>Issued At:</span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: '#F0F6FC' }}>
                    {new Date(issuedOrder.issuedAt).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={handleDownloadJson}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}
                  >
                    <Download size={13} />
                    <span>Download Ticket (JSON)</span>
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={handlePrint}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}
                  >
                    <Printer size={13} />
                    <span>Print Work Order</span>
                  </button>
                </div>

                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={onClose}
                >
                  Close & Return
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
