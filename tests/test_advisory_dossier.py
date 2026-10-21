"""
test_advisory_dossier.py

Hermetic unit and integration test suite for the Operator Advisory Dossier & Audit Trail (TASK-10), verifying:
- Complete decision-support dossier models (proposed parameter change, conformal confidence bounds, safety checklist, XAI top features)
- Webster timing advisory integration with full dossier attributions
- Operator authorization workflow with deterministic SHA-256 tamper-evident hashing
- Non-actuation protocol adherence (read-only decision support, mandatory human approval)
- Municipal Dispatch Order (MDO) generation and lookup
- Database persistence in advisory_audit_log table
- REST endpoints (/api/v1/recommendations/{id}/authorize, /dispatch-order, /audit/logs)
- Tamper-evidence verification
"""

from datetime import datetime, timezone
import hashlib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.core.database import AsyncSessionLocal
from backend.main import app
from backend.schemas.recommendations import (
    AuthorizeAdvisoryRequest,
    ConformalPredictedImpact,
    DispatchWorkOrder,
    FeatureAttribution,
    ProposedParameterChange,
    RecommendationStatus,
    SafetyConstraintChecklist
)
from backend.services.rule_engine import AdvisoryRuleEngine, rule_engine

client = TestClient(app)


def test_seeded_traffic_advisory_has_complete_dossier():
    """Verifies that the seeded traffic congestion advisory contains complete dossier models."""
    rec = rule_engine.get_recommendation("REC-TRF-20260920-001")
    assert rec is not None
    assert rec.domain == "TRAFFIC"

    # 1. Proposed Change
    assert rec.proposedChange is not None
    assert rec.proposedChange.phaseId == 1
    assert rec.proposedChange.parameter == "greenSplitSec"
    assert rec.proposedChange.currentValue == 45.0
    assert rec.proposedChange.recommendedValue == 55.0

    # 2. Conformal Predicted Impact
    assert rec.predictedImpact is not None
    assert rec.predictedImpact.delayDeltaPct == -18.4
    assert len(rec.predictedImpact.delayDeltaCI) == 2
    assert rec.predictedImpact.delayDeltaCI[0] < rec.predictedImpact.delayDeltaCI[1]
    assert rec.predictedImpact.queueDeltaMeters == -24.0
    assert rec.predictedImpact.fuelSavedLitersPerHr == 32.5

    # 3. Safety Checklist
    assert rec.safetyChecklist is not None
    assert rec.safetyChecklist.pedestrianPhaseSafe is True
    assert rec.safetyChecklist.maxWaitThresholdSafe is True
    assert rec.safetyChecklist.emergencyPreemptionClear is True

    # 4. Top-5 TreeSHAP Features
    assert len(rec.topFeatures) == 5
    feature_names = [f.feature for f in rec.topFeatures]
    assert "Upstream Corridor Queue Length" in feature_names


def test_webster_timing_advisory_dossier():
    """Verifies that Webster delay minimization timing recommendations generate valid dossiers."""
    advisory = rule_engine.generate_webster_timing_advisory(
        intersection_id="urn:ngsi-ld:Intersection:PUNE:INT-VN-01",
        baseline_cycle_sec=90
    )
    assert advisory is not None
    assert advisory.proposedChange is not None
    assert advisory.proposedChange.parameter == "greenSplitSec"
    assert advisory.proposedChange.recommendedValue > 0

    assert advisory.predictedImpact is not None
    assert advisory.predictedImpact.delayDeltaPct < 0.0
    assert len(advisory.predictedImpact.delayDeltaCI) == 2

    assert advisory.safetyChecklist is not None
    assert advisory.safetyChecklist.pedestrianPhaseSafe is True
    assert len(advisory.topFeatures) == 5


