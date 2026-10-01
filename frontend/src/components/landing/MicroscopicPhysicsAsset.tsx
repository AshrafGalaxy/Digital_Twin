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
    </div>
  );
};
