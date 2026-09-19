export type SourceMode = 'LIVE' | 'REPLAY' | 'SIMULATION' | 'PREDICTED' | 'STALE' | 'INVALID';

export type QualityStatus = 'VALID' | 'STALE' | 'DEGRADED' | 'INVALID';

export interface EntityCurrentState {
  entityId: string;
  entityType: string;
  sourceMode: SourceMode;
  observedAt: string;
  updatedAt: string;
  metrics: {
    averageSpeedKmh?: number;
    vehicleFlowPerHour?: number;
    occupancyPercent?: number;
    queueLengthMeters?: number;
    congestionIndex?: number;
    activePowerKw?: number;
  };
  qualityStatus: QualityStatus;
  freshnessSeconds: number;
}

export interface IntersectionAsset {
  id: string;
  name: string;
  controlType: string;
  coordinates: [number, number];
  cycleTimeSec: number;
}

export interface RoadSegmentAsset {
  id: string;
  name: string;
  direction: string;
  lanes: number;
  speedLimitKmh: number;
  coordinates: [number, number][];
}

export interface TrafficSensorAsset {
  id: string;
  name: string;
  linkedSegmentId: string;
  direction: string;
  coordinates: [number, number];
}

export interface BuildingAsset {
  id: string;
  name: string;
  category: string;
  grossFloorAreaSqMeters: number;
  baselineMetrics: {
    averageDaytimeDemandKW: number;
    peakEveningDemandKW: number;
    nightBaseDemandKW: number;
  };
  provenanceNotice: string;
}
