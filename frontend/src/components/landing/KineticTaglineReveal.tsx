import React, { useRef, useState, useEffect } from 'react';
import { motion, useScroll, useTransform, useSpring, MotionValue } from 'framer-motion';
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

interface KineticWordProps {
  word: string;
  index: number;
  total: number;
  progress: MotionValue<number>;
}

const KineticWord: React.FC<KineticWordProps> = ({ word, index, total, progress }) => {
  // Overlapping progressive window for each word across scroll travel
  const start = (index / total) * 0.82;
  const end = Math.min(start + 0.18, 1.0);

  const opacity = useTransform(progress, [start, end], [0.22, 1.0]);
  const color = useTransform(progress, [start, end], ['#475569', '#F8FAFC']);
  const y = useTransform(progress, [start, end], [3, 0]);

  return (
    <motion.span
      className="tagline-word"
      style={{ opacity, color, y }}
    >
      {word}
    </motion.span>
  );
};

export const KineticTaglineReveal: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Measure section progress as it scrolls through the active viewing zone of the viewport
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start 0.88', 'start 0.24']
  });

  // Physics spring smoothing to turn discrete mouse wheel notches into liquid-smooth continuous flow
  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 120,
    damping: 24,
    mass: 0.15,
    restDelta: 0.001
  });

  const [progressPercent, setProgressPercent] = useState<number>(0);

  useEffect(() => {
    const unsubscribe = smoothProgress.on('change', (latest) => {
      const pct = Math.min(100, Math.max(0, Math.round(latest * 100)));
      setProgressPercent(pct);
    });
    return () => unsubscribe();
  }, [smoothProgress]);

  const isTagActive = progressPercent > 0;
  const isVerified = progressPercent >= 98;

  return (
    <section className="tagline-reveal-track" ref={containerRef}>
      <div className="tagline-sticky-wrapper">
        <div className="tagline-reveal-inner">
          {/* Crisp, Standard Governance Philosophy Tag */}
          <div className={`kinetic-eyebrow font-mono ${isTagActive ? 'active' : ''}`}>
            <span className={`eyebrow-indicator ${isTagActive ? 'active' : ''}`} />
            <span className="eyebrow-title">GOVERNANCE PHILOSOPHY</span>
            <span className="eyebrow-sep">/</span>
            <span className="eyebrow-state font-mono">
              {isVerified ? (
                <span className="eyebrow-verified">
                  <CheckCircle2 size={12} />
                  <span>VERIFIED</span>
                </span>
              ) : (
                <span>{progressPercent}% ILLUMINATED</span>
              )}
            </span>
          </div>

          {/* Silky Continuous Word-by-Word Illuminated Headline */}
          <h2 className="tagline-heading" aria-label={TAGLINE_WORDS.join(' ')}>
            {TAGLINE_WORDS.map((word, idx) => (
              <KineticWord
                key={idx}
                word={word}
                index={idx}
                total={TAGLINE_WORDS.length}
                progress={smoothProgress}
              />
            ))}
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
