# Task 04: SUMO Multimodal Transit Bus Routes & Priority Simulation

- **Task Identifier:** `TASK-04`
- **Domain:** Intelligent Traffic Mobility & Adaptive Corridor Control
- **Specification Reference:** [`TRAFFIC_MANAGEMENT.md`](../../FuturePlans/TRAFFIC_MANAGEMENT.md) Section 7.2 & 8.2
- **Component / Scope:** Simulation & Modeling
- **Priority:** High
- **Type:** Simulation & Modeling Enhancement

---

## 1. Context & Objective

The existing SUMO simulation setup (`simulation/net/viman_nagar.net.xml`, `viman_nagar.rou.xml`) models general passenger car traffic along the corridor. 

However, urban arterials in India (such as Nagar Road) carry significant public transit volume (PMPML buses) alongside non-lane-based mixed traffic. This task models **scheduled public transit bus routes, physical bus stops, and dynamic Transit Signal Priority (TSP)** within the microscopic SUMO environment via the TraCI API. Furthermore, it calibrates the corridor's vehicle mix to mirror authentic Indian traffic conditions.

---

## 2. Microscopic Simulation & Priority Logic

### 2.1 Indian Mixed-Traffic Vehicle Fleet Calibration
Configure `vType` definitions in `simulation/routes/viman_nagar.rou.xml` with calibrated sub-lane parameters:

| Vehicle Class | Class ID | Proportion | Length | Width | Max Speed | Acceleration | Lateral Alignment |
|---|---|---|---|---|---|---|---|
| **Two-Wheeler** | `motorcycle` | 45% | 1.8 m | 0.8 m | 60 km/h | 2.5 m/s² | `arbitrary` (lane-filtering) |
| **Auto-Rickshaw** | `rickshaw` | 15% | 2.6 m | 1.3 m | 45 km/h | 1.8 m/s² | `sublane` |
| **Passenger Car** | `passenger` | 30% | 4.5 m | 1.8 m | 70 km/h | 2.2 m/s² | `center` |
| **Public Transit Bus** | `bus` | 10% | 12.0 m | 2.5 m | 50 km/h | 1.2 m/s² | `right` (curbside preference) |

### 2.2 Transit Signal Priority (TSP) TraCI Logic
When a transit bus trips an upstream detector $150\text{ m}$ upstream of `INT-VN-01` or `INT-SN-01`:

```text
Detector Tripped (Bus Detected, Distance: 150m, Speed: v_bus)
                       │
         Is Phase Currently Green for Bus Approach?
              ├── YES ──► Will green expire before bus reaches stop line?
              │                ├── YES ──► Extend Green by Δt (max +15s, within safety envelope)
              │                └── NO  ──► No intervention needed
              └── NO  ──► Can conflicting phase be truncated safely (g_conflicting >= g_min)?
                               ├── YES ──► Early Red Truncation (advance bus green)
                               └── NO  ──► Queue bus until standard cycle turnover
```

### 2.3 Person-Delay Evaluation Metric
Traditional signal optimization minimizes vehicle delay. With transit prioritization, we evaluate **person-delay**:
$$\text{Total Person Delay} = \sum_{v \in \text{Vehicles}} d_v \cdot O_v$$
Where average occupancy $O_{\text{car}} = 1.3$ passengers, $O_{\text{two\_wheeler}} = 1.1$, and $O_{\text{bus}} = 42.0$ passengers.

---

## 3. Data Contracts & Scenario Results

The simulation runner (`simulation/runner.py`) will output transit-specific KPIs:

```json
{
  "runId": "RUN-TSP-20260925-01",
  "templateId": "SCEN-TSP-01",
  "kpis": {
    "carAverageDelaySec": 28.4,
    "busAverageDelaySec": 11.2,
    "busDelayReductionPct": -60.5,
    "totalPersonDelayHours": 184.2,
    "personDelayReductionPct": -22.4,
    "transitPunctualityScore": 0.94
  },
  "provenance": {
    "sourceMode": "SIMULATION",
    "sumoVersion": "1.20.0",
    "seed": 42
  }
}
```

---

## 4. Implementation Steps

1. **Update Route & Network Files:**
   - Add bus stops in `viman_nagar.net.xml` (`bus_stop_vn_eb`, `bus_stop_sn_eb`, `bus_stop_phx_wb`).
   - Define PMPML bus schedules with realistic dwell times ($20\text{s} \pm 5\text{s}$).
2. **Implement TraCI TSP Controller (`simulation/tsp_controller.py`):**
   - Subscribe to inductive loop detectors $150\text{ m}$ ahead of intersection.
   - Implement `check_and_apply_tsp(traci_conn, junction_id, detector_id)`.
   - Apply green extension (`traci.trafficlight.setPhaseDuration`) or phase skip subject to minimum green bounds ($g_{\min} = 15\text{s}$).
3. **Extend Scenario Service (`backend/services/scenario_service.py`):**
   - Add template `SCEN-TSP-01` ("Multimodal Transit Signal Priority (PMPML)").
   - Parse transit person-delay metrics in `DeltaKPICalculator`.
4. **Hermetic Simulation Tests (`tests/test_sumo_simulation.py`):**
   - Verify headless simulation runs with bus routes without throwing TraCI errors.
   - Verify bus travel time decreases under TSP compared to fixed-time baseline.

---

## 5. Verification & Acceptance Criteria

- [ ] Bus routes and bus stops loaded in SUMO network without collision or teleport errors.
- [ ] TSP logic grants green extension without truncating pedestrian or conflicting phase minimums.
- [ ] Person-delay reduction is computed accurately and saved to `scenario_kpis` table.
- [ ] Hermetic tests pass cleanly: `pytest tests/test_sumo_simulation.py`.
