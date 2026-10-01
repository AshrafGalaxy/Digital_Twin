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
    </div>
  );
};
