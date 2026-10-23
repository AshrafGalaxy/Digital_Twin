"""
energy_advisory.py

Pydantic schemas for Human-in-the-Loop Demand-Response Advisory Dossiers,
Physical Safety Interlocks, and Dual-Key Operator Dispatch Authorization (TASK-10 / GitHub #22).
Enforces strict traceability, read-only decision support, and cryptographic audit hashing.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AdvisoryStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    AUTHORIZED = "AUTHORIZED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class SafetyInterlocks(BaseModel):
    voltageCompliant: bool = Field(True, description="Feeder voltage within 415V +/- 6% statutory tolerance")
    voltageValueV: float = Field(409.8, description="Monitored line voltage in Volts")
    rampRateCompliant: bool = Field(True, description="Inverter slew ramp rate throttled <= 10%/min")
    rampRatePctPerMin: float = Field(8.0, description="Active inverter slew rate in %/min")
    socBounded: bool = Field(True, description="Battery state of charge satisfies SoC >= 20% floor")
    currentSocPct: float = Field(32.0, description="Active battery state of charge percentage")
    comfortPreserved: bool = Field(True, description="Zone indoor temperature setback satisfies ASHRAE 55 <= 25.5 deg C")
    projectedIndoorTempC: float = Field(24.2, description="Projected peak indoor temperature in deg C")


class DispatchScheduleSlot(BaseModel):
    timeSlot: str = Field(..., description="Interval label e.g. 18:30-19:00 IST")
    bessAction: str = Field(..., description="Battery action: CHARGE, DISCHARGE, or IDLE")
    bessKw: float = Field(..., description="Active battery power dispatch in kW")
    hvacSetbackDeltaC: float = Field(..., description="Thermostat temperature setback adjustment in deg C")


class EnergyAdvisoryDossier(BaseModel):
    advisoryId: str = Field(..., description="Unique advisory identifier e.g. ADVISORY-DR-20261023-001")
    facilityId: str = Field(..., description="Target facility entity ID")
    facilityName: str = Field(..., description="Human readable facility name")
    feederId: Optional[str] = Field(None, description="Associated distribution feeder ID")
    generatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: AdvisoryStatus = Field(default=AdvisoryStatus.PENDING_REVIEW)
    recommendedAction: str = Field(..., description="Actionable operational demand response recommendation")
    projectedSavingsInr: float = Field(..., description="Projected net electricity cost savings in INR")
    peakReductionKw: float = Field(..., description="Total peak electrical demand reduction in kW")
    batteryWearCycles: float = Field(..., description="Equivalent battery degradation wear in full cycles")
    avoidedCarbonKg: float = Field(..., description="Estimated avoided grid carbon emissions in kg CO2e")
    safetyChecks: SafetyInterlocks = Field(default_factory=SafetyInterlocks)
    schedule: List[DispatchScheduleSlot] = Field(default_factory=list)
    auditHash: Optional[str] = Field(None, description="SHA-256 tamper-evident digital signature")
    dispatchOrderId: Optional[str] = Field(None, description="Issued municipal dispatch ticket ID")
    authorizedBy: Optional[str] = None
    badgeId: Optional[str] = None
    shiftId: Optional[str] = None
    notes: Optional[str] = None
    governanceNotice: str = Field(
        default="Advisory decision support only. Emits an audited OpenADR / Modbus dispatch work order. Local BMS and BESS safety logic remains authoritative."
    )


class AuthorizeEnergyAdvisoryRequest(BaseModel):
    reviewer: str = Field(..., min_length=2, max_length=120, description="Authorizing operator name")
    badgeId: str = Field(..., min_length=2, max_length=64, description="Operator municipal badge identifier")
    shiftId: str = Field(default="SHIFT-EVENING-B", min_length=2, max_length=64, description="Operating duty shift")
    decision: AdvisoryStatus = Field(default=AdvisoryStatus.AUTHORIZED, description="Authorization decision: AUTHORIZED or REJECTED")
    notes: Optional[str] = Field(None, max_length=1000, description="Operational justification notes")


class EnergyDispatchWorkOrder(BaseModel):
    dispatchOrderId: str = Field(..., description="Unique dispatch ticket ID e.g. EDO-20261023-XXXX")
    advisoryId: str = Field(..., description="Referenced advisory ID")
    facilityId: str = Field(..., description="Target facility ID")
    facilityName: str = Field(..., description="Target facility name")
    authorizedBy: str = Field(..., description="Authorizing operator")
    badgeId: str = Field(..., description="Operator badge ID")
    shiftId: str = Field(..., description="Operating shift")
    issuedAt: datetime = Field(..., description="Authorization timestamp")
    decision: AdvisoryStatus = Field(..., description="Recorded decision")
    schedule: List[DispatchScheduleSlot] = Field(..., description="Authorized dispatch schedule")
    safetyChecks: SafetyInterlocks = Field(..., description="Validated safety interlocks")
    projectedSavingsInr: float = Field(..., description="Projected financial savings in INR")
    peakReductionKw: float = Field(..., description="Peak demand reduction in kW")
    avoidedCarbonKg: float = Field(..., description="Avoided carbon emissions in kg CO2e")
    tamperEvidentHash: str = Field(..., description="Cryptographic SHA-256 tamper-evident hash")
    openAdrPayload: Dict[str, Any] = Field(..., description="OpenADR 2.0b EiEvent payload structure")
    modbusRegisters: Dict[str, int] = Field(..., description="Standard Modbus register mapping for BMS")
    governanceDisclaimer: str = Field(
        default="Advisory decision support only. Emits an audited OpenADR / Modbus dispatch work order. Local BMS and BESS safety logic remains authoritative."
    )
