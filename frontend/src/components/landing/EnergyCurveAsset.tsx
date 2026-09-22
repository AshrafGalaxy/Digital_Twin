import React from 'react';

export const EnergyCurveAsset: React.FC = () => {
  return (
    <div className="bento-asset-container energy-curve-wrap">
      <svg
        viewBox="0 0 260 170"
        className="bento-svg-graphic"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
      >
        <defs>
          {/* Amber/Gold Luminous Glow Gradient */}
          <radialGradient id="energyRadial" cx="60%" cy="40%" r="65%">
            <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.25" />
            <stop offset="60%" stopColor="#D97706" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#0D1117" stopOpacity="0" />
          </radialGradient>

          {/* Area Fill Gradient */}
          <linearGradient id="energyArea" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.3" />
            <stop offset="70%" stopColor="#D97706" stopOpacity="0.05" />
            <stop offset="100%" stopColor="#0D1117" stopOpacity="0" />
          </linearGradient>

          {/* Stroke Gradient */}
          <linearGradient id="energyStroke" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10B981" />
            <stop offset="45%" stopColor="#F59E0B" />
            <stop offset="85%" stopColor="#EF4444" />
          </linearGradient>

          {/* Subdued Shaved Demand Area */}
          <linearGradient id="shavedArea" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#10B981" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#0D1117" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Ambient Glow */}
        <rect width="260" height="170" fill="url(#energyRadial)" />

        {/* Contract Feeder Baseline (5,200 kW max capacity) */}
        <line x1="15" y1="35" x2="245" y2="35" stroke="rgba(239, 68, 68, 0.4)" strokeWidth="1" strokeDasharray="3 3" />
        <text x="245" y="30" fill="#EF4444" fontSize="8" fontFamily="monospace" textAnchor="end">
          FEEDER LIMIT 5,200 kW
        </text>

        {/* Unmitigated Observed Demand Curve (Area) */}
        <path
          d="M 15 150
             L 15 115
             C 45 110, 75 95, 105 85
             C 135 75, 155 45, 185 45
             C 215 45, 235 65, 245 70
             L 245 150 Z"
          fill="url(#energyArea)"
        />

        {/* Unmitigated Observed Demand Line */}
        <path
          d="M 15 115
             C 45 110, 75 95, 105 85
             C 135 75, 155 45, 185 45
             C 215 45, 235 65, 245 70"
          fill="none"
          stroke="url(#energyStroke)"
          strokeWidth="2.2"
          strokeLinecap="round"
        />

        {/* Calibrated Advisory Trajectory (Peak Shaving) */}
        <path
          d="M 135 75
             C 155 68, 185 68, 245 88"
          fill="none"
          stroke="#10B981"
          strokeWidth="2"
          strokeDasharray="4 3"
          strokeLinecap="round"
        />

        {/* Peak Demand Highlight Node */}
        <circle cx="185" cy="45" r="4.5" fill="#EF4444" />
        <circle cx="185" cy="45" r="8" fill="none" stroke="#EF4444" strokeWidth="1" opacity="0.6" className="animate-ping-slow" />
        <text x="185" y="38" fill="#F0F6FC" fontSize="8.5" fontFamily="monospace" textAnchor="middle" fontWeight="700">
          4,862 kW
        </text>

        {/* Time Axis Labels */}
        <text x="20" y="162" fill="#8B949E" fontSize="8" fontFamily="monospace">08:00</text>
        <text x="130" y="162" fill="#8B949E" fontSize="8" fontFamily="monospace">14:00 (PEAK)</text>
        <text x="235" y="162" fill="#8B949E" fontSize="8" fontFamily="monospace">20:00</text>
      </svg>

      <div className="bento-asset-hud">
        <div className="hud-badge font-mono">
          <span className="hud-dot warning" />
          <span>BLD-PHOENIX-01 • CHILLER LOAD</span>
        </div>
        <div className="hud-metric font-mono">
          <span className="metric-val text-amber">4,862</span>
          <span className="metric-unit">kW</span>
          <span className="metric-tag advisory">-380 kW ADVISORY</span>
        </div>
      </div>
    </div>
  );
};
