# Task 02: Webster Adaptive Signal Timing Optimization Engine

- **Task Identifier:** `TASK-02`
- **Domain:** Intelligent Traffic Mobility & Adaptive Corridor Control
- **Specification Reference:** [`TRAFFIC_MANAGEMENT.md`](../../FuturePlans/TRAFFIC_MANAGEMENT.md) Section 9.1
- **Component / Scope:** Simulation & Control
- **Priority:** High
- **Type:** Core Feature Implementation

---

## 1. Context & Objective

Currently, signal optimization in `backend/services/rule_engine.py` generates heuristic split extensions (+5s to +15s) based on fixed queue threshold bounds. 

This task implements a **rigorous mathematical optimizer** using the **modified Webster delay minimization formulation under saturation and safety constraints**. The engine computes optimal cycle lengths ($C$) and phase green splits ($g_j$) that minimize overall junction delay while guaranteeing pedestrian clearance safety invariants and preventing queue collapse ($x_j \le 0.85$).

---

## 2. Mathematical Formulation

### 2.1 Webster Total Delay Minimization Objective
$$\min \sum_{j=1}^{M} D_j = \sum_{j=1}^{M} \left[ \frac{C (1 - \lambda_j)^2}{2(1 - \lambda_j x_j)} + \frac{x_j^2}{2 q_j (1 - x_j)} \right]$$

Where:
- $M$: Number of signal phases (typically 4 stages for standard dual-ring arterial chowks).
- $C$: Total signal cycle length in seconds ($60\text{s} \le C \le 150\text{s}$).
- $\lambda_j = \frac{g_j}{C}$: Green split ratio for phase $j$.
- $q_j$: Arrival flow rate on phase approach $j$ ($\text{vehicles/second}$).
- $s_j$: Saturation flow rate on phase approach $j$ (typically $1800 \text{ veh/hr/lane} = 0.50 \text{ veh/s/lane}$).
- $x_j = \frac{q_j}{s_j \lambda_j}$: Degree of saturation on phase $j$.

### 2.2 Optimal Cycle Length (Webster Formula)
$$C_0 = \frac{1.5 L + 5}{1 - Y}$$
Where:
- $L = \sum_{j=1}^{M} l_j$: Total lost time per cycle (amber + all-red clearance, typically $4\text{s} \times 4\text{ phases} = 16\text{s}$).
- $Y = \sum_{j=1}^{M} y_j = \sum_{j=1}^{M} \frac{q_j}{s_j}$: Critical flow ratio sum ($Y < 0.90$ for stability).
- Clamped bounds: $C = \max(60, \min(150, \text{round}(C_0)))$.

### 2.3 Hard Operational & Safety Constraints
1. **Degree of Saturation Cap:**
   $$x_j \le 0.85 \quad \forall j \in \{1, \dots, M\}$$
   Prevents hyper-congested queue collapse where residual queues carry over into subsequent cycles.
2. **Phase Green Bounds:**
   $$g_{\min} \le g_j \le g_{\max} \quad (15\text{s} \le g_j \le 75\text{s})$$
3. **Pedestrian Crosswalk Clearance Invariant:**
   $$g_j \ge t_{\text{ped\_clearance}} = \frac{\text{crosswalk\_width}}{1.2\text{ m/s}}$$
   For a $14\text{ m}$ arterial width, $g_j \ge 11.67\text{s} \rightarrow \mathbf{12\text{s}}$ minimum green under all conditions. No optimization may ever violate this safety bound.

---

## 3. Data Contracts & Recommendation Payload

The output of the optimizer must conform to the canonical advisory recommendation schema:

```json
{
  "recommendationId": "REC-VN-20260925-01",
  "intersectionId": "INT-VN-01",
  "generatedAt": "2026-09-25T16:25:00Z",
  "targetCycleSec": 110,
  "baselineCycleSec": 90,
  "phases": [
    {"phaseId": 1, "description": "Nagar Road EB/WB Through", "greenSec": 45, "saturationX": 0.72},
    {"phaseId": 2, "description": "Nagar Road EB/WB Right Turn", "greenSec": 25, "saturationX": 0.68},
    {"phaseId": 3, "description": "Viman Nagar North Approach", "greenSec": 22, "saturationX": 0.78},
    {"phaseId": 4, "description": "Pedestrian & Minor Approach", "greenSec": 18, "saturationX": 0.40}
  ],
  "estimatedDelayReductionSec": 14.8,
  "safetyValidation": {
    "maxSaturation": 0.78,
    "pedestrianInvariantVerified": true,
    "minGreenSatisfied": true
  },
  "provenance": {
    "sourceMode": "PREDICTED",
    "optimizerVersion": "webster-constrained-v2.1"
  },
  "status": "REQUIRES_HUMAN_APPROVAL"
}
```

---

## 4. Implementation Steps

1. **Create Optimizer Module (`backend/services/signal_optimizer.py`):**
   - Implement `class WebsterSignalOptimizer`.
   - Method `compute_optimal_timing(approaches: list[ApproachDemand], constraints: SignalConstraints) -> TimingPlan`.
   - Calculate critical ratios $y_j = q_j / s_j$, cycle time $C$, and allocate effective green time proportionally:
     $$g_j = (C - L) \cdot \frac{y_j}{Y}$$
   - Apply boundary enforcement: if $g_j < g_{\min}$ or $g_j < t_{\text{ped}}$, clamp and redistribute remaining slack time to critical phases while keeping $x_j \le 0.85$.
2. **Integrate with Recommendation Engine (`backend/services/rule_engine.py`):**
   - Call `WebsterSignalOptimizer` when detector occupancy $> 0.65$ or queue $> 50\text{m}$.
   - Attach safety verification metadata (`pedestrianInvariantVerified=True`, `maxSaturation <= 0.85`).
3. **Database Persistence:**
   - Store recommendation in the `timing_recommendations` table with status `REQUIRES_HUMAN_APPROVAL`.
4. **Hermetic Test Suite (`tests/test_signal_optimizer.py`):**
   - Test balanced flow conditions.
   - Test extreme unbalanced demand (heavy arterial flow vs minor side-street).
   - Test pedestrian invariant enforcement: ensure crosswalk clearance time is NEVER truncated even if side-street volume is near zero.

---

## 5. Verification & Acceptance Criteria

- [ ] All phase green splits satisfy $g_j \ge t_{\text{ped}}$ ($14\text{m} / 1.2\text{m/s} = 12\text{s}$).
- [ ] No phase exceeds degree of saturation $x_j > 0.85$.
- [ ] Sum of green phases + lost time equals target cycle $C \in [60\text{s}, 150\text{s}]$.
- [ ] All tests in `tests/test_signal_optimizer.py` pass hermetically with zero failures.
