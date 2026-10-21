import React, { useState, useEffect } from 'react';
import {
  X,
  ShieldCheck,
  CheckCircle2,
  Copy,
  Check,
  RefreshCw
} from 'lucide-react';
import {
  fetchAccessInquiries,
  approveAccessInquiry,
  rejectAccessInquiry,
  AccessInquiryRecord,
  ApproveInquiryResponse
} from '../../services/api';

interface AdminProvisioningModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const AUTHORIZED_ROLES = [
  'Traffic Systems Engineer',
  'Energy Grid Manager',
  'Executive Auditor',
  'Municipal Analyst'
];

export const AdminProvisioningModal: React.FC<AdminProvisioningModalProps> = ({
  isOpen,
  onClose
}) => {
  const [inquiries, setInquiries] = useState<AccessInquiryRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'PENDING' | 'APPROVED' | 'REJECTED'>('PENDING');

  // Selected inquiry for approval dialog
  const [selectedInquiry, setSelectedInquiry] = useState<AccessInquiryRecord | null>(null);
  const [assignedRole, setAssignedRole] = useState<string>(AUTHORIZED_ROLES[0]);
  const [expiryDays, setExpiryDays] = useState<number>(7);
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  // Approval result details (Magic link + email payload)
  const [approvalResult, setApprovalResult] = useState<ApproveInquiryResponse | null>(null);
  const [copiedLink, setCopiedLink] = useState<boolean>(false);
  const [copiedEmail, setCopiedEmail] = useState<boolean>(false);

  // Reject dialog state
  const [rejectingInquiry, setRejectingInquiry] = useState<AccessInquiryRecord | null>(null);
  const [rejectionReason, setRejectionReason] = useState<string>('');

  const loadInquiries = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAccessInquiries(statusFilter === 'ALL' ? undefined : statusFilter);
      setInquiries(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load access inquiries.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadInquiries();
    }
  }, [isOpen, statusFilter]);

  if (!isOpen) return null;

  const handleApprove = async () => {
    if (!selectedInquiry) return;
    setActionLoading(true);
    setError(null);
    try {
      const result = await approveAccessInquiry(selectedInquiry.id, {
        assigned_role: assignedRole,
        expiry_days: expiryDays,
        reviewer_notes: reviewNotes.trim() || undefined
      });
      setApprovalResult(result);
      setSelectedInquiry(null);
      loadInquiries();
    } catch (err: any) {
      setError(err.message || 'Failed to approve inquiry.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!rejectingInquiry || !rejectionReason.trim()) return;
    setActionLoading(true);
    setError(null);
    try {
      await rejectAccessInquiry(rejectingInquiry.id, rejectionReason.trim());
      setRejectingInquiry(null);
      setRejectionReason('');
      loadInquiries();
    } catch (err: any) {
      setError(err.message || 'Failed to reject inquiry.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCopyMagicLink = () => {
    if (!approvalResult) return;
    const fullUrl = `${window.location.origin}${approvalResult.magic_link}`;
    navigator.clipboard.writeText(fullUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const handleCopyEmailDraft = () => {
    if (!approvalResult) return;
    const textToCopy = `Subject: ${approvalResult.email_payload.subject}\n\nTo: ${approvalResult.email_payload.to}\n\n${approvalResult.email_payload.body}`;
    navigator.clipboard.writeText(textToCopy);
    setCopiedEmail(true);
    setTimeout(() => setCopiedEmail(false), 2000);
  };

  const counts = {
    total: inquiries.length,
    pending: inquiries.filter((i) => i.status === 'PENDING').length,
    approved: inquiries.filter((i) => i.status === 'APPROVED').length,
    rejected: inquiries.filter((i) => i.status === 'REJECTED').length
  };

  return (
    <div
      className="settings-modal-overlay"
      style={{ zIndex: 10000 }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="admin-provisioning-title"
    >
      <div
        className="settings-modal-card"
        style={{
          maxWidth: '860px',
          width: '92vw',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Modal Header */}
        <div className="settings-modal-header" style={{ borderBottom: '1px solid var(--color-border)' }}>
          <div className="settings-header-title-group">
            <div className="settings-icon-badge" style={{ backgroundColor: 'rgba(47, 129, 247, 0.15)' }}>
              <ShieldCheck size={18} color="#2F81F7" />
            </div>
            <div>
              <h2 id="admin-provisioning-title" className="settings-title">
                Platform Administration: Access & Provisioning Console
              </h2>
              <p className="settings-description">
                Evaluate prospective agency requests, authorize operational roles, and issue single-use cryptographic magic links.
              </p>
            </div>
          </div>
          <button
            type="button"
            className="settings-close-btn"
            onClick={onClose}
            aria-label="Close administration console"
          >
            <X size={18} />
          </button>
        </div>

        {/* Console Toolbar & Filter Tabs */}
        <div
          style={{
            padding: '12px 20px',
            background: 'var(--color-surface-subtle)',
            borderBottom: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px'
          }}
        >
          {/* Status Filter Tabs */}
          <div style={{ display: 'flex', gap: '6px' }}>
            {(['PENDING', 'APPROVED', 'REJECTED', 'ALL'] as const).map((st) => (
              <button
                key={st}
                type="button"
                onClick={() => setStatusFilter(st)}
                style={{
                  padding: '6px 12px',
                  fontSize: '12px',
                  fontWeight: 600,
                  borderRadius: '4px',
                  border: statusFilter === st ? '1px solid var(--color-primary)' : '1px solid var(--color-border)',
                  backgroundColor: statusFilter === st ? 'var(--color-primary-subtle)' : 'var(--color-surface)',
                  color: statusFilter === st ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                  cursor: 'pointer'
                }}
              >
                {st === 'ALL' ? 'All Inquiries' : st.charAt(0) + st.slice(1).toLowerCase()}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
              Pending: <strong>{counts.pending}</strong> &bull; Approved: <strong>{counts.approved}</strong> &bull; Rejected: <strong>{counts.rejected}</strong>
            </span>
            <button
              type="button"
              onClick={loadInquiries}
              disabled={loading}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 10px',
                fontSize: '12px',
                borderRadius: '4px',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-surface)',
                color: 'var(--color-text)',
                cursor: 'pointer'
              }}
              title="Refresh requests"
            >
              <RefreshCw size={13} className={loading ? 'spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
          {error && (
            <div
              style={{
                marginBottom: '16px',
                padding: '10px 14px',
                borderRadius: '6px',
                backgroundColor: 'var(--color-danger-subtle)',
                border: '1px solid var(--color-danger)',
                color: 'var(--color-danger)',
                fontSize: '12px'
              }}
            >
              {error}
            </div>
          )}

          {/* Success Banner when token is newly generated */}
          {approvalResult && (
            <div
              style={{
                marginBottom: '20px',
                padding: '16px',
                borderRadius: '8px',
                backgroundColor: 'rgba(63, 185, 80, 0.12)',
                border: '1px solid var(--color-success)',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CheckCircle2 size={18} color="#3FB950" />
                  <span style={{ fontWeight: 700, color: 'var(--color-text)', fontSize: '14px' }}>
                    Access Granted for {approvalResult.inquiry_id} (Role: {approvalResult.assigned_role})
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setApprovalResult(null)}
                  style={{ background: 'transparent', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}
                >
                  <X size={16} />
                </button>
              </div>

              {/* Generated Magic Access Link */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <label style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                  Single-Use Cryptographic Magic Access Link:
                </label>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <input
                    type="text"
                    readOnly
                    value={`${window.location.origin}${approvalResult.magic_link}`}
                    style={{
                      flex: 1,
                      padding: '8px 12px',
                      borderRadius: '4px',
                      border: '1px solid var(--color-border-strong)',
                      backgroundColor: 'var(--color-surface)',
                      color: 'var(--color-text)',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '12px'
                    }}
                  />
                  <button
                    type="button"
                    onClick={handleCopyMagicLink}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '8px 14px',
                      borderRadius: '4px',
                      backgroundColor: copiedLink ? 'var(--color-success)' : 'var(--color-primary)',
                      color: '#FFFFFF',
                      border: 'none',
                      fontWeight: 600,
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    {copiedLink ? <Check size={14} /> : <Copy size={14} />}
                    <span>{copiedLink ? 'Copied' : 'Copy Link'}</span>
                  </button>
                </div>
              </div>

              {/* Forwarding Email Draft Card */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <label style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
                    Forwarding Email Draft for {approvalResult.email_payload.to}:
                  </label>
                  <button
                    type="button"
                    onClick={handleCopyEmailDraft}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      border: '1px solid var(--color-border)',
                      backgroundColor: 'var(--color-surface)',
                      color: 'var(--color-text)',
                      fontSize: '11px',
                      cursor: 'pointer'
                    }}
                  >
                    {copiedEmail ? <Check size={12} color="#3FB950" /> : <Copy size={12} />}
                    <span>{copiedEmail ? 'Copied Email Draft' : 'Copy Email Draft'}</span>
                  </button>
                </div>
                <textarea
                  readOnly
                  rows={6}
                  value={approvalResult.email_payload.body}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    border: '1px solid var(--color-border)',
                    backgroundColor: 'var(--color-surface)',
                    color: 'var(--color-text-secondary)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '11px',
                    lineHeight: 1.45,
                    resize: 'none'
                  }}
                />
              </div>
            </div>
          )}

          {/* Active Approval Dialog */}
          {selectedInquiry && (
            <div
              style={{
                marginBottom: '20px',
                padding: '16px',
                borderRadius: '8px',
                backgroundColor: 'var(--color-surface-raised)',
                border: '1px solid var(--color-primary)',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--color-text)' }}>
                  Authorize Digital Twin Access: {selectedInquiry.organization} ({selectedInquiry.contact_name})
                </span>
                <button
                  type="button"
                  onClick={() => setSelectedInquiry(null)}
                  style={{ background: 'transparent', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}
                >
                  <X size={16} />
                </button>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '4px' }}>
                    Assign Authorized Municipal Role
                  </label>
                  <select
                    value={assignedRole}
                    onChange={(e) => setAssignedRole(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px',
                      borderRadius: '4px',
                      border: '1px solid var(--color-border)',
                      backgroundColor: 'var(--color-surface)',
                      color: 'var(--color-text)',
                      fontSize: '12px'
                    }}
                  >
                    {AUTHORIZED_ROLES.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '4px' }}>
                    Token Expiration Horizon
                  </label>
                  <select
                    value={expiryDays}
                    onChange={(e) => setExpiryDays(Number(e.target.value))}
                    style={{
                      width: '100%',
                      padding: '8px',
                      borderRadius: '4px',
                      border: '1px solid var(--color-border)',
                      backgroundColor: 'var(--color-surface)',
                      color: 'var(--color-text)',
                      fontSize: '12px'
                    }}
                  >
                    <option value={7}>7 Days (Standard Evaluation)</option>
                    <option value={14}>14 Days (Corridor Pilot Demonstration)</option>
                    <option value={30}>30 Days (Extended Municipal Sandbox)</option>
                    <option value={90}>90 Days (Institutional Term)</option>
                  </select>
                </div>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '4px' }}>
                  Reviewer Audit Notes (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Authorized for corridor simulation trials; single-operator credential."
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    border: '1px solid var(--color-border)',
                    backgroundColor: 'var(--color-surface)',
                    color: 'var(--color-text)',
                    fontSize: '12px'
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setSelectedInquiry(null)}
                  style={{
                    padding: '8px 14px',
                    borderRadius: '4px',
                    border: '1px solid var(--color-border)',
                    backgroundColor: 'transparent',
                    color: 'var(--color-text)',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleApprove}
                  disabled={actionLoading}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '8px 16px',
                    borderRadius: '4px',
                    border: 'none',
                    backgroundColor: 'var(--color-primary)',
                    color: '#FFFFFF',
                    fontWeight: 600,
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                >
                  <ShieldCheck size={14} />
                  <span>{actionLoading ? 'Issuing Token...' : 'Confirm Approval & Generate Magic Link'}</span>
                </button>
              </div>
            </div>
          )}

          {/* Active Reject Dialog */}
          {rejectingInquiry && (
            <div
              style={{
                marginBottom: '20px',
                padding: '16px',
                borderRadius: '8px',
                backgroundColor: 'var(--color-surface-raised)',
                border: '1px solid var(--color-danger)',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}
            >
              <span style={{ fontWeight: 700, fontSize: '13px', color: 'var(--color-danger)' }}>
                Reject Access Request: {rejectingInquiry.organization} ({rejectingInquiry.id})
              </span>
              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '4px' }}>
                  Stated Rejection Reason:
                </label>
                <input
                  type="text"
                  placeholder="e.g. Unverified municipal domain or unauthorized commercial scraping."
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '4px',
                    border: '1px solid var(--color-border)',
                    backgroundColor: 'var(--color-surface)',
                    color: 'var(--color-text)',
                    fontSize: '12px'
                  }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setRejectingInquiry(null)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '4px',
                    border: '1px solid var(--color-border)',
                    backgroundColor: 'transparent',
                    color: 'var(--color-text)',
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleReject}
                  disabled={actionLoading || !rejectionReason.trim()}
                  style={{
                    padding: '6px 14px',
                    borderRadius: '4px',
                    border: 'none',
                    backgroundColor: 'var(--color-danger)',
                    color: '#FFFFFF',
                    fontWeight: 600,
                    fontSize: '12px',
                    cursor: 'pointer'
                  }}
                >
                  {actionLoading ? 'Rejecting...' : 'Confirm Rejection'}
                </button>
              </div>
            </div>
          )}

          {/* Inquiries List Table */}
          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)', fontSize: '13px' }}>
              Loading access inquiries from authoritative database...
            </div>
          ) : inquiries.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-muted)', fontSize: '13px' }}>
              No inquiries found for filter: {statusFilter}.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {inquiries.map((inq) => (
                <div
                  key={inq.id}
                  style={{
                    padding: '14px 16px',
                    borderRadius: '8px',
                    backgroundColor: 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                    boxShadow: 'var(--shadow-sm)'
                  }}
                >
                  {/* Card Header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--color-primary)', fontSize: '13px' }}>
                          {inq.id}
                        </span>
                        <span
                          style={{
                            fontSize: '11px',
                            fontWeight: 600,
                            padding: '2px 8px',
                            borderRadius: '12px',
                            backgroundColor:
                              inq.status === 'APPROVED'
                                ? 'var(--color-success-subtle)'
                                : inq.status === 'REJECTED'
                                ? 'var(--color-danger-subtle)'
                                : 'var(--color-warning-subtle)',
                            color:
                              inq.status === 'APPROVED'
                                ? 'var(--color-success)'
                                : inq.status === 'REJECTED'
                                ? 'var(--color-danger)'
                                : 'var(--color-warning)'
                          }}
                        >
                          {inq.status}
                        </span>
                        {inq.assigned_role && (
                          <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)', background: 'var(--color-surface-raised)', padding: '2px 8px', borderRadius: '4px', border: '1px solid var(--color-border)' }}>
                            Role: {inq.assigned_role}
                          </span>
                        )}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                        <span style={{ fontWeight: 600, color: 'var(--color-text)', fontSize: '14px' }}>
                          {inq.organization}
                        </span>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '12px' }}>
                          ({inq.contact_name} &bull; {inq.work_email})
                        </span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      {inq.status === 'PENDING' && (
                        <>
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedInquiry(inq);
                              setRejectingInquiry(null);
                            }}
                            style={{
                              padding: '5px 12px',
                              borderRadius: '4px',
                              backgroundColor: 'var(--color-primary)',
                              color: '#FFFFFF',
                              border: 'none',
                              fontSize: '11px',
                              fontWeight: 600,
                              cursor: 'pointer'
                            }}
                          >
                            Approve Access
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setRejectingInquiry(inq);
                              setSelectedInquiry(null);
                            }}
                            style={{
                              padding: '5px 10px',
                              borderRadius: '4px',
                              backgroundColor: 'transparent',
                              color: 'var(--color-danger)',
                              border: '1px solid var(--color-border)',
                              fontSize: '11px',
                              cursor: 'pointer'
                            }}
                          >
                            Reject
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Metadata Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                    <div><strong>Jurisdiction:</strong> {inq.jurisdiction}</div>
                    <div><strong>Domain:</strong> {inq.domain}</div>
                    <div><strong>Scale:</strong> {inq.infrastructure_scale || 'Pilot Corridor'}</div>
                    <div><strong>Submitted:</strong> {new Date(inq.created_at).toLocaleString()}</div>
                  </div>

                  {/* Notes / Message */}
                  {inq.message && (
                    <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', background: 'var(--color-surface-subtle)', padding: '6px 10px', borderRadius: '4px', border: '1px solid var(--color-border)' }}>
                      <strong>Requester Notes:</strong> {inq.message}
                    </div>
                  )}

                  {inq.rejection_reason && (
                    <div style={{ fontSize: '11px', color: 'var(--color-danger)', background: 'var(--color-danger-subtle)', padding: '6px 10px', borderRadius: '4px' }}>
                      <strong>Rejection Rationale:</strong> {inq.rejection_reason}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="settings-modal-footer" style={{ borderTop: '1px solid var(--color-border)' }}>
          <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
            Authoritative Platform System of Record &bull; Single-use cryptographic tokens
          </span>
          <button
            type="button"
            className="settings-cancel-btn"
            onClick={onClose}
          >
            Close Console
          </button>
        </div>
      </div>
    </div>
  );
};
