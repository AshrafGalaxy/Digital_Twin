"""
bess_optimizer.py

Battery Energy Storage System (BESS) 24-Hour Battery Arbitrage and Peak Shaving Optimizer (ENERGY-06).
Formulates a convex Linear Program (LP) solved via scipy.optimize.linprog(method='highs')
across a 24-hour planning horizon (T=24, dt=1.0 hour).
Minimizes total electricity cost under dynamic Time-of-Use (ToU) tariffs and monthly maximum demand charges,
while strictly respecting battery State-of-Charge (SoC) operating boundaries, C-rate degradation limits,
and transformer contract demand headroom.

Mathematical Formulation:
Minimize:
    sum_{t=0}^{23} (C_tou(t) * P_grid(t) * dt) + C_peak * P_peak_max + epsilon * sum_{t=0}^{23} (P_ch(t) + P_dis(t))

Subject to:
    1. Power Balance:
       P_grid(t) - P_feedin(t) - P_ch(t) + P_dis(t) = P_load(t) - P_solar(t)  for all t in 0..23
    2. State of Charge (SoC) Dynamics:
       E(0) = E_init + (P_ch(0) * eta_ch - P_dis(0) / eta_dis) * dt
       E(t) = E(t-1) + (P_ch(t) * eta_ch - P_dis(t) / eta_dis) * dt  for all t in 1..23
       where eta_ch = eta_dis = sqrt(0.885) (~0.940744)
    3. Safe Operating Envelope:
       0.20 * E_cap <= E(t) <= 0.90 * E_cap  for all t in 0..23
    4. C-Rate Degradation Limits:
       0 <= P_ch(t) <= 0.5 * E_cap (1000 kW for 2000 kWh pack)
       0 <= P_dis(t) <= 1.0 * E_cap (2000 kW for 2000 kWh pack)
    5. Peak Demand Envelope:
       P_grid(t) <= P_peak_max  for all t in 0..23
       P_grid(t) <= P_contract_limit (3500 kW)  for all t in 0..23
    6. End-of-Horizon Replenishment:
       SoC(23) >= SoC_init - 0.05
"""

from datetime import datetime, timezone
import logging
import math
import threading
from typing import Any, Dict, List, Optional
import uuid

import numpy as np
from pydantic import BaseModel, ConfigDict, Field
from scipy.optimize import linprog

logger = logging.getLogger("digital_twin.energy.bess_optimizer")


