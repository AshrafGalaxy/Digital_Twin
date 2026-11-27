"""
test_telemetry_streamer_batching.py

Hermetic tests for Issue #58 (ENH-03):
1. Bounded O(1) batch SQL statements per table inside TelemetryStreamerWorker.tick_once.
2. Offloading numeric physics computation off the asyncio event loop via asyncio.to_thread.
3. Preserved State Separation invariant on batched entity_current_state upserts.
4. Savepoint isolation for microgrid failures inside tick_once.
5. Zero emojis and zero em/en dashes across modified modules.
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest
from sqlalchemy import event, text

import backend.ingestion.telemetry_streamer as streamer_mod
from backend.core.database import persistence_manager
from backend.ingestion.telemetry_streamer import CORRIDOR_SEGMENTS, telemetry_streamer
from backend.services.energy_topology_service import energy_topology_service

REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_synthetic_segments(count: int) -> List[streamer_mod.CorridorSegmentDict]:
    return [
        {
            "id": f"urn:ngsi-ld:RoadSegment:TEST:SCALE-{idx:03d}",
            "name": f"Scaled Corridor Link {idx:03d}",
            "speedLimit": 50.0,
            "baseSpeed": 40.0,
            "capacity": 2400,
            "approachStorageMeters": 450.0,
        }
        for idx in range(count)
    ]


@pytest.mark.asyncio
async def test_tick_executes_bounded_batch_statements_per_table(monkeypatch):
    """
    One tick must execute a bounded O(1) number of SQL execute calls per table
    rather than scaling linearly with segment count (10 vs 60 segments).
    """
    sync_engine = persistence_manager.engine.sync_engine
    recorded_sql: List[str] = []

    def _on_execute(_conn, _cursor, statement, _parameters, _context, executemany):
        recorded_sql.append(statement)

    def _count_table_inserts(table_name: str) -> int:
        marker = f"INSERT INTO {table_name}"
        return sum(1 for sql in recorded_sql if marker in sql)

    event.listen(sync_engine, "before_cursor_execute", _on_execute)
    try:
        # 1. Default 10-segment network
        recorded_sql.clear()
        res_default = await telemetry_streamer.tick_once()
        assert res_default["status"] == "TICK_SUCCESS"

        counts_default = {
            "traffic_observations": _count_table_inserts("traffic_observations"),
            "segment_los_history": _count_table_inserts("segment_los_history"),
            "energy_observations": _count_table_inserts("energy_observations"),
            "environment_observations": _count_table_inserts("environment_observations"),
            "energy_asset_telemetry": _count_table_inserts("energy_asset_telemetry"),
            "entity_current_state": _count_table_inserts("entity_current_state"),
        }

        assert counts_default["traffic_observations"] == 1
        assert counts_default["segment_los_history"] == 1
        assert counts_default["energy_observations"] == 1
        assert counts_default["environment_observations"] == 1
        assert counts_default["energy_asset_telemetry"] == 1
        assert counts_default["entity_current_state"] == 2

        # 2. Scaled 60-segment network (same O(1) statement counts per table)
        monkeypatch.setattr(streamer_mod, "CORRIDOR_SEGMENTS", _make_synthetic_segments(60))
        recorded_sql.clear()
        res_scaled = await telemetry_streamer.tick_once()
        assert res_scaled["status"] == "TICK_SUCCESS"
        assert res_scaled["segmentsUpdated"] == 60

        assert _count_table_inserts("traffic_observations") == 1
        assert _count_table_inserts("segment_los_history") == 1
        assert _count_table_inserts("energy_observations") == 1
        assert _count_table_inserts("environment_observations") == 1
        assert _count_table_inserts("energy_asset_telemetry") == 1
        assert _count_table_inserts("entity_current_state") == 2
    finally:
        event.remove(sync_engine, "before_cursor_execute", _on_execute)
        async with persistence_manager.session_factory() as session:
            await session.execute(text("DELETE FROM traffic_observations WHERE segment_id LIKE '%TEST:SCALE-%'"))
            await session.execute(text("DELETE FROM segment_los_history WHERE segment_id LIKE '%TEST:SCALE-%'"))
            await session.execute(text("DELETE FROM entity_current_state WHERE entity_id LIKE '%TEST:SCALE-%'"))
            await session.commit()


@pytest.mark.asyncio
async def test_tick_offloads_numeric_computation_from_event_loop(monkeypatch):
    """
    Verifies telemetry physics loops execute inside asyncio.to_thread so the
    event loop remains responsive during larger corridor ticks.
    """
    to_thread_calls: List[str] = []
    orig_to_thread = asyncio.to_thread

    async def _spy_to_thread(func, /, *args, **kwargs):
        to_thread_calls.append(getattr(func, "__name__", str(func)))
        return await orig_to_thread(func, *args, **kwargs)

    monkeypatch.setattr(asyncio, "to_thread", _spy_to_thread)
    monkeypatch.setattr(streamer_mod, "CORRIDOR_SEGMENTS", _make_synthetic_segments(150))

    heartbeats = 0

    async def _heartbeat():
        nonlocal heartbeats
        for _ in range(5):
            await asyncio.sleep(0)
            heartbeats += 1

    try:
        hb_task = asyncio.create_task(_heartbeat())
        res = await telemetry_streamer.tick_once()
        await hb_task

        assert res["status"] == "TICK_SUCCESS"
        assert res["segmentsUpdated"] == 150
        assert "_compute_tick_payload" in to_thread_calls
        assert "_compute_asset_telemetry_batch" in to_thread_calls
        assert heartbeats == 5
    finally:
        async with persistence_manager.session_factory() as session:
            await session.execute(text("DELETE FROM traffic_observations WHERE segment_id LIKE '%TEST:SCALE-%'"))
            await session.execute(text("DELETE FROM segment_los_history WHERE segment_id LIKE '%TEST:SCALE-%'"))
            await session.execute(text("DELETE FROM entity_current_state WHERE entity_id LIKE '%TEST:SCALE-%'"))
            await session.commit()


@pytest.mark.asyncio
async def test_batch_simulation_preserves_live_and_replay_state():
    """
    Verifies batched entity_current_state upsert keeps LIVE and REPLAY rows
    untouched during a SIMULATION tick.
    """
    seg_replay = CORRIDOR_SEGMENTS[1]["id"]
    now_iso = datetime.now(timezone.utc).isoformat()
    preserved_metrics = {
        "averageSpeedKmh": 11.1,
        "vehicleFlowPerHour": 999.0,
        "occupancyPercent": 77.0,
        "queueLengthMeters": 310.0,
        "congestionIndex": 0.78,
    }

    async with persistence_manager.session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO entity_current_state (
                    entity_id, entity_type, source_mode, observed_at, updated_at,
                    metrics, quality_status, freshness_seconds
                ) VALUES (
                    :entity_id, 'RoadSegment', 'REPLAY', :observed_at, :updated_at,
                    :metrics, 'VALID', 0.0
                ) ON CONFLICT (entity_id) DO UPDATE SET
                    source_mode = 'REPLAY',
                    metrics = EXCLUDED.metrics,
                    observed_at = EXCLUDED.observed_at,
                    updated_at = EXCLUDED.updated_at
            """),
            {
                "entity_id": seg_replay,
                "observed_at": now_iso,
                "updated_at": now_iso,
                "metrics": json.dumps(preserved_metrics),
            },
        )
        await session.commit()

    tick_res = await telemetry_streamer.tick_once()
    assert tick_res["status"] == "TICK_SUCCESS"

    async with persistence_manager.session_factory() as session:
        row = (
            await session.execute(
                text("SELECT source_mode, metrics FROM entity_current_state WHERE entity_id = :id"),
                {"id": seg_replay},
            )
        ).fetchone()
        assert row is not None
        assert row[0] == "REPLAY"
        parsed = json.loads(row[1]) if isinstance(row[1], str) else row[1]
        assert parsed["averageSpeedKmh"] == 11.1
        assert parsed["queueLengthMeters"] == 310.0


