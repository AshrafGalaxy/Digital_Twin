import React from 'react';
import { Loader2 } from 'lucide-react';

interface ViewLoadingFallbackProps {
  label?: string;
}

export const ViewLoadingFallback: React.FC<ViewLoadingFallbackProps> = ({ label }) => {
  const displayLabel = label ? `Loading ${label}...` : 'Loading view...';

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: '100%',
        height: '100%',
        minHeight: '260px',
        padding: 'var(--space-6, 24px)',
        boxSizing: 'border-box'
      }}
    >
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 'var(--space-3, 12px)',
          padding: '14px 20px',
          borderRadius: 'var(--radius-md, 8px)',
          background: 'var(--color-surface, #0F172A)',
          border: '1px solid var(--color-border, #1E2736)',
          color: 'var(--color-text, #F8FAFC)',
          boxShadow: 'var(--shadow-md, 0 8px 24px rgba(0, 0, 0, 0.28))'
        }}
      >
        <Loader2
          size={18}
          aria-hidden="true"
          style={{
            color: 'var(--color-primary, #388BFD)',
            flexShrink: 0,
            animation: 'spin 0.9s linear infinite'
          }}
        />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span
            style={{
              fontSize: '13px',
              fontWeight: 600,
              color: 'var(--color-text, #F8FAFC)'
            }}
          >
            {displayLabel}
          </span>
          <span
            style={{
              fontSize: '11px',
              color: 'var(--text-muted, #CBD5E1)'
            }}
          >
            Initializing module chunk
          </span>
        </div>
      </div>
    </div>
  );
};
