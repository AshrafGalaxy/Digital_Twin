import React from 'react';

export const ConformalBandsAsset: React.FC = () => {
  return (
    <div className="bento-visual-frame bento-frame-photo">
      <img
        src="/assets/images/embedded-road-sensor-asphalt.png"
        alt="Embedded Road Sensor on Asphalt Pavement"
        className="bento-asset-img"
        loading="lazy"
      />
      <div className="bento-img-overlay" aria-hidden="true" />
    </div>
  );
};
