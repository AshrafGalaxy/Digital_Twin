import React from 'react';

interface DigitalTwinLogoProps {
  size?: number;
  className?: string;
  style?: React.CSSProperties;
  glow?: boolean;
}

export const DigitalTwinLogo: React.FC<DigitalTwinLogoProps> = ({
  size = 22,
  className = '',
  style = {},
  glow = false
}) => {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 512 512"
      width={size}
      height={size}
      className={`digital-twin-logo ${className}`}
      style={{
        flexShrink: 0,
        display: 'inline-block',
        verticalAlign: 'middle',
        filter: glow ? 'drop-shadow(0 0 8px rgba(47, 129, 247, 0.6))' : undefined,
        borderRadius: '50%',
        ...style
      }}
      aria-label="Digital Twin Platform Logo"
    >
      {/* Gradient & Glow Filter Defs */}
      <defs>
        <linearGradient id="dtLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38BDF8" />
          <stop offset="100%" stopColor="#2F81F7" />
        </linearGradient>
      </defs>

      {/* Sleek Dark Tech Badge Container */}
      <circle cx="256" cy="256" r="238" fill="rgba(22, 27, 34, 0.95)" stroke="rgba(56, 189, 248, 0.35)" strokeWidth="12" />

      {/* Refined Telemetry Waveform Glyph */}
      <path
        d="M 457 224
           A 204 204 0 0 0 68 177
           C 56 204, 68 230, 110 230
           L 180 230
           L 230 116
           L 282 396
           L 332 282
           L 402 282
           C 444 282, 456 308, 444 335
           A 204 204 0 0 1 55 288"
        fill="none"
        stroke="url(#dtLogoGrad)"
        strokeWidth="24"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

export default DigitalTwinLogo;
