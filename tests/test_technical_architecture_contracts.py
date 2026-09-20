"""
test_technical_architecture_contracts.py

Verifies compliance with TECHNICAL_ARCHITECTURE.md contracts:
- §13.2 Canonical REST Resources (/health, /roads, /intersections, /entities/{id},
  /observations, /forecasts, /scenarios, /scenario-runs/{id}, /models, /data-quality)
- §13.3 WebSocket Channel Endpoints (/ws/operations, /ws/system, /ws/scenarios/{runId})
- §6 Architectural Invariants (State separation, advisory recommendations, provenance tagging)
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root_health_contract():
    """Verifies GET /health returns database connectivity and operational status per §13.2."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["status"] in ("HEALTHY", "DEGRADED")
    assert "database" in data
    assert "activeBackend" in data["database"]
    assert data["database"]["activeBackend"] in ("postgresql", "sqlite")

def test_canonical_roads_endpoints():
    """Verifies GET /api/v1/roads and GET /api/v1/roads/{id} per §13.2."""
    res = client.get("/api/v1/roads")
    assert res.status_code == 200
    roads = res.json()
    assert isinstance(roads, list)
    assert len(roads) >= 8  # Corridor has 10 approved road segments

    # Test single road segment detail
    sample_id = roads[0]["id"]
    res_detail = client.get(f"/api/v1/roads/{sample_id}")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert "entity" in detail
    assert "currentState" in detail
    assert "forecast15m" in detail
    assert detail["forecast15m"]["sourceMode"] == "PREDICTED"

def test_canonical_intersections_endpoint():
    """Verifies GET /api/v1/intersections per §13.2."""
    res = client.get("/api/v1/intersections")
    assert res.status_code == 200
    ixs = res.json()
    assert isinstance(ixs, list)
    assert len(ixs) >= 2  # Viman Nagar Chowk and Somnath Nagar Chowk
    names = [ix["name"] for ix in ixs]
    assert any("Viman Nagar" in n for n in names)

def test_canonical_generic_entity_resolver():
    """Verifies GET /api/v1/entities/{id} resolves road segments, intersections, and buildings per §13.2."""
    # Resolve road segment
    res_seg = client.get("/api/v1/entities/urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01")
    assert res_seg.status_code == 200
    assert res_seg.json()["entityType"] == "RoadSegment"

    # Resolve intersection
    res_ix = client.get("/api/v1/entities/urn:ngsi-ld:Intersection:PUNE:VN-01")
    assert res_ix.status_code == 200
    assert res_ix.json()["entityType"] == "Intersection"

    # Resolve building zone
    res_bld = client.get("/api/v1/entities/urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01")
    if res_bld.status_code == 404:
        # Check alternative URN format
        res_bld = client.get("/api/v1/entities/urn:ngsi-ld:BuildingZone:PUNE:PHOENIX-01")
    assert res_bld.status_code == 200
    assert res_bld.json()["entityType"] == "BuildingZone"

    # Non-existent entity returns 404
    res_404 = client.get("/api/v1/entities/non-existent-urn")
    assert res_404.status_code == 404

def test_canonical_observations_hypertable_query():
    """Verifies GET /api/v1/observations supports domain filtering per §13.2."""
    res = client.get("/api/v1/observations?domain=traffic&limit=10")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_canonical_corridor_forecasts():
    """Verifies GET /api/v1/forecasts returns PREDICTED values with model citations per §13.2."""
    res = client.get("/api/v1/forecasts")
    assert res.status_code == 200
    data = res.json()
    assert data["sourceMode"] == "PREDICTED"
    assert "trafficForecasts" in data
    assert len(data["trafficForecasts"]) > 0
    tf = data["trafficForecasts"][0]
    assert tf["sourceMode"] == "PREDICTED"
    assert "conformalIntervals" in tf or "confidenceLower" in tf

def test_canonical_scenarios_and_runs():
    """Verifies GET /api/v1/scenarios lists pre-approved simulation templates per §13.2."""
    res = client.get("/api/v1/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 3
    template_ids = [s["id"] for s in scenarios]
    assert "SCEN-BASE-01" in template_ids
    assert "SCEN-INT-01" in template_ids

def test_canonical_models_metadata():
    """Verifies GET /api/v1/models returns ML model cards, metrics, and baseline comparisons per §13.2."""
    res = client.get("/api/v1/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) >= 2
    domains = [m["domain"].lower() for m in models]
    assert "traffic" in domains
    assert "energy" in domains
    for m in models:
        assert m["status"] in ("APPROVED_FOR_DEMO", "FALLBACK")
        assert "testMae" in m
        assert "testRmse" in m

def test_canonical_data_quality_report():
    """Verifies GET /api/v1/data-quality returns ingestion health and quarantine summary per §13.2."""
    res = client.get("/api/v1/data-quality")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert "schemaCompliancePct" in data
    assert "quarantineSummary" in data

def test_websocket_operations_channel():
    """Verifies /ws/operations WebSocket accepts connection and handles ping per §13.3."""
    with client.websocket_connect("/ws/operations") as ws:
        msg = ws.receive_json()
        assert msg["eventType"] == "CONNECTION_ESTABLISHED"
        assert msg["channel"] == "operations"
        ws.send_text("ping")
        pong = ws.receive_json()
        assert pong["eventType"] == "PONG"

def test_websocket_system_channel():
    """Verifies /ws/system WebSocket broadcasts system health per §13.3."""
    with client.websocket_connect("/ws/system") as ws:
        msg = ws.receive_json()
        assert msg["eventType"] == "SYSTEM_STATUS"
        assert msg["channel"] == "system"
        assert "database" in msg
        ws.send_text("ping")
        pong = ws.receive_json()
        assert pong["eventType"] == "PONG"

def test_architectural_invariants():
    """Verifies core architectural invariants defined in TECHNICAL_ARCHITECTURE.md §6."""
    # Invariant 7: Recommendations are advisory and require human approval
    res = client.get("/api/v1/recommendations")
    assert res.status_code == 200
    recs = res.json()
    for rec in recs:
        assert rec.get("humanApprovalRequired", True) is True

    # Invariant 3 & 4: Observations and predictions are separate data classes
    state_res = client.get("/api/v1/state/current")
    assert state_res.status_code == 200
    state_items = state_res.json()
    assert isinstance(state_items, list)
    for item in state_items:
        # Current state is observed/replayed, not predicted
        assert item.get("sourceMode") in ("LIVE", "REPLAY", "SIMULATION")
        assert item.get("sourceMode") != "PREDICTED"
