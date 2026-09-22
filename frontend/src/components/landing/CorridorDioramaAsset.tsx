import React from 'react';

export const CorridorDioramaAsset: React.FC = () => {
  return (
    <div className="bento-asset-container corridor-diorama-wrap">
      <svg
        viewBox="0 0 460 170"
        className="bento-svg-graphic"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
      >
        <defs>
          <radialGradient id="dioramaRadial" cx="50%" cy="50%" r="60%">
            <stop offset="0%" stopColor="#2F81F7" stopOpacity="0.25" />
            <stop offset="60%" stopColor="#1F6FEB" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#0D1117" stopOpacity="0" />
          </radialGradient>

          {/* Isometric Building Face Gradients */}
          <linearGradient id="bldgTopGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#388BFD" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#1F6FEB" stopOpacity="0.6" />
          </linearGradient>

          <linearGradient id="bldgSideGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#161B22" />
            <stop offset="100%" stopColor="#0D1117" />
          </linearGradient>

          {/* Dual Carriageway Arterial Gradient */}
          <linearGradient id="arterialSpineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#38BDF8" />
            <stop offset="50%" stopColor="#2F81F7" />
            <stop offset="100%" stopColor="#58A6FF" />
          </linearGradient>
        </defs>

        <rect width="460" height="170" fill="url(#dioramaRadial)" />

        {/* Isometric Grid Lines */}
        <g stroke="rgba(255, 255, 255, 0.04)" strokeWidth="0.8">
          <line x1="20" y1="130" x2="160" y2="40" />
          <line x1="120" y1="150" x2="260" y2="60" />
          <line x1="220" y1="160" x2="360" y2="70" />
          <line x1="320" y1="160" x2="440" y2="85" />
        </g>

        {/* Monitored 1.8 km Arterial Centerline Highway */}
        <path
          d="M 30 115 L 140 100 L 250 85 L 360 70 L 430 60"
          stroke="rgba(48, 54, 61, 0.9)"
          strokeWidth="18"
          strokeLinecap="round"
        />

        {/* Eastbound Corridor Active Flow Line */}
        <path
          d="M 30 111 L 140 96 L 250 81 L 360 66 L 430 56"
          fill="none"
          stroke="url(#arterialSpineGrad)"
          strokeWidth="3"
          strokeLinecap="round"
        />

        {/* Westbound Corridor Active Flow Line */}
        <path
          d="M 30 119 L 140 104 L 250 89 L 360 74 L 430 64"
          fill="none"
          stroke="#F59E0B"
          strokeWidth="2"
          strokeDasharray="6 4"
          strokeLinecap="round"
        />

        {/* Intersection INT-VN-01 (Viman Nagar Chowk) */}
        <g transform="translate(60, 95)">
          <rect x="-16" y="-16" width="32" height="32" rx="4" fill="rgba(22, 27, 34, 0.9)" stroke="#38BDF8" strokeWidth="1.5" />
          <circle cx="0" cy="0" r="4" fill="#38BDF8" />
          <text x="0" y="26" fill="#F0F6FC" fontSize="8.5" fontFamily="monospace" textAnchor="middle" fontWeight="600">
            INT-VN-01
          </text>
          <text x="0" y="35" fill="#8B949E" fontSize="7.5" fontFamily="monospace" textAnchor="middle">
            VIMAN NAGAR
          </text>
        </g>

        {/* Phoenix Marketcity Commercial Entity (BLD-PHOENIX-01) Extruded 3D Footprint */}
        <g transform="translate(230, 20)">
          {/* Building Isometric Base */}
          <polygon points="0,40 50,25 90,45 40,60" fill="url(#bldgTopGrad)" stroke="#388BFD" strokeWidth="1" />
          <polygon points="0,40 40,60 40,75 0,55" fill="url(#bldgSideGrad)" stroke="#30363D" strokeWidth="1" />
          <polygon points="40,60 90,45 90,60 40,75" fill="url(#bldgSideGrad)" stroke="#30363D" strokeWidth="1" />
          
          {/* HVAC Telemetry Sensor Node on Roof */}
          <circle cx="45" cy="42" r="3.5" fill="#F59E0B" />
          <circle cx="45" cy="42" r="7" fill="none" stroke="#F59E0B" strokeWidth="1" opacity="0.8" className="animate-ping-slow" />
          
          <text x="45" y="16" fill="#F0F6FC" fontSize="9" fontFamily="monospace" textAnchor="middle" fontWeight="700">
            BLD-PHOENIX-01
          </text>
          <text x="45" y="88" fill="#F59E0B" fontSize="8" fontFamily="monospace" textAnchor="middle">
            COMMERCIAL METER (4,862 kW)
          </text>
        </g>

        {/* Intersection INT-SN-01 (Somnath Nagar Chowk) */}
        <g transform="translate(390, 50)">
          <rect x="-16" y="-16" width="32" height="32" rx="4" fill="rgba(22, 27, 34, 0.9)" stroke="#58A6FF" strokeWidth="1.5" />
          <circle cx="0" cy="0" r="4" fill="#58A6FF" />
          <text x="0" y="26" fill="#F0F6FC" fontSize="8.5" fontFamily="monospace" textAnchor="middle" fontWeight="600">
            INT-SN-01
          </text>
          <text x="0" y="35" fill="#8B949E" fontSize="7.5" fontFamily="monospace" textAnchor="middle">
            SOMNATH NAGAR
          </text>
        </g>
      </svg>

      <div className="bento-asset-hud">
        <div className="hud-badge font-mono">
          <span className="hud-dot live" />
          <span>CORRIDOR PHYSICAL TOPOLOGY</span>
        </div>
        <div className="hud-metric font-mono">
          <span className="metric-val text-blue">1.8 km</span>
          <span className="metric-unit">arterial span</span>
          <span className="metric-tag physical">POSTGIS REGISTERED</span>
        </div>
      </div>
    </div>
  );
};
