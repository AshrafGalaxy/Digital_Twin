"""
study_area.py

Endpoints for querying the authoritative study-area boundary geometry.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/study-area", tags=["Study Area"])

STUDY_AREA_PATH = Path("data/study_area.geojson")
FALLBACK_PATH = Path("../data/study_area.geojson")

@router.get("", response_model=Dict[str, Any])
async def get_study_area_geojson():
    path = STUDY_AREA_PATH if STUDY_AREA_PATH.exists() else FALLBACK_PATH
    if not path.exists():
        raise HTTPException(status_code=404, detail="Study area GeoJSON not found on server")
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed reading study area file at %s: %s", path, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load study area geometry.")
