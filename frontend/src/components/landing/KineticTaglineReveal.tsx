import React, { useEffect, useRef, useState, useCallback } from 'react';
import { ShieldCheck, Database, Sliders, CheckCircle2 } from 'lucide-react';

const TAGLINE_WORDS = [
  'Every',
  'urban',
  'recommendation',
  'backed',
  'by',
  'mathematical',
  'proof,',
  'conformal',
  'uncertainty',
  'bounds,',
  'and',
  'human-in-the-loop',
  'governance.'
];

export const KineticTaglineReveal: React.FC = () => {
  const trackRef = useRef<HTMLDivElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [activeWordIndex, setActiveWordIndex] = useState<number>(-1);
  const [scrollProgress, setScrollProgress] = useState<number>(0);

  const calculateProgress = useCallback(() => {
    const track = trackRef.current;
    const wrapper = wrapperRef.current;
    if (!track || !wrapper) return;

    const rect = track.getBoundingClientRect();
    const windowHeight = window.innerHeight;

    // The sticky wrapper docks at top: 14vh
    const topDock = windowHeight * 0.14;
    // Total distance the wrapper travels in sticky state
    const scrollRange = Math.max(rect.height - wrapper.offsetHeight, 100);
    // How much user has scrolled past the sticky docking threshold
    const currentScroll = topDock - rect.top;

    if (currentScroll <= 0) {
      setActiveWordIndex(-1);
      setScrollProgress(0);
    } else {
      const progress = Math.min(Math.max(currentScroll / scrollRange, 0), 1);
      setScrollProgress(progress);

      const wordCount = TAGLINE_WORDS.length;
      // Progressively light up words 0..12
      const targetIndex = Math.min(
        Math.floor(progress * (wordCount + 0.5)),
        wordCount - 1
      );
      setActiveWordIndex(targetIndex);
    }
  }, []);

  useEffect(() => {
    let rafId: number | null = null;
    const onScrollOrResize = () => {
      if (rafId) return;
      rafId = requestAnimationFrame(() => {
        calculateProgress();
        rafId = null;
      });
    };

    window.addEventListener('scroll', onScrollOrResize, { passive: true });
    window.addEventListener('resize', onScrollOrResize, { passive: true });
    document.addEventListener('scroll', onScrollOrResize, { passive: true });

    // Also attach to any scrollable parent element as fallback
    const track = trackRef.current;
    const listeners: HTMLElement[] = [];
    if (track) {
      let parent = track.parentElement;
      while (parent) {
        const overflowY = window.getComputedStyle(parent).overflowY;
        if (overflowY === 'auto' || overflowY === 'scroll') {
          parent.addEventListener('scroll', onScrollOrResize, { passive: true });
          listeners.push(parent);
        }
        parent = parent.parentElement;
      }
    }

    calculateProgress();

    return () => {
      window.removeEventListener('scroll', onScrollOrResize);
      window.removeEventListener('resize', onScrollOrResize);
      document.removeEventListener('scroll', onScrollOrResize);
      listeners.forEach((el) => el.removeEventListener('scroll', onScrollOrResize));
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, [calculateProgress]);

  const isTagActive = activeWordIndex >= 0;
  const progressPercent = Math.round(scrollProgress * 100);

  return (
    <section className="tagline-reveal-track" ref={trackRef}>
      <div className="tagline-sticky-wrapper" ref={wrapperRef}>
        <div className="tagline-reveal-inner">
          {/* Crisp, Unglowed Governance Philosophy Tag */}
          <div className={`kinetic-eyebrow font-mono ${isTagActive ? 'active' : ''}`}>
            <span className={`eyebrow-indicator ${isTagActive ? 'active' : ''}`} />
            <span className="eyebrow-title">GOVERNANCE PHILOSOPHY</span>
            <span className="eyebrow-sep">/</span>
            <span className="eyebrow-state font-mono">
              {progressPercent === 100 ? (
                <span className="eyebrow-verified">
                  <CheckCircle2 size={12} />
                  <span>VERIFIED</span>
                </span>
              ) : (
                <span>{progressPercent}% ILLUMINATED</span>
              )}
            </span>
          </div>

          {/* Word by word illuminated headline */}
          <h2 className="tagline-heading" aria-label={TAGLINE_WORDS.join(' ')}>
            {TAGLINE_WORDS.map((word, idx) => {
              const isLit = idx <= activeWordIndex;
              return (
                <span
                  key={idx}
                  className={`tagline-word ${isLit ? 'lit' : ''}`}
                >
                  {word}
                </span>
              );
            })}
          </h2>

          <p className="tagline-subtext">
            Eliminating black-box guesswork and unverified autonomous actuation from municipal traffic networks and commercial microgrids through rigorous empirical validation.
          </p>

          <div className="tagline-guarantee-strip font-mono">
            <div className="guarantee-pill">
              <Database size={13} color="var(--color-primary)" />
              <span>POSTGRESQL SYSTEM OF RECORD</span>
            </div>
            <div className="guarantee-pill">
              <Sliders size={13} color="var(--color-predicted)" />
              <span>CONFORMAL UNCERTAINTY CALIBRATION</span>
            </div>
            <div className="guarantee-pill">
              <ShieldCheck size={13} color="var(--color-success)" />
              <span>READ-ONLY NON-ACTUATION CONTRACT</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
