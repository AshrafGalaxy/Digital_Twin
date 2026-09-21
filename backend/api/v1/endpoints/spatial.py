"""
spatial.py

FastAPI endpoints for the Spatial Fidelity Foundation (Phase 8A).
Exposes the versioned spatial registry, SUMO-to-PostGIS cross-references,
and 3D-ready GeoJSON layers for Cesium and MapLibre.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, Path

from backend.schemas.spatial import SpatialRegistryCatalog, SpatialEntityResolution
from backend.services.spatial_registry_service import spatial_service

router = APIRouter(prefix="/spatial", tags=["Spatial Registry & 3D Geometry"])


@router.get("/registry", response_model=SpatialRegistryCatalog)
async def get_spatial_registry():
    """
    Returns the complete, authoritative corridor spatial registry.
    Contains versioned mappings between PostGIS entities, SUMO edges/lanes/junctions,
    traffic signal controllers, building heights, and sensors.
    """
    return spatial_service.catalog


@router.get("/corridor-3d", response_model=Dict[str, Any])
async def get_corridor_3d_geojson():
    """
    Returns a unified 3D GeoJSON FeatureCollection structured for CesiumJS ingestion.
    Includes extruded building footprints with height/level attributes,
    road centerlines with lane counts, signal heads at stop lines, and sensor markers.
    """
    return spatial_service.get_corridor_3d_geojson()


@router.get("/layers/{layer_name}", response_model=Dict[str, Any])
async def get_spatial_layer(
    layer_name: str = Path(..., description="Target layer: buildings, roads, intersections, signals, sensors, study_area")
):
    """
    Returns a GeoJSON FeatureCollection filtered to a specific spatial layer.
    """
    valid_layers = {"buildings", "roads", "intersections", "signals", "sensors", "study_area"}
    norm_layer = layer_name.lower().strip()
    if norm_layer not in valid_layers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid layer '{layer_name}'. Valid layers are: {', '.join(sorted(valid_layers))}"
        )
    return spatial_service.get_layer_geojson(norm_layer)


@router.get("/resolve/{entity_id}", response_model=SpatialEntityResolution)
async def resolve_spatial_entity(
    entity_id: str = Path(..., description="Canonical URN or short-form ID of the entity")
):
    """
    Resolves any entity identifier to its PostGIS coordinates, equivalent SUMO ID,
    and associated spatial properties.
    """
    res = spatial_service.resolve_entity(entity_id)
    if not res.spatialFound:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found in spatial registry")
    return res


@router.get("/signals", response_model=Dict[str, Any])
async def get_signal_registry():
    """
    Returns the signal controller and signal group mapping specifications.
    """
    cat = spatial_service.catalog
    return {
        "registryVersion": cat.registryVersion,
        "totalControllers": len(cat.signalControllers),
        "controllers": [c.model_dump() for c in cat.signalControllers],
    }


@router.get("/buildings", response_model=Dict[str, Any])
async def get_building_registry():
    """
    Returns building footprint polygons, heights, levels, and energy zone associations.
    """
    cat = spatial_service.catalog
    return {
        "registryVersion": cat.registryVersion,
        "totalBuildings": len(cat.buildingZoneMappings),
        "buildings": [b.model_dump() for b in cat.buildingZoneMappings],
    }
