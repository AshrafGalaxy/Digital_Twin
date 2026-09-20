import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { EntityCurrentState, IntersectionAsset, RoadSegmentAsset } from '../types/twin';
import buildings3dGeoJson from '../assets/corridor_buildings_3d.json';
import { ProvenanceBadge } from './ProvenanceBadge';

interface MapOperationsViewProps {
  studyAreaGeoJson: any;
  roadSegments: RoadSegmentAsset[];
  intersections: IntersectionAsset[];
  liveStates: Record<string, EntityCurrentState>;
  selectedEntity?: RoadSegmentAsset | IntersectionAsset | null;
  compareEntity?: RoadSegmentAsset | null;
  currentTheme?: 'light' | 'dark';
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
  currentTheme = 'dark',
  onSelectEntity,
  onSelectCompareEntity
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const [is3DMode, setIs3DMode] = useState<boolean>(false);
  const [isTableView, setIsTableView] = useState<boolean>(false);

  // Initialize MapLibre GL Map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    const isLight = currentTheme === 'light';

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
              'raster-saturation': isLight ? -0.15 : -0.7,
              'raster-brightness-max': isLight ? 0.98 : 0.6,
              'raster-contrast': isLight ? 0.05 : 0.2
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
      markersRef.current.forEach(m => m.remove());
      markersRef.current = [];
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Dynamically update map raster styling and vector layers on theme toggle
  useEffect(() => {
    const currentMap = map.current;
    if (!currentMap) return;

    const isLight = currentTheme === 'light';
    const applyTheme = () => {
      if (currentMap.getLayer('osm-tiles-layer')) {
        currentMap.setPaintProperty('osm-tiles-layer', 'raster-saturation', isLight ? -0.15 : -0.7);
        currentMap.setPaintProperty('osm-tiles-layer', 'raster-brightness-max', isLight ? 0.98 : 0.6);
        currentMap.setPaintProperty('osm-tiles-layer', 'raster-contrast', isLight ? 0.05 : 0.2);
      }
      if (currentMap.getLayer('study-area-line')) {
        currentMap.setPaintProperty('study-area-line', 'line-color', isLight ? '#006B6F' : '#22D3EE');
      }
      if (currentMap.getLayer('study-area-fill')) {
        currentMap.setPaintProperty('study-area-fill', 'fill-color', isLight ? '#006B6F' : '#0F4C5C');
        currentMap.setPaintProperty('study-area-fill', 'fill-opacity', isLight ? 0.08 : 0.12);
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
      markersRef.current.forEach(m => m.remove());
      markersRef.current = [];

      const isLight = currentTheme === 'light';
      intersections.forEach(ix => {
        const el = document.createElement('div');
        el.className = 'intersection-marker';
        el.style.width = '14px';
        el.style.height = '14px';
        el.style.borderRadius = '50%';
        el.style.backgroundColor = isLight ? '#006B6F' : '#0F4C5C';
        el.style.border = isLight ? '2px solid #00565A' : '2px solid #22D3EE';
        el.style.boxShadow = isLight ? '0 1px 4px rgba(0, 107, 111, 0.4)' : '0 0 10px rgba(34, 211, 238, 0.6)';
        el.style.cursor = 'pointer';

        el.addEventListener('click', () => {
          onSelectEntity(ix);
        });

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat(ix.coordinates)
          .addTo(currentMap);
        markersRef.current.push(marker);
      });

      // 5. Add Energy Entity Marker (Phoenix Marketcity) per UI_UX_SPEC §7.3
      const energyEl = document.createElement('div');
      energyEl.className = 'energy-entity-marker';
      energyEl.style.display = 'flex';
      energyEl.style.alignItems = 'center';
      energyEl.style.gap = '4px';
      energyEl.style.padding = '3px 7px';
      energyEl.style.borderRadius = '12px';
      energyEl.style.backgroundColor = isLight ? '#FFF' : '#1E293B';
      energyEl.style.border = '1.5px solid #F59E0B';
      energyEl.style.boxShadow = '0 2px 6px rgba(0,0,0,0.3)';
      energyEl.style.fontSize = '12px';
      energyEl.style.fontWeight = '600';
      energyEl.style.color = isLight ? '#B45309' : '#FBBF24';
      energyEl.style.cursor = 'pointer';
      energyEl.title = 'Phoenix Marketcity Commercial Energy Zone (Sanctioned: 8,500 kVA)';
      energyEl.innerHTML = '⚡ Phoenix (Energy)';
      const energyMarker = new maplibregl.Marker({ element: energyEl })
        .setLngLat([73.9170, 18.5625])
        .addTo(currentMap);
      markersRef.current.push(energyMarker);

      // 6. Add Environmental Context Station Marker (Lohegaon CAAQMS) per UI_UX_SPEC §7.3
      const envEl = document.createElement('div');
      envEl.className = 'env-station-marker';
      envEl.style.display = 'flex';
      envEl.style.alignItems = 'center';
      envEl.style.gap = '4px';
      envEl.style.padding = '3px 7px';
      envEl.style.borderRadius = '12px';
      envEl.style.backgroundColor = isLight ? '#FFF' : '#1E293B';
      envEl.style.border = '1.5px solid #10B981';
      envEl.style.boxShadow = '0 2px 6px rgba(0,0,0,0.3)';
      envEl.style.fontSize = '12px';
      envEl.style.fontWeight = '600';
      envEl.style.color = isLight ? '#047857' : '#34D399';
      envEl.style.cursor = 'pointer';
      envEl.title = 'Pune Airport / Lohegaon CAAQMS Air Quality Reference Station (NAAQS: Moderate)';
      envEl.innerHTML = '🍃 CAAQMS Air Station';
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
    const currentMap = map.current;
    if (!currentMap) return;

    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (!is3DMode) {
      // Transition camera to 3D Extrusion perspective
      if (prefersReducedMotion) {
        currentMap.jumpTo({
          pitch: 58,
          bearing: -22,
          zoom: 15.3
        });
      } else {
        currentMap.easeTo({
          pitch: 58,
          bearing: -22,
          zoom: 15.3,
          duration: 1400
        });
      }
      if (currentMap.getLayer('corridor-buildings-extrusion')) {
        currentMap.setLayoutProperty('corridor-buildings-extrusion', 'visibility', 'visible');
      }
      setIs3DMode(true);
    } else {
      // Return to 2D Operational Baseline
      if (prefersReducedMotion) {
        currentMap.jumpTo({
          pitch: 20,
          bearing: 0,
          zoom: 14.5
        });
      } else {
        currentMap.easeTo({
          pitch: 20,
          bearing: 0,
          zoom: 14.5,
          duration: 1100
        });
      }
      if (currentMap.getLayer('corridor-buildings-extrusion')) {
        currentMap.setLayoutProperty('corridor-buildings-extrusion', 'visibility', 'none');
      }
      setIs3DMode(false);
    }
  };

  return (
    <div className="map-container-relative" style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={mapContainer} className="map-viewport" />

      {/* 3D Presentation & Accessibility Mode Overlay Controls */}
      <div className="map-3d-controls-overlay">
        <button
          type="button"
          className={`map-view-toggle-btn ${isTableView ? 'active' : ''}`}
          onClick={() => setIsTableView(!isTableView)}
          title={isTableView ? "Return to Visual 2D Map Canvas" : "Switch to Synchronized Accessible Table View (WCAG Fallback per UI_UX_SPEC §18.2)"}
        >
          <span>{isTableView ? '🗺️ 2D Map View' : '📋 Accessible Table View'}</span>
        </button>

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

      {/* Accessible Synchronized Table View per UI_UX_SPEC §18.2 */}
      {isTableView && (
        <div className="accessible-map-table-view" role="region" aria-label="Synchronized Corridor Map Information Table">
          <div className="accessible-table-header">
            <div>
              <h2 className="accessible-table-title">Synchronized Corridor Telemetry & Asset Table</h2>
              <p className="accessible-table-caption">
                Screen-reader and keyboard accessible tabular alternative for spatial corridor map layers per UI_UX_SPEC §18.2 (WCAG 2.1 AA).
              </p>
            </div>
            <button
              className="map-view-toggle-btn"
              onClick={() => setIsTableView(false)}
              style={{ fontSize: '12px' }}
            >
              Close Table & Return to Map
            </button>
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
                            setIsTableView(false);
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
                          setIsTableView(false);
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
