import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface WebGLRecoveryOverlayProps {
  viewLabel: string;
  onRebuild?: () => void;
}

/**
 * Operator-facing recovery notice rendered over a map or 3D canvas while its
 * WebGL graphics context is unavailable and awaiting browser restoration.
 */
export const WebGLRecoveryOverlay: React.FC<WebGLRecoveryOverlayProps> = ({
  viewLabel,
  onRebuild
}) => {
  return (
    <div
      role="alert"
      aria-live="assertive"
      className="webgl-recovery-overlay"
      style={{
        position: 'absolute',
        inset: 0,
        zIndex: 60,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        background: 'rgba(11, 17, 32, 0.82)',
        backdropFilter: 'blur(6px)'
      }}
    >
      <div
        className="webgl-recovery-card"
        style={{
          maxWidth: '460px',
          width: '100%',
          padding: '20px',
          borderRadius: 'var(--radius-md, 8px)',
          background: 'var(--bg-card, #161B22)',
          border: '1px solid var(--border-default, rgba(148, 163, 184, 0.28))',
          boxShadow: '0 16px 40px rgba(1, 4, 9, 0.65)',
          color: 'var(--text-primary, #E6EDF3)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
          <AlertTriangle size={18} color="#F59E0B" style={{ flexShrink: 0 }} aria-hidden="true" />
          <h4
            style={{
              margin: 0,
              fontSize: '14px',
              fontWeight: 600,
              color: 'var(--text-primary, #E6EDF3)'
            }}
          >
            {viewLabel} Unavailable: Graphics Context Lost
          </h4>
        </div>
        <p
          style={{
            margin: '0 0 14px 0',
            fontSize: '12px',
            lineHeight: 1.55,
            color: 'var(--text-secondary, #94A3B8)'
          }}
        >
          The WebGL graphics context was interrupted by a display driver reset or device sleep.
          The canvas is temporarily unavailable and will rebuild automatically without a page reload once graphics hardware restores.
        </p>
        {onRebuild && (
          <button
            type="button"
            onClick={onRebuild}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '7px 12px',
              borderRadius: 'var(--radius-sm, 6px)',
              background: 'var(--color-primary-base, #0284C7)',
              color: '#FFFFFF',
              border: 'none',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <RotateCcw size={13} aria-hidden="true" />
            <span>Rebuild {viewLabel}</span>
          </button>
        )}
      </div>
    </div>
  );
};
