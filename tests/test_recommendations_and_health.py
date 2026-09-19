"""
test_recommendations_and_health.py

Unit and integration tests for Phase 6: Advisory Recommendation & Governance Workflow (D-10)
and Platform Reliability, Security, and Diagnostics (D-11).
Tests rule evaluation, human governance invariants, audit trail logging, and subsystem health checks.
"""

from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.main import app
from backend.schemas.recommendations import (
    AdvisoryRecommendation,
    RecommendationDomain,
    RecommendationSeverity,
    RecommendationStatus
)
from backend.services.rule_engine import AdvisoryRuleEngine, rule_engine


@pytest.fixture
def client():
    return TestClient(app)


def test_rule_engine_initial_seeding_and_invariants():
    """Verifies that the rule engine initializes with realistic seeded advisories and mandatory governance flags."""
    recs = rule_engine.list_recommendations()
    assert len(recs) >= 3

    # Traffic advisory verification
    trf_rec = next((r for r in recs if r.domain == RecommendationDomain.TRAFFIC), None)
    assert trf_rec is not None
    assert trf_rec.humanApprovalRequired is True
    assert "human verification" in trf_rec.governanceNotice.lower()
    assert trf_rec.evidence.sourceMode == "PREDICTED"
    assert trf_rec.evidence.modelVersion == "traffic-xgb-v1"
    assert trf_rec.evidence.scenarioId == "SCEN-INT-01"

    # Energy advisory verification
    nrg_rec = next((r for r in recs if r.domain == RecommendationDomain.ENERGY), None)
    assert nrg_rec is not None
    assert nrg_rec.humanApprovalRequired is True
    assert nrg_rec.evidence.threshold == 4800.0


def test_review_lifecycle_and_audit_trail_preservation():
    """Verifies that human governance review updates status and appends to the chronological audit log."""
    engine = AdvisoryRuleEngine()
    rec_id = "REC-TRF-20260920-001"

    # Initial state should be ACTIVE
    rec = engine.get_recommendation(rec_id)
    assert rec is not None
    assert rec.status == RecommendationStatus.ACTIVE
    initial_audit_len = len(rec.auditTrail)

    # 1. Transition to UNDER_REVIEW
    updated = engine.review_recommendation(
        rec_id=rec_id,
        new_status=RecommendationStatus.UNDER_REVIEW,
        reviewer="Traffic Cell Senior Engineer",
        notes="Field CCTV confirms eastbound queue spillback at Viman Nagar Chowk."
    )
    assert updated is not None
    assert updated.status == RecommendationStatus.UNDER_REVIEW
    assert len(updated.auditTrail) == initial_audit_len + 1
    assert updated.auditTrail[-1].reviewer == "Traffic Cell Senior Engineer"
    assert updated.auditTrail[-1].previousStatus == RecommendationStatus.ACTIVE
    assert updated.auditTrail[-1].newStatus == RecommendationStatus.UNDER_REVIEW

    # 2. Transition to ACKNOWLEDGED
    final_rec = engine.review_recommendation(
        rec_id=rec_id,
        new_status=RecommendationStatus.ACKNOWLEDGED,
        reviewer="Municipal Deputy Commissioner",
        notes="Approved manual cycle adjustment outside platform."
    )
    assert final_rec.status == RecommendationStatus.ACKNOWLEDGED
    assert len(final_rec.auditTrail) == initial_audit_len + 2
    assert final_rec.auditTrail[-1].newStatus == RecommendationStatus.ACKNOWLEDGED


def test_api_recommendation_filtering_and_review(client):
    """Verifies REST endpoints for listing, filtering, and reviewing recommendations."""
    # 1. Filter by TRAFFIC domain
    res = client.get("/api/v1/recommendations?domain=TRAFFIC")
    assert res.status_code == 200
    traffic_recs = res.json()
    assert len(traffic_recs) >= 1
    for r in traffic_recs:
        assert r["domain"] == "TRAFFIC"

    # 2. Summary stats
    res_sum = client.get("/api/v1/recommendations/summary")
    assert res_sum.status_code == 200
    summary = res_sum.json()
    assert summary["totalActive"] >= 1
    assert "TRAFFIC" in summary["byDomain"]

    # 3. Execute review via API
    rec_id = "REC-NRG-20260920-002"
    review_res = client.post(
        f"/api/v1/recommendations/{rec_id}/review",
        json={
            "newStatus": "UNDER_REVIEW",
            "reviewer": "Facility Energy Manager",
            "notes": "Checking chiller stage schedule."
        }
    )
    assert review_res.status_code == 200
    updated = review_res.json()
    assert updated["status"] == "UNDER_REVIEW"
    assert updated["auditTrail"][-1]["reviewer"] == "Facility Energy Manager"


def test_health_check_deep_subsystem_reporting(client):
    """Verifies that /api/v1/health returns detailed diagnostic indicators for all subsystems."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] in ("HEALTHY", "DEGRADED")
    assert data["governanceMode"] == "HUMAN_ADVISORY"
    assert "subsystems" in data

    subsystems = data["subsystems"]
    assert "database" in subsystems
    assert subsystems["mlTrafficModel"] is True
    assert subsystems["mlEnergyModel"] is True
    assert subsystems["simulationEngine"] is True
    assert subsystems["scenarioTemplatesCount"] >= 3
    assert subsystems["activeAdvisoriesCount"] >= 1


def test_recommendation_non_actuation_invariant():
    """Verifies that recommendations contain no physical actuator triggers and remain strictly advisory."""
    for rec in rule_engine.list_recommendations():
        assert rec.humanApprovalRequired is True
        assert "no physical intervention" in rec.governanceNotice.lower() or "requires human verification" in rec.governanceNotice.lower()
        # Verify no external actuation URLs or webhook triggers
        assert not hasattr(rec, "actuatorEndpoint")
        assert not hasattr(rec, "autoExecute")
