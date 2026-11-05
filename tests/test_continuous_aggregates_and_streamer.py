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
import random
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.main import app
from backend.core.database import persistence_manager, get_db_session
from backend.core.schema_migrator import init_db_schema
from backend.ingestion.telemetry_streamer import (
    CORRIDOR_SEGMENTS,
    compute_link_kinematics,
    telemetry_streamer,
)
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


def test_high_demand_kinematics_emit_spillback_above_storage():
    """A blocked high-demand approach can queue past its storage. Speed and flow are not floored."""
    segment = next(item for item in CORRIDOR_SEGMENTS if item["id"].endswith("SEG-NR-EB-01"))
    storage = segment["approachStorageMeters"]
    assert storage >= 200.0

    row = compute_link_kinematics(
        speed_limit_kmh=segment["speedLimit"],
        base_speed_kmh=segment["baseSpeed"],
        capacity_vph=segment["capacity"],
        approach_storage_m=storage,
        rush_intensity=1.0,
        speed_jitter=0.0,
        flow_jitter=0.0,
        demand_vph=2880.0,
        discharge_vph=150.0,
    )

    assert row["queueLengthMeters"] > 200.0
    assert row["queueLengthMeters"] > storage
    assert row["spillbackMeters"] > 0.0
    assert 0.0 <= row["averageSpeedKmh"] < 14.0
    assert row["averageSpeedKmh"] <= 120.0
    assert 0.0 <= row["vehicleFlowPerHour"] < 400.0


@pytest.mark.asyncio
async def test_peak_tick_persists_simulation_spillback():
    """A peak-hour generated tick stays SIMULATION and can store a queue above 200 m."""
    peak = datetime(2026, 6, 15, 18, 30, tzinfo=timezone.utc)
    tick_res = await telemetry_streamer.tick_once(now=peak, rng=random.Random(42))

    assert tick_res["status"] == "TICK_SUCCESS"
    assert telemetry_streamer.mode == "SIMULATION"

    async with persistence_manager.session_factory() as session:
        result = await session.execute(
            text("""
                SELECT average_speed_kmh, vehicle_flow_per_hour, queue_length_meters, source_mode
                FROM traffic_observations
                WHERE observed_at = :observed_at
            """),
            {"observed_at": peak},
        )
        rows = result.fetchall()

    assert len(rows) >= 10
    assert all(row.source_mode == "SIMULATION" for row in rows)
    assert all(0.0 <= float(row.average_speed_kmh) <= 120.0 for row in rows)
    assert max(float(row.queue_length_meters) for row in rows) > 200.0
    assert min(float(row.average_speed_kmh) for row in rows) < 14.0
    assert min(float(row.vehicle_flow_per_hour) for row in rows) < 400.0


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

