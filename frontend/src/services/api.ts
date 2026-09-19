import {
  EntityCurrentState,
  IntersectionAsset,
  RoadSegmentAsset,
  TrafficSensorAsset,
  BuildingAsset,
  AdvisoryRecommendation,
  AdvisorySummary
} from '../types/twin';

const API_BASE = '/api/v1';

export async function fetchStudyArea(): Promise<any> {
  const res = await fetch(`${API_BASE}/study-area`);
  if (!res.ok) throw new Error('Failed to fetch study area');
  return res.json();
}

export async function fetchIntersections(): Promise<IntersectionAsset[]> {
  const res = await fetch(`${API_BASE}/assets/intersections`);
  if (!res.ok) throw new Error('Failed to fetch intersections');
  return res.json();
}

export async function fetchRoadSegments(): Promise<RoadSegmentAsset[]> {
  const res = await fetch(`${API_BASE}/assets/segments`);
  if (!res.ok) throw new Error('Failed to fetch road segments');
  return res.json();
}

export async function fetchSensors(): Promise<TrafficSensorAsset[]> {
  const res = await fetch(`${API_BASE}/assets/sensors`);
  if (!res.ok) throw new Error('Failed to fetch sensors');
  return res.json();
}

export async function fetchEnergyEntities(): Promise<BuildingAsset[]> {
  const res = await fetch(`${API_BASE}/assets/energy`);
  if (!res.ok) throw new Error('Failed to fetch energy entities');
  return res.json();
}

export async function fetchCurrentState(): Promise<EntityCurrentState[]> {
  try {
    const res = await fetch(`${API_BASE}/state/current`);
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export async function fetchHistoricalSnapshot(minutesAgo: number): Promise<EntityCurrentState[]> {
  try {
    const res = await fetch(`${API_BASE}/state/snapshot?minutes_ago=${minutesAgo}`);
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


export async function fetchScenarioTemplates(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/scenarios/templates`);
  if (!res.ok) throw new Error('Failed to fetch scenario templates');
  return res.json();
}

export async function runScenario(params: {
  templateId: string;
  greenExtensionSec: number;
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
  const res = await fetch(`${API_BASE}/recommendations${query}`);
  if (!res.ok) throw new Error('Failed to fetch advisory recommendations');
  return res.json();
}

export async function fetchAdvisorySummary(): Promise<AdvisorySummary> {
  const res = await fetch(`${API_BASE}/recommendations/summary`);
  if (!res.ok) throw new Error('Failed to fetch advisory summary');
  return res.json();
}

export async function fetchRecommendationDetail(recId: string): Promise<AdvisoryRecommendation> {
  const res = await fetch(`${API_BASE}/recommendations/${recId}`);
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

