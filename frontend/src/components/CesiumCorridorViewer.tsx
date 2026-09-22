import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as Cesium from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import { EntityCurrentState, RoadSegmentAsset, IntersectionAsset } from '../types/twin';
import { fetchCorridor3DGeoJson } from '../services/spatialApi';
import { Corridor3DFeatureCollection } from '../types/spatial';
import { CesiumCameraControls, CORRIDOR_VIEWPOINTS, CameraViewpoint } from './CesiumCameraControls';
import { Activity, AlertTriangle } from 'lucide-react';

interface CesiumCorridorViewerProps {
  roadSegments: RoadSegmentAsset[];
  intersections: IntersectionAsset[];
  liveStates: Record<string, EntityCurrentState>;
  selectedEntity?: RoadSegmentAsset | IntersectionAsset | null;
  currentTheme?: 'light' | 'dark';
  onSelectEntity: (entity: RoadSegmentAsset | IntersectionAsset) => void;
}

interface LiveKinematicVehicle {
  id: string;
  name: string;
  segmentId: string;
  coords: [number, number][];
  lengthMeters: number;
  laneIndex: number;
  progress: number; // 0.0 to 1.0 along segment
  speedKmh: number;
  dimensions: Cesium.Cartesian3;
  color: Cesium.Color;
  currentPosition: Cesium.Cartesian3;
  currentOrientation: Cesium.Quaternion;
}

function computePolylineLengthMeters(coords: [number, number][]): number {
  let total = 0;
  for (let i = 0; i < coords.length - 1; i++) {
    const dx = (coords[i + 1][0] - coords[i][0]) * 105360.0;
    const dy = (coords[i + 1][1] - coords[i][1]) * 111139.0;
    total += Math.hypot(dx, dy);
  }
  return Math.max(50.0, total);
}

// Calculates WGS84 Position and Cesium Orientation for a vehicle at fractional progress [0, 1)
function computeKinematicPose(
  coords: [number, number][],
  progress: number,
  laneIndex: number
): { position: Cesium.Cartesian3; orientation: Cesium.Quaternion } {
  const normProgress = ((progress % 1.0) + 1.0) % 1.0;
  const index = Math.min(coords.length - 2, Math.floor(normProgress * (coords.length - 1)));
  const p1 = coords[index];
  const p2 = coords[index + 1];

  const subT = (normProgress * (coords.length - 1)) - index;
  const baseLng = p1[0] + (p2[0] - p1[0]) * subT;
  const baseLat = p1[1] + (p2[1] - p1[1]) * subT;

  const dx = p2[0] - p1[0];
  const dy = p2[1] - p1[1];
  const segLen = Math.hypot(dx, dy) || 1e-6;
  const tx = dx / segLen;
  const ty = dy / segLen;

  // Perpendicular normal vector pointing right of travel direction
  const nx = ty;
  const ny = -tx;

  // True Heading in Cesium (measured clockwise from North)
  const heading = Math.atan2(dx, dy);

  // Multi-lane lateral distribution (Lane 0: -3.2m Curbside, Lane 1: 0m Through, Lane 2: +3.2m Median)
  const laneOffsetMeters = (laneIndex - 1) * 3.2;

  // Scale meters to degrees at 18.56° latitude (1 deg lat ≈ 111139m, 1 deg lng ≈ 105360m)
  const lng = baseLng + (nx * laneOffsetMeters) / 105360.0;
  const lat = baseLat + (ny * laneOffsetMeters) / 111139.0;

  const position = Cesium.Cartesian3.fromDegrees(lng, lat, 1.2);
  const orientation = Cesium.Transforms.headingPitchRollQuaternion(
    position,
    new Cesium.HeadingPitchRoll(heading, 0, 0)
  );

  return { position, orientation };
}

