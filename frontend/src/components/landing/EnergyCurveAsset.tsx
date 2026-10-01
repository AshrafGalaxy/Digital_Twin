import React from 'react';

export const EnergyCurveAsset: React.FC = () => {
  return (
    <div className="bento-visual-frame bento-frame-photo">
      <img
        src="/assets/images/twilight-glass-corporate-complex.png"
        alt="Twilight Glass Corporate Commercial Microgrid Complex"
        className="bento-asset-img"
        loading="lazy"
      />
      <div className="bento-img-overlay" aria-hidden="true" />
      <div className="bento-img-telemetry">
        <div className="bento-telemetry-pill">
          <span className="bento-pill-dot" style={{ background: '#F59E0B', boxShadow: '0 0 8px rgba(245, 158, 11, 0.8)' }} />
          <span className="bento-pill-label">PEAK TARIFF ADVISORY</span>
        </div>
        <div className="bento-telemetry-metric" style={{ color: '#FCD34D', borderColor: 'rgba(245, 158, 11, 0.3)' }}>
          -380 kW LOAD SHAVE
        </div>
      </div>
    </div>
  );
};
