# Master Demo Handbook - Volume 1: System Architecture and Data Flow

## 1. What is a Digital Twin in Plain Language?

Imagine you have a busy arterial street in a modern city with cars driving, traffic lights changing, commercial shopping malls consuming electricity, and air quality sensors measuring dust in the air. 

A **Digital Twin** is a dynamic, software-based mirror of that real physical corridor running inside a computer. 

However, a digital twin is **not** just a 3D video game or a static map. What makes it a true digital twin are three interconnected layers:
1. **Live Connectivity:** It receives real-time operational measurements (speeds, traffic volumes, electricity demand, air pollution levels) from field sensors and telemetry pipelines.
2. **Physics and AI Intelligence:** It does not simply display the present moment. It runs machine learning models and microscopic traffic physics to forecast what will happen 15, 30, and 60 minutes into the future.
3. **What-If Simulation Sandbox:** It allows city engineers and operators to test interventions safely in software (such as changing a signal timing or shedding building power) before ever touching physical street equipment.

---

## 2. High-Level Architectural Anatomy

The platform is designed as a **Modular Monolith** using modern, production-grade open-source technologies. It consists of four primary structural tiers:

```
[ Physical Assets & IoT Sensors ]
  - Road Segments, Induction Loops, Radars
  - Substation Transformers, Smart Power Meters
  - Continuous Ambient Air Quality Stations (CAAQMS)
            |
            v  (MQTT Protocol / JSON Telemetry)
[ Backend Ingestion & Persistence Engine ]
  - FastAPI Modular Monolith (Python 3.11)
  - Telemetry Streamer & Data Sanitizer
  - Dual-Engine Database: TimescaleDB / PostgreSQL (with resilient SQLite fallback)
            |
            v  (REST APIs & Real-Time WebSockets)
[ Analytical Brain & AI Pipelines ]
  - XGBoost Multi-Horizon Forecasting Engine
  - Conformal Prediction (Distribution-Free Uncertainty)
  - TreeSHAP Explainable AI Attributions
  - Indo-HCM Level of Service (LOS) Engine
  - SUMO Microscopic Physics Simulation (with Kinematic Fallback)
  - Deterministic Governance Rule Engine
            |
            v  (Push via WebSockets every 1.0 - 2.4s)
[ Frontend Operations Console ]
  - React 18 + TypeScript + Vite
  - 3D Digital Twin Viewer: CesiumJS (Photogrammetry, 3D extruded buildings, animated traffic)
  - 2D Operational GIS: Leaflet / Mapbox
  - Accessible Analytics: Recharts & Tailwind CSS
```

---

## 3. End-to-End Data Pipeline: From Sensor to Screen

To explain this to judges, walk through the journey of a single packet of traffic or energy data from the street to the browser.

### Step 1: Data Generation at the Field Asset
- **Traffic Telemetry:** Induction loops or radar sensors on corridor segments record vehicle counts and vehicle speeds over 60-second polling intervals.
- **Energy Telemetry:** Digital power meters at commercial facilities and distribution substations sample 3-phase voltages and currents every 15 minutes.
- **Air Quality Telemetry:** Regional CAAQMS stations measure particulate matter (PM2.5, PM10) and nitrogen dioxide (NO2).
- **In our reference pilot:** Telemetry is streamed by an autonomous background worker (`telemetry_streamer.py`) that executes calibrated physical equations based on empirical ground-truth surveys.

### Step 2: Transport via MQTT Protocol
- Telemetry packets are formatted using the open smart city NGSI-LD / FIWARE standard and published to lightweight MQTT topics such as:
  `corridor/traffic/SEG-NR-EB-01/telemetry`
  `corridor/energy/BLD-PHOENIX-01/power`
- MQTT allows thousands of sensor nodes to transmit tiny payloads without overwhelming the server.

### Step 3: Ingestion, Validation, and Data Sanitization
- The backend MQTT Consumer receives the payload and immediately runs it through strict validation guards in `backend/schemas/`:
  - **Sanity Bounds:** Speed must be between 0 and 120 km/h. Power must be non-negative.
  - **Timestamp Integrity:** The timestamp must not be from the future.
  - **Quarantine Handling:** If a sensor transmits corrupted, impossible, or schema-violating data, it is not dropped silently. It is routed to the **Data Quarantine Queue** (`quarantine_observations` table) for forensic review.

### Step 4: Storage in the Dual-Engine Database
- The sanitized record is stored in our relational database.
- **Why Dual-Engine?** 
  - In full cloud or municipal server deployments, the platform connects to **PostgreSQL with TimescaleDB hypertables**, which partitions time-series records by timestamp for blazing-fast analytical queries.
  - If PostgreSQL is offline or if running on a standalone laptop for a field demonstration, the platform automatically and transparently falls back to a **Resilient Local SQLite Engine** (`digital_twin.db`). Zero configuration needed; zero downtime.

