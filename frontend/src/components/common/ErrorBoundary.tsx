import { Component, ErrorInfo, Fragment, ReactNode } from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  componentName?: string;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  resetCount: number;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      resetCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error(`[ErrorBoundary] Captured exception in ${this.props.componentName || 'component'}:`, error, errorInfo);
  }

  handleReset = (): void => {
    this.setState((prev) => ({
      hasError: false,
      error: null,
      resetCount: prev.resetCount + 1
    }));
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const compTitle = this.props.componentName
        ? `${this.props.componentName} Diagnostic State`
        : 'Component Diagnostic State';

      return (
        <div
          role="alert"
          className="error-boundary-fallback"
          style={{
            position: 'relative',
            zIndex: 70,
            margin: 'var(--space-4, 16px)',
            maxWidth: '540px',
            padding: 'var(--space-4, 16px)',
            borderRadius: 'var(--radius-md, 8px)',
            background: 'var(--bg-card, #161B22)',
            border: '1px solid var(--border-default, rgba(148, 163, 184, 0.25))',
            boxShadow: 'var(--shadow-lg, 0 14px 38px rgba(1, 4, 9, 0.65))'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <AlertTriangle size={18} color="#F59E0B" style={{ flexShrink: 0 }} aria-hidden="true" />
            <h4
              style={{
                margin: 0,
                fontSize: '13px',
                fontWeight: 600,
                color: 'var(--text-primary, #E6EDF3)'
              }}
            >
              {compTitle}
            </h4>
          </div>
          <p
            style={{
              margin: '0 0 12px 0',
              fontSize: '12px',
              lineHeight: 1.5,
              color: 'var(--text-secondary, #8B949E)'
            }}
          >
            An isolated exception occurred while rendering this module. The rest of the platform remains fully operational.
          </p>
          {this.state.error?.message && (
            <code
              style={{
                display: 'block',
                padding: '6px 10px',
                marginBottom: '12px',
                borderRadius: 'var(--radius-sm, 4px)',
                background: 'rgba(0, 0, 0, 0.25)',
                fontSize: '11px',
                color: '#EF4444',
                wordBreak: 'break-all'
              }}
            >
              {this.state.error.message}
            </code>
          )}
          <button
            type="button"
            onClick={this.handleReset}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: 'var(--radius-sm, 4px)',
              background: 'var(--color-primary-base, #0284C7)',
              color: '#FFFFFF',
              border: 'none',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <RotateCcw size={13} aria-hidden="true" />
            <span>Recover Component</span>
          </button>
        </div>
      );
    }

    return <Fragment key={this.state.resetCount}>{this.props.children}</Fragment>;
  }
}
