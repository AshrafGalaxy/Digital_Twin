import React from 'react';

export const MapLegend: React.FC = () => {
  return (
    <div className="map-legend">
      <span className="legend-title">Corridor Traffic Velocity</span>
      <div className="legend-items">
        <div className="legend-item">
          <div className="legend-color-box" style={{ backgroundColor: '#10B981' }} />
          <span>&gt; 35 km/h (Normal)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color-box" style={{ backgroundColor: '#F59E0B' }} />
          <span>20 - 35 km/h (Moderate)</span>
        </div>
        <div className="legend-item">
          <div className="legend-color-box" style={{ backgroundColor: '#EF4444' }} />
          <span>&lt; 20 km/h (Congested)</span>
        </div>
      </div>
    </div>
  );
};
