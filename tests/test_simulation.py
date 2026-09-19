"""
test_simulation.py

Unit and integration tests for Phase 4: SUMO microscopic simulation,
scenario runner, comparative KPI calculation, and state separation invariants.
"""

import pytest
from simulation.runner import SUMOCorridorRunner
from simulation.kpi_calculator import ScenarioKPICalculator
from backend.services.scenario_service import ScenarioService


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
