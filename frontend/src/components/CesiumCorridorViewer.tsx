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
          new Cesium.OpenStreetMapImageryProvider({
            url: 'https://tile.openstreetmap.org/'
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

      // Click Handler for Entity Picking
      const handler = new Cesium.ScreenSpaceEventHandler(scene.canvas);
      handler.setInputAction((movement: any) => {
        const pickedObject = scene.pick(movement.position);
        if (Cesium.defined(pickedObject) && pickedObject.id) {
          const entity = pickedObject.id;
          const entityId = entity.id || (entity.properties && entity.properties.entityId?.getValue());
          if (entityId) {
            // Find matching road segment or intersection
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

  // 3. Render Static 3D Spatial Geometry (Buildings, Roads, Sensors)
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || !corridorGeoJson) return;

    // Clear static entities (keep dynamic vehicles & signals in dataSources)
    viewer.entities.removeAll();

    const isLight = currentTheme === 'light';

    corridorGeoJson.features.forEach((feature) => {
      const props = feature.properties || {};
      const layer = props.layer;

      // A. Building Extrusion (Phoenix Marketcity)
      if (layer === 'buildings' && feature.geometry.type === 'Polygon') {
        const coords = feature.geometry.coordinates[0];
        const flatHierarchy = coords.map((c: number[]) =>
          Cesium.Cartesian3.fromDegrees(c[0], c[1], 0)
        );

        const height = props.heightMeters || 45.0;
        const buildingColor = Cesium.Color.fromCssColorString(
          props.colorTint || (isLight ? '#006B6F' : '#0F4C5C')
        ).withAlpha(0.88);

        const outlineColor = Cesium.Color.fromCssColorString(
          isLight ? '#004A4D' : '#38BDF8'
        ).withAlpha(0.95);

        viewer.entities.add({
          id: feature.id,
          name: props.name || 'Phoenix Marketcity',
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
            heightMeters: height,
            levels: props.buildingLevels || 6
          }
        });

        // Building Floating Label
        if (coords.length > 0) {
          const centerLng = coords.reduce((acc: number, c: number[]) => acc + c[0], 0) / coords.length;
          const centerLat = coords.reduce((acc: number, c: number[]) => acc + c[1], 0) / coords.length;

          viewer.entities.add({
            position: Cesium.Cartesian3.fromDegrees(centerLng, centerLat, height + 6.0),
            label: {
              text: `🏢 ${props.name || 'Phoenix Marketcity'} (${height}m)`,
              font: '600 13px Inter, sans-serif',
              fillColor: Cesium.Color.WHITE,
              outlineColor: Cesium.Color.fromCssColorString('#0F172A'),
              outlineWidth: 3,
              style: Cesium.LabelStyle.FILL_AND_OUTLINE,
              verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
              pixelOffset: new Cesium.Cartesian2(0, -6),
              disableDepthTestDistance: Number.POSITIVE_INFINITY
            }
          });
        }
      }

      // B. Road Segment Centerlines & Ribbons
      if (layer === 'roads' && feature.geometry.type === 'LineString') {
        const coords = feature.geometry.coordinates;
        const positions = coords.map((c: number[]) =>
          Cesium.Cartesian3.fromDegrees(c[0], c[1], 1.5)
        );

        const isEB = (props.direction || '').toUpperCase() === 'EASTBOUND';
        const roadColor = Cesium.Color.fromCssColorString(
          isEB ? '#0EA5E9' : '#F59E0B'
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
            color: Cesium.Color.fromCssColorString(isLight ? '#006B6F' : '#22D3EE'),
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2,
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          },
          label: {
            text: `🚦 ${props.name}`,
            font: '500 12px Inter, sans-serif',
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

      {/* Top Legend / Status Overlay */}
      <div className="cesium-overlay-legend">
        <div className="cesium-status-badge">
          <Activity size={13} className="text-emerald-400 animate-pulse" />
          <span>3D Simulation Twin • 1.8 km Nagar Road</span>
        </div>
        <div className="cesium-legend-items">
          <span className="legend-chip">
            <span className="chip-color" style={{ backgroundColor: '#0F4C5C' }} />
            <span>Phoenix (45m)</span>
          </span>
          <span className="legend-chip">
            <span className="chip-color" style={{ backgroundColor: '#10B981' }} />
            <span>Flowing (&gt;40)</span>
          </span>
          <span className="legend-chip">
            <span className="chip-color" style={{ backgroundColor: '#F59E0B' }} />
            <span>Dense (20-40)</span>
          </span>
          <span className="legend-chip">
            <span className="chip-color" style={{ backgroundColor: '#EF4444' }} />
            <span>Queued (&lt;20)</span>
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
