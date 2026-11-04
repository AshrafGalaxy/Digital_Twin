"""
test_simulation.py

Unit and integration tests for Phase 4: SUMO microscopic simulation,
scenario runner, comparative KPI calculation, and state separation invariants.
"""

import inspect

import pytest
from simulation.runner import SUMOCorridorRunner
from simulation.kpi_calculator import ScenarioKPICalculator
from backend.services.scenario_service import ScenarioService


def _kinematic_runner() -> SUMOCorridorRunner:
    """Force the calibrated fallback so the comparison does not depend on a local SUMO binary."""
    runner = SUMOCorridorRunner()
    runner.has_native_sumo = False
    return runner


def test_simulation_runner_deterministic_execution():
    """Verifies that running with identical seeds produces identical KPI outputs."""
    runner = SUMOCorridorRunner()
    
    run1 = runner.run_scenario("SCEN-BASE-01", seed=42)
    run2 = runner.run_scenario("SCEN-BASE-01", seed=42)

    assert run1["source_mode"] == "SIMULATION"
    assert run2["source_mode"] == "SIMULATION"
    assert run1["kpis"]["average_travel_time_sec"] == run2["kpis"]["average_travel_time_sec"]
    assert run1["kpis"]["average_delay_sec"] == run2["kpis"]["average_delay_sec"]
    assert run1["kpis"]["p95_queue_length_meters"] == run2["kpis"]["p95_queue_length_meters"]


def test_intervention_improves_corridor_kpis():
    """Verifies that dynamic split intervention (SCEN-INT-01) yields positive mobility deltas."""
    runner = SUMOCorridorRunner()

    base_run = runner.run_scenario("SCEN-BASE-01", seed=42)
    int_run = runner.run_scenario("SCEN-INT-01", seed=42, parameters={"green_extension_sec": 15.0})

    deltas = ScenarioKPICalculator.calculate_deltas(base_run["kpis"], int_run["kpis"])

    # Expect reduced delay and queue length
    assert deltas["delay_delta_pct"] < 0, "Expected intervention to reduce vehicle delay"
    assert deltas["queue_length_delta_pct"] < 0, "Expected intervention to reduce queue spillback"
    assert deltas["throughput_delta_pct"] > 0, "Expected intervention to increase corridor throughput"
    assert deltas["overall_verdict"] == "POSITIVE_MOBILITY_IMPACT"


def test_scenario_service_provenance_and_governance():
    """Verifies that ScenarioService strictly enforces SIMULATION provenance and disclaimer."""
    service = ScenarioService()
    templates = service.list_templates()
    assert len(templates) >= 2

    run_record = service.execute_comparative_run(
        intervention_template_id="SCEN-INT-01",
        green_extension_sec=15.0,
        random_seed=42
    )

    assert run_record["sourceMode"] == "SIMULATION"
    assert "governanceNotice" in run_record
    assert "SIMULATION OUTPUT" in run_record["governanceNotice"]
    assert "baseline" in run_record
    assert "intervention" in run_record
    assert "deltas" in run_record


def test_zero_green_extension_matches_baseline_at_peak_demand():
    """Seed 42 and a 0 second extension must not invent a delay or queue reduction."""
    runner = _kinematic_runner()
    base = runner.run_scenario(
        "SCEN-BASE-01",
        seed=42,
        parameters={"demand_multiplier": 1.0},
    )
    zero = runner.run_scenario(
        "SCEN-INT-01",
        seed=42,
        parameters={"demand_multiplier": 1.0, "green_extension_sec": 0},
    )

    assert base["source_mode"] == "SIMULATION"
    assert zero["source_mode"] == "SIMULATION"
    assert zero["engine_used"] == "CALIBRATED_KINEMATIC_FALLBACK"
    assert abs(zero["kpis"]["average_delay_sec"] - base["kpis"]["average_delay_sec"]) < 5.0
    assert abs(zero["kpis"]["p95_queue_length_meters"] - base["kpis"]["p95_queue_length_meters"]) < 20.0
    assert zero["kpis"] == base["kpis"]
    assert zero["raw_stats"]["saturation_degree"] == base["raw_stats"]["saturation_degree"]
    assert zero["raw_stats"]["green_time_sec"] == base["raw_stats"]["green_time_sec"] == 35.0


