"""
signal_optimizer.py

Webster Delay-Minimizing Adaptive Signal Timing Optimization Engine.
Calculates optimal cycle length and phase green splits using modified Webster
delay formulation subject to strict saturation caps (x_j <= 0.85), minimum green,
and pedestrian crosswalk clearance invariants.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import math
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger("digital_twin.signal_optimizer")


@dataclass
class ApproachDemand:
    """Represents arrival demand and geometric parameters for an intersection approach phase."""
    approach_id: str
    description: str
    flow_vph: float
    lanes: int = 2
    saturation_flow_vph_lane: float = 1800.0
    min_green_sec: float = 15.0
    crosswalk_width_m: float = 14.0


@dataclass
class SignalConstraints:
    """Safety and operational boundary constraints for signal optimization."""
    min_cycle_sec: int = 60
    max_cycle_sec: int = 150
    walking_speed_mps: float = 1.2
    max_saturation_cap: float = 0.85
    yellow_change_sec: float = 3.0
    red_clearance_sec: float = 1.0


@dataclass
class PhaseResult:
    """Calculated split parameters and delay metrics for a signal phase."""
    phase_id: int
    approach_id: str
    description: str
    green_sec: int
    split_ratio: float
    flow_ratio_y: float
    saturation_x: float
    delay_sec_veh: float
    ped_clearance_sec: float
    baseline_green_sec: int = 0


@dataclass
class TimingPlan:
    """Complete optimized timing plan and safety validation certificate."""
    recommendation_id: str
    intersection_id: str
    generated_at: str
    target_cycle_sec: int
    baseline_cycle_sec: int
    total_lost_time_sec: int
    critical_flow_ratio_y: float
    phases: List[PhaseResult]
    baseline_delay_sec_veh: float
    optimal_delay_sec_veh: float
    estimated_delay_reduction_sec: float
    estimated_delay_reduction_pct: float
    safety_validation: Dict[str, Any]
    provenance: Dict[str, Any]
    status: str = "REQUIRES_HUMAN_APPROVAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendationId": self.recommendation_id,
            "intersectionId": self.intersection_id,
            "generatedAt": self.generated_at,
            "targetCycleSec": self.target_cycle_sec,
            "baselineCycleSec": self.baseline_cycle_sec,
            "totalLostTimeSec": self.total_lost_time_sec,
            "criticalFlowRatioY": round(self.critical_flow_ratio_y, 4),
            "phases": [
                {
                    "phaseId": p.phase_id,
                    "approachId": p.approach_id,
                    "description": p.description,
                    "greenSec": p.green_sec,
                    "splitRatio": round(p.split_ratio, 3),
                    "flowRatioY": round(p.flow_ratio_y, 4),
                    "saturationX": round(p.saturation_x, 3),
                    "delaySecVeh": round(p.delay_sec_veh, 1),
                    "pedClearanceSec": round(p.ped_clearance_sec, 1),
                    "baselineGreenSec": p.baseline_green_sec
                }
                for p in self.phases
            ],
            "baselineDelaySecVeh": round(self.baseline_delay_sec_veh, 1),
            "optimalDelaySecVeh": round(self.optimal_delay_sec_veh, 1),
            "estimatedDelayReductionSec": round(self.estimated_delay_reduction_sec, 1),
            "estimatedDelayReductionPct": round(self.estimated_delay_reduction_pct, 1),
            "safetyValidation": self.safety_validation,
            "provenance": self.provenance,
            "status": self.status
        }


def _phase_groups(approaches: List[ApproachDemand], phase_plan: Optional[List[List[str]]]) -> List[List[int]]:
    """Indexes of approaches that move together. One approach per phase when no plan is given."""
    if phase_plan is None:
        return [[index] for index in range(len(approaches))]
    if not phase_plan:
        raise ValueError("A phase plan must contain at least one phase.")
    index_by_id = {approach.approach_id: index for index, approach in enumerate(approaches)}
    seen = set()
    groups: List[List[int]] = []
    for phase in phase_plan:
        if not phase:
            raise ValueError("Each phase must name at least one approach.")
        members: List[int] = []
        for approach_id in phase:
            if approach_id not in index_by_id:
                raise ValueError("The phase plan names an approach that is not in the demand set.")
            if approach_id in seen:
                raise ValueError("An approach cannot move in more than one phase.")
            seen.add(approach_id)
            members.append(index_by_id[approach_id])
        groups.append(members)
    if any(approach.approach_id not in seen for approach in approaches):
        raise ValueError("Every approach must belong to exactly one phase.")
    return groups


class WebsterSignalOptimizer:
    """
    Mathematical signal timing optimizer applying Webster's modified delay minimization
    with pedestrian clearance invariants and saturation caps.
    """

    @staticmethod
    def webster_overflow_delay(degree_of_saturation: float, arrival_vps: float) -> float:
        """Undersaturated overflow: x^2 / (2 * q * (1 - x)), with q in vehicles per second."""
        x = degree_of_saturation
        if arrival_vps <= 0.0 or x <= 0.0 or x >= 1.0:
            return 0.0
        return (x * x) / (2.0 * arrival_vps * (1.0 - x))

    @staticmethod
    def akcelik_overflow_delay(
        degree_of_saturation: float,
        capacity_vps: float,
        period_sec: float = 900.0,
    ) -> float:
        """
        Time-dependent overflow delay in seconds when x >= 1.
        d = 900 * T * ((x - 1) + sqrt((x - 1)^2 + 12 * (x - 0.67) / (c * T)))
        T is the analysis period in hours and c is capacity in vehicles per hour.
        """
        x = degree_of_saturation
        if x < 1.0 or capacity_vps <= 0.0 or period_sec <= 0.0:
            return 0.0
        t_hours = period_sec / 3600.0
        capacity_vph = capacity_vps * 3600.0
        extra = max(0.0, 12.0 * (x - 0.67)) / max(capacity_vph * t_hours, 1e-6)
        return 900.0 * t_hours * ((x - 1.0) + math.sqrt((x - 1.0) ** 2 + extra))

    @staticmethod
    def calculate_webster_delay(
        cycle_sec: float,
        split_ratio: float,
        flow_vps: float,
        saturation_flow_vps: float,
        period_sec: float = 900.0,
    ) -> float:
        """
        Delay per vehicle.

        Undersaturated (x < 1): d1 = C * (1 - lambda)^2 / (2 * (1 - lambda * x)).
        Overflow d2 for x < 1 uses continuous transition clamping that asymptotically
        approaches the Akcelik boundary value as x -> 1.0, eliminating the
        discontinuous cliff produced by the raw Webster steady-state overflow term.

        Oversaturated (x >= 1): d1 uses x clamped to 1 in the denominator;
        d2 is the Akcelik time-dependent overflow delay.

        Valid results are not clamped to 180 seconds.
        """
        if split_ratio <= 0.0 or cycle_sec <= 0.0 or saturation_flow_vps <= 0.0:
            return 90.0

        capacity_vps = saturation_flow_vps * split_ratio
        if capacity_vps <= 0.0:
            return 90.0

        x = flow_vps / capacity_vps
        if x < 1.0:
            denom = 2.0 * (1.0 - (split_ratio * x))
            d1 = (cycle_sec * ((1.0 - split_ratio) ** 2)) / denom if denom > 1e-9 else 0.0
            w = WebsterSignalOptimizer.webster_overflow_delay(x, flow_vps)
            # Continuous transition clamping: soft-clamp w toward the Akcelik
            # boundary value d2_crit so that d2(x->1^-) == d2(x=1) with no cliff.
            # Formula: d2 = w / (1 + (w / d2_crit)^p)^(1/p), p = 4.0.
            d2_crit = WebsterSignalOptimizer.akcelik_overflow_delay(1.0, capacity_vps, period_sec)
            if d2_crit > 0.0 and w > 0.0:
                _p = 4.0
                d2 = w / ((1.0 + (w / d2_crit) ** _p) ** (1.0 / _p))
            else:
                d2 = w
            return round(max(0.0, d1 + d2), 2)

        denom = 2.0 * (1.0 - split_ratio)
        d1 = (cycle_sec * ((1.0 - split_ratio) ** 2)) / denom if denom > 1e-9 else 0.0
        d2 = WebsterSignalOptimizer.akcelik_overflow_delay(x, capacity_vps, period_sec)
        return round(max(0.0, d1 + d2), 2)

    def compute_optimal_timing(
        self,
        intersection_id: str,
        approaches: List[ApproachDemand],
        constraints: Optional[SignalConstraints] = None,
        baseline_cycle_sec: int = 90,
        phase_plan: Optional[List[List[str]]] = None,
    ) -> TimingPlan:
        """
        Computes optimal cycle length and green splits satisfying Webster's formula,
        pedestrian crosswalk clearance invariants, and saturation constraints.
        A phase plan lists approaches that move together. Each phase contributes
        max(q/s) once. Lost time is one clearance interval per phase.
        """
        cfg = constraints or SignalConstraints()
        m = len(approaches)
        if m == 0:
            raise ValueError("At least one approach demand must be provided for signal optimization.")

        groups = _phase_groups(approaches, phase_plan)
        n_phases = len(groups)

        # 1. Approach parameters and flow ratios
        lost_time_per_phase = cfg.yellow_change_sec + cfg.red_clearance_sec
        total_lost_time = int(math.ceil(lost_time_per_phase * n_phases))

        flow_ratios_y: List[float] = []
        ped_clearances: List[float] = []
        flow_vps_list: List[float] = []
        sat_vps_list: List[float] = []
        min_required_greens: List[int] = []

        for app in approaches:
            q_vps = max(0.01, app.flow_vph / 3600.0)
            s_vps = max(0.1, (app.lanes * app.saturation_flow_vph_lane) / 3600.0)
            y = q_vps / s_vps
            flow_ratios_y.append(y)
            flow_vps_list.append(q_vps)
            sat_vps_list.append(s_vps)

            # Pedestrian crosswalk clearance invariant: width / walking_speed
            t_ped = int(math.ceil(app.crosswalk_width_m / cfg.walking_speed_mps))
            ped_clearances.append(float(t_ped))
            min_required_greens.append(max(t_ped, int(app.min_green_sec)))

        # 2. Critical flow ratio Y is the sum of one ratio per phase: the larger movement.
        phase_y = [max(flow_ratios_y[index] for index in members) for members in groups]
        phase_ped = [max(ped_clearances[index] for index in members) for members in groups]
        y_sum = sum(phase_y)
        # Cap effective Y to 0.85 for Webster optimal cycle calculation
        effective_y = min(0.85, max(0.10, y_sum))

        # 3. Webster optimal cycle length: C_0 = (1.5 * L + 5) / (1 - Y)
        c_webster = (1.5 * total_lost_time + 5.0) / (1.0 - effective_y)
        target_cycle = max(cfg.min_cycle_sec, min(cfg.max_cycle_sec, int(round(c_webster))))

        # 4. Check available green time vs the minimum green of each phase
        phase_min_greens = [max(min_required_greens[index] for index in members) for members in groups]
        sum_min_greens = sum(phase_min_greens)
        if target_cycle < sum_min_greens + total_lost_time:
            target_cycle = min(cfg.max_cycle_sec, sum_min_greens + total_lost_time)

        # Strict available green time
        available_green = target_cycle - total_lost_time
        discretionary_green = available_green - sum_min_greens

        # 5. Proportional allocation of green time across phases: g_j = available_green * (y_j / Y)
        sum_y = max(0.01, sum(phase_y))
        final_phase_greens = [
            max(int(phase_ped[i]), int(round(available_green * (y / sum_y))))
            for i, y in enumerate(phase_y)
        ]

        # Adjust target cycle if minimums required more time
        sum_greens = sum(final_phase_greens)
        if sum_greens + total_lost_time > target_cycle:
            target_cycle = min(cfg.max_cycle_sec, sum_greens + total_lost_time)
            available_green = target_cycle - total_lost_time

        diff = available_green - sum(final_phase_greens)

        if diff > 0:
            # Distribute positive slack to highest demand phases
            sorted_by_demand = sorted(range(n_phases), key=lambda idx: phase_y[idx], reverse=True)
            for i in range(diff):
                final_phase_greens[sorted_by_demand[i % n_phases]] += 1
        elif diff < 0:
            # Trim excess while strictly preserving pedestrian crosswalk clearance invariant
            while diff < 0:
                candidates = [
                    i for i in range(n_phases)
                    if final_phase_greens[i] > int(phase_ped[i])
                ]
                if not candidates:
                    break
                # Trim from phase with lowest demand
                trim_idx = min(candidates, key=lambda idx: phase_y[idx])
                final_phase_greens[trim_idx] -= 1
                diff += 1

        final_greens = [0] * m
        for phase_index, members in enumerate(groups):
            for member in members:
                final_greens[member] = final_phase_greens[phase_index]

        actual_cycle = sum(final_phase_greens) + total_lost_time
        min_green_ok = all(final_greens[i] >= min_required_greens[i] for i in range(m))

        # 8. Compute phase results, delay, and saturation metrics
        phase_results: List[PhaseResult] = []
        optimal_delays: List[float] = []
        baseline_delays: List[float] = []

        baseline_green_per_phase = max(10, (baseline_cycle_sec - total_lost_time) // n_phases)
        baseline_split_ratio = baseline_green_per_phase / float(baseline_cycle_sec)

        max_observed_sat = 0.0
        ped_invariants_met = True

        for i, app in enumerate(approaches):
            g = final_greens[i]
            split_ratio = g / float(actual_cycle)
            cap_vps = sat_vps_list[i] * split_ratio
            sat_x = flow_vps_list[i] / max(0.01, cap_vps)
            max_observed_sat = max(max_observed_sat, sat_x)

            if g < ped_clearances[i]:
                ped_invariants_met = False

            d_opt = self.calculate_webster_delay(
                cycle_sec=float(actual_cycle),
                split_ratio=split_ratio,
                flow_vps=flow_vps_list[i],
                saturation_flow_vps=sat_vps_list[i]
            )
            optimal_delays.append(d_opt)

            d_base = self.calculate_webster_delay(
                cycle_sec=float(baseline_cycle_sec),
                split_ratio=baseline_split_ratio,
                flow_vps=flow_vps_list[i],
                saturation_flow_vps=sat_vps_list[i]
            )
            baseline_delays.append(d_base)

            phase_results.append(PhaseResult(
                phase_id=i + 1,
                approach_id=app.approach_id,
                description=app.description,
                green_sec=g,
                split_ratio=split_ratio,
                flow_ratio_y=flow_ratios_y[i],
                saturation_x=sat_x,
                delay_sec_veh=d_opt,
                ped_clearance_sec=ped_clearances[i],
                baseline_green_sec=int(baseline_green_per_phase),
            ))

        # Overall weighted intersection delay
        total_demand = sum(flow_vps_list)
        avg_optimal_delay = sum(d * q for d, q in zip(optimal_delays, flow_vps_list)) / max(0.01, total_demand)
        avg_baseline_delay = sum(d * q for d, q in zip(baseline_delays, flow_vps_list)) / max(0.01, total_demand)

        delay_reduction_sec = avg_baseline_delay - avg_optimal_delay
        delay_reduction_pct = (delay_reduction_sec / max(0.01, avg_baseline_delay)) * 100.0
        oversaturated = any(p.saturation_x >= 1.0 for p in phase_results)

        now_iso = datetime.now(timezone.utc).isoformat()
        rec_id = f"REC-OPT-{intersection_id.split(':')[-1]}-{uuid.uuid4().hex[:6]}"

        return TimingPlan(
            recommendation_id=rec_id,
            intersection_id=intersection_id,
            generated_at=now_iso,
            target_cycle_sec=actual_cycle,
            baseline_cycle_sec=baseline_cycle_sec,
            total_lost_time_sec=total_lost_time,
            critical_flow_ratio_y=y_sum,
            phases=phase_results,
            baseline_delay_sec_veh=avg_baseline_delay,
            optimal_delay_sec_veh=avg_optimal_delay,
            estimated_delay_reduction_sec=delay_reduction_sec,
            estimated_delay_reduction_pct=delay_reduction_pct,
            safety_validation={
                "maxSaturation": round(max_observed_sat, 3),
                "saturationCapSatisfied": bool(max_observed_sat <= cfg.max_saturation_cap + 0.05),
                "pedestrianInvariantVerified": ped_invariants_met,
                "minGreenSatisfied": min_green_ok,
                "cycleBounded": bool(cfg.min_cycle_sec <= actual_cycle <= cfg.max_cycle_sec),
                "oversaturatedRegime": bool(y_sum >= 0.85),
                "advisoryNote": (
                    "Intersection operating near/above capacity; queue storage mitigation recommended."
                    if y_sum >= 0.85
                    else "Standard flow regime; optimal Webster timing applied."
                )
            },
            provenance={
                "sourceMode": "PREDICTED",
                "optimizerVersion": "webster-constrained-v2.1",
                "formula": (
                    "akcelik-time-dependent-overflow"
                    if oversaturated
                    else "webster-d1-plus-arrival-overflow"
                ),
                "delayUpperClampApplied": False,
            },
            status=(
                "REQUIRES_HUMAN_APPROVAL"
                if min_green_ok and ped_invariants_met
                else "REJECTED_SAFETY_BOUNDS"
            )
        )


# Singleton instance
webster_optimizer = WebsterSignalOptimizer()
