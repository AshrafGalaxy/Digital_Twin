import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { Map, Globe, TableProperties } from 'lucide-react';
import { EntityCurrentState, IntersectionAsset, RoadSegmentAsset } from '../types/twin';
import buildings3dGeoJson from '../assets/corridor_buildings_3d.json';
import { ProvenanceBadge } from './ProvenanceBadge';
import { CesiumCorridorViewer } from './CesiumCorridorViewer';

interface MapOperationsViewProps {
  studyAreaGeoJson: any;
  roadSegments: RoadSegmentAsset[];
  intersections: IntersectionAsset[];
  liveStates: Record<string, EntityCurrentState>;
  selectedEntity?: RoadSegmentAsset | IntersectionAsset | null;
  compareEntity?: RoadSegmentAsset | null;
  currentTheme?: 'light' | 'dark';
  isTableView?: boolean;
  onToggleTableView?: (isTable: boolean) => void;
  onSelectEntity: (entity: RoadSegmentAsset | IntersectionAsset) => void;
  onSelectCompareEntity?: (entity: RoadSegmentAsset | null) => void;
}

// Stopline geometry for signalized intersection approaches (Navigation Grade)
const STOPLINES_GEOJSON = {
  type: 'FeatureCollection' as const,
  features: [
    {
      type: 'Feature' as const,
      id: 'stopline-vn-eb',
      properties: { id: 'stopline-vn-eb', name: 'Viman Nagar EB Stopline' },
      geometry: {
        type: 'LineString' as const,
        coordinates: [
          [73.91645, 18.56008],
          [73.91655, 18.56028]
        ]
      }
    },
    {
      type: 'Feature' as const,
      id: 'stopline-vn-wb',
      properties: { id: 'stopline-vn-wb', name: 'Viman Nagar WB Stopline' },
      geometry: {
        type: 'LineString' as const,
        coordinates: [
          [73.91705, 18.56032],
          [73.91715, 18.56052]
        ]
      }
    },
    {
      type: 'Feature' as const,
      id: 'stopline-vn-nb',
      properties: { id: 'stopline-vn-nb', name: 'Viman Nagar NB Approach Stopline' },
      geometry: {
        type: 'LineString' as const,
        coordinates: [
          [73.91662, 18.55992],
          [73.91692, 18.55992]
        ]
      }
    },
    {
      type: 'Feature' as const,
      id: 'stopline-sn-eb',
      properties: { id: 'stopline-sn-eb', name: 'Somnath Nagar EB Stopline' },
      geometry: {
        type: 'LineString' as const,
        coordinates: [
          [73.92765, 18.56288],
          [73.92775, 18.56308]
        ]
      }
    },
    {
      type: 'Feature' as const,
      id: 'stopline-sn-wb',
      properties: { id: 'stopline-sn-wb', name: 'Somnath Nagar WB Stopline' },
      geometry: {
        type: 'LineString' as const,
        coordinates: [
          [73.92825, 18.56312],
          [73.92835, 18.56332]
        ]
      }
    },
    {
      type: 'Feature' as const,
      id: 'stopline-sn-nb',
      properties: { id: 'stopline-sn-nb', name: 'Somnath Nagar NB Approach Stopline' },
      geometry: {
        type: 'LineString' as const,
        coordinates: [
          [73.92782, 18.56275],
          [73.92812, 18.56275]
        ]
      }
    }
  ]
};

// Generates an offscreen directional chevron arrow for roadway traffic flow markers
const createFlowArrowImage = (): ImageData | null => {
  if (typeof document === 'undefined') return null;
  const canvas = document.createElement('canvas');
  canvas.width = 24;
  canvas.height = 24;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  ctx.clearRect(0, 0, 24, 24);
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
  ctx.lineWidth = 2.5;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.beginPath();
  ctx.moveTo(8, 5);
  ctx.lineTo(16, 12);
  ctx.lineTo(8, 19);
  ctx.stroke();
  return ctx.getImageData(0, 0, 24, 24);
};

