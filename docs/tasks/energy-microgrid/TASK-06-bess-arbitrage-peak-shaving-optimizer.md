# Task 06: BESS Battery Arbitrage & Time-of-Use Peak Shaving Optimizer

- **Task Identifier:** `TASK-06`
- **Domain:** Energy Management & Microgrid Optimization
- **Specification Reference:** [`ENERGY_MANAGEMENT.md`](../../FuturePlans/ENERGY_MANAGEMENT.md) Section 9.1
- **Primary Assignee:** Engineer 2 (Optimization & Control)
- **Priority:** High
- **Type:** Mathematical Optimization & Economic Dispatch

---

## 1. Context & Objective

Commercial power consumers face severe financial penalties for crossing contract demand thresholds alongside steep Time-of-Use (ToU) electricity tariffs (e.g., peak evening rates up to $2.5\times$ higher than off-peak solar/night hours).

Installing a Battery Energy Storage System (BESS) allows **tariff arbitrage** (charging during cheap off-peak/solar hours and discharging during evening peak hours) and **peak shaving** (discharging to cap building grid import below sanctioned contract limits).

This task implements the **BESS Battery Arbitrage & Peak Shaving Optimizer**. Formulated as a Mixed-Integer Linear Program (MILP) or convex optimization problem, the engine solves for the 24-hour charge/discharge schedule that minimizes net electricity cost while strictly respecting battery State-of-Charge (SoC) operating boundaries ($20\% \le SoC \le 90\%$), C-rate degradation limits, and transformer thermal capacity.

---

## 2. Mathematical Formulation

### 2.1 Economic Objective Function
$$\min \sum_{t=1}^{T} \left( C_{\text{tou}}(t) \cdot P_{\text{grid}}(t) \cdot \Delta t + C_{\text{peak}} \cdot \max_{t} [P_{\text{grid}}(t)] \right)$$

Where:
- $T = 24$ (Hourly or 15-minute time steps $\Delta t$).
- $C_{\text{tou}}(t)$: Time-of-Use volumetric electricity tariff ($\text{INR/kWh}$ or $\$ / \text{kWh}$).
  - Off-Peak (00:00–06:00): Base rate ($₹4.50/\text{kWh}$).
  - Solar Hours (09:00–16:00): Normal rate ($₹7.20/\text{kWh}$).
  - Peak Evening (18:00–22:00): Peak tariff ($₹11.80/\text{kWh}$).
- $C_{\text{peak}}$: Monthly contract demand penalty charge ($\text{INR/kVA}$ or $\text{INR/kW}$).
- $P_{\text{grid}}(t)$: Net active power imported from utility grid.

### 2.2 Microgrid Power Balance Constraint
$$P_{\text{grid}}(t) = P_{\text{load}}(t) - \hat{P}_{\text{pv}}(t) + P_{\text{bess,ch}}(t) - P_{\text{bess,dis}}(t)$$

### 2.3 Battery Physical & Degradation Constraints
1. **State of Charge (SoC) Dynamic Recursion:**
   $$SoC(t+1) = SoC(t) + \frac{P_{\text{bess,ch}}(t) \cdot \eta_{\text{ch}} - \frac{P_{\text{bess,dis}}(t)}{\eta_{\text{dis}}}}{E_{\text{bess,capacity}}} \cdot \Delta t$$
2. **Safe Operating Limits:**
   $$SoC_{\min} \le SoC(t) \le SoC_{\max} \quad (0.20 \le SoC(t) \le 0.90)$$
   (Prevents deep discharge degradation and dendrite plating).
3. **Power C-Rate Limits:**
   $$0 \le P_{\text{bess,ch}}(t) \le P_{\text{ch,max}} = 0.5 \cdot E_{\text{bess,capacity}} \quad (0.5C \text{ rate})$$
   $$0 \le P_{\text{bess,dis}}(t) \le P_{\text{dis,max}} = 1.0 \cdot E_{\text{bess,capacity}} \quad (1.0C \text{ rate})$$
4. **Non-Simultaneous Charge/Discharge Binary Invariant:**
   $$u_{\text{ch}}(t) + u_{\text{dis}}(t) \le 1 \quad \forall t \in \{1, \dots, T\}, \quad u \in \{0, 1\}$$
5. **Contract Demand Ceiling:**
   $$P_{\text{grid}}(t) \le P_{\text{contract\_demand\_limit}} \quad \forall t$$

---

## 3. Data Contracts & Recommendation Payload

```json
{
  "recommendationId": "REC-BESS-20260926-001",
  "facilityId": "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
  "generatedAt": "2026-09-26T12:00:00Z",
  "targetScheduleDate": "2026-09-26",
  "projectedCostSavingsInr": 18450.0,
  "peakShavingReductionKw": 840.0,
  "batteryCycleWearEquivalent": 0.82,
  "hourlySchedule": [
    {
      "hour": 2,
      "tariffRateInr": 4.50,
      "action": "CHARGE",
      "powerKw": 250.0,
      "targetSoCPct": 85.0
    },
    {
      "hour": 19,
      "tariffRateInr": 11.80,
      "action": "DISCHARGE",
      "powerKw": 450.0,
      "targetSoCPct": 28.0
    }
  ],
  "governanceNotice": "Advisory only. Requires human verification before central dispatch."
}
```

---

## 4. Step-by-Step Implementation Guide

1. **Optimization Solver:** Implement `backend/services/bess_optimizer.py` using SciPy Linear Programming (`scipy.optimize.linprog`) or PuLP/CBC MILP.
2. **Tariff Profile Engine:** Ingest dynamic ToU tariff schedules and demand penalty rules.
3. **Integration with Load & Solar Forecasts:** Pass inputs from Task 04 and Task 05 into the solver.
4. **REST Endpoints:** Expose `POST /api/v1/energy/optimize-bess` and `GET /api/v1/energy/bess/schedule`.
5. **Automated Tests:** Add hermetic tests in `tests/test_bess_optimizer.py` proving economic superiority ($>15\%$ cost reduction) vs unmanaged baseline.

---

## 5. Architectural Invariants Checklist (`AGENTS.md`)
- [ ] **Strict Non-Actuation:** Optimization produces advisory schedules; direct battery BMS commands require authorized human sign-off.
- [ ] **State Separation Invariant:** Optimizer results are written to `recommendations` and never overwrite measured twin state.
- [ ] **Strictly Zero Emojis:** Zero emojis in code, logs, and UI schemas.
