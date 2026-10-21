import React, { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  Lightbulb,
  MapPin,
  FlaskConical,
  History,
  FileCheck,
  Hash,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import {
  AdvisoryRecommendation,
  DispatchWorkOrder,
  RecommendationSeverity,
  RecommendationStatus
} from '../../types/twin';
import { FeatureAttributionMiniChart } from './FeatureAttributionMiniChart';
import { AuthorizeAdvisoryModal } from './AuthorizeAdvisoryModal';

interface AdvisoryCardProps {
  advisory: AdvisoryRecommendation;
  initialReviewerName?: string;
  onNavigateToEntity?: (entityId: string) => void;
  onNavigateToScenarios?: () => void;
  onAdvisoryUpdated?: () => void;
}

export const AdvisoryCard: React.FC<AdvisoryCardProps> = ({
  advisory,
  initialReviewerName,
  onNavigateToEntity,
  onNavigateToScenarios,
  onAdvisoryUpdated
}) => {
  const [showAuthModal, setShowAuthModal] = useState<boolean>(false);
  const [showAuditDrawer, setShowAuditDrawer] = useState<boolean>(false);

  const getSeverityBadgeClass = (severity: RecommendationSeverity) => {
    switch (severity) {
      case 'CRITICAL':
        return 'badge-critical';
      case 'WARNING':
        return 'badge-warning';
      case 'INFO':
      default:
        return 'badge-info';
    }
  };

  const getStatusBadgeClass = (status: RecommendationStatus) => {
    switch (status) {
      case 'ACTIVE':
        return 'status-active';
      case 'UNDER_REVIEW':
        return 'status-review';
      case 'ACKNOWLEDGED':
        return 'status-acknowledged';
      case 'DISMISSED':
        return 'status-dismissed';
      default:
        return '';
    }
  };

  const handleAuthorized = (_order: DispatchWorkOrder) => {
    if (onAdvisoryUpdated) {
      onAdvisoryUpdated();
    }
  };

  return (
    <div className="advisory-card" style={{
      background: 'var(--color-surface, #09090B)',
      border: '1px solid var(--color-border, #16171B)',
      borderRadius: 'var(--radius-lg, 12px)',
      padding: '20px',
      marginBottom: '16px',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)'
    }}>
      {/* Header Bar */}
      <div className="advisory-card-header" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '8px',
        marginBottom: '12px'
      }}>
        <div className="advisory-badges-left" style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span className={`domain-pill domain-${(advisory.domain || 'traffic').toLowerCase()}`}>
            {advisory.domain}
          </span>
          <span className={`severity-pill ${getSeverityBadgeClass(advisory.severity)}`}>
            {advisory.severity}
          </span>
          <span className={`advisory-status-pill ${getStatusBadgeClass(advisory.status)}`}>
            {(advisory.status || 'ACTIVE').replace('_', ' ')}
          </span>
          <span className="rec-id-tag font-mono" style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
            {advisory.recommendationId}
          </span>
        </div>

        <span className="rec-timestamp" style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
          Generated: {new Date(advisory.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      {/* Advisory Title & Context */}
      <h3 className="advisory-card-title" style={{ fontSize: '15px', fontWeight: 700, margin: '0 0 6px 0', color: 'var(--color-text, #F0F6FC)' }}>
        {advisory.title}
      </h3>
      <p className="advisory-card-desc" style={{ fontSize: '12px', color: 'var(--color-text-secondary, #C9D1D9)', lineHeight: 1.5, margin: '0 0 14px 0' }}>
        {advisory.description}
      </p>

      {/* Proposed Parameter Change Delta Box (if present) */}
      {advisory.proposedChange && (
        <div style={{
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--color-border-strong, #222329)',
          borderRadius: 'var(--radius-md, 8px)',
          padding: '12px 14px',
          marginBottom: '14px'
        }}>
          <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--color-text-secondary)' }}>
            Proposed Controller Adjustment
          </span>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '12px',
            marginTop: '8px',
            fontSize: '12px'
          }}>
            <div>
              <span style={{ display: 'block', fontSize: '10px', color: 'var(--color-text-muted)' }}>Parameter:</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#F0F6FC' }}>
                {advisory.proposedChange.parameter}
                {advisory.proposedChange.phaseId != null && ` (Phase ${advisory.proposedChange.phaseId})`}
              </span>
            </div>
            <div>
              <span style={{ display: 'block', fontSize: '10px', color: 'var(--color-text-muted)' }}>Current Baseline:</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-secondary)' }}>
                {advisory.proposedChange.currentValue.toFixed(1)} {advisory.proposedChange.unit}
              </span>
            </div>
            <div>
              <span style={{ display: 'block', fontSize: '10px', color: 'var(--color-text-muted)' }}>Recommended Split:</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#3FB950' }}>
                {advisory.proposedChange.recommendedValue.toFixed(1)} {advisory.proposedChange.unit}
              </span>
            </div>
            <div>
              <span style={{ display: 'block', fontSize: '10px', color: 'var(--color-text-muted)' }}>Delta:</span>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                color: advisory.proposedChange.recommendedValue >= advisory.proposedChange.currentValue ? '#58A6FF' : '#FF7B72'
              }}>
                {advisory.proposedChange.recommendedValue >= advisory.proposedChange.currentValue ? '+' : ''}
                {(advisory.proposedChange.recommendedValue - advisory.proposedChange.currentValue).toFixed(1)} {advisory.proposedChange.unit}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Conformal Predictive Impact Row (if present) */}
      {advisory.predictedImpact && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '10px',
          marginBottom: '14px'
        }}>
          {/* Delay Saved */}
          <div style={{
            background: 'rgba(47, 129, 247, 0.08)',
            border: '1px solid rgba(47, 129, 247, 0.25)',
            borderRadius: 'var(--radius-md, 8px)',
            padding: '10px 12px'
          }}>
            <span style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: '#58A6FF', textTransform: 'uppercase' }}>
              Projected Delay Impact
            </span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '4px' }}>
              <span style={{ fontSize: '16px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#F0F6FC' }}>
                {advisory.predictedImpact.delayDeltaPct.toFixed(1)}%
              </span>
              <span style={{
                fontSize: '10px',
                fontFamily: 'var(--font-mono)',
                color: '#8B949E',
                background: 'rgba(255, 255, 255, 0.06)',
                padding: '1px 5px',
                borderRadius: '4px'
              }}>
                90% CI: [{advisory.predictedImpact.delayDeltaCI[0].toFixed(1)}%, {advisory.predictedImpact.delayDeltaCI[1].toFixed(1)}%]
              </span>
            </div>
          </div>

          {/* Queue Reduction */}
          <div style={{
            background: 'rgba(63, 185, 80, 0.08)',
            border: '1px solid rgba(63, 185, 80, 0.25)',
            borderRadius: 'var(--radius-md, 8px)',
            padding: '10px 12px'
          }}>
            <span style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: '#3FB950', textTransform: 'uppercase' }}>
              Queue Reduction
            </span>
            <div style={{ fontSize: '16px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#F0F6FC', marginTop: '4px' }}>
              {advisory.predictedImpact.queueDeltaMeters.toFixed(1)} m
            </div>
          </div>

          {/* Fuel Saved */}
          <div style={{
            background: 'rgba(210, 153, 34, 0.08)',
            border: '1px solid rgba(210, 153, 34, 0.25)',
            borderRadius: 'var(--radius-md, 8px)',
            padding: '10px 12px'
          }}>
            <span style={{ display: 'block', fontSize: '10px', fontWeight: 600, color: '#D29922', textTransform: 'uppercase' }}>
              Fuel Burn Savings
            </span>
            <div style={{ fontSize: '16px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#F0F6FC', marginTop: '4px' }}>
              {advisory.predictedImpact.fuelSavedLitersPerHr.toFixed(1)} L/hr
            </div>
          </div>
        </div>
      )}

      {/* Safety Constraint Checklist (if present) */}
      {advisory.safetyChecklist && (
        <div style={{
          background: 'rgba(9, 9, 11, 0.5)',
          border: '1px solid var(--color-border-strong, #222329)',
          borderRadius: 'var(--radius-md, 8px)',
          padding: '10px 14px',
          marginBottom: '14px'
        }}>
          <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Statutory Safety Constraint Checklist
          </span>
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '12px',
            marginTop: '8px',
            fontSize: '11px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <CheckCircle2 size={13} color={advisory.safetyChecklist.pedestrianPhaseSafe ? '#3FB950' : '#F85149'} />
              <span style={{ color: 'var(--color-text-secondary)' }}>
                Pedestrian Walk Phase Preserved (&ge; 14s)
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <CheckCircle2 size={13} color={advisory.safetyChecklist.maxWaitThresholdSafe ? '#3FB950' : '#F85149'} />
              <span style={{ color: 'var(--color-text-secondary)' }}>
                Max Cross-Street Wait Bounded (&lt; 90s)
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <CheckCircle2 size={13} color={advisory.safetyChecklist.emergencyPreemptionClear ? '#3FB950' : '#F85149'} />
              <span style={{ color: 'var(--color-text-secondary)' }}>
                Emergency Preemption Clear
              </span>
            </div>
          </div>
        </div>
      )}

      {/* XAI Attribution Mini-Chart (if topFeatures present) */}
      {advisory.topFeatures && advisory.topFeatures.length > 0 && (
        <FeatureAttributionMiniChart features={advisory.topFeatures} />
      )}

      {/* Operational Dispatch Order Banner (if already authorized) */}
      {advisory.dispatchOrderId && (
        <div style={{
          background: 'rgba(63, 185, 80, 0.08)',
          border: '1px solid rgba(63, 185, 80, 0.3)',
          borderRadius: 'var(--radius-md, 8px)',
          padding: '10px 14px',
          marginTop: '14px',
          marginBottom: '14px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '8px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileCheck size={16} color="#3FB950" />
            <span style={{ fontSize: '11px', fontWeight: 600, color: '#3FB950' }}>
              Municipal Dispatch Order Issued:
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '12px', color: '#F0F6FC' }}>
              {advisory.dispatchOrderId}
            </span>
          </div>
          {advisory.tamperEvidentHash && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px', color: '#58A6FF', fontFamily: 'var(--font-mono)' }}>
              <Hash size={11} />
              <span>SHA-256: {advisory.tamperEvidentHash.substring(0, 12)}...</span>
            </div>
          )}
        </div>
      )}

      {/* Traceable Rule Evidence Box */}
      <div className="advisory-evidence-box" style={{ marginTop: '14px' }}>
        <div className="evidence-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span className="evidence-title" style={{ fontSize: '11px', fontWeight: 700, color: 'var(--color-text-secondary)' }}>
            Traceable Telemetry Evidence
          </span>
          <span className={`provenance-tag prov-${(advisory.evidence?.sourceMode || 'LIVE').toLowerCase()}`}>
            {advisory.evidence?.sourceMode || 'LIVE'}
          </span>
        </div>
        <div className="evidence-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px', fontSize: '11px' }}>
          <div className="evidence-item">
            <span className="ev-label">Target Entity:</span>
            <span className="ev-val font-mono">{(advisory.targetEntityId || '').split(':').pop() || advisory.targetEntityId || 'N/A'}</span>
          </div>
          <div className="evidence-item">
            <span className="ev-label">Trigger Rule:</span>
            <span className="ev-val font-mono">{advisory.triggerRule || 'N/A'}</span>
          </div>
          <div className="evidence-item">
            <span className="ev-label">Trigger Value:</span>
            <span className="ev-val font-bold">
              {advisory.evidence?.observedOrPredictedValue != null
                ? Number(advisory.evidence.observedOrPredictedValue).toFixed(1)
                : '--'}{' '}
              {advisory.evidence?.unit || ''}{' '}
              {advisory.evidence?.threshold != null && (
                <>(Thresh: {Number(advisory.evidence.threshold).toFixed(1)})</>
              )}
            </span>
          </div>
          {advisory.evidence?.confidenceScore != null && (
            <div className="evidence-item">
              <span className="ev-label">Confidence:</span>
              <span className="ev-val">{(Number(advisory.evidence.confidenceScore) * 100).toFixed(0)}%</span>
            </div>
          )}
        </div>
      </div>

      {/* Suggested Action Callout */}
      <div className="suggested-action-callout" style={{ marginTop: '12px' }}>
        <div className="action-icon"><Lightbulb size={16} color="var(--color-primary)" /></div>
        <div className="action-content">
          <span className="action-heading">Suggested Advisory Intervention:</span>
          <p className="action-text">{advisory.suggestedAction}</p>
        </div>
      </div>

      {/* Actions Toolbar */}
      <div className="advisory-actions-bar" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '10px',
        marginTop: '16px',
        paddingTop: '12px',
        borderTop: '1px solid var(--color-border, #16171B)'
      }}>
        <div className="action-btns-left" style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {onNavigateToEntity && (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => onNavigateToEntity(advisory.targetEntityId)}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}
            >
              <MapPin size={13} />
              <span>Inspect on Map</span>
            </button>
          )}
          {advisory.domain === 'TRAFFIC' && onNavigateToScenarios && (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={onNavigateToScenarios}
              style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}
            >
              <FlaskConical size={13} />
              <span>Test in Scenario Studio</span>
            </button>
          )}
        </div>

        <div className="action-btns-right" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setShowAuditDrawer(!showAuditDrawer)}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}
          >
            <History size={13} />
            <span>Audit Log ({(advisory.auditTrail || []).length})</span>
            {showAuditDrawer ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>

          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => setShowAuthModal(true)}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <ShieldCheck size={14} />
            <span>{advisory.status === 'ACKNOWLEDGED' ? 'Re-Issue Work Order' : 'Authorize / Dispatch Order'}</span>
          </button>
        </div>
      </div>

      {/* Audit Trail Drawer */}
      {showAuditDrawer && (
        <div className="audit-trail-panel" style={{
          marginTop: '14px',
          background: 'rgba(5, 5, 7, 0.75)',
          border: '1px solid var(--color-border-strong, #222329)',
          borderRadius: 'var(--radius-md, 8px)',
          padding: '14px'
        }}>
          <h4 className="audit-title" style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-text-secondary)', margin: '0 0 10px 0' }}>
            Chronological Audit History & Municipal Decisions
          </h4>
          <div className="audit-timeline" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {(advisory.auditTrail || []).map((entry, idx) => (
              <div key={idx} className="audit-entry" style={{
                background: 'rgba(255, 255, 255, 0.02)',
                border: '1px solid var(--color-border, #16171B)',
                borderRadius: '6px',
                padding: '8px 10px',
                fontSize: '11px'
              }}>
                <div className="audit-meta" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span className="audit-time font-mono" style={{ color: 'var(--color-text-muted)' }}>
                    {new Date(entry.timestamp).toLocaleString()}
                  </span>
                  <span className="audit-reviewer" style={{ color: '#58A6FF', fontWeight: 600 }}>
                    {entry.reviewer}
                  </span>
                </div>
                <div className="audit-transition" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span className="status-badge-sm" style={{ padding: '1px 6px', borderRadius: '4px', background: 'rgba(255, 255, 255, 0.06)' }}>
                    {entry.previousStatus}
                  </span>
                  <span className="arrow" style={{ color: 'var(--color-text-muted)' }}>&rarr;</span>
                  <span className="status-badge-sm" style={{ padding: '1px 6px', borderRadius: '4px', background: 'rgba(47, 129, 247, 0.15)', color: '#58A6FF' }}>
                    {entry.newStatus}
                  </span>
                </div>
                {entry.notes && (
                  <p className="audit-notes" style={{ margin: '4px 0 0 0', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
                    "{entry.notes}"
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Authorization Modal */}
      {showAuthModal && (
        <AuthorizeAdvisoryModal
          advisory={advisory}
          initialReviewerName={initialReviewerName}
          onClose={() => setShowAuthModal(false)}
          onAuthorized={handleAuthorized}
        />
      )}
    </div>
  );
};
