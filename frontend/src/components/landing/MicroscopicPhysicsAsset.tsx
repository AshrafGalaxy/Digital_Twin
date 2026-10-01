import React from 'react';

export const MicroscopicPhysicsAsset: React.FC = () => {
  return (
    <div className="bento-visual-frame bento-frame-photo">
      <img
        src="/assets/images/rugged-industrial-pole-enclosure.png"
        alt="Rugged Edge Ingestion Controller Enclosure"
        className="bento-asset-img"
        loading="lazy"
      />
      <div className="bento-img-overlay" aria-hidden="true" />
      <div className="bento-img-telemetry">
        <div className="bento-telemetry-pill">
          <span className="bento-pill-dot" style={{ background: '#38BDF8', boxShadow: '0 0 8px rgba(56, 189, 248, 0.8)' }} />
          <span className="bento-pill-label">EDGE CONTROLLER NODE</span>
        </div>
        <div className="bento-telemetry-metric" style={{ color: '#7DD3FC', borderColor: 'rgba(56, 189, 248, 0.3)' }}>
          50 Hz • 100ms LATENCY
        </div>
      </div>
    </div>
  );
};
