"""
canonical.py

Canonical Pydantic schemas (NGSI-LD inspired) for events, state, forecasts,
and advisory recommendations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

try:
    from core.constants import (
        Direction,
        EntityType,
        QualityStatus,
        SourceMode,
        SPEED_MAX_KMH,
        SPEED_MIN_KMH,
        OCCUPANCY_MAX_PCT,
        OCCUPANCY_MIN_PCT
    )
except ImportError:
    from backend.core.constants import (
        Direction,
        EntityType,
        QualityStatus,
        SourceMode,
        SPEED_MAX_KMH,
        SPEED_MIN_KMH,
        OCCUPANCY_MAX_PCT,
        OCCUPANCY_MIN_PCT
    )

class BaseEntitySchema(BaseModel):
    id: str
    type: EntityType
    name: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class IntersectionSchema(BaseEntitySchema):
    type: EntityType = EntityType.INTERSECTION
    controlType: str = "SIGNALIZED"
    cycleTimeSec: int = 120
    phasesCount: int = 4
    coordinates: List[float] = Field(..., min_length=2, max_length=2)
    connectedSegments: List[str] = Field(default_factory=list)

class RoadSegmentSchema(BaseEntitySchema):
    type: EntityType = EntityType.ROAD_SEGMENT
    direction: Direction
    fromIntersection: Optional[str] = None
    toIntersection: Optional[str] = None
    lengthMeters: float
    laneCount: int = 3
    speedLimitKmh: float = 50.0
    freeFlowSpeedKmh: float = 45.0
    capacityVehPerHour: int = 3600
    osmHighway: str = "primary"
    coordinates: List[List[float]]

class TrafficSensorSchema(BaseEntitySchema):
    type: EntityType = EntityType.TRAFFIC_SENSOR
    linkedSegmentId: str
    direction: Direction
    sensorType: str = "INDUCTIVE_LOOP_EMULATION"
    supportedSourceModes: List[SourceMode] = Field(
        default_factory=lambda: [SourceMode.REPLAY, SourceMode.SIMULATION, SourceMode.LIVE]
    )
    coordinates: List[float]
    samplingIntervalSec: int = 60
    freshnessThresholdSec: int = 180

class BuildingZoneSchema(BaseEntitySchema):
    type: EntityType = EntityType.BUILDING
    category: str = "COMMERCIAL_RETAIL"
    grossFloorAreaSqm: float
    sanctionedLoadKva: Optional[float] = None
    contractDemandKw: Optional[float] = None
    coordinates: List[float]

# ==========================================
# Telemetry Ingestion Schemas
# ==========================================

class TrafficObservationEvent(BaseModel):
    observedAt: datetime
    sensorId: str
    segmentId: str
    sourceMode: SourceMode
    averageSpeedKmh: float = Field(..., ge=SPEED_MIN_KMH, le=SPEED_MAX_KMH)
    vehicleFlowPerHour: float = Field(..., ge=0.0)
    occupancyPercent: Optional[float] = Field(None, ge=OCCUPANCY_MIN_PCT, le=OCCUPANCY_MAX_PCT)
    queueLengthMeters: Optional[float] = Field(None, ge=0.0)
    congestionIndex: Optional[float] = Field(None, ge=0.0, le=1.0)
    qualityFlag: QualityStatus = QualityStatus.VALID

    @field_validator("observedAt")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

class EnergyObservationEvent(BaseModel):
    observedAt: datetime
    buildingId: str
    sourceMode: SourceMode
    activePowerKw: float = Field(..., ge=0.0)
    reactivePowerKvar: Optional[float] = None
    powerFactor: Optional[float] = Field(None, ge=0.0, le=1.0)
    qualityFlag: QualityStatus = QualityStatus.VALID

    @field_validator("observedAt")
    @classmethod
    def ensure_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

class EnvironmentObservationEvent(BaseModel):
    observedAt: datetime
    stationId: str
    sourceMode: SourceMode
    aqiValue: Optional[float] = Field(None, ge=0.0)
    pm25: Optional[float] = Field(None, ge=0.0)
    pm10: Optional[float] = Field(None, ge=0.0)
    temperatureC: Optional[float] = None
    relativeHumidityPct: Optional[float] = Field(None, ge=0.0, le=100.0)
    precipitationMm: Optional[float] = Field(None, ge=0.0)
    qualityFlag: QualityStatus = QualityStatus.VALID

# ==========================================
# Authoritative State & Forecast Schemas
# ==========================================

class EntityCurrentStateResponse(BaseModel):
    entityId: str
    entityType: str
    sourceMode: SourceMode
    observedAt: datetime
    updatedAt: datetime
    metrics: Dict[str, Any]
    qualityStatus: QualityStatus
    freshnessSeconds: float

class ForecastRecord(BaseModel):
    targetTimestamp: datetime
    entityId: str
    domain: str
    modelVersionId: str
    horizonMinutes: int
    sourceMode: SourceMode = SourceMode.PREDICTED
    predictedValue: float
    unit: str
    confidenceLower: Optional[float] = None
    confidenceUpper: Optional[float] = None
    inputQualityStatus: QualityStatus = QualityStatus.VALID

# ==========================================
# Scenario & Recommendation Schemas
# ==========================================

class ScenarioRunRecord(BaseModel):
    id: str
    templateId: str
    name: str
    status: str
    sourceMode: SourceMode = SourceMode.SIMULATION
    parameters: Dict[str, Any]
    kpis: Optional[Dict[str, Any]] = None

class AdvisoryRecommendationRecord(BaseModel):
    id: str
    generatedAt: datetime
    domain: str
    urgency: str = "MEDIUM"
    title: str
    rationale: str
    advisoryAction: str
    evidence: Dict[str, Any]
    humanApprovalRequired: bool = True
    reviewStatus: str = "PENDING"
