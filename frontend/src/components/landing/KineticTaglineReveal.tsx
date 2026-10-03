import React, { useEffect, useRef, useState } from 'react';
import { ShieldCheck, Database, Sliders, Sparkles } from 'lucide-react';

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
  const [activeWordIndex, setActiveWordIndex] = useState<number>(-1);
  const [scrollProgress, setScrollProgress] = useState<number>(0);

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;

    const handleScroll = () => {
      const rect = track.getBoundingClientRect();
      const windowHeight = window.innerHeight;

      // Start illuminating when top enters upper viewport
      const startOffset = windowHeight * 0.45;
      const totalScrollDistance = rect.height - windowHeight * 0.35;
      const currentScroll = startOffset - rect.top;

      if (currentScroll <= 0) {
        setActiveWordIndex(-1);
        setScrollProgress(0);
      } else {
        const progress = Math.min(Math.max(currentScroll / totalScrollDistance, 0), 1);
        setScrollProgress(progress);

        const wordCount = TAGLINE_WORDS.length;
        // Map 0..1 progress to word indices -1..wordCount-1
        const targetIndex = Math.min(Math.floor(progress * (wordCount + 1)) - 1, wordCount - 1);
        setActiveWordIndex(targetIndex);
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('resize', handleScroll, { passive: true });
    handleScroll();

    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleScroll);
    };
  }, []);

  const isTagGlowing = activeWordIndex >= 0;
  const progressPercent = Math.round(scrollProgress * 100);

  return (
    <section className="tagline-reveal-track" ref={trackRef}>
      <div className="tagline-sticky-wrapper">
        <div className="tagline-reveal-inner">
          {/* Glowing Governance Philosophy Tag */}
          <div
            className={`tagline-eyebrow font-mono ${isTagGlowing ? 'glowing' : ''}`}
            style={{
              borderColor: isTagGlowing ? '#38BDF8' : undefined,
              boxShadow: isTagGlowing
                ? `0 0 24px rgba(56, 189, 248, ${0.35 + scrollProgress * 0.45}), 0 0 48px rgba(56, 189, 248, 0.25)`
                : undefined
            }}
          >
            <span className={`shimmer-pulse-gem ${isTagGlowing ? 'active-gem' : ''}`} />
            <span className="eyebrow-title">GOVERNANCE PHILOSOPHY</span>
            <span className="eyebrow-sep">/</span>
            <span className="eyebrow-state font-mono">
              {progressPercent === 100 ? (
                <span className="flex items-center gap-1 text-emerald-400">
                  <Sparkles size={11} className="inline mr-1" />
                  VERIFIED
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
                  style={{
                    transitionDelay: `${Math.min(idx * 15, 120)}ms`
                  }}
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
