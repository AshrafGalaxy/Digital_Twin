"""
assets.py

Endpoints for querying static corridor assets: intersections, road segments,
sensors, and representative building zones.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/assets", tags=["Corridor Assets"])

CORRIDOR_ASSETS_PATH = Path("data/samples/corridor_assets.json")
CORRIDOR_ASSETS_FALLBACK = Path("../data/samples/corridor_assets.json")
SENSOR_REGISTRY_PATH = Path("data/samples/sensor_registry.json")
SENSOR_REGISTRY_FALLBACK = Path("../data/samples/sensor_registry.json")
ENERGY_ASSETS_PATH = Path("data/samples/energy_assets.json")
ENERGY_ASSETS_FALLBACK = Path("../data/samples/energy_assets.json")

def _load_json_file(primary: Path, fallback: Path) -> Dict[str, Any]:
    path = primary if primary.exists() else fallback
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Asset file {primary.name} not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@router.get("/intersections", response_model=List[Dict[str, Any]])
async def get_intersections():
    data = _load_json_file(CORRIDOR_ASSETS_PATH, CORRIDOR_ASSETS_FALLBACK)
    return data.get("intersections", [])

@router.get("/segments", response_model=List[Dict[str, Any]])
async def get_road_segments():
    data = _load_json_file(CORRIDOR_ASSETS_PATH, CORRIDOR_ASSETS_FALLBACK)
    return data.get("roadSegments", [])

@router.get("/sensors", response_model=List[Dict[str, Any]])
async def get_sensors():
    data = _load_json_file(SENSOR_REGISTRY_PATH, SENSOR_REGISTRY_FALLBACK)
    return data.get("sensors", [])

@router.get("/energy", response_model=List[Dict[str, Any]])
async def get_energy_entities():
    data = _load_json_file(ENERGY_ASSETS_PATH, ENERGY_ASSETS_FALLBACK)
    return data.get("entities", [])
