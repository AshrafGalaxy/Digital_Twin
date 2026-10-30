import { Component, ErrorInfo, ReactNode } from 'react';
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
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error(`[ErrorBoundary] Captured exception in ${this.props.componentName || 'component'}:`, error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
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
          style={{
            margin: 'var(--space-3, 12px) 0',
            padding: 'var(--space-4, 16px)',
            borderRadius: 'var(--radius-md, 8px)',
            background: 'var(--bg-surface-elevated, #161B22)',
            border: '1px solid var(--border-color, rgba(255, 255, 255, 0.1))',
            boxShadow: 'var(--shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.3))'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <AlertTriangle size={18} color="#F59E0B" style={{ flexShrink: 0 }} />
            <h4
              style={{
                margin: 0,
                fontSize: '13px',
                fontWeight: 600,
                color: 'var(--color-text, #E6EDF3)'
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
              color: 'var(--color-text-secondary, #8B949E)'
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
            <RotateCcw size={13} />
            <span>Recover Component</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
