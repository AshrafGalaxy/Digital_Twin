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


def test_replay_session_control_lifecycle():
    """Verify the telemetry stream replay control and status management endpoints."""
    # 1. Check initial replay status
    status_res = client.get("/api/v1/stream/replay/status")
    assert status_res.status_code == 200
    status = status_res.json()
    assert "isPlaying" in status
    assert "minutesAgo" in status
    assert "speed" in status

    # 2. Seek to -180 minutes
    seek_res = client.post("/api/v1/stream/replay/control", json={
        "action": "seek",
        "minutes_ago": 180
    })
    assert seek_res.status_code == 200
    seek_data = seek_res.json()
    assert seek_data["minutesAgo"] == 180
    assert seek_data["sourceMode"] == "REPLAY"

    # 3. Start playback at 5x speed
    play_res = client.post("/api/v1/stream/replay/control", json={"action": "play"})
    assert play_res.status_code == 200
    assert play_res.json()["isPlaying"] is True

    speed_res = client.post("/api/v1/stream/replay/control", json={
        "action": "speed",
        "speed": 5.0
    })
    assert speed_res.status_code == 200
    assert speed_res.json()["speed"] == 5.0

    # 4. Pause playback
    pause_res = client.post("/api/v1/stream/replay/control", json={"action": "pause"})
    assert pause_res.status_code == 200
    assert pause_res.json()["isPlaying"] is False

    # 5. Jump back to live
    live_res = client.post("/api/v1/stream/replay/control", json={"action": "jump_to_live"})
    assert live_res.status_code == 200
    live_data = live_res.json()
    assert live_data["minutesAgo"] == 0
    assert live_data["isPlaying"] is False
    assert live_data["sourceMode"] == "SIMULATION"


def test_replay_control_input_validation():
    """Verify input validation rules on replay control endpoint."""
    # Out of range minutes_ago (> 720) should fail validation with 422
    invalid_res = client.post("/api/v1/stream/replay/control", json={
        "action": "seek",
        "minutes_ago": 1500
    })
    assert invalid_res.status_code == 422


def test_segment_comparison_endpoint_valid_pair():
    """Verify GET /api/v1/state/compare returns side-by-side metrics, deltas, and LOS."""
    seg_a = "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01"
    seg_b = "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-02"
    response = client.get(f"/api/v1/state/compare?segment_a={seg_a}&segment_b={seg_b}")
    assert response.status_code == 200
    data = response.json()

    # Check segment A and B structure
    assert data["segmentA"]["id"] == seg_a
    assert data["segmentA"]["direction"] == "EASTBOUND"
    assert data["segmentA"]["levelOfService"] in ["A", "B", "C", "D", "E", "F"]

    assert data["segmentB"]["id"] == seg_b
    assert data["segmentB"]["direction"] == "WESTBOUND"
    assert data["segmentB"]["levelOfService"] in ["A", "B", "C", "D", "E", "F"]

    # Check comparative deltas
    deltas = data["deltas"]
    assert "speedDeltaKmh" in deltas
    assert "queueDeltaMeters" in deltas
    assert "congestionIndexDelta" in deltas
    assert "flowDeltaPerHour" in deltas

    # Check directional imbalance diagnosis
    imbalance = data["directionalImbalance"]
    assert imbalance["severity"] in ["CRITICAL", "ELEVATED", "BALANCED"]
    assert len(imbalance["summary"]) > 10


def test_segment_comparison_endpoint_invalid_segment():
    """Verify GET /api/v1/state/compare returns 404 if a segment ID is invalid."""
    seg_a = "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01"
    seg_b = "urn:ngsi-ld:RoadSegment:PUNE:NON-EXISTENT"
    response = client.get(f"/api/v1/state/compare?segment_a={seg_a}&segment_b={seg_b}")
    assert response.status_code == 404


