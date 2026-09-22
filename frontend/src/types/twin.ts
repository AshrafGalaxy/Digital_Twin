export type SourceMode = 'LIVE' | 'REPLAY' | 'SIMULATION' | 'PREDICTED' | 'STALE' | 'INVALID';

export type MunicipalRole =
  | 'Municipal Analyst'
  | 'Traffic Systems Engineer'
  | 'Energy Grid Manager'
  | 'Executive Auditor';

export type QualityStatus = 'VALID' | 'STALE' | 'DEGRADED' | 'INVALID';

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: MunicipalRole;
  department: string;
  token?: string;
  authenticatedAt: string;
  clearance?: string;
  workspaces?: string[];
}


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
  connectedSegments?: string[];
  phases?: number;
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

export interface ConformalInterval {
  lower: number;
  upper: number;
  margin: number;
  coverageTarget: number;
  empiricalTestCoverage: number;
}

export interface FeatureContribution {
  feature: string;
  displayName: string;
  contribution: number;
  impact: 'INCREASES' | 'DECREASES';
}

export interface LocalExplanation {
  baseValue: number;
  topContributors: FeatureContribution[];
}

export interface TrafficForecast {
  entityId: string;
  targetMetric: string;
  sourceMode: SourceMode;
  generatedAt: string;
  targetTimestamp: string;
  horizonMinutes: number;
  predictedValue: number;
  confidenceLower: number;
  confidenceUpper: number;
  conformalIntervals?: {
    interval90: ConformalInterval;
    interval95: ConformalInterval;
  };
  explanation?: LocalExplanation;
  unit: string;
  modelVersion: string;
  inputQualityStatus: string;
  baselineComparison: {
    persistenceValue?: number;
    modelTestMae?: number;
    persistenceMae?: number;
    accuracyGainPct?: number;
  };
  localityNotice: string;
}

export interface EnergyForecast {
  entityId: string;
  targetMetric: string;
  sourceMode: SourceMode;
  generatedAt: string;
  targetTimestamp: string;
  horizonMinutes: number;
  predictedValue: number;
  confidenceLower: number;
  confidenceUpper: number;
  conformalIntervals?: {
    interval90: ConformalInterval;
    interval95: ConformalInterval;
  };
  explanation?: LocalExplanation;
  unit: string;
  modelVersion: string;
  inputQualityStatus: string;
  isPeakDemandAlert: boolean;
  peakThresholdKw: number;
  baselineComparison: {
    persistenceValue?: number;
    modelTestMae?: number;
    persistenceMae?: number;
    sameHourMae?: number;
    accuracyGainPct?: number;
  };
  sourceLimitation: string;
}

export interface ModelVersion {
  modelId: string;
  domain: string;
  targetMetric: string;
  horizonMinutes: number;
  unit: string;
  status: string;
  testMae: number;
  testRmse: number;
  improvementVsPersistencePct: number;
  trainedAt: string;
  localityCaveat?: string;
}

export type RecommendationDomain = 'TRAFFIC' | 'ENERGY' | 'ENVIRONMENT';
export type RecommendationSeverity = 'INFO' | 'WARNING' | 'CRITICAL';
export type RecommendationStatus = 'ACTIVE' | 'UNDER_REVIEW' | 'ACKNOWLEDGED' | 'DISMISSED';

export interface RecommendationEvidence {
  sourceMode: SourceMode;
  metricName: string;
  observedOrPredictedValue: number;
  threshold: number;
  unit: string;
  horizonMinutes?: number;
  modelVersion?: string;
  scenarioId?: string;
  confidenceScore?: number;
  timestamp: string;
}

export interface AuditLogEntry {
  timestamp: string;
  previousStatus: RecommendationStatus;
  newStatus: RecommendationStatus;
  reviewer: string;
  notes?: string;
}

export interface AdvisoryRecommendation {
  recommendationId: string;
  domain: RecommendationDomain;
  severity: RecommendationSeverity;
  status: RecommendationStatus;
  targetEntityId: string;
  title: string;
  description: string;
  triggerRule: string;
  evidence: RecommendationEvidence;
  suggestedAction: string;
  humanApprovalRequired: boolean;
  governanceNotice: string;
  auditTrail: AuditLogEntry[];
  createdAt: string;
  updatedAt: string;
}

export interface AdvisorySummary {
  totalActive: number;
  criticalCount: number;
  warningCount: number;
  infoCount: number;
  byDomain: Record<string, number>;
}

