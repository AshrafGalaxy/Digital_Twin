import React from 'react';

export const CorridorDioramaAsset: React.FC = () => {
  return (
    <div className="bento-visual-frame bento-frame-photo">
      <img
        src="/assets/images/cinematic-illuminated-urban-model.png"
        alt="Cinematic Illuminated Physical Urban Scale Model"
        className="bento-asset-img"
        loading="lazy"
      />
      <div className="bento-img-overlay" aria-hidden="true" />
      <div className="bento-img-telemetry">
        <div className="bento-telemetry-pill">
          <span className="bento-pill-dot" style={{ background: '#10B981', boxShadow: '0 0 8px rgba(16, 185, 129, 0.8)' }} />
          <span className="bento-pill-label">PHYSICAL TWIN SCALE REPLICA</span>
        </div>
        <div className="bento-telemetry-metric">
          1.8 km DUAL ARTERIAL • 10 SEGMENTS
        </div>
      </div>
    </div>
  );
};
