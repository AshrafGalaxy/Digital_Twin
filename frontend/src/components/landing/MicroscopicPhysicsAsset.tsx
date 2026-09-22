import React from 'react';

export const MicroscopicPhysicsAsset: React.FC = () => {
  return (
    <div className="bento-asset-container physics-model-wrap">
      <svg
        viewBox="0 0 260 170"
        className="bento-svg-graphic"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
      >
        <defs>
          <radialGradient id="physicsRadial" cx="50%" cy="50%" r="60%">
            <stop offset="0%" stopColor="#10B981" stopOpacity="0.25" />
            <stop offset="70%" stopColor="#059669" stopOpacity="0.06" />
            <stop offset="100%" stopColor="#0D1117" stopOpacity="0" />
          </radialGradient>

          {/* Roadbed Gradient */}
          <linearGradient id="roadBedGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#161B22" />
            <stop offset="100%" stopColor="#0D1117" />
          </linearGradient>

          {/* Laser Scan Loop Sensor Beam */}
          <linearGradient id="loopSensorBeam" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#10B981" stopOpacity="0.8" />
          </linearGradient>
        </defs>

        <rect width="260" height="170" fill="url(#physicsRadial)" />

        {/* 3-Lane Road Arterial Bed */}
        <rect x="10" y="30" width="240" height="100" rx="4" fill="url(#roadBedGrad)" stroke="#30363D" strokeWidth="1" />

        {/* Lane Dividers */}
        <line x1="10" y1="63" x2="250" y2="63" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1" strokeDasharray="8 6" />
        <line x1="10" y1="97" x2="250" y2="97" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1" strokeDasharray="8 6" />

        {/* Inductive Loop Sensor Array (Virtual Detection Zone) */}
        <rect x="145" y="30" width="16" height="100" fill="rgba(56, 189, 248, 0.12)" stroke="url(#loopSensorBeam)" strokeWidth="1.2" strokeDasharray="2 2" />
        <text x="153" y="24" fill="#38BDF8" fontSize="7.5" fontFamily="monospace" textAnchor="middle">
          LOOP ARRAY IL-03
        </text>

        {/* Lane 1 Vehicles & Speed Vectors */}
        <g transform="translate(40, 41)">
          <rect width="24" height="12" rx="2" fill="#2F81F7" />
          <line x1="24" y1="6" x2="38" y2="6" stroke="#38BDF8" strokeWidth="1.5" strokeLinecap="round" />
        </g>
        <g transform="translate(110, 41)">
          <rect width="22" height="12" rx="2" fill="#10B981" />
          <line x1="22" y1="6" x2="34" y2="6" stroke="#10B981" strokeWidth="1.5" strokeLinecap="round" />
        </g>
        <g transform="translate(190, 41)">
          <rect width="28" height="12" rx="2" fill="#58A6FF" />
          <line x1="28" y1="6" x2="42" y2="6" stroke="#58A6FF" strokeWidth="1.5" strokeLinecap="round" />
        </g>

        {/* Lane 2 Vehicles (Queue behind bottleneck) */}
        <g transform="translate(25, 75)">
          <rect width="22" height="12" rx="2" fill="#F59E0B" />
          <line x1="22" y1="6" x2="30" y2="6" stroke="#F59E0B" strokeWidth="1.5" strokeLinecap="round" />
        </g>
        <g transform="translate(85, 75)">
          <rect width="26" height="12" rx="2" fill="#EF4444" />
          <line x1="26" y1="6" x2="31" y2="6" stroke="#EF4444" strokeWidth="1.5" strokeLinecap="round" />
        </g>
        <g transform="translate(170, 75)">
          <rect width="24" height="12" rx="2" fill="#F59E0B" />
          <line x1="24" y1="6" x2="32" y2="6" stroke="#F59E0B" strokeWidth="1.5" strokeLinecap="round" />
        </g>

        {/* Lane 3 Bus/Transit Vehicle (BRTS Lane) */}
        <g transform="translate(60, 108)">
          <rect width="42" height="14" rx="2" fill="#38BDF8" />
          <line x1="42" y1="7" x2="58" y2="7" stroke="#38BDF8" strokeWidth="1.8" strokeLinecap="round" />
          <text x="21" y="10" fill="#0D1117" fontSize="7" fontFamily="monospace" textAnchor="middle" fontWeight="bold">PMPML</text>
        </g>
        <g transform="translate(180, 108)">
          <rect width="22" height="12" rx="2" fill="#10B981" />
          <line x1="22" y1="6" x2="36" y2="6" stroke="#10B981" strokeWidth="1.5" strokeLinecap="round" />
        </g>

        {/* Kinematic Model Label */}
        <text x="15" y="152" fill="#8B949E" fontSize="8" fontFamily="monospace">
          KRAUSS CAR-FOLLOWING MODEL (d_safe = 2.0s)
        </text>
      </svg>

      <div className="bento-asset-hud">
        <div className="hud-badge font-mono">
          <span className="hud-dot success" />
          <span>SUMO MICROSCOPIC KINEMATICS</span>
        </div>
        <div className="hud-metric font-mono">
          <span className="metric-val text-emerald">100%</span>
          <span className="metric-unit">physics-valid</span>
          <span className="metric-tag synthetic">SYNTHETIC FEED</span>
        </div>
      </div>
    </div>
  );
};