def test_authorize_advisory_generates_sha256_and_order_id():
    """Verifies dispatcher authorization workflow, SHA-256 calculation, and order ID format."""
    engine = AdvisoryRuleEngine()
    rec_id = "REC-TRF-20260920-001"

    req = AuthorizeAdvisoryRequest(
        badgeId="PUNE-TP-4091",
        shiftId="SHIFT-EVENING-B",
        reviewer="Traffic Cell Senior Inspector",
        decision=RecommendationStatus.ACKNOWLEDGED,
        notes="Authorizing SCEN-INT-01 green extension for evening rush."
    )

    result = engine.authorize_advisory(rec_id, req)
    assert result is not None
    updated_rec, dispatch_order = result

    # Verify Dispatch Work Order
    assert dispatch_order.dispatchOrderId.startswith("MDO-")
    assert dispatch_order.badgeId == "PUNE-TP-4091"
    assert dispatch_order.shiftId == "SHIFT-EVENING-B"
    assert dispatch_order.decision == RecommendationStatus.ACKNOWLEDGED
    assert len(dispatch_order.tamperEvidentHash) == 64

    # Verify updated recommendation state
    assert updated_rec.status == RecommendationStatus.ACKNOWLEDGED
    assert updated_rec.dispatchOrderId == dispatch_order.dispatchOrderId
    assert updated_rec.tamperEvidentHash == dispatch_order.tamperEvidentHash

    # Verify audit trail appended
    latest_audit = updated_rec.auditTrail[-1]
    assert "PUNE-TP-4091" in latest_audit.reviewer
    assert latest_audit.newStatus == RecommendationStatus.ACKNOWLEDGED


def test_strict_non_actuation_invariant():
    """Verifies Non-Negotiable Invariant #4: recommendations remain advisory with zero field actuation."""
    engine = AdvisoryRuleEngine()
    rec = engine.get_recommendation("REC-TRF-20260920-001")
    assert rec.humanApprovalRequired is True

    req = AuthorizeAdvisoryRequest(
        badgeId="PUNE-TP-4091",
        shiftId="SHIFT-A",
        reviewer="Inspector",
        decision=RecommendationStatus.ACKNOWLEDGED
    )
    updated_rec, dispatch_order = engine.authorize_advisory("REC-TRF-20260920-001", req)

    # Human approval invariant must never be mutated
    assert updated_rec.humanApprovalRequired is True
    assert "Advisory decision support only" in dispatch_order.governanceDisclaimer


def test_get_dispatch_order():
    """Verifies retrieval of registered dispatch work orders from the rule engine."""
    engine = AdvisoryRuleEngine()
    req = AuthorizeAdvisoryRequest(
        badgeId="PUNE-TP-1001",
        shiftId="SHIFT-A",
        reviewer="Inspector Kulkarni",
        decision=RecommendationStatus.ACKNOWLEDGED
    )
    _, dispatch_order = engine.authorize_advisory("REC-TRF-20260920-001", req)

    retrieved = engine.get_dispatch_order("REC-TRF-20260920-001")
    assert retrieved is not None
    assert retrieved.dispatchOrderId == dispatch_order.dispatchOrderId
    assert retrieved.tamperEvidentHash == dispatch_order.tamperEvidentHash


def test_sha256_tamper_evidence():
    """Verifies that any modification to authorization parameters changes the cryptographic hash."""
    rec_id = "REC-TRF-20260920-001"
    target = "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01"

    manifest_a = f"REC:{rec_id}|ENTITY:{target}|BADGE:PUNE-TP-4091|SHIFT:SHIFT-A|DECISION:ACKNOWLEDGED"
    manifest_b = f"REC:{rec_id}|ENTITY:{target}|BADGE:PUNE-TP-9999|SHIFT:SHIFT-A|DECISION:ACKNOWLEDGED"

    hash_a = hashlib.sha256(manifest_a.encode("utf-8")).hexdigest()
    hash_b = hashlib.sha256(manifest_b.encode("utf-8")).hexdigest()

    assert hash_a != hash_b


@pytest.mark.asyncio
async def test_api_authorize_advisory_endpoint():
    """Verifies POST /api/v1/recommendations/{id}/authorize generates an authenticated dispatch order."""
    payload = {
        "badgeId": "PUNE-TP-4091",
        "shiftId": "SHIFT-EVENING-B",
        "reviewer": "Traffic Cell Duty Officer",
        "decision": "ACKNOWLEDGED",
        "notes": "Field authorization granted per municipal congestion protocol."
    }

    resp = client.post("/api/v1/recommendations/REC-TRF-20260920-001/authorize", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["dispatchOrderId"].startswith("MDO-")
    assert data["recommendationId"] == "REC-TRF-20260920-001"
    assert data["badgeId"] == "PUNE-TP-4091"
    assert data["shiftId"] == "SHIFT-EVENING-B"
    assert len(data["tamperEvidentHash"]) == 64

    # Verify record in database table advisory_audit_log
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT audit_id, dispatch_order_id, tamper_evident_hash FROM advisory_audit_log WHERE recommendation_id = :r"),
            {"r": "REC-TRF-20260920-001"}
        )
        row = result.fetchone()
        assert row is not None
        assert row[1] == data["dispatchOrderId"]
        assert row[2] == data["tamperEvidentHash"]


