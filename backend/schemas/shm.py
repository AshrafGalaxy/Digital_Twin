"""
shm.py

Pydantic schemas and physical bounds validators for Structural Health Monitoring (SHM)
telemetry, bridge strain/vibration metrics, and dynamic vehicle axle impact loads (TASK-07 / Section 10.1).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from backend.core.constants import (
    SHM_HCV_AXLE_LIMIT_TONNES,
    SHM_PPV_HARD_MAX_MMS,
    SHM_PPV_MAX_MMS,
    SHM_PPV_MIN_MMS,
    SHM_RESONANT_DRIFT_THRESHOLD_PCT,
    SHM_STRAIN_MAX_MICROSTRAIN,
    SHM_STRAIN_MIN_MICROSTRAIN,
    SHM_STRAIN_YIELD_ALERT,
    SourceMode,
    StructuralIntegrityStatus,
)


class SHMReadingValue(BaseModel):
    value: float
    unit: str
    qualityScore: float = Field(default=1.0, ge=0.0, le=1.0)


class ResonantFreqReading(BaseModel):
    value: float = Field(..., gt=0.0, description="Measured fundamental resonant frequency in Hz")
    baselineHz: float = Field(..., gt=0.0, description="Span baseline natural frequency in Hz")
    driftPct: float = Field(..., description="Stiffness degradation drift percentage: ((f0 - baseline) / baseline) * 100")


class SHMTelemetryPayload(BaseModel):
    structureId: str = Field(..., min_length=3, description="Canonical infrastructure structure URN/ID")
    structureName: Optional[str] = Field(default=None, description="Human readable name of flyover/bridge")
    spanId: str = Field(..., min_length=2, description="Specific bridge span or pier identifier")
    sensorId: Optional[str] = Field(default="SENSOR-SHM-01", description="Sensor station or gauge cluster ID")
    observedAt: datetime = Field(..., description="ISO 8601 observation timestamp")
    vibrationPPV: SHMReadingValue = Field(..., description="Peak Particle Velocity vibration metric in mm/s")
    strain: SHMReadingValue = Field(..., description="Microstrain along tension flanges in microstrain")
    resonantFreqHz: ResonantFreqReading = Field(..., description="Span natural frequency and drift metrics")
    ambientTempC: float = Field(..., ge=-20.0, le=70.0, description="Ambient structural temperature in Celsius")
    hcvAxleLoadTonnes: Optional[float] = Field(default=None, ge=0.0, description="Weigh-in-Motion detected axle load in tonnes")
    integrityStatus: Optional[str] = Field(default=StructuralIntegrityStatus.NOMINAL.value, description="Status evaluation")
    provenance: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {"sourceMode": SourceMode.LIVE.value, "sensorType": "FBG_OPTICAL_PIEZO"}
    )

    @field_validator("vibrationPPV")
    @classmethod
    def validate_vibration(cls, v: SHMReadingValue) -> SHMReadingValue:
        if v.value < SHM_PPV_MIN_MMS or v.value > SHM_PPV_HARD_MAX_MMS:
            raise ValueError(
                f"Peak Particle Velocity {v.value} mm/s violates physical bounds [{SHM_PPV_MIN_MMS}, {SHM_PPV_HARD_MAX_MMS}]"
            )
        return v

    @field_validator("strain")
    @classmethod
    def validate_strain(cls, v: SHMReadingValue) -> SHMReadingValue:
        if v.value < SHM_STRAIN_MIN_MICROSTRAIN or v.value > SHM_STRAIN_MAX_MICROSTRAIN:
            raise ValueError(
                f"Strain reading {v.value} microstrain violates physical bounds [{SHM_STRAIN_MIN_MICROSTRAIN}, {SHM_STRAIN_MAX_MICROSTRAIN}]"
            )
        return v


class SHMTelemetryRecord(BaseModel):
    id: Optional[int] = None
    structureId: str
    structureName: Optional[str] = None
    spanId: str
    sensorId: str
    observedAt: str
    vibrationPpvMms: float
    strainMicrostrain: float
    resonantFreqHz: float
    resonantBaselineHz: float
    resonantDriftPct: float
    temperatureCelsius: float
    hcvAxleLoadTonnes: Optional[float] = None
    integrityStatus: str
    sourceMode: str
    qualityScore: float
    provenanceMetadata: Optional[Dict[str, Any]] = None


class SHMStructureSummary(BaseModel):
    structureId: str
    structureName: str
    totalSpans: int
    sensorCount: int
    latestStatus: str
    lastObservedAt: Optional[str] = None
    peakVibrationMms: float
    peakStrainMicrostrain: float
    resonantFrequencyHz: float
    resonantDriftPct: float


class SHMStructureStatus(BaseModel):
    structureId: str
    structureName: str
    spanId: str
    integrityStatus: str
    isFatigueAlert: bool
    isOverloadAlert: bool
    activeAlerts: List[str]
    currentMetrics: Dict[str, Any]
    safetyThresholds: Dict[str, Any]
    lastUpdated: str

