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

export interface ScenarioTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  parametersSchema: Record<string, any>;
  defaultParameters: Record<string, any>;
}

export interface ScenarioKPIs {
  average_travel_time_sec: number;
  average_delay_sec: number;
  p95_queue_length_meters: number;
  throughput_veh_per_hour: number;
}

export interface ScenarioDeltas {
  travel_time_delta_pct?: number;
  travel_time_saved_sec?: number;
  delay_delta_pct?: number;
  delay_saved_sec?: number;
  queue_length_delta_pct?: number;
  queue_reduced_meters?: number;
  throughput_delta_pct?: number;
  additional_throughput_vph?: number;
  overall_verdict: string;
}

export interface ScenarioRunResult {
  runId: string;
  templateId: string;
  name: string;
  status: string;
  sourceMode: SourceMode;
  governanceNotice: string;
  randomSeed: number;
  networkVersion: string;
  demandVersion: string;
  executedAt: string;
  parameters: Record<string, any>;
  baseline: {
    templateId: string;
    kpis: ScenarioKPIs;
  };
  intervention: {
    templateId: string;
    kpis: ScenarioKPIs;
  };
  deltas: ScenarioDeltas;
}
