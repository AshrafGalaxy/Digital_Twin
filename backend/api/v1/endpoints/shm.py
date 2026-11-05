"""
shm.py

REST API endpoints for Critical Infrastructure Structural Health Monitoring (SHM) Telemetry (TASK-07 / Section 10.1).
Exposes bridge and flyover structural integrity status, strain/vibration telemetry,
resonant frequency drift evaluations, and Weigh-in-Motion dynamic axle impact alerts.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import get_current_user
from backend.core.database import get_db
from backend.schemas.shm import (
    SHMStructureStatus,
    SHMStructureSummary,
    SHMTelemetryPayload,
    SHMTelemetryRecord,
)
from backend.services.shm_service import shm_service

logger = logging.getLogger("digital_twin.api.shm")

router = APIRouter(prefix="/shm", tags=["Structural Health Monitoring"])


@router.get("/structures", response_model=List[SHMStructureSummary])
async def list_monitored_structures(
    session: AsyncSession = Depends(get_db),
) -> List[SHMStructureSummary]:
    """
    Lists all monitored bridges, flyovers, and viaducts with current health summaries.
    """
    try:
        return await shm_service.get_monitored_structures(session)
    except Exception as e:
        logger.error("Error retrieving monitored structures: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve structural assets: {str(e)}",
        )


@router.get("/structures/{structure_id}/status", response_model=SHMStructureStatus)
async def get_structure_status(
    structure_id: str,
    session: AsyncSession = Depends(get_db),
) -> SHMStructureStatus:
    """
    Retrieves real-time operational status, active fatigue/overload alarms,
    and safety envelope thresholds for a specific structural asset.
    """
    try:
        return await shm_service.get_structure_status(session, structure_id)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No observation is stored for this structure",
        )
    except Exception as e:
        logger.error("Error retrieving status for structure %s: %s", structure_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve status for structure {structure_id}: {str(e)}",
        )


@router.get(
    "/structures/{structure_id}/telemetry",
    response_model=List[SHMTelemetryRecord],
)
async def get_structure_telemetry_history(
    structure_id: str,
    limit: int = Query(50, ge=1, le=1000, description="Max historical records to return"),
    hours: Optional[float] = Query(None, gt=0, le=168, description="Filter records within last N hours"),
    session: AsyncSession = Depends(get_db),
) -> List[SHMTelemetryRecord]:
    """
    Retrieves historical vibration, strain, and resonant frequency observations for a structure.
    """
    try:
        return await shm_service.get_structure_history(
            session=session, structure_id=structure_id, limit=limit, hours=hours
        )
    except Exception as e:
        logger.error("Error retrieving telemetry history for %s: %s", structure_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve telemetry history for structure {structure_id}: {str(e)}",
        )


@router.post(
    "/telemetry",
    response_model=SHMTelemetryRecord,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_shm_telemetry(
    payload: SHMTelemetryPayload,
    session: AsyncSession = Depends(get_db),
    _officer: Any = Depends(get_current_user),
) -> SHMTelemetryRecord:
    """
    Ingests, validates, evaluates, and stores a new SHM telemetry reading from an on-structure sensor cluster.
    Enforces strict physical bounds and updates the real-time twin state.
    """
    try:
        return await shm_service.ingest_shm_payload(session, payload)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(val_err),
        )
    except Exception as e:
        logger.error("Error ingesting SHM telemetry payload: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest SHM telemetry: {str(e)}",
        )

