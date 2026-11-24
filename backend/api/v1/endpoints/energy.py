from backend.api.v1.endpoints.auth import bind_dual_control, require_operational_officer
"""
energy.py

REST API endpoints for the Canonical Electrical Network Topology & Multi-Asset Telemetry Engine (Energy TASK-01).
Provides electrical single-line graph hierarchy, live 3-phase AC power metrics,
and corridor-wide microgrid power flow analytics.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.schemas.energy_advisory import (
    AdvisoryStatus,
    AuthorizeEnergyAdvisoryRequest,
    EnergyAdvisoryDossier,
    EnergyDispatchWorkOrder,
    EnergyOfficerCredentials,
)
from backend.services.bess_optimizer import (
    BessOptimizationRequest,
    BessOptimizationResult,
    bess_optimizer,
)
from backend.services.building_thermal_service import (
    PrecoolingSimulationRequest,
    PrecoolingSimulationResult,
    SimulationStepRequest,
    ThermalState,
    ThermalZoneConfig,
    building_thermal_service,
)
from backend.services.energy_advisory_service import energy_advisory_service
from backend.services.energy_topology_service import energy_topology_service
from backend.services.grid_safety_gateway import (
    CandidateDispatchRequest,
    GridSafetyGateway,
    GridSafetyInterlockResult,
    HeartbeatPingRequest,
    ModbusRegisterMap,
    OpenADREventPayload,
    grid_safety_gateway,
)
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
    pccGridImportKw: Optional[float] = None
    solarGenerationKw: float
    bessNetPowerKw: float
    facilityTotalLoadKw: float
    technicalLossesKw: float
    powerBalanceResidualKw: float
    residualShare: float
    residualShareThreshold: float
    gridMeterStatus: str
    maxFeederLoadingRatio: float
    criticalFeederId: Optional[str] = None
    thermalAlertStatus: str
    feeders: List[FeederThermalMarginModel]
    provenance: Dict[str, Any]


def _raise_power_balance_error(exc: Exception, action: str) -> None:
    if isinstance(exc, LookupError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No substation is registered for this identifier",
        ) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    logger.error("%s: %s", action, exc)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"{action}: {str(exc)}",
    ) from exc


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
async def trigger_telemetry_tick(
    session: AsyncSession = Depends(get_db),
    _officer: Dict[str, Any] = Depends(require_operational_officer)
):
    """
    Manually triggers a simulated 3-phase AC telemetry tick across all canonical microgrid assets.
    Requires operational officer credentials (TASK-10 / BUG-22).
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
        _raise_power_balance_error(e, "Failed to calculate power balance")


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
        _raise_power_balance_error(e, "Failed to record power balance snapshot")


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
        _raise_power_balance_error(e, "Failed to query feeder thermal margins")


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
    session: AsyncSession = Depends(get_db),
    officer: Dict[str, Any] = Depends(require_operational_officer)
):
    primary, concurring = bind_dual_control(officer, request.concurringToken)
    request.primarySubject = primary["sub"]
    request.concurringSubject = concurring["sub"]
    request.primaryOfficer = EnergyOfficerCredentials(
        officerName=primary["name"],
        badgeId=primary["badge"],
        department=primary["department"] or "Municipal Utilities & Commercial Grid",
    )
    request.concurringOfficer = EnergyOfficerCredentials(
        officerName=concurring["name"],
        badgeId=concurring["badge"],
        department=concurring["department"] or "Municipal Utilities & Commercial Grid",
    )
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


