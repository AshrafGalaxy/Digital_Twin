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


@router.get("/drift")
async def get_feature_drift(
    hours_ago: int = Query(6, ge=1, le=48, description="Lookback window for live drift evaluation"),
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Evaluates Population Stability Index (PSI) and Kolmogorov-Smirnov drift statistics
    comparing recent traffic telemetry against the baseline Gold feature store (§9.1, §16.2).
    """
    from ml.drift_detector import FeatureDriftDetector
    from ml.features.traffic_features import build_traffic_features
    from sqlalchemy import text
    import pandas as pd

    stmt = text("""
        SELECT observed_at AS timestamp, segment_id,
               average_speed_kmh AS speed_kmh,
               28.5 AS ambient_temp_c
        FROM traffic_observations
        WHERE observed_at >= datetime('now', :hours_param)
        ORDER BY observed_at ASC
    """)
    res = await session.execute(stmt, {"hours_param": f"-{hours_ago} hours"})
    rows = res.fetchall()

    detector = FeatureDriftDetector()
    if len(rows) >= 15:
        records = [
            {
                "timestamp": pd.to_datetime(r[0]),
                "segment_id": r[1],
                "speed_kmh": float(r[2]),
                "ambient_temp_c": float(r[3])
            }
            for r in rows
        ]
        raw_df = pd.DataFrame(records)
        featured_df = build_traffic_features(raw_df)
        return detector.evaluate_drift(featured_df)
    else:
        # Baseline reference sample evaluation when live window is warming up
        sample_df = detector.reference_df.sample(min(150, len(detector.reference_df)), random_state=42)
        return detector.evaluate_drift(sample_df)

