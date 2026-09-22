import {
  SpatialRegistryCatalog,
  Corridor3DFeatureCollection
} from '../types/spatial';

export async function fetchSpatialRegistry(): Promise<SpatialRegistryCatalog> {
  const res = await fetch('/api/v1/spatial/registry');
  if (!res.ok) {
    throw new Error(`Failed to fetch spatial registry: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchCorridor3DGeoJson(): Promise<Corridor3DFeatureCollection> {
  const res = await fetch('/api/v1/spatial/corridor-3d');
  if (!res.ok) {
    throw new Error(`Failed to fetch corridor 3D GeoJSON: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchSpatialLayer(layerName: string): Promise<Corridor3DFeatureCollection> {
  const res = await fetch(`/api/v1/spatial/layers/${layerName}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch spatial layer ${layerName}: ${res.status}`);
  }
  return res.json();
}

export async function resolveSpatialEntity(entityId: string): Promise<any> {
  const res = await fetch(`/api/v1/spatial/resolve/${encodeURIComponent(entityId)}`);
  if (!res.ok) {
    throw new Error(`Failed to resolve spatial entity ${entityId}: ${res.status}`);
  }
  return res.json();
}
