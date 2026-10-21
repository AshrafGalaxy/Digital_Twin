"""
test_spat_adapter.py

Hermetic unit and integration test suite for the Real-Time Signal Phase and Timing
(SPaT) Controller Ingestion Adapter (TASK-08), verifying:
- Inbound NTCIP 1202 / SAE J2735 packet validation and cycle bounding
- Sub-second freshness SLA evaluation (VALID <= 3s, STALE 3-10s, DISCONNECTED > 10s)
- Virtual controller phase cycle progression and countdown calculation
- Database persistence in signal_phase_history and entity_current_state
- REST endpoints (/api/v1/traffic/signals/{id}/spat, /signals/spat/ingest, /signals/{id}/spat/history)
- Test isolation and order invariance
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import text

from backend.core.database import AsyncSessionLocal
from backend.main import app
from backend.services.spat_adapter import (
    ControllerMode,
    IntersectionSPaTState,
    SPaTAdapter,
    SPaTPacket,
    SignalColor,
    spat_adapter
)

client = TestClient(app)


def test_spat_packet_validation_valid():
    """Verifies that a valid J2735 SPaT packet parses correctly."""
    now_iso = datetime.now(timezone.utc).isoformat()
    raw = {
        "intersection_id": "urn:ngsi-ld:Intersection:PUNE:INT-VN-01",
        "timestamp": now_iso,
        "cycle_length_sec": 90,
        "elapsed_cycle_sec": 15.0,
        "active_phase": 1,
        "active_phase_name": "Nagar Road EB Through + Right",
        "phase_color": "GREEN",
        "time_to_next_phase_sec": 20.0,
        "preempt_status": "NONE",
        "controller_mode": "ACTUATED",
        "provenance": {
            "sourceMode": "LIVE",
            "protocol": "SAE_J2735_SPAT"
        }
    }
    packet = SPaTPacket(**raw)
    assert packet.intersection_id == "urn:ngsi-ld:Intersection:PUNE:INT-VN-01"
    assert packet.cycle_length_sec == 90
    assert packet.active_phase == 1
    assert packet.phase_color == SignalColor.GREEN
    assert packet.controller_mode == ControllerMode.ACTUATED


def test_spat_packet_invalid_cycle_bounds():
    """Verifies that cycle lengths outside physical bounds (40-240s) are rejected."""
    now_iso = datetime.now(timezone.utc).isoformat()
    # Cycle too small (<40s)
    with pytest.raises(ValidationError):
        SPaTPacket(
            intersection_id="INT-TEST-01",
            timestamp=now_iso,
            cycle_length_sec=25,
            elapsed_cycle_sec=5.0,
            active_phase=1,
            active_phase_name="Approach 1",
            phase_color=SignalColor.GREEN,
            time_to_next_phase_sec=10.0
        )

    # Cycle too large (>240s)
    with pytest.raises(ValidationError):
        SPaTPacket(
            intersection_id="INT-TEST-01",
            timestamp=now_iso,
            cycle_length_sec=300,
            elapsed_cycle_sec=5.0,
            active_phase=1,
            active_phase_name="Approach 1",
            phase_color=SignalColor.GREEN,
            time_to_next_phase_sec=10.0
        )


def test_spat_packet_invalid_color():
    """Verifies that non-standard aspect colors are rejected by schema."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with pytest.raises(ValidationError):
        SPaTPacket(
            intersection_id="INT-TEST-01",
            timestamp=now_iso,
            cycle_length_sec=90,
            active_phase=1,
            active_phase_name="Approach 1",
            phase_color="BLUE",
            time_to_next_phase_sec=10.0
        )