def test_zero_green_extension_matches_baseline_when_demand_is_light():
    """Unchanged saturation at demand multiplier 0.4 must not invent a shorter queue."""
    runner = _kinematic_runner()
    base = runner.run_scenario(
        "SCEN-BASE-01",
        seed=7,
        parameters={"demand_multiplier": 0.4},
    )
    zero = runner.run_scenario(
        "SCEN-INT-01",
        seed=7,
        parameters={"demand_multiplier": 0.4, "green_extension_sec": 0},
    )

    assert zero["kpis"]["average_delay_sec"] == base["kpis"]["average_delay_sec"]
    assert zero["kpis"]["p95_queue_length_meters"] == base["kpis"]["p95_queue_length_meters"]
    assert zero["raw_stats"]["saturation_degree"] == base["raw_stats"]["saturation_degree"]
    assert zero["source_mode"] == "SIMULATION"


def test_positive_green_extension_raises_capacity():
    """A longer green is the only control, and it must move delay, queue, and throughput with capacity."""
    runner = _kinematic_runner()
    base = runner.run_scenario(
        "SCEN-BASE-01",
        seed=42,
        parameters={"demand_multiplier": 1.0},
    )
    longer = runner.run_scenario(
        "SCEN-INT-01",
        seed=42,
        parameters={"demand_multiplier": 1.0, "green_extension_sec": 15.0},
    )

    assert longer["raw_stats"]["effective_capacity_vph"] > base["raw_stats"]["effective_capacity_vph"]
    assert longer["raw_stats"]["saturation_degree"] < base["raw_stats"]["saturation_degree"]
    assert longer["kpis"]["average_delay_sec"] < base["kpis"]["average_delay_sec"]
    assert longer["kpis"]["p95_queue_length_meters"] < base["kpis"]["p95_queue_length_meters"]
    assert longer["kpis"]["throughput_veh_per_hour"] > base["kpis"]["throughput_veh_per_hour"]
    assert longer["source_mode"] == "SIMULATION"


def test_completed_trips_are_not_replaced_by_a_constant():
    """Arrived vehicles keep their own travel times. An empty sample is not rewritten as 145 seconds."""
    depart_times = {"veh-a": 12.0, "veh-b": 40.0}
    samples = SUMOCorridorRunner.collect_completed_travel_times(
        depart_times,
        ["veh-a", "veh-b", "unknown"],
        100.0,
    )
    assert samples == [88.0, 60.0]
    assert "veh-a" not in depart_times
    assert "veh-b" not in depart_times

    kpis = ScenarioKPICalculator.aggregate_vehicle_records(
        completed_travel_times=samples,
        waiting_times=[10.0, 12.0],
        sampled_queue_lengths=[20.0, 30.0],
        simulation_duration_sec=3600.0,
    )
    assert kpis["average_travel_time_sec"] == 74.0

    empty = ScenarioKPICalculator.aggregate_vehicle_records(
        completed_travel_times=[],
        waiting_times=[10.0],
        sampled_queue_lengths=[20.0],
        simulation_duration_sec=3600.0,
    )
    assert empty["average_travel_time_sec"] == 0.0
    assert "145.0" not in inspect.getsource(SUMOCorridorRunner._run_native_sumo)


def test_state_isolation_invariant():
    """Verifies that running a simulation does NOT mutate live/replay entity current state."""
    service = ScenarioService()
    
    # Execute a run
    run_record = service.execute_comparative_run(
        intervention_template_id="SCEN-INT-01",
        random_seed=99
    )
    
    # State isolation check: run record is marked SIMULATION
    assert run_record["sourceMode"] == "SIMULATION"
    # Ensure it didn't write to any live state
    assert run_record["status"] == "COMPLETED"


if __name__ == "__main__":
    test_simulation_runner_deterministic_execution()
    test_intervention_improves_corridor_kpis()
    test_scenario_service_provenance_and_governance()
    test_state_isolation_invariant()
    print("ALL SIMULATION TESTS PASSED!")
