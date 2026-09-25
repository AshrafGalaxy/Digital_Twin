# Task 03: Arterial Coordination (Green Wave) Progression Offset Calculator

- **Task Identifier:** `TASK-03`
- **Domain:** Intelligent Traffic Mobility & Adaptive Corridor Control
- **Specification Reference:** [`TRAFFIC_MANAGEMENT.md`](../../FuturePlans/TRAFFIC_MANAGEMENT.md) Section 9.2
- **Component / Scope:** Simulation & Control
- **Priority:** High
- **Type:** Core Feature Implementation

---

## 1. Context & Objective

Arterial corridors with closely spaced signalized junctions (such as the $850\text{ m}$ link between Viman Nagar Chowk `INT-VN-01` and Somnath Nagar Chowk `INT-SN-01` along Nagar Road) suffer from severe stop-and-go delays if junctions operate uncoordinated. 

This task implements an **arterial coordination offset engine** that calculates the optimal phase offset ($\theta_{i, i+1}$) to establish bidirectional or directional green waves. Crucially, the engine incorporates a **downstream queue storage capacity invariant** to prevent platoons from slamming into standing queues.

---

## 2. Mathematical Formulation

### 2.1 Bandwidth Progression Offset
$$\theta_{i, i+1} = \frac{d_{i, i+1}}{v_{\text{progression}}} \pmod C$$

Where:
- $d_{i, i+1}$: Link center-line distance between sequential chowks extracted from PostGIS network geometry ($850\text{ m}$ on Nagar Road).
- $v_{\text{progression}}$: Target design progression speed ($40\text{ km/h} \approx 11.11\text{ m/s}$).
- $C$: Common corridor cycle length in seconds (synchronized across coordinated intersections, e.g., $90\text{s}$ or $110\text{s}$).
- $\theta_{i, i+1}$: Relative time offset in seconds for phase initiation at downstream intersection $i+1$.

*Numerical Baseline:*
$$t_{\text{travel}} = \frac{850\text{ m}}{11.11\text{ m/s}} \approx 76.5\text{ s}$$
$$\theta_{1, 2} = 76.5 \pmod{90} = 76.5\text{s} \approx \mathbf{76\text{s}} \quad (\text{or an advance of } -14\text{s})$$

### 2.2 Downstream Queue Storage Capacity Invariant
A standard progression offset assumes an empty downstream link. If a residual queue of length $Q_{\text{downstream}}$ exists at the downstream intersection, the arriving platoon will encounter the tail of the queue prematurely, creating deceleration shockwaves and link blockages.

The effective progression travel time must be adjusted by the queue clearing time:
$$t_{\text{effective}} = \frac{d_{i, i+1} - Q_{\text{downstream}}}{v_{\text{progression}}}$$
$$\theta_{\text{adjusted}} = \max\left(0, \; t_{\text{effective}} - \frac{Q_{\text{downstream}}}{v_{\text{dissipation}}}\right) \pmod C$$
Where $v_{\text{dissipation}}$ is the backward queue clearance wave speed (typically $18\text{ km/h} = 5.0\text{ m/s}$).

**Safety Invariant:** If $Q_{\text{downstream}} > 0.65 \times d_{i, i+1}$ ($>550\text{ m}$), corridor coordination must **suspend green wave progression** and switch to a **Queue-Flush Protocol** (gating upstream traffic) until the bottleneck dissipates.

---

## 3. Data Contracts & API Schema

```json
{
  "corridorId": "CORRIDOR-NAGAR-ROAD",
  "upstreamIntersectionId": "INT-VN-01",
  "downstreamIntersectionId": "INT-SN-01",
  "distanceMeters": 850.0,
  "commonCycleSec": 90,
  "progressionSpeedKmh": 40.0,
  "nominalOffsetSec": 76.5,
  "downstreamQueueMeters": 120.0,
  "adjustedOffsetSec": 62.0,
  "coordinationMode": "PROGRESSION_ACTIVE",
  "queueStorageRatio": 0.141,
  "safetyStatus": "ENVELOPE_VERIFIED",
  "provenance": {
    "sourceMode": "PREDICTED",
    "calculatedAt": "2026-09-25T16:30:00Z"
  }
}
```

---

## 4. Implementation Steps

1. **Create Coordination Module (`backend/services/arterial_coordinator.py`):**
   - Implement `class ArterialProgressionCoordinator`.
   - Method `calculate_progression_offset(upstream_id: str, downstream_id: str, common_cycle: int, downstream_queue_m: float) -> OffsetResult`.
2. **PostGIS Distance Integration:**
   - Retrieve accurate link distances directly from `road_network_topology` instead of relying on hardcoded constants.
3. **Safety Policy Hook (`backend/services/safety_validator.py`):**
   - Check $Q_{\text{downstream}} / d_{i, i+1}$. If $> 0.65$, set status to `QUEUE_FLUSH_REQUIRED` and raise alert.
4. **Endpoint Exposure (`backend/api/v1/endpoints/optimization.py`):**
   - Add `GET /api/v1/corridors/{id}/green-wave-offset`.
5. **Unit Tests (`tests/test_arterial_coordination.py`):**
   - Verify nominal offset calculation for $90\text{s}$ and $110\text{s}$ cycles.
   - Verify queue-adjusted offset decreases as downstream queue grows.
   - Verify queue spillback threshold ($>65\%$) triggers progression suspension.

---

## 5. Verification & Acceptance Criteria

- [ ] Offset is bounded within $[0, C - 1]$ seconds.
- [ ] Progression offset accounts for residual downstream queue length.
- [ ] Safety envelope suspends green wave when storage ratio exceeds 0.65.
- [ ] All unit tests pass hermetically: `pytest tests/test_arterial_coordination.py`.