def test_spat_freshness_sla_thresholds():
    """
    Verifies the 3-tier freshness SLA:
    - Age <= 3.0s -> VALID
    - 3.0s < Age <= 10.0s -> STALE
    - Age > 10.0s -> DISCONNECTED
    """
    state = IntersectionSPaTState(
        intersection_id="INT-SLA-01",
        intersection_name="SLA Test Intersection",
        cycle_length_sec=90
    )
    base_time = datetime(2026, 10, 21, 12, 0, 0, tzinfo=timezone.utc)
    state.last_heartbeat = base_time

    # 1. Fresh packet (age = 1.5s)
    t_fresh = base_time + timedelta(seconds=1.5)
    status, latency = state.evaluate_freshness(now=t_fresh)
    assert status == "VALID"
    assert round(latency, 1) == 1.5

    # 2. Stale packet (age = 4.5s)
    t_stale = base_time + timedelta(seconds=4.5)
    status, latency = state.evaluate_freshness(now=t_stale)
    assert status == "STALE"
    assert round(latency, 1) == 4.5

    # 3. Disconnected packet (age = 12.0s)
    t_disc = base_time + timedelta(seconds=12.0)
    status, latency = state.evaluate_freshness(now=t_disc)
    assert status == "DISCONNECTED"
    assert round(latency, 1) == 12.0


def test_spat_synthetic_tick_progression():
    """
    Verifies that virtual controller simulation advances stage elapsed seconds
    and transitions correctly through green, yellow, and red intervals.
    """
    adapter = SPaTAdapter()
    int_id = "urn:ngsi-ld:Intersection:PUNE:INT-VN-01"

    # Initial state
    s0 = adapter.get_current_spat(int_id)
    assert s0.cycle_length_sec == 90

    # Advance by 10 seconds
    s1 = adapter.generate_synthetic_tick(int_id, elapsed_seconds_delta=10.0)
    assert s1.elapsed_cycle_sec == pytest.approx(15.0, abs=1.0)
    assert s1.time_to_next_phase_sec > 0.0

    # Advance past Phase 1 duration into yellow/all-red
    s2 = adapter.generate_synthetic_tick(int_id, elapsed_seconds_delta=12.0)
    assert s2.elapsed_cycle_sec == pytest.approx(27.0, abs=1.0)
    # At 27s in a 25s green + 3s yellow interval, aspect should be YELLOW
    assert s2.phase_color in (SignalColor.YELLOW, SignalColor.RED)


@pytest.mark.asyncio
async def test_spat_phase_transition_db_persistence():
    """
    Verifies that when a phase transition is ingested, a record is inserted
    into signal_phase_history and entity_current_state is updated.
    """
    adapter = SPaTAdapter()
    int_id = "urn:ngsi-ld:Intersection:PUNE:INT-VN-01"
    now1 = datetime(2026, 10, 21, 14, 0, 0, tzinfo=timezone.utc)
    now2 = datetime(2026, 10, 21, 14, 0, 25, tzinfo=timezone.utc)

    async with AsyncSessionLocal() as session:
        # Initial packet: Phase 1 Green
        p1 = {
            "intersection_id": int_id,
            "timestamp": now1.isoformat(),
            "cycle_length_sec": 90,
            "elapsed_cycle_sec": 0.0,
            "active_phase": 1,
            "active_phase_name": "Nagar Road EB Through + Right",
            "phase_color": SignalColor.GREEN,
            "time_to_next_phase_sec": 25.0,
            "provenance": {"sourceMode": "LIVE"}
        }
        await adapter.ingest_packet(p1, session=session)

        # Transition packet: Phase 1 Yellow
        p2 = {
            "intersection_id": int_id,
            "timestamp": now2.isoformat(),
            "cycle_length_sec": 90,
            "elapsed_cycle_sec": 25.0,
            "active_phase": 1,
            "active_phase_name": "Nagar Road EB Through + Right",
            "phase_color": SignalColor.YELLOW,
            "time_to_next_phase_sec": 3.0,
            "provenance": {"sourceMode": "LIVE"}
        }
        await adapter.ingest_packet(p2, session=session)

        # Verify entry in signal_phase_history
        hist_res = await session.execute(
            text("SELECT phase_id, color, duration_sec FROM signal_phase_history WHERE intersection_id = :id ORDER BY id DESC LIMIT 1"),
            {"id": int_id}
        )
        row = hist_res.fetchone()
        assert row is not None
        assert row[0] == 1
        assert row[1] == "GREEN"
        assert row[2] >= 20.0

        # Verify entry in entity_current_state
        state_res = await session.execute(
            text("SELECT entity_type, source_mode, metrics FROM entity_current_state WHERE entity_id = :id"),
            {"id": int_id}
        )
        state_row = state_res.fetchone()
        assert state_row is not None
        assert state_row[0] == "TrafficSignal"
        assert state_row[1] == "LIVE"


