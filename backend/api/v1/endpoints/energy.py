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
from backend.schemas.energy_advisory import (
    AdvisoryStatus,
    AuthorizeEnergyAdvisoryRequest,
    EnergyAdvisoryDossier,
    EnergyDispatchWorkOrder
)
from backend.services.energy_advisory_service import energy_advisory_service
from backend.services.energy_topology_service import energy_topology_service
from backend.services.power_balance_service import power_balance_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/energy", tags=["Energy Analytics"])


class FeederThermalMarginModel(BaseModel):
    feederId: str
    name: str
    voltageKv: float
    currentAmps: float
    ratedCurrentAmps: float
    thermalLoadingRatio: float
    thermalLoadingPct: float
    status: str
    availableHeadroomKw: float
    activePowerKw: float
    reactivePowerKvar: float
    apparentPowerKva: float
    powerFactor: float
    cableLengthMeters: float
    conductorResistanceOhm: float
    branchLossKw: float


class PowerBalanceResponseModel(BaseModel):
    substationId: str
    timestamp: str
    pccGridImportKw: float
    solarGenerationKw: float
    bessNetPowerKw: float
    facilityTotalLoadKw: float
    technicalLossesKw: float
    powerBalanceResidualKw: float
    maxFeederLoadingRatio: float
    criticalFeederId: Optional[str] = None
    thermalAlertStatus: str
    feeders: List[FeederThermalMarginModel]
    provenance: Dict[str, Any]


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


@router.get("/power-balance", response_model=PowerBalanceResponseModel)
async def get_power_balance(
    substation_id: Optional[str] = Query(None, description="Substation / PCC node identifier"),
    session: AsyncSession = Depends(get_db)
):
    """
    Computes live electrical bus active and reactive power conservation and branch thermal margins:
    P_grid + P_pv + P_bess = P_loads + P_losses + residual.
    """
    try:
        return await power_balance_service.calculate_power_balance(
            substation_id=substation_id,
            session=session
        )
    except Exception as e:
        logger.error("Failed to compute electrical bus power balance: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate power balance: {str(e)}"
        )


@router.post("/power-balance/snapshot", response_model=PowerBalanceResponseModel)
async def create_power_balance_snapshot(
    substation_id: Optional[str] = Query(None, description="Substation / PCC node identifier"),
    session: AsyncSession = Depends(get_db)
):
    """
    Calculates power balance and persists an authoritative snapshot to Table 34 (energy_power_balance_history).
    """
    try:
        return await power_balance_service.record_power_balance_snapshot(
            substation_id=substation_id,
            session=session
        )
    except Exception as e:
        logger.error("Failed to record power balance snapshot: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record power balance snapshot: {str(e)}"
        )


@router.get("/feeders/thermal-margins", response_model=List[FeederThermalMarginModel])
async def get_feeder_thermal_margins(
    substation_id: Optional[str] = Query(None, description="Substation / PCC node identifier"),
    session: AsyncSession = Depends(get_db)
):
    """
    Retrieves distribution branch thermal ampacity loading margins, available kW headroom,
    and thermal alert statuses (NOMINAL, WARNING, CRITICAL_OVERLOAD_RISK).
    """
    try:
        return await power_balance_service.get_feeder_thermal_margins(
            substation_id=substation_id,
            session=session
        )
    except Exception as e:
        logger.error("Failed to retrieve feeder thermal margins: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query feeder thermal margins: {str(e)}"
        )


@router.get("/power-balance/history", response_model=List[Dict[str, Any]])
async def get_power_balance_history(
    substation_id: Optional[str] = Query(None, description="Substation / PCC node identifier"),
    limit: int = Query(50, ge=1, le=500, description="Max historical points to return"),
    session: AsyncSession = Depends(get_db)
):
    """
    Retrieves historical power balance snapshots and feeder loading metrics from Table 34.
    """
    try:
        return await power_balance_service.get_power_balance_history(
            substation_id=substation_id,
            limit=limit,
            session=session
        )
    except Exception as e:
        logger.error("Failed to retrieve power balance history: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query power balance history: {str(e)}"
        )


@router.get("/advisories", response_model=List[EnergyAdvisoryDossier])
async def list_energy_advisories(
    status_filter: Optional[AdvisoryStatus] = Query(None, alias="status", description="Filter by advisory status")
):
    """
    Returns active or historical energy demand-response advisory dossiers.
    """
    return energy_advisory_service.list_advisories(status=status_filter)


@router.get("/advisories/{advisory_id}", response_model=EnergyAdvisoryDossier)
async def get_energy_advisory_detail(advisory_id: str):
    """
    Retrieves complete demand-response advisory dossier with schedule and physical interlocks.
    """
    dossier = energy_advisory_service.get_advisory(advisory_id)
    if not dossier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Energy advisory dossier '{advisory_id}' not found."
        )
    return dossier


@router.post("/advisories/{advisory_id}/authorize", response_model=EnergyDispatchWorkOrder)
async def authorize_energy_advisory(
    advisory_id: str,
    request: AuthorizeEnergyAdvisoryRequest,
    session: AsyncSession = Depends(get_db)
):
    """
    Authorizes an energy demand-response advisory via dual-key operator sign-off.
    Generates a cryptographic SHA-256 tamper-evident hash, creates an official
    OpenADR 2.0b / Modbus dispatch ticket, and writes an immutable audit record
    to Table 29 (advisory_audit_log).
    """
    work_order = await energy_advisory_service.authorize_advisory(
        advisory_id=advisory_id,
        request=request,
        session=session
    )
    if not work_order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Energy advisory dossier '{advisory_id}' not found."
        )
    return work_order


@router.get("/advisories/{advisory_id}/dispatch-ticket", response_model=EnergyDispatchWorkOrder)
async def get_energy_dispatch_ticket(advisory_id: str):
    """
    Retrieves the generated OpenADR 2.0b / Modbus municipal dispatch ticket for an advisory.
    """
    ticket = energy_advisory_service.get_dispatch_ticket(advisory_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No dispatch ticket issued for energy advisory '{advisory_id}'."
        )
    return ticket

