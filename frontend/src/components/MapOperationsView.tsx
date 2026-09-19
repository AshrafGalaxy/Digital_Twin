import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { EntityCurrentState, IntersectionAsset, RoadSegmentAsset } from '../types/twin';
import buildings3dGeoJson from '../assets/corridor_buildings_3d.json';

interface MapOperationsViewProps {
  studyAreaGeoJson: any;
  roadSegments: RoadSegmentAsset[];
  intersections: IntersectionAsset[];
  liveStates: Record<string, EntityCurrentState>;
  selectedEntity?: RoadSegmentAsset | IntersectionAsset | null;
  compareEntity?: RoadSegmentAsset | null;
  onSelectEntity: (entity: RoadSegmentAsset | IntersectionAsset) => void;
  onSelectCompareEntity?: (entity: RoadSegmentAsset | null) => void;
}

export const MapOperationsView: React.FC<MapOperationsViewProps> = ({
  studyAreaGeoJson,
  roadSegments,
  intersections,
  liveStates,
  selectedEntity,
  compareEntity,
  onSelectEntity,
  onSelectCompareEntity
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [is3DMode, setIs3DMode] = useState<boolean>(false);

  // Initialize MapLibre GL Map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'osm-tiles': {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          }
        },
        layers: [
          {
            id: 'osm-tiles-layer',
            type: 'raster',
            source: 'osm-tiles',
            minzoom: 0,
            maxzoom: 19,
            paint: {
              'raster-saturation': -0.7,
              'raster-brightness-max': 0.6,
              'raster-contrast': 0.2
            }
          }
        ]
      },
      center: [73.9220, 18.5615], // Corridor midpoint
      zoom: 14.5,
      pitch: 20,
      attributionControl: false
    });

    map.current.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'bottom-right');
    map.current.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Render Study Area, Assets, and 3D Extrusions when data is ready
  useEffect(() => {
    const currentMap = map.current;
    if (!currentMap) return;

    const onMapLoad = () => {
      // 1. Add Study Area Boundary Source and Layers
      if (studyAreaGeoJson && !currentMap.getSource('study-area')) {
        currentMap.addSource('study-area', {
          type: 'geojson',
          data: studyAreaGeoJson
        });

        currentMap.addLayer({
          id: 'study-area-fill',
          type: 'fill',
          source: 'study-area',
          paint: {
            'fill-color': '#0F4C5C',
            'fill-opacity': 0.12
          }
        });

        currentMap.addLayer({
          id: 'study-area-line',
          type: 'line',
          source: 'study-area',
          paint: {
            'line-color': '#22D3EE',
            'line-width': 1.5,
            'line-dasharray': [3, 2]
          }
        });
      }

      // 2. Add Road Segments
      const segmentsGeoJson = {
        type: 'FeatureCollection',
        features: roadSegments.map(seg => {
          const state = liveStates[seg.id];
          const speed = state?.metrics.averageSpeedKmh ?? 45.0;
          let color = '#10B981'; // Green
          if (speed < 20) color = '#EF4444'; // Red
          else if (speed < 35) color = '#F59E0B'; // Amber

          const isSelected = selectedEntity?.id === seg.id;
          const isCompare = compareEntity?.id === seg.id;
          let casingColor = 'transparent';
          let casingWidth = 0;
          if (isSelected) {
            casingColor = '#22D3EE';
            casingWidth = 11;
          } else if (isCompare) {
            casingColor = '#F59E0B';
            casingWidth = 10;
          }

          return {
            type: 'Feature',
            id: seg.id,
            properties: {
              ...seg,
              color,
              speed,
              isSelected,
              isCompare,
              casingColor,
              casingWidth
            },
            geometry: {
              type: 'LineString',
              coordinates: seg.coordinates
            }
          };
        })
      };

      if (!currentMap.getSource('road-segments')) {
        currentMap.addSource('road-segments', {
          type: 'geojson',
          data: segmentsGeoJson as any
        });

        // Background casing layer for selected & compared segments
        currentMap.addLayer({
          id: 'road-segments-casing',
          type: 'line',
          source: 'road-segments',
          layout: {
            'line-cap': 'round',
            'line-join': 'round'
          },
          paint: {
            'line-color': ['get', 'casingColor'],
            'line-width': ['get', 'casingWidth'],
            'line-opacity': 0.85
          }
        });

        currentMap.addLayer({
          id: 'road-segments-line',
          type: 'line',
          source: 'road-segments',
          layout: {
            'line-cap': 'round',
            'line-join': 'round'
          },
          paint: {
            'line-color': ['get', 'color'],
            'line-width': 6,
            'line-opacity': 0.9
          }
        });

        currentMap.on('click', 'road-segments-line', (e) => {
          if (!e.features || !e.features[0]) return;
          const clickedId = e.features[0].id;
          const found = roadSegments.find(s => s.id === clickedId);
          if (!found) return;

          // If Shift is pressed while another road segment is active, set comparison target
          if (e.originalEvent.shiftKey && onSelectCompareEntity && selectedEntity && 'speedLimitKmh' in selectedEntity && selectedEntity.id !== found.id) {
            onSelectCompareEntity(found);
          } else {
            onSelectEntity(found);
          }
        });

        currentMap.on('mouseenter', 'road-segments-line', () => {
          currentMap.getCanvas().style.cursor = 'pointer';
        });
        currentMap.on('mouseleave', 'road-segments-line', () => {
          currentMap.getCanvas().style.cursor = '';
        });
      } else {
        (currentMap.getSource('road-segments') as maplibregl.GeoJSONSource).setData(segmentsGeoJson as any);
      }

      // 3. Add 3D Building Extrusions Layer (Phase 8, D-13)
      if (!currentMap.getSource('corridor-buildings-3d')) {
        currentMap.addSource('corridor-buildings-3d', {
          type: 'geojson',
          data: buildings3dGeoJson as any
        });

        currentMap.addLayer({
          id: 'corridor-buildings-extrusion',
          type: 'fill-extrusion',
          source: 'corridor-buildings-3d',
          layout: {
            visibility: is3DMode ? 'visible' : 'none'
          },
          paint: {
            'fill-extrusion-color': ['get', 'color'],
            'fill-extrusion-height': ['get', 'height'],
            'fill-extrusion-base': ['get', 'base_height'],
            'fill-extrusion-opacity': 0.88
          }
        });
      } else if (currentMap.getLayer('corridor-buildings-extrusion')) {
        currentMap.setLayoutProperty(
          'corridor-buildings-extrusion',
          'visibility',
          is3DMode ? 'visible' : 'none'
        );
      }

      // 4. Add Intersections Markers
      intersections.forEach(ix => {
        const el = document.createElement('div');
        el.className = 'intersection-marker';
        el.style.width = '14px';
        el.style.height = '14px';
        el.style.borderRadius = '50%';
        el.style.backgroundColor = '#0F4C5C';
        el.style.border = '2px solid #22D3EE';
        el.style.boxShadow = '0 0 10px rgba(34, 211, 238, 0.6)';
        el.style.cursor = 'pointer';

        el.addEventListener('click', () => {
          onSelectEntity(ix);
        });

        new maplibregl.Marker({ element: el })
          .setLngLat(ix.coordinates)
          .addTo(currentMap);
      });
    };

    if (currentMap.isStyleLoaded()) {
      onMapLoad();
    } else {
      currentMap.once('load', onMapLoad);
    }
  }, [studyAreaGeoJson, roadSegments, intersections, liveStates, selectedEntity, compareEntity, onSelectEntity, onSelectCompareEntity, is3DMode]);

  const toggle3DMode = () => {
    const currentMap = map.current;
    if (!currentMap) return;

    if (!is3DMode) {
      // Transition camera to 3D Extrusion perspective
      currentMap.easeTo({
        pitch: 58,
        bearing: -22,
        zoom: 15.3,
        duration: 1400
      });
      if (currentMap.getLayer('corridor-buildings-extrusion')) {
        currentMap.setLayoutProperty('corridor-buildings-extrusion', 'visibility', 'visible');
      }
      setIs3DMode(true);
    } else {
      // Smoothly return to 2D Operational Baseline
      currentMap.easeTo({
        pitch: 20,
        bearing: 0,
        zoom: 14.5,
        duration: 1100
      });
      if (currentMap.getLayer('corridor-buildings-extrusion')) {
        currentMap.setLayoutProperty('corridor-buildings-extrusion', 'visibility', 'none');
      }
      setIs3DMode(false);
    }
  };

  return (
    <div className="map-container-relative" style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={mapContainer} className="map-viewport" />

      {/* 3D Presentation Mode Overlay Controls */}
      <div className="map-3d-controls-overlay">
        <button
          type="button"
          className={`map-3d-toggle-btn ${is3DMode ? 'active' : ''}`}
          onClick={toggle3DMode}
          title={is3DMode ? "Return to 2D Operations Map" : "Enable 3D Corridor Extrusions Presentation"}
        >
          <span className="btn-icon">{is3DMode ? '🌐' : '🏢'}</span>
          <span>{is3DMode ? '3D Extrusions Active' : 'Enable 3D View'}</span>
        </button>
        {is3DMode && (
          <span className="provenance-badge badge-simulation" style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.4)' }}>
            3D SIMULATION
          </span>
        )}
      </div>
    </div>
  );
};
