import React from 'react';

export const ConformalBandsAsset: React.FC = () => {
  return (
    <div className="bento-asset-container conformal-bands-wrap">
      <svg
        viewBox="0 0 260 170"
        className="bento-svg-graphic"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
      >
        <defs>
          {/* Violet Glow */}
          <radialGradient id="conformalRadial" cx="50%" cy="50%" r="60%">
            <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.25" />
            <stop offset="60%" stopColor="#6366F1" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#0D1117" stopOpacity="0" />
          </radialGradient>

          {/* 90% Outer Conformal Ribbon Gradient */}
          <linearGradient id="band90Grad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#6366F1" stopOpacity="0.08" />
          </linearGradient>

          {/* 80% Inner Conformal Ribbon Gradient */}
          <linearGradient id="band80Grad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#A78BFA" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0.15" />
          </linearGradient>

          {/* Core Prediction Trajectory Neon */}
          <linearGradient id="predCoreNeon" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#C4B5FD" />
            <stop offset="50%" stopColor="#A78BFA" />
            <stop offset="100%" stopColor="#818CF8" />
          </linearGradient>
        </defs>

        {/* Ambient Glow */}
        <rect width="260" height="170" fill="url(#conformalRadial)" />

        {/* Horizon Cutoff Line (T+0 Now) */}
        <line x1="80" y1="20" x2="80" y2="150" stroke="rgba(255, 255, 255, 0.2)" strokeWidth="1" strokeDasharray="2 2" />
        <text x="80" y="16" fill="#8B949E" fontSize="8" fontFamily="monospace" textAnchor="middle">NOW (T=0)</text>

        {/* Historical Observed Telemetry Segment */}
        <path
          d="M 15 95 L 40 85 L 60 90 L 80 82"
          fill="none"
          stroke="#F0F6FC"
          strokeWidth="2"
          strokeLinecap="round"
        />

        {/* 90% Outer Conformal Prediction Envelope Ribbon */}
        <path
          d="M 80 82
             C 120 70, 160 55, 245 42
             L 245 132
             C 160 115, 120 95, 80 82 Z"
          fill="url(#band90Grad)"
          stroke="rgba(139, 92, 246, 0.4)"
          strokeWidth="0.8"
        />

        {/* 80% Inner Conformal Prediction Envelope Ribbon */}
        <path
          d="M 80 82
             C 120 74, 160 62, 245 55
             L 245 118
             C 160 102, 120 88, 80 82 Z"
          fill="url(#band80Grad)"
          stroke="rgba(167, 139, 250, 0.5)"
          strokeWidth="0.8"
        />

        {/* Center Machine Learning Point Forecast Line */}
        <path
          d="M 80 82
             C 120 78, 160 68, 245 86"
          fill="none"
          stroke="url(#predCoreNeon)"
          strokeWidth="2.5"
          strokeLinecap="round"
        />

        {/* Persistence Baseline Comparator */}
        <line x1="80" y1="82" x2="245" y2="82" stroke="rgba(139, 148, 158, 0.5)" strokeWidth="1.2" strokeDasharray="3 3" />
        <text x="245" y="80" fill="#8B949E" fontSize="7.5" fontFamily="monospace" textAnchor="end">
          PERSISTENCE
        </text>

        {/* Forecast Horizon Labels */}
        <text x="140" y="162" fill="#8B949E" fontSize="8" fontFamily="monospace">T+15m</text>
        <text x="195" y="162" fill="#8B949E" fontSize="8" fontFamily="monospace">T+30m</text>
        <text x="245" y="162" fill="#8B949E" fontSize="8" fontFamily="monospace" textAnchor="end">T+60m</text>
      </svg>

      <div className="bento-asset-hud">
        <div className="hud-badge font-mono">
          <span className="hud-dot violet" />
          <span>CONFORMAL ENVELOPE (80% / 90%)</span>
        </div>
        <div className="hud-metric font-mono">
          <span className="metric-val text-violet">±3.8</span>
          <span className="metric-unit">km/h bound</span>
          <span className="metric-tag tree">TreeSHAP VERIFIED</span>
        </div>
      </div>
    </div>
  );
};
