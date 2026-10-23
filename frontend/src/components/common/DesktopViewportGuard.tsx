import React, { useState, useEffect } from 'react';
import { Monitor, Maximize2 } from 'lucide-react';

interface DesktopViewportGuardProps {
  minWidth?: number;
}

export const DesktopViewportGuard: React.FC<DesktopViewportGuardProps> = ({
  minWidth = 1024
}) => {
  const [isSmallScreen, setIsSmallScreen] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.innerWidth < minWidth;
  });
  const [isDismissed, setIsDismissed] = useState<boolean>(false);

  useEffect(() => {
    const handleResize = () => {
      const small = window.innerWidth < minWidth;
      setIsSmallScreen(small);
      // Reset dismissal if window is expanded past threshold and then shrunk again
      if (!small) {
        setIsDismissed(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsDismissed(true);
      }
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [minWidth]);

  const handleRequestFullscreen = async () => {
    try {
      if (!document.fullscreenElement) {
        if (document.documentElement.requestFullscreen) {
          await document.documentElement.requestFullscreen();
        } else if ((document.documentElement as any).webkitRequestFullscreen) {
          await (document.documentElement as any).webkitRequestFullscreen();
        } else if ((document.documentElement as any).msRequestFullscreen) {
          await (document.documentElement as any).msRequestFullscreen();
        }
      }
    } catch (err) {
      console.warn('Fullscreen request rejected or not supported by browser:', err);
    }
  };

  if (!isSmallScreen || isDismissed) {
    return null;
  }

  return (
    <aside
      className="desktop-viewport-guard"
      role="dialog"
      aria-modal="true"
      aria-label="Display Viewport Notice"
    >
      <div className="viewport-guard-backdrop" />
      <div className="viewport-guard-card">
        <div className="viewport-guard-icon-container">
          <div className="viewport-guard-icon-circle">
            <Monitor size={28} className="viewport-guard-icon" />
          </div>
        </div>

        <h2 className="viewport-guard-title">
          Switch to Fullscreen for the Best Experience
        </h2>

        <p className="viewport-guard-desc">
          This platform is designed for interactive maps, live telemetry feeds, and dense analytics dashboards. In a smaller window, the controls and data views will feel cramped and hard to read.
        </p>

        <div className="viewport-guard-actions">
          <button
            type="button"
            className="viewport-fullscreen-btn"
            onClick={handleRequestFullscreen}
          >
            <Maximize2 size={15} />
            <span>Switch to Fullscreen</span>
          </button>

          <button
            type="button"
            className="viewport-override-btn"
            onClick={() => setIsDismissed(true)}
          >
            Continue with smaller window
          </button>
        </div>

        <div className="viewport-guard-footer">
          <Maximize2 size={13} className="viewport-footer-icon" />
          <span>Tip: Press F11 for fullscreen, or press Esc to exit or dismiss at any time.</span>
        </div>
      </div>
    </aside>
  );
};
