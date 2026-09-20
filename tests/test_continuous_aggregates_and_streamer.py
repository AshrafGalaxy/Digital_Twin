"""
test_continuous_aggregates_and_streamer.py

Automated tests for Track 4, Task P4-B: Native Continuous Aggregates & Background Telemetry Worker.
Verifies:
1. In-process telemetry streamer physics execution, DB writes, and state updates.
2. 15-minute continuous aggregates rollups engine across SQLite and PostgreSQL.
3. Analytics rollup endpoints (GET and POST compute).
4. Streamer control API (start, stop, pause, resume, tick_once, set_interval).
5. Health diagnostic reporting of streamer metrics and 19 initialized tables.
"""

import asyncio
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.main import app
from backend.core.database import persistence_manager, get_db_session
from backend.core.schema_migrator import init_db_schema
from backend.ingestion.telemetry_streamer import telemetry_streamer
from backend.services.continuous_aggregator import continuous_aggregator


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.asyncio
async def test_schema_includes_traffic_15m_aggregates():
    """Verifies that the schema migrator creates table 19 (traffic_15m_aggregates)."""
    res = await init_db_schema()
    assert res["status"] == "INITIALIZED"
    assert res["tablesCount"] >= 19

    async with persistence_manager.session_factory() as session:
        check = await session.execute(text("SELECT COUNT(*) FROM traffic_15m_aggregates"))
        count = check.scalar()
        assert count is not None
        assert count >= 0


@pytest.mark.asyncio
async def test_telemetry_streamer_physics_tick_and_persistence():
    """Verifies that a single physics tick persists observations and updates entity current state."""
    initial_ticks = telemetry_streamer.ticks_count
    tick_res = await telemetry_streamer.tick_once()

    assert tick_res["status"] == "TICK_SUCCESS"
    assert tick_res["tickNumber"] == initial_ticks + 1
    assert tick_res["segmentsUpdated"] == 10
    assert tick_res["buildingPowerKw"] >= 2000.0
    assert tick_res["aqi"] > 0.0

    # Verify DB records
    async with persistence_manager.session_factory() as session:
        # 1. Traffic observations
        t_res = await session.execute(
            text("SELECT COUNT(*) FROM traffic_observations WHERE source_mode = :m"),
            {"m": telemetry_streamer.mode}
        )
        assert (t_res.scalar() or 0) >= 10

        # 2. Energy observations
        e_res = await session.execute(
            text("SELECT COUNT(*) FROM energy_observations WHERE building_id = 'urn:ngsi-ld:BuildingZone:PUNE:PHOENIX-01'")
        )
        assert (e_res.scalar() or 0) >= 1

        # 3. Air quality observations
        env_res = await session.execute(
            text("SELECT COUNT(*) FROM environment_observations WHERE station_id = 'urn:ngsi-ld:AirQualityStation:PUNE:STATION-VIMAN-AQI-01'")
        )
        assert (env_res.scalar() or 0) >= 1

        # 4. Entity current state updated
        state_res = await session.execute(
            text("SELECT COUNT(*) FROM entity_current_state WHERE entity_type = 'RoadSegment'")
        )
        assert (state_res.scalar() or 0) >= 10


@pytest.mark.asyncio
async def test_continuous_aggregator_seed_and_compute():
    """Verifies 15-minute continuous aggregates rollups seeding and computation."""
    async with persistence_manager.session_factory() as session:
        # Seed synthetic historical rollups
        seeded = await continuous_aggregator.seed_synthetic_historical_rollups(session)
        # Even if already seeded, query should return rollups
        rollups = await continuous_aggregator.get_traffic_rollups(session, hours_ago=24, limit=50)
        assert len(rollups) > 0
        first = rollups[0]
        assert "bucket15m" in first
        assert "segmentId" in first
        assert "avgSpeedKmh" in first
        assert "totalFlowVeh" in first
        assert "avgOccupancyPercent" in first
        assert "avgQueueLengthMeters" in first
        assert "avgCongestionIndex" in first

        # Test compute and materialize pass from raw observations
        rows = await continuous_aggregator.compute_and_materialize_rollups(session, hours_back=24)
        assert rows >= 0


def test_analytics_api_traffic_rollups(client):
    """Verifies GET /api/v1/analytics/rollups/traffic endpoint."""
    resp = client.get("/api/v1/analytics/rollups/traffic?hours_ago=24&limit=50")
    assert resp.status_code == 200
    data = resp.json()

    assert "totalRecords" in data
    assert "rollups" in data
    assert data["totalRecords"] >= 1
    assert len(data["rollups"]) >= 1

    first_item = data["rollups"][0]
    assert "bucket15m" in first_item
    assert "segmentId" in first_item
    assert "avgSpeedKmh" in first_item
    assert "totalFlowVeh" in first_item


def test_analytics_api_traffic_rollups_segment_filter(client):
    """Verifies segment filtering on GET /api/v1/analytics/rollups/traffic."""
    seg_id = "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01"
    resp = client.get(f"/api/v1/analytics/rollups/traffic?segment_id={seg_id}&hours_ago=24")
    assert resp.status_code == 200
    data = resp.json()

    assert data["segmentId"] == seg_id
    for r in data["rollups"]:
        assert r["segmentId"] == seg_id


def test_analytics_api_compute_endpoint(client):
    """Verifies POST /api/v1/analytics/rollups/compute endpoint."""
    resp = client.post("/api/v1/analytics/rollups/compute?hours_back=12")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "COMPUTED"
    assert "rowsAffected" in data
    assert data["hoursBack"] == 12


def test_streamer_api_status_and_controls(client):
    """Verifies GET /api/v1/stream/simulator/status and POST /api/v1/stream/simulator/control."""
    # 1. Get status
    resp = client.get("/api/v1/stream/simulator/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "isRunning" in data
    assert "isPaused" in data
    assert "ticksCount" in data
    assert "intervalSec" in data
    assert data["sourceMode"] in ("SIMULATION", "REPLAY")

    initial_ticks = data["ticksCount"]

    # 2. Pause
    pause_resp = client.post("/api/v1/stream/simulator/control", json={"action": "pause"})
    assert pause_resp.status_code == 200
    assert pause_resp.json()["isPaused"] is True

    # 3. Resume
    resume_resp = client.post("/api/v1/stream/simulator/control", json={"action": "resume"})
    assert resume_resp.status_code == 200
    assert resume_resp.json()["isPaused"] is False

    # 4. Trigger manual tick
    tick_resp = client.post("/api/v1/stream/simulator/control", json={"action": "tick_once"})
    assert tick_resp.status_code == 200
    assert tick_resp.json()["ticksCount"] >= initial_ticks + 1

    # 5. Set interval
    int_resp = client.post("/api/v1/stream/simulator/control", json={"action": "set_interval", "interval_sec": 8.0})
    assert int_resp.status_code == 200
    assert int_resp.json()["intervalSec"] == 8.0

    # Reset back to 5.0
    client.post("/api/v1/stream/simulator/control", json={"action": "set_interval", "interval_sec": 5.0})


def test_health_reports_streamer_and_tables(client):
    """Verifies /api/v1/health exposes streamer diagnostics and 19 tables."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()

    subsystems = data["subsystems"]
    assert subsystems["database"] is True
    assert subsystems["databaseTablesCount"] >= 19
    assert "telemetryStreamerActive" in subsystems
    assert "telemetryStreamerTicks" in subsystems
    assert subsystems["telemetryStreamerTicks"] >= 0