### Step 5: The Analytical and AI Processing Brain
- Once data is saved, backend background workers calculate key derived metrics:
  - The **LOS Engine** computes Level of Service grades (LOS A through F) using the Indian Highway Capacity Manual (IRC:106) standard.
  - The **Power Balance Service** calculates 3-phase AC active power, reactive power, and feeder thermal loading.
  - The **Forecast Service** feeds recent 15-minute lags into our XGBoost model to predict traffic velocity and building power demand for the next 15, 30, and 60 minutes.
  - The **Rule Engine** evaluates safety and operational thresholds (e.g. speed dropping below 20 km/h or feeder load exceeding 85%).

### Step 6: Real-Time WebSocket Broadcast
- Instead of the browser repeatedly asking the server for updates (polling), the backend uses a persistent **WebSocket connection** (`/ws/operations` and `/api/v1/ws/state`).
- Whenever a new observation or aggregate is calculated, the server immediately pushes a compact JSON event to all connected clients.
- If a momentary network lag occurs, the frontend maintains a 2.4-second organic heartbeat so the user interface never freezes or stutters.

### Step 7: Frontend Rendering on the Operations Map
- The React application receives the WebSocket message and updates the state.
- In **2D Mode**, road segments instantly update their color (Green for fast, Amber for moderate, Red for congested).
- In **3D Cesium Mode**, virtual 3D vehicles moving along the corridor smoothly accelerate or decelerate to match the actual calculated speed of that segment.
- The **Corridor Telemetry HUD** at the top updates its numbers: Average Speed, Congestion Percentage, Commercial Power Demand, and Active Sensors count.

---

## 4. The Three Golden Architectural Invariants

If the judges ask what rules govern the system engineering of this project, present these three non-negotiable invariants:

### Invariant 1: Strict State Separation
- In many poorly designed systems, simulated numbers or predictive machine learning outputs overwrite historical sensor readings.
- In our platform, **Ground Truth Observed Data**, **SUMO Simulation Data**, and **Machine Learning Forecasts** live in completely separate tables.
- A prediction is tagged `PREDICTED` and never called a measurement.
- A simulation output is tagged `SIMULATION` and never claimed to be observed ground truth.

### Invariant 2: Strict Non-Actuation (Human-in-the-Loop Decision Support)
- This platform is strictly a **decision-support advisory system**, not an automated physical actuator.
- It will **never** directly change a physical traffic light signal on the street or trip a physical circuit breaker at an electrical substation.
- Why? In municipal engineering, autonomous actuation of safety-critical infrastructure introduces severe public liability and safety risks.
- Instead, the platform generates **Actionable Advisory Dossiers**. A certified municipal operator or traffic engineer must inspect the recommendation, review the predicted impact, and formally authorize the plan before any field action is taken.

### Invariant 3: Mandatory Provenance on Every Dynamic Value
- Every single metric shown on any screen carries four mandatory provenance metadata tags:
  1. `sourceMode`: One of `LIVE`, `REPLAY`, `SIMULATION`, `PREDICTED`, or `STALE`.
  2. `observedAt` / `generatedAt`: Exact ISO-8601 UTC timestamp.
  3. `unit`: The engineering unit (km/h, kW, veh/h, dBA, microgram/m3).
  4. `qualityStatus`: `VALID`, `SUSPECT`, or `CALIBRATED`.

---

## 5. Security and Role-Based Access Control (RBAC)

Municipal city operations involve multiple agencies who should only see what is relevant to their job. The platform enforces cryptographic JWT role-based access:

| Role Name | Primary Responsibilities | Allowed Navigation Tabs |
| :--- | :--- | :--- |
| **Traffic Systems Engineer** | Signal timing, corridor mobility, queue clearance, simulation | Operations Map, Traffic Analytics, Scenario Studio, Recommendations |
| **Energy Grid Manager** | Substation loading, commercial building demand response, BESS | Operations Map, Energy Analytics, Environment Context, Recommendations |
| **Executive Auditor** | Regulatory compliance, carbon emissions, model accuracy, budget | Recommendations, Pilot Evaluation, System Health |
| **Municipal Analyst** | Cross-domain unified operations, macro analytics, system health | Full Access across all 11 tabs and administration modals |

Sessions are stored with cryptographic JSON Web Tokens (JWT) in local storage, with automatic token expiration checks and single-use magic access link redemption.

