# Technical Architecture Specification
## Digital Twin-Enabled Smart City Analytics Platform

> **Document Status:** Authoritative Engineering Architecture Blueprint  
> **Pilot Corridor:** Viman Nagar Chowk ↔ Somnath Nagar Chowk (1.8 km arterial, Nagar Road, Pune, Maharashtra)  
> **Deployment Model:** Docker Compose modular monolith with resilient local multi-storage engine

---

## 1. Approved Technical Stack

| Layer | Component | Approved Technology | Role & Responsibility |
|---|---|---|---|
| **Frontend** | Application Shell | React 18 + TypeScript + Vite | Civic operations dashboard |
| **Geospatial UI** | Vector Map Canvas | MapLibre GL JS + OpenStreetMap | Interactive vector basemap, road segments, intersection markers |
| **Backend Core** | Modular Monolith | Python 3.11 + FastAPI + Uvicorn | Async REST APIs (`/api/v1`), WebSockets, background consumers |
| **Transport** | Message Broker | Eclipse Mosquitto (MQTT 3.1.1/5.0) | High-throughput sensor telemetry transport (`nagartwin/#`, `dt/v1/corridor/#`) |
| **Persistence** | Multi-Storage DB | PostgreSQL 16 + TimescaleDB + PostGIS | Canonical entity store, spatial queries, hypertable time-series |
| **Local Resilient**| Local Storage Fallback | SQLite 3 (WAL mode) + aiosqlite | Zero-dependency local persistence with automatic failover |
| **Traffic Simulation**| Micro-simulation | Eclipse SUMO 1.20+ via libsumo/TraCI | Baseline (`SCEN-BASE-01`) vs intervention (`SCEN-INT-01`) simulation |
| **Machine Learning**| Tabular Forecaster | XGBoost Regressors (joblib artifacts) | 15-min traffic speed & 60-min building power forecasts |
| **Uncertainty & XAI**| Calibration / SHAP | Conformal Prediction & TreeSHAP | 80%/90% confidence bands and local feature attributions |
| **Decision Support**| Advisory Engine | Deterministic Python Rule Engine | Transparent rules with mandatory human authorization |

---

## 2. Non-Negotiable Architecture Invariants

1. **System of Record:** PostgreSQL/TimescaleDB (or resilient SQLite fallback) is authoritative. MQTT is message transport only.
2. **State Separation Invariant:** Observed (`LIVE`/`REPLAY`), `SIMULATION`, and `PREDICTED` records are strictly separated into distinct tables. Predictions and simulations never overwrite observed twin current state.
3. **Strict Non-Actuation:** The platform is read-only decision support. Recommendations are advisory and require human authorization outside the platform before any physical signal or infrastructure change.
4. **Mandatory Provenance:** Every dynamic value returned by APIs or WebSockets includes `sourceMode`, `observedAt`/`generatedAt`, unit, and quality status (`VALID`, `STALE`, `DEGRADED`, `INVALID`).

---

## 3. Storage Architecture

```text
               +----------------------------------------------------+
               |                STUDY_AREAS (Spatial)               |
               +----------------------------------------------------+
                         |                           |
            +------------+------------+              +----------------------+
            |                         |                                     |
+---------------------+     +--------------------+                +-------------------+
|    INTERSECTIONS    |     |   ROAD_SEGMENTS    |                |  BUILDING_ZONES   |
+---------------------+     +--------------------+                +-------------------+
                                      |                                     |
                            +--------------------+                          |
                            |      SENSORS       |                          |
                            +--------------------+                          |
                                      |                                     |
            +-------------------------+-------------------------------------+
            |                                  |                            |
+-----------------------+          +-----------------------+    +-----------------------+
|  TRAFFIC_OBSERVATIONS |          |  ENERGY_OBSERVATIONS  |    |  ENVIRONMENT_OBSERVS  |
|     (Hypertable)      |          |     (Hypertable)      |    |      (Timeseries)     |
+-----------------------+          +-----------------------+    +-----------------------+
            |
+---------------------------------------------------------------------------------------+
| ENTITY_CURRENT_STATE (Authoritative Live/Replay State) | QUARANTINE_OBSERVATIONS (DLQ) |
+---------------------------------------------------------------------------------------+
```

