import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface MapLegendProps {
  isDrawerOpen?: boolean;
  isComparisonMode?: boolean;
}

export const MapLegend: React.FC<MapLegendProps> = ({
  isDrawerOpen = false,
  isComparisonMode = false
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <aside
      className={`map-legend ${isDrawerOpen ? (isComparisonMode ? 'drawer-comparison-open' : 'drawer-open') : ''} ${isCollapsed ? 'collapsed' : ''}`}
      aria-label="Corridor Traffic Velocity Legend"
    >
      <div className="legend-header" onClick={() => setIsCollapsed(!isCollapsed)}>
        <span className="legend-title">Corridor Traffic Velocity</span>
        <button
          type="button"
          className="legend-collapse-btn"
          aria-label={isCollapsed ? 'Expand legend' : 'Collapse legend'}
        >
          {isCollapsed ? <ChevronDown size={12} /> : <ChevronUp size={12} />}
        </button>
      </div>

      {!isCollapsed && (
        <div className="legend-content">
          <div className="legend-items">
            <div className="legend-item" title="Speed above 35 km/h (Free Flow / Minor Delay)">
              <div className="legend-color-box" style={{ backgroundColor: '#3FB950' }} />
              <span>&gt; 35 km/h (Normal)</span>
            </div>
            <div className="legend-item" title="Speed between 20 and 35 km/h (Moderate Delay)">
              <div className="legend-color-box" style={{ backgroundColor: '#D29922' }} />
              <span>20–35 km/h (Moderate)</span>
            </div>
            <div className="legend-item" title="Speed under 20 km/h (Significant Congestion / Queueing)">
              <div className="legend-color-box" style={{ backgroundColor: '#F85149' }} />
              <span>&lt; 20 km/h (Congested)</span>
            </div>
          </div>
          <div className="legend-asset-row">
            <span className="legend-asset-chip">🚦 Signalized Chowk</span>
            <span className="legend-asset-chip">⚡ Phoenix Energy</span>
          </div>
        </div>
      )}
    </aside>
  );
};