@router.post("/optimize-bess", response_model=BessOptimizationResult)
@router.post("/bess/optimize", response_model=BessOptimizationResult)
async def optimize_bess_schedule(
    request: BessOptimizationRequest,
) -> BessOptimizationResult:
    """
    Computes a 24-hour convex Linear Program (LP) optimization schedule for BESS battery arbitrage
    and peak demand shaving under Time-of-Use tariffs and monthly peak penalty constraints.
    Returns optimal hourly dispatch setpoints, projected financial savings, peak shaving reduction,
    governance non-actuation notice, and calculation provenance.
    """
    if request.custom_load_profile_kw is not None and len(request.custom_load_profile_kw) != 24:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="customLoadProfileKw must contain exactly 24 hourly floating point values.",
        )
    if request.custom_solar_profile_kw is not None and len(request.custom_solar_profile_kw) != 24:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="customSolarProfileKw must contain exactly 24 hourly floating point values.",
        )
    if request.custom_tariff_profile_inr is not None and len(request.custom_tariff_profile_inr) != 24:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="customTariffProfileInr must contain exactly 24 hourly floating point values.",
        )

    try:
        result = bess_optimizer.optimize_24h_schedule(
            facility_id=request.facility_id,
            target_schedule_date=request.target_schedule_date,
            initial_soc_pct=request.initial_soc_pct,
            custom_load_profile_kw=request.custom_load_profile_kw,
            custom_solar_profile_kw=request.custom_solar_profile_kw,
            contract_demand_ceiling_kw=request.contract_demand_ceiling_kw,
            demand_penalty_rate_inr=request.demand_penalty_rate_inr,
            custom_tariff_profile_inr=request.custom_tariff_profile_inr,
            capacity_kwh=request.capacity_kwh,
        )
        return BessOptimizationResult(**result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        logger.error("BESS optimization solver failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BESS optimization solver failed: {str(exc)}",
        ) from exc
    except Exception as exc:
        logger.error("Failed to execute BESS 24h schedule optimization: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute BESS optimization: {str(exc)}",
        ) from exc


@router.get("/bess/schedule", response_model=BessOptimizationResult)
@router.get("/bess-schedule", response_model=BessOptimizationResult)
async def get_active_bess_schedule(
    facility_id: Optional[str] = Query(None, description="Target facility entity identifier"),
    facilityId: Optional[str] = Query(None, description="Target facility entity identifier camelCase alias"),
) -> BessOptimizationResult:
    """
    Retrieves active 24-hour BESS battery arbitrage and peak shaving schedule for the requested facility.
    If no active schedule is cached, automatically generates an advisory optimization schedule.
    """
    target_facility_id = facility_id or facilityId or "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01"
    try:
        schedule = bess_optimizer.get_active_schedule(facility_id=target_facility_id, auto_generate=True)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Active BESS optimization schedule for facility '{target_facility_id}' not found.",
            )
        return BessOptimizationResult(**schedule)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to query active BESS schedule for %s: %s", target_facility_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query active BESS schedule: {str(exc)}",
        ) from exc


# ---------------------------------------------------------------------------
# Grid Safety Interlocks & OpenADR / Modbus Failsafe Dispatch Gateway (ENERGY-07)
# ---------------------------------------------------------------------------


class HeartbeatPingResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str = Field(default="HEARTBEAT_ACKNOWLEDGED", description="Heartbeat acknowledgement status")
    sender_id: str = Field(..., alias="senderId", description="Actuator or controller sender identifier")
    heartbeat_timestamp: str = Field(..., alias="heartbeatTimestamp", description="Timestamp of registered heartbeat in ISO 8601 format")
    watchdog_counter: int = Field(..., alias="watchdogCounter", description="Monotonic watchdog tick counter")
    failsafe_active: bool = Field(..., alias="failsafeActive", description="Whether failsafe mode is active")
    timeout_limit_seconds: float = Field(default=60.0, alias="timeoutLimitSeconds", description="Watchdog timeout limit in seconds")


class ModbusDispatchResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    setpoint_high: int = Field(..., alias="setpointHigh", ge=0, le=65535, description="Register 40001: Setpoint High Word")
    setpoint_low: int = Field(..., alias="setpointLow", ge=0, le=65535, description="Register 40002: Setpoint Low Word")
    control_mode: int = Field(..., alias="controlMode", ge=0, le=3, description="Register 40003: Control Mode (0=Standby, 1=Charge, 2=Discharge, 3=Failsafe)")
    interlock_bitmask: int = Field(..., alias="interlockBitmask", ge=0, le=15, description="Register 40004: Interlock Bitmask (bit 0=volt, 1=ramp, 2=soc, 3=heartbeat)")
    watchdog_counter: int = Field(..., alias="watchdogCounter", ge=0, le=65535, description="Register 40005: Watchdog Counter")
    raw_registers: Dict[str, int] = Field(default_factory=dict, alias="rawRegisters")
    named_registers: Dict[str, int] = Field(default_factory=dict, alias="namedRegisters")
    register_list: List[int] = Field(default_factory=list, alias="registerList")
    is_safe: bool = Field(default=True, alias="isSafe")
    action_taken: str = Field(default="APPROVED", alias="actionTaken")
    governance_notice: str = Field(
        default="Advisory decision support only. Local BMS and protection relays remain authoritative.",
        alias="governanceNotice",
    )


class GatewayStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    gateway_operational: bool = Field(..., alias="gatewayOperational")
    current_setpoint_kw: float = Field(..., alias="currentSetpointKw")
    current_control_mode: int = Field(..., alias="currentControlMode")
    current_control_mode_label: str = Field(..., alias="currentControlModeLabel")
    failsafe_active: bool = Field(..., alias="failsafeActive")
    last_heartbeat_timestamp: str = Field(..., alias="lastHeartbeatTimestamp")
    last_heartbeat_sender: str = Field(..., alias="lastHeartbeatSender")
    heartbeat_age_seconds: float = Field(..., alias="heartbeatAgeSeconds")
    heartbeat_timeout_limit_seconds: float = Field(default=60.0, alias="heartbeatTimeoutLimitSeconds")
    watchdog_counter: int = Field(..., alias="watchdogCounter")
    nominal_voltage_v: float = Field(default=415.0, alias="nominalVoltageV")
    voltage_operating_envelope_v: List[float] = Field(default_factory=lambda: [390.1, 439.9], alias="voltageOperatingEnvelopeV")
    ramp_rate_slew_limit_pct_per_min: float = Field(default=10.0, alias="rampRateSlewLimitPctPerMin")
    deadband_threshold_kw: float = Field(default=15.0, alias="deadbandThresholdKw")
    statistics: Dict[str, int] = Field(default_factory=dict)
    governance_notice: str = Field(
        default="Advisory decision support only. Local BMS remains authoritative.",
        alias="governanceNotice",
    )


@router.post("/dispatch/validate-safety", response_model=GridSafetyInterlockResult)
@router.post("/dispatch/validate", response_model=GridSafetyInterlockResult)
async def validate_dispatch_safety(
    request: CandidateDispatchRequest = Body(default_factory=CandidateDispatchRequest),
) -> GridSafetyInterlockResult:
    """
    Validates candidate dispatch setpoint against the 4 physical grid safety interlocks:
    1. Under/over-voltage lockout: 0.94 * V_nom <= V_line <= 1.06 * V_nom (390.1V to 439.9V for 415V nominal).
    2. Ramp-rate slew throttling: |delta_P / delta_t| <= 0.10 * P_rated (kW/min) (e.g. max 200 kW/min for 2000 kW BESS).
    3. Dead-band thresholding: suppress dispatch if |delta_P_shave| < 15.0 kW.
    4. Communication loss fallback: t_now - t_heartbeat > 60.0s triggers COMMUNICATION_LOST_FAILSAFE.
    Returns interlock verification status, approved power setpoint, control mode, Register 40004 bitmask, and provenance.
    """
    try:
        return grid_safety_gateway.validate_safety(request=request)
    except Exception as exc:
        logger.error("Failed to validate dispatch safety: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate dispatch safety: {str(exc)}",
        ) from exc


@router.post("/dispatch/serialize-openadr", response_model=OpenADREventPayload)
async def serialize_openadr_dispatch(
    request: CandidateDispatchRequest = Body(default_factory=CandidateDispatchRequest),
) -> OpenADREventPayload:
    """
    Validates candidate dispatch setpoint against the 4 physical grid safety interlocks
    and serializes the evaluated dispatch into canonical OpenADR 2.0b distributeEvent Profile B XML and JSON payloads.
    If approved, updates gateway telemetry state with the approved setpoint.
    """
    try:
        interlock_res = grid_safety_gateway.validate_safety(request=request)
        if interlock_res.is_safe and interlock_res.action_taken == "APPROVED":
            grid_safety_gateway.apply_approved_dispatch(interlock_res)

        return grid_safety_gateway.serialize_openadr(
            interlock_result=interlock_res,
            event_id=request.event_id,
            target_id=request.target_id or request.facility_id,
            resource_id=request.resource_id,
            duration=request.duration or "PT1H",
        )
    except Exception as exc:
        logger.error("Failed to serialize OpenADR dispatch: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serialize OpenADR dispatch: {str(exc)}",
        ) from exc


@router.post("/dispatch/serialize-modbus", response_model=ModbusDispatchResponse)
async def serialize_modbus_dispatch(
    request: CandidateDispatchRequest = Body(default_factory=CandidateDispatchRequest),
) -> ModbusDispatchResponse:
    """
    Validates candidate dispatch setpoint against the 4 physical grid safety interlocks
    and serializes the evaluated dispatch into Modbus TCP holding registers (Registers 40001 to 40005).
    If approved, updates gateway telemetry state with the approved setpoint.
    """
    try:
        interlock_res = grid_safety_gateway.validate_safety(request=request)
        if interlock_res.is_safe and interlock_res.action_taken == "APPROVED":
            grid_safety_gateway.apply_approved_dispatch(interlock_res)

        modbus_map = grid_safety_gateway.serialize_modbus(interlock_result=interlock_res)
        raw_regs = {str(k): v for k, v in modbus_map.raw_registers.items()}

        return ModbusDispatchResponse(
            setpointHigh=modbus_map.setpoint_high,
            setpointLow=modbus_map.setpoint_low,
            controlMode=modbus_map.control_mode,
            interlockBitmask=modbus_map.interlock_bitmask,
            watchdogCounter=modbus_map.watchdog_counter,
            rawRegisters=raw_regs,
            namedRegisters=modbus_map.named_registers,
            registerList=modbus_map.to_register_list(),
            isSafe=interlock_res.is_safe,
            actionTaken=interlock_res.action_taken,
        )
    except Exception as exc:
        logger.error("Failed to serialize Modbus dispatch: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serialize Modbus dispatch: {str(exc)}",
        ) from exc


