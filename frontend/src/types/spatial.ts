export interface SpatialLaneModel {
  laneIndex: number;
  sumoLaneId: string;
  type: 'CURBSIDE' | 'THROUGH' | 'MEDIAN_OVERTAKING' | string;
  widthMeters: number;
  offsetMeters: number;
}

export interface SpatialRoadSegment {
  segmentId: string;
  sumoEdgeId: string;
  name: string;
  direction: 'EASTBOUND' | 'WESTBOUND' | 'NORTHBOUND' | 'SOUTHBOUND' | string;
  fromJunction?: string;
  toJunction?: string;
  lengthMeters: number;
  laneCount: number;
  speedLimitKmh: number;
  osmHighway: string;
  coordinates: [number, number][];
  lanes: SpatialLaneModel[];
}

export interface SpatialIntersection {
  intersectionId: string;
  sumoJunctionId: string;
  name: string;
  controlType: string;
  coordinates: [number, number];
  cycleTimeSec: number;
  phasesCount: number;
  approachEdges: string[];
  departureEdges: string[];
  tlsProgramId?: string;
}

export interface SpatialSignalGroup {
  groupId: string;
  name: string;
  approachEdge: string;
  sumoLinks: number[];
  stopLineCoordinate: [number, number];
  headingDegrees: number;
  greenDurationSec: number;
  yellowDurationSec: number;
}

export interface SpatialSignalController {
  controllerId: string;
  intersectionId: string;
  sumoTlsId: string;
  cycleTimeSec: number;
  signalGroups: SpatialSignalGroup[];
}

export interface SpatialBuildingZone {
  buildingId: string;
  name: string;
  category: string;
  grossFloorAreaSqm: number;
  contractDemandKw: number;
  heightMeters: number;
  buildingLevels: number;
  modelFidelityLevel: string;
  roofType: string;
  colorTint: string;
  centroid: [number, number];
  footprintPolygon: [number, number][];
}

export interface SpatialSensor {
  sensorId: string;
  name: string;
  segmentId?: string;
  sumoEdgeId?: string;
  direction: string;
  coordinates: [number, number];
  elevationMeters: number;
  sensorType: string;
  samplingIntervalSec: number;
}

export interface SpatialRegistryCatalog {
  registryVersion: string;
  crs: string;
  studyAreaId: string;
  name: string;
  boundaryCoordinates: [number, number][];
  roadSegmentMappings: SpatialRoadSegment[];
  intersectionMappings: SpatialIntersection[];
  signalControllers: SpatialSignalController[];
  buildingZoneMappings: SpatialBuildingZone[];
  sensorMappings: SpatialSensor[];
}

export interface Corridor3DFeature {
  type: 'Feature';
  id: string;
  geometry: {
    type: 'Point' | 'LineString' | 'Polygon';
    coordinates: any;
  };
  properties: {
    layer: 'study_area' | 'buildings' | 'roads' | 'intersections' | 'signals' | 'sensors' | string;
    entityType: string;
    name: string;
    heightMeters?: number;
    buildingLevels?: number;
    colorTint?: string;
    direction?: string;
    laneCount?: number;
    speedLimitKmh?: number;
    headingDegrees?: number;
    elevationMeters?: number;
    sensorType?: string;
    [key: string]: any;
  };
}

export interface Corridor3DFeatureCollection {
  type: 'FeatureCollection';
  features: Corridor3DFeature[];
  metadata?: {
    generatedAt: string;
    crs: string;
    featureCount: number;
    studyArea: string;
    corridorLengthKm: number;
  };
}
