import React from 'react';

export const ConformalBandsAsset: React.FC = () => {
  return (
    <div className="bento-visual-frame">
      <svg
        viewBox="0 0 360 160"
        className="bento-svg-stage"
        preserveAspectRatio="xMidYMid meet"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Conformal Ribbon Gradients */}
          <linearGradient id="band90Grad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#818CF8" stopOpacity="0.22" />
            <stop offset="100%" stopColor="#6366F1" stopOpacity="0.06" />
          </linearGradient>

          <linearGradient id="band80Grad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#A78BFA" stopOpacity="0.38" />
            <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.12" />
          </linearGradient>

          <linearGradient id="medianSplineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#38BDF8" />
            <stop offset="50%" stopColor="#A78BFA" />
            <stop offset="100%" stopColor="#F472B6" />
          </linearGradient>

          <filter id="conformalGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Ambient Radial Violet Bloom */}
        <radialGradient id="violetBloom" cx="65%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.14" />
          <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.0" />
        </radialGradient>
        <circle cx="230" cy="80" r="130" fill="url(#violetBloom)" pointerEvents="none" />

        {/* Horizon Guides (t+15m, t+30m projection lines) */}
        <line x1="120" y1="20" x2="120" y2="140" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" strokeDasharray="4 4" />
        <line x1="240" y1="20" x2="240" y2="140" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" strokeDasharray="4 4" />

        {/* 90% Outer Conformal Envelope Band */}
        <path
          d="M 20 80
             C 80 72, 140 45, 220 32
             C 270 24, 310 18, 340 15
             L 340 145
             C 310 142, 270 136, 220 128
             C 140 115, 80 88, 20 80 Z"
          fill="url(#band90Grad)"
        />
        {/* 90% Boundary Contour Lines */}
        <path
          d="M 20 80 C 80 72, 140 45, 220 32 C 270 24, 310 18, 340 15"
          fill="none"
          stroke="#818CF8"
          strokeWidth="1.2"
          strokeDasharray="4 3"
          opacity="0.6"
        />
        <path
          d="M 20 80 C 80 88, 140 115, 220 128 C 270 136, 310 142, 340 145"
          fill="none"
          stroke="#818CF8"
          strokeWidth="1.2"
          strokeDasharray="4 3"
          opacity="0.6"
        />

        {/* 80% Inner Conformal Ribbon Band */}
        <path
          d="M 20 80
             C 80 74, 140 56, 220 48
             C 270 42, 310 38, 340 35
             L 340 125
             C 310 122, 270 118, 220 112
             C 140 104, 80 86, 20 80 Z"
          fill="url(#band80Grad)"
        />
        <path
          d="M 20 80 C 80 74, 140 56, 220 48 C 270 42, 310 38, 340 35"
          fill="none"
          stroke="#A78BFA"
          strokeWidth="1.2"
          opacity="0.75"
        />
        <path
          d="M 20 80 C 80 86, 140 104, 220 112 C 270 118, 310 122, 340 125"
          fill="none"
          stroke="#A78BFA"
          strokeWidth="1.2"
          opacity="0.75"
        />

        {/* Central Luminous Point Forecast Spline */}
        <path
          d="M 20 80
             C 80 80, 140 70, 220 80
             C 270 86, 310 80, 340 80"
          fill="none"
          stroke="url(#medianSplineGrad)"
          strokeWidth="2.8"
          strokeLinecap="round"
          filter="url(#conformalGlow)"
        />

        {/* Calibration Scatter Ground-Truth Points */}
        <circle cx="65" cy="78" r="3" fill="#38BDF8" filter="url(#conformalGlow)" />
        <circle cx="105" cy="73" r="2.5" fill="#38BDF8" opacity="0.9" />
        <circle cx="150" cy="72" r="3" fill="#A78BFA" filter="url(#conformalGlow)" />
        <circle cx="190" cy="76" r="2.5" fill="#A78BFA" opacity="0.9" />
        <circle cx="260" cy="84" r="3" fill="#F472B6" filter="url(#conformalGlow)" />
        <circle cx="300" cy="81" r="2.5" fill="#F472B6" opacity="0.9" />

        {/* Key Forecast Vertices */}
        <g transform="translate(120, 71)">
          <circle r="10" fill="none" stroke="#38BDF8" strokeWidth="1" opacity="0.4" />
          <circle r="4" fill="#38BDF8" filter="url(#conformalGlow)" />
        </g>

        <g transform="translate(240, 81)">
          <circle r="10" fill="none" stroke="#A78BFA" strokeWidth="1" opacity="0.4" />
          <circle r="4" fill="#A78BFA" filter="url(#conformalGlow)" />
        </g>
      </svg>
    </div>
  );
};
