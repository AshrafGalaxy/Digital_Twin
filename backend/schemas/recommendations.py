"""
recommendations.py

Pydantic schemas for Advisory Recommendations and Governance Review Workflow (D-10).
Enforces strict traceability to observed/predicted/scenario evidence and mandatory
human approval governance invariants.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.core.constants import SourceMode


class RecommendationDomain(str, Enum):
    TRAFFIC = "TRAFFIC"
    ENERGY = "ENERGY"
    ENVIRONMENT = "ENVIRONMENT"


class RecommendationSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class RecommendationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    DISMISSED = "DISMISSED"


class RecommendationEvidence(BaseModel):
    sourceMode: SourceMode = Field(..., description="Data class provenance: PREDICTED, REPLAY, or SIMULATION")
    metricName: str = Field(..., description="Target metric triggering rule (e.g. speed_kmh, demand_kw)")
    observedOrPredictedValue: float = Field(..., description="Quantitative trigger value")
    threshold: float = Field(..., description="Rule decision threshold violated")
    unit: str = Field(..., description="Unit of measurement")
    horizonMinutes: Optional[int] = Field(None, description="Forecast horizon if PREDICTED")
    modelVersion: Optional[str] = Field(None, description="Model ID generating evidence")
    scenarioId: Optional[str] = Field(None, description="SUMO scenario ID if SIMULATION")
    confidenceScore: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score or input completeness")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of evidence")


class AuditLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    previousStatus: RecommendationStatus
    newStatus: RecommendationStatus
    reviewer: str = Field(..., description="Authorized reviewer identity")
    notes: Optional[str] = Field(None, description="Review justification or action plan notes")


class ProposedParameterChange(BaseModel):
    phaseId: Optional[int] = Field(None, description="Signal phase ID being adjusted")
    parameter: str = Field(..., description="Parameter name: greenSplitSec, offsetSec, or cycleLengthSec")
    currentValue: float = Field(..., description="Active operational baseline value")
    recommendedValue: float = Field(..., description="Optimizer recommended value")
    unit: str = Field(default="s", description="Unit of measurement")


class ConformalPredictedImpact(BaseModel):
    delayDeltaPct: float = Field(..., description="Predicted percentage change in corridor delay")
    delayDeltaCI: List[float] = Field(..., description="Conformal 90% confidence interval [lower, upper]")
    queueDeltaMeters: float = Field(..., description="Expected queue reduction in meters")
    fuelSavedLitersPerHr: float = Field(..., description="Estimated fuel burn savings in L/hr")


class SafetyConstraintChecklist(BaseModel):
    pedestrianPhaseSafe: bool = Field(default=True, description="Statutory walk phase preserved (>= 14s)")
    maxWaitThresholdSafe: bool = Field(default=True, description="Cross-street waiting time bounded (< 90s)")
    emergencyPreemptionClear: bool = Field(default=True, description="No conflicting emergency vehicle preemption")


class FeatureAttribution(BaseModel):
    feature: str = Field(..., description="Feature name driving the recommendation")
    impact: float = Field(..., description="TreeSHAP impact attribution percentage")


class AdvisoryRecommendation(BaseModel):
    recommendationId: str = Field(..., description="Unique identifier (e.g. REC-TRF-20260920-001)")
    domain: RecommendationDomain
    severity: RecommendationSeverity
    status: RecommendationStatus = Field(default=RecommendationStatus.ACTIVE)
    targetEntityId: str = Field(..., description="NGSI-LD entity ID (RoadSegment, Building, or Sensor)")
    title: str = Field(..., description="Human-readable summary title")
    description: str = Field(..., description="Detailed contextual explanation")
    triggerRule: str = Field(..., description="Deterministic rule identifier (e.g. RULE-TRF-CONGESTION-PREDICTED)")
    evidence: RecommendationEvidence
    suggestedAction: str = Field(..., description="Concrete advisory operational recommendation")
    proposedChange: Optional[ProposedParameterChange] = None
    predictedImpact: Optional[ConformalPredictedImpact] = None
    safetyChecklist: Optional[SafetyConstraintChecklist] = None
    topFeatures: List[FeatureAttribution] = Field(default_factory=list)
    dispatchOrderId: Optional[str] = None
    tamperEvidentHash: Optional[str] = None
    humanApprovalRequired: bool = Field(default=True, description="Strict invariant: platform cannot actuate external systems")
    governanceNotice: str = Field(
        default="Advisory only. Requires human verification and municipal authorization before any physical intervention.",
        description="Non-negotiable governance disclaimer"
    )
    auditTrail: List[AuditLogEntry] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReviewRecommendationRequest(BaseModel):
    newStatus: RecommendationStatus = Field(..., description="Target status: UNDER_REVIEW, ACKNOWLEDGED, or DISMISSED")
    reviewer: str = Field(default="Municipal Traffic Cell Officer", min_length=2, description="Reviewer name or identifier")
    notes: Optional[str] = Field(None, max_length=500, description="Contextual justification for review action")


class AuthorizeAdvisoryRequest(BaseModel):
    badgeId: str = Field(..., min_length=2, max_length=64, description="Dispatcher municipal badge ID")
    shiftId: str = Field(default="SHIFT-A", min_length=2, max_length=64, description="Operating shift identifier")
    reviewer: str = Field(default="Municipal Traffic Officer", min_length=2, description="Authorized reviewer name")
    decision: RecommendationStatus = Field(default=RecommendationStatus.ACKNOWLEDGED, description="Authorization status")
    notes: Optional[str] = Field(None, max_length=1000, description="Operational justification and dispatch notes")


class DispatchWorkOrder(BaseModel):
    dispatchOrderId: str = Field(..., description="Unique municipal dispatch identifier (MDO-YYYYMMDD-XXXX)")
    recommendationId: str = Field(..., description="Target recommendation ID")
    targetEntityId: str = Field(..., description="Physical corridor entity target")
    authorizedBy: str = Field(..., description="Authorizing dispatcher")
    badgeId: str = Field(..., description="Dispatcher badge number")
    shiftId: str = Field(..., description="Duty shift identifier")
    issuedAt: datetime = Field(..., description="Authorization timestamp")
    decision: RecommendationStatus = Field(..., description="Authorization status decision")
    proposedChange: Optional[ProposedParameterChange] = None
    predictedImpact: Optional[ConformalPredictedImpact] = None
    safetyChecklist: Optional[SafetyConstraintChecklist] = None
    notes: Optional[str] = None
    tamperEvidentHash: str = Field(..., description="Cryptographic SHA-256 hash")
    governanceDisclaimer: str = Field(
        default="Advisory decision support only. Requires physical dispatch confirmation by field maintenance personnel."
    )


class AdvisoryAuditLogRecord(BaseModel):
    id: Optional[int] = None
    auditId: str
    recommendationId: str
    targetEntityId: str
    actionType: str
    previousStatus: str
    newStatus: str
    authorizedBy: str
    badgeId: Optional[str] = None
    shiftId: Optional[str] = None
    justificationNotes: Optional[str] = None
    dispatchOrderId: Optional[str] = None
    dispatchPayloadJson: Dict[str, Any]
    tamperEvidentHash: str
    createdAt: datetime


class AdvisorySummary(BaseModel):
    totalActive: int
    criticalCount: int
    warningCount: int
    infoCount: int
    byDomain: Dict[str, int]