class HourlyScheduleItem(BaseModel):
    """
    Hourly dispatch setpoint and electrical telemetry result for BESS optimization.
    """
    model_config = ConfigDict(populate_by_name=True)

    hour: int = Field(..., ge=0, le=23, description="Hour of day (0 to 23)")
    tariffRateInr: float = Field(..., description="Time-of-Use electricity tariff in INR/kWh")
    action: str = Field(..., description="Battery action: CHARGE, DISCHARGE, or STANDBY")
    powerKw: float = Field(..., ge=0.0, description="Active battery power magnitude in kW")
    targetSoCPct: float = Field(..., ge=0.0, le=100.0, description="Battery State of Charge percentage")
    loadKw: float = Field(..., description="Facility demand load in kW")
    solarKw: float = Field(..., description="On-site solar PV generation in kW")
    gridImportKw: float = Field(..., ge=0.0, description="Net active power imported from utility grid in kW")
    feedinKw: float = Field(..., ge=0.0, description="Excess generation exported or curtailed in kW")
    storedEnergyKwh: float = Field(..., ge=0.0, description="Stored battery energy in kWh at end of hour")
    netPowerKw: float = Field(..., description="Net battery power in kW (positive: discharging, negative: charging)")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class BessOptimizationRequest(BaseModel):
    """
    Request payload schema for BESS 24-hour economic dispatch optimization.
    Supports both snake_case and camelCase field aliases.
    """
    model_config = ConfigDict(populate_by_name=True)

    facility_id: str = Field(
        default="urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        alias="facilityId",
        description="Target facility or building entity identifier"
    )
    target_schedule_date: Optional[str] = Field(
        default=None,
        alias="targetScheduleDate",
        description="Target date for the 24-hour dispatch schedule (YYYY-MM-DD)"
    )
    initial_soc_pct: float = Field(
        default=50.0,
        alias="initialSocPct",
        ge=0.0,
        le=100.0,
        description="Initial battery State of Charge percentage at start of horizon"
    )
    custom_load_profile_kw: Optional[List[float]] = Field(
        default=None,
        alias="customLoadProfileKw",
        description="Optional 24-hour facility active load profile in kW"
    )
    custom_solar_profile_kw: Optional[List[float]] = Field(
        default=None,
        alias="customSolarProfileKw",
        description="Optional 24-hour solar PV generation profile in kW"
    )
    contract_demand_ceiling_kw: float = Field(
        default=3500.0,
        alias="contractDemandCeilingKw",
        gt=0.0,
        description="Sanctioned maximum grid contract demand limit in kW"
    )
    demand_penalty_rate_inr: float = Field(
        default=650.0,
        alias="demandPenaltyRateInr",
        ge=0.0,
        description="Monthly maximum demand penalty rate in INR/kW"
    )
    custom_tariff_profile_inr: Optional[List[float]] = Field(
        default=None,
        alias="customTariffProfileInr",
        description="Optional 24-hour Time-of-Use tariff profile in INR/kWh"
    )
    capacity_kwh: float = Field(
        default=2000.0,
        alias="capacityKwh",
        gt=0.0,
        description="Total battery storage capacity in kWh"
    )

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class BessOptimizationResult(BaseModel):
    """
    Standardized advisory result payload for BESS 24-hour economic dispatch optimization.
    """
    model_config = ConfigDict(populate_by_name=True)

    recommendationId: str = Field(..., description="Unique recommendation tracking identifier")
    facilityId: str = Field(..., description="Target facility or building entity identifier")
    generatedAt: str = Field(..., description="ISO 8601 UTC timestamp when optimization was computed")
    targetScheduleDate: str = Field(..., description="Target schedule date (YYYY-MM-DD)")
    projectedCostSavingsInr: float = Field(..., description="Net projected daily electricity cost savings in INR")
    costSavingsPct: float = Field(..., description="Percentage cost reduction relative to unmanaged baseline")
    peakShavingReductionKw: float = Field(..., description="Maximum grid peak demand reduction achieved in kW")
    batteryCycleWearEquivalent: float = Field(..., description="Equivalent full battery cycles consumed over 24 hours")
    unmanagedPeakKw: float = Field(..., description="Maximum grid import peak under unmanaged baseline in kW")
    optimizedPeakKw: float = Field(..., description="Maximum grid import peak under optimized BESS schedule in kW")
    unmanagedCostInr: float = Field(..., description="Total unmanaged electricity cost in INR")
    optimizedCostInr: float = Field(..., description="Total optimized electricity cost in INR")
    hourlySchedule: List[HourlyScheduleItem] = Field(..., description="24-hour step-by-step dispatch schedule")
    governanceNotice: str = Field(
        default="Advisory only. Requires human verification before central dispatch.",
        description="Non-actuation governance advisory notice"
    )
    provenance: Dict[str, Any] = Field(..., description="Traceable data provenance and solver metadata")

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(by_alias=True)


