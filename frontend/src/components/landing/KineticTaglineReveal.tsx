import React, { useEffect, useRef, useState } from 'react';
import { ShieldCheck, Database, Sliders } from 'lucide-react';

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
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeWordIndex, setActiveWordIndex] = useState<number>(-1);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const handleScroll = () => {
      const rect = el.getBoundingClientRect();
      const windowHeight = window.innerHeight;

      // Calculate progress of section through the viewport
      const startTrigger = windowHeight * 0.85;
      const endTrigger = windowHeight * 0.25;
      const totalDistance = startTrigger - endTrigger;
      const currentPos = startTrigger - rect.top;

      if (currentPos <= 0) {
        setActiveWordIndex(-1);
      } else {
        const progress = Math.min(Math.max(currentPos / totalDistance, 0), 1);
        const wordCount = TAGLINE_WORDS.length;
        const targetIndex = Math.floor(progress * (wordCount + 1)) - 1;
        setActiveWordIndex(targetIndex);
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return (
    <section className="tagline-reveal-section" ref={containerRef}>
      <div className="tagline-reveal-inner">
        <div className="tagline-eyebrow font-mono">
          <span className="shimmer-pulse-gem" />
          <span>GOVERNANCE PHILOSOPHY</span>
        </div>

        <h2 className="tagline-heading" aria-label={TAGLINE_WORDS.join(' ')}>
          {TAGLINE_WORDS.map((word, idx) => {
            const isLit = idx <= activeWordIndex;
            return (
              <span
                key={idx}
                className={`tagline-word ${isLit ? 'lit' : ''}`}
                style={{
                  transitionDelay: `${idx * 15}ms`
                }}
              >
                {word}{' '}
              </span>
            );
          })}
        </h2>

        <p className="tagline-subtext">
          Eliminating black-box guesswork and unverified actuation from municipal traffic networks and commercial microgrids through rigorous empirical validation.
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
    </section>
  );
};
