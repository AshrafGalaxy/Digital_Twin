# Task 01: Canonical Level of Service (LOS) & Hydrodynamic State Engine

- **Task Identifier:** `TASK-01`
- **Domain:** Intelligent Traffic Mobility & Adaptive Corridor Control
- **Specification Reference:** [`TRAFFIC_MANAGEMENT.md`](../../FuturePlans/TRAFFIC_MANAGEMENT.md) Section 7.1
- **Primary Assignee:** Engineer 1 (Backend & Telemetry)
- **Priority:** High
- **Type:** Architectural Enhancement / Gap Fix

---

## 1. Context & Objective

Currently, the Level of Service (LOS A–F) indicator is calculated superficially on the frontend client (`TrafficAnalyticsView.tsx`) using only a raw speed threshold check. 

In a production digital twin, Level of Service and hydrodynamic state must be **canonically calculated on the server** during state projection and aggregate rollups. The calculation must adhere to the **Indian Highway Capacity Manual (IRC:106 guidelines)** combining both space-mean speed ($v$) and volume-to-capacity ratio ($V/C = q / C_{\text{veh}}$). This ensures consistency across APIs, simulation calibrators, ML feature stores, and frontend dashboards.

---

## 2. Mathematical & Algorithmic Formulation

### 2.1 Hydrodynamic Continuity & Fundamental Relationship
$$\text{Flow Rate: } q = k \cdot v$$
$$\text{Continuity: } \frac{\partial k}{\partial t} + \frac{\partial q}{\partial x} = 0$$

Where:
- $q$: Flow rate ($\text{vehicles/hour}$ or $\text{PCU/hour}$).
- $k$: Traffic density ($\text{vehicles/km}$).
- $v$: Space-mean speed ($\text{km/h}$).

### 2.2 Normalized Congestion Index (CI)
$$CI = \min\left(1.0, \; \max\left(0.0, \; 1.0 - \frac{v_{\text{observed}}}{v_{\text{free}}}\right)\right)$$
Where $v_{\text{free}}$ is the link design speed (default: $50.0\text{ km/h}$ for 6-lane urban divided arterial).

### 2.3 IRC:106 Level of Service Criteria for Urban Arterials

| Level of Service (LOS) | Volume-to-Capacity Ratio ($V/C$) | Space-Mean Speed ($v$) | Operational Condition |
|---|---|---|---|
| **LOS A** | $V/C \le 0.35$ | $v \ge 50.0\text{ km/h}$ | Free flow; low density; individual speeds unhindered. |
| **LOS B** | $0.35 < V/C \le 0.50$ | $v \ge 40.0\text{ km/h}$ | Reasonably free flow; minor restriction on maneuvering. |
| **LOS C** | $0.50 < V/C \le 0.70$ | $v \ge 30.0\text{ km/h}$ | Stable flow; maneuvers noticeably restricted by traffic. |
| **LOS D** | $0.70 < V/C \le 0.85$ | $v \ge 22.0\text{ km/h}$ | Approaching unstable flow; high density; queues form at signals. |
| **LOS E** | $0.85 < V/C \le 1.00$ | $v \ge 15.0\text{ km/h}$ | Unstable flow; operation at or near corridor design capacity. |
| **LOS F** | $V/C > 1.00$ | $v < 15.0\text{ km/h}$ | Forced/breakdown flow; severe queue spillback; stop-and-go. |

*Boundary Condition:* If $V/C$ and speed suggest differing LOS grades, the worse grade is selected to represent actual driver delay truthfully.

---

## 3. Database Schema & Data Contracts

Update the SQLite / TimescaleDB schema in `backend/core/schema_migrator.py` to persist canonical hydrodynamic states:

```sql
-- Add columns to entity_current_state or traffic_15m_aggregates
ALTER TABLE entity_current_state ADD COLUMN level_of_service TEXT DEFAULT 'C';
ALTER TABLE entity_current_state ADD COLUMN volume_capacity_ratio REAL DEFAULT 0.0;
ALTER TABLE entity_current_state ADD COLUMN congestion_index REAL DEFAULT 0.0;
ALTER TABLE entity_current_state ADD COLUMN density_veh_km REAL DEFAULT 0.0;
```

Canonical JSON API Response contract:
```json
{
  "segmentId": "SEG-NR-EB-01",
  "averageSpeed": {"value": 24.5, "unit": "km/h", "qualityScore": 0.98},
  "volumeVehHr": {"value": 2150, "unit": "veh/h", "qualityScore": 0.97},
  "capacityVehHr": {"value": 3600, "unit": "veh/h", "qualityScore": 1.00},
  "volumeCapacityRatio": 0.597,
  "densityVehKm": 87.75,
  "congestionIndex": 0.51,
  "levelOfService": "C",
  "provenance": {
    "sourceMode": "REPLAY",
    "observedAt": "2026-09-25T16:20:00Z"
  }
}
```

---

## 4. Implementation Steps

1. **Service Layer Implementation (`backend/services/traffic_state_service.py`):**
   - Create function `calculate_los(volume_veh_hr: float, speed_kmh: float, capacity_veh_hr: float = 3600.0) -> tuple[str, float, float, float]`.
   - Calculate $V/C$, density $k = q / \max(v, 1.0)$, Congestion Index $CI$, and IRC:106 LOS grade (`A` through `F`).
2. **State Projection & Rollup Update:**
   - In `project_current_state()` and `aggregate_15m()`, compute and write `level_of_service`, `volume_capacity_ratio`, and `congestion_index` into `entity_current_state` and `traffic_15m_aggregates`.
3. **Endpoint Integration (`backend/api/v1/endpoints/state.py`):**
   - Ensure `GET /api/v1/state/corridor` and `GET /api/v1/road-segments/{id}` expose `levelOfService` and `volumeCapacityRatio`.
4. **Hermetic Unit Tests (`tests/test_traffic_state.py`):**
   - Test free-flow conditions (speed $52\text{ km/h}$, $V/C = 0.25 \rightarrow \text{LOS A}$).
   - Test breakdown/choke conditions (speed $8\text{ km/h}$, $V/C = 1.15 \rightarrow \text{LOS F}$).
   - Test zero-division resilience when speed is $0.0\text{ km/h}$.

---

## 5. Verification & Acceptance Criteria

- [ ] `calculate_los()` correctly maps all IRC:106 thresholds with zero exceptions.
- [ ] `levelOfService` and `volumeCapacityRatio` are persisted to database state.
- [ ] Zero emojis in any log messages or API payloads.
- [ ] Hermetic tests pass: `pytest tests/test_traffic_state.py -v`.
