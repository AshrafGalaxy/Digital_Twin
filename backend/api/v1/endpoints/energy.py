"""
energy.py

REST API endpoints for the Canonical Electrical Network Topology & Multi-Asset Telemetry Engine (Energy TASK-01).
Provides electrical single-line graph hierarchy, live 3-phase AC power metrics,
and corridor-wide microgrid power flow analytics.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.services.energy_topology_service import energy_topology_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/energy", tags=["Energy Analytics"])


class EnergyTelemetryModel(BaseModel):
    assetId: str = Field(..., description="Unique node/asset identifier")
    name: Optional[str] = Field(None, description="Human readable asset name")
    nodeType: Optional[str] = Field(None, description="Asset classification")
    nominalVoltageKv: Optional[float] = None
    ratedCapacityKva: Optional[float] = None
    ratedCurrentAmps: Optional[float] = None
    loadingPct: Optional[float] = None
    activePowerKw: float = Field(..., description="Active Power P in kW")
    reactivePowerKvar: float = Field(..., description="Reactive Power Q in kVAR")
    apparentPowerKva: float = Field(..., description="Apparent Power S in kVA")
    powerFactor: float = Field(..., description="Power Factor PF (0.0 to 1.0)")
    voltageV: float = Field(..., description="Line-to-Line Voltage in Volts")
    currentA: float = Field(..., description="Phase Line Current in Amperes")
    frequencyHz: float = Field(50.00, description="Grid Frequency in Hz")
    voltageUnbalancePct: float = Field(0.50, description="Voltage unbalance percentage")
    currentUnbalancePct: float = Field(1.20, description="Current unbalance percentage")
    deviceMetrics: Dict[str, Any] = Field(default_factory=dict, description="Asset specific parameters")
    observedAt: str = Field(..., description="Observation ISO timestamp")
    sourceMode: str = Field("SIMULATION", description="Data provenance mode")
    qualityStatus: str = Field("VALID", description="Data quality classification")


class MicrogridSummaryModel(BaseModel):
    gridImportKw: float = Field(..., description="Net active power imported from the primary grid")
    solarGenerationKw: float = Field(..., description="Total rooftop solar PV generation")
    bessPowerKw: float = Field(..., description="Net battery power (negative = charging, positive = discharging)")
    bessStateOfChargePct: float = Field(..., description="Battery state of charge percentage")
    evChargingLoadKw: float = Field(..., description="Total EV fast-charging power")
    buildingLoadKw: float = Field(..., description="Total commercial building demand")
    netPowerFactor: float = Field(..., description="Corridor net power factor at PCC")
    renewableSelfConsumptionPct: float = Field(..., description="Solar self-consumption percentage")
    carbonOffsetKgPerHour: float = Field(..., description="Estimated carbon offset (kg CO2 / hr)")
    sourceMode: str = Field("SIMULATION")
    qualityStatus: str = Field("VALID")
    observedAt: str = Field(..., description="Summary calculation timestamp")


@router.get("/topology", response_model=Dict[str, Any])
async def get_energy_topology(session: AsyncSession = Depends(get_db)):
    """
    Retrieves the hierarchical single-line electrical network tree:
    Primary Substation -> 11kV Feeders -> Solar PV, BESS, Building Loads, EV Charging Hubs.
    """
    try:
        return await energy_topology_service.get_topology_tree(session=session)
    except Exception as e:
        logger.error("Failed to retrieve energy topology: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query electrical network topology: {str(e)}"
        )


@router.get("/telemetry/live", response_model=List[EnergyTelemetryModel])
async def get_live_energy_telemetry(session: AsyncSession = Depends(get_db)):
    """
    Returns latest 3-phase AC telemetry across all canonical microgrid assets.
    """
    try:
        return await energy_topology_service.get_live_telemetry(session=session)
    except Exception as e:
        logger.error("Failed to retrieve live energy telemetry: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query live energy telemetry: {str(e)}"
        )


@router.get("/summary", response_model=MicrogridSummaryModel)
async def get_microgrid_summary(session: AsyncSession = Depends(get_db)):
    """
    Returns corridor-wide microgrid power balance KPIs and renewable self-consumption ratios.
    """
    try:
        return await energy_topology_service.get_microgrid_summary(session=session)
    except Exception as e:
        logger.error("Failed to compute microgrid summary: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate microgrid summary: {str(e)}"
        )


@router.get("/telemetry/history", response_model=List[Dict[str, Any]])
async def get_asset_telemetry_history(
    asset_id: str = Query(..., description="Node/Asset identifier"),
    limit: int = Query(50, ge=1, le=500, description="Max historical points to return"),
    session: AsyncSession = Depends(get_db)
):
    """
    Retrieves historical 3-phase AC telemetry readings for a specific asset node.
    """
    try:
        res = await session.execute(
            text("""
                SELECT active_power_kw, reactive_power_kvar, apparent_power_kva,
                       power_factor, voltage_v, current_a, frequency_hz,
                       voltage_unbalance_pct, current_unbalance_pct,
                       device_metrics_json, observed_at, source_mode, quality_status
                FROM energy_asset_telemetry
                WHERE asset_id = :asset_id
                ORDER BY observed_at DESC
                LIMIT :limit
            """),
            {"asset_id": asset_id, "limit": limit}
        )
        points = []
        for r in res.fetchall():
            metrics_raw = r[9]
            metrics = json.loads(metrics_raw) if isinstance(metrics_raw, str) else (metrics_raw or {})
            obs_time = r[10].isoformat() if hasattr(r[10], "isoformat") else str(r[10])
            points.append({
                "assetId": asset_id,
                "activePowerKw": float(r[0]),
                "reactivePowerKvar": float(r[1]),
                "apparentPowerKva": float(r[2]),
                "powerFactor": float(r[3]),
                "voltageV": float(r[4]),
                "currentA": float(r[5]),
                "frequencyHz": float(r[6]),
                "voltageUnbalancePct": float(r[7]),
                "currentUnbalancePct": float(r[8]),
                "deviceMetrics": metrics,
                "observedAt": obs_time,
                "sourceMode": r[11],
                "qualityStatus": r[12]
            })
        return points
    except Exception as e:
        logger.error("Failed to retrieve asset telemetry history: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query telemetry history for {asset_id}: {str(e)}"
        )


@router.post("/telemetry/tick", response_model=List[Dict[str, Any]])
async def trigger_telemetry_tick(session: AsyncSession = Depends(get_db)):
    """
    Manually triggers a simulated 3-phase AC telemetry tick across all canonical microgrid assets.
    """
    try:
        records = await energy_topology_service.generate_telemetry_tick(session=session)
        return records
    except Exception as e:
        logger.error("Manual energy telemetry tick failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate telemetry tick: {str(e)}"
        )
