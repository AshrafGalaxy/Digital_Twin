import React, { useRef, useState, useCallback } from 'react';

interface SpotlightTiltCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  spotlightColor?: string;
  maxTilt?: number;
  enableTilt?: boolean;
}

/**
 * Executive-grade interactive card featuring cursor-following ambient spotlight
 * and micro 3D perspective tilt. Engineered for minimal overhead and zero React re-render churn.
 */
export const SpotlightTiltCard: React.FC<SpotlightTiltCardProps> = ({
  children,
  className = '',
  spotlightColor = 'rgba(56, 189, 248, 0.08)',
  maxTilt = 2.4,
  enableTilt = true,
  style,
  ...rest
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);

  const handlePointerMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      const card = cardRef.current;
      if (!card) return;

      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      card.style.setProperty('--spotlight-x', `${x}px`);
      card.style.setProperty('--spotlight-y', `${y}px`);

      if (enableTilt) {
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const percentX = (x - centerX) / centerX;
        const percentY = (y - centerY) / centerY;

        const tiltX = -percentY * maxTilt;
        const tiltY = percentX * maxTilt;

        card.style.setProperty('--card-rotate-x', `${tiltX.toFixed(2)}deg`);
        card.style.setProperty('--card-rotate-y', `${tiltY.toFixed(2)}deg`);
      }
    },
    [enableTilt, maxTilt]
  );

  const handlePointerEnter = useCallback(() => {
    setIsHovered(true);
  }, []);

  const handlePointerLeave = useCallback(() => {
    setIsHovered(false);
    const card = cardRef.current;
    if (!card) return;

    card.style.setProperty('--card-rotate-x', '0deg');
    card.style.setProperty('--card-rotate-y', '0deg');
  }, []);

  return (
    <div
      ref={cardRef}
      className={`spotlight-tilt-card ${isHovered ? 'is-hovered' : ''} ${className}`}
      onPointerMove={handlePointerMove}
      onPointerEnter={handlePointerEnter}
      onPointerLeave={handlePointerLeave}
      style={
        {
          ...style,
          '--spotlight-color': spotlightColor,
        } as React.CSSProperties
      }
      {...rest}
    >
      {/* Specular Radial Spotlight Beam Layer */}
      <div className="spotlight-radial-beam" aria-hidden="true" />
      {/* Specular 1px Border Illumination Layer */}
      <div className="spotlight-border-beam" aria-hidden="true" />
      {children}
    </div>
  );
};