class BessOptimizer:
    """
    24-Hour Battery Energy Storage System (BESS) Arbitrage and Peak Shaving Optimizer.
    Uses SciPy Linear Programming with the HiGHS interior point / simplex solver.
    """

    DEFAULT_CAPACITY_KWH: float = 2000.0
    DEFAULT_SOC_MIN: float = 0.20
    DEFAULT_SOC_MAX: float = 0.90
    DEFAULT_C_RATE_CHARGE: float = 0.5
    DEFAULT_C_RATE_DISCHARGE: float = 1.0
    ROUND_TRIP_EFFICIENCY: float = 0.885
    ONE_WAY_EFFICIENCY: float = math.sqrt(0.885)  # approx 0.940744386
    DEFAULT_CONTRACT_CEILING_KW: float = 3500.0
    DEFAULT_DEMAND_PENALTY_RATE_INR: float = 650.0
    REGULARIZATION_EPSILON: float = 0.0001

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._schedule_cache: Dict[str, Dict[str, Any]] = {}

    def get_default_load_profile(self) -> List[float]:
        """
        Returns standard 24-hour commercial facility load profile in kW (range 950 to 3100 kW).
        Models off-peak base load, morning business ramp, afternoon sustained demand,
        evening peak retail banquet hours (18:00 to 21:00), and late evening drop.
        """
        return [
            950.0, 950.0, 950.0, 950.0, 950.0, 950.0,
            1500.0, 1800.0, 2200.0, 2400.0, 2550.0, 2600.0,
            2650.0, 2600.0, 2550.0, 2500.0, 2600.0, 2750.0,
            3100.0, 3100.0, 2700.0, 2400.0, 1600.0, 1200.0
        ]

    def get_default_solar_profile(self) -> List[float]:
        """
        Returns standard 24-hour rooftop solar PV generation profile in kW for a 1000 kWp array.
        Zero generation overnight (18:00 to 06:00), rising smoothly to peak at midday (~1000 kW).
        """
        return [
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 120.0, 380.0, 680.0, 890.0, 980.0,
            1000.0, 960.0, 850.0, 620.0, 350.0, 90.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ]

    def get_default_tariff_profile(self) -> List[float]:
        """
        Returns standard 24-hour Time-of-Use (ToU) volumetric tariff in INR/kWh:
        - Off-Peak (00:00 to 06:00): INR 4.50 / kWh
        - Normal / Solar Hours (06:00 to 18:00): INR 7.20 / kWh
        - Peak Evening (18:00 to 22:00): INR 11.80 / kWh
        - Post-Peak Night (22:00 to 24:00): INR 7.20 / kWh
        """
        return [4.5] * 6 + [7.2] * 12 + [11.8] * 4 + [7.2] * 2

    def optimize_24h_schedule(
        self,
        facility_id: str = "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        target_schedule_date: Optional[str] = None,
        initial_soc_pct: float = 50.0,
        custom_load_profile_kw: Optional[List[float]] = None,
        custom_solar_profile_kw: Optional[List[float]] = None,
        contract_demand_ceiling_kw: Optional[float] = None,
        demand_penalty_rate_inr: Optional[float] = None,
        custom_tariff_profile_inr: Optional[List[float]] = None,
        capacity_kwh: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Solves the 24-hour BESS arbitrage and peak shaving linear program using scipy.optimize.linprog(method='highs').
        Caches and returns the optimization result dictionary conforming to BessOptimizationResult.
        """
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        schedule_date = target_schedule_date or now_dt.strftime("%Y-%m-%d")

        # 1. Parameter resolution and physical bound normalization
        e_cap = float(capacity_kwh) if capacity_kwh is not None and capacity_kwh > 0 else self.DEFAULT_CAPACITY_KWH
        p_contract = (
            float(contract_demand_ceiling_kw)
            if contract_demand_ceiling_kw is not None and contract_demand_ceiling_kw > 0
            else self.DEFAULT_CONTRACT_CEILING_KW
        )
        c_peak = (
            float(demand_penalty_rate_inr)
            if demand_penalty_rate_inr is not None and demand_penalty_rate_inr >= 0
            else self.DEFAULT_DEMAND_PENALTY_RATE_INR
        )

        # Normalize SoC input: if provided as percentage (e.g. 50.0), scale to fraction (0.50)
        soc_init_val = float(initial_soc_pct)
        if soc_init_val > 1.0:
            soc_init = soc_init_val / 100.0
        else:
            soc_init = soc_init_val
        soc_init = min(self.DEFAULT_SOC_MAX, max(self.DEFAULT_SOC_MIN, soc_init))

        # 2. Ingest 24-hour profiles
        if custom_load_profile_kw is not None and len(custom_load_profile_kw) == 24:
            load = np.array([float(v) for v in custom_load_profile_kw], dtype=np.float64)
        else:
            load = np.array(self.get_default_load_profile(), dtype=np.float64)

        if custom_solar_profile_kw is not None and len(custom_solar_profile_kw) == 24:
            solar = np.array([max(0.0, float(v)) for v in custom_solar_profile_kw], dtype=np.float64)
        else:
            solar = np.array(self.get_default_solar_profile(), dtype=np.float64)

        if custom_tariff_profile_inr is not None and len(custom_tariff_profile_inr) == 24:
            c_tou = np.array([float(v) for v in custom_tariff_profile_inr], dtype=np.float64)
        else:
            c_tou = np.array(self.get_default_tariff_profile(), dtype=np.float64)

        # 3. Formulate Linear Program (LP)
        # Decision variables layout:
        # Index 0..23:   P_grid(t)   [24 vars]  (Grid import in kW)
        # Index 24..47:  P_feedin(t) [24 vars]  (Grid export/curtailment in kW)
        # Index 48..71:  P_ch(t)     [24 vars]  (Battery charging power in kW)
        # Index 72..95:  P_dis(t)    [24 vars]  (Battery discharging power in kW)
        # Index 96..119: E(t)        [24 vars]  (Stored energy at end of hour t in kWh)
        # Index 120:     P_peak_max  [1 var]    (Auxiliary peak grid import scalar in kW)
        num_vars = 121
        dt = 1.0
        eta_ch = self.ONE_WAY_EFFICIENCY
        eta_dis = self.ONE_WAY_EFFICIENCY
        p_ch_max = self.DEFAULT_C_RATE_CHARGE * e_cap
        p_dis_max = self.DEFAULT_C_RATE_DISCHARGE * e_cap
        e_min = self.DEFAULT_SOC_MIN * e_cap
        e_max = self.DEFAULT_SOC_MAX * e_cap
        eps = self.REGULARIZATION_EPSILON

        # Objective vector c:
        # c = sum(C_tou(t) * P_grid(t) * dt) + C_peak * P_peak_max + eps * sum(P_ch(t) + P_dis(t))
        c_obj = np.zeros(num_vars, dtype=np.float64)
        c_obj[0:24] = c_tou * dt
        c_obj[24:48] = 0.0
        c_obj[48:72] = eps
        c_obj[72:96] = eps
        c_obj[96:120] = 0.0
        c_obj[120] = c_peak

        # Variable Bounds
        var_bounds: List[Tuple[Optional[float], Optional[float]]] = []
        # P_grid: 0 <= P_grid(t) <= P_contract
        var_bounds.extend([(0.0, p_contract)] * 24)
        # P_feedin: 0 <= P_feedin(t) <= None
        var_bounds.extend([(0.0, None)] * 24)
        # P_ch: 0 <= P_ch(t) <= 0.5 * E_cap (1000 kW)
        var_bounds.extend([(0.0, p_ch_max)] * 24)
        # P_dis: 0 <= P_dis(t) <= 1.0 * E_cap (2000 kW)
        var_bounds.extend([(0.0, p_dis_max)] * 24)
        # E: e_min <= E(t) <= e_max (20% to 90% SoC)
        var_bounds.extend([(e_min, e_max)] * 24)
        # P_peak_max: 0 <= P_peak_max <= P_contract
        var_bounds.append((0.0, p_contract))

        # Equality Constraints: A_eq * x = b_eq
        # 1) Power Balance (24 equations):
        #    P_grid(t) - P_feedin(t) - P_ch(t) + P_dis(t) = P_load(t) - P_solar(t)
        # 2) Energy Recursion (24 equations):
        #    For t=0: E(0) - eta_ch * dt * P_ch(0) + (dt / eta_dis) * P_dis(0) = E_init
        #    For t>0: E(t) - E(t-1) - eta_ch * dt * P_ch(t) + (dt / eta_dis) * P_dis(t) = 0
        a_eq = np.zeros((48, num_vars), dtype=np.float64)
        b_eq = np.zeros(48, dtype=np.float64)

        for t in range(24):
            # Power balance
            a_eq[t, t] = 1.0
            a_eq[t, 24 + t] = -1.0
            a_eq[t, 48 + t] = -1.0
            a_eq[t, 72 + t] = 1.0
            b_eq[t] = load[t] - solar[t]

            # Energy recursion
            row = 24 + t
            a_eq[row, 96 + t] = 1.0
            if t > 0:
                a_eq[row, 96 + t - 1] = -1.0
            else:
                b_eq[row] = soc_init * e_cap
            a_eq[row, 48 + t] = -eta_ch * dt
            a_eq[row, 72 + t] = (1.0 / eta_dis) * dt

        # Inequality Constraints: A_ub * x <= b_ub
        # 1) Peak envelope (24 inequalities):
        #    P_grid(t) - P_peak_max <= 0
        # 2) End-of-horizon replenishment (1 inequality):
        #    SoC(23) >= SoC_init - 0.05  =>  -E(23) <= -max(SoC_min, SoC_init - 0.05) * E_cap
        a_ub = np.zeros((25, num_vars), dtype=np.float64)
        b_ub = np.zeros(25, dtype=np.float64)

        for t in range(24):
            a_ub[t, t] = 1.0
            a_ub[t, 120] = -1.0
            b_ub[t] = 0.0

        replenish_target = max(self.DEFAULT_SOC_MIN, soc_init - 0.05) * e_cap
        a_ub[24, 96 + 23] = -1.0
        b_ub[24] = -replenish_target

        # 4. Solve Convex Linear Program with HiGHS
        res = linprog(
            c=c_obj,
            A_ub=a_ub,
            b_ub=b_ub,
            A_eq=a_eq,
            b_eq=b_eq,
            bounds=var_bounds,
            method="highs",
        )

        if not res.success:
            logger.error("BESS linear program failed to converge: %s", res.message)
            raise RuntimeError(f"BESS optimization failed: {res.message}")

        sol = res.x
        opt_p_grid = sol[0:24]
        opt_p_feedin = sol[24:48]
        opt_p_ch = sol[48:72]
        opt_p_dis = sol[72:96]
        opt_energy = sol[96:120]
        opt_p_peak = float(sol[120])

        # 5. Compute unmanaged baseline and financial impact
        # In unmanaged baseline, battery does not operate (P_ch = 0, P_dis = 0)
        net_unmanaged = np.maximum(0.0, load - solar)
        unmanaged_energy_cost = float(np.sum(c_tou * net_unmanaged * dt))
        unmanaged_peak_kw = float(np.max(net_unmanaged))
        unmanaged_peak_cost = float(c_peak * unmanaged_peak_kw)
        unmanaged_total_cost = unmanaged_energy_cost + unmanaged_peak_cost

        opt_energy_cost = float(np.sum(c_tou * opt_p_grid * dt))
        opt_peak_cost = float(c_peak * opt_p_peak)
        opt_total_cost = opt_energy_cost + opt_peak_cost

        projected_savings_inr = max(0.0, unmanaged_total_cost - opt_total_cost)
        cost_savings_pct = (
            (projected_savings_inr / unmanaged_total_cost * 100.0)
            if unmanaged_total_cost > 0.0
            else 0.0
        )
        peak_shaving_reduction_kw = max(0.0, unmanaged_peak_kw - opt_p_peak)

        # Equivalent cycle wear: total discharged kWh / usable capacity
        total_discharge_kwh = float(np.sum(opt_p_dis * dt))
        usable_capacity_kwh = (self.DEFAULT_SOC_MAX - self.DEFAULT_SOC_MIN) * e_cap
        cycle_wear_equivalent = (
            round(total_discharge_kwh / usable_capacity_kwh, 2)
            if usable_capacity_kwh > 0.0
            else 0.0
        )

        # 6. Build hourly dispatch schedule
        hourly_schedule: List[Dict[str, Any]] = []
        for t in range(24):
            ch_kw = float(opt_p_ch[t])
            dis_kw = float(opt_p_dis[t])
            soc_pct = float(opt_energy[t] / e_cap * 100.0)

            # Determine distinct operating action
            if ch_kw > 0.1:
                action = "CHARGE"
                power_kw = round(ch_kw, 2)
                net_power = -power_kw
            elif dis_kw > 0.1:
                action = "DISCHARGE"
                power_kw = round(dis_kw, 2)
                net_power = power_kw
            else:
                action = "STANDBY"
                power_kw = 0.0
                net_power = 0.0

            hourly_schedule.append({
                "hour": t,
                "tariffRateInr": round(float(c_tou[t]), 2),
                "action": action,
                "powerKw": power_kw,
                "targetSoCPct": round(soc_pct, 1),
                "loadKw": round(float(load[t]), 2),
                "solarKw": round(float(solar[t]), 2),
                "gridImportKw": round(float(opt_p_grid[t]), 2),
                "feedinKw": round(float(opt_p_feedin[t]), 2),
                "storedEnergyKwh": round(float(opt_energy[t]), 2),
                "netPowerKw": round(net_power, 2)
            })

        rec_uuid = str(uuid.uuid4())[:8].upper()
        date_clean = schedule_date.replace("-", "")
        recommendation_id = f"REC-BESS-{date_clean}-{rec_uuid}"

        provenance = {
            "sourceMode": "PREDICTED",
            "generatedAt": now_iso,
            "qualityScore": 1.0,
            "qualityStatus": "VERIFIED",
            "solver": "scipy.optimize.linprog(method='highs')",
            "planningHorizonHours": 24,
            "timeStepHours": 1.0,
            "roundTripEfficiency": self.ROUND_TRIP_EFFICIENCY
        }

        result = {
            "recommendationId": recommendation_id,
            "facilityId": facility_id,
            "generatedAt": now_iso,
            "targetScheduleDate": schedule_date,
            "projectedCostSavingsInr": round(projected_savings_inr, 2),
            "costSavingsPct": round(cost_savings_pct, 2),
            "peakShavingReductionKw": round(peak_shaving_reduction_kw, 2),
            "batteryCycleWearEquivalent": cycle_wear_equivalent,
            "unmanagedPeakKw": round(unmanaged_peak_kw, 2),
            "optimizedPeakKw": round(opt_p_peak, 2),
            "unmanagedCostInr": round(unmanaged_total_cost, 2),
            "optimizedCostInr": round(opt_total_cost, 2),
            "hourlySchedule": hourly_schedule,
            "governanceNotice": "Advisory only. Requires human verification before central dispatch.",
            "provenance": provenance
        }

        # Cache active schedule
        self.cache_schedule(facility_id, result)

        logger.info(
            "BESS 24h optimization succeeded for facility %s: savings=INR %.2f (%.1f%%), peak reduction=%.1f kW",
            facility_id,
            projected_savings_inr,
            cost_savings_pct,
            peak_shaving_reduction_kw
        )

        return result

    def get_active_schedule(
        self,
        facility_id: str,
        auto_generate: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves active optimization schedule for facility_id from cache.
        If auto_generate is True and schedule is not found, computes default schedule on the fly.
        """
        with self._lock:
            if facility_id in self._schedule_cache:
                return self._schedule_cache[facility_id]

            # Check normalized suffix alias (e.g. BLD-PHOENIX-01)
            for cached_id, sched in self._schedule_cache.items():
                if facility_id in cached_id or cached_id in facility_id:
                    return sched

        if auto_generate:
            return self.optimize_24h_schedule(facility_id=facility_id)

        return None

    def cache_schedule(self, facility_id: str, schedule: Dict[str, Any]) -> None:
        """
        Thread-safely stores an optimization schedule in the in-memory cache.
        """
        with self._lock:
            self._schedule_cache[facility_id] = schedule

    def clear_cache(self) -> None:
        """
        Clears the in-memory schedule cache.
        """
        with self._lock:
            self._schedule_cache.clear()


# Module-level singleton instance
bess_optimizer = BessOptimizer()

__all__ = [
    "BessOptimizer",
    "bess_optimizer",
    "HourlyScheduleItem",
    "BessOptimizationRequest",
    "BessOptimizationResult",
]
