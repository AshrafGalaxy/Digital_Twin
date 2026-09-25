import {
  EntityCurrentState,
  IntersectionAsset,
  RoadSegmentAsset,
  TrafficSensorAsset,
  BuildingAsset,
  AdvisoryRecommendation,
  AdvisorySummary,
  AuthUser,
  EnvironmentState,
  AirQualityStationAsset
} from '../types/twin';

const API_BASE = '/api/v1';

/**
 * Resilient fetch wrapper with automatic backoff and retry.
 * Handles transient network dropouts, 503 (backend warming up), and 502/504 gateway delays gracefully.
 */
export async function resilientFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
  retries = 3,
  delayMs = 400
): Promise<Response> {
  let attempt = 0;
  while (attempt < retries) {
    try {
      const res = await fetch(input, init);
      if ((res.status === 503 || res.status === 502 || res.status === 504) && attempt < retries - 1) {
        attempt++;
        await new Promise((resolve) => setTimeout(resolve, delayMs * attempt));
        continue;
      }
      return res;
    } catch (err) {
      attempt++;
      if (attempt >= retries) throw err;
      await new Promise((resolve) => setTimeout(resolve, delayMs * attempt));
    }
  }
  return fetch(input, init);
}

export async function fetchStudyArea(): Promise<any> {
  const res = await resilientFetch(`${API_BASE}/study-area`);
  if (!res.ok) throw new Error('Failed to fetch study area');
  return res.json();
}

export async function fetchIntersections(): Promise<IntersectionAsset[]> {
  const res = await resilientFetch(`${API_BASE}/assets/intersections`);
  if (!res.ok) throw new Error('Failed to fetch intersections');
  return res.json();
}

export async function fetchRoadSegments(): Promise<RoadSegmentAsset[]> {
  const res = await resilientFetch(`${API_BASE}/assets/segments`);
  if (!res.ok) throw new Error('Failed to fetch road segments');
  return res.json();
}

export async function fetchSensors(): Promise<TrafficSensorAsset[]> {
  const res = await resilientFetch(`${API_BASE}/assets/sensors`);
  if (!res.ok) throw new Error('Failed to fetch sensors');
  return res.json();
}

export async function fetchEnergyEntities(): Promise<BuildingAsset[]> {
  const res = await resilientFetch(`${API_BASE}/assets/energy`);
  if (!res.ok) throw new Error('Failed to fetch energy entities');
  return res.json();
}

