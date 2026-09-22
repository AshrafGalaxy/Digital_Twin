import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { Map, Globe, TableProperties } from 'lucide-react';
import { EntityCurrentState, IntersectionAsset, RoadSegmentAsset } from '../types/twin';
import { ProvenanceBadge } from './ProvenanceBadge';
import { CesiumCorridorViewer } from './CesiumCorridorViewer';
import { fetchCorridor3DGeoJson } from '../services/spatialApi';
import { Corridor3DFeatureCollection } from '../types/spatial';

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

// Stopline geometry for signalized intersection approaches (Surveyed Ground Truth, Indian LHD)
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
          [73.91814, 18.56070],
          [73.91816, 18.56084]
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
          [73.91834, 18.56096],
          [73.91836, 18.56110]
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
          [73.91818, 18.56068],
          [73.91828, 18.56068]
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
          [73.92776, 18.56260],
          [73.92780, 18.56274]
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
          [73.92800, 18.56286],
          [73.92804, 18.56300]
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
          [73.92785, 18.56275],
          [73.92795, 18.56275]
        ]
      }
    }
  ]
};

// Intersection Yellow Box Junction Polygons (Do Not Block Chowk)
const JUNCTION_BOXES_GEOJSON = {
  type: 'FeatureCollection' as const,
  features: [
    {
      type: 'Feature' as const,
      id: 'box-vn',
      properties: { id: 'box-vn', name: 'Viman Nagar Yellow Box Junction' },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [
          [
            [73.91816, 18.56070],
            [73.91834, 18.56070],
            [73.91834, 18.56110],
            [73.91816, 18.56110],
            [73.91816, 18.56070]
          ]
        ]
      }
    },
    {
      type: 'Feature' as const,
      id: 'box-sn',
      properties: { id: 'box-sn', name: 'Somnath Nagar Yellow Box Junction' },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [
          [
            [73.92778, 18.56260],
            [73.92802, 18.56260],
            [73.92802, 18.56300],
            [73.92778, 18.56300],
            [73.92778, 18.56260]
          ]
        ]
      }
    }
  ]
};

