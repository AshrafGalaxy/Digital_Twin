# System Architecture Diagram
## Digital Twin-Enabled Smart City Analytics Platform

> **Document Status:** Reference Architecture Diagram (Deliverable `D-12`)  
> **Pilot Corridor:** Viman Nagar Chowk $\leftrightarrow$ Somnath Nagar Chowk, Nagar Road, Pune  
> **Core Invariant:** Strictly advisory decision support. No automated public infrastructure actuation.

---

```mermaid
flowchart TB
    subgraph SENSORS["Corridor Physical & Telemetry Sources"]
        direction TB
        S1["Optical Traffic Sensors<br/>(DS-VN-EB-01 .. DS-SN-WB-02)"]
        S2["Commercial Building Power Meter<br/>(BLD-PHOENIX-01)"]
        S3["AQI & Environmental Monitor<br/>(Viman Nagar Station)"]
    end

    subgraph TRANSPORT["Event Transport Layer"]
        MQTT["Eclipse Mosquitto 2.0 MQTT Broker<br/>(TCP :1883 / WS :9001)"]
    end

    subgraph BACKEND["FastAPI Modular Monolith (Python 3.11)"]
        direction TB
        
        subgraph INGESTION["Ingestion & Validation Engine"]
            VAL["IngestionValidator<br/>• Schema Range Bounds<br/>• Staleness Check (&lt;60s)<br/>• Future Timestamp Rejection"]
            CANON["Canonical NGSI-LD Transformer<br/>• TrafficObservationEvent<br/>• EnergyObservationEvent"]
        end

        subgraph STATE_PERSISTENCE["State & Persistence Tier"]
            PG[("PostgreSQL 16 + PostGIS + TimescaleDB<br/>• entity_current_state<br/>• observation_history<br/>• scenario_runs")]
            MEM[("In-Memory State Store<br/>(Graceful Fallback Cache)")]
        end

        subgraph ANALYTICS_SIM["Predictive & Simulation Engines"]
            direction LR
            SUMO["Eclipse SUMO 1.20 + TraCI<br/>(Kinematic Car-Following Fallback)"]
            ML_TRAFFIC["XGBoost Traffic Forecaster<br/>(15-min speed lead; p10/p90 intervals)"]
            ML_ENERGY["XGBoost Energy Forecaster<br/>(60-min active power lead)"]
        end

        subgraph GOVERNANCE["Governance & Advisory Decision Engine"]
            RULE["Deterministic Rule Engine<br/>• RULE-TRF-CONGESTION-PREDICTED<br/>• RULE-NRG-PEAK-SURGE<br/>• RULE-ENV-STALE-TELEMETRY"]
            AUDIT[("Advisory Review Audit Trail<br/>(Status: ACTIVE ➔ REVIEW ➔ ACKNOWLEDGED)")]
        end

        subgraph API_TIER["REST & WebSocket API Tier (:8000)"]
            API_HEALTH["/api/v1/health"]
            API_ASSETS["/api/v1/assets/*"]
            API_STATE["/api/v1/state/*"]
            API_STREAM["/api/v1/stream (WS)"]
            API_SCENARIO["/api/v1/scenarios/*"]
            API_FORECAST["/api/v1/forecasts/*"]
            API_RECS["/api/v1/recommendations/*"]
        end
    end

    subgraph FRONTEND["Operations Dashboard (React 18 + Vite :5173 / Nginx :80)"]
        direction TB
        MAP["MapLibre GL JS 2D Operations View<br/>(Nagar Road Corridor Centerline & Assets)"]
        DRAWER["Entity Detail Drawer<br/>(Current Telemetry & ForecastPanel)"]
        STUDIO["Scenario Studio Modal<br/>(Side-by-Side Baseline vs Intervention KPIs)"]
        ADVISORY_CTR["Advisory Decision Support Center<br/>(Traceable Evidence & Review Workflow)"]
    end

    %% Flow Connections
    S1 & S2 & S3 -->|Raw Telemetry Payloads| MQTT
    MQTT -->|MQTT Consumer| VAL
    VAL -->|Validated Events| CANON
    CANON -->|Current State Projection| PG & MEM
    PG & MEM -.->|State Snapshots| API_STATE
    PG & MEM -->|Live Event Push| API_STREAM

    CANON -.->|Historical Series| ML_TRAFFIC & ML_ENERGY
    ML_TRAFFIC & ML_ENERGY -->|Predictions| API_FORECAST & RULE
    SUMO -->|Comparative KPIs| API_SCENARIO & RULE
    RULE -->|Traceable Advisories| AUDIT
    AUDIT -->|Advisory Lifecycle| API_RECS

    API_STREAM ==>|Real-Time WebSocket Updates| MAP
    API_STATE & API_ASSETS -->|Corridor Topology| MAP
    API_FORECAST -->|Inference Bounds & Baselines| DRAWER
    API_SCENARIO -->|KPI Comparisons| STUDIO
    API_RECS -->|Human Governance Actions| ADVISORY_CTR
```

---

## Key Subsystems Description

1. **Ingestion & Validation Engine:** Validates incoming physical telemetry against physical sanity boundaries (e.g. speed $0 \dots 120\text{ km/h}$), rejects future timestamps, and detects sensor staleness ($> 60\text{s}$).
2. **State & Persistence Tier:** Primary system of record in PostgreSQL/TimescaleDB with transparent in-memory fallback during local development.
3. **Predictive & Simulation Engines:**
   - **XGBoost Regressors:** 15-minute speed forecast (+31.6% MAE improvement over persistence) and 60-minute energy demand forecast (+77.8% MAE improvement over persistence) running locally on CPU in $< 5\text{ ms}$.
   - **Eclipse SUMO / Kinematic Runner:** Microscopic simulation engine evaluating dynamic signal timing interventions with deterministic seed control.
4. **Governance Rule Engine:** Deterministic, transparent rule evaluation linking evidence directly to operational recommendations with mandatory human review workflows.
5. **Presentation Layer:** MapLibre GL 2D spatial twin, dynamic entity drawers, simulation studio, and advisory center.
