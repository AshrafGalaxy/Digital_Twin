# Task 06: Multimodal Transit Stop Crowd Flow & Dynamic Dwell Time Forecasting

- **Task Identifier:** `TASK-06`
- **Domain:** Intelligent Traffic Mobility & Adaptive Corridor Control
- **Specification Reference:** [`TRAFFIC_MANAGEMENT.md`](../../FuturePlans/TRAFFIC_MANAGEMENT.md) Section 8.2
- **Primary Assignee:** Engineer 4 (ML & Forecasting)
- **Priority:** Medium
- **Type:** Machine Learning & Transit Intelligence

---

## 1. Context & Objective

Transit Signal Priority (TSP) often fails in practice because fixed estimates of bus arrival time ignore **unpredictable passenger dwell times at curbside bus stops**. If a signal gives an early green extension while a bus is still boarding passengers, valuable green time is wasted while arterial side-streets queue up.

This task develops a **transit stop crowd flow and dynamic dwell time forecaster**. Using privacy-preserving optical/Time-of-Flight (ToF) passenger count sensors at corridor bus stops (e.g., Viman Nagar Bus Bay and Phoenix Marketcity Stop), the model predicts passenger boarding counts and vehicle dwell duration, informing the TSP controller exactly when the bus will re-enter traffic.

---

## 2. Mathematical Formulation & Architecture

### 2.1 Dynamic Dwell Time Model
$$t_{\text{dwell}} = t_{\text{door}} + \beta \cdot N_{\text{boarding}} + \gamma \cdot N_{\text{alighting}} + \epsilon$$

Where:
- $t_{\text{door}}$: Mechanical door opening and clearance time ($3.5\text{s}$).
- $N_{\text{boarding}}$: Forecasted number of waiting passengers boarding the incoming bus.
- $N_{\text{alighting}}$: Forecasted number of alighting passengers.
- $\beta$: Average boarding marginal headway ($1.8\text{ s/passenger}$ for stepped Indian transit buses).
- $\gamma$: Average alighting marginal headway ($1.2\text{ s/passenger}$).
- $\epsilon$: Stochastic disturbance capturing ticketing delay or baggage handling.

### 2.2 Bus Stop Crowd Surge & Platform Density
$$\text{Crowd Density } D_{\text{stop}} = \frac{N_{\text{waiting}}}{A_{\text{platform}}} \quad (\text{passengers/m}^2)$$

Where $A_{\text{platform}}$ is the effective shelter waiting area ($45.0\text{ m}^2$).
- **Safety Invariant:** If $D_{\text{stop}} > 2.5\text{ pax/m}^2$, issue an operational surge alert to municipal transit dispatch to inject short-loop feeder buses.

### 2.3 TSP Synchronization Hook
The forecasted departure timestamp $T_{\text{ready}} = T_{\text{arrival}} + t_{\text{dwell}}$ is streamed to the TSP controller (Task 04). The controller withholds the green extension request until $T_{\text{ready}} - 8\text{s}$, eliminating wasted phase time.

---

## 3. Data Contracts & Ingestion Schema

MQTT Telemetry Topic:
`citytwin/v1/live/transit/nagar_road/crowd_sensor/STOP-VN-01`

Payload:
```json
{
  "stopId": "STOP-VN-01",
  "stopName": "Viman Nagar Chowk Bus Bay",
  "observedAt": "2026-09-25T16:40:00Z",
  "waitingPassengers": 28,
  "platformAreaM2": 45.0,
  "crowdDensityPaxM2": 0.62,
  "surgeRisk": "LOW",
  "predictedDwellTimeSec": {
    "expected": 38.5,
    "confidenceInterval90": [32.0, 46.2]
  },
  "provenance": {
    "sourceMode": "LIVE",
    "sensorType": "TOF_OPTICAL_GRID",
    "qualityScore": 0.99
  }
}
```

---

## 4. Implementation Steps

1. **Schema Migration (`backend/core/schema_migrator.py`):**
   - Create tables `transit_stop_observations` and `transit_dwell_forecasts`.
2. **Dwell Time Prediction Service (`backend/services/transit_dwell_service.py`):**
   - Implement `predict_dwell_time(stop_id: str, route_id: str, current_crowd: int, hour: int) -> DwellPrediction`.
   - Implement queue surge evaluator: trigger `CROWD_SURGE_ALERT` if $D_{\text{stop}} > 2.5$.
3. **TSP Coupling (`simulation/tsp_controller.py`):**
   - Update TSP TraCI logic to query `predict_dwell_time()` before extending green durations.
4. **API Endpoints (`backend/api/v1/endpoints/transit.py`):**
   - `GET /api/v1/transit/stops` (list corridor transit stops with crowd density).
   - `GET /api/v1/transit/stops/{id}/dwell-forecast`.
5. **Hermetic Test Suite (`tests/test_transit_dwell.py`):**
   - Test linear dwell time scaling with passenger load.
   - Verify surge threshold boundary condition.

---

## 5. Verification & Acceptance Criteria

- [ ] Dwell time accounts for door dead time and per-passenger boarding rates.
- [ ] Platform crowd surge alerts fire when density exceeds $2.5\text{ pax/m}^2$.
- [ ] Hermetic tests pass cleanly: `pytest tests/test_transit_dwell.py`.
