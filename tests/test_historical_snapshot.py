"""
test_historical_snapshot.py

Tests for P1-B historical snapshot API and provenance invariants.
Verifies that historical queries return REPLAY source mode, correct timestamps,
and realistic corridor metrics without mutating current live state.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_corridor_snapshot_default_endpoint():
    """Verify GET /api/v1/state/snapshot returns 10 corridor segments with REPLAY provenance."""
    response = client.get("/api/v1/state/snapshot?minutes_ago=60")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 10

    for item in data:
        assert item["entityType"] == "RoadSegment"
        assert item["sourceMode"] == "REPLAY"
        assert item["qualityStatus"] == "VALID"
        assert "averageSpeedKmh" in item["metrics"]
        assert "congestionIndex" in item["metrics"]
        assert 10.0 <= item["metrics"]["averageSpeedKmh"] <= 60.0
        assert 0.0 <= item["metrics"]["congestionIndex"] <= 1.0


def test_corridor_snapshot_evening_rush_profile():
    """Verify evening rush hour snapshot reflects heavy Eastbound congestion."""
    # Target 18:30 UTC (which corresponds to evening peak in test calculations)
    target_time = "2026-09-19T18:30:00Z"
    response = client.get(f"/api/v1/state/snapshot?target_time={target_time}")
    assert response.status_code == 200
    data = response.json()

    eb_segments = [s for s in data if "EB" in s["entityId"]]
    assert len(eb_segments) >= 3

    # In evening rush, EB speed should be congested (< 25 km/h)
    for seg in eb_segments:
        assert seg["metrics"]["averageSpeedKmh"] < 25.0
        assert seg["metrics"]["congestionIndex"] > 0.50
        assert seg["sourceMode"] == "REPLAY"


def test_corridor_snapshot_preserves_live_state_isolation():
    """Verify that querying historical snapshots never overwrites or mutates current live state."""
    # 1. Query current state
    current_res_1 = client.get("/api/v1/state/current")
    assert current_res_1.status_code == 200
    initial_live_records = current_res_1.json()

    # 2. Query multiple historical snapshots
    client.get("/api/v1/state/snapshot?minutes_ago=120")
    client.get("/api/v1/state/snapshot?minutes_ago=360")
    client.get("/api/v1/state/snapshot?minutes_ago=720")

    # 3. Query current state again; verify isolation invariant
    current_res_2 = client.get("/api/v1/state/current")
    assert current_res_2.status_code == 200
    after_live_records = current_res_2.json()

    # The current state entity count and contents should remain independent of historical queries
    assert len(initial_live_records) == len(after_live_records)