@router.post("/dispatch/heartbeat", response_model=HeartbeatPingResponse)
async def register_actuator_heartbeat(
    request: Optional[HeartbeatPingRequest] = Body(default=None),
) -> HeartbeatPingResponse:
    """
    Registers an actuator, SCADA client, or BMS keepalive ping to reset the 60-second fallback timer.
    Increments the monotonic watchdog tick counter and clears communication loss failsafe status.
    """
    try:
        sender_id = request.sender_id if (request and request.sender_id) else "BMS-LOCAL-ACTUATOR-01"
        ts = request.timestamp if request else None
        result = grid_safety_gateway.record_heartbeat(sender_id=sender_id, timestamp=ts)
        return HeartbeatPingResponse(**result)
    except Exception as exc:
        logger.error("Failed to record actuator heartbeat: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record actuator heartbeat: {str(exc)}",
        ) from exc


@router.get("/dispatch/gateway-status", response_model=GatewayStatusResponse)
@router.get("/dispatch/status", response_model=GatewayStatusResponse)
async def get_grid_safety_gateway_status(
    current_time: Optional[float] = Query(None, alias="currentTime", description="Optional evaluation epoch timestamp in seconds"),
) -> GatewayStatusResponse:
    """
    Returns live operational health, heartbeat telemetry, watchdog counter, and failsafe status of the Grid Safety Gateway.
    """
    try:
        status_data = grid_safety_gateway.get_gateway_status(current_time=current_time)
        return GatewayStatusResponse(**status_data)
    except Exception as exc:
        logger.error("Failed to retrieve grid safety gateway status: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve grid safety gateway status: {str(exc)}",
        ) from exc


# =========================================================================
# Building Thermal Network & Occupancy Setback Endpoints (TASK-03 / ENERGY-03)
# =========================================================================

@router.get("/zones", response_model=List[Dict[str, Any]])
async def list_thermal_zones(session: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns list of all configured building thermal zones with current temperatures,
    occupancy, setback status, and ASHRAE 55 compliance indicators.
    """
    try:
        return await building_thermal_service.get_all_thermal_zones(session)
    except Exception as exc:
        logger.error("Failed to list thermal zones: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list thermal zones: {str(exc)}",
        ) from exc


@router.get("/zones/{zone_id}/thermal-state", response_model=ThermalState)
async def get_zone_thermal_state(
    zone_id: str,
    session: AsyncSession = Depends(get_db),
) -> ThermalState:
    """
    Returns the physical 2R-2C parameters and instantaneous thermal state for a specific zone.
    """
    state = await building_thermal_service.get_latest_zone_state(zone_id, session)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal zone '{zone_id}' not found.",
        )
    return state


@router.post("/zones/{zone_id}/step", response_model=ThermalState)
async def step_zone_simulation(
    zone_id: str,
    request: SimulationStepRequest = Body(...),
    session: AsyncSession = Depends(get_db),
) -> ThermalState:
    """
    Advances the 2R-2C thermal simulation for a zone by dt_seconds, applying Runge-Kutta 4th-order (RK4)
    numerical integration, dynamic occupancy setback, and internal sensible heat gains.
    """
    next_state = await building_thermal_service.advance_zone_step(zone_id, request, session)
    if not next_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal zone '{zone_id}' not found.",
        )
    return next_state


@router.post("/zones/{zone_id}/simulate-precooling", response_model=PrecoolingSimulationResult)
async def simulate_zone_precooling(
    zone_id: str,
    request: PrecoolingSimulationRequest = Body(...),
    session: AsyncSession = Depends(get_db),
) -> PrecoolingSimulationResult:
    """
    Executes a 24-hour diurnal simulation comparing baseline operation against a pre-cooling strategy.
    Quantifies peak chiller demand reduction (kW) and electricity tariff savings (INR) while evaluating
    ASHRAE 55 statutory comfort compliance.
    """
    cfg = await building_thermal_service.get_zone_config(zone_id, session)
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thermal zone '{zone_id}' not found.",
        )
    return building_thermal_service.simulate_precooling_comparison(cfg, request)



