import React from 'react';

export const ArterialWaveAsset: React.FC = () => {
  return (
    <div className="bento-visual-frame bento-frame-photo">
      <img
        src="/assets/images/twilight-city-highway-light-trails.png"
        alt="Twilight Arterial Highway Traffic Light Trails"
        className="bento-asset-img"
        loading="eager"
      />
      <div className="bento-img-overlay" aria-hidden="true" />
      <div className="bento-img-telemetry">
        <div className="bento-telemetry-pill">
          <span className="bento-pill-dot" />
          <span className="bento-pill-label">SYNCHRONIZED ARTERIAL FLOW</span>
        </div>
        <div className="bento-telemetry-metric">
          34.2 km/h • 2,400 PCU/h
        </div>
      </div>
    </div>
  );
};


