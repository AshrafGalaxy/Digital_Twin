"""
state.py

Endpoints for querying authoritative current twin state and historical telemetry.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db_session
from ....schemas.canonical import EntityCurrentStateResponse

router = APIRouter(prefix="/state", tags=["Twin State"])

@router.get("/current", response_model=List[EntityCurrentStateResponse])
async def get_current_state(
    entity_type: Optional[str] = Query(None, description="Filter by EntityType (RoadSegment, TrafficSensor, etc.)"),
    session: AsyncSession = Depends(get_db_session)
):
    query_str = """
        SELECT entity_id, entity_type, source_mode, observed_at, updated_at,
               metrics, quality_status, freshness_seconds
        FROM entity_current_state
    """
    params: Dict[str, Any] = {}
    if entity_type:
        query_str += " WHERE entity_type = :entity_type"
        params["entity_type"] = entity_type

    query_str += " ORDER BY entity_id ASC"
    
    try:
        result = await session.execute(text(query_str), params)
        rows = result.mappings().all()
        
        records = []
        now_utc = datetime.now(timezone.utc)
        for row in rows:
            observed_at = row["observed_at"]
            freshness = max(0.0, (now_utc - observed_at).total_seconds())
            
            raw_metrics = row["metrics"]
            metrics_dict = json.loads(raw_metrics) if isinstance(raw_metrics, str) else (raw_metrics or {})
            
            records.append(EntityCurrentStateResponse(
                entityId=row["entity_id"],
                entityType=row["entity_type"],
                sourceMode=row["source_mode"],
                observedAt=observed_at,
                updatedAt=row["updated_at"],
                metrics=metrics_dict,
                qualityStatus=row["quality_status"],
                freshnessSeconds=round(freshness, 1)
            ))
        return records
    except Exception:
        # If database table is not yet populated or offline, return empty list gracefully
        return []

@router.get("/history")
async def get_telemetry_history(
    segment_id: Optional[str] = Query(None, description="Road segment ID"),
    limit: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session)
):
    query_str = """
        SELECT observed_at, sensor_id, segment_id, source_mode,
               average_speed_kmh, vehicle_flow_per_hour, occupancy_percent,
               queue_length_meters, congestion_index, quality_flag
        FROM traffic_observations
    """
    params: Dict[str, Any] = {"limit": limit}
    if segment_id:
        query_str += " WHERE segment_id = :segment_id"
        params["segment_id"] = segment_id
        
    query_str += " ORDER BY observed_at DESC LIMIT :limit"
    
    try:
        result = await session.execute(text(query_str), params)
        return [dict(row) for row in result.mappings().all()]
    except Exception:
        return []
