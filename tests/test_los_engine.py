"""
test_los_engine.py

Comprehensive hermetic test suite for the Canonical Level of Service (LOS)
and Hydrodynamic State Engine, covering:
- Hydrodynamic continuity equations (q = k * v, V/C ratio, density, CI)
- Zero-division resilience and boundary conditions
- Dual criteria worse-grade selection policy
- Pluggable policy standards (Indo-HCM / IRC:106 vs US HCM 6th Edition)
- FastAPI REST endpoints (/traffic/policies, /traffic/corridor/los, /traffic/segment/{id}/los)
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.los_engine import (
    LOSEngine,
    PolicyStandard,
    INDO_HCM_THRESHOLDS,
    US_HCM_THRESHOLDS,
    los_engine
)

client = TestClient(app)


def test_hydrodynamics_free_flow():
    """Verifies hydrodynamic calculations under free-flow conditions."""
    engine = LOSEngine()
    res = engine.compute_hydrodynamics(
        speed_kmh=48.0,
        flow_vph=720.0,
        capacity_vph=2400.0,
        free_flow_speed_kmh=50.0
    )
    assert res["volume_capacity_ratio"] == 0.3
    assert res["density_veh_km"] == 15.0
    assert res["speed_ratio"] == 0.96
    assert res["congestion_index"] == 0.04


def test_hydrodynamics_congested():
    """Verifies hydrodynamic calculations under high-demand congested conditions."""
    engine = LOSEngine()
    res = engine.compute_hydrodynamics(
        speed_kmh=15.0,
        flow_vph=2100.0,
        capacity_vph=2400.0,
        free_flow_speed_kmh=50.0
    )
    assert res["volume_capacity_ratio"] == 0.875
    assert res["density_veh_km"] == 140.0
    assert res["speed_ratio"] == 0.3
    assert res["congestion_index"] == 0.7


def test_hydrodynamics_zero_speed_boundary():
    """A stopped speed is labeled STOPPED and density stays within jam density."""
    engine = LOSEngine()
    res = engine.compute_hydrodynamics(
        speed_kmh=0.0,
        flow_vph=1800.0,
        capacity_vph=1800.0,
        free_flow_speed_kmh=50.0
    )
    moving = engine.compute_hydrodynamics(
        speed_kmh=36.0,
        flow_vph=1800.0,
        capacity_vph=1800.0,
        free_flow_speed_kmh=50.0
    )
    assert res["density_veh_km"] != 1800.0
    assert res["density_veh_km"] == res["jam_density_veh_km"]
    assert res["density_veh_km"] <= 200.0
    assert res["speed_state"] == "STOPPED"
    assert res["speed_ratio"] == 0.0
    assert res["congestion_index"] == 1.0
    assert moving["density_veh_km"] == 50.0
    assert moving["speed_state"] == "MOVING"


def test_custom_district_policy_is_not_the_us_table():
    """At vc 0.28 and speed ratio 0.86 the district table is not the US grade, and Indo-HCM stays B."""
    engine = LOSEngine()
    grade_custom, _ = engine.classify_los(0.28, 0.86, PolicyStandard.CUSTOM_DISTRICT)
    grade_us, _ = engine.classify_los(0.28, 0.86, PolicyStandard.US_HCM_6TH)
    grade_indo, _ = engine.classify_los(0.28, 0.86, PolicyStandard.INDO_HCM)
    assert grade_us == "A"
    assert grade_indo == "B"
    assert grade_custom != grade_us
    assert grade_custom == "B"


def test_unknown_policy_is_rejected():
    """An unknown policy name is not silently graded with the US table."""
    engine = LOSEngine()
    with pytest.raises(ValueError):
        engine.classify_los(0.28, 0.86, "NOT_A_POLICY")


def test_worse_grade_boundary_rule_vc_dominant():
    """
    Verifies that when speed is high but V/C is high (e.g., flow near capacity with fast vehicles),
    the worse grade dictated by V/C is selected.
    """
    engine = LOSEngine()
    # Under Indo-HCM:
    # vc = 0.95 -> Grade E (max_vc 1.00)
    # speed_ratio = 0.92 -> Grade A (min_speed_ratio 0.90)
    # Worse grade must be E
    grade, condition = engine.classify_los(
        vc_ratio=0.95,
        speed_ratio=0.92,
        policy_standard=PolicyStandard.INDO_HCM
    )
    assert grade == "E"
    assert "capacity" in condition.lower() or "unstable" in condition.lower()


def test_worse_grade_boundary_rule_speed_dominant():
    """
    Verifies that when V/C is low but speed is severely degraded (e.g., incident or roadblock),
    the worse grade dictated by speed is selected.
    """
    engine = LOSEngine()
    # Under Indo-HCM:
    # vc = 0.25 -> Grade A (max_vc 0.35)
    # speed_ratio = 0.20 -> Grade F (below 0.30)
    # Worse grade must be F
    grade, condition = engine.classify_los(
        vc_ratio=0.25,
        speed_ratio=0.20,
        policy_standard=PolicyStandard.INDO_HCM
    )
    assert grade == "F"
    assert "breakdown" in condition.lower() or "forced" in condition.lower()


def test_policy_standard_differences():
    """Verifies that differing policy standards apply their specific criteria."""
    engine = LOSEngine()
    # vc = 0.33, speed_ratio = 0.88
    # Under Indo-HCM:
    #   vc 0.33 <= 0.35 -> A
    #   speed_ratio 0.88 < 0.90 -> B
    #   Worse -> B
    grade_indo, _ = engine.classify_los(
        vc_ratio=0.33,
        speed_ratio=0.88,
        policy_standard=PolicyStandard.INDO_HCM
    )
    assert grade_indo == "B"

    # Under US HCM 6th:
    #   vc 0.33 <= 0.50 -> B
    #   speed_ratio 0.88 >= 0.85 -> A
    #   Worse -> B
    grade_us, _ = engine.classify_los(
        vc_ratio=0.33,
        speed_ratio=0.88,
        policy_standard=PolicyStandard.US_HCM_6TH
    )
    assert grade_us == "B"


def test_compute_segment_los_contract():
    """Verifies compute_segment_los produces a valid data contract with provenance."""
    engine = LOSEngine()
    rec = engine.compute_segment_los(
        segment_id="urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
        speed_kmh=36.0,
        flow_vph=1450.0,
        capacity_vph=2400.0,
        free_flow_speed_kmh=50.0,
        policy_standard=PolicyStandard.INDO_HCM,
        source_mode="REPLAY"
    )

    assert rec["segmentId"] == "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01"
    assert rec["speedKmh"] == 36.0
    assert rec["flowVehHr"] == 1450.0
    assert rec["capacityVehHr"] == 2400.0
    assert rec["volumeCapacityRatio"] == round(1450.0 / 2400.0, 3)
    assert rec["levelOfService"] in ("A", "B", "C", "D", "E", "F")
    assert "provenance" in rec
    assert rec["provenance"]["sourceMode"] == "REPLAY"
    assert rec["provenance"]["qualityScore"] >= 0.9


def test_corridor_summary_evaluation():
    """Verifies evaluate_corridor_summary computes correct corridor aggregates using space-mean speed."""
    engine = LOSEngine()
    segments = [
        engine.compute_segment_los("SEG-1", 45.0, 800.0, 2400.0, 50.0, length_m=500.0),
        engine.compute_segment_los("SEG-2", 20.0, 1900.0, 2400.0, 50.0, length_m=500.0),
        engine.compute_segment_los("SEG-3", 35.0, 1200.0, 2400.0, 50.0, length_m=500.0),
    ]

    summary = engine.evaluate_corridor_summary(segments, PolicyStandard.INDO_HCM)
    assert summary["totalSegmentsEvaluated"] == 3
    assert summary["criticalSegmentId"] == "SEG-2"  # Highest V/C
    # Harmonic space-mean speed across equal lengths: 3 / (1/45 + 1/20 + 1/35) = 29.8 km/h
    assert summary["averageSpeedKmh"] == 29.8
    assert summary["corridorLevelOfService"] in ("A", "B", "C", "D", "E", "F")


def test_corridor_summary_space_mean_speed_two_link():
    """
    Verifies length-weighted space-mean speed calculation for two unequal segments:
    50m link @ 10 km/h and 1000m link @ 50 km/h yields 42.0 km/h (not 30.0 km/h arithmetic).
    """
    engine = LOSEngine()
    seg_short = engine.compute_segment_los("SEG-SHORT", 10.0, 500.0, 2000.0, 50.0, length_m=50.0)
    seg_long = engine.compute_segment_los("SEG-LONG", 50.0, 1000.0, 2000.0, 50.0, length_m=1000.0)

    summary = engine.evaluate_corridor_summary([seg_short, seg_long], PolicyStandard.INDO_HCM)
    # Total distance: 1.05 km, Total time: (0.05/10) + (1.00/50) = 0.005 + 0.02 = 0.025 hr -> 42.0 km/h
    assert summary["averageSpeedKmh"] == 42.0


def test_corridor_summary_zero_speed_resilience():
    """Verifies that stopped segments (0 km/h) are handled gracefully without ZeroDivisionError."""
    engine = LOSEngine()
    seg_stopped = engine.compute_segment_los("SEG-STOPPED", 0.0, 0.0, 2000.0, 50.0, length_m=200.0)
    seg_moving = engine.compute_segment_los("SEG-MOVING", 40.0, 800.0, 2000.0, 50.0, length_m=800.0)

    summary = engine.evaluate_corridor_summary([seg_stopped, seg_moving], PolicyStandard.INDO_HCM)
    assert summary["totalSegmentsEvaluated"] == 2
    # Moving link travel time: 0.8 km / 40 km/h = 0.02 hr. Total length: 1.0 km -> 50.0 km/h effective space mean
    assert summary["averageSpeedKmh"] == 50.0

    # All segments stopped
    summary_all_stopped = engine.evaluate_corridor_summary([seg_stopped], PolicyStandard.INDO_HCM)
    assert summary_all_stopped["averageSpeedKmh"] == 0.0


def test_corridor_summary_empty():
    """Verifies graceful and honest handling of empty segment list in corridor summary (no fabricated metrics)."""
    engine = LOSEngine()
    summary = engine.evaluate_corridor_summary([], PolicyStandard.INDO_HCM)
    assert summary["totalSegmentsEvaluated"] == 0
    assert summary["criticalSegmentId"] is None
    assert summary["corridorLevelOfService"] is None
    assert summary["averageSpeedKmh"] is None
    assert summary["averageVolumeCapacityRatio"] is None
    assert summary["averageDensityVehKm"] is None
    assert summary["averageCongestionIndex"] is None


# ============================================================================
# API Endpoint Tests
# ============================================================================

def test_api_traffic_policies():
    """Verifies GET /api/v1/traffic/policies returns supported standards."""
    res = client.get("/api/v1/traffic/policies")
    assert res.status_code == 200
    policies = res.json()
    assert isinstance(policies, list)
    assert len(policies) >= 2

    ids = [p["id"] for p in policies]
    assert "INDO_HCM" in ids
    assert "US_HCM_6TH" in ids

    default_policy = next(p for p in policies if p["id"] == "INDO_HCM")
    assert default_policy["isDefault"] is True


def test_api_corridor_los_default():
    """Verifies GET /api/v1/traffic/corridor/los returns valid corridor summary and segments."""
    res = client.get("/api/v1/traffic/corridor/los")
    assert res.status_code == 200
    data = res.json()
    assert "corridorSummary" in data
    assert "segments" in data

    summary = data["corridorSummary"]
    assert "corridorLevelOfService" in summary
    assert "averageSpeedKmh" in summary
    assert "averageVolumeCapacityRatio" in summary
    assert summary["policyStandard"] == "INDO_HCM"

    segments = data["segments"]
    assert len(segments) >= 8
    for seg in segments:
        assert "segmentId" in seg
        assert "speedKmh" in seg
        assert "flowVehHr" in seg
        assert "volumeCapacityRatio" in seg
        assert "levelOfService" in seg
        assert "provenance" in seg
        assert seg["provenance"]["sourceMode"] in ("REPLAY", "LIVE", "SIMULATION")


def test_api_corridor_los_us_hcm():
    """Verifies GET /api/v1/traffic/corridor/los with policy_standard=US_HCM_6TH."""
    res = client.get("/api/v1/traffic/corridor/los?policy_standard=US_HCM_6TH")
    assert res.status_code == 200
    data = res.json()
    assert data["corridorSummary"]["policyStandard"] == "US_HCM_6TH"


def test_api_corridor_los_invalid_policy():
    """Verifies GET /api/v1/traffic/corridor/los returns 400 for unknown policy standard."""
    res = client.get("/api/v1/traffic/corridor/los?policy_standard=NONEXISTENT_STANDARD")
    assert res.status_code == 400
    data = res.json()
    assert "Invalid policy standard" in data["detail"]


def test_api_segment_los_single():
    """Verifies GET /api/v1/traffic/segment/{segment_id}/los returns single segment detail."""
    res = client.get("/api/v1/traffic/segment/SEG-NR-EB-01/los")
    assert res.status_code == 200
    seg = res.json()
    assert "SEG-NR-EB-01" in seg["segmentId"]
    assert "levelOfService" in seg
    assert "volumeCapacityRatio" in seg
    assert "densityVehKm" in seg


def test_api_segment_los_not_found():
    """Verifies GET /api/v1/traffic/segment/{segment_id}/los returns 404 for unknown segment."""
    res = client.get("/api/v1/traffic/segment/SEG-UNKNOWN-999/los")
    assert res.status_code == 404


def test_compute_segment_los_provenance_honest_quality_scores():
    """
    Verifies that compute_segment_los assigns honest tier-0 synthetic quality score
    (0.70) for SIMULATION feeds per AGENTS.md Section 3, while assigning 0.98 for LIVE and 0.95 for REPLAY.
    """
    engine = LOSEngine()

    # 1. SIMULATION mode defaults to 0.70
    sim_res = engine.compute_segment_los(
        segment_id="SEG-NR-EB-01",
        speed_kmh=25.0,
        flow_vph=1200.0,
        capacity_vph=2400.0,
        source_mode="SIMULATION"
    )
    assert sim_res["provenance"]["sourceMode"] == "SIMULATION"
    assert sim_res["provenance"]["qualityScore"] == 0.70

    # 2. LIVE mode defaults to 0.98
    live_res = engine.compute_segment_los(
        segment_id="SEG-NR-EB-01",
        speed_kmh=25.0,
        flow_vph=1200.0,
        capacity_vph=2400.0,
        source_mode="LIVE"
    )
    assert live_res["provenance"]["sourceMode"] == "LIVE"
    assert live_res["provenance"]["qualityScore"] == 0.98

    # 3. REPLAY mode defaults to 0.95
    replay_res = engine.compute_segment_los(
        segment_id="SEG-NR-EB-01",
        speed_kmh=25.0,
        flow_vph=1200.0,
        capacity_vph=2400.0,
        source_mode="REPLAY"
    )
    assert replay_res["provenance"]["sourceMode"] == "REPLAY"
    assert replay_res["provenance"]["qualityScore"] == 0.95

    # 4. Explicit override preserved
    override_res = engine.compute_segment_los(
        segment_id="SEG-NR-EB-01",
        speed_kmh=25.0,
        flow_vph=1200.0,
        capacity_vph=2400.0,
        source_mode="SIMULATION",
        quality_score=0.85
    )
    assert override_res["provenance"]["qualityScore"] == 0.85

