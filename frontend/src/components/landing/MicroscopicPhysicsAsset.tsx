import React from 'react';

export const MicroscopicPhysicsAsset: React.FC = () => {
  return (
    <div className="bento-visual-frame">
      <svg
        viewBox="0 0 360 160"
        className="bento-svg-stage"
        preserveAspectRatio="xMidYMid meet"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="roadwayAsphalt" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#1E293B" stopOpacity="0.8" />
            <stop offset="50%" stopColor="#0F172A" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#0B0F17" stopOpacity="0.95" />
          </linearGradient>

          <linearGradient id="leadVehicleTrail" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.0" />
            <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.8" />
          </linearGradient>

          <linearGradient id="followVehicleTrail" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#10B981" stopOpacity="0.0" />
            <stop offset="100%" stopColor="#10B981" stopOpacity="0.8" />
          </linearGradient>

          <linearGradient id="sensorLaserBeam" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.1" />
            <stop offset="50%" stopColor="#38BDF8" stopOpacity="0.85" />
            <stop offset="100%" stopColor="#38BDF8" stopOpacity="0.1" />
          </linearGradient>

          <filter id="physicsGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Ambient Radar Grid Background */}
        <radialGradient id="radarBackGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#10B981" stopOpacity="0.09" />
          <stop offset="100%" stopColor="#10B981" stopOpacity="0.0" />
        </radialGradient>
        <circle cx="180" cy="80" r="140" fill="url(#radarBackGlow)" pointerEvents="none" />

        {/* Multi-Lane Highway Surface Bed */}
        <rect x="15" y="24" width="330" height="112" rx="8" fill="url(#roadwayAsphalt)" stroke="#334155" strokeWidth="1" />

        {/* Dashed Lane Dividers */}
        <line x1="15" y1="61" x2="345" y2="61" stroke="rgba(255, 255, 255, 0.16)" strokeWidth="1.2" strokeDasharray="10 8" />
        <line x1="15" y1="98" x2="345" y2="98" stroke="rgba(255, 255, 255, 0.16)" strokeWidth="1.2" strokeDasharray="10 8" />

        {/* Virtual Inductive Loop Sensor Beam */}
        <line x1="210" y1="24" x2="210" y2="136" stroke="url(#sensorLaserBeam)" strokeWidth="2" strokeDasharray="3 3" filter="url(#physicsGlow)" />
        <circle cx="210" cy="24" r="3" fill="#38BDF8" filter="url(#physicsGlow)" />
        <circle cx="210" cy="136" r="3" fill="#38BDF8" filter="url(#physicsGlow)" />

        {/* LANE 1: High-Speed Free Flow (Top Lane) */}
        {/* Lead Vehicle */}
        <g transform="translate(250, 36)">
          {/* Kinetic Speed Trail */}
          <line x1="-35" y1="8" x2="0" y2="8" stroke="url(#leadVehicleTrail)" strokeWidth="2.5" strokeLinecap="round" />
          {/* Vehicle Pod */}
          <rect width="28" height="16" rx="4" fill="#1E293B" stroke="#38BDF8" strokeWidth="1.5" />
          <line x1="18" y1="4" x2="24" y2="4" stroke="#38BDF8" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="18" y1="12" x2="24" y2="12" stroke="#38BDF8" strokeWidth="1.5" strokeLinecap="round" />
          {/* Forward Radar Cone */}
          <path d="M 28 8 L 65 -2 M 28 8 L 65 18" stroke="rgba(56, 189, 248, 0.35)" strokeWidth="1" strokeDasharray="2 3" />
        </g>

        {/* Following Vehicle with Calibrated Krauss Gap */}
        <g transform="translate(130, 36)">
          <line x1="-30" y1="8" x2="0" y2="8" stroke="url(#leadVehicleTrail)" strokeWidth="2" strokeLinecap="round" />
          <rect width="26" height="16" rx="4" fill="#0F172A" stroke="#38BDF8" strokeWidth="1.5" />
          {/* Krauss Safe Braking Distance Arc */}
          <path d="M 32 3 Q 55 8 32 13" fill="none" stroke="#38BDF8" strokeWidth="1.2" opacity="0.75" />
          <path d="M 40 1 Q 68 8 40 15" fill="none" stroke="#38BDF8" strokeWidth="1" opacity="0.4" />
        </g>

        {/* Third Vehicle in Lane 1 */}
        <g transform="translate(35, 36)">
          <rect width="24" height="16" rx="4" fill="#0F172A" stroke="rgba(56, 189, 248, 0.6)" strokeWidth="1.2" />
        </g>

        {/* LANE 2: Coordinated Transit / Platoon Flow (Middle Lane) */}
        {/* BRTS Transit Unit */}
        <g transform="translate(180, 72)">
          <line x1="-40" y1="9" x2="0" y2="9" stroke="url(#followVehicleTrail)" strokeWidth="2.5" strokeLinecap="round" />
          <rect width="44" height="18" rx="4" fill="#064E3B" stroke="#10B981" strokeWidth="1.6" />
          {/* Windows / Tech Highlights */}
          <rect x="6" y="4" width="8" height="10" rx="1.5" fill="#34D399" opacity="0.6" />
          <rect x="18" y="4" width="8" height="10" rx="1.5" fill="#34D399" opacity="0.6" />
          <rect x="30" y="4" width="8" height="10" rx="1.5" fill="#34D399" opacity="0.6" />
          {/* Priority Beacon */}
          <circle cx="22" cy="0" r="3" fill="#10B981" filter="url(#physicsGlow)" />
        </g>

        {/* Following Vehicle in Lane 2 */}
        <g transform="translate(65, 73)">
          <rect width="26" height="16" rx="4" fill="#0F172A" stroke="#10B981" strokeWidth="1.4" />
          <path d="M 32 3 Q 60 8 32 13" fill="none" stroke="#10B981" strokeWidth="1.2" opacity="0.7" />
        </g>

        {/* LANE 3: Merging Vehicle Dynamics (Bottom Lane) */}
        <g transform="translate(240, 110)">
          <rect width="26" height="16" rx="4" fill="#1E293B" stroke="#F59E0B" strokeWidth="1.4" />
          <circle cx="32" cy="8" r="2.5" fill="#F59E0B" filter="url(#physicsGlow)" />
        </g>

        <g transform="translate(110, 110)">
          <rect width="28" height="16" rx="4" fill="#0F172A" stroke="rgba(245, 158, 11, 0.7)" strokeWidth="1.2" />
          {/* Merging Trajectory Vector Arc */}
          <path d="M 35 4 C 60 0, 80 -18, 95 -18" fill="none" stroke="#F59E0B" strokeWidth="1.2" strokeDasharray="3 3" opacity="0.75" />
        </g>
      </svg>
    </div>
  );
};