export const CesiumCorridorViewer: React.FC<CesiumCorridorViewerProps> = ({
  roadSegments,
  intersections,
  liveStates,
  selectedEntity,
  currentTheme = 'dark',
  onSelectEntity
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Cesium.Viewer | null>(null);
  const vehiclesCollectionRef = useRef<Cesium.CustomDataSource | null>(null);
  const signalsCollectionRef = useRef<Cesium.CustomDataSource | null>(null);
  const activeVehiclesRef = useRef<LiveKinematicVehicle[]>([]);
  const lastTimeRef = useRef<number>(performance.now());
  const [activeViewpointId, setActiveViewpointId] = useState<string>('corridor-overview');
  const [basemap3D, setBasemap3D] = useState<'satellite' | 'streets' | 'dark'>('satellite');
  const [solarTime, setSolarTime] = useState<'midday' | 'golden' | 'night'>('golden');
  const [hoveredBuilding3D, setHoveredBuilding3D] = useState<{
    name: string;
    category: string;
    height: number;
    levels: number;
    demandKw?: number;
  } | null>(null);
  const [hoverPos3D, setHoverPos3D] = useState<{ x: number; y: number } | null>(null);
  const [corridorGeoJson, setCorridorGeoJson] = useState<Corridor3DFeatureCollection | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorNotice, setErrorNotice] = useState<string | null>(null);

  // 1. Fetch Authoritative Corridor 3D GeoJSON
  useEffect(() => {
    let isMounted = true;
    fetchCorridor3DGeoJson()
      .then((data) => {
        if (isMounted) {
          setCorridorGeoJson(data);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error('[Cesium] Failed to fetch 3D GeoJSON:', err);
          setErrorNotice('Unable to load corridor 3D assets. Using local fallback geometry.');
          setIsLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Initialize Cesium Viewer
  useEffect(() => {
    if (!containerRef.current || viewerRef.current) return;

    try {
      const viewer = new Cesium.Viewer(containerRef.current, {
        animation: false,
        baseLayerPicker: false,
        fullscreenButton: false,
        geocoder: false,
        homeButton: false,
        infoBox: false,
        sceneModePicker: false,
        selectionIndicator: false,
        timeline: false,
        navigationHelpButton: false,
        navigationInstructionsInitiallyVisible: false,
        scene3DOnly: true,
        shadows: true, // Enable real-time astronomical building shadows
        baseLayer: new Cesium.ImageryLayer(
          new Cesium.UrlTemplateImageryProvider({
            url: 'https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            maximumLevel: 18 // CLAMP to 18 to eliminate "map data not yet available"!
          })
        )
      });

      // Configure Scene Aesthetics, Atmosphere & Shadow Mapping
      const scene = viewer.scene;
      scene.globe.depthTestAgainstTerrain = false;
      scene.globe.enableLighting = true; // Solar angle lighting based on clock time
      scene.highDynamicRange = true; // HDR tone-mapping for realistic light bounces

      if (scene.fog) {
        scene.fog.enabled = true;
        scene.fog.density = 0.00015;
      }
      if (viewer.shadowMap) {
        viewer.shadowMap.size = 2048;
        viewer.shadowMap.softShadows = true;
        viewer.shadowMap.darkness = 0.55; // Realistic ambient shadow level
      }

      // Initial Golden Hour Sun Position (4:00 PM IST / 10:30 UTC over Pune)
      viewer.clock.currentTime = Cesium.JulianDate.fromIso8601('2026-09-22T10:30:00Z');
      viewer.clock.shouldAnimate = false;

      scene.backgroundColor = Cesium.Color.fromCssColorString(
        currentTheme === 'light' ? '#E2E8F0' : '#0B1320'
      );

      // Add dynamic collections for vehicles & signals
      const vehicleDataSource = new Cesium.CustomDataSource('corridor-vehicles');
      const signalDataSource = new Cesium.CustomDataSource('corridor-signals');
      viewer.dataSources.add(vehicleDataSource);
      viewer.dataSources.add(signalDataSource);
      vehiclesCollectionRef.current = vehicleDataSource;
      signalsCollectionRef.current = signalDataSource;

      // Screen-Space Handlers: Click Picking and Dynamic Mouse Hover
      const handler = new Cesium.ScreenSpaceEventHandler(scene.canvas);

      // Left Click: Select Entity
      handler.setInputAction((movement: any) => {
        const pickedObject = scene.pick(movement.position);
        if (Cesium.defined(pickedObject) && pickedObject.id) {
          const entity = pickedObject.id;
          const entityId = entity.id || (entity.properties && entity.properties.entityId?.getValue?.());
          if (entityId) {
            const foundRoad = roadSegments.find((r) => r.id === entityId);
            if (foundRoad) {
              onSelectEntity(foundRoad);
              return;
            }
            const foundIx = intersections.find((ix) => ix.id === entityId);
            if (foundIx) {
              onSelectEntity(foundIx);
              return;
            }
          }
        }
      }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

      // Mouse Move: Dynamic Building Hover Tooltip
      handler.setInputAction((movement: any) => {
        const pickedObject = scene.pick(movement.endPosition);
        if (Cesium.defined(pickedObject) && pickedObject.id) {
          const entity = pickedObject.id;
          const eType = entity.properties?.entityType?.getValue?.() || entity.properties?.entityType;
          if (eType === 'BuildingZone') {
            setHoveredBuilding3D({
              name: entity.name || 'Corridor Building',
              category: entity.properties?.category?.getValue?.() || entity.properties?.category || 'COMMERCIAL',
              height: entity.properties?.heightMeters?.getValue?.() || entity.properties?.heightMeters || 24,
              levels: entity.properties?.levels?.getValue?.() || entity.properties?.levels || 6,
              demandKw: entity.properties?.contractDemandKw?.getValue?.() || entity.properties?.contractDemandKw
            });
            setHoverPos3D({ x: movement.endPosition.x, y: movement.endPosition.y });
            return;
          }
        }
        setHoveredBuilding3D(null);
        setHoverPos3D(null);
      }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);

      viewerRef.current = viewer;

      // Initial Camera Fly-To: Full Corridor Overview
      const defaultVp = CORRIDOR_VIEWPOINTS[0];
      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(
          defaultVp.longitude,
          defaultVp.latitude,
          defaultVp.height
        ),
        orientation: {
          heading: Cesium.Math.toRadians(defaultVp.headingDegrees),
          pitch: Cesium.Math.toRadians(defaultVp.pitchDegrees),
          roll: Cesium.Math.toRadians(defaultVp.rollDegrees)
        },
        duration: 1.5
      });

      return () => {
        handler.destroy();
        if (!viewer.isDestroyed()) {
          viewer.destroy();
        }
        viewerRef.current = null;
      };
    } catch (e) {
      console.error('[Cesium] Viewer initialization error:', e);
      setErrorNotice('WebGL 3D engine failed to initialize.');
    }
  }, [currentTheme]);

  // 2.5 Dynamic 3D Basemap Swapping (Satellite, Google-Style Streets, Dark Canvas)
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || viewer.isDestroyed()) return;
    const layers = viewer.imageryLayers;
    layers.removeAll();

    let provider: Cesium.ImageryProvider;
    if (basemap3D === 'streets') {
      provider = new Cesium.UrlTemplateImageryProvider({
        url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
        subdomains: ['a', 'b', 'c', 'd'],
        maximumLevel: 20,
        credit: '© OpenStreetMap contributors, © CARTO'
      });
    } else if (basemap3D === 'dark') {
      provider = new Cesium.UrlTemplateImageryProvider({
        url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png',
        subdomains: ['a', 'b', 'c', 'd'],
        maximumLevel: 20,
        credit: '© OpenStreetMap contributors, © CARTO'
      });
    } else {
      provider = new Cesium.UrlTemplateImageryProvider({
        url: 'https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        maximumLevel: 19,
        credit: '© Esri, Maxar, Earthstar Geographics'
      });
    }
    const layer = layers.addImageryProvider(provider);
    layer.minificationFilter = Cesium.TextureMinificationFilter.LINEAR_MIPMAP_LINEAR;
    layer.magnificationFilter = Cesium.TextureMagnificationFilter.LINEAR;
  }, [basemap3D]);

  // 3. Render Static 3D Spatial Geometry (Buildings, Roads, Sensors, Trees, Secondary Streets)
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || !corridorGeoJson) return;

    // Clear static entities (keep dynamic vehicles & signals in dataSources)
    viewer.entities.removeAll();

    corridorGeoJson.features.forEach((feature) => {
      const props = feature.properties || {};
      const layer = props.layer;

      // A. Building Extrusion (Surveyed Buildings with Functional Category Color Tints)
      if (layer === 'buildings' && feature.geometry.type === 'Polygon') {
        if (feature.id?.includes('BLD-METRO-') || props.category === 'TRANSIT_INFRASTRUCTURE') {
          return;
        }
        const coords = feature.geometry.coordinates[0];
        const flatHierarchy = coords.map((c: number[]) =>
          Cesium.Cartesian3.fromDegrees(c[0], c[1], 0)
        );

        const height = props.heightMeters || 24.0;
        const category = props.category || 'COMMERCIAL_RETAIL';
        const categoryColors: Record<string, { fill: string; outline: string }> = {
          COMMERCIAL_RETAIL: { fill: '#0284C7', outline: '#38BDF8' },
          COMMERCIAL_IT: { fill: '#2563EB', outline: '#60A5FA' },
          COMMERCIAL_OFFICE: { fill: '#2563EB', outline: '#60A5FA' },
          CORPORATE_HQ: { fill: '#2563EB', outline: '#60A5FA' },
          HOSPITALITY_HOTEL: { fill: '#D97706', outline: '#FBBF24' },
          RESIDENTIAL_COMPLEX: { fill: '#059669', outline: '#34D399' },
          CIVIC_EDUCATION: { fill: '#7C3AED', outline: '#A78BFA' },
          HEALTHCARE: { fill: '#DC2626', outline: '#F87171' },
          MIXED_USE: { fill: '#0D9488', outline: '#2DD4BF' },
          TRANSIT_INFRASTRUCTURE: { fill: '#0891B2', outline: '#22D3EE' },
        };
        const colors = categoryColors[category] || { fill: '#0284C7', outline: '#38BDF8' };
        const buildingColor = Cesium.Color.fromCssColorString(colors.fill).withAlpha(0.85);
        const outlineColor = Cesium.Color.fromCssColorString(colors.outline).withAlpha(0.95);

        viewer.entities.add({
          id: feature.id,
          name: props.name || 'Building Zone',
          polygon: {
            hierarchy: new Cesium.PolygonHierarchy(flatHierarchy),
            extrudedHeight: height,
            height: 0,
            material: buildingColor,
            outline: true,
            outlineColor: outlineColor,
            outlineWidth: 2
          },
          properties: {
            entityId: feature.id,
            entityType: 'BuildingZone',
            category: category,
            heightMeters: height,
            levels: props.buildingLevels || 6,
            contractDemandKw: props.contractDemandKw
          }
        });
      }

      // B. Realistic 3D Sidewalk Trees (Wood Trunk Cylinder + Organic Foliage Ellipsoid along sidewalks)
      if (layer === 'trees' && feature.geometry.type === 'Point') {
        const [lng, lat] = feature.geometry.coordinates;
        const treeH = props.heightMeters || 7.5;
        const trunkH = props.trunkHeightMeters || 2.6;
        const canopyH = Math.max(2.4, treeH - trunkH);
        const canopyR = (props.canopyDiameterMeters || 5.5) / 2;
        const isFlowering = Boolean(props.isFlowering);

        // 1. Natural Wood Trunk (Slender cylinder planted on sidewalk)
        viewer.entities.add({
          name: `${props.species || 'Street Tree'} Trunk`,
          position: Cesium.Cartesian3.fromDegrees(lng, lat, trunkH / 2),
          cylinder: {
            length: trunkH,
            topRadius: 0.22,
            bottomRadius: 0.28,
            material: Cesium.Color.fromCssColorString('#4A2E18'),
            outline: false
          }
        });

        // 2. Leafy / Flowering Organic Canopy (Ellipsoid sitting atop trunk)
        viewer.entities.add({
          id: feature.id,
          name: props.species || 'Sidewalk Tree Canopy',
          position: Cesium.Cartesian3.fromDegrees(lng, lat, trunkH + canopyH * 0.65),
          ellipsoid: {
            radii: new Cesium.Cartesian3(canopyR, canopyR, canopyH * 0.75),
            material: isFlowering
              ? Cesium.Color.fromCssColorString('#D9531E').withAlpha(0.92) // Gulmohar fiery bloom
              : Cesium.Color.fromCssColorString('#2E7D32').withAlpha(0.92), // Lush Neem foliage
            outline: true,
            outlineColor: Cesium.Color.fromCssColorString(isFlowering ? '#EA580C' : '#15803D').withAlpha(0.6)
          },
          properties: {
            entityId: feature.id,
            entityType: 'UrbanTreeCanopy',
            species: props.species
          }
        });
      }

      // C. Secondary Connector Streets
      if (layer === 'secondary_streets' && feature.geometry.type === 'LineString') {
        const coords = feature.geometry.coordinates;
        const positions = coords.map((c: number[]) =>
          Cesium.Cartesian3.fromDegrees(c[0], c[1], 0.5)
        );

        viewer.entities.add({
          id: feature.id,
          name: props.name || 'Connector Street',
          polyline: {
            positions: positions,
            width: 3.5,
            material: Cesium.Color.fromCssColorString('#475569').withAlpha(0.65),
            clampToGround: true
          },
          properties: {
            entityId: feature.id,
            entityType: 'SecondaryStreet',
            highwayType: props.highwayType
          }
        });
      }

      // D. Road Segment Centerlines & Curved 3D Ribbons
      if (layer === 'roads' && feature.geometry.type === 'LineString') {
        const coords = feature.geometry.coordinates;
        const positions = coords.map((c: number[]) =>
          Cesium.Cartesian3.fromDegrees(c[0], c[1], 1.5)
        );

        const isEB = (props.direction || '').toUpperCase() === 'EASTBOUND';
        const roadColor = Cesium.Color.fromCssColorString(
          isEB ? '#2F81F7' : '#D29922'
        ).withAlpha(0.85);

        // Road Surface Ribbon
        viewer.entities.add({
          id: feature.id,
          name: props.name || 'Road Segment',
          polyline: {
            positions: positions,
            width: (props.laneCount || 3) * 3.8,
            material: new Cesium.PolylineGlowMaterialProperty({
              glowPower: 0.15,
              color: roadColor
            }),
            clampToGround: true
          },
          properties: {
            entityId: feature.id,
            entityType: 'RoadSegment',
            direction: props.direction,
            laneCount: props.laneCount
          }
        });
      }

      // C. Intersections (Stoplines & Landmark Hubs)
      if (layer === 'intersections' && feature.geometry.type === 'Point') {
        const [lng, lat] = feature.geometry.coordinates;
        viewer.entities.add({
          id: feature.id,
          name: props.name || 'Intersection',
          position: Cesium.Cartesian3.fromDegrees(lng, lat, 2.0),
          point: {
            pixelSize: 14,
            color: Cesium.Color.fromCssColorString('#2F81F7'),
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2,
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          },
          label: {
            text: props.name || 'Intersection',
            font: "600 12px 'General Sans', -apple-system, sans-serif",
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            pixelOffset: new Cesium.Cartesian2(0, -16),
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          },
          properties: {
            entityId: feature.id,
            entityType: 'Intersection'
          }
        });
      }

      // D. Traffic & Environmental Sensors
      if (layer === 'sensors' && feature.geometry.type === 'Point') {
        const [lng, lat] = feature.geometry.coordinates;
        const elev = props.elevationMeters || 2.5;

        viewer.entities.add({
          id: feature.id,
          name: props.name || 'Sensor',
          position: Cesium.Cartesian3.fromDegrees(lng, lat, elev),
          cylinder: {
            length: elev,
            topRadius: 0.4,
            bottomRadius: 0.4,
            material: Cesium.Color.fromCssColorString('#38BDF8').withAlpha(0.7)
          },
          point: {
            pixelSize: 8,
            color: Cesium.Color.fromCssColorString('#38BDF8'),
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 1.5,
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          },
          properties: {
            entityId: feature.id,
            entityType: 'Sensor'
          }
        });
      }
    });

    // E. Pune Metro Aqua Line Elevated Viaduct & Support Piers (Strict Central Road Median Alignment)
    const METRO_VIADUCT_POINTS = [
      [73.911606, 18.558657],
      [73.912220, 18.558862],
      [73.912873, 18.559075],
      [73.913518, 18.559292],
      [73.914161, 18.559526],
      [73.914803, 18.559768],
      [73.915444, 18.560011],
      [73.916100, 18.560235],
      [73.916752, 18.560439],
      [73.917407, 18.560643],
      [73.918062, 18.560844], // Viman Nagar Chowk Median
      [73.918727, 18.561026],
      [73.919386, 18.561215], // Viman Nagar Metro Station (Median)
      [73.920044, 18.561399],
      [73.920701, 18.561594],
      [73.921362, 18.561782],
      [73.922028, 18.561950],
      [73.922693, 18.562111],
      [73.923357, 18.562285],
      [73.924021, 18.562456],
      [73.924697, 18.562598],
      [73.925387, 18.562678],
      [73.926074, 18.562732],
      [73.926761, 18.562777],
      [73.927445, 18.562812],
      [73.928125, 18.562851], // Somnath Nagar Chowk Median
      [73.928808, 18.562911],
      [73.929491, 18.562971],
      [73.930174, 18.563031],
      [73.930858, 18.563091],
      [73.931538, 18.563164],
      [73.932220, 18.563230]
    ];

    const viaductPositions = METRO_VIADUCT_POINTS.map(p =>
      Cesium.Cartesian3.fromDegrees(p[0], p[1], 9.5)
    );

    // Elevated concrete box girder along median
    viewer.entities.add({
      name: 'Pune Metro Aqua Line Viaduct',
      polyline: {
        positions: viaductPositions,
        width: 6.5,
        material: Cesium.Color.fromCssColorString('#94A3B8').withAlpha(0.95),
        clampToGround: false
      }
    });

    // Slender cylindrical support piers along central median (r=0.55m strictly inside 2.5m median)
    METRO_VIADUCT_POINTS.forEach((pt, idx) => {
      viewer.entities.add({
        name: `Metro Pier P-${idx + 1}`,
        position: Cesium.Cartesian3.fromDegrees(pt[0], pt[1], 4.75),
        cylinder: {
          length: 9.5,
          topRadius: 0.55,
          bottomRadius: 0.55,
          material: Cesium.Color.fromCssColorString('#64748B'),
          outline: false
        }
      });
    });

    // Elevated Circular Metro Station Badge (Zero Road Encroachment)
    const STATION_MEDIAN_COORD = [73.919386, 18.561215];
    viewer.entities.add({
      name: 'Pune Metro • Viman Nagar Station Indicator',
      position: Cesium.Cartesian3.fromDegrees(STATION_MEDIAN_COORD[0], STATION_MEDIAN_COORD[1], 12.25),
      cylinder: {
        length: 5.5,
        topRadius: 0.15,
        bottomRadius: 0.15,
        material: Cesium.Color.fromCssColorString('#0284C7').withAlpha(0.7)
      }
    });

    viewer.entities.add({
      name: 'Pune Metro • Viman Nagar Station',
      position: Cesium.Cartesian3.fromDegrees(STATION_MEDIAN_COORD[0], STATION_MEDIAN_COORD[1], 15.0),
      point: {
        pixelSize: 26,
        color: Cesium.Color.fromCssColorString('#0284C7'),
        outlineColor: Cesium.Color.WHITE,
        outlineWidth: 3,
        disableDepthTestDistance: Number.POSITIVE_INFINITY
      },
      label: {
        text: '🚇 Viman Nagar Metro Station',
        font: "bold 12px 'General Sans', -apple-system, sans-serif",
        fillColor: Cesium.Color.WHITE,
        outlineColor: Cesium.Color.fromCssColorString('#0F172A'),
        outlineWidth: 3,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cesium.Cartesian2(0, -24),
        disableDepthTestDistance: Number.POSITIVE_INFINITY
      }
    });

    // F. Chowk Pedestrian Zebra Crossings & Signal Gantries in 3D
    const CHOWK_LOCATIONS = [
      { id: 'VN-01', name: 'Viman Nagar Chowk', lng: 73.91825, lat: 18.56090 },
      { id: 'SN-01', name: 'Somnath Nagar Chowk', lng: 73.92790, lat: 18.56283 }
    ];

    CHOWK_LOCATIONS.forEach(chowk => {
      // 3D Traffic Signal Mast & Gantry
      viewer.entities.add({
        name: `${chowk.name} Signal Gantry`,
        position: Cesium.Cartesian3.fromDegrees(chowk.lng, chowk.lat, 3.0),
        cylinder: {
          length: 6.0,
          topRadius: 0.2,
          bottomRadius: 0.25,
          material: Cesium.Color.fromCssColorString('#334155'),
          outline: false
        }
      });

      // Signal Head Housing with Active Green/Red Emissive Indicator
      viewer.entities.add({
        name: `${chowk.name} Signal Head`,
        position: Cesium.Cartesian3.fromDegrees(chowk.lng, chowk.lat, 6.2),
        box: {
          dimensions: new Cesium.Cartesian3(1.2, 0.6, 0.6),
          material: Cesium.Color.fromCssColorString('#10B981').withAlpha(0.95), // Active green phase
          outline: true,
          outlineColor: Cesium.Color.WHITE
        }
      });
    });

    // G. Chowk Pedestrian Zebra Crossings & Box Junction Markings in 3D (IRC:35 Grade)
    const CHOWK_ZEBRA_STRIPES = [
      // Viman Nagar Chowk Zebra Crossings
      { id: 'vn-zebra-w-eb', positions: [[73.91812, 18.56068], [73.91812, 18.56086]] },
      { id: 'vn-zebra-w-wb', positions: [[73.91812, 18.56096], [73.91812, 18.56112]] },
      { id: 'vn-zebra-e-eb', positions: [[73.91838, 18.56068], [73.91838, 18.56086]] },
      { id: 'vn-zebra-e-wb', positions: [[73.91838, 18.56096], [73.91838, 18.56112]] },
      { id: 'vn-zebra-s-nb', positions: [[73.91816, 18.56066], [73.91834, 18.56066]] },
      // Somnath Nagar Chowk Zebra Crossings
      { id: 'sn-zebra-w', positions: [[73.92774, 18.56260], [73.92774, 18.56302]] },
      { id: 'sn-zebra-e', positions: [[73.92806, 18.56260], [73.92806, 18.56302]] },
      { id: 'sn-zebra-s', positions: [[73.92778, 18.56258], [73.92802, 18.56258]] },
    ];

    CHOWK_ZEBRA_STRIPES.forEach(stripe => {
      viewer.entities.add({
        name: 'Pedestrian Zebra Crossing',
        polyline: {
          positions: stripe.positions.map(p => Cesium.Cartesian3.fromDegrees(p[0], p[1], 0.2)),
          width: 8.0,
          material: new Cesium.PolylineDashMaterialProperty({
            color: Cesium.Color.WHITE.withAlpha(0.95),
            gapColor: Cesium.Color.TRANSPARENT,
            dashLength: 16.0,
            dashPattern: 255
          }),
          clampToGround: true
        }
      });
    });

    // Yellow Box Junctions in 3D
    const CHOWK_BOX_JUNCTIONS = [
      {
        name: 'Viman Nagar Box Junction',
        positions: [
          [73.91816, 18.56070],
          [73.91834, 18.56070],
          [73.91834, 18.56110],
          [73.91816, 18.56110],
          [73.91816, 18.56070]
        ]
      },
      {
        name: 'Somnath Nagar Box Junction',
        positions: [
          [73.92778, 18.56260],
          [73.92802, 18.56260],
          [73.92802, 18.56300],
          [73.92778, 18.56300],
          [73.92778, 18.56260]
        ]
      }
    ];

    CHOWK_BOX_JUNCTIONS.forEach(box => {
      viewer.entities.add({
        name: box.name,
        polygon: {
          hierarchy: new Cesium.PolygonHierarchy(
            box.positions.map(p => Cesium.Cartesian3.fromDegrees(p[0], p[1], 0.1))
          ),
          material: Cesium.Color.fromCssColorString('#F59E0B').withAlpha(0.18),
          outline: true,
          outlineColor: Cesium.Color.fromCssColorString('#F59E0B').withAlpha(0.85),
          outlineWidth: 2,
          height: 0.1
        }
      });
    });
  }, [corridorGeoJson, currentTheme]);

  // 3B. Dynamic Solar Position & Shadow Control Effect
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    if (solarTime === 'midday') {
      viewer.clock.currentTime = Cesium.JulianDate.fromIso8601('2026-09-22T06:00:00Z'); // 11:30 AM IST
      viewer.scene.globe.enableLighting = true;
      viewer.shadows = true;
    } else if (solarTime === 'golden') {
      viewer.clock.currentTime = Cesium.JulianDate.fromIso8601('2026-09-22T10:30:00Z'); // 4:00 PM IST (crisp dramatic architectural shadows)
      viewer.scene.globe.enableLighting = true;
      viewer.shadows = true;
    } else if (solarTime === 'night') {
      viewer.clock.currentTime = Cesium.JulianDate.fromIso8601('2026-09-22T15:30:00Z'); // 9:00 PM IST
      viewer.scene.globe.enableLighting = true;
      viewer.shadows = false;
    }
  }, [solarTime]);

  // 4. Dynamic Live Vehicle Kinematics Engine (Continuous 60 FPS Sub-Second Motion)
  useEffect(() => {
    const dataSource = vehiclesCollectionRef.current;
    if (!dataSource || roadSegments.length === 0) return;

    // Collect new vehicle list while preserving existing progress of moving vehicles
    const existingVehiclesMap = new Map(activeVehiclesRef.current.map(v => [v.id, v]));
    const nextVehicles: LiveKinematicVehicle[] = [];

    roadSegments.forEach((segment) => {
      const state = liveStates[segment.id];
      const speed = state?.metrics?.averageSpeedKmh ?? 38.0;
      const flow = state?.metrics?.vehicleFlowPerHour ?? 1200;
      const coords = segment.coordinates;

      if (!coords || coords.length < 2) return;

      // Determine vehicle color based on traffic speed
      let vehicleColor = Cesium.Color.fromCssColorString('#10B981'); // Flowing (Green)
      if (speed < 20) {
        vehicleColor = Cesium.Color.fromCssColorString('#EF4444'); // Congested (Red)
      } else if (speed < 35) {
        vehicleColor = Cesium.Color.fromCssColorString('#F59E0B'); // Dense (Amber)
      }

      const vehicleCount = Math.max(2, Math.min(5, Math.round(flow / 400)));
      for (let i = 0; i < vehicleCount; i++) {
        const vehId = `veh-${segment.id}-${i}`;
        const laneIndex = i % 3;
        const isBusOrVan = laneIndex === 0 && (i % 2 === 0);
        const dimensions = isBusOrVan
          ? new Cesium.Cartesian3(6.5, 2.3, 2.6) // Transit Bus / Mini-Van
          : new Cesium.Cartesian3(4.2, 1.85, 1.45); // Sedan / Compact Car

        const existing = existingVehiclesMap.get(vehId);
        const progress = existing ? existing.progress : (i + 0.3) / vehicleCount;
        const initialPose = computeKinematicPose(coords, progress, laneIndex);

        const vehItem: LiveKinematicVehicle = {
          id: vehId,
          name: `Vehicle ${segment.direction} [Lane ${laneIndex}] #${i + 1}`,
          segmentId: segment.id,
          coords: coords,
          lengthMeters: computePolylineLengthMeters(coords),
          laneIndex: laneIndex,
          progress: progress,
          speedKmh: speed,
          dimensions: dimensions,
          color: isBusOrVan ? Cesium.Color.fromCssColorString('#38BDF8') : vehicleColor,
          currentPosition: initialPose.position,
          currentOrientation: initialPose.orientation
        };
        nextVehicles.push(vehItem);
      }
    });

    activeVehiclesRef.current = nextVehicles;

    // Synchronize Cesium entities with dynamic CallbackProperty bindings
    dataSource.entities.removeAll();
    nextVehicles.forEach((veh) => {
      dataSource.entities.add({
        id: veh.id,
        name: veh.name,
        position: new Cesium.CallbackProperty(() => veh.currentPosition, false) as any,
        orientation: new Cesium.CallbackProperty(() => veh.currentOrientation, false) as any,
        box: {
          dimensions: veh.dimensions,
          material: new Cesium.ColorMaterialProperty(
            new Cesium.CallbackProperty(() => veh.color, false) as any
          ),
          outline: true,
          outlineColor: Cesium.Color.WHITE.withAlpha(0.7)
        }
      });
    });
  }, [liveStates, roadSegments]);

  // 4B. 60 FPS Continuous Frame Kinematic Clock Listener (scene.preRender)
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    lastTimeRef.current = performance.now();
    const removePreRenderListener = viewer.scene.preRender.addEventListener(() => {
      const now = performance.now();
      const dt = Math.min((now - lastTimeRef.current) / 1000.0, 0.1); // Clamp frame delta to 100ms
      lastTimeRef.current = now;

      const vehicles = activeVehiclesRef.current;
      for (let i = 0; i < vehicles.length; i++) {
        const veh = vehicles[i];
        const speedMps = Math.max(5.0, veh.speedKmh * (1000.0 / 3600.0));
        veh.progress = (veh.progress + (speedMps * dt) / Math.max(80.0, veh.lengthMeters)) % 1.0;
        const pose = computeKinematicPose(veh.coords, veh.progress, veh.laneIndex);
        veh.currentPosition = pose.position;
        veh.currentOrientation = pose.orientation;
      }
    });

    return () => {
      removePreRenderListener();
    };
  }, []);

  // 5. Selected Entity Focus Effect
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || !selectedEntity) return;

    if ('coordinates' in selectedEntity) {
      const coords = selectedEntity.coordinates;
      if (Array.isArray(coords) && coords.length > 0) {
        let targetLng = 73.9185;
        let targetLat = 18.5580;
        if (typeof coords[0] === 'number') {
          targetLng = coords[0] as number;
          targetLat = coords[1] as number;
        } else if (Array.isArray(coords[0])) {
          const mid = Math.floor(coords.length / 2);
          targetLng = (coords as [number, number][])[mid][0];
          targetLat = (coords as [number, number][])[mid][1];
        }

        viewer.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(targetLng, targetLat, 220),
          orientation: {
            heading: viewer.camera.heading,
            pitch: Cesium.Math.toRadians(-35),
            roll: 0
          },
          duration: 1.2
        });
      }
    }
  }, [selectedEntity]);

  // 5. Camera Fly-To Handler
  const handleFlyTo = useCallback((vp: CameraViewpoint) => {
    const viewer = viewerRef.current;
    if (!viewer) return;

    setActiveViewpointId(vp.id);
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(vp.longitude, vp.latitude, vp.height),
      orientation: {
        heading: Cesium.Math.toRadians(vp.headingDegrees),
        pitch: Cesium.Math.toRadians(vp.pitchDegrees),
        roll: Cesium.Math.toRadians(vp.rollDegrees)
      },
      duration: 1.8
    });
  }, []);

  return (
    <div className="cesium-viewer-wrapper" style={{ position: 'relative', width: '100%', height: '100%', minHeight: '520px' }}>
      {/* 3D Viewport Container */}
      <div
        ref={containerRef}
        className="cesium-container"
        style={{ width: '100%', height: '100%', borderRadius: 'var(--radius-md, 8px)', overflow: 'hidden' }}
      />

      {/* Viewpoint Camera Toolbar */}
      <CesiumCameraControls
        activeViewpointId={activeViewpointId}
        onFlyToViewpoint={handleFlyTo}
      />

      {/* 3D Basemap Selector Bar */}
      <div
        className="cesium-basemap-toolbar"
        style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          zIndex: 20,
          display: 'flex',
          gap: '3px',
          background: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(8px)',
          padding: '3px',
          borderRadius: '8px',
          border: '1px solid rgba(255, 255, 255, 0.12)'
        }}
        role="toolbar"
        aria-label="3D Basemap Selection"
      >
        <button
          type="button"
          className={`map-view-toggle-btn ${basemap3D === 'satellite' ? 'active' : ''}`}
          onClick={() => setBasemap3D('satellite')}
          title="High-Resolution Satellite Imagery"
          style={{
            padding: '4px 8px',
            fontSize: '11px',
            borderRadius: '5px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: basemap3D === 'satellite' ? '#2F81F7' : 'transparent',
            color: '#FFFFFF'
          }}
        >
          <span>🛰️ Satellite</span>
        </button>
        <button
          type="button"
          className={`map-view-toggle-btn ${basemap3D === 'streets' ? 'active' : ''}`}
          onClick={() => setBasemap3D('streets')}
          title="Google Maps-Style Clean Street Map"
          style={{
            padding: '4px 8px',
            fontSize: '11px',
            borderRadius: '5px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: basemap3D === 'streets' ? '#2F81F7' : 'transparent',
            color: '#FFFFFF'
          }}
        >
          <span>🗺️ Streets</span>
        </button>
        <button
          type="button"
          className={`map-view-toggle-btn ${basemap3D === 'dark' ? 'active' : ''}`}
          onClick={() => setBasemap3D('dark')}
          title="Dark Operations Canvas"
          style={{
            padding: '4px 8px',
            fontSize: '11px',
            borderRadius: '5px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: basemap3D === 'dark' ? '#2F81F7' : 'transparent',
            color: '#FFFFFF'
          }}
        >
          <span>🌃 Dark</span>
        </button>
      </div>

      {/* Dynamic Solar Time & Building Shadow Toolbar (Pune Local Time) */}
      <div
        className="cesium-solar-toolbar"
        style={{
          position: 'absolute',
          top: '52px',
          right: '12px',
          zIndex: 20,
          display: 'flex',
          gap: '3px',
          background: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(8px)',
          padding: '3px',
          borderRadius: '8px',
          border: '1px solid rgba(255, 255, 255, 0.12)'
        }}
        role="toolbar"
        aria-label="3D Solar Lighting & Shadow Preset"
      >
        <button
          type="button"
          className={`map-view-toggle-btn ${solarTime === 'golden' ? 'active' : ''}`}
          onClick={() => setSolarTime('golden')}
          title="Golden Hour (4:00 PM IST) - Architectural Shadows across Nagar Road"
          style={{
            padding: '4px 8px',
            fontSize: '11px',
            borderRadius: '5px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: solarTime === 'golden' ? '#D97706' : 'transparent',
            color: '#FFFFFF'
          }}
        >
          <span>🌅 Golden (4 PM)</span>
        </button>
        <button
          type="button"
          className={`map-view-toggle-btn ${solarTime === 'midday' ? 'active' : ''}`}
          onClick={() => setSolarTime('midday')}
          title="Midday (11:30 AM IST) - Overhead Sun"
          style={{
            padding: '4px 8px',
            fontSize: '11px',
            borderRadius: '5px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: solarTime === 'midday' ? '#2563EB' : 'transparent',
            color: '#FFFFFF'
          }}
        >
          <span>☀️ Day (11 AM)</span>
        </button>
        <button
          type="button"
          className={`map-view-toggle-btn ${solarTime === 'night' ? 'active' : ''}`}
          onClick={() => setSolarTime('night')}
          title="Night Operations (9:00 PM IST)"
          style={{
            padding: '4px 8px',
            fontSize: '11px',
            borderRadius: '5px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: solarTime === 'night' ? '#7C3AED' : 'transparent',
            color: '#FFFFFF'
          }}
        >
          <span>🌙 Night</span>
        </button>
      </div>

      {/* 3D Building Dynamic Hover Tooltip Card */}
      {hoveredBuilding3D && hoverPos3D && (
        <div
          className="cesium-building-hover-card"
          style={{
            position: 'absolute',
            left: Math.min(hoverPos3D.x + 14, (typeof window !== 'undefined' ? window.innerWidth : 1200) - 300),
            top: Math.max(10, hoverPos3D.y - 12),
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
            {hoveredBuilding3D.name}
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
              {hoveredBuilding3D.category?.replace(/_/g, ' ')}
            </span>
            <span style={{ fontSize: '11px', color: '#94A3B8' }}>
              {hoveredBuilding3D.height}m ({hoveredBuilding3D.levels} floors)
            </span>
          </div>
          {hoveredBuilding3D.demandKw && (
            <div style={{ fontSize: '11px', color: '#F0883E', fontWeight: 600 }}>
              ⚡ Sanctioned Demand: {hoveredBuilding3D.demandKw.toLocaleString()} kW
            </div>
          )}
        </div>
      )}

      {/* Top Legend / Status Overlay */}
      <div className="cesium-overlay-legend">
        <div className="cesium-status-badge">
          <Activity size={13} className="text-emerald-400 animate-pulse" />
          <span>3D Simulation Twin • 1.8 km Nagar Road</span>
        </div>
        <div className="cesium-legend-items">
          <span className="legend-chip">
            <span className="chip-color" style={{ backgroundColor: '#0284C7' }} />
            <span>Retail / Malls</span>
          </span>
          <span className="legend-chip">
            <span className="chip-color" style={{ backgroundColor: '#2563EB' }} />
            <span>IT / Tech Parks</span>
          </span>
          <span className="legend-chip">
            <span className="chip-color" style={{ backgroundColor: '#D97706' }} />
            <span>Hotels</span>
          </span>
          <span className="legend-chip">
            <span className="chip-color" style={{ backgroundColor: '#059669' }} />
            <span>Residential</span>
          </span>
        </div>
      </div>

      {/* Loading Banner */}
      {isLoading && (
        <div className="cesium-loading-curtain">
          <div className="spinner-border text-cyan-400" role="status" />
          <span>Ingesting 3D Corridor Spatial Registry...</span>
        </div>
      )}

      {/* Error / Notice Notification */}
      {errorNotice && (
        <div className="cesium-error-notice" role="alert">
          <AlertTriangle size={15} />
          <span>{errorNotice}</span>
        </div>
      )}
    </div>
  );
};
