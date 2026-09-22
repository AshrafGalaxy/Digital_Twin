import React from 'react';

export const MapLegend: React.FC = () => {
  return (
    <div className="map-legend">
      <span className="legend-title">Corridor Traffic Velocity</span>
      <div className="legend-items">
        <div className="legend-item">
          <div className="legend-color-box" style={{ backgroundColor: '#3FB950' }} />
          <span>&gt; 35 km/h (Normal)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color-box" style={{ backgroundColor: '#D29922' }} />
          <span>20 - 35 km/h (Moderate)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color-box" style={{ backgroundColor: '#F85149' }} />
          <span>&lt; 20 km/h (Congested)</span>
        </div>
      </div>
    </div>
  );
};
