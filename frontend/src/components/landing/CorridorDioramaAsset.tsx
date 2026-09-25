import React from 'react';

export const CorridorDioramaAsset: React.FC = () => {
  return (
    <div className="bento-visual-frame">
      <svg
        viewBox="0 0 760 180"
        className="bento-svg-stage"
        preserveAspectRatio="xMidYMid meet"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="corridorRoadbed" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#1E293B" />
            <stop offset="50%" stopColor="#0F172A" />
            <stop offset="100%" stopColor="#1E293B" />
          </linearGradient>

          <linearGradient id="corridorGlowLine" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#38BDF8" />
            <stop offset="50%" stopColor="#818CF8" />
            <stop offset="100%" stopColor="#38BDF8" />
          </linearGradient>

          <linearGradient id="phoenixFacadeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="rgba(245, 158, 11, 0.35)" />
            <stop offset="50%" stopColor="rgba(217, 119, 6, 0.2)" />
            <stop offset="100%" stopColor="rgba(15, 23, 42, 0.9)" />
          </linearGradient>

          <filter id="dioramaBloom" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Ambient Backlight Glow for Key Nodes */}
        <radialGradient id="nodeWestGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.14" />
          <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.0" />
        </radialGradient>
        <circle cx="160" cy="100" r="100" fill="url(#nodeWestGlow)" pointerEvents="none" />

        <radialGradient id="bldGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.12" />
          <stop offset="100%" stopColor="#F59E0B" stopOpacity="0.0" />
        </radialGradient>
        <circle cx="380" cy="65" r="110" fill="url(#bldGlow)" pointerEvents="none" />

        <radialGradient id="nodeEastGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#10B981" stopOpacity="0.14" />
          <stop offset="100%" stopColor="#10B981" stopOpacity="0.0" />
        </radialGradient>
        <circle cx="600" cy="100" r="100" fill="url(#nodeEastGlow)" pointerEvents="none" />

        {/* 1.8 km Distance Ruler Axis Base */}
        <line x1="60" y1="155" x2="700" y2="155" stroke="rgba(255, 255, 255, 0.12)" strokeWidth="1" />
        {/* Major Distance Ticks */}
        <line x1="60" y1="150" x2="60" y2="160" stroke="#38BDF8" strokeWidth="1.5" />
        <line x1="160" y1="150" x2="160" y2="160" stroke="#38BDF8" strokeWidth="1.5" />
        <line x1="380" y1="150" x2="380" y2="160" stroke="#F59E0B" strokeWidth="1.5" />
        <line x1="600" y1="150" x2="600" y2="160" stroke="#10B981" strokeWidth="1.5" />
        <line x1="700" y1="150" x2="700" y2="160" stroke="#10B981" strokeWidth="1.5" />

        {/* Main Arterial Highway Ribbon (Nagar Road) */}
        <rect x="50" y="88" width="660" height="24" rx="4" fill="url(#corridorRoadbed)" stroke="#334155" strokeWidth="1" />
        {/* Median Divider Glowing Strip */}
        <line x1="50" y1="100" x2="710" y2="100" stroke="url(#corridorGlowLine)" strokeWidth="1.5" strokeDasharray="8 6" opacity="0.8" />

        {/* Cross Approach Legs (Viman Nagar North/South) */}
        <rect x="146" y="50" width="28" height="100" rx="3" fill="#1E293B" stroke="#334155" strokeWidth="1" opacity="0.85" />
        <line x1="160" y1="50" x2="160" y2="150" stroke="rgba(255, 255, 255, 0.15)" strokeWidth="1" strokeDasharray="4 4" />

        {/* Cross Approach Legs (Somnath Nagar North/South) */}
        <rect x="586" y="50" width="28" height="100" rx="3" fill="#1E293B" stroke="#334155" strokeWidth="1" opacity="0.85" />
        <line x1="600" y1="50" x2="600" y2="150" stroke="rgba(255, 255, 255, 0.15)" strokeWidth="1" strokeDasharray="4 4" />

        {/* WEST NODE: INT-VN-01 (Viman Nagar Chowk) */}
        <g transform="translate(160, 100)">
          {/* Radar Scanner Ring */}
          <circle r="30" fill="none" stroke="#38BDF8" strokeWidth="1" opacity="0.2" strokeDasharray="4 4">
            <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="18s" repeatCount="indefinite" />
          </circle>
          <circle r="18" fill="none" stroke="#38BDF8" strokeWidth="1.2" opacity="0.6" />
          {/* Vertical Elevation Pillar */}
          <line x1="0" y1="-28" x2="0" y2="0" stroke="#38BDF8" strokeWidth="2" />
          <circle cx="0" cy="-28" r="5" fill="#38BDF8" filter="url(#dioramaBloom)" />
          <circle cx="0" cy="0" r="3" fill="#38BDF8" />
        </g>

        {/* CENTRAL COMMERCIAL FACILITY: BLD-PHOENIX-01 (Phoenix Marketcity) */}
        <g transform="translate(340, 24)">
          {/* Multi-Tiered Isometric Architectural Silhouette */}
          {/* Base Podium Block */}
          <polygon points="40,25 90,0 90,45 40,70" fill="url(#phoenixFacadeGrad)" stroke="#F59E0B" strokeWidth="1" />
          <polygon points="0,45 40,25 40,70 0,90" fill="rgba(15, 23, 42, 0.9)" stroke="#F59E0B" strokeWidth="1" opacity="0.75" />
          <polygon points="40,25 0,45 50,20 90,0" fill="rgba(245, 158, 11, 0.2)" stroke="#F59E0B" strokeWidth="1" />

          {/* Upper Atrium Tower */}
          <polygon points="50,15 80,0 80,30 50,45" fill="rgba(245, 158, 11, 0.3)" stroke="#F59E0B" strokeWidth="1" />
          <polygon points="25,28 50,15 50,45 25,58" fill="rgba(15, 23, 42, 0.95)" stroke="#F59E0B" strokeWidth="0.8" />
          <polygon points="50,15 25,28 55,13 80,0" fill="rgba(245, 158, 11, 0.35)" stroke="#F59E0B" strokeWidth="1" />

          {/* Glowing Rooftop Energy Beacon */}
          <circle cx="52" cy="14" r="12" fill="none" stroke="#F59E0B" strokeWidth="1" opacity="0.3">
            <animate attributeName="r" values="10;16;10" dur="3s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.4;0.1;0.4" dur="3s" repeatCount="indefinite" />
          </circle>
          <circle cx="52" cy="14" r="4.5" fill="#F59E0B" filter="url(#dioramaBloom)" />

          {/* Energy Feed Connecting Link to Arterial */}
          <path d="M 40 70 L 40 64" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="2 2" />
        </g>

        {/* EAST NODE: INT-SN-01 (Somnath Nagar Chowk) */}
        <g transform="translate(600, 100)">
          {/* Radar Scanner Ring */}
          <circle r="30" fill="none" stroke="#10B981" strokeWidth="1" opacity="0.2" strokeDasharray="4 4">
            <animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="18s" repeatCount="indefinite" />
          </circle>
          <circle r="18" fill="none" stroke="#10B981" strokeWidth="1.2" opacity="0.6" />
          {/* Vertical Elevation Pillar */}
          <line x1="0" y1="-28" x2="0" y2="0" stroke="#10B981" strokeWidth="2" />
          <circle cx="0" cy="-28" r="5" fill="#10B981" filter="url(#dioramaBloom)" />
          <circle cx="0" cy="0" r="3" fill="#10B981" />
        </g>

        {/* Dynamic Traffic Packets Flowing Along Nagar Road */}
        <circle cx="110" cy="94" r="3" fill="#38BDF8" filter="url(#dioramaBloom)" />
        <circle cx="230" cy="94" r="3" fill="#38BDF8" filter="url(#dioramaBloom)" />
        <circle cx="270" cy="106" r="3" fill="#10B981" filter="url(#dioramaBloom)" />
        <circle cx="480" cy="94" r="3" fill="#F59E0B" filter="url(#dioramaBloom)" />
        <circle cx="530" cy="106" r="3" fill="#38BDF8" filter="url(#dioramaBloom)" />
        <circle cx="650" cy="94" r="3" fill="#10B981" filter="url(#dioramaBloom)" />
      </svg>
    </div>
  );
};