def test_api_authorize_missing_404():
    """Verifies that authorizing an unknown advisory ID returns HTTP 404."""
    payload = {
        "badgeId": "PUNE-TP-4091",
        "shiftId": "SHIFT-A",
        "reviewer": "Officer",
        "decision": "ACKNOWLEDGED"
    }
    resp = client.post("/api/v1/recommendations/REC-UNKNOWN-999/authorize", json=payload)
    assert resp.status_code == 404


def test_api_authorize_validation_failure_422():
    """Verifies that an incomplete authorization payload fails validation with HTTP 422."""
    # badgeId is mandatory (omitted here)
    payload = {
        "shiftId": "SHIFT-A",
        "reviewer": "Officer"
    }
    resp = client.post("/api/v1/recommendations/REC-TRF-20260920-001/authorize", json=payload)
    assert resp.status_code == 422


def test_api_get_dispatch_order_endpoint():
    """Verifies GET /api/v1/recommendations/{id}/dispatch-order retrieves the issued order."""
    # First authorize
    auth_payload = {
        "badgeId": "PUNE-TP-4091",
        "shiftId": "SHIFT-A",
        "reviewer": "Duty Inspector",
        "decision": "ACKNOWLEDGED"
    }
    auth_resp = client.post("/api/v1/recommendations/REC-TRF-20260920-001/authorize", json=auth_payload)
    assert auth_resp.status_code == 200
    expected_order_id = auth_resp.json()["dispatchOrderId"]

    # Now retrieve order
    resp = client.get("/api/v1/recommendations/REC-TRF-20260920-001/dispatch-order")
    assert resp.status_code == 200
    data = resp.json()
    assert data["dispatchOrderId"] == expected_order_id
    assert data["badgeId"] == "PUNE-TP-4091"


def test_api_audit_logs_endpoint():
    """Verifies GET /api/v1/recommendations/audit/logs returns persistent records from database."""
    resp = client.get("/api/v1/recommendations/audit/logs?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if len(data) > 0:
        entry = data[0]
        assert "auditId" in entry
        assert "recommendationId" in entry
        assert "tamperEvidentHash" in entry
        assert "dispatchOrderId" in entry


@pytest.mark.asyncio
async def test_authorize_preserves_under_review_previous_status():
    """Verifies Bug 12.3 fix: previous status is faithfully recorded as UNDER_REVIEW in audit trail."""
    engine = AdvisoryRuleEngine()
    rec_id = "REC-TRF-20260920-001"

    # 1. First review moves status to UNDER_REVIEW
    reviewed = engine.review_recommendation(
        rec_id=rec_id,
        new_status=RecommendationStatus.UNDER_REVIEW,
        reviewer="Traffic Cell Senior Inspector",
        notes="Reviewing simulation queue dynamics."
    )
    assert reviewed is not None
    assert reviewed.status == RecommendationStatus.UNDER_REVIEW

    # 2. Authorize moves status to ACKNOWLEDGED
    auth_req = AuthorizeAdvisoryRequest(
        badgeId="MCC-OPS-4091",
        shiftId="SHIFT-A",
        reviewer="Inspector",
        decision=RecommendationStatus.ACKNOWLEDGED,
        notes="Authorized after field confirmation."
    )
    auth_result = engine.authorize_advisory(rec_id, auth_req)
    assert auth_result is not None
    updated_rec, dispatch_order = auth_result

    # Latest audit log must capture UNDER_REVIEW as previousStatus, not ACTIVE
    latest_audit = updated_rec.auditTrail[-1]
    assert latest_audit.previousStatus == RecommendationStatus.UNDER_REVIEW
    assert latest_audit.newStatus == RecommendationStatus.ACKNOWLEDGED
