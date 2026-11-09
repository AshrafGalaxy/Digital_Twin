"""
test_pilot_evaluation.py

Hermetic unit and integration tests for Milestone 9:
- Multi-horizon evaluation benchmarks & persistence baselines
- Municipal executive decision-support report generator (JSON & Markdown)
- Reproducible corridor bundle export
- Non-actuation and provenance invariant verification
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient
from backend.core.config import settings
from backend.main import app
from backend.services.evaluation_service import (
    EvaluationService,
    score_forecast_holdout,
)
from backend.services.report_generator import MunicipalReportGenerator

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


def _empty_state_db(tmp_path):
    db_path = tmp_path / "empty_state.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE entity_current_state (source_mode TEXT)")
    return db_path


def test_empty_current_state_counts_stay_zero(monkeypatch, tmp_path):
    """A readable empty table reports zero for every source mode."""
    monkeypatch.setattr(settings, "SQLITE_DB_PATH", str(_empty_state_db(tmp_path)))
    counts = MunicipalReportGenerator()._query_live_provenance_counts()
    assert counts == {
        "LIVE": 0,
        "REPLAY": 0,
        "SIMULATION": 0,
        "PREDICTED": 0,
        "STALE": 0,
        "INVALID": 0,
    }


def test_missing_state_database_stays_zero(monkeypatch, tmp_path):
    """A missing database file does not substitute a baseline count."""
    monkeypatch.setattr(settings, "SQLITE_DB_PATH", str(tmp_path / "absent.db"))
    counts = MunicipalReportGenerator()._query_live_provenance_counts()
    assert counts["LIVE"] == 0
    assert counts["REPLAY"] == 0
    assert counts["PREDICTED"] == 0
    assert counts["SIMULATION"] == 0


def test_recorded_source_count_is_kept(monkeypatch, tmp_path):
    """A real row is counted, and the modes with no rows stay at zero."""
    db_path = tmp_path / "one_live_row.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE entity_current_state (source_mode TEXT)")
        conn.execute("INSERT INTO entity_current_state (source_mode) VALUES ('LIVE')")
    monkeypatch.setattr(settings, "SQLITE_DB_PATH", str(db_path))
    counts = MunicipalReportGenerator()._query_live_provenance_counts()
    assert counts["LIVE"] == 1
    assert counts["REPLAY"] == 0
    assert counts["PREDICTED"] == 0
    assert counts["SIMULATION"] == 0


def test_scenario_runs_do_not_raise_simulation_count(monkeypatch):
    """Scenario runs stay in their own field and do not fill the simulation count."""
    monkeypatch.setattr(
        "backend.services.report_generator.evaluation_service.get_multi_horizon_benchmarks",
        lambda: {"horizons": {}},
    )
    monkeypatch.setattr(
        "backend.services.report_generator.scenario_service.list_recent_runs",
        lambda limit=5: [{"id": "run-1"}, {"id": "run-2"}],
    )
    monkeypatch.setattr(
        MunicipalReportGenerator,
        "_query_live_provenance_counts",
        lambda self: {
            "LIVE": 0,
            "REPLAY": 0,
            "SIMULATION": 0,
            "PREDICTED": 0,
            "STALE": 0,
            "INVALID": 0,
        },
    )
    report = MunicipalReportGenerator().generate_executive_report()
    modes = report["provenanceAudit"]["sourceModes"]
    assert modes["LIVE"] == 0
    assert modes["REPLAY"] == 0
    assert modes["SIMULATION"] == 0
    assert modes["PREDICTED"] == 0
    assert report["provenanceAudit"]["scenarioRunCount"] == 2
    assert report["scenarioStudioSummary"]["totalRunsRecorded"] == 2


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
