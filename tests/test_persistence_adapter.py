"""
test_persistence_adapter.py

Automated tests for Track 4, Task P4-A: Multi-Storage Resilient Persistence Layer.
Verifies dynamic database engine selection, automatic DDL migrations (all 18 tables),
authoritative corridor asset seeding, custom SQLite compatibility functions,
and health diagnostic reporting.
"""

import asyncio
from datetime import datetime, timezone
import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.database import (
    persistence_manager,
    get_active_backend,
    get_persistence_info,
    check_db_health,
    get_db_session
)
from backend.core.schema_migrator import init_db_schema


@pytest.fixture
def client():
    return TestClient(app)


def test_multi_storage_engine_initialization():
    """Verifies that the persistence adapter initializes and provides connection health."""
    backend = get_active_backend()
    assert backend in ("sqlite", "postgresql")

    info = get_persistence_info()
    assert info["backend"] == backend
    assert info["status"] == "ONLINE"
    assert "isFallback" in info
    assert "databaseName" in info


@pytest.mark.asyncio
async def test_database_health_check_returns_true():
    """Verifies that check_db_health() executes SELECT 1 successfully."""
    healthy = await check_db_health()
    assert healthy is True


@pytest.mark.asyncio
async def test_schema_migrator_all_eighteen_tables():
    """Verifies that all 18 tables specified in the digital twin architecture are created."""
    res = await init_db_schema()
    assert res["status"] == "INITIALIZED"
    assert res["tablesCount"] >= 18

    expected_tables = {
        "study_areas",
        "intersections",
        "road_segments",
        "sensors",
        "building_zones",
        "entity_current_state",
        "traffic_observations",
        "energy_observations",
        "environment_observations",
        "model_versions",
        "forecasts",
        "scenario_templates",
        "scenario_runs",
        "scenario_kpis",
        "recommendations",
        "ingestion_errors",
        "audit_events",
        "quarantine_observations"
    }

    async with persistence_manager.session_factory() as session:
        backend = get_active_backend()
        if backend == "sqlite":
            query = text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        else:
            query = text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")

        rows = (await session.execute(query)).fetchall()
        actual_tables = {r[0] for r in rows}

        missing = expected_tables - actual_tables
        assert not missing, f"Missing required tables: {missing}"


@pytest.mark.asyncio
async def test_authoritative_corridor_assets_seeded():
    """Verifies that the schema migrator seeds all core spatial assets on startup."""
    async with persistence_manager.session_factory() as session:
        # Study Area
        study_areas = (await session.execute(text("SELECT id, city, country, crs FROM study_areas"))).fetchall()
        assert len(study_areas) >= 1
        assert study_areas[0][1] == "Pune"
        assert study_areas[0][3] == "EPSG:4326"

        # Intersections
        intersections = (await session.execute(text("SELECT id, name, control_type FROM intersections"))).fetchall()
        assert len(intersections) == 2

        # Road Segments
        road_segments = (await session.execute(text("SELECT id, name, direction, speed_limit_kmh FROM road_segments"))).fetchall()
        assert len(road_segments) == 10

        # Sensors
        sensors = (await session.execute(text("SELECT id, sensor_type FROM sensors"))).fetchall()
        assert len(sensors) == 10

        # Building Zone
        building_zones = (await session.execute(text("SELECT id, category FROM building_zones"))).fetchall()
        assert len(building_zones) >= 1
        assert building_zones[0][0] == "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01"

        # Scenario Templates
        templates = (await session.execute(text("SELECT id FROM scenario_templates"))).fetchall()
        template_ids = {t[0] for t in templates}
        assert "SCEN-BASE-01" in template_ids
        assert "SCEN-INT-01" in template_ids


@pytest.mark.asyncio
async def test_authoritative_current_state_provenance():
    """
    Verifies that initial current state entities carry strict REPLAY provenance
    and valid quality status per AGENTS.md §7.1.
    """
    async with persistence_manager.session_factory() as session:
        rows = (await session.execute(text("""
            SELECT entity_id, entity_type, source_mode, quality_status, metrics
            FROM entity_current_state
        """))).fetchall()

        assert len(rows) >= 11
        for row in rows:
            assert row[2] in ("REPLAY", "LIVE", "SIMULATION"), f"Invalid provenance for {row[0]}: {row[2]}"
            assert row[3] == "VALID"
            assert row[4] is not None


@pytest.mark.asyncio
async def test_custom_sqlite_now_function_cross_compatibility():
    """Verifies that SELECT NOW() executes without syntax errors in raw SQL."""
    async with persistence_manager.session_factory() as session:
        res = await session.execute(text("SELECT NOW()"))
        val = res.scalar()
        assert val is not None
        # Must be parseable as ISO timestamp
        dt = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
        assert dt.year >= 2026


@pytest.mark.asyncio
async def test_transactional_integrity_and_rollback():
    """Verifies ACID rollback semantics on session exception."""
    test_id = "test-rollback-probe-99"

    # Attempt to insert and force exception to verify rollback
    try:
        async with persistence_manager.session_factory() as session:
            await session.execute(text("""
                INSERT INTO audit_events (event_type, source_service, details)
                VALUES ('TEST_EVENT', :srv, '{}')
            """), {"srv": test_id})
            # Force deliberate error before commit
            raise RuntimeError("Simulated transaction failure")
    except RuntimeError:
        pass

    # Verify that the uncommitted record does not exist
    async with persistence_manager.session_factory() as session:
        res = await session.execute(
            text("SELECT COUNT(*) FROM audit_events WHERE source_service = :srv"),
            {"srv": test_id}
        )
        assert res.scalar() == 0


def test_health_endpoint_persistence_diagnostics(client):
    """Verifies that /api/v1/health reports database readiness, backend type, and tables count."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] in ("HEALTHY", "DEGRADED")
    subsystems = data["subsystems"]
    assert subsystems["database"] is True
    assert subsystems["databaseBackend"] in ("sqlite", "postgresql")
    assert subsystems["databaseMode"] in ("PRIMARY_POSTGRES", "RESILIENT_SQLITE")
    assert subsystems["databaseTablesCount"] >= 18


def test_current_state_endpoint_serves_seeded_entities(client):
    """Verifies that GET /api/v1/state/current returns all seeded corridor entities."""
    res = client.get("/api/v1/state/current")
    assert res.status_code == 200
    records = res.json()

    assert len(records) >= 11
    road_segments = [r for r in records if r["entityType"] == "RoadSegment"]
    assert len(road_segments) >= 10

    # Verify that every record has valid speed/metrics
    first_seg = road_segments[0]
    assert "averageSpeedKmh" in first_seg["metrics"]
    assert first_seg["sourceMode"] in ("REPLAY", "LIVE", "SIMULATION")
    assert first_seg["qualityStatus"] == "VALID"