export async function fetchCurrentState(): Promise<EntityCurrentState[]> {
  try {
    const res = await resilientFetch(`${API_BASE}/state/current`);
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export async function fetchHistoricalSnapshot(minutesAgo: number): Promise<EntityCurrentState[]> {
  try {
    const res = await resilientFetch(`${API_BASE}/state/snapshot?minutes_ago=${minutesAgo}`);
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export async function fetchReplayStatus(): Promise<{
  isPlaying: boolean;
  minutesAgo: number;
  speed: number;
  targetTime: string;
  sourceMode: string;
}> {
  try {
    const res = await fetch(`${API_BASE}/stream/replay/status`);
    if (!res.ok) return { isPlaying: false, minutesAgo: 0, speed: 1.0, targetTime: new Date().toISOString(), sourceMode: 'SIMULATION' };
    return res.json();
  } catch {
    return { isPlaying: false, minutesAgo: 0, speed: 1.0, targetTime: new Date().toISOString(), sourceMode: 'SIMULATION' };
  }
}

export async function controlReplaySession(params: {
  action: 'play' | 'pause' | 'seek' | 'speed' | 'jump_to_live';
  minutes_ago?: number;
  speed?: number;
}): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/stream/replay/control`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export interface SegmentComparisonResult {
  segmentA: {
    id: string;
    name: string;
    direction: string;
    speedLimitKmh: number;
    averageSpeedKmh: number;
    congestionIndex: number;
    vehicleFlowPerHour: number;
    queueLengthMeters: number;
    levelOfService: string;
    sourceMode: string;
  };
  segmentB: {
    id: string;
    name: string;
    direction: string;
    speedLimitKmh: number;
    averageSpeedKmh: number;
    congestionIndex: number;
    vehicleFlowPerHour: number;
    queueLengthMeters: number;
    levelOfService: string;
    sourceMode: string;
  };
  deltas: {
    speedDeltaKmh: number;
    queueDeltaMeters: number;
    congestionIndexDelta: number;
    flowDeltaPerHour: number;
  };
  directionalImbalance: {
    dominantCongestionDirection?: string;
    severity: 'CRITICAL' | 'ELEVATED' | 'BALANCED';
    summary: string;
  };
}

export async function fetchSegmentComparison(
  segmentA: string,
  segmentB: string
): Promise<SegmentComparisonResult | null> {
  try {
    const res = await fetch(
      `${API_BASE}/state/compare?segment_a=${encodeURIComponent(segmentA)}&segment_b=${encodeURIComponent(segmentB)}`
    );
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}


export async function fetchScenarioTemplates(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/scenarios/templates`);
  if (!res.ok) throw new Error('Failed to fetch scenario templates');
  return res.json();
}

export async function runScenario(params: {
  templateId: string;
  greenExtensionSec?: number;
  coordinationOffsetSec?: number;
  demandMultiplier: number;
  randomSeed: number;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/scenarios/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error('Failed to execute simulation run');
  return res.json();
}

export async function proposeAdvisoryFromScenarioRun(
  runId: string,
  reviewer: string = 'Municipal Analyst',
  notes: string = ''
): Promise<any> {
  const res = await fetch(`${API_BASE}/scenarios/runs/${encodeURIComponent(runId)}/propose-advisory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewer, notes })
  });
  if (!res.ok) throw new Error('Failed to propose advisory recommendation');
  return res.json();
}

export async function fetchRecentScenarioRuns(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE}/scenarios/runs`);
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export async function fetchTrafficForecast(segmentId: string, currentSpeed?: number): Promise<any> {
  const url = currentSpeed !== undefined
    ? `${API_BASE}/forecasts/traffic/${encodeURIComponent(segmentId)}?current_speed=${currentSpeed}`
    : `${API_BASE}/forecasts/traffic/${encodeURIComponent(segmentId)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch traffic forecast');
  return res.json();
}

export async function fetchEnergyForecast(buildingId: string, currentKw?: number): Promise<any> {
  const url = currentKw !== undefined
    ? `${API_BASE}/forecasts/energy/${encodeURIComponent(buildingId)}?current_kw=${currentKw}`
    : `${API_BASE}/forecasts/energy/${encodeURIComponent(buildingId)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch energy forecast');
  return res.json();
}

export async function fetchForecastModels(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE}/forecasts/models`);
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export function connectStateStream(
  onUpdate: (data: any) => void,
  onConnectionChange?: (connected: boolean) => void
): () => void {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.hostname}:8000/api/v1/stream/state`;

  let ws: WebSocket | null = null;
  let reconnectTimeout: any = null;
  let isUnmounted = false;

  function connect() {
    if (isUnmounted) return;
    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        onConnectionChange?.(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          onUpdate(payload);
        } catch (e) {
          console.warn('Failed parsing WS payload', e);
        }
      };

      ws.onclose = () => {
        onConnectionChange?.(false);
        if (!isUnmounted) {
          reconnectTimeout = setTimeout(connect, 3000);
        }
      };

      ws.onerror = () => {
        ws?.close();
      };
    } catch {
      onConnectionChange?.(false);
      reconnectTimeout = setTimeout(connect, 3000);
    }
  }

  connect();

  return () => {
    isUnmounted = true;
    clearTimeout(reconnectTimeout);
    ws?.close();
  };
}

export async function fetchRecommendations(domain?: string, status?: string): Promise<AdvisoryRecommendation[]> {
  const params = new URLSearchParams();
  if (domain) params.append('domain', domain);
  if (status) params.append('status', status);
  const query = params.toString() ? `?${params.toString()}` : '';
  const res = await resilientFetch(`${API_BASE}/recommendations${query}`);
  if (!res.ok) throw new Error('Failed to fetch advisory recommendations');
  return res.json();
}

export async function fetchAdvisorySummary(): Promise<AdvisorySummary> {
  const res = await resilientFetch(`${API_BASE}/recommendations/summary`);
  if (!res.ok) throw new Error('Failed to fetch advisory summary');
  return res.json();
}

export async function fetchRecommendationDetail(recId: string): Promise<AdvisoryRecommendation> {
  const res = await resilientFetch(`${API_BASE}/recommendations/${recId}`);
  if (!res.ok) throw new Error(`Failed to fetch recommendation ${recId}`);
  return res.json();
}

export async function reviewRecommendation(
  recId: string,
  newStatus: string,
  reviewer: string,
  notes?: string
): Promise<AdvisoryRecommendation> {
  const res = await fetch(`${API_BASE}/recommendations/${recId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ newStatus, reviewer, notes })
  });
  if (!res.ok) throw new Error(`Failed to review recommendation ${recId}`);
  return res.json();
}

export async function triggerRuleEvaluation(): Promise<AdvisoryRecommendation[]> {
  const res = await fetch(`${API_BASE}/recommendations/evaluate`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error('Failed to trigger rule evaluation');
  return res.json();
}

export interface DatasetManifestSummary {
  id: string;
  manifestId: string;
  name: string;
  localityClassification: 'PILOT_LOCAL' | 'PUNE_NON_LOCAL' | 'REGIONAL_CONTEXT' | 'BENCHMARK_SYNTHETIC' | 'SIMULATION';
  sourceMode: string;
  license: string;
  intendedUse: string;
  prohibitedClaim?: string;
  manifestJson?: string;
  manifestMarkdown?: string;
  fieldsCount?: number;
}

export interface DatasetCatalogResponse {
  catalogVersion: string;
  updatedAt: string;
  studyArea: string;
  totalDatasets: number;
  datasets: DatasetManifestSummary[];
}

export interface DetailedDatasetManifest {
  datasetId: string;
  datasetName: string;
  version: string;
  sourceUrl: string;
  accessDate: string;
  license: string;
  attributionRequirements?: string;
  localityClassification: string;
  sourceMode: string;
  geographicBoundary?: any;
  temporalCoverage?: any;
  fields?: Array<{ name: string; unit: string; description: string }>;
  intendedUse: string;
  prohibitedClaims: string;
  knownLimitations: string;
  privacySensitivityAssessment?: string;
  status?: string;
}

export async function fetchDatasetManifests(): Promise<DatasetCatalogResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/datasets/manifests`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function fetchDatasetManifest(id: string): Promise<DetailedDatasetManifest | null> {
  try {
    const res = await fetch(`${API_BASE}/datasets/manifests/${id}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export interface QuarantineRecord {
  id: number;
  quarantinedAt: string;
  entityId?: string;
  entityType?: string;
  sourceMode?: string;
  observedAt?: string;
  rejectionReason: string;
  rawPayload: Record<string, any>;
  validationDetails: Record<string, any>;
}

export interface QuarantineQueueResponse {
  totalQuarantined: number;
  reasonsBreakdown: Record<string, number>;
  lastQuarantinedAt?: string;
  dataHonestyStatus: string;
  records: QuarantineRecord[];
}

export async function fetchQuarantineQueue(
  limit: number = 50,
  offset: number = 0,
  reason?: string
): Promise<QuarantineQueueResponse | null> {
  try {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    if (reason) params.append('reason', reason);

    const res = await fetch(`${API_BASE}/health/quarantine?${params.toString()}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export interface TrafficRollupRecord {
  bucket15m: string;
  segmentId: string;
  sampleCount: number;
  avgSpeedKmh: number;
  p85SpeedKmh: number;
  totalFlowVeh: number;
  avgOccupancyPercent: number;
  avgQueueLengthMeters: number;
  maxQueueLengthMeters: number;
  avgCongestionIndex: number;
}

export interface TrafficRollupsResponse {
  totalRecords: number;
  segmentId?: string;
  hoursAgo: number;
  rollups: TrafficRollupRecord[];
}

export async function fetchTrafficRollups(
  segmentId?: string,
  hoursAgo: number = 12,
  limit: number = 100
): Promise<TrafficRollupsResponse | null> {
  try {
    const params = new URLSearchParams();
    if (segmentId) params.append('segment_id', segmentId);
    params.append('hours_ago', hoursAgo.toString());
    params.append('limit', limit.toString());

    const res = await fetch(`${API_BASE}/analytics/rollups/traffic?${params.toString()}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export interface StreamerStatusResponse {
  isRunning: boolean;
  isPaused: boolean;
  ticksCount: number;
  intervalSec: number;
  lastTickAt?: string;
  sourceMode: string;
}

export async function fetchStreamerStatus(): Promise<StreamerStatusResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/stream/simulator/status`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function controlStreamer(params: {
  action: 'start' | 'stop' | 'pause' | 'resume' | 'tick_once' | 'set_interval';
  interval_sec?: number;
}): Promise<StreamerStatusResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/stream/simulator/control`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

// Milestone 9: Evaluation, Executive Reporting & Corridor Export
export async function fetchEvaluationBenchmarks(): Promise<any> {
  const res = await fetch(`${API_BASE}/analytics/evaluation/benchmarks`);
  if (!res.ok) throw new Error('Failed to fetch evaluation benchmarks');
  return res.json();
}

export async function fetchExecutiveSummary(): Promise<any> {
  const res = await fetch(`${API_BASE}/reports/executive-summary`);
  if (!res.ok) throw new Error('Failed to fetch executive summary');
  return res.json();
}

export async function fetchExecutiveSummaryMarkdown(): Promise<string> {
  const res = await fetch(`${API_BASE}/reports/executive-summary/markdown`);
  if (!res.ok) throw new Error('Failed to fetch executive markdown briefing');
  return res.text();
}

export async function fetchCorridorBundle(): Promise<any> {
  const res = await fetch(`${API_BASE}/export/corridor-bundle`);
  if (!res.ok) throw new Error('Failed to export corridor bundle');
  return res.json();
}

export async function loginMunicipalUser(usernameOrEmail: string, password: string): Promise<AuthUser> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username_or_email: usernameOrEmail,
      password
    })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Authentication failed. Please verify credentials.');
  }
  return res.json();
}

export async function registerMunicipalUser(payload: {
  name: string;
  email: string;
  password: string;
  role: string;
  department?: string;
}): Promise<AuthUser> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Registration failed.');
  }
  return res.json();
}

export async function fetchMunicipalRoles(): Promise<{ roles: string[]; metadata: Record<string, any> }> {
  const res = await fetch(`${API_BASE}/auth/roles`);
  if (!res.ok) throw new Error('Failed to fetch municipal roles');
  return res.json();
}

export async function fetchCurrentEnvironment(stationId?: string): Promise<EnvironmentState> {
  const url = stationId
    ? `${API_BASE}/environment/current?station_id=${encodeURIComponent(stationId)}`
    : `${API_BASE}/environment/current`;
  const res = await resilientFetch(url);
  if (!res.ok) throw new Error('Failed to fetch environment state');
  return res.json();
}

export async function fetchEnvironmentStations(): Promise<AirQualityStationAsset[]> {
  const res = await resilientFetch(`${API_BASE}/environment/stations`);
  if (!res.ok) throw new Error('Failed to fetch environment stations');
  return res.json();
}