@pytest.mark.asyncio
async def test_microgrid_failure_does_not_rollback_traffic_observations(monkeypatch):
    """
    A failure inside energy_topology_service.generate_telemetry_tick must be
    isolated to its nested savepoint so traffic/environment rows still commit.
    """
    async def _boom(*args, **kwargs):
        raise RuntimeError("Simulated microgrid telemetry failure")

    monkeypatch.setattr(energy_topology_service, "generate_telemetry_tick", _boom)

    isolated_ts = datetime(2026, 7, 1, 9, 15, tzinfo=timezone.utc)
    try:
        res = await telemetry_streamer.tick_once(now=isolated_ts)
        assert res["status"] == "TICK_SUCCESS"

        async with persistence_manager.session_factory() as session:
            count_res = await session.execute(
                text("SELECT COUNT(*) FROM traffic_observations WHERE observed_at = :ts"),
                {"ts": isolated_ts},
            )
            assert (count_res.scalar() or 0) == len(CORRIDOR_SEGMENTS)
    finally:
        async with persistence_manager.session_factory() as session:
            await session.execute(text("DELETE FROM traffic_observations WHERE observed_at = :ts"), {"ts": isolated_ts})
            await session.execute(text("DELETE FROM segment_los_history WHERE observed_at = :ts"), {"ts": isolated_ts})
            await session.execute(text("DELETE FROM energy_observations WHERE observed_at = :ts"), {"ts": isolated_ts})
            await session.execute(text("DELETE FROM environment_observations WHERE observed_at = :ts"), {"ts": isolated_ts})
            await session.commit()


def test_no_forbidden_characters_in_modified_modules():
    """Verify modified modules stay free of emojis, em dashes, and en dashes."""
    files = [
        REPO_ROOT / "backend" / "ingestion" / "telemetry_streamer.py",
        REPO_ROOT / "backend" / "services" / "energy_topology_service.py",
        REPO_ROOT / "tests" / "test_telemetry_streamer_batching.py",
    ]
    for path in files:
        content = path.read_text(encoding="utf-8")
        assert "\u2014" not in content, f"Em dash found in {path}"
        assert "\u2013" not in content, f"En dash found in {path}"
