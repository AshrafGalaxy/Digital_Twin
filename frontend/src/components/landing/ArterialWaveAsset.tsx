import React from 'react';

export const ArterialWaveAsset: React.FC<{ speed?: number }> = ({ speed = 34.2 }) => {
  return (
    <div className="bento-asset-container arterial-wave-wrap">
      <svg
        viewBox="0 0 460 170"
        className="bento-svg-graphic"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
      >
        <defs>
          {/* Deep Ambient Glow Gradient */}
          <radialGradient id="arterialRadialGlow" cx="50%" cy="50%" r="60%">
            <stop offset="0%" stopColor="#2F81F7" stopOpacity="0.35" />
            <stop offset="60%" stopColor="#1F6FEB" stopOpacity="0.1" />
            <stop offset="100%" stopColor="#0D1117" stopOpacity="0" />
          </radialGradient>

          {/* Area Under Wave Gradient */}
          <linearGradient id="arterialAreaGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.32" />
            <stop offset="50%" stopColor="#2F81F7" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#0D1117" stopOpacity="0" />
          </linearGradient>

          {/* Precision Neon Flow Stroke Gradient */}
          <linearGradient id="arterialNeonStroke" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10B981" />
            <stop offset="35%" stopColor="#38BDF8" />
            <stop offset="70%" stopColor="#2F81F7" />
            <stop offset="100%" stopColor="#58A6FF" />
          </linearGradient>

          {/* Grid Pattern */}
          <pattern id="arterialGrid" width="30" height="25" patternUnits="userSpaceOnUse">
            <path d="M 30 0 L 0 0 0 25" fill="none" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="0.8" />
          </pattern>
        </defs>

        {/* Ambient Glow */}
        <rect width="460" height="170" fill="url(#arterialRadialGlow)" />

        {/* Precision Coordinate Grid */}
        <rect width="460" height="170" fill="url(#arterialGrid)" />

        {/* Target Baseline Speed Guide (40 km/h) */}
        <line x1="20" y1="55" x2="440" y2="55" stroke="rgba(88, 166, 255, 0.25)" strokeWidth="1" strokeDasharray="4 4" />
        <text x="440" y="51" fill="#8B949E" fontSize="9" fontFamily="monospace" textAnchor="end">
          FREE-FLOW 45 km/h
        </text>

        {/* Wave Area Fill */}
        <path
          d="M 20 150
             L 20 110
             C 60 115, 90 70, 130 75
             C 170 80, 190 120, 230 110
             C 270 100, 290 60, 330 65
             C 370 70, 400 95, 440 85
             L 440 150 Z"
          fill="url(#arterialAreaGrad)"
        />

        {/* Continuous Telemetry Stroke */}
        <path
          d="M 20 110
             C 60 115, 90 70, 130 75
             C 170 80, 190 120, 230 110
             C 270 100, 290 60, 330 65
             C 370 70, 400 95, 440 85"
          fill="none"
          stroke="url(#arterialNeonStroke)"
          strokeWidth="2.5"
          strokeLinecap="round"
        />

        {/* Monitored Corridor Nodes */}
        {/* INT-VN-01 */}
        <circle cx="130" cy="75" r="4.5" fill="#38BDF8" />
        <circle cx="130" cy="75" r="9" fill="none" stroke="#38BDF8" strokeWidth="1.2" opacity="0.6" className="animate-ping-slow" />
        <text x="130" y="94" fill="#E6EDF3" fontSize="9.5" fontFamily="monospace" textAnchor="middle" fontWeight="600">
          INT-VN-01
        </text>

        {/* SEG-NR-EB Midpoint */}
        <circle cx="230" cy="110" r="3.5" fill="#F59E0B" />
        <text x="230" y="130" fill="#8B949E" fontSize="8.5" fontFamily="monospace" textAnchor="middle">
          SEG-NR-EB-02 (28.4 km/h)
        </text>

        {/* INT-SN-01 Terminus */}
        <circle cx="330" cy="65" r="4.5" fill="#58A6FF" />
        <circle cx="330" cy="65" r="9" fill="none" stroke="#58A6FF" strokeWidth="1.2" opacity="0.6" className="animate-ping-slow" />
        <text x="330" y="52" fill="#E6EDF3" fontSize="9.5" fontFamily="monospace" textAnchor="middle" fontWeight="600">
          INT-SN-01
        </text>

        {/* Live Sweeping Pulse Indicator */}
        <line x1="440" y1="30" x2="440" y2="150" stroke="#58A6FF" strokeWidth="1.5" opacity="0.8" />
      </svg>

      {/* Floating HUD Telemetry Readout */}
      <div className="bento-asset-hud">
        <div className="hud-badge font-mono">
          <span className="hud-dot live" />
          <span>ARTERIAL FLOW • 10 SEGMENTS</span>
        </div>
        <div className="hud-metric font-mono">
          <span className="metric-val">{speed.toFixed(1)}</span>
          <span className="metric-unit">km/h</span>
          <span className="metric-tag">LoS C (STABLE)</span>
        </div>
      </div>
    </div>
  );
};
