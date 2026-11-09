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
from backend.services.evaluation_service import (
    EvaluationService,
    score_forecast_holdout,
)

client = TestClient(app)


def test_multi_horizon_evaluation_benchmarks():
    """The report lists the trained 15-minute horizon and a later holdout."""
    response = client.get("/api/v1/analytics/evaluation/benchmarks")
    assert response.status_code == 200
    data = response.json()

    assert data["seriesProvenance"] == "GENERATED"
    assert data["testSplitStartsAt"] > data["holdoutStartsAfter"]
    assert "15m" in data["horizons"]
    assert "30m" not in data["horizons"]
    assert "60m" not in data["horizons"]

    h15 = data["horizons"]["15m"]
    assert h15["status"] == "SCORED"
    assert isinstance(h15["modelMae"], float)
    assert isinstance(h15["persistenceMae"], float)
    assert h15["r2Score"] is not None

    cov90 = data["conformalCoverage"]["target90"]
    cov95 = data["conformalCoverage"]["target95"]
    assert isinstance(cov90["empiricalCoveragePct"], float)
    assert isinstance(cov95["empiricalCoveragePct"], float)
    assert cov90["valid"] is (cov90["empiricalCoveragePct"] >= 90.0)
    assert cov95["valid"] is (cov95["empiricalCoveragePct"] >= 95.0)


def test_negative_r2_is_not_floored():
    """A prediction worse than the mean of the target keeps a negative R-squared."""
    scored = score_forecast_holdout([0.0, 10.0], [10.0, 0.0], [0.0, 10.0])
    assert scored["r2Score"] < 0


def test_missing_artifact_does_not_invent_a_model_score(monkeypatch):
    """A missing model file omits model MAE and does not substitute a slope."""
    class _EmptyForecaster:
        traffic_artifact = None
        energy_artifact = None

    monkeypatch.setattr(
        "backend.services.evaluation_service.CorridorForecaster",
        _EmptyForecaster,
    )
    data = EvaluationService().get_multi_horizon_benchmarks(force_recompute=True)
    assert data["horizons"]["15m"]["status"] == "MODEL_UNAVAILABLE"
    assert data["horizons"]["15m"]["modelMae"] is None
    assert data["buildingEnergy"]["modelMae"] is None
    assert data["conformalCoverage"]["status"] == "MODEL_UNAVAILABLE"
    serialized = str(data)
    assert "0.95 + 1.2" not in serialized
    assert "* 0.94" not in serialized


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
