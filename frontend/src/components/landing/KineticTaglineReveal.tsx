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
  // Cascading continuous window with generous 24% soft overlap
  const start = (index / (total + 1.5)) * 0.78;
  const end = Math.min(start + 0.24, 1.0);

  // Hardware-accelerated GPU opacity and subtle 2px micro-glide
  const opacity = useTransform(progress, [start, end], [0, 1]);
  const y = useTransform(progress, [start, end], [2, 0]);

  return (
    <span className="tagline-word-wrapper">
      {/* Base muted word in low-contrast slate */}
      <span className="tagline-word-base" aria-hidden="true">
        {word}
      </span>
      {/* Illuminated word in pure white, smoothly blended on the compositor thread */}
      <motion.span
        className="tagline-word-lit"
        aria-hidden="true"
        style={{ opacity, y }}
      >
        {word}
      </motion.span>
    </span>
  );
};

export const KineticTaglineReveal: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Measure section progress across a generous, comfortable viewing window
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start 0.92', 'end 0.20']
  });

  // Soft hydraulic damping spring to convert mouse wheel detents into continuous liquid flow
  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 75,
    damping: 26,
    mass: 0.45,
    restDelta: 0.0005
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
  const isVerified = progressPercent >= 95;

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

          {/* Silky Continuous Dual-Layer Illuminated Headline */}
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
