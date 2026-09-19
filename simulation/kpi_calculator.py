"""
kpi_calculator.py

Standardized Key Performance Indicator (KPI) calculator for SUMO microscopic simulation
and scenario evaluation on the Nagar Road pilot corridor.
Follows ADR-004 specification for baseline vs. intervention comparison.
"""

from typing import Any, Dict, Optional
import numpy as np


class ScenarioKPICalculator:
    """
    Computes arterial performance indicators and comparative deltas between
    baseline (SCEN-BASE-01) and mobility intervention (SCEN-INT-01) runs.
    """

    @staticmethod
    def calculate_deltas(
        baseline_kpis: Dict[str, float],
        intervention_kpis: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculates percentage changes from baseline to intervention.
        Negative deltas in delay/travel time/queue indicate improvements.
        Positive deltas in throughput indicate capacity improvement.
        """
        deltas = {}
        
        # 1. Travel time delta (%)
        base_tt = baseline_kpis.get("average_travel_time_sec", 0.0)
        int_tt = intervention_kpis.get("average_travel_time_sec", 0.0)
        if base_tt > 0:
            deltas["travel_time_delta_pct"] = round(((int_tt - base_tt) / base_tt) * 100.0, 2)
            deltas["travel_time_saved_sec"] = round(base_tt - int_tt, 1)

        # 2. Delay delta (%)
        base_delay = baseline_kpis.get("average_delay_sec", 0.0)
        int_delay = intervention_kpis.get("average_delay_sec", 0.0)
        if base_delay > 0:
            deltas["delay_delta_pct"] = round(((int_delay - base_delay) / base_delay) * 100.0, 2)
            deltas["delay_saved_sec"] = round(base_delay - int_delay, 1)

        # 3. p95 Queue length delta (%)
        base_q = baseline_kpis.get("p95_queue_length_meters", 0.0)
        int_q = intervention_kpis.get("p95_queue_length_meters", 0.0)
        if base_q > 0:
            deltas["queue_length_delta_pct"] = round(((int_q - base_q) / base_q) * 100.0, 2)
            deltas["queue_reduced_meters"] = round(base_q - int_q, 1)

        # 4. Throughput delta (%)
        base_tp = baseline_kpis.get("throughput_veh_per_hour", 0.0)
        int_tp = intervention_kpis.get("throughput_veh_per_hour", 0.0)
        if base_tp > 0:
            deltas["throughput_delta_pct"] = round(((int_tp - base_tp) / base_tp) * 100.0, 2)
            deltas["additional_throughput_vph"] = round(int_tp - base_tp, 1)

        # Summary verdict
        is_improved = (
            deltas.get("delay_delta_pct", 0.0) < -5.0 and
            deltas.get("queue_length_delta_pct", 0.0) < -5.0
        )
        deltas["overall_verdict"] = "POSITIVE_MOBILITY_IMPACT" if is_improved else "NEUTRAL_OR_MARGINAL"

        return deltas

    @staticmethod
    def aggregate_vehicle_records(
        completed_travel_times: list,
        waiting_times: list,
        sampled_queue_lengths: list,
        simulation_duration_sec: float = 3600.0
    ) -> Dict[str, float]:
        """
        Aggregates raw vehicle and edge simulation step measurements into standardized KPIs.
        """
        avg_travel_time = float(np.mean(completed_travel_times)) if completed_travel_times else 0.0
        avg_delay = float(np.mean(waiting_times)) if waiting_times else 0.0
        p95_queue = float(np.percentile(sampled_queue_lengths, 95)) if sampled_queue_lengths else 0.0
        
        # Throughput scaled to vehicles per hour
        n_completed = len(completed_travel_times)
        throughput_vph = round((n_completed / max(1.0, simulation_duration_sec)) * 3600.0, 1)

        return {
            "average_travel_time_sec": round(avg_travel_time, 2),
            "average_delay_sec": round(avg_delay, 2),
            "p95_queue_length_meters": round(p95_queue, 2),
            "throughput_veh_per_hour": throughput_vph
        }
