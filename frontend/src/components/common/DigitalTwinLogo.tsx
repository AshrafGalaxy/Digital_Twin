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
      {/* White Circular Container Badge */}
      <circle cx="256" cy="256" r="238" fill="#FFFFFF" stroke="#E2E8F0" strokeWidth="4" />

      {/* Single Continuous Solid Digital Twin Telemetry Glyph */}
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
        stroke="#1D4ED8"
        strokeWidth="34"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

export default DigitalTwinLogo;
