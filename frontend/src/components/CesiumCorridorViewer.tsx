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
  const [activeViewpointId, setActiveViewpointId] = useState<string>('corridor-overview');
  const [basemap3D, setBasemap3D] = useState<'satellite' | 'streets' | 'dark'>('satellite');
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
        shadows: false,
        baseLayer: new Cesium.ImageryLayer(
          new Cesium.UrlTemplateImageryProvider({
            url: 'https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            maximumLevel: 18 // CLAMP to 18 to eliminate "map data not yet available"!
          })
        )
      });

      // Configure Scene Aesthetics & Atmosphere
      const scene = viewer.scene;
      scene.globe.depthTestAgainstTerrain = false;
      scene.globe.enableLighting = currentTheme === 'dark';
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
        url: 'https://services.arcgisonline.com/arcgis/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        maximumLevel: 19
      });
    } else if (basemap3D === 'dark') {
      provider = new Cesium.UrlTemplateImageryProvider({
        url: 'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        maximumLevel: 16
      });
    } else {
      provider = new Cesium.UrlTemplateImageryProvider({
        url: 'https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        maximumLevel: 18
      });
    }
    layers.addImageryProvider(provider);
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

      // A. Building Extrusion (89 Surveyed Buildings with Functional Category Color Tints)
      if (layer === 'buildings' && feature.geometry.type === 'Polygon') {
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
  }, [corridorGeoJson, currentTheme]);

  // 4. Dynamic Live Vehicle Simulation Stream
  useEffect(() => {
    const dataSource = vehiclesCollectionRef.current;
    if (!dataSource || roadSegments.length === 0) return;

    // Clear prior vehicles
    dataSource.entities.removeAll();

    // Populate dynamic vehicles across active corridor road segments based on live telemetry
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

      // Distribute 2-5 vehicles per segment along coordinates
      const vehicleCount = Math.max(2, Math.min(5, Math.round(flow / 400)));
      for (let i = 0; i < vehicleCount; i++) {
        const t = (i + 0.5) / vehicleCount;
        const index = Math.min(coords.length - 2, Math.floor(t * (coords.length - 1)));
        const p1 = coords[index];
        const p2 = coords[index + 1];

        // Linear interpolation
        const subT = (t * (coords.length - 1)) - index;
        const lng = p1[0] + (p2[0] - p1[0]) * subT;
        const lat = p1[1] + (p2[1] - p1[1]) * subT;

        // Heading angle in radians
        const dx = p2[0] - p1[0];
        const dy = p2[1] - p1[1];
        const heading = Math.atan2(dy, dx);

        const position = Cesium.Cartesian3.fromDegrees(lng, lat, 1.8);
        const orientation = Cesium.Transforms.headingPitchRollQuaternion(
          position,
          new Cesium.HeadingPitchRoll(heading, 0, 0)
        );

        dataSource.entities.add({
          id: `veh-${segment.id}-${i}`,
          name: `Vehicle ${segment.direction} #${i + 1}`,
          position: position,
          orientation: orientation,
          box: {
            dimensions: new Cesium.Cartesian3(4.2, 1.9, 1.5), // Length, Width, Height
            material: vehicleColor,
            outline: true,
            outlineColor: Cesium.Color.WHITE.withAlpha(0.6)
          }
        });
      }
    });
  }, [liveStates, roadSegments]);

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
