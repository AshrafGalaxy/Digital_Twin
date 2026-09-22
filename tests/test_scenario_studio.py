"""
test_scenario_studio.py

Hermetic unit and integration tests for Scenario Studio:
- Template registry validation
- Microscopic simulation execution for SCEN-INT-01 and SCEN-INT-02
- Comparative KPI extraction & state separation invariant
- Human-governed advisory proposal workflow from simulation runs
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.scenario_service import scenario_service
from backend.services.rule_engine import rule_engine

client = TestClient(app)


def test_list_scenario_templates():
    """Verify all approved scenario templates are present."""
    response = client.get("/api/v1/scenarios/templates")
    assert response.status_code == 200
    templates = response.json()
    assert len(templates) >= 3
    template_ids = {t["id"] for t in templates}
    assert "SCEN-BASE-01" in template_ids
    assert "SCEN-INT-01" in template_ids
    assert "SCEN-INT-02" in template_ids


def test_execute_scen_int_01_green_extension():
    """Verify execution of dynamic green split re-allocation scenario."""
    payload = {
        "templateId": "SCEN-INT-01",
        "greenExtensionSec": 20.0,
        "demandMultiplier": 1.1,
        "randomSeed": 101
    }
    response = client.post("/api/v1/scenarios/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["sourceMode"] == "SIMULATION"
    assert "SIMULATION OUTPUT" in data["governanceNotice"]
    assert data["randomSeed"] == 101
    assert data["parameters"]["greenExtensionSec"] == 20.0

    # Baseline vs Intervention checks
    assert data["baseline"]["templateId"] == "SCEN-BASE-01"
    assert data["intervention"]["templateId"] == "SCEN-INT-01"

    kpis_base = data["baseline"]["kpis"]
    kpis_int = data["intervention"]["kpis"]
    assert kpis_int["average_delay_sec"] < kpis_base["average_delay_sec"]
    assert data["deltas"]["delay_saved_sec"] > 0
    assert "POSITIVE" in data["deltas"]["overall_verdict"] or "RECOMMENDED" in data["deltas"]["overall_verdict"]


def test_execute_scen_int_02_arterial_coordination():
    """Verify execution of arterial progression offset scenario."""
    payload = {
        "templateId": "SCEN-INT-02",
        "coordinationOffsetSec": 35.0,
        "demandMultiplier": 1.0,
        "randomSeed": 42
    }
    response = client.post("/api/v1/scenarios/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["sourceMode"] == "SIMULATION"
    assert data["templateId"] == "SCEN-INT-02"
    assert data["parameters"]["coordinationOffsetSec"] == 35.0

    deltas = data["deltas"]
    assert deltas["travel_time_saved_sec"] > 0
    assert deltas["delay_saved_sec"] > 0


def test_propose_advisory_from_run():
    """Verify transforming simulation run into a non-actuating human advisory."""
    # 1. Run simulation
    run_res = client.post("/api/v1/scenarios/run", json={
        "templateId": "SCEN-INT-01",
        "greenExtensionSec": 15.0,
        "demandMultiplier": 1.0,
        "randomSeed": 42
    })
    assert run_res.status_code == 200
    run_id = run_res.json()["runId"]

    # 2. Propose advisory
    prop_res = client.post(
        f"/api/v1/scenarios/runs/{run_id}/propose-advisory",
        json={
            "reviewer": "Traffic Operations Chief",
            "notes": "Validated against 18:30 queue spillback telemetry."
        }
    )
    assert prop_res.status_code == 200
    advisory = prop_res.json()

    assert advisory["recommendationId"].startswith("REC-SCEN-")
    assert advisory["domain"] == "TRAFFIC"
    assert advisory["humanApprovalRequired"] is True
    assert advisory["evidence"]["sourceMode"] == "SIMULATION"
    assert "Physical traffic signals are NOT actuated" in advisory["governanceNotice"]
    assert len(advisory["auditTrail"]) >= 1
    assert advisory["auditTrail"][0]["reviewer"] == "Traffic Operations Chief"

    # 3. Verify it appears in active recommendations endpoint
    rec_list_res = client.get("/api/v1/recommendations")
    assert rec_list_res.status_code == 200
    all_recs = rec_list_res.json()
    matching = [r for r in all_recs if r["recommendationId"] == advisory["recommendationId"]]
    assert len(matching) == 1
    assert matching[0]["title"] == advisory["title"]


def test_propose_advisory_nonexistent_run():
    """Verify 404 returned for unknown run ID."""
    res = client.post(
        "/api/v1/scenarios/runs/urn:ngsi-ld:ScenarioRun:NONEXISTENT/propose-advisory",
        json={"reviewer": "Nobody"}
    )
    assert res.status_code == 404
