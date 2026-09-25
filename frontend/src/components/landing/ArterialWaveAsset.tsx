import React from 'react';

export const ArterialWaveAsset: React.FC = () => {
  return (
    <div className="bento-visual-frame">
      <svg
        viewBox="0 0 760 180"
        className="bento-svg-stage"
        preserveAspectRatio="xMidYMid meet"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Wave Area Gradients */}
          <linearGradient id="artWaveAreaGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.25" />
            <stop offset="50%" stopColor="#2F81F7" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#0B0F17" stopOpacity="0.0" />
          </linearGradient>

          <linearGradient id="artWaveSecAreaGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#10B981" stopOpacity="0.16" />
            <stop offset="60%" stopColor="#059669" stopOpacity="0.04" />
            <stop offset="100%" stopColor="#0B0F17" stopOpacity="0.0" />
          </linearGradient>

          {/* Stroke Glow Gradients */}
          <linearGradient id="artNeonLine" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#38BDF8" />
            <stop offset="35%" stopColor="#2F81F7" />
            <stop offset="70%" stopColor="#818CF8" />
            <stop offset="100%" stopColor="#38BDF8" />
          </linearGradient>

          <linearGradient id="artSyncLine" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10B981" />
            <stop offset="50%" stopColor="#34D399" />
            <stop offset="100%" stopColor="#10B981" />
          </linearGradient>

          {/* Subtle Ambient Grid */}
          <pattern id="artGrid" width="40" height="30" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 30" fill="none" stroke="rgba(255, 255, 255, 0.025)" strokeWidth="0.8" />
          </pattern>

          {/* High-Performance Neon Glow */}
          <filter id="artGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Ambient Grid Canvas */}
        <rect width="760" height="180" fill="url(#artGrid)" />

        {/* Soft Radial Backlight */}
        <radialGradient id="artCenterBloom" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.12" />
          <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.0" />
        </radialGradient>
        <circle cx="380" cy="90" r="220" fill="url(#artCenterBloom)" pointerEvents="none" />

        {/* Horizontal Baseline Reference Guide */}
        <line x1="40" y1="140" x2="720" y2="140" stroke="rgba(255, 255, 255, 0.08)" strokeWidth="1" strokeDasharray="6 4" />
        <line x1="40" y1="60" x2="720" y2="60" stroke="rgba(56, 189, 248, 0.12)" strokeWidth="1" strokeDasharray="4 6" />

        {/* Secondary Harmonized Green Progression Wave (Area + Line) */}
        <path
          d="M 40 180
             L 40 115
             C 120 110, 180 75, 250 82
             C 320 89, 380 135, 470 125
             C 560 115, 620 70, 720 80
             L 720 180 Z"
          fill="url(#artWaveSecAreaGrad)"
        />
        <path
          d="M 40 115
             C 120 110, 180 75, 250 82
             C 320 89, 380 135, 470 125
             C 560 115, 620 70, 720 80"
          fill="none"
          stroke="url(#artSyncLine)"
          strokeWidth="1.8"
          strokeDasharray="5 3"
          opacity="0.85"
        />

        {/* Primary Velocity Wave (Area Fill) */}
        <path
          d="M 40 180
             L 40 100
             C 110 108, 170 42, 250 48
             C 330 54, 390 120, 480 110
             C 560 100, 630 46, 720 56
             L 720 180 Z"
          fill="url(#artWaveAreaGrad)"
        />

        {/* Primary Velocity Wave Glowing Neon Stroke */}
        <path
          d="M 40 100
             C 110 108, 170 42, 250 48
             C 330 54, 390 120, 480 110
             C 560 100, 630 46, 720 56"
          fill="none"
          stroke="url(#artNeonLine)"
          strokeWidth="3"
          strokeLinecap="round"
          filter="url(#artGlow)"
        />

        {/* Coordinated Signal Beacon 1 (Viman Nagar Chowk) */}
        <g transform="translate(250, 48)">
          <circle r="22" fill="none" stroke="#38BDF8" strokeWidth="1" opacity="0.25" strokeDasharray="3 3">
            <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="20s" repeatCount="indefinite" />
          </circle>
          <circle r="12" fill="none" stroke="#38BDF8" strokeWidth="1.2" opacity="0.6" />
          <circle r="5" fill="#38BDF8" filter="url(#artGlow)" />
          <line x1="0" y1="5" x2="0" y2="92" stroke="rgba(56, 189, 248, 0.25)" strokeWidth="1" strokeDasharray="2 3" />
        </g>

        {/* Central Midpoint Flow Node */}
        <g transform="translate(480, 110)">
          <circle r="16" fill="none" stroke="#818CF8" strokeWidth="1" opacity="0.3" />
          <circle r="4.5" fill="#818CF8" filter="url(#artGlow)" />
          <line x1="0" y1="5" x2="0" y2="30" stroke="rgba(129, 140, 248, 0.25)" strokeWidth="1" strokeDasharray="2 3" />
        </g>

        {/* Coordinated Signal Beacon 2 (Somnath Nagar Chowk) */}
        <g transform="translate(720, 56)">
          <circle r="22" fill="none" stroke="#38BDF8" strokeWidth="1" opacity="0.25" strokeDasharray="3 3">
            <animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="20s" repeatCount="indefinite" />
          </circle>
          <circle r="12" fill="none" stroke="#38BDF8" strokeWidth="1.2" opacity="0.6" />
          <circle r="5" fill="#38BDF8" filter="url(#artGlow)" />
          <line x1="0" y1="5" x2="0" y2="84" stroke="rgba(56, 189, 248, 0.25)" strokeWidth="1" strokeDasharray="2 3" />
        </g>

        {/* Moving Flow Particles along Wave Path */}
        <circle cx="150" cy="65" r="3" fill="#FFFFFF" filter="url(#artGlow)" opacity="0.9" />
        <circle cx="360" cy="85" r="2.5" fill="#38BDF8" filter="url(#artGlow)" opacity="0.8" />
        <circle cx="610" cy="68" r="3" fill="#FFFFFF" filter="url(#artGlow)" opacity="0.9" />
        <circle cx="670" cy="52" r="2" fill="#34D399" opacity="0.75" />
      </svg>
    </div>
  );
};