### Table Inventory
1. `study_areas`: Corridor polygon geometry (PostGIS / GeoJSON).
2. `intersections`: Signalized junction coordinates, cycle times, phase configurations.
3. `road_segments`: Directed road geometries, lane counts, speed limits, capacities.
4. `sensors`: Traffic sensor metadata, sampling rates, freshness thresholds.
5. `building_zones`: Commercial facility profiles, gross floor areas, power limits.
6. `entity_current_state`: Latest authoritative metrics with timestamp conflict guards.
7. `traffic_observations`: Time-series speed, flow, occupancy, queue length hypertable.
8. `energy_observations`: Commercial active/reactive power, power factor, energy hypertable.
9. `environment_observations`: Ambient AQI, PM2.5, PM10, temperature, humidity.
10. `model_versions`: Registry of trained ML artifacts, horizons, metrics, demo status.
11. `forecasts`: 15m/60m ahead predictions with confidence bounds and feature citations.
12. `scenario_templates`: Pre-approved simulation scenario parameter schemas.
13. `scenario_runs`: Simulation executions, random seeds, run status, artifact paths.
14. `scenario_kpis`: Comparative delay, travel time, queue, and throughput metrics.
15. `recommendations`: Advisory action proposals with evidence and review audit trails.
16. `ingestion_errors`: Ingestion validation failure logs.
17. `audit_events`: System configuration and administrative action logs.
18. `quarantine_observations`: Dead-letter queue capturing rejected payloads with reasons.
19. `traffic_15m_aggregates`: Continuous 15-minute analytical rollups (p85 speed, max queue).
20. `spatial_road_segment_map`: PostGIS <-> SUMO edge mappings with per-lane widths and offsets.
21. `spatial_intersection_map`: Junction coordinates, cycle times, approach edges, and TLS IDs.
22. `spatial_signal_controller_map`: Controller parameters and signal group mappings.
23. `spatial_building_zone_map`: Building footprint, extrusion heights (28m), levels, and categories.
24. `spatial_sensor_map`: Sensor mounting coordinates, elevation, and sampling intervals.
25. `spatial_scenario_geometry_map`: Scenario templates mapped to corridor edges and junctions.

---

## 4. Ingestion & Event Transport

### 4.1 Topic Hierarchy
- **Canonical:** `nagartwin/{environment}/{sourceMode}/{domain}/{entityId}`
- **Corridor Wildcard:** `dt/v1/corridor/#`

### 4.2 Ingestion Validation Pipeline
Incoming payloads must pass Pydantic schema validation, coordinate sanity, physical range checks (speed 0–120 km/h, occupancy 0–100%), and timestamp sanity (future timestamps rejected). Invalid events are redirected to `quarantine_observations`.

---

## 5. Canonical REST & WebSocket Contracts

### 5.1 REST Endpoints (`/api/v1`)
- `GET /health`: System health and multi-storage connectivity status.
- `GET /api/v1/roads`: List corridor road segments with geometries and capacities.
- `GET /api/v1/roads/{id}`: Detailed segment data, current state, and 15m forecast.
- `GET /api/v1/intersections`: List signalized junctions and phase schemes.
- `GET /api/v1/entities/{id}`: Generic NGSI-LD-aligned entity resolver.
- `GET /api/v1/observations`: Query hypertable observations by domain, entity, time.
- `GET /api/v1/forecasts`: Retrieve current corridor predictions across traffic & energy.
- `GET /api/v1/scenarios`: List approved simulation scenario templates.
- `POST /api/v1/scenario-runs`: Execute comparative SUMO simulation run.
- `GET /api/v1/scenario-runs/{id}`: Query run status, baseline vs intervention KPIs.
- `GET /api/v1/models`: List active ML model cards, metrics, and baseline comparisons.
- `GET /api/v1/data-quality`: Ingestion health, schema compliance rates, quarantine summary.
- `GET /api/v1/spatial/registry`: Full PostGIS <-> SUMO spatial mapping registry.
- `GET /api/v1/spatial/corridor-3d`: GeoJSON FeatureCollection with 3D extrusions and lane centerlines.
- `GET /api/v1/spatial/layers/{layer_name}`: Filtered spatial layers (`roads`, `buildings`, `signals`, etc.).
- `GET /api/v1/spatial/resolve/{entity_id}`: Resolves NGSI-LD ID to spatial and simulation attributes.

### 5.2 Canonical WebSocket Channels
- `/ws/operations`: Real-time operational twin feed (traffic, energy, environment state).
- `/ws/system`: Broker, streamer, and database health event stream.
- `/ws/scenarios/{runId}`: Progress and KPI stream for active simulation executions.

---

## 6. Deployment Topology

```text
Docker Compose Profiles:
- Default: postgres (TimescaleDB) + mosquitto + backend (FastAPI) + frontend (Nginx/Vite)
- --profile full: adds minio (artifact storage) + mlflow (experiment tracking)
```
