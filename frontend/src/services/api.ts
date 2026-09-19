import { EntityCurrentState, IntersectionAsset, RoadSegmentAsset, TrafficSensorAsset, BuildingAsset } from '../types/twin';

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