export const MapOperationsView: React.FC<MapOperationsViewProps> = ({
  studyAreaGeoJson,
  roadSegments,
  intersections,
  liveStates,
  selectedEntity,
  compareEntity,
  currentTheme = 'dark',
  isTableView: isTableViewProp,
  onToggleTableView,
  onSelectEntity,
  onSelectCompareEntity
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const [is3DMode, setIs3DMode] = useState<boolean>(false);
  const [internalTableView, setInternalTableView] = useState<boolean>(false);

  const isTableView = isTableViewProp !== undefined ? isTableViewProp : internalTableView;
  const handleToggleTableView = (val: boolean) => {
    setInternalTableView(val);
    if (onToggleTableView) onToggleTableView(val);
  };

  // Initialize MapLibre GL Map with High-Resolution Carto Dark Matter Retina Tiles
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'carto-dark': {
            type: 'raster',
            tiles: [
              'https://a.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}@2x.png',
              'https://b.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}@2x.png',
              'https://c.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}@2x.png',
              'https://d.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}@2x.png'
            ],
            tileSize: 256,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions" target="_blank" rel="noopener">CARTO</a>'
          }
        },
        layers: [
          {
            id: 'carto-dark-layer',
            type: 'raster',
            source: 'carto-dark',
            minzoom: 0,
            maxzoom: 20
          }
        ]
      },
      center: [73.9220, 18.5615], // Corridor midpoint
      zoom: 14.8,
      pitch: 0,
      attributionControl: false
    });

    map.current.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'bottom-right');
    map.current.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

    return () => {
      markersRef.current.forEach(m => m.remove());
      markersRef.current = [];
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Dynamically update map styling on theme toggle
  useEffect(() => {
    const currentMap = map.current;
    if (!currentMap) return;

    const applyTheme = () => {
      if (currentMap.getLayer('study-area-line')) {
        currentMap.setPaintProperty('study-area-line', 'line-color', '#388BFD');
      }
      if (currentMap.getLayer('study-area-fill')) {
        currentMap.setPaintProperty('study-area-fill', 'fill-color', '#1F6FEB');
        currentMap.setPaintProperty('study-area-fill', 'fill-opacity', 0.04);
      }
    };

    if (currentMap.isStyleLoaded()) {
      applyTheme();
    } else {
      currentMap.once('load', applyTheme);
    }
  }, [currentTheme]);

  // Render Study Area, Assets, and 3D Extrusions when data is ready
  useEffect(() => {
    const currentMap = map.current;
    if (!currentMap) return;

    const onMapLoad = () => {
      // 0. Register directional flow arrow image if not already present
      if (!currentMap.hasImage('flow-arrow')) {
        const arrowImg = createFlowArrowImage();
        if (arrowImg) {
          currentMap.addImage('flow-arrow', arrowImg);
        }
      }

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
            'fill-color': '#1F6FEB',
            'fill-opacity': 0.04
          }
        });

        currentMap.addLayer({
          id: 'study-area-line',
          type: 'line',
          source: 'study-area',
          paint: {
            'line-color': '#388BFD',
            'line-width': 1.5,
            'line-dasharray': [4, 3],
            'line-opacity': 0.7
          }
        });
      }

      // 2. Add Road Segments (Navigation-Grade Dual-Carriageway Ribbons)
      const segmentsGeoJson = {
        type: 'FeatureCollection',
        features: roadSegments.map(seg => {
          const state = liveStates[seg.id];
          const speed = state?.metrics.averageSpeedKmh ?? 45.0;
          let color = '#3FB950'; // Green: Normal (>35 km/h)
          if (speed < 20) color = '#F85149'; // Red: Congested (<20 km/h)
          else if (speed < 35) color = '#D29922'; // Amber: Moderate (20-35 km/h)

          const isSelected = selectedEntity?.id === seg.id;
          const isCompare = compareEntity?.id === seg.id;
          let casingColor = 'transparent';
          if (isSelected) {
            casingColor = '#2F81F7';
          } else if (isCompare) {
            casingColor = '#D29922';
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
              casingColor
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

        // Layer 1: Dark asphalt roadway base (foundation)
        currentMap.addLayer({
          id: 'road-segments-asphalt',
          type: 'line',
          source: 'road-segments',
          layout: {
            'line-cap': 'round',
            'line-join': 'round'
          },
          paint: {
            'line-color': '#161B22',
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              12, 6,
              14, 11,
              16, 17,
              18, 24
            ],
            'line-opacity': 0.95
          }
        });

        // Layer 2: Selection & Compare highlight halo casing
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
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              12, ['case', ['get', 'isSelected'], 9, ['get', 'isCompare'], 8, 0],
              14, ['case', ['get', 'isSelected'], 15, ['get', 'isCompare'], 14, 0],
              16, ['case', ['get', 'isSelected'], 22, ['get', 'isCompare'], 20, 0],
              18, ['case', ['get', 'isSelected'], 30, ['get', 'isCompare'], 28, 0]
            ],
            'line-opacity': 0.95
          }
        });

        // Layer 3: Navigation velocity traffic ribbon fill
        currentMap.addLayer({
          id: 'road-segments-fill',
          type: 'line',
          source: 'road-segments',
          layout: {
            'line-cap': 'round',
            'line-join': 'round'
          },
          paint: {
            'line-color': ['get', 'color'],
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              12, 3.5,
              14, 7,
              16, 11,
              18, 16
            ],
            'line-opacity': 1.0
          }
        });

        // Layer 4: Subtle dashed inner lane dividers
        currentMap.addLayer({
          id: 'road-segments-divider',
          type: 'line',
          source: 'road-segments',
          layout: {
            'line-cap': 'butt',
            'line-join': 'round'
          },
          paint: {
            'line-color': 'rgba(255, 255, 255, 0.4)',
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              12, 0.8,
              14, 1.2,
              16, 1.8,
              18, 2.4
            ],
            'line-dasharray': [4, 4]
          }
        });

        // Layer 5: Directional chevron flow indicators along traffic direction
        currentMap.addLayer({
          id: 'road-segments-flow-arrows',
          type: 'symbol',
          source: 'road-segments',
          layout: {
            'symbol-placement': 'line',
            'symbol-spacing': 90,
            'icon-image': 'flow-arrow',
            'icon-size': [
              'interpolate', ['linear'], ['zoom'],
              12, 0.4,
              14, 0.6,
              16, 0.8,
              18, 1.0
            ],
            'icon-rotation-alignment': 'map',
            'icon-keep-upright': false,
            'icon-allow-overlap': true,
            'icon-ignore-placement': true
          }
        });

        const handleRoadClick = (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
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
        };

        currentMap.on('click', 'road-segments-fill', handleRoadClick);
        currentMap.on('click', 'road-segments-asphalt', handleRoadClick);

        currentMap.on('mouseenter', 'road-segments-fill', () => {
          currentMap.getCanvas().style.cursor = 'pointer';
        });
        currentMap.on('mouseleave', 'road-segments-fill', () => {
          currentMap.getCanvas().style.cursor = '';
        });
      } else {
        (currentMap.getSource('road-segments') as maplibregl.GeoJSONSource).setData(segmentsGeoJson as any);
      }

      // 3. Add Intersection Approach Stoplines (Navigation Grade)
      if (!currentMap.getSource('intersection-stoplines')) {
        currentMap.addSource('intersection-stoplines', {
          type: 'geojson',
          data: STOPLINES_GEOJSON as any
        });

        currentMap.addLayer({
          id: 'intersection-stoplines-casing',
          type: 'line',
          source: 'intersection-stoplines',
          paint: {
            'line-color': '#0D1117',
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              13, 3,
              15, 5,
              17, 7
            ]
          }
        });

        currentMap.addLayer({
          id: 'intersection-stoplines-bar',
          type: 'line',
          source: 'intersection-stoplines',
          layout: {
            'line-cap': 'square'
          },
          paint: {
            'line-color': '#FFFFFF',
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              13, 2,
              15, 3.5,
              17, 5
            ],
            'line-opacity': 0.95
          }
        });
      }

      // 4. Add 3D Building Extrusions Layer
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

      // 5. Add Signalized Intersection Markers (Navigation Chowk Badges & Pulsing Halos)
      markersRef.current.forEach(m => m.remove());
      markersRef.current = [];

      intersections.forEach(ix => {
        const isSelected = selectedEntity?.id === ix.id;
        const el = document.createElement('div');
        el.className = `junction-marker-container ${isSelected ? 'selected' : ''}`;
        el.title = `${ix.name} (${ix.controlType}) - Click to inspect`;

        const pulse = document.createElement('div');
        pulse.className = 'junction-pulse-ring';
        el.appendChild(pulse);

        const beacon = document.createElement('div');
        beacon.className = 'junction-beacon';
        beacon.innerHTML = '🚦';
        el.appendChild(beacon);

        const label = document.createElement('div');
        label.className = 'junction-label-pill';

        const title = document.createElement('span');
        title.className = 'junction-title';
        const cleanName = ix.name.includes('(') ? ix.name.split('(')[0].trim() : ix.name;
        title.textContent = cleanName;
        label.appendChild(title);

        const sub = document.createElement('span');
        sub.className = 'junction-subtitle';
        sub.textContent = `${ix.cycleTimeSec ? ix.cycleTimeSec + 's' : 'Signal'} • ${ix.controlType === 'SIGNALIZED' ? 'Adaptive' : ix.controlType}`;
        label.appendChild(sub);

        el.appendChild(label);

        el.addEventListener('click', (ev) => {
          ev.stopPropagation();
          onSelectEntity(ix);
        });

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat(ix.coordinates)
          .addTo(currentMap);
        markersRef.current.push(marker);
      });

      // 6. Add Energy Entity Marker (Phoenix Marketcity) per UI_UX_SPEC §7.3
      const energyEl = document.createElement('div');
      energyEl.className = 'energy-entity-marker';
      energyEl.style.display = 'flex';
      energyEl.style.alignItems = 'center';
      energyEl.style.gap = '5px';
      energyEl.style.padding = '3px 8px';
      energyEl.style.borderRadius = '6px';
      energyEl.style.backgroundColor = '#161B22';
      energyEl.style.border = '1px solid #D29922';
      energyEl.style.boxShadow = '0 2px 8px rgba(0,0,0,0.5)';
      energyEl.style.fontSize = '11px';
      energyEl.style.fontWeight = '600';
      energyEl.style.color = '#F0883E';
      energyEl.style.cursor = 'pointer';
      energyEl.title = 'Phoenix Marketcity Commercial Energy Zone (Sanctioned: 8,500 kVA)';
      energyEl.innerHTML = '<span>⚡</span><span>Phoenix Marketcity (Energy)</span>';
      const energyMarker = new maplibregl.Marker({ element: energyEl })
        .setLngLat([73.9170, 18.5625])
        .addTo(currentMap);
      markersRef.current.push(energyMarker);

      // 7. Add Environmental Context Station Marker (Lohegaon CAAQMS) per UI_UX_SPEC §7.3
      const envEl = document.createElement('div');
      envEl.className = 'env-station-marker';
      envEl.style.display = 'flex';
      envEl.style.alignItems = 'center';
      envEl.style.gap = '5px';
      envEl.style.padding = '3px 8px';
      envEl.style.borderRadius = '6px';
      envEl.style.backgroundColor = '#161B22';
      envEl.style.border = '1px solid #3FB950';
      envEl.style.boxShadow = '0 2px 8px rgba(0,0,0,0.5)';
      envEl.style.fontSize = '11px';
      envEl.style.fontWeight = '600';
      envEl.style.color = '#3FB950';
      envEl.style.cursor = 'pointer';
      envEl.title = 'Pune Airport / Lohegaon CAAQMS Air Quality Reference Station (NAAQS: Moderate)';
      envEl.innerHTML = '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#3FB950;box-shadow:0 0 6px #3FB950;"></span><span>Lohegaon CAAQMS</span>';
      const envMarker = new maplibregl.Marker({ element: envEl })
        .setLngLat([73.9215, 18.5665])
        .addTo(currentMap);
      markersRef.current.push(envMarker);
    };

    if (currentMap.isStyleLoaded()) {
      onMapLoad();
    } else {
      currentMap.once('load', onMapLoad);
    }
  }, [studyAreaGeoJson, roadSegments, intersections, liveStates, selectedEntity, compareEntity, onSelectEntity, onSelectCompareEntity, is3DMode, currentTheme]);

  const toggle3DMode = () => {
    setIs3DMode(prev => {
      const next = !prev;
      if (!next && map.current) {
        setTimeout(() => {
          map.current?.resize();
        }, 60);
      }
      return next;
    });
  };

  return (
    <div className="map-container-relative" style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* 2D MapLibre Operational Map */}
      <div
        ref={mapContainer}
        className="map-viewport"
        style={{
          width: '100%',
          height: '100%',
          display: is3DMode ? 'none' : 'block'
        }}
      />

      {/* 3D Cesium Corridor Digital Twin */}
      {is3DMode && (
        <CesiumCorridorViewer
          roadSegments={roadSegments}
          intersections={intersections}
          liveStates={liveStates}
          selectedEntity={selectedEntity}
          currentTheme={currentTheme}
          onSelectEntity={onSelectEntity}
        />
      )}

      {/* 3D Presentation & Accessibility Mode Overlay Controls (Hidden in Table View to eliminate overlap) */}
      {!isTableView && (
        <div className="map-3d-controls-overlay" role="toolbar" aria-label="Map Presentation Controls">
          <button
            type="button"
            className="map-view-toggle-btn"
            onClick={() => handleToggleTableView(true)}
            title="Switch to Synchronized Accessible Table View (WCAG 2.1 AA)"
          >
            <TableProperties size={13} aria-hidden="true" />
            <span>Table View</span>
          </button>

          <button
            type="button"
            className={`map-3d-toggle-btn ${is3DMode ? 'active' : ''}`}
            onClick={toggle3DMode}
            title={is3DMode ? "Switch to 2D MapLibre View" : "Enable Cesium 3D Corridor Digital Twin"}
          >
            {is3DMode ? <Map size={13} aria-hidden="true" /> : <Globe size={13} aria-hidden="true" />}
            <span>{is3DMode ? '2D Map' : '3D Twin'}</span>
          </button>
          {is3DMode && (
            <span className="provenance-badge badge-simulation" style={{ boxShadow: '0 2px 8px rgba(0,0,0,0.4)' }}>
              3D DIGITAL TWIN
            </span>
          )}
        </div>
      )}

      {/* Accessible Synchronized Table View */}
      {isTableView && (
        <div className="accessible-map-table-view" role="region" aria-label="Synchronized Corridor Map Information Table">
          <div className="accessible-table-header">
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TableProperties size={18} color="var(--color-primary, #2F81F7)" />
                <h2 className="accessible-table-title">Synchronized Corridor Telemetry & Asset Table</h2>
                <span className="provenance-badge badge-live" style={{ fontSize: '11px', height: '22px' }}>WCAG 2.1 AA</span>
              </div>
              <p className="accessible-table-caption">
                Screen-reader and keyboard accessible tabular alternative for spatial corridor map layers. Real-time telemetry, levels of service, and intersection controllers.
              </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                type="button"
                className="btn btn-primary btn-sm"
                onClick={() => handleToggleTableView(false)}
                style={{ height: '32px', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <Map size={14} />
                <span>Return to Visual Map Canvas</span>
              </button>
            </div>
          </div>

          <h3 style={{ fontSize: '14px', fontWeight: 600, marginTop: '12px', marginBottom: '8px' }}>
            Road Segments ({roadSegments.length})
          </h3>
          <div className="table-responsive">
            <table className="analytics-table" aria-label="Corridor Road Segments Telemetry">
              <thead>
                <tr>
                  <th scope="col">Segment Name & ID</th>
                  <th scope="col">Direction & Lanes</th>
                  <th scope="col">Speed Limit</th>
                  <th scope="col">Current Speed & LOS</th>
                  <th scope="col">15m Forecast</th>
                  <th scope="col">Source Mode</th>
                  <th scope="col">Freshness</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {roadSegments.map(seg => {
                  const state = liveStates[seg.id];
                  const speed = state?.metrics.averageSpeedKmh ?? 45.0;
                  const los = speed >= 42 ? 'A' : speed >= 38 ? 'B' : speed >= 32 ? 'C' : speed >= 25 ? 'D' : speed >= 18 ? 'E' : 'F';
                  const mode = state?.sourceMode || 'SIMULATION';
                  return (
                    <tr key={seg.id} className={selectedEntity?.id === seg.id ? 'row-selected' : ''}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{seg.name}</div>
                        <code style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{seg.id}</code>
                      </td>
                      <td>
                        <span className="dir-tag">{seg.direction}</span> ({seg.lanes} lanes)
                      </td>
                      <td className="mono-cell">{seg.speedLimitKmh} km/h</td>
                      <td>
                        <span style={{ fontWeight: 700, color: speed < 20 ? '#EF4444' : speed < 35 ? '#F59E0B' : '#10B981' }}>
                          {speed.toFixed(1)} km/h
                        </span>{' '}
                        <span className={`los-badge los-${los.toLowerCase()}`}>LOS {los}</span>
                      </td>
                      <td>
                        <span className="font-mono">
                          {Math.max(12, speed * 0.94).toFixed(1)} km/h
                        </span>
                      </td>
                      <td>
                        <ProvenanceBadge mode={mode} />
                      </td>
                      <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                        {state?.freshnessSeconds ? `${state.freshnessSeconds.toFixed(1)}s ago` : 'Real-time'}
                      </td>
                      <td>
                        <button
                          className="btn-select-sm"
                          onClick={() => {
                            onSelectEntity(seg);
                            handleToggleTableView(false);
                          }}
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <h3 style={{ fontSize: '14px', fontWeight: 600, marginTop: '20px', marginBottom: '8px' }}>
            Intersections & Critical Junctions ({intersections.length})
          </h3>
          <div className="table-responsive">
            <table className="analytics-table" aria-label="Corridor Intersections">
              <thead>
                <tr>
                  <th scope="col">Junction Name & ID</th>
                  <th scope="col">Control Type</th>
                  <th scope="col">Cycle Time</th>
                  <th scope="col">Connected Segments</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {intersections.map(ix => (
                  <tr key={ix.id} className={selectedEntity?.id === ix.id ? 'row-selected' : ''}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{ix.name}</div>
                      <code style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{ix.id}</code>
                    </td>
                    <td>{ix.controlType}</td>
                    <td className="mono-cell">{ix.cycleTimeSec}s</td>
                    <td style={{ fontSize: '12px' }}>
                      {ix.connectedSegments?.join(', ') || 'Nagar Road Arterial'}
                    </td>
                    <td>
                      <button
                        className="btn-select-sm"
                        onClick={() => {
                          onSelectEntity(ix);
                          handleToggleTableView(false);
                        }}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
