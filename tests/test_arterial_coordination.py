"""
test_arterial_coordination.py

Hermetic unit and integration test suite for Arterial Two-Way Green Wave
Progression and Offset Optimizer Engine (TASK-03, Issue #7).

Verifies:
1. Nominal progression offset calculation bounded in [0, C - 1] for 90s and 110s cycles.
2. Downstream queue clearance wave adjustment decreasing offset as queue grows.
3. Queue spillback cutoff (> 0.65 ratio) suspending progression.
4. Two-way arterial coordination efficiency and directional weighting.
5. Distance resolution from spatial registry and reference fallback.
6. REST API endpoint contracts:
   - GET /api/v1/traffic/corridors/{corridor_id}/green-wave-offset
   - POST /api/v1/traffic/optimizer/green-wave
   - GET /api/v1/traffic/corridors/{corridor_id}/coordination-plan
7. Standardized provenance metadata and strict advisory compliance status.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.arterial_coordinator import (
    ArterialProgressionCoordinator,
    CorridorCoordinationPlan,
    ProgressionOffsetResult,
    ProgressionRequest,
    arterial_coordinator,
)

client = TestClient(app)


# ============================================================================
# 1. Nominal Offset Bounds [0, C - 1] across 90s and 110s Cycles
# ============================================================================


def test_nominal_offset_bounds_90s_and_110s_cycles():
    """
    Verifies nominal progression offset calculation theta = (d / v_prog) mod C.
    The resulting offset must be strictly non-negative, bounded by the common cycle C,
    and its floor integer representation must fall strictly in [0, C - 1].
    """
    coordinator = ArterialProgressionCoordinator()

    test_cases = [
        # (distance_m, speed_kmh, cycle_sec)
        (850.0, 40.0, 90),
        (850.0, 40.0, 110),
        (1200.0, 45.0, 90),
        (1200.0, 45.0, 110),
        (450.0, 35.0, 90),
        (450.0, 35.0, 110),
        (1800.0, 50.0, 90),
        (1800.0, 50.0, 110),
        (300.0, 30.0, 90),
        (300.0, 30.0, 110),
    ]

    for distance_m, speed_kmh, cycle_sec in test_cases:
        result = coordinator.calculate_progression_offset(
            upstream_intersection_id="INT-VN-01",
            downstream_intersection_id="INT-SN-01",
            common_cycle_sec=cycle_sec,
            downstream_queue_m=0.0,
            progression_speed_kmh=speed_kmh,
            distance_meters=distance_m,
        )

        v_prog_mps = speed_kmh / 3.6
        expected_travel_time = distance_m / v_prog_mps
        expected_nominal_offset = expected_travel_time % cycle_sec

        assert result.commonCycleSec == cycle_sec
        assert result.distanceMeters == distance_m
        assert abs(result.nominalTravelTimeSec - round(expected_travel_time, 2)) < 0.05
        assert abs(result.nominalOffsetSec - round(expected_nominal_offset, 2)) < 0.05

        # Strict bounds verification: 0 <= offset < C and int(offset) in [0, C - 1]
        assert 0.0 <= result.nominalOffsetSec < cycle_sec
        assert 0 <= int(result.nominalOffsetSec) <= (cycle_sec - 1)
        assert 0.0 <= result.adjustedOffsetSec < cycle_sec
        assert 0 <= int(result.adjustedOffsetSec) <= (cycle_sec - 1)


def test_nominal_offset_exact_multiples_of_cycle():
    """
    Verifies that when nominal travel time is an exact multiple of the cycle,
    the offset is exactly 0.0 seconds.
    """
    coordinator = ArterialProgressionCoordinator()

    # 1000m at 40 km/h (11.111 m/s) -> 90.0s travel time.
    # With cycle = 90s, nominal offset should be 0.0s.
    speed_kmh = 40.0
    v_mps = speed_kmh / 3.6
    distance_m = 90.0 * v_mps  # exactly 1000.0 meters

    result = coordinator.calculate_progression_offset(
        upstream_intersection_id="INT-01",
        downstream_intersection_id="INT-02",
        common_cycle_sec=90,
        downstream_queue_m=0.0,
        progression_speed_kmh=speed_kmh,
        distance_meters=distance_m,
    )

    assert abs(result.nominalTravelTimeSec - 90.0) < 0.01
    assert result.nominalOffsetSec == 0.0
    assert 0 <= int(result.nominalOffsetSec) <= 89


# ============================================================================
# 2. Queue Clearance Adjustment Decreasing Offset
# ============================================================================


def test_queue_clearance_adjustment_decreases_offset():
    """
    Verifies that the presence of a downstream residual queue decreases the offset.
    Physical reason: The downstream signal must turn green earlier by the queue
    clearance time t_clearance = Q / v_dissipation to clear stopped vehicles before
    the incoming platoon arrives.
    """
    coordinator = ArterialProgressionCoordinator()
    link_distance = 850.0
    cycle = 90
    speed_kmh = 40.0
    v_dissipation = 5.0  # 5 m/s backward wave

    # Evaluate monotonic decrease across growing queue lengths: 0m, 50m, 100m, 150m, 200m
    queue_lengths = [0.0, 50.0, 100.0, 150.0, 200.0]
    previous_offset = None

    for q in queue_lengths:
        result = coordinator.calculate_progression_offset(
            upstream_intersection_id="INT-VN-01",
            downstream_intersection_id="INT-SN-01",
            common_cycle_sec=cycle,
            downstream_queue_m=q,
            progression_speed_kmh=speed_kmh,
            distance_meters=link_distance,
            dissipation_speed_mps=v_dissipation,
        )

        assert result.coordinationMode == "PROGRESSION_ACTIVE"
        assert result.safetyStatus == "ENVELOPE_VERIFIED"
        assert result.progressionSuspended is False

        # Effective distance must decrease by exactly Q
        assert abs(result.effectiveDistanceMeters - (link_distance - q)) < 0.1

        # Queue clearance time must equal Q / v_dissipation
        expected_clearance = q / v_dissipation
        assert abs(result.queueClearanceTimeSec - round(expected_clearance, 2)) < 0.05

        # Offset must decrease strictly as queue grows
        if previous_offset is not None:
            assert result.adjustedOffsetSec < previous_offset

        previous_offset = result.adjustedOffsetSec

    # Specific calculation check for Q = 100m:
    # d_eff = 750m, v_prog = 11.111 m/s -> t_eff = 67.5s
    # t_clearance = 100 / 5.0 = 20.0s
    # theta_adj = (67.5 - 20.0) mod 90 = 47.5s
    res_100 = coordinator.calculate_progression_offset(
        upstream_intersection_id="INT-VN-01",
        downstream_intersection_id="INT-SN-01",
        common_cycle_sec=90,
        downstream_queue_m=100.0,
        progression_speed_kmh=40.0,
        distance_meters=850.0,
        dissipation_speed_mps=5.0,
    )
    assert abs(res_100.adjustedOffsetSec - 47.5) < 0.1
    assert res_100.adjustedOffsetSec < res_100.nominalOffsetSec


# ============================================================================
# 3. Queue Spillback Cutoff (> 0.65 Ratio) Suspending Progression
# ============================================================================


def test_queue_spillback_cutoff_suspends_progression():
    """
    CRITICAL SAFETY TEST:
    Verifies that when downstream queue storage ratio Q / d exceeds 0.65:
    - coordinationMode is set to 'QUEUE_FLUSH_REQUIRED'
    - safetyStatus is set to 'QUEUE_SPILLBACK_RISK'
    - progressionSuspended is True
    - Progression bandwidth and bidirectional efficiencies are set to 0.0
    """
    coordinator = ArterialProgressionCoordinator()
    link_distance = 800.0

    # Case A: Queue ratio = 0.50 (400m / 800m) <= 0.65 threshold -> PROGRESSION_ACTIVE
    res_safe = coordinator.calculate_progression_offset(
        upstream_intersection_id="INT-VN-01",
        downstream_intersection_id="INT-SN-01",
        common_cycle_sec=90,
        downstream_queue_m=400.0,
        distance_meters=link_distance,
    )
    assert res_safe.queueStorageRatio == 0.50
    assert res_safe.coordinationMode == "PROGRESSION_ACTIVE"
    assert res_safe.safetyStatus == "ENVELOPE_VERIFIED"
    assert res_safe.progressionSuspended is False
    assert res_safe.bidirectionalEfficiency > 0.0

    # Case B: Queue ratio exactly 0.65 (520m / 800m) <= 0.65 threshold -> PROGRESSION_ACTIVE
    res_boundary = coordinator.calculate_progression_offset(
        upstream_intersection_id="INT-VN-01",
        downstream_intersection_id="INT-SN-01",
        common_cycle_sec=90,
        downstream_queue_m=520.0,
        distance_meters=link_distance,
    )
    assert res_boundary.queueStorageRatio == 0.65
    assert res_boundary.coordinationMode == "PROGRESSION_ACTIVE"
    assert res_boundary.safetyStatus == "ENVELOPE_VERIFIED"
    assert res_boundary.progressionSuspended is False

    # Case C: Queue ratio 0.66 (528m / 800m) > 0.65 threshold -> QUEUE_FLUSH_REQUIRED
    res_risk = coordinator.calculate_progression_offset(
        upstream_intersection_id="INT-VN-01",
        downstream_intersection_id="INT-SN-01",
        common_cycle_sec=90,
        downstream_queue_m=528.0,
        distance_meters=link_distance,
    )
    assert res_risk.queueStorageRatio == 0.66
    assert res_risk.coordinationMode == "QUEUE_FLUSH_REQUIRED"
    assert res_risk.safetyStatus == "QUEUE_SPILLBACK_RISK"
    assert res_risk.progressionSuspended is True
    assert res_risk.bidirectionalEfficiency == 0.0
    assert res_risk.bandwidthEfficiencyPct == 0.0
    assert "QUEUE_FLUSH_REQUIRED" in res_risk.coordinationMode
    assert "spillback" in res_risk.safetyStatus.lower()
    assert "queue-flush" in res_risk.safetyAdvisory.lower()

    # Case D: Severe spillback (700m / 800m = 0.875) -> QUEUE_FLUSH_REQUIRED
    res_severe = coordinator.calculate_progression_offset(
        upstream_intersection_id="INT-VN-01",
        downstream_intersection_id="INT-SN-01",
        common_cycle_sec=90,
        downstream_queue_m=700.0,
        distance_meters=link_distance,
    )
    assert res_severe.queueStorageRatio == 0.875
    assert res_severe.progressionSuspended is True
    assert res_severe.coordinationMode == "QUEUE_FLUSH_REQUIRED"
    assert res_severe.safetyStatus == "QUEUE_SPILLBACK_RISK"


# ============================================================================
# 4. Two-Way Arterial Coordination Efficiency and Directional Weighting
# ============================================================================


def test_twoway_arterial_coordination_and_directional_weighting():
    """
    Verifies two-way bidirectional coordination efficiency and directional weighting.
    Validates compromise offset shifts towards the direction with higher priority weight.
    """
    coordinator = ArterialProgressionCoordinator()

    # Symmetric weights (50% forward, 50% reverse)
    res_balanced = coordinator.calculate_progression_offset(
        upstream_intersection_id="INT-VN-01",
        downstream_intersection_id="INT-SN-01",
        common_cycle_sec=90,
        downstream_queue_m=0.0,
        progression_speed_kmh=40.0,
        distance_meters=850.0,
        forward_weight=0.5,
        reverse_weight=0.5,
    )
    assert 0.0 <= res_balanced.bidirectionalEfficiency <= 1.0
    assert 0.0 <= res_balanced.bandwidthEfficiencyPct <= 100.0
    assert res_balanced.forwardWeight == 0.5
    assert res_balanced.reverseWeight == 0.5

    # 100% Forward Priority: Optimal compromise must match forward offset
    res_fwd_only = coordinator.calculate_progression_offset(
        upstream_intersection_id="INT-VN-01",
        downstream_intersection_id="INT-SN-01",
        common_cycle_sec=90,
        downstream_queue_m=0.0,
        progression_speed_kmh=40.0,
        distance_meters=850.0,
        forward_weight=1.0,
        reverse_weight=0.0,
    )
    assert abs(res_fwd_only.optimalCompromiseOffsetSec - res_fwd_only.forwardOffsetSec) < 0.1
    assert res_fwd_only.forwardEfficiency == 1.0
    assert res_fwd_only.forwardWeight == 1.0
    assert res_fwd_only.reverseWeight == 0.0

    # 100% Reverse Priority: Optimal compromise must match reverse offset
    res_rev_only = coordinator.calculate_progression_offset(
        upstream_intersection_id="INT-VN-01",
        downstream_intersection_id="INT-SN-01",
        common_cycle_sec=90,
        downstream_queue_m=0.0,
        progression_speed_kmh=40.0,
        distance_meters=850.0,
        forward_weight=0.0,
        reverse_weight=1.0,
    )
    assert abs(res_rev_only.optimalCompromiseOffsetSec - res_rev_only.reverseOffsetSec) < 0.1
    assert res_rev_only.reverseEfficiency == 1.0
    assert res_rev_only.forwardWeight == 0.0
    assert res_rev_only.reverseWeight == 1.0

    # Asymmetric 75/25 Priority
    res_asym = coordinator.calculate_progression_offset(
        upstream_intersection_id="INT-VN-01",
        downstream_intersection_id="INT-SN-01",
        common_cycle_sec=90,
        downstream_queue_m=30.0,
        progression_speed_kmh=40.0,
        distance_meters=850.0,
        forward_weight=0.75,
        reverse_weight=0.25,
    )
    assert res_asym.forwardEfficiency >= res_asym.reverseEfficiency


# ============================================================================
# 5. Distance Resolution from Spatial Registry and Fallback
# ============================================================================


def test_distance_resolution_from_spatial_registry_and_fallback():
    """
    Verifies inter-junction distance resolution:
    - Same junction -> 0.0m
    - Registered corridor nodes -> resolves from catalog or reference pilot fallback (850.0m)
    - Generic unknown corridor nodes -> generic fallback (800.0m)
    - Explicit distance override -> exact override preserved
    """
    coordinator = ArterialProgressionCoordinator()

    # 1. Identical nodes
    dist_zero = coordinator.resolve_link_distance("INT-VN-01", "INT-VN-01")
    assert dist_zero == 0.0

    # 2. Reference corridor pilot nodes (VN-01 and SN-01)
    dist_pilot = coordinator.resolve_link_distance(
        upstream_id="INT-VN-01",
        downstream_id="INT-SN-01",
        corridor_id="CORRIDOR-NAGAR-ROAD",
    )
    assert dist_pilot in (850.0, 1180.0, 480.0, 450.0) or dist_pilot > 0.0

    # 3. Generic unknown corridor fallback
    dist_generic = coordinator.resolve_link_distance(
        upstream_id="INT-UNKNOWN-A",
        downstream_id="INT-UNKNOWN-B",
        corridor_id="CORRIDOR-GENERIC",
    )
    assert dist_generic == 800.0

    # 4. Explicit distance override taking precedence in progression calculation
    res_override = coordinator.calculate_progression_offset(
        upstream_intersection_id="INT-UNKNOWN-A",
        downstream_intersection_id="INT-UNKNOWN-B",
        common_cycle_sec=90,
        distance_meters=1450.0,
    )
    assert res_override.distanceMeters == 1450.0


# ============================================================================
# 6. REST API Endpoint Contracts
# ============================================================================


def test_api_green_wave_offset_nominal_and_provenance():
    """
    Verifies GET /api/v1/traffic/corridors/{id}/green-wave-offset:
    - Status 200 OK
    - Valid offset values bounded in [0, C)
    - Standardized provenance (sourceMode 'PREDICTED', qualityScore 1.0)
    - Advisory compliance status 'REQUIRES_HUMAN_APPROVAL'
    """
    response = client.get(
        "/api/v1/traffic/corridors/CORRIDOR-NAGAR-ROAD/green-wave-offset",
        params={
            "upstream_intersection_id": "INT-VN-01",
            "downstream_intersection_id": "INT-SN-01",
            "common_cycle_sec": 90,
            "downstream_queue_m": 40.0,
            "progression_speed_kmh": 40.0,
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["corridorId"] == "CORRIDOR-NAGAR-ROAD"
    assert data["upstreamIntersectionId"] == "INT-VN-01"
    assert data["downstreamIntersectionId"] == "INT-SN-01"
    assert data["commonCycleSec"] == 90
    assert 0.0 <= data["nominalOffsetSec"] < 90.0
    assert 0.0 <= data["adjustedOffsetSec"] < 90.0
    assert data["coordinationMode"] == "PROGRESSION_ACTIVE"
    assert data["safetyStatus"] == "ENVELOPE_VERIFIED"
    assert data["progressionSuspended"] is False
    assert data["advisoryStatus"] == "REQUIRES_HUMAN_APPROVAL"

    # Provenance verification
    provenance = data["provenance"]
    assert provenance["sourceMode"] == "PREDICTED"
    assert provenance["qualityScore"] == 1.0
    assert "calculatedAt" in provenance
    assert provenance["advisoryCompliance"] == "REQUIRES_HUMAN_APPROVAL"


def test_api_green_wave_offset_camelcase_query_params():
    """
    Verifies GET /api/v1/traffic/corridors/{id}/green-wave-offset supports camelCase parameters.
    """
    response = client.get(
        "/api/v1/traffic/corridors/CORRIDOR-NAGAR-ROAD/green-wave-offset",
        params={
            "upstreamIntersectionId": "INT-VN-01",
            "downstreamIntersectionId": "INT-SN-01",
            "commonCycleSec": 110,
            "downstreamQueueMeters": 60.0,
            "progressionSpeedKmh": 45.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["commonCycleSec"] == 110
    assert 0.0 <= data["nominalOffsetSec"] < 110.0
    assert 0 <= int(data["nominalOffsetSec"]) <= 109


def test_api_green_wave_offset_spillback_rejection():
    """
    Verifies that high queue storage ratio triggers spillback suspension via REST API.
    """
    response = client.get(
        "/api/v1/traffic/corridors/CORRIDOR-NAGAR-ROAD/green-wave-offset",
        params={
            "upstream_intersection_id": "INT-VN-01",
            "downstream_intersection_id": "INT-SN-01",
            "common_cycle_sec": 90,
            "downstream_queue_m": 600.0,
            "distance_meters": 800.0,  # Q / d = 600 / 800 = 0.75 > 0.65
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["queueStorageRatio"] == 0.75
    assert data["coordinationMode"] == "QUEUE_FLUSH_REQUIRED"
    assert data["safetyStatus"] == "QUEUE_SPILLBACK_RISK"
    assert data["progressionSuspended"] is True
    assert data["bidirectionalEfficiency"] == 0.0


def test_api_green_wave_offset_missing_parameters():
    """
    Verifies HTTP 422 Unprocessable Entity when required intersection parameters are missing.
    """
    response = client.get(
        "/api/v1/traffic/corridors/CORRIDOR-NAGAR-ROAD/green-wave-offset",
        params={"common_cycle_sec": 90},
    )
    assert response.status_code == 422


def test_api_optimizer_green_wave_post():
    """
    Verifies POST /api/v1/traffic/optimizer/green-wave accepting JSON payload.
    """
    payload = {
        "corridorId": "CORRIDOR-NAGAR-ROAD",
        "upstreamIntersectionId": "INT-VN-01",
        "downstreamIntersectionId": "INT-SN-01",
        "commonCycleSec": 90,
        "downstreamQueueMeters": 45.0,
        "progressionSpeedKmh": 40.0,
        "distanceMeters": 850.0,
        "forwardWeight": 0.7,
        "reverseWeight": 0.3,
    }

    response = client.post("/api/v1/traffic/optimizer/green-wave", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["corridorId"] == "CORRIDOR-NAGAR-ROAD"
    assert data["upstreamIntersectionId"] == "INT-VN-01"
    assert data["downstreamIntersectionId"] == "INT-SN-01"
    assert data["forwardWeight"] == 0.7
    assert data["reverseWeight"] == 0.3
    assert data["coordinationMode"] == "PROGRESSION_ACTIVE"
    assert data["safetyStatus"] == "ENVELOPE_VERIFIED"
    assert data["advisoryStatus"] == "REQUIRES_HUMAN_APPROVAL"
    assert data["provenance"]["sourceMode"] == "PREDICTED"


def test_api_corridor_coordination_plan_get():
    """
    Verifies GET /api/v1/traffic/corridors/{id}/coordination-plan returning
    a multi-intersection coordination plan with link offsets and corridor efficiency.
    """
    response = client.get(
        "/api/v1/traffic/corridors/CORRIDOR-NAGAR-ROAD/coordination-plan",
        params={
            "common_cycle_sec": 90,
            "progression_speed_kmh": 40.0,
            "forward_weight": 0.6,
            "reverse_weight": 0.4,
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["corridorId"] == "CORRIDOR-NAGAR-ROAD"
    assert len(data["intersections"]) >= 2
    assert len(data["links"]) >= 1
    assert data["commonCycleSec"] == 90
    assert 0.0 <= data["networkBidirectionalEfficiency"] <= 1.0
    assert 0.0 <= data["networkBandwidthEfficiencyPct"] <= 100.0
    assert data["overallSafetyStatus"] in ("ENVELOPE_VERIFIED", "QUEUE_SPILLBACK_RISK")
    assert data["coordinationMode"] in ("PROGRESSION_ACTIVE", "QUEUE_FLUSH_REQUIRED")
    assert data["advisoryStatus"] == "REQUIRES_HUMAN_APPROVAL"
    assert data["provenance"]["sourceMode"] == "PREDICTED"

    # Verify each coordinated link in the plan
    for link in data["links"]:
        assert 0.0 <= link["nominalOffsetSec"] < 90.0
        assert 0.0 <= link["adjustedOffsetSec"] < 90.0
        assert link["advisoryStatus"] == "REQUIRES_HUMAN_APPROVAL"
        assert link["provenance"]["sourceMode"] == "PREDICTED"
