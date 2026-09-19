# Operational Runbook: Digital Twin Smart City Analytics Platform
## Viman Nagar ↔ Somnath Nagar Corridor Pilot (Pune)

> **Document Status:** Operational Runbook (Deliverable `D-11`)  
> **Applies to:** Platform Operators, Reviewers, Demonstrators, and System Evaluators  
> **Core Policy:** Non-actuating advisory twin. Human verification required prior to any physical intervention.

---

## 1. System Architecture & Port Allocation

The platform runs as a modular monolith backend, an interactive React/MapLibre frontend, and supporting persistence and transport services:

| Component | Technology | Default Port | Internal Port | Purpose |
|---|---|---|---|---|
| **Frontend** | React 18 + Vite / Nginx | `5173` (dev) / `80` (prod) | `80` | MapLibre 2D twin, Scenario Studio, Advisory Center |
| **Backend API** | FastAPI + Uvicorn | `8000` | `8000` | Canonical schema validation, REST APIs, WebSockets |
| **MQTT Broker** | Eclipse Mosquitto 2.0 | `1883` (TCP) / `9001` (WS) | `1883` / `9001` | High-frequency telemetry transport |
| **Database** | PostgreSQL 16 + TimescaleDB + PostGIS | `5432` | `5432` | Authoritative twin state & spatiotemporal storage |

---

## 2. Quickstart Execution Methods

### Method A: Single-Command Local Dev (Recommended for Windows Laptop)
The root directory includes automated launchers with environment preflight checks and interactive terminal spawning:

- **Command Prompt (CMD):**
  ```cmd
  start_dev.bat
  ```
- **PowerShell:**
  ```powershell
  .\start_dev.ps1
  ```

Both launchers verify Python `.venv`, Node `node_modules`, validate the database/models, and open two distinct sub-processes for backend (`http://localhost:8000`) and frontend (`http://localhost:5173`). Pressing `Ctrl+C` cleanly shuts down all processes.

---

### Method B: Full-Stack Container Deployment (Docker Compose)
To launch the entire platform in isolated containers on any VM or laptop:

```bash
# 1. Build and launch all services in detached mode
docker compose up --build -d

# 2. Inspect container status
docker compose ps

# 3. View live backend logs
docker compose logs -f backend

# 4. Stop platform services
docker compose down
```

Services will be accessible at:
- **Dashboard UI:** `http://localhost:5173`
- **Backend API & Swagger Docs:** `http://localhost:8000/docs`
- **Subsystem Health Diagnostics:** `http://localhost:8000/api/v1/health`

---

## 3. Platform Health & Diagnostics Verification

### Subsystem Health Endpoint
Query `GET /api/v1/health` to confirm platform readiness:

```bash
curl -s http://localhost:8000/api/v1/health | jq
```

**Expected JSON Response:**
```json
{
  "status": "HEALTHY",
  "environment": "development",
  "version": "1.0.0",
  "subsystems": {
    "database": true,
    "mlTrafficModel": true,
    "mlEnergyModel": true,
    "simulationEngine": true,
    "scenarioTemplatesCount": 3,
    "activeAdvisoriesCount": 3
  },
  "governanceMode": "HUMAN_ADVISORY"
}
```

---

## 4. Degraded-State Resiliency & Recovery Procedures

The platform is designed with graceful degradation so that partial infrastructure failures never cause silent UI crashes:

### 4.1 PostgreSQL Offline / Connection Refused
- **Behavior:** The backend automatically falls back to an in-memory thread-safe state store (`_MEMORY_STATE_STORE`).
- **Indicator:** `/api/v1/health` marks `"database": false` and status becomes `"DEGRADED"`. UI displays live replayed state from memory.
- **Recovery:** Start or restart PostgreSQL via `docker compose up -d postgres`. The backend reconnects on the next transaction cycle.

### 4.2 Eclipse Mosquitto MQTT Broker Offline
- **Behavior:** Backend switches from MQTT subscriber mode to synthetic corridor clock generator.
- **Indicator:** Dashboard updates every 2 seconds; source mode pill shows `REPLAY` or `SIMULATION`.
- **Recovery:** Run `docker compose restart mosquitto`.

