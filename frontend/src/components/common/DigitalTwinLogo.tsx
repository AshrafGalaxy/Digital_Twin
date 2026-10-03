import React from 'react';

interface DigitalTwinLogoProps {
  size?: number;
  className?: string;
  style?: React.CSSProperties;
}

export const DigitalTwinLogo: React.FC<DigitalTwinLogoProps> = ({
  size = 22,
  className = '',
  style = {}
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
        borderRadius: '50%',
        ...style
      }}
      aria-label="Digital Twin Platform Logo"
    >
      {/* White Circular Container Badge */}
      <circle cx="256" cy="256" r="238" fill="#FFFFFF" stroke="#E2E8F0" strokeWidth="4" />

      {/* Telemetry Waveform Glyph */}
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
        strokeWidth="32"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

export default DigitalTwinLogo;
