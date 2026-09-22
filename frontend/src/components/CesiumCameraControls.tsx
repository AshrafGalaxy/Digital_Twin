import React from 'react';
import { Compass, Building2, TrafficCone, Eye, MapPin } from 'lucide-react';

export interface CameraViewpoint {
  id: string;
  name: string;
  icon: 'corridor' | 'viman' | 'somnath' | 'phoenix' | 'topdown';
  longitude: number;
  latitude: number;
  height: number;
  headingDegrees: number;
  pitchDegrees: number;
  rollDegrees: number;
}

export const CORRIDOR_VIEWPOINTS: CameraViewpoint[] = [
  {
    id: 'corridor-overview',
    name: 'Full Corridor',
    icon: 'corridor',
    longitude: 73.9185,
    latitude: 18.5580,
    height: 750,
    headingDegrees: 68,
    pitchDegrees: -38,
    rollDegrees: 0
  },
  {
    id: 'viman-nagar-chowk',
    name: 'Viman Nagar Chowk',
    icon: 'viman',
    longitude: 73.9125,
    latitude: 18.5615,
    height: 180,
    headingDegrees: 75,
    pitchDegrees: -30,
    rollDegrees: 0
  },
  {
    id: 'phoenix-marketcity',
    name: 'Phoenix Zone (3D)',
    icon: 'phoenix',
    longitude: 73.9168,
    latitude: 18.5595,
    height: 220,
    headingDegrees: 320,
    pitchDegrees: -28,
    rollDegrees: 0
  },
  {
    id: 'somnath-nagar-chowk',
    name: 'Somnath Nagar Chowk',
    icon: 'somnath',
    longitude: 73.9288,
    latitude: 18.5658,
    height: 180,
    headingDegrees: 245,
    pitchDegrees: -30,
    rollDegrees: 0
  },
  {
    id: 'top-down-plan',
    name: 'Nadir (Top-Down)',
    icon: 'topdown',
    longitude: 73.9205,
    latitude: 18.5635,
    height: 1600,
    headingDegrees: 0,
    pitchDegrees: -90,
    rollDegrees: 0
  }
];

interface CesiumCameraControlsProps {
  activeViewpointId?: string;
  onFlyToViewpoint: (viewpoint: CameraViewpoint) => void;
}

export const CesiumCameraControls: React.FC<CesiumCameraControlsProps> = ({
  activeViewpointId,
  onFlyToViewpoint
}) => {
  const renderIcon = (icon: CameraViewpoint['icon']) => {
    switch (icon) {
      case 'corridor':
        return <Eye size={14} className="viewpoint-icon" />;
      case 'viman':
        return <TrafficCone size={14} className="viewpoint-icon" />;
      case 'phoenix':
        return <Building2 size={14} className="viewpoint-icon" />;
      case 'somnath':
        return <TrafficCone size={14} className="viewpoint-icon" />;
      case 'topdown':
        return <Compass size={14} className="viewpoint-icon" />;
      default:
        return <MapPin size={14} className="viewpoint-icon" />;
    }
  };

  return (
    <div className="cesium-camera-toolbar" role="toolbar" aria-label="3D Corridor Camera Presets">
      <span className="cesium-camera-label">
        <Compass size={13} className="text-cyan-400" />
        <span>3D Views</span>
      </span>
      <div className="cesium-camera-buttons">
        {CORRIDOR_VIEWPOINTS.map((vp) => {
          const isActive = activeViewpointId === vp.id;
          return (
            <button
              key={vp.id}
              type="button"
              className={`cesium-camera-btn ${isActive ? 'active' : ''}`}
              title={`Fly camera to ${vp.name}`}
              onClick={() => onFlyToViewpoint(vp)}
            >
              {renderIcon(vp.icon)}
              <span>{vp.name}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
