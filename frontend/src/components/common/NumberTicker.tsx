import React, { useEffect, useState, useRef } from 'react';

interface NumberTickerProps {
  value: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  duration?: number;
  className?: string;
}

/**
 * Lightweight, zero-dependency rolling number ticker for high-impact metric rollups.
 * Runs on requestAnimationFrame with a calibrated ease-out cubic curve upon intersection.
 */
export const NumberTicker: React.FC<NumberTickerProps> = ({
  value,
  prefix = '',
  suffix = '',
  decimals = 0,
  duration = 1600,
  className = ''
}) => {
  const [displayValue, setDisplayValue] = useState<number>(0);
  const containerRef = useRef<HTMLSpanElement>(null);
  const hasAnimated = useRef<boolean>(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasAnimated.current) {
            hasAnimated.current = true;
            const startTime = performance.now();

            const step = (now: number) => {
              const elapsed = now - startTime;
              const progress = Math.min(elapsed / duration, 1);
              // Smooth ease-out cubic curve
              const easeOut = 1 - Math.pow(1 - progress, 3);
              const current = easeOut * value;
              setDisplayValue(current);

              if (progress < 1) {
                requestAnimationFrame(step);
              } else {
                setDisplayValue(value);
              }
            };

            requestAnimationFrame(step);
          }
        });
      },
      { threshold: 0.15 }
    );

    const el = containerRef.current;
    if (el) {
      observer.observe(el);
    }

    return () => {
      if (el) observer.unobserve(el);
      observer.disconnect();
    };
  }, [value, duration]);

  const formatted =
    decimals > 0
      ? displayValue.toFixed(decimals)
      : Math.round(displayValue).toLocaleString();

  return (
    <span ref={containerRef} className={`number-ticker ${className}`}>
      {prefix}
      {formatted}
      {suffix}
    </span>
  );
};