@pytest.mark.asyncio
async def test_simulation_tick_does_not_overwrite_observed_current_state():
    """
    Verifies Non-Negotiable Invariant #2 (State Separation Invariant):
    A seeded LIVE or REPLAY current-state row in entity_current_state must survive
    telemetry_streamer.tick_once() with its source_mode, speed, and queue length untouched.
    Simulations must still record their time-series rows into history tables with honest
    tier-0 synthetic quality score (0.70).
    """
    import json

    seg_id = "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01"
    bld_id = "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01"
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        # 1. Seed a LIVE road segment and a LIVE building into entity_current_state
        async with persistence_manager.session_factory() as session:
            live_seg_metrics = {
                "averageSpeedKmh": 6.5,
                "vehicleFlowPerHour": 450.0,
                "occupancyPercent": 85.0,
                "queueLengthMeters": 420.0,
                "congestionIndex": 0.87
            }
            await session.execute(
                text("""
                    INSERT INTO entity_current_state (
                        entity_id, entity_type, source_mode, observed_at, updated_at,
                        metrics, quality_status, freshness_seconds
                    ) VALUES (
                        :entity_id, :entity_type, :source_mode, :observed_at, :updated_at,
                        :metrics, :quality_status, :freshness_seconds
                    ) ON CONFLICT(entity_id) DO UPDATE SET
                        source_mode = EXCLUDED.source_mode,
                        observed_at = EXCLUDED.observed_at,
                        updated_at = EXCLUDED.updated_at,
                        metrics = EXCLUDED.metrics,
                        quality_status = EXCLUDED.quality_status,
                        freshness_seconds = EXCLUDED.freshness_seconds
                """),
                {
                    "entity_id": seg_id,
                    "entity_type": "RoadSegment",
                    "source_mode": "LIVE",
                    "observed_at": now_iso,
                    "updated_at": now_iso,
                    "metrics": json.dumps(live_seg_metrics),
                    "quality_status": "VALID",
                    "freshness_seconds": 0.0,
                }
            )

            live_bld_metrics = {
                "activePowerKw": 3333.0,
                "reactivePowerKvar": 1050.0,
                "powerFactor": 0.95,
                "energyConsumptionKwh": 80000.0
            }
            await session.execute(
                text("""
                    INSERT INTO entity_current_state (
                        entity_id, entity_type, source_mode, observed_at, updated_at,
                        metrics, quality_status, freshness_seconds
                    ) VALUES (
                        :entity_id, :entity_type, :source_mode, :observed_at, :updated_at,
                        :metrics, :quality_status, :freshness_seconds
                    ) ON CONFLICT(entity_id) DO UPDATE SET
                        source_mode = EXCLUDED.source_mode,
                        observed_at = EXCLUDED.observed_at,
                        updated_at = EXCLUDED.updated_at,
                        metrics = EXCLUDED.metrics,
                        quality_status = EXCLUDED.quality_status,
                        freshness_seconds = EXCLUDED.freshness_seconds
                """),
                {
                    "entity_id": bld_id,
                    "entity_type": "Building",
                    "source_mode": "LIVE",
                    "observed_at": now_iso,
                    "updated_at": now_iso,
                    "metrics": json.dumps(live_bld_metrics),
                    "quality_status": "VALID",
                    "freshness_seconds": 0.0,
                }
            )
            await session.commit()

        # 2. Trigger streamer tick in SIMULATION mode
        assert telemetry_streamer.mode == "SIMULATION"
        tick_res = await telemetry_streamer.tick_once()
        assert tick_res["status"] == "TICK_SUCCESS"

        # 3. Verify entity_current_state was NOT overwritten by simulation
        async with persistence_manager.session_factory() as session:
            seg_row = (await session.execute(
                text("SELECT source_mode, metrics, quality_status FROM entity_current_state WHERE entity_id = :id"),
                {"id": seg_id}
            )).fetchone()
            assert seg_row is not None
            assert seg_row[0] == "LIVE"
            seg_metrics = json.loads(seg_row[1]) if isinstance(seg_row[1], str) else seg_row[1]
            assert seg_metrics["averageSpeedKmh"] == 6.5
            assert seg_metrics["queueLengthMeters"] == 420.0

            bld_row = (await session.execute(
                text("SELECT source_mode, metrics FROM entity_current_state WHERE entity_id = :id"),
                {"id": bld_id}
            )).fetchone()
            assert bld_row is not None
            assert bld_row[0] == "LIVE"
            bld_metrics = json.loads(bld_row[1]) if isinstance(bld_row[1], str) else bld_row[1]
            assert bld_metrics["activePowerKw"] == 3333.0

            # 4. Verify historical tables DID receive SIMULATION observation with honest quality score
            sim_obs = (await session.execute(
                text("SELECT source_mode, average_speed_kmh FROM traffic_observations WHERE segment_id = :id ORDER BY observed_at DESC LIMIT 1"),
                {"id": seg_id}
            )).fetchone()
            assert sim_obs is not None
            assert sim_obs[0] == "SIMULATION"

            sim_los = (await session.execute(
                text("SELECT source_mode, quality_score FROM segment_los_history WHERE segment_id = :id ORDER BY observed_at DESC LIMIT 1"),
                {"id": seg_id}
            )).fetchone()
            assert sim_los is not None
            assert sim_los[0] == "SIMULATION"
            assert sim_los[1] == 0.70
    finally:
        # Hermetic order-invariance: restore pristine REPLAY state for SEG-NR-EB-01
        async with persistence_manager.session_factory() as session:
            await session.execute(
                text("""
                    UPDATE entity_current_state
                    SET source_mode = 'REPLAY',
                        metrics = :metrics
                    WHERE entity_id = :id
                """),
                {
                    "id": seg_id,
                    "metrics": json.dumps({
                        "averageSpeedKmh": 42.5,
                        "vehicleFlowPerHour": 1820.0,
                        "occupancyPercent": 32.0,
                        "queueLengthMeters": 15.0,
                        "congestionIndex": 0.35
                    })
                }
            )
            await session.commit()

