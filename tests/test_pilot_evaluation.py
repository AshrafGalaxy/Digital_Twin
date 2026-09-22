"""
test_pilot_evaluation.py

Hermetic unit and integration tests for Milestone 9:
- Multi-horizon evaluation benchmarks & persistence baselines
- Municipal executive decision-support report generator (JSON & Markdown)
- Reproducible corridor bundle export
- Non-actuation and provenance invariant verification
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_multi_horizon_evaluation_benchmarks():
    """Verify multi-horizon benchmarks across 15m, 30m, and 60m."""
    response = client.get("/api/v1/analytics/evaluation/benchmarks")
    assert response.status_code == 200
    data = response.json()

    assert "horizons" in data
    assert "15m" in data["horizons"]
    assert "30m" in data["horizons"]
    assert "60m" in data["horizons"]

    h15 = data["horizons"]["15m"]
    assert h15["modelMae"] > 0
    assert h15["persistenceMae"] > 0
    assert h15["modelMae"] < h15["persistenceMae"]
    assert h15["skillScore"] > 0
    assert h15["improvementPct"] > 10.0

    # Conformal interval coverage check
    assert "conformalCoverage" in data
    cov90 = data["conformalCoverage"]["target90"]
    cov95 = data["conformalCoverage"]["target95"]
    assert cov90["empiricalCoveragePct"] >= 85.0
    assert cov95["empiricalCoveragePct"] >= 90.0


def test_executive_summary_report_json():
    """Verify municipal executive briefing in structured JSON format."""
    response = client.get("/api/v1/reports/executive-summary")
    assert response.status_code == 200
    report = response.json()

    assert report["reportId"].startswith("REP-PUNE-NR-")
    assert "corridor" in report
    assert "Viman Nagar" in report["corridor"]["boundary"]
    assert report["corridor"]["lengthKm"] == 1.8

    # Provenance audit check
    assert "provenanceAudit" in report
    assert report["provenanceAudit"]["stateSeparationInvariantEnforced"] is True
    assert report["provenanceAudit"]["zeroActuationPolicyEnforced"] is True

    # Statutory governance notice
    assert "READ-ONLY DECISION SUPPORT NOTICE" in report["governanceNotice"]
    assert "NOT actuated by this platform" in report["governanceNotice"]


def test_executive_summary_report_markdown():
    """Verify publication-ready executive briefing in Markdown format."""
    response = client.get("/api/v1/reports/executive-summary/markdown")
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]
    text = response.text

    assert "# Municipal Decision-Support Briefing:" in text
    assert "Viman Nagar Chowk (INT-VN-01)" in text
    assert "Multi-Horizon Forecasting Accuracy Benchmarks" in text
    assert "Conformal Prediction Uncertainty Coverage" in text
    assert "Physical traffic signal controllers are NOT actuated" in text


def test_export_corridor_bundle():
    """Verify reproducible export bundle packaging for peer and municipal review."""
    response = client.get("/api/v1/export/corridor-bundle")
    assert response.status_code == 200
    bundle = response.json()

    assert bundle["corridorBundleVersion"] == "1.0.0"
    assert "corridorMetadata" in bundle
    assert "evaluationBenchmarks" in bundle
    assert "scenarioRuns" in bundle
    assert "provenanceAudit" in bundle
    assert "governanceNotice" in bundle
