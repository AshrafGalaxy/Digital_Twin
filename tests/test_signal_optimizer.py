"""
test_signal_optimizer.py

Hermetic unit test suite for the Webster Delay-Minimizing Adaptive Signal Timing
Optimization Engine (TASK-02), verifying:
- Webster optimal cycle calculation (C_0 = (1.5L + 5) / (1 - Y))
- Pedestrian crosswalk clearance invariant (g_j >= crosswalk_width / 1.2 m/s)
- Saturation degree cap enforcement (x_j <= 0.85)
- Conservation of cycle time (sum(g_j) + L == C)
- Delay reduction estimation against baseline fixed plans
- REST API endpoint contracts (/traffic/optimizer/webster, /traffic/intersection/{id}/optimal-timing)
- Advisory Rule Engine integration
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.signal_optimizer import (
    ApproachDemand,
    SignalConstraints,
    WebsterSignalOptimizer,
    webster_optimizer
)
from backend.services.rule_engine import AdvisoryRuleEngine

client = TestClient(app)


def test_webster_balanced_flow():
    """Verifies Webster optimization under symmetric 4-phase arterial flow."""
    optimizer = WebsterSignalOptimizer()
    approaches = [
        ApproachDemand("APP-EB", "Eastbound Through", 800.0, lanes=2, min_green_sec=15.0, crosswalk_width_m=14.0),
        ApproachDemand("APP-WB", "Westbound Through", 800.0, lanes=2, min_green_sec=15.0, crosswalk_width_m=14.0),
        ApproachDemand("APP-NB", "Northbound Approach", 350.0, lanes=1, min_green_sec=15.0, crosswalk_width_m=12.0),
        ApproachDemand("APP-SB", "Southbound Approach", 350.0, lanes=1, min_green_sec=15.0, crosswalk_width_m=12.0)
    ]

    plan = optimizer.compute_optimal_timing(
        intersection_id="INT-BALANCED-01",
        approaches=approaches,
        baseline_cycle_sec=90
    )

    # 1. Cycle length bounds [60, 150]
    assert 60 <= plan.target_cycle_sec <= 150

    # 2. Conservation of cycle time: sum(green) + lost_time == target_cycle
    total_green = sum(p.green_sec for p in plan.phases)
    assert total_green + plan.total_lost_time_sec == plan.target_cycle_sec

    # 3. All pedestrian crosswalk clearance invariants verified
    assert plan.safety_validation["pedestrianInvariantVerified"] is True
    for p in plan.phases:
        assert p.green_sec >= p.ped_clearance_sec

    # 4. Cycle is safely bounded
    assert plan.safety_validation["cycleBounded"] is True


def test_pedestrian_invariant_enforcement_zero_vehicle_flow():
    """
    CRITICAL SAFETY TEST:
    Ensures that pedestrian crosswalk clearance is NEVER truncated or compromised,
    even if an approach has nearly zero vehicular demand.
    """
    optimizer = WebsterSignalOptimizer()
    approaches = [
        ApproachDemand("APP-EB", "Heavy Arterial Eastbound", 1200.0, lanes=3, min_green_sec=20.0, crosswalk_width_m=16.0),
        ApproachDemand("APP-WB", "Heavy Arterial Westbound", 1150.0, lanes=3, min_green_sec=20.0, crosswalk_width_m=16.0),
        ApproachDemand("APP-NB", "Minor Side-Street North", 40.0, lanes=1, min_green_sec=10.0, crosswalk_width_m=18.0), # 18m crosswalk -> 15s clearance
        ApproachDemand("APP-SB", "Minor Side-Street South", 30.0, lanes=1, min_green_sec=10.0, crosswalk_width_m=18.0)  # 18m crosswalk -> 15s clearance
    ]

    plan = optimizer.compute_optimal_timing(
        intersection_id="INT-PED-SAFETY-01",
        approaches=approaches,
        baseline_cycle_sec=90
    )

    # Minimum clearance for 18m width at 1.2 m/s = 15s
    nb_phase = next(p for p in plan.phases if p.approach_id == "APP-NB")
    sb_phase = next(p for p in plan.phases if p.approach_id == "APP-SB")

    assert nb_phase.green_sec >= 15
    assert sb_phase.green_sec >= 15
    assert plan.safety_validation["pedestrianInvariantVerified"] is True


def test_saturation_cap_under_heavy_congestion():
    """
    Verifies that when approach flows are heavy, the optimizer expands green time
    to cap the degree of saturation.
    """
    optimizer = WebsterSignalOptimizer()
    approaches = [
        ApproachDemand("APP-1", "Phase 1", 900.0, lanes=2, saturation_flow_vph_lane=1800.0),
        ApproachDemand("APP-2", "Phase 2", 850.0, lanes=2, saturation_flow_vph_lane=1800.0),
        ApproachDemand("APP-3", "Phase 3", 400.0, lanes=2, saturation_flow_vph_lane=1800.0),
        ApproachDemand("APP-4", "Phase 4", 350.0, lanes=2, saturation_flow_vph_lane=1800.0)
    ]

    plan = optimizer.compute_optimal_timing(
        intersection_id="INT-HEAVY-01",
        approaches=approaches,
        constraints=SignalConstraints(max_saturation_cap=0.85)
    )

    # Max saturation should be kept within safe operating bounds (allowing discrete integer second tolerance)
    assert plan.safety_validation["maxSaturation"] <= 0.88
    assert plan.safety_validation["saturationCapSatisfied"] is True
    assert plan.safety_validation["oversaturatedRegime"] is False  # y_sum = (900+850+400+350)/3600 = 2500/3600 = 0.694
    assert plan.optimal_delay_sec_veh < 120.0

    # Test extreme oversaturation (y_sum >= 0.85)
    heavy_approaches = [
        ApproachDemand("APP-1", "Phase 1", 1600.0, lanes=2, saturation_flow_vph_lane=1800.0),
        ApproachDemand("APP-2", "Phase 2", 1550.0, lanes=2, saturation_flow_vph_lane=1800.0),
    ]
    heavy_plan = optimizer.compute_optimal_timing(
        intersection_id="INT-EXTREME-01",
        approaches=heavy_approaches
    )
    assert heavy_plan.safety_validation["oversaturatedRegime"] is True
    assert "queue storage mitigation recommended" in heavy_plan.safety_validation["advisoryNote"]


def test_delay_reduction_positive():
    """Verifies that Webster timing produces lower delay than an unbalanced baseline plan."""
    optimizer = WebsterSignalOptimizer()
    # Heavily asymmetric demand where fixed equal splits produce high delay on major approaches
    approaches = [
        ApproachDemand("APP-MAJ-1", "Major Arterial 1", 1200.0, lanes=2),
        ApproachDemand("APP-MAJ-2", "Major Arterial 2", 1100.0, lanes=2),
        ApproachDemand("APP-MIN-1", "Minor Street 1", 150.0, lanes=1),
        ApproachDemand("APP-MIN-2", "Minor Street 2", 120.0, lanes=1)
    ]

    plan = optimizer.compute_optimal_timing(
        intersection_id="INT-DELAY-01",
        approaches=approaches,
        baseline_cycle_sec=80
    )

    assert plan.estimated_delay_reduction_sec >= 0.0
    assert plan.optimal_delay_sec_veh <= plan.baseline_delay_sec_veh


def test_webster_overflow_term_uses_arrival_flow():
    """At x = 0.75 and q = 0.15 veh/s the overflow term is 7.50 s, not the capacity form."""
    overflow = WebsterSignalOptimizer.webster_overflow_delay(0.75, 0.15)
    assert abs(overflow - 7.50) < 0.01
    delay = WebsterSignalOptimizer.calculate_webster_delay(
        cycle_sec=90.0,
        split_ratio=0.40,
        flow_vps=0.15,
        saturation_flow_vps=0.50,
    )
    # Uniform term: 90 * (0.6)^2 / (2 * (1 - 0.40 * 0.75)) = 23.142857
    assert abs(delay - (23.142857 + 7.50)) < 0.01
    assert delay == 30.64


def test_oversaturated_delay_is_not_a_single_cap():
    """A worse degree of saturation must not collapse onto the same 180 second cap."""
    milder = WebsterSignalOptimizer.calculate_webster_delay(90.0, 0.40, 0.30, 0.50)
    worse = WebsterSignalOptimizer.calculate_webster_delay(90.0, 0.40, 0.40, 0.50)
    assert milder != 180.0
    assert worse != 180.0
    assert worse > milder


def test_delay_reduction_can_be_negative():
    """A constrained plan that is slower than the baseline reports a negative reduction."""
    optimizer = WebsterSignalOptimizer()
    approaches = [
        ApproachDemand("APP-A", "Approach A", 2200.0, lanes=2, min_green_sec=40.0, crosswalk_width_m=3.6, saturation_flow_vph_lane=1800.0),
        ApproachDemand("APP-B", "Approach B", 2200.0, lanes=2, min_green_sec=40.0, crosswalk_width_m=3.6, saturation_flow_vph_lane=1800.0),
    ]
    plan = optimizer.compute_optimal_timing(
        intersection_id="INT-WORSE-01",
        approaches=approaches,
        constraints=SignalConstraints(min_cycle_sec=60, max_cycle_sec=70),
        baseline_cycle_sec=150,
    )
    assert plan.optimal_delay_sec_veh > plan.baseline_delay_sec_veh
    assert plan.estimated_delay_reduction_sec < 0.0
    assert plan.provenance["sourceMode"] == "PREDICTED"
    assert plan.provenance["delayUpperClampApplied"] is False


def test_advisory_current_green_is_the_baseline_green():
    """The dossier current value is the baseline phase green, and feature impacts are not invented."""
    engine = AdvisoryRuleEngine()
    approaches = [
        ApproachDemand("APP-A", "Approach A", 500.0, lanes=2, min_green_sec=10.0, crosswalk_width_m=12.0),
        ApproachDemand("APP-B", "Approach B", 280.0, lanes=2, min_green_sec=10.0, crosswalk_width_m=12.0),
    ]
    advisory = engine.generate_webster_timing_advisory(
        intersection_id="urn:ngsi-ld:Intersection:TEST:INT-BIND",
        approaches=approaches,
        baseline_cycle_sec=90,
    )
    plan = webster_optimizer.compute_optimal_timing(
        intersection_id="urn:ngsi-ld:Intersection:TEST:INT-BIND",
        approaches=approaches,
        baseline_cycle_sec=90,
    )
    assert advisory.proposedChange is not None
    assert advisory.proposedChange.currentValue == float(plan.phases[0].baseline_green_sec)
    assert advisory.proposedChange.recommendedValue == float(plan.phases[0].green_sec)
    assert advisory.topFeatures == []
    assert advisory.evidence.confidenceScore is None
    assert advisory.predictedImpact is not None
    assert advisory.predictedImpact.delayDeltaCI is None
    assert advisory.evidence.sourceMode == "PREDICTED"

    heavier = [
        ApproachDemand("APP-A", "Approach A", 1400.0, lanes=2, min_green_sec=10.0, crosswalk_width_m=12.0),
        ApproachDemand("APP-B", "Approach B", 300.0, lanes=2, min_green_sec=10.0, crosswalk_width_m=12.0),
    ]
    other = engine.generate_webster_timing_advisory(
        intersection_id="urn:ngsi-ld:Intersection:TEST:INT-BIND-2",
        approaches=heavier,
        baseline_cycle_sec=90,
    )
    assert other.topFeatures == []
    assert [item.impact for item in advisory.topFeatures] != [42.0, 28.0, 14.0, -10.0, 6.0]


def test_rule_engine_webster_advisory():
    """Verifies AdvisoryRuleEngine generates compliant Webster timing recommendations."""
    engine = AdvisoryRuleEngine()
    rec = engine.generate_webster_timing_advisory(
        intersection_id="urn:ngsi-ld:Intersection:PUNE:INT-VN-01",
        baseline_cycle_sec=90
    )

    assert rec.domain.value == "TRAFFIC"
    assert rec.humanApprovalRequired is True
    assert "INT-VN-01" in rec.targetEntityId
    assert "Webster" in rec.title
    assert "Do not authorize" in rec.suggestedAction
    assert "max saturation" in rec.suggestedAction
    assert rec.safetyChecklist is not None
    assert rec.safetyChecklist.maxWaitThresholdSafe is False
    assert "Verified: pedestrian crosswalk clearance invariant met" not in rec.suggestedAction
    assert len(rec.auditTrail) >= 1


def test_webster_advisory_text_matches_a_legal_plan():
    """A plan inside the saturation cap keeps the verified sentence and still requires a person."""
    engine = AdvisoryRuleEngine()
    rec = engine.generate_webster_timing_advisory(
        intersection_id="urn:ngsi-ld:Intersection:TEST:INT-LEGAL",
        approaches=[
            ApproachDemand("APP-EB", "Eastbound Through", 240.0, lanes=2, min_green_sec=10.0, crosswalk_width_m=12.0),
            ApproachDemand("APP-WB", "Westbound Through", 240.0, lanes=2, min_green_sec=10.0, crosswalk_width_m=12.0),
            ApproachDemand("APP-NB", "Northbound Approach", 180.0, lanes=2, min_green_sec=10.0, crosswalk_width_m=12.0),
            ApproachDemand("APP-SB", "Southbound Approach", 180.0, lanes=2, min_green_sec=10.0, crosswalk_width_m=12.0),
        ],
    )
    assert rec.safetyChecklist is not None
    assert rec.safetyChecklist.pedestrianPhaseSafe is True
    assert rec.safetyChecklist.minGreenSatisfied is True
    assert rec.safetyChecklist.maxWaitThresholdSafe is True
    assert rec.safetyChecklist.emergencyPreemptionClear is True
    assert "pedestrian crosswalk clearance invariant met" in rec.suggestedAction
    assert "Human authorization is required" in rec.suggestedAction
    assert rec.humanApprovalRequired is True
    assert "Webster Optimization Engine" in rec.auditTrail[0].reviewer


# ============================================================================
# REST API Endpoint Tests
# ============================================================================

def test_api_optimize_signal_timing_post():
    """Verifies POST /api/v1/traffic/optimizer/webster computes and persists timing plan."""
    payload = {
        "intersectionId": "urn:ngsi-ld:Intersection:PUNE:INT-VN-01",
        "baselineCycleSec": 90,
        "approaches": [
            {
                "approachId": "APP-NR-EB",
                "description": "Nagar Road EB",
                "flowVehHr": 1400.0,
                "lanes": 3,
                "saturationFlowVehHrLane": 1800.0,
                "minGreenSec": 20.0,
                "crosswalkWidthMeters": 16.0
            },
            {
                "approachId": "APP-NR-WB",
                "description": "Nagar Road WB",
                "flowVehHr": 1350.0,
                "lanes": 3,
                "saturationFlowVehHrLane": 1800.0,
                "minGreenSec": 20.0,
                "crosswalkWidthMeters": 16.0
            },
            {
                "approachId": "APP-VN-NB",
                "description": "Viman Nagar NB",
                "flowVehHr": 700.0,
                "lanes": 2,
                "saturationFlowVehHrLane": 1800.0,
                "minGreenSec": 15.0,
                "crosswalkWidthMeters": 14.0
            },
            {
                "approachId": "APP-VN-SB",
                "description": "Viman Nagar SB",
                "flowVehHr": 650.0,
                "lanes": 2,
                "saturationFlowVehHrLane": 1800.0,
                "minGreenSec": 15.0,
                "crosswalkWidthMeters": 14.0
            }
        ]
    }

    res = client.post("/api/v1/traffic/optimizer/webster", json=payload)
    assert res.status_code == 200
    plan = res.json()

    assert "recommendationId" in plan
    assert plan["intersectionId"] == "urn:ngsi-ld:Intersection:PUNE:INT-VN-01"
    assert 60 <= plan["targetCycleSec"] <= 150
    assert len(plan["phases"]) == 4
    assert plan["safetyValidation"]["pedestrianInvariantVerified"] is True
    assert plan["status"] == "REQUIRES_HUMAN_APPROVAL"


def test_api_get_intersection_optimal_timing():
    """Verifies GET /api/v1/traffic/intersection/{id}/optimal-timing returns timing plan."""
    res = client.get("/api/v1/traffic/intersection/INT-VN-01/optimal-timing")
    assert res.status_code == 200
    plan = res.json()

    assert "INT-VN-01" in plan["intersectionId"]
    assert len(plan["phases"]) >= 2
    assert plan["targetCycleSec"] >= 60
    assert plan["safetyValidation"]["minGreenSatisfied"] is True
    assert plan["status"] == "REQUIRES_HUMAN_APPROVAL"


def test_min_green_certificate_rejects_infeasible_cycle():
    """A cycle cap that cannot hold statutory greens must not certify them as satisfied."""
    optimizer = WebsterSignalOptimizer()
    approaches = [
        ApproachDemand("A", "Approach A", 351.0, lanes=2, min_green_sec=35.0, crosswalk_width_m=3.6),
        ApproachDemand("B", "Approach B", 311.0, lanes=2, min_green_sec=35.0, crosswalk_width_m=3.6),
        ApproachDemand("C", "Approach C", 176.0, lanes=2, min_green_sec=30.0, crosswalk_width_m=3.6),
        ApproachDemand("D", "Approach D", 162.0, lanes=2, min_green_sec=30.0, crosswalk_width_m=3.6),
    ]
    plan = optimizer.compute_optimal_timing(
        intersection_id="INT-MIN-GREEN",
        approaches=approaches,
        constraints=SignalConstraints(max_cycle_sec=90),
    )
    greens = [phase.green_sec for phase in plan.phases]
    assert greens == [26, 23, 13, 12]
    assert plan.safety_validation["minGreenSatisfied"] is False
    assert plan.safety_validation["pedestrianInvariantVerified"] is True
    assert plan.status == "REJECTED_SAFETY_BOUNDS"


def test_min_green_certificate_accepts_feasible_plan():
    """When the cycle can hold the floors, each green meets max(min green, pedestrian clearance)."""
    optimizer = WebsterSignalOptimizer()
    approaches = [
        ApproachDemand("EB", "Eastbound", 800.0, lanes=2, min_green_sec=15.0, crosswalk_width_m=14.0),
        ApproachDemand("WB", "Westbound", 800.0, lanes=2, min_green_sec=15.0, crosswalk_width_m=14.0),
        ApproachDemand("NB", "Northbound", 350.0, lanes=1, min_green_sec=15.0, crosswalk_width_m=12.0),
        ApproachDemand("SB", "Southbound", 350.0, lanes=1, min_green_sec=15.0, crosswalk_width_m=12.0),
    ]
    plan = optimizer.compute_optimal_timing(
        intersection_id="INT-LEGAL-GREEN",
        approaches=approaches,
    )
    for phase, approach in zip(plan.phases, approaches):
        floor = max(approach.min_green_sec, phase.ped_clearance_sec)
        assert phase.green_sec >= floor
    assert plan.safety_validation["minGreenSatisfied"] is True
    assert plan.status == "REQUIRES_HUMAN_APPROVAL"


def test_api_get_intersection_optimal_timing_custom_intersection():
    """Verifies GET /api/v1/traffic/intersection/{id}/optimal-timing generates valid plan for non-hardcoded ID."""
    res = client.get("/api/v1/traffic/intersection/INT-ANYCITY-99/optimal-timing")
    assert res.status_code == 200
    plan = res.json()

    assert "INT-ANYCITY-99" in plan["intersectionId"]
    assert len(plan["phases"]) == 4
    assert 60 <= plan["targetCycleSec"] <= 150
    assert plan["safetyValidation"]["pedestrianInvariantVerified"] is True