### 4.3 Eclipse SUMO Binaries Missing on Host
- **Behavior:** The simulation engine automatically switches from `TraCI` to the calibrated **Kinematic Queue & Car-Following Runner**.
- **Evidence:** Scenario runs still output deterministic arterial travel times, delays, queues, and comparative deltas under seed `42`.
- **Verification:** Run `pytest tests/test_simulation.py -v`.

### 4.4 Missing Forecast Model Artifacts
- **Behavior:** `CorridorForecaster` falls back to historical moving-average and heuristic persistence baselines.
- **Recovery:** Re-run local training:
  ```powershell
  .venv\Scripts\python ml/training/train_traffic_model.py
  .venv\Scripts\python ml/training/train_energy_model.py
  ```

---

## 5. Step-by-Step Stakeholder & Academic Demonstration Script

Follow this 5-minute script during live reviews or recorded video walkthroughs:

1. **Corridor Exploration & 2D Twin:**
   - Open `http://localhost:5173`.
   - Observe the MapLibre 2D view of Nagar Road from Viman Nagar Chowk (`VN-01`) to Somnath Nagar Chowk (`SN-01`).
   - Click on Road Segment `SEG-NR-EB-01` to open the `EntityDetailDrawer`.
   - Observe the real-time speed, volume, and congestion index. Note the explicit provenance tag: `REPLAY` or `SIMULATION`.
2. **Near-Term Predictive Intelligence (Phase 5):**
   - In the drawer, inspect the **15-Minute Forecast Panel**.
   - Review predicted speed ($22.4\text{ km/h}$), the 80% prediction interval ($p_{10}$ to $p_{90}$), and the baseline comparison (+31.6% improvement over persistence).
   - Point out the mandatory data locality caveat: *"Validates corridor ML pipeline; not calibrated to field loops."*
   - Select Phoenix Marketcity (`BLD-PHOENIX-01`) and inspect the **60-Minute Building Energy Forecast**.
3. **What-If Simulation in Scenario Studio (Phase 4):**
   - Click **Scenario Studio** in the top navigation bar.
   - Select `SCEN-INT-01 (Dynamic Green Split Re-allocation)`.
   - Click **Run Simulation Scenario**.
   - Review the side-by-side KPI comparison table: note the simulated $-19.5\%$ vehicle delay reduction and $+13.6\%$ throughput increase.
   - Note the prominent `SIMULATION` tag and non-actuation disclaimer.
4. **Advisory Decision Support & Governance Workflow (Phase 6):**
   - Click the **Advisories** button in the header (displaying badge `[Advisories 3]`).
   - Read the prominent **Governance Mandate Banner**: *"All recommendations are strictly advisory. No automated actuation."*
   - Drill into `REC-TRF-20260920-001` (Arterial Congestion Surge Predicted on Nagar Road Eastbound).
   - Inspect the **Traceable Evidence** box (showing model version `traffic-xgb-v1`, horizon +15m, predicted value vs threshold).
   - Click **Review / Update Status**, enter reviewer name `"Traffic Cell Officer"`, select status `ACKNOWLEDGED`, enter operational notes, and submit.
   - Click **Audit Trail** to demonstrate that the lifecycle change is permanently recorded with timestamp and reviewer identity.

---

## 6. Safety, Privacy & Governance Verification Checklist

Before publishing or demonstrating the platform, verify compliance with `AGENTS.md`:

- [x] **Zero Physical Actuation:** No endpoint or rule sends signals to city signal controllers or building BMS systems.
- [x] **Strict Provenance Tagging:** Every dynamic value displays `LIVE`, `REPLAY`, `SIMULATION`, or `PREDICTED`.
- [x] **State Separation Invariant:** Forecasts and scenario simulation outputs are completely isolated and never overwrite authoritative observed state.
- [x] **No Personal Identifiable Information (PII):** No camera feeds, license plates, MAC addresses, or individual GPS traces are ingested.
- [x] **Transparent Limitations:** Data locality caveats and benchmark source disclaimers are visible in the UI and documented in model cards.