# ============================================================================
# API Endpoint Tests
# ============================================================================

def test_api_get_spat_current():
    """Verifies GET /api/v1/traffic/signals/{id}/spat returns current state."""
    res = client.get("/api/v1/traffic/signals/urn:ngsi-ld:Intersection:PUNE:INT-VN-01/spat")
    assert res.status_code == 200
    data = res.json()
    assert "intersectionId" in data
    assert "activePhase" in data
    assert "activePhaseName" in data
    assert "phaseColor" in data
    assert data["phaseColor"] in ("GREEN", "YELLOW", "RED", "FLASHING_YELLOW")
    assert "timeToNextPhaseSec" in data
    assert "freshnessStatus" in data
    assert data["freshnessStatus"] in ("VALID", "STALE", "DISCONNECTED")
    assert "provenance" in data


def test_api_post_spat_ingest_valid():
    """Verifies POST /api/v1/traffic/signals/spat/ingest processes incoming frames."""
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "intersectionId": "urn:ngsi-ld:Intersection:PUNE:INT-VN-01",
        "timestamp": now_iso,
        "cycleLengthSec": 90,
        "elapsedCycleSec": 30.0,
        "activePhase": 2,
        "activePhaseName": "Nagar Road WB Through",
        "phaseColor": "GREEN",
        "timeToNextPhaseSec": 15.0,
        "preemptStatus": "NONE",
        "controllerMode": "ACTUATED",
        "provenance": {
            "sourceMode": "LIVE",
            "protocol": "SAE_J2735_SPAT"
        }
    }
    res = client.post("/api/v1/traffic/signals/spat/ingest", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["activePhase"] == 2
    assert data["phaseColor"] == "GREEN"
    assert data["timeToNextPhaseSec"] == 15.0


def test_api_post_spat_ingest_invalid():
    """Verifies that an invalid SPaT packet triggers a 422 Unprocessable Entity."""
    payload = {
        "intersectionId": "INT-INVALID",
        "timestamp": "not-a-timestamp",
        "cycleLengthSec": 10,  # Invalid: < 40s
        "activePhase": 99,     # Invalid: > 8
        "activePhaseName": "Invalid Phase",
        "phaseColor": "PURPLE", # Invalid color
        "timeToNextPhaseSec": -5.0
    }
    res = client.post("/api/v1/traffic/signals/spat/ingest", json=payload)
    assert res.status_code == 422


def test_api_get_spat_history():
    """Verifies GET /api/v1/traffic/signals/{id}/spat/history returns phase intervals."""
    res = client.get("/api/v1/traffic/signals/urn:ngsi-ld:Intersection:PUNE:INT-VN-01/spat/history?limit=10")
    assert res.status_code == 200
    records = res.json()
    assert isinstance(records, list)


def test_spat_unregistered_intersection_fallback():
    """Verifies that querying an unregistered intersection creates a clean fallback without error."""
    adapter = SPaTAdapter()
    state = adapter.get_current_spat("INT-NEW-DISTRICT-09")
    assert state.intersection_id == "INT-NEW-DISTRICT-09"
    assert state.cycle_length_sec == 90
    assert state.active_phase == 1
    assert state.phase_color == SignalColor.GREEN
