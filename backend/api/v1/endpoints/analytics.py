"""
analytics.py

Continuous aggregates and analytical rollup endpoints for the Digital Twin Platform (P4-B).
Provides performant 15-minute rolling aggregations of traffic observations across the corridor.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.services.continuous_aggregator import continuous_aggregator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class TrafficRollupRecord(BaseModel):
    bucket15m: str = Field(..., description="ISO timestamp of the 15-minute window bucket")
    segmentId: str = Field(..., description="URN of the road segment")
    sampleCount: int = Field(..., description="Number of raw observations in this bucket")
    avgSpeedKmh: float = Field(..., description="Average vehicle speed (km/h)")
    p85SpeedKmh: float = Field(..., description="85th percentile speed (km/h)")
    totalFlowVeh: float = Field(..., description="Total or hourly vehicle flow rate")
    avgOccupancyPercent: float = Field(..., description="Average road occupancy percentage")
    avgQueueLengthMeters: float = Field(..., description="Average queue length in meters")
    maxQueueLengthMeters: float = Field(..., description="Peak queue length in meters")
    avgCongestionIndex: float = Field(..., description="Congestion index (0.0 to 1.0)")


class TrafficRollupsResponse(BaseModel):
    totalRecords: int
    segmentId: Optional[str] = None
    hoursAgo: int
    rollups: List[TrafficRollupRecord]


class RollupComputeResponse(BaseModel):
    status: str
    rowsAffected: int
    hoursBack: int


@router.get("/rollups/traffic", response_model=TrafficRollupsResponse)
async def get_traffic_rollups(
    segment_id: Optional[str] = Query(None, description="Filter by RoadSegment URN"),
    hours_ago: int = Query(12, ge=1, le=168, description="History window in hours"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    session: AsyncSession = Depends(get_db)
):
    """
    Retrieves materialized 15-minute rolling continuous aggregates for corridor traffic.
    Returns speed, flow, occupancy, and queue metrics aggregated at 900-second intervals.
    """
    records = await continuous_aggregator.get_traffic_rollups(
        session=session,
        segment_id=segment_id,
        hours_ago=hours_ago,
        limit=limit
    )
    return TrafficRollupsResponse(
        totalRecords=len(records),
        segmentId=segment_id,
        hoursAgo=hours_ago,
        rollups=records
    )


@router.post("/rollups/compute", response_model=RollupComputeResponse)
async def compute_traffic_rollups(
    hours_back: int = Query(24, ge=1, le=168, description="Lookback window in hours"),
    session: AsyncSession = Depends(get_db)
):
    """
    Forces an immediate computation and materialization pass of 15-minute continuous aggregates
    from raw traffic observations in the database.
    """
    rows = await continuous_aggregator.compute_and_materialize_rollups(session=session, hours_back=hours_back)
    return RollupComputeResponse(
        status="COMPUTED",
        rowsAffected=rows,
        hoursBack=hours_back
    )