// Pedestrian Zebra Crossing Markings across Intersection Approach Legs (IRC:35 High-Fidelity)
const ZEBRA_CROSSINGS_GEOJSON = {
  type: 'FeatureCollection' as const,
  features: [
    {
      type: 'Feature' as const,
      id: 'zebra-vn-w',
      properties: { id: 'zebra-vn-w', name: 'Viman Nagar West Pedestrian Crossing' },
      geometry: {
        type: 'LineString' as const,
        coordinates: [
          [73.91812, 18.56068],
          [73.91812, 18.56112]
        ]
      }
    },
    {
      type: 'Feature' as const,
      id: 'zebra-vn-e',
      properties: { id: 'zebra-vn-e', name: 'Viman Nagar East Pedestrian Crossing' },
      geometry: {
        type: 'LineString' as const,
        coordinates: [
          [73.91838, 18.56068],
          [73.91838, 18.56112]
        ]
      }
    },
    {
      type: 'Feature' as const,
      id: 'zebra-vn-s',
      properties: { id: 'zebra-vn-s', name: 'Viman Nagar South Pedestrian Crossing' },
      geometry: {
        type: 'LineString' as const,
        coordinates: [
          [73.91816, 18.56066],
          [73.91834, 18.56066]
        ]
      }
    },
    {
      type: 'Feature' as const,
      id: 'zebra-sn-w',
      properties: { id: 'zebra-sn-w', name: 'Somnath Nagar West Pedestrian Crossing' },
      geometry: {
        type: 'LineString' as const,
        coordinates: [
          [73.92774, 18.56258],
          [73.92774, 18.56302]
        ]
      }
    },
    {
      type: 'Feature' as const,
      id: 'zebra-sn-e',
      properties: { id: 'zebra-sn-e', name: 'Somnath Nagar East Pedestrian Crossing' },
      geometry: {
        type: 'LineString' as const,
        coordinates: [
          [73.92806, 18.56258],
          [73.92806, 18.56302]
        ]
      }
    },
    {
      type: 'Feature' as const,
      id: 'zebra-sn-s',
      properties: { id: 'zebra-sn-s', name: 'Somnath Nagar South Pedestrian Crossing' },
      geometry: {
        type: 'LineString' as const,
        coordinates: [
          [73.92778, 18.56258],
          [73.92802, 18.56258]
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
  const [basemapMode, setBasemapMode] = useState<'satellite' | 'streets' | 'dark'>('satellite');
  const [mapLoaded, setMapLoaded] = useState<boolean>(false);
  const [corridorGeoJson, setCorridorGeoJson] = useState<Corridor3DFeatureCollection | null>(null);
  const [internalTableView, setInternalTableView] = useState<boolean>(false);
  const [hoveredBuilding, setHoveredBuilding] = useState<{
    name: string;
    category: string;
    height: number;
    levels: number;
    demandKw?: number;
    areaSqm?: number;
  } | null>(null);
  const [hoverPos, setHoverPos] = useState<{ x: number; y: number } | null>(null);

  const isTableView = isTableViewProp !== undefined ? isTableViewProp : internalTableView;
  const handleToggleTableView = (val: boolean) => {
    setInternalTableView(val);
    if (onToggleTableView) onToggleTableView(val);
  };

  // Fetch Spatial Corridor 3D GeoJSON for secondary streets and urban vegetation
  useEffect(() => {
    fetchCorridor3DGeoJson()
      .then(data => setCorridorGeoJson(data))
      .catch(err => console.warn('Could not load corridor 3D GeoJSON for 2D map:', err));
  }, []);

  // Initialize MapLibre GL Map with Premium Esri Satellite, Google-style Streets, and Dark Canvas (0 Watermarks)
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    const newMap = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'esri-satellite': {
            type: 'raster',
            tiles: [
              'https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
            ],
            tileSize: 256,
            maxzoom: 19,
            attribution: '&copy; Esri, Maxar, Earthstar Geographics'
          },
          'esri-streets': {
            type: 'raster',
            tiles: [
              'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
              'https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
              'https://c.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png'
            ],
            tileSize: 256,
            maxzoom: 20,
            attribution: '&copy; OpenStreetMap contributors, &copy; CARTO'
          },
          'esri-dark-base': {
            type: 'raster',
            tiles: [
              'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
              'https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
              'https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png'
            ],
            tileSize: 256,
            maxzoom: 20,
            attribution: '&copy; OpenStreetMap contributors, &copy; CARTO'
          },
          'esri-dark-ref': {
            type: 'raster',
            tiles: [
              'https://a.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}@2x.png'
            ],
            tileSize: 256,
            maxzoom: 20
          }
        },
        layers: [
          {
            id: 'esri-satellite-layer',
            type: 'raster',
            source: 'esri-satellite',
            minzoom: 0,
            maxzoom: 22,
            layout: {
              visibility: 'visible'
            }
          },
          {
            id: 'esri-streets-layer',
            type: 'raster',
            source: 'esri-streets',
            minzoom: 0,
            maxzoom: 22,
            layout: {
              visibility: 'none'
            }
          },
          {
            id: 'esri-dark-base-layer',
            type: 'raster',
            source: 'esri-dark-base',
            minzoom: 0,
            maxzoom: 22,
            layout: {
              visibility: 'none'
            }
          },
          {
            id: 'esri-dark-ref-layer',
            type: 'raster',
            source: 'esri-dark-ref',
            minzoom: 0,
            maxzoom: 22,
            layout: {
              visibility: 'none'
            }
          }
        ]
      },
      center: [73.9220, 18.5615], // Corridor midpoint
      zoom: 14.8,
      maxZoom: 20,
      pitch: 0,
      attributionControl: false
    });

    newMap.on('load', () => {
      setMapLoaded(true);
    });

    newMap.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'bottom-right');
    newMap.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');

    map.current = newMap;

    return () => {
      markersRef.current.forEach(m => m.remove());
      markersRef.current = [];
      newMap.remove();
      map.current = null;
      setMapLoaded(false);
    };
  }, []);

  // Dynamically update basemap layer visibility when switching between Satellite, Streets, and Dark Canvas
  useEffect(() => {
    const currentMap = map.current;
    if (!currentMap || !mapLoaded) return;

    if (currentMap.getLayer('esri-satellite-layer')) {
      currentMap.setLayoutProperty(
        'esri-satellite-layer',
        'visibility',
        basemapMode === 'satellite' ? 'visible' : 'none'
      );
    }
    if (currentMap.getLayer('esri-streets-layer')) {
      currentMap.setLayoutProperty(
        'esri-streets-layer',
        'visibility',
        basemapMode === 'streets' ? 'visible' : 'none'
      );
    }
    if (currentMap.getLayer('esri-dark-base-layer')) {
      currentMap.setLayoutProperty(
        'esri-dark-base-layer',
        'visibility',
        basemapMode === 'dark' ? 'visible' : 'none'
      );
    }
    if (currentMap.getLayer('esri-dark-ref-layer')) {
      currentMap.setLayoutProperty(
        'esri-dark-ref-layer',
        'visibility',
        basemapMode === 'dark' ? 'visible' : 'none'
      );
    }
  }, [basemapMode, mapLoaded]);

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

      // 1.5 Add Secondary Streets (Contextual urban street grid)
      if (corridorGeoJson) {
        const secFeatures = corridorGeoJson.features.filter(f => f.properties?.layer === 'secondary_streets');
        if (secFeatures.length > 0) {
          if (!currentMap.getSource('secondary-streets')) {
            currentMap.addSource('secondary-streets', {
              type: 'geojson',
              data: {
                type: 'FeatureCollection',
                features: secFeatures
              } as any
            });

            currentMap.addLayer({
              id: 'secondary-streets-layer',
              type: 'line',
              source: 'secondary-streets',
              layout: {
                'line-cap': 'round',
                'line-join': 'round'
              },
              paint: {
                'line-color': '#475569',
                'line-width': [
                  'interpolate', ['linear'], ['zoom'],
                  12, 1.5,
                  14, 2.5,
                  16, 4.0
                ],
                'line-opacity': 0.65
              }
            });
          } else {
            (currentMap.getSource('secondary-streets') as maplibregl.GeoJSONSource).setData({
              type: 'FeatureCollection',
              features: secFeatures
            } as any);
          }
        }

        // 1.6 Add Urban Median Trees (Green canopy markers along Nagar Road)
        const treeFeatures = corridorGeoJson.features.filter(f => f.properties?.layer === 'trees');
        if (treeFeatures.length > 0) {
          if (!currentMap.getSource('urban-trees')) {
            currentMap.addSource('urban-trees', {
              type: 'geojson',
              data: {
                type: 'FeatureCollection',
                features: treeFeatures
              } as any
            });

            currentMap.addLayer({
              id: 'urban-trees-layer',
              type: 'circle',
              source: 'urban-trees',
              paint: {
                'circle-color': '#2D6A4F',
                'circle-radius': [
                  'interpolate', ['linear'], ['zoom'],
                  12, 2.5,
                  14, 4,
                  16, 6
                ],
                'circle-stroke-color': '#52B788',
                'circle-stroke-width': 1.5,
                'circle-opacity': 0.9
              }
            });
          } else {
            (currentMap.getSource('urban-trees') as maplibregl.GeoJSONSource).setData({
              type: 'FeatureCollection',
              features: treeFeatures
            } as any);
          }
        }
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

        // Layer 1: Dark asphalt roadway base (Calibrated to 10.5m physical scale, zero median bleed)
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
              12, 3.5,
              14, 6.5,
              16, 10.5,
              18, 15.5
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
              12, ['case', ['get', 'isSelected'], 5.5, ['get', 'isCompare'], 5.0, 0],
              14, ['case', ['get', 'isSelected'], 9.5, ['get', 'isCompare'], 9.0, 0],
              16, ['case', ['get', 'isSelected'], 14.5, ['get', 'isCompare'], 14.0, 0],
              18, ['case', ['get', 'isSelected'], 20.0, ['get', 'isCompare'], 19.0, 0]
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
              12, 2.5,
              14, 4.8,
              16, 8.0,
              18, 12.0
            ],
            'line-opacity': 1.0
          }
        });

        // Layer 4A: Left Dashed Lane Divider (Separating Lane 0 Curbside from Lane 1 Through)
        currentMap.addLayer({
          id: 'road-segments-divider-left',
          type: 'line',
          source: 'road-segments',
          layout: {
            'line-cap': 'butt',
            'line-join': 'round'
          },
          paint: {
            'line-color': 'rgba(255, 255, 255, 0.45)',
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              12, 0.5,
              14, 0.8,
              16, 1.2,
              18, 1.6
            ],
            'line-offset': [
              'interpolate', ['linear'], ['zoom'],
              12, -0.8,
              14, -1.5,
              16, -2.4,
              18, -3.6
            ],
            'line-dasharray': [4, 4]
          }
        });

        // Layer 4B: Right Dashed Lane Divider (Separating Lane 1 Through from Lane 2 Median)
        currentMap.addLayer({
          id: 'road-segments-divider-right',
          type: 'line',
          source: 'road-segments',
          layout: {
            'line-cap': 'butt',
            'line-join': 'round'
          },
          paint: {
            'line-color': 'rgba(255, 255, 255, 0.45)',
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              12, 0.5,
              14, 0.8,
              16, 1.2,
              18, 1.6
            ],
            'line-offset': [
              'interpolate', ['linear'], ['zoom'],
              12, 0.8,
              14, 1.5,
              16, 2.4,
              18, 3.6
            ],
            'line-dasharray': [4, 4]
          }
        });

        // Layer 5: Directional chevron flow indicators centered cleanly within the through-lane
        currentMap.addLayer({
          id: 'road-segments-flow-arrows',
          type: 'symbol',
          source: 'road-segments',
          layout: {
            'symbol-placement': 'line',
            'symbol-spacing': 110,
            'icon-image': 'flow-arrow',
            'icon-size': [
              'interpolate', ['linear'], ['zoom'],
              12, 0.35,
              14, 0.5,
              16, 0.7,
              18, 0.85
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

      // 3B. Add Yellow Box Junctions and Zebra Crossings (IRC:35 Navigation Grade)
      if (!currentMap.getSource('junction-boxes')) {
        currentMap.addSource('junction-boxes', {
          type: 'geojson',
          data: JUNCTION_BOXES_GEOJSON as any
        });

        currentMap.addLayer({
          id: 'junction-boxes-fill',
          type: 'fill',
          source: 'junction-boxes',
          paint: {
            'fill-color': '#F59E0B',
            'fill-opacity': 0.12
          }
        });

        currentMap.addLayer({
          id: 'junction-boxes-outline',
          type: 'line',
          source: 'junction-boxes',
          paint: {
            'line-color': '#F59E0B',
            'line-width': 2.0,
            'line-opacity': 0.85
          }
        });
      }

      if (!currentMap.getSource('zebra-crossings')) {
        currentMap.addSource('zebra-crossings', {
          type: 'geojson',
          data: ZEBRA_CROSSINGS_GEOJSON as any
        });

        currentMap.addLayer({
          id: 'zebra-crossings-stripes',
          type: 'line',
          source: 'zebra-crossings',
          paint: {
            'line-color': '#FFFFFF',
            'line-width': [
              'interpolate', ['linear'], ['zoom'],
              13, 3.5,
              15, 5.5,
              17, 8.5
            ],
            'line-dasharray': [0.8, 0.8],
            'line-opacity': 0.95
          }
        });
      }

      // 4. Add 2D & 3D Building Layers (Category Color-Coded with Interactive Hover Tooltips)
      const bldFeatures = corridorGeoJson?.features.filter(f => f.properties?.layer === 'buildings') || [];
      const categoryColorMap: Record<string, { fill: string; border: string }> = {
        COMMERCIAL_RETAIL: { fill: '#0284C7', border: '#38BDF8' },
        COMMERCIAL_IT: { fill: '#2563EB', border: '#60A5FA' },
        COMMERCIAL_OFFICE: { fill: '#2563EB', border: '#60A5FA' },
        CORPORATE_HQ: { fill: '#2563EB', border: '#60A5FA' },
        HOSPITALITY_HOTEL: { fill: '#D97706', border: '#FBBF24' },
        RESIDENTIAL_COMPLEX: { fill: '#059669', border: '#34D399' },
        CIVIC_EDUCATION: { fill: '#7C3AED', border: '#A78BFA' },
        HEALTHCARE: { fill: '#DC2626', border: '#F87171' },
        MIXED_USE: { fill: '#0D9488', border: '#2DD4BF' },
        TRANSIT_INFRASTRUCTURE: { fill: '#0891B2', border: '#22D3EE' },
      };

      const buildingsGeoJson = {
        type: 'FeatureCollection',
        features: bldFeatures.map(f => {
          const cat = f.properties?.category || 'COMMERCIAL_RETAIL';
          const colors = categoryColorMap[cat] || { fill: '#0284C7', border: '#38BDF8' };
          return {
            ...f,
            properties: {
              ...f.properties,
              color: colors.fill,
              borderColor: colors.border,
              height: f.properties?.heightMeters || 24,
              base_height: 0
            }
          };
        })
      };

      if (!currentMap.getSource('corridor-buildings-source')) {
        currentMap.addSource('corridor-buildings-source', {
          type: 'geojson',
          data: buildingsGeoJson as any
        });

        // 2D Building Footprint Fill
        currentMap.addLayer({
          id: 'corridor-buildings-2d-fill',
          type: 'fill',
          source: 'corridor-buildings-source',
          layout: {
            visibility: is3DMode ? 'none' : 'visible'
          },
          paint: {
            'fill-color': ['get', 'color'],
            'fill-opacity': 0.58
          }
        });

        // 2D Building Perimeter Outline
        currentMap.addLayer({
          id: 'corridor-buildings-2d-line',
          type: 'line',
          source: 'corridor-buildings-source',
          layout: {
            visibility: is3DMode ? 'none' : 'visible'
          },
          paint: {
            'line-color': ['get', 'borderColor'],
            'line-width': 1.5,
            'line-opacity': 0.9
          }
        });

        // 3D Building Extrusion (active in 3D pitch/isometric view)
        currentMap.addLayer({
          id: 'corridor-buildings-extrusion',
          type: 'fill-extrusion',
          source: 'corridor-buildings-source',
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

        // Interactive Cursor Hover Tooltip for Buildings
        currentMap.on('mousemove', 'corridor-buildings-2d-fill', (e) => {
          if (!e.features || !e.features[0]) return;
          const p = e.features[0].properties || {};
          setHoveredBuilding({
            name: p.name || 'Corridor Building',
            category: p.category || 'COMMERCIAL',
            height: p.heightMeters || p.height || 24,
            levels: p.buildingLevels || 6,
            demandKw: p.contractDemandKw,
            areaSqm: p.grossFloorAreaSqm
          });
          setHoverPos({ x: e.point.x, y: e.point.y });
          currentMap.getCanvas().style.cursor = 'pointer';
        });

        currentMap.on('mouseleave', 'corridor-buildings-2d-fill', () => {
          setHoveredBuilding(null);
          setHoverPos(null);
          currentMap.getCanvas().style.cursor = '';
        });
      } else {
        (currentMap.getSource('corridor-buildings-source') as maplibregl.GeoJSONSource).setData(buildingsGeoJson as any);
        if (currentMap.getLayer('corridor-buildings-2d-fill')) {
          currentMap.setLayoutProperty('corridor-buildings-2d-fill', 'visibility', is3DMode ? 'none' : 'visible');
        }
        if (currentMap.getLayer('corridor-buildings-2d-line')) {
          currentMap.setLayoutProperty('corridor-buildings-2d-line', 'visibility', is3DMode ? 'none' : 'visible');
        }
        if (currentMap.getLayer('corridor-buildings-extrusion')) {
          currentMap.setLayoutProperty('corridor-buildings-extrusion', 'visibility', is3DMode ? 'visible' : 'none');
        }
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

    if (!mapLoaded) return;
    onMapLoad();
  }, [mapLoaded, studyAreaGeoJson, roadSegments, intersections, liveStates, selectedEntity, compareEntity, onSelectEntity, onSelectCompareEntity, is3DMode, currentTheme, corridorGeoJson]);

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
    <div className="map-view-wrapper" style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* 2D MapLibre Canvas */}
      <div
        ref={mapContainer}
        className="maplibre-container"
        style={{
          width: '100%',
          height: '100%',
          display: is3DMode ? 'none' : 'block'
        }}
        role="region"
        aria-label="Interactive 2D Corridor Map Canvas"
      />

      {/* 2D Building Interactive Hover Tooltip Card */}
      {hoveredBuilding && hoverPos && !is3DMode && (
        <div
          className="building-hover-card"
          style={{
            position: 'absolute',
            left: Math.min(hoverPos.x + 14, (typeof window !== 'undefined' ? window.innerWidth : 1200) - 300),
            top: Math.max(10, hoverPos.y - 12),
            pointerEvents: 'none',
            zIndex: 40,
            backgroundColor: 'rgba(15, 23, 42, 0.95)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(255, 255, 255, 0.18)',
            borderRadius: '8px',
            padding: '10px 14px',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
            maxWidth: '280px',
            color: '#FFFFFF'
          }}
        >
          <div style={{ fontWeight: 700, fontSize: '13px', marginBottom: '4px', color: '#F8FAFC' }}>
            {hoveredBuilding.name}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
            <span
              style={{
                fontSize: '10px',
                fontWeight: 700,
                textTransform: 'uppercase',
                padding: '2px 6px',
                borderRadius: '4px',
                backgroundColor: 'rgba(255, 255, 255, 0.12)',
                color: '#38BDF8'
              }}
            >
              {hoveredBuilding.category?.replace(/_/g, ' ')}
            </span>
            <span style={{ fontSize: '11px', color: '#94A3B8' }}>
              {hoveredBuilding.height}m ({hoveredBuilding.levels} floors)
            </span>
          </div>
          {hoveredBuilding.demandKw && (
            <div style={{ fontSize: '11px', color: '#F0883E', fontWeight: 600 }}>
              ⚡ Sanctioned Demand: {hoveredBuilding.demandKw.toLocaleString()} kW
            </div>
          )}
        </div>
      )}

      {/* 3D Cesium WebGL Digital Twin Viewer */}
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

          {!is3DMode && (
            <div style={{ display: 'flex', gap: '3px', background: 'rgba(15,23,42,0.85)', padding: '2px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.12)' }}>
              <button
                type="button"
                className={`map-view-toggle-btn ${basemapMode === 'satellite' ? 'active' : ''}`}
                onClick={() => setBasemapMode('satellite')}
                title="Photorealistic Satellite Imagery"
              >
                <span>🛰️ Satellite</span>
              </button>
              <button
                type="button"
                className={`map-view-toggle-btn ${basemapMode === 'streets' ? 'active' : ''}`}
                onClick={() => setBasemapMode('streets')}
                title="Google Maps-Style Clean Street Map"
              >
                <span>🗺️ Streets</span>
              </button>
              <button
                type="button"
                className={`map-view-toggle-btn ${basemapMode === 'dark' ? 'active' : ''}`}
                onClick={() => setBasemapMode('dark')}
                title="Dark Operations Canvas"
              >
                <span>🌃 Dark</span>
              </button>
            </div>
          )}

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
