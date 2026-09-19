import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import { EntityCurrentState, IntersectionAsset, RoadSegmentAsset } from '../types/twin';

interface MapOperationsViewProps {
  studyAreaGeoJson: any;
  roadSegments: RoadSegmentAsset[];
  intersections: IntersectionAsset[];
  liveStates: Record<string, EntityCurrentState>;
  onSelectEntity: (entity: RoadSegmentAsset | IntersectionAsset) => void;
}

export const MapOperationsView: React.FC<MapOperationsViewProps> = ({
  studyAreaGeoJson,
  roadSegments,
  intersections,
  liveStates,
  onSelectEntity
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);

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
      pitch: 25,
      attributionControl: false
    });

    map.current.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'bottom-right');
    map.current.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Render Study Area and Assets when data is ready
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

          return {
            type: 'Feature',
            id: seg.id,
            properties: {
              ...seg,
              color,
              speed
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
          if (found) onSelectEntity(found);
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

      // 3. Add Intersections Markers
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
  }, [studyAreaGeoJson, roadSegments, intersections, liveStates, onSelectEntity]);

  return <div ref={mapContainer} className="map-viewport" />;
};
