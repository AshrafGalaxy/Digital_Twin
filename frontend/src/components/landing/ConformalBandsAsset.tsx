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
      <div className="bento-img-telemetry">
        <div className="bento-telemetry-pill">
          <span className="bento-pill-dot" style={{ background: '#A78BFA', boxShadow: '0 0 8px rgba(167, 139, 250, 0.8)' }} />
          <span className="bento-pill-label">GROUND TRUTH SENSOR</span>
        </div>
        <div className="bento-telemetry-metric" style={{ color: '#C4B5FD', borderColor: 'rgba(167, 139, 250, 0.3)' }}>
          ±1.2 km/h CONFORMAL BOUND
        </div>
      </div>
    </div>
  );
};
