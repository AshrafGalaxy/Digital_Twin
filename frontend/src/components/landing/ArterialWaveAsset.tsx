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
    </div>
  );
};
