import React from 'react';

export const EnergyCurveAsset: React.FC = () => {
  return (
    <div className="bento-visual-frame">
      <svg
        viewBox="0 0 360 160"
        className="bento-svg-stage"
        preserveAspectRatio="xMidYMid meet"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="energyCurveFill" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.32" />
            <stop offset="50%" stopColor="#D97706" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#0B0F17" stopOpacity="0.0" />
          </linearGradient>

          <linearGradient id="energySplineGlow" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#F59E0B" />
            <stop offset="45%" stopColor="#EF4444" />
            <stop offset="70%" stopColor="#10B981" />
            <stop offset="100%" stopColor="#38BDF8" />
          </linearGradient>

          <linearGradient id="towerFacetGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="rgba(47, 129, 247, 0.25)" />
            <stop offset="100%" stopColor="rgba(30, 41, 59, 0.4)" />
          </linearGradient>

          <filter id="energyBloom" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Ambient Radial Backlight for Energy Pulse */}
        <radialGradient id="energyBackBloom" cx="60%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.12" />
          <stop offset="100%" stopColor="#F59E0B" stopOpacity="0.0" />
        </radialGradient>
        <circle cx="220" cy="80" r="120" fill="url(#energyBackBloom)" pointerEvents="none" />

        {/* 15-Minute Load Frequency Bar Spectrum along Base */}
        <g opacity="0.35">
          <rect x="25" y="132" width="6" height="14" rx="2" fill="#F59E0B" />
          <rect x="37" y="126" width="6" height="20" rx="2" fill="#F59E0B" />
          <rect x="49" y="118" width="6" height="28" rx="2" fill="#F59E0B" />
          <rect x="61" y="105" width="6" height="41" rx="2" fill="#F59E0B" />
          <rect x="73" y="90" width="6" height="56" rx="2" fill="#EF4444" />
          <rect x="85" y="82" width="6" height="64" rx="2" fill="#EF4444" />
          <rect x="97" y="88" width="6" height="58" rx="2" fill="#10B981" />
          <rect x="109" y="96" width="6" height="50" rx="2" fill="#10B981" />
          <rect x="121" y="104" width="6" height="42" rx="2" fill="#10B981" />
          <rect x="133" y="112" width="6" height="34" rx="2" fill="#38BDF8" />
          <rect x="145" y="120" width="6" height="26" rx="2" fill="#38BDF8" />
          <rect x="157" y="128" width="6" height="18" rx="2" fill="#38BDF8" />
        </g>

        {/* Shaving Window Highlight Zone */}
        <rect x="80" y="35" width="70" height="110" rx="6" fill="rgba(16, 185, 129, 0.06)" stroke="rgba(16, 185, 129, 0.25)" strokeDasharray="3 3" />

        {/* Threshold Feeder Ceiling Guide */}
        <line x1="20" y1="52" x2="200" y2="52" stroke="rgba(239, 68, 68, 0.4)" strokeWidth="1" strokeDasharray="4 4" />

        {/* Diurnal Thermal Load Area Fill */}
        <path
          d="M 20 146
             L 20 135
             C 50 130, 70 85, 100 68
             C 120 56, 140 86, 170 78
             C 200 70, 230 115, 270 120
             L 270 146 Z"
          fill="url(#energyCurveFill)"
        />

        {/* Glowing Dynamic Load Stroke */}
        <path
          d="M 20 135
             C 50 130, 70 85, 100 68
             C 120 56, 140 86, 170 78
             C 200 70, 230 115, 270 120"
          fill="none"
          stroke="url(#energySplineGlow)"
          strokeWidth="2.5"
          strokeLinecap="round"
          filter="url(#energyBloom)"
        />

        {/* Isometric Commercial Facility Silhouette (Phoenix Marketcity) */}
        <g transform="translate(230, 32)">
          {/* Main Tower Primary Facet */}
          <polygon points="40,25 90,0 90,85 40,110" fill="url(#towerFacetGrad)" stroke="#38BDF8" strokeWidth="1" opacity="0.8" />
          {/* Left Wing Facet */}
          <polygon points="0,45 40,25 40,110 0,130" fill="rgba(15, 23, 42, 0.85)" stroke="#30363D" strokeWidth="1" />
          {/* Top Roof Slab */}
          <polygon points="40,25 0,45 50,20 90,0" fill="rgba(56, 189, 248, 0.2)" stroke="#38BDF8" strokeWidth="1" />

          {/* Glowing Floor Slabs */}
          <line x1="40" y1="45" x2="90" y2="20" stroke="rgba(56, 189, 248, 0.5)" strokeWidth="1" />
          <line x1="40" y1="65" x2="90" y2="40" stroke="rgba(56, 189, 248, 0.5)" strokeWidth="1" />
          <line x1="40" y1="85" x2="90" y2="60" stroke="rgba(56, 189, 248, 0.5)" strokeWidth="1" />
          <line x1="0" y1="65" x2="40" y2="45" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="0.8" />
          <line x1="0" y1="85" x2="40" y2="65" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="0.8" />
          <line x1="0" y1="105" x2="40" y2="85" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="0.8" />

          {/* Rooftop Central Chiller Plant Node */}
          <circle cx="45" cy="22" r="14" fill="none" stroke="#10B981" strokeWidth="1" opacity="0.3">
            <animate attributeName="r" values="12;18;12" dur="3s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.4;0.1;0.4" dur="3s" repeatCount="indefinite" />
          </circle>
          <circle cx="45" cy="22" r="4.5" fill="#10B981" filter="url(#energyBloom)" />
          <line x1="45" y1="22" x2="45" y2="0" stroke="#10B981" strokeWidth="1.2" />
          <circle cx="45" cy="0" r="2.5" fill="#34D399" />
        </g>

        {/* Peak Shaving Active Vertex Point */}
        <g transform="translate(100, 68)">
          <circle r="8" fill="none" stroke="#F59E0B" strokeWidth="1" opacity="0.5" />
          <circle r="3.5" fill="#F59E0B" filter="url(#energyBloom)" />
        </g>

        <g transform="translate(170, 78)">
          <circle r="8" fill="none" stroke="#10B981" strokeWidth="1" opacity="0.5" />
          <circle r="3.5" fill="#10B981" filter="url(#energyBloom)" />
        </g>
      </svg>
    </div>
  );
};
