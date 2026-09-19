# Technical Architecture
## NagarRoad Twin — Digital Twin-Enabled Smart City Analytics

> **Document status:** Baseline implementation architecture  
> **Companion documents:** `PROJECT_CONTEXT.md`, `PRD.md`  
> **Study area:** Viman Nagar Chowk (Phoenix Mall) ↔ Somnath Nagar Chowk, Nagar Road, Pune  
> **Architecture style:** Modular monolith with event-driven ingestion  
> **Primary principle:** Build one correct, reproducible corridor twin before adding production-scale infrastructure.

---

## 1. Purpose

This document defines the technical architecture required to implement NagarRoad Twin. It is the binding technical reference for agents and developers working on frontend, backend, GIS, ingestion, simulation, machine learning, data storage, testing, and deployment.

It defines:

- System boundaries and non-goals.
- Component responsibilities.
- Data/control flow.
- Canonical data model principles.
- Service/module boundaries.
- Database and storage approach.
- MQTT and API contracts.
- Simulation and ML integration.
- Deployment topology.
- Security, observability, quality, and migration rules.

Detailed table definitions, JSON schemas, UI screens, ML feature sets, and deployment commands may be expanded in later documents. This file defines the architecture that those details must follow.

---

## 2. Architecture goals

1. Support a real digital-twin lifecycle: **observe → validate → synchronize → predict → simulate → recommend → visualize**.
2. Use the same downstream pipeline for **simulation**, **replay**, and optional **live** sources.
3. Keep observed, predicted, and scenario-simulated state separate.
4. Be reproducible on a developer laptop or one small VM.
5. Be explainable and suitable for academic evaluation.
6. Avoid infrastructure that does not provide measurable MVP value.
7. Preserve a migration path toward context brokers, larger stream processing, advanced models, and optional 3D visualization.

---

## 3. Architecture decisions

### 3.1 Selected MVP architecture

```text
React + TypeScript + Vite + MapLibre
                │
                │ REST + WebSocket
                ▼
        FastAPI modular monolith
                │
      ┌─────────┼─────────┬──────────────┐
      │         │         │              │
      ▼         ▼         ▼              ▼
 Ingestion   Twin Core  ML/Rules     Scenario Service
 Validation  State API  Inference    SUMO + TraCI
      │         │         │              │
      └─────────┴─────────┴──────────────┘
                │
                ▼
 PostgreSQL + TimescaleDB + PostGIS
                │
      ┌─────────┼──────────┐n      ▼         ▼          ▼
  MinIO/local  MLflow     MQTT Mosquitto
  artifacts    experiments  event transport
```

> Note: In the rendered implementation diagram, replace the accidental textual `\n` marker after `┬──────────┐` with normal whitespace. The intended branches are **MinIO/local artifacts**, **MLflow experiments**, and **MQTT Mosquitto event transport**.

### 3.2 Why modular monolith

The MVP uses one FastAPI application divided into internal modules rather than independently deployed microservices.

Reasons:

- The study area has only 2 junctions, 8–15 road segments, and low event volume.
- A single team/student can debug one codebase more reliably.
- Shared schema, transaction boundaries, authentication, and logging are simpler.
- The project needs research evidence and functional completion more than distributed-systems complexity.
- Modules can later become services if load, ownership, or failure isolation requirements justify it.

### 3.3 Explicitly rejected/deferred architecture choices

| Choice | MVP decision | Reason |
|---|---|---|
| Kafka/Flink | Deferred | MQTT + FastAPI + Postgres is adequate at MVP event volume |
| FIWARE Orion-LD | Deferred | Adopt the entity semantics first; broker operational cost is not justified yet |
| Eclipse Ditto | Deferred | Useful future device/twin middleware; not required for current state model |
| Neo4j | Deferred | Relationships are shallow and queryable with relational keys/PostGIS |
| Kubernetes | Deferred | Docker Compose is enough for laptop/small-VM deployment |
| Full microservices | Deferred | Adds deployment/testing/observability complexity without MVP benefit |
| Deep/GNN/RL models | Deferred | Need stronger data scale and baselines first |
| 3D-first frontend | Deferred | Must not delay operational 2D workflows |
| Physical control integration | Prohibited in MVP | Safety, authorization, and real-infrastructure access are out of scope |

---

## 4. System boundary

### 4.1 Inside the system

- Viman Nagar–Somnath Nagar study-area asset model.
- OSM-derived road and junction geometry.
- Logical sensors and data-source adapters.
- Simulation, replay, and optional live input modes.
- MQTT ingestion and schema/range/timestamp validation.
- Current and historical twin state.
- Traffic/energy feature generation and inference.
- SUMO scenario execution through TraCI.
- Rule-based recommendations.
- REST and WebSocket APIs.
- React/MapLibre operator dashboard.
- Experiment, model, and scenario artifacts.

### 4.2 Outside the system

- Real Pune ATMS integration.
- Public signal control.
- CCTV/video ingestion.
- Individual-level mobility tracking.
- Full city model.
- Municipal production reliability/SLA.
- Hardware sensor procurement and field-device lifecycle management.
- 3D mesh generation or use of Google imagery as a data source.

---

## 5. Logical architecture

### 5.1 Layered view

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Presentation Layer                                                   │
│ React + TypeScript + Vite                                            │
│ MapLibre 2D operations dashboard · Charts · Alerts · Scenario UI     │
│ Optional: CesiumJS 3D visual presentation                            │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ REST / WebSocket
┌───────────────────────────────▼──────────────────────────────────────┐
│ Application Layer — FastAPI Modular Monolith                         │
│ Asset API · Twin State API · Ingestion API · Forecast API             │
│ Scenario API · Recommendation API · Auth/Health/Export APIs           │
└───────┬────────────────┬─────────────────┬───────────────────────────┘
        │                │                 │
┌───────▼───────┐ ┌──────▼────────┐ ┌──────▼────────────────────────┐
│ Data Ingestion │ │ Twin Core      │ │ Intelligence & Simulation     │
│ MQTT consumer  │ │ current state  │ │ features · XGBoost inference │
│ API poller     │ │ history        │ │ rules · SUMO/TraCI scenarios │
│ replay worker  │ │ provenance     │ │ SHAP / model metadata         │
│ validation     │ │ relationships  │ │                               │
└───────┬────────┘ └──────┬────────┘ └──────┬────────────────────────┘
        │                 │                  │
┌───────▼─────────────────▼──────────────────▼────────────────────────┐
│ Persistence Layer                                                     │
│ PostgreSQL + TimescaleDB + PostGIS                                   │
│ entity registry · current state · observations · forecasts · runs    │
└─────────────┬─────────────────────┬───────────────────────┬──────────┘
              │                     │                       │
       ┌──────▼──────┐       ┌──────▼──────┐        ┌──────▼───────┐
       │ MinIO/local │       │ MLflow       │        │ Mosquitto     │
       │ raw/artifacts│      │ runs/models  │        │ MQTT broker   │
       └─────────────┘       └─────────────┘        └──────────────┘

Sources: SUMO · historical files · weather/AQI APIs · optional permitted sensors
```

### 5.2 Core design rule

A source mode may differ only **before canonical transformation**. Once an event has been transformed to the canonical entity/observation contract, validation, storage, feature generation, inference, twin updates, recommendations, APIs, and UI must behave consistently.

---

## 6. Component catalog

| Component | Responsibility | Inputs | Outputs | MVP deployment |
|---|---|---|---|---|
| React dashboard | Operator/research UI | REST, WebSocket | User interactions, scenario requests | Container/static build |
| MapLibre map | 2D spatial visualization | GeoJSON/API state | Roads, assets, overlays | Browser library |
| FastAPI gateway | API routing, auth, validation, coordination | HTTP/WebSocket | JSON responses/events | Same backend container |
| MQTT consumer | Subscribes to canonical/raw source topics | MQTT messages | Validated ingestion jobs | Backend worker/module |
| API poller | Retrieves allowed weather/AQI/live API data | HTTP APIs | Canonical events | Scheduled backend job |
| Replay worker | Streams historical data as events | CSV/Parquet/JSON | MQTT events | Backend job/container |
| Simulation publisher | Publishes SUMO/synthetic observations | SUMO/Python generator | MQTT events | Simulation module |
| Validation module | Validates schema, ranges, timestamps, IDs | Raw/canonical events | Valid event or error record | FastAPI internal module |
| Twin core | Maintains current/historical/predicted/scenario state | Valid observations, forecasts, scenarios | Twin-state API data | FastAPI + DB |
| Feature module | Builds lag/window/time/weather features | Observations/context | Model-ready feature frames | Scheduled job/internal module |
| Inference module | Runs traffic and energy prediction | Feature vectors | Forecast + interval + metadata | FastAPI internal module |
| Rule engine | Produces advisory recommendations | Forecasts, thresholds, KPIs | Recommendation records | FastAPI internal module |
| SUMO scenario service | Executes baseline/intervention scenario | Scenario configuration | Scenario run/KPIs/artifacts | Worker/container |
| PostgreSQL | Relational transactional persistence | Queries/writes | State/history/configuration | Database container |
| TimescaleDB | Time-series hypertables/aggregates | Observations/forecasts | Time-window analytics | PostgreSQL extension |
| PostGIS | Geometry/geospatial query support | Spatial layers | GeoJSON/spatial joins | PostgreSQL extension |
| MinIO/local storage | Raw imports, model/scenario artifacts | Files | Artifact URIs | Optional container/local directory |
| MLflow | Tracks model experiments/runs | Params/metrics/artifacts | Run/model metadata | Optional container/local files |
| Mosquitto | Event broker | Publishers/subscribers | MQTT message routing | Container |

---

## 7. Data modes and adapters

### 7.1 Mode overview

| Mode | Source | Purpose | Required in MVP |
|---|---|---|---:|
| Simulation | SUMO traffic output; Python synthetic energy generator | Controlled scenarios, integration testing, demonstrations | Yes |
| Replay | Historical traffic/energy/weather files streamed at configurable speed | Reproducible demo/model evaluation | Yes |
| Live | Permitted external APIs or sensor device feed | Optional realistic operation | No |
| Predicted | ML model output based on observations/features | Forecast visualization and decision support | Yes |

### 7.2 Adapter contract

Every source adapter must produce or be transformable into this internal envelope before persistence:

```json
{
  "eventId": "uuid-or-deterministic-id",
  "entityId": "urn:ngsi-ld:TrafficFlowObserved:segment-001",
  "entityType": "TrafficFlowObserved",
  "observedAt": "2026-09-19T12:00:00Z",
  "receivedAt": "2026-09-19T12:00:02Z",
  "sourceMode": "simulation",
  "sourceId": "sumo:baseline-run-001",
  "payload": {
    "averageVehicleSpeed": 24.8,
    "vehicleCount": 54,
    "congestionIndex": 0.46
  },
  "units": {
    "averageVehicleSpeed": "km/h",
    "vehicleCount": "vehicles",
    "congestionIndex": "ratio"
  },
  "quality": {
    "score": 1.0,
    "status": "valid"
  },
  "geometryRef": "road-segment-001"
}
```

### 7.3 Adapter rules

- Adapters may add source-specific metadata but must not bypass validation.
- `sourceMode` is immutable once an event is created.
- A replayed observation retains the historical `observedAt` and gets a new `receivedAt`.
- Scenario/simulation observations must contain a scenario run reference where applicable.
- Missing input values must be represented explicitly (`null`, missing flag, or quality status), not silently substituted.

---

## 8. End-to-end data flow

### 8.1 Ingestion flow

```text
1. Source adapter/generator creates raw event
2. Publisher sends event to MQTT topic OR poller passes event internally
3. Ingestion consumer receives event
4. Validation module checks schema, identity, timestamp, units, ranges, and duplicates
5. Canonical transformer maps event to NGSI-LD-inspired contract
6. Raw/invalid metadata is retained according to retention policy
7. Valid observation is inserted into historical observations hypertable
8. Current-state record is upserted only if event is newer/valid
9. State update is emitted to WebSocket subscribers
10. Feature/inference scheduler includes the observation in next forecast cycle
```

### 8.2 Forecast flow

```text
1. Scheduled job selects eligible entity/time window
2. Feature module queries observations + static road/building features + weather context
3. Feature validation checks completeness/freshness
4. Inference module loads approved model version
5. Model produces forecast and optional prediction interval
6. Explanation metadata is generated/stored where practical
7. Forecast is stored separately from observed state
8. Rule engine evaluates thresholds/conditions
9. Recommendation, if any, is stored with linked evidence
10. Forecast/recommendation update is published to dashboard clients
```

### 8.3 Scenario flow

```text
1. User selects predefined scenario in dashboard
2. Dashboard sends scenario request to Scenario API
3. API validates user input against allowed parameters
4. Scenario service creates immutable scenario_run record
5. Service runs baseline SUMO configuration
6. Service runs intervention SUMO configuration with comparable seed/demand
7. Service calculates KPIs and stores outputs/artifact URIs
8. Service marks run complete/failed
9. Dashboard receives scenario status/progress event
10. Dashboard renders baseline vs intervention comparison
11. Optional recommendation links to scenario run; no real-world actuation occurs
```

### 8.4 State separation rule

```text
Observed state      = event from simulation/replay/live source
Predicted state     = ML output derived from observations/features
Scenario state      = output from explicit SUMO baseline/intervention run
Recommendation      = advisory decision record derived from evidence
```

No category may overwrite another category.

---

## 9. Twin domain model

### 9.1 Core entities

| Entity | Description | Mutable state? |
|---|---|---:|
| StudyArea | Versioned corridor polygon/boundary | Rarely |
| RoadSegment | Directed road section within twin network | Static + operational state |
| Intersection | Junction/chowk, signal context, related segments | Static + operational state |
| TrafficSensor | Logical/real/replayed observation source | Yes |
| TrafficFlowObserved | Time-stamped traffic observation | Append-only |
| BuildingZone | Representative building/zone energy entity | Static + operational state |
| EnergyMeter | Logical/real/replay energy source | Yes |
| EnergyConsumptionObserved | Time-stamped energy observation | Append-only |
| WeatherStation/WeatherObserved | Weather context entity/observation | Append-only |
| AirQualityStation/AirQualityObserved | Environment entity/observation | Append-only |
| Forecast | Versioned prediction record | Append-only |
| Scenario | Defined baseline/intervention template | Versioned |
| ScenarioRun | Immutable execution of scenario | Append-only |
| Recommendation | Advisory output with evidence | Append-only/status-updatable |
| ModelVersion | Metadata/URI/metrics of approved model | Versioned |

### 9.2 Relationship model

```text
StudyArea
  ├── contains → RoadSegment
  ├── contains → Intersection
  ├── contains → BuildingZone
  └── contains → Sensor/Station

RoadSegment
  ├── startsAt / endsAt → Intersection
  ├── observedBy → TrafficSensor
  ├── receives → TrafficFlowObserved
  ├── has → Forecast
  └── isTargetOf → Recommendation

BuildingZone
  ├── measuredBy → EnergyMeter
  ├── receives → EnergyConsumptionObserved
  └── has → Forecast

Scenario
  └── executedAs → ScenarioRun

ScenarioRun
  ├── produces → Scenario KPI records
  └── supports → Recommendation
```

### 9.3 Twin state semantics

For each mutable entity, the system should retain:

| State category | Meaning | Storage location |
|---|---|---|
| Reported/observed state | Most recent valid source observation | `entity_current_state` + observations hypertable |
| Historical state | All accepted observations | TimescaleDB hypertable |
| Predicted state | Model-generated future estimate | `forecasts` table |
| Simulated state | Explicit scenario output | `scenario_runs` + KPI/result tables/artifacts |
| Desired state | Not implemented in MVP | Future extension only |

---

## 10. Canonical data model approach

### 10.1 Design choice

The MVP uses **custom JSON entities inspired by NGSI-LD and FIWARE Smart Data Models**, stored as structured relational fields plus JSONB where needed. It is not claimed to be a fully compliant NGSI-LD broker implementation.

The canonical model uses these principles:

- Globally unique URN-style IDs where practical.
- Explicit `type` values.
- ISO-8601 timestamps in UTC.
- GeoJSON geometry for spatial references.
- Explicit units.
- Source/provenance metadata on every observation/forecast.
- Separate static entity data from high-frequency observations.
- Stable field names across simulation, replay, and live modes.

### 10.2 Example traffic entity

```json
{
  "id": "urn:ngsi-ld:RoadSegment:viman-somnath-001",
  "type": "RoadSegment",
  "name": "Viman Nagar to Somnath Nagar Segment 001",
  "geometry": {
    "type": "LineString",
    "coordinates": [[73.914, 18.567], [73.916, 18.568]]
  },
  "laneCount": 2,
  "capacityVehPerHour": 900,
  "fromIntersectionId": "urn:ngsi-ld:Intersection:viman-nagar-chowk",
  "toIntersectionId": "urn:ngsi-ld:Intersection:somnath-nagar-chowk",
  "networkVersion": "v0.1"
}
```

### 10.3 Example forecast

```json
{
  "id": "urn:ngsi-ld:TrafficForecast:viman-somnath-001:2026-09-19T12:15:00Z",
  "type": "TrafficForecast",
  "targetEntityId": "urn:ngsi-ld:RoadSegment:viman-somnath-001",
  "targetMetric": "congestionIndex",
  "generatedAt": "2026-09-19T12:00:00Z",
  "targetTime": "2026-09-19T12:15:00Z",
  "horizonMinutes": 15,
  "prediction": 0.71,
  "lowerBound": 0.62,
  "upperBound": 0.80,
  "modelVersion": "traffic-xgb-v1",
  "sourceMode": "predicted",
  "basedOnObservationWindow": {
    "start": "2026-09-19T11:00:00Z",
    "end": "2026-09-19T12:00:00Z"
  },
  "quality": {
    "status": "valid",
    "inputCompleteness": 0.95
  }
}
```

---

## 11. Persistence architecture

### 11.1 Database choice

A single PostgreSQL instance with TimescaleDB and PostGIS extensions is the MVP persistence foundation.

Reasons:

- One operational database rather than separate relational/time-series/geospatial services.
- SQL joins across assets, time-series observations, and geometry.
- PostGIS supports map and spatial-query needs.
- TimescaleDB supports hypertables, time bucketing, retention, and continuous aggregates.
- The MVP’s low event rate does not justify Kafka, InfluxDB plus PostgreSQL, or a graph database.

### 11.2 Logical database groups

| Schema/group | Purpose |
|---|---|
| `core` | Study area, entities, relationship tables, current state |
| `telemetry` | Observations, quality status, ingestion metadata, hypertables |
| `forecasting` | Features, forecasts, model versions, explanation metadata |
| `simulation` | Scenario templates, runs, KPIs, result references |
| `decision` | Recommendations, threshold rules, evidence links |
| `platform` | Users, roles, API metadata, jobs, audit events |

### 11.3 Key tables

| Table | Purpose |
|---|---|
| `study_areas` | Boundary/version/capture metadata |
| `road_segments` | Static road attributes + PostGIS line geometry |
| `intersections` | Static junction attributes + point geometry |
| `sensors` | Logical/real source registry |
| `building_zones` | Energy entity geometry/metadata |
| `entity_current_state` | Latest valid state per entity/metric/source context |
| `traffic_observations` | Timescale hypertable for traffic observations |
| `energy_observations` | Timescale hypertable for energy observations |
| `environment_observations` | Timescale hypertable for weather/AQI observations |
| `ingestion_errors` | Invalid/rejected events and reasons |
| `forecasts` | Immutable prediction records |
| `model_versions` | Model registry metadata / MLflow links |
| `scenario_templates` | Allowed scenario definitions |
| `scenario_runs` | Execution metadata/status/configuration/seed |
| `scenario_kpis` | Baseline/intervention comparison metrics |
| `recommendations` | Advisory outputs and evidence references |
| `audit_events` | Relevant user/system actions |

### 11.4 Storage rules

- Static geometry/entities are versioned but change infrequently.
- Observations are append-only except for controlled correction procedures.
- Current state is an upserted projection of the latest valid observation.
- Forecasts and scenario outputs are immutable records.
- Raw imported files, SUMO artifacts, model artifacts, and optional chart exports are stored in MinIO/local object storage with URI references in PostgreSQL.
- Database migrations must be versioned.

---

## 12. MQTT architecture

### 12.1 Broker

Use Eclipse Mosquitto in Docker Compose for the MVP.

### 12.2 Topic convention

```text
nagartwin/{environment}/{mode}/{domain}/{entity-or-source-id}
```

Examples:

```text
nagartwin/dev/simulation/traffic/sumo-baseline-001
nagartwin/dev/replay/traffic/pune-counts-rto-2023
nagartwin/dev/replay/energy/uci-electricity
nagartwin/dev/live/weather/open-meteo-pune
nagartwin/dev/live/airquality/cpcb-station-id
nagartwin/dev/system/health
```

### 12.3 Topic design rules

- `environment` is `dev`, `demo`, or `prod` only when applicable.
- `mode` is mandatory: `simulation`, `replay`, or `live`.
- `domain` is `traffic`, `energy`, `weather`, `airquality`, or `system`.
- MQTT topics identify routing; canonical event payload identifies entity and provenance.
- MQTT is not the system-of-record; PostgreSQL is.

### 12.4 QoS and delivery

| Use | Suggested QoS | Rationale |
|---|---:|---|
| Simulation/replay telemetry | 0 or 1 | Loss-tolerant for demo; use 1 where ordering/reliability matters |
| Live permitted sensor telemetry | 1 | At-least-once delivery with deduplication at ingest |
| System health/control notifications | 1 | Delivery should be reliable |

### 12.5 Ingestion idempotency

The ingestion module must handle at-least-once delivery:

- Use `eventId` where supplied.
- Otherwise derive deterministic event identity from source ID, entity ID, observed timestamp, metric, and payload hash.
- Reject or mark duplicates without corrupting current state.

---

## 13. REST and WebSocket API architecture

### 13.1 API design principles

- REST for query, configuration, scenario creation, model metadata, and exports.
- WebSocket for current-state, forecast, recommendation, and scenario-progress push events.
- JSON responses use ISO-8601 timestamps and explicit units.
- APIs always return provenance where a value is displayed.
- Long-running scenario tasks return an ID/status rather than blocking HTTP.
- Version public APIs under `/api/v1`.

### 13.2 Core REST resources

| Resource | Example endpoint | Purpose |
|---|---|---|
| Health | `GET /health` | Application/database/broker health |
| Study area | `GET /api/v1/study-area` | Corridor boundary and metadata |
| Roads | `GET /api/v1/roads` | Road geometries/current summary |
| Road detail | `GET /api/v1/roads/{id}` | Static/current/historical/forecast data |
| Intersections | `GET /api/v1/intersections` | Junction state/configuration |
| Entities | `GET /api/v1/entities/{id}` | Generic entity detail |
| Observations | `GET /api/v1/observations` | Filtered time-range data |
| Forecasts | `GET /api/v1/forecasts` | Query predictions by target/horizon |
| Recommendations | `GET /api/v1/recommendations` | Advisory items/evidence |
| Scenarios | `GET /api/v1/scenarios` | Predefined templates |
| Run scenario | `POST /api/v1/scenario-runs` | Start approved scenario |
| Scenario status | `GET /api/v1/scenario-runs/{id}` | Progress/results/artifacts |
| Model metadata | `GET /api/v1/models` | Model versions/metrics/status |
| Data quality | `GET /api/v1/data-quality` | Freshness/errors/coverage |

### 13.3 WebSocket channels

| Channel | Event types |
|---|---|
| `/ws/operations` | `state.updated`, `forecast.created`, `recommendation.created`, `alert.created` |
| `/ws/scenarios/{runId}` | `scenario.started`, `scenario.progress`, `scenario.completed`, `scenario.failed` |
| `/ws/system` | `health.changed`, `ingestion.error`, `source.stale` |

### 13.4 Standard event shape

```json
{
  "eventType": "state.updated",
  "eventId": "uuid",
  "emittedAt": "2026-09-19T12:00:04Z",
  "entityId": "urn:ngsi-ld:RoadSegment:viman-somnath-001",
  "sourceMode": "simulation",
  "payload": {},
  "traceId": "optional-correlation-id"
}
```

---

## 14. Validation and data-quality architecture

### 14.1 Validation stages

| Stage | Checks |
|---|---|
| Transport | Topic/source allowed, message parseable, payload size limit |
| Schema | Required keys, types, enum values, units |
| Identity | Known/allowed entity IDs or controlled registration path |
| Time | ISO-8601, no impossible future/stale timestamps beyond configured tolerance |
| Range | Speed, counts, energy, AQI/weather values within sensible bounds |
| Spatial | Valid GeoJSON/geometry reference where needed |
| Duplicate | Event ID/hash not already accepted |
| Quality | Score/status computed and attached |

### 14.2 Quality statuses

| Status | Meaning |
|---|---|
| `valid` | Passed validation and eligible for state update/model features |
| `suspect` | Stored but requires caution; may be excluded from models |
| `stale` | Too old for current operational view |
| `duplicate` | Repeated event; not re-applied to state |
| `invalid` | Fails required validation; retained in error log only |
| `missing` | Expected value absent/unavailable |

### 14.3 Quality-score use

Data-quality score must influence:

- Whether an observation updates current state.
- Whether it is eligible for feature generation.
- UI status/badges.
- Recommendation confidence display.

---

## 15. ML architecture

### 15.1 Model strategy

The MVP trains only two primary supervised regression models:

| Domain | Baselines | Selected MVP model | Future only |
|---|---|---|---|
| Traffic | Persistence, historical average | XGBoost regressor | LSTM/TCN/STGNN/GNN |
| Energy | Persistence, same-hour average | XGBoost regressor | LSTM/TCN/physics-informed model |

### 15.2 Feature pipeline

```text
observations + static asset features + weather/context
        ↓
quality/freshness checks
        ↓
lag features + rolling aggregates + calendar features
        ↓
feature snapshot with timestamp/entity/model context
        ↓
train or inference input
```

Traffic features may include:

- Prior speed/count/congestion values.
- 5/10/15/30/60-minute lags.
- Rolling average/min/max/variance.
- Time of day/day of week/weekend flag.
- Road capacity/lane count.
- Weather values.
- Optional nearby segment aggregate when data is available.

Energy features may include:

- Prior load values.
- Rolling load statistics.
- Hour/day/weekend/holiday flags.
- Temperature/humidity/weather.
- Building/zone metadata.
- Occupancy proxy if approved/available.

### 15.3 Training architecture

```text
Versioned input dataset
        ↓
Chronological train/validation/test split
        ↓
Baseline generation
        ↓
XGBoost training / parameter selection
        ↓
Evaluation: MAE, RMSE, optional sMAPE
        ↓
Prediction interval method
        ↓
MLflow params, metrics, artifacts, model registration
        ↓
Approved model version referenced by inference service
```

### 15.4 Inference architecture

- Scheduled inference is the default: run every 5 minutes or configured interval.
- On-demand inference may be added for a selected entity but must reuse the same feature/model code.
- A model must be loaded by explicit approved model version.
- Prediction output includes target time, horizon, value, interval, input completeness, model version, and provenance.
- If sufficient valid features are unavailable, inference returns unavailable/stale status rather than fabricating a forecast.

### 15.5 Explainability

- Store global model feature importance for every model version.
- Generate SHAP explanations for selected or sampled forecasts where computationally appropriate.
- Recommendations must reference the forecast/model/version that triggered them.

---

## 16. Recommendation architecture

### 16.1 MVP rule engine

The recommendation engine is deterministic and transparent.

Example rules:

```text
IF traffic.congestion_forecast_15m >= configured_threshold
AND forecast.input_completeness >= configured_minimum
THEN create advisory: "Evaluate alternate routing or signal-timing scenario"

IF energy.load_forecast_60m >= configured_peak_threshold
THEN create advisory: "Review peak-demand mitigation scenario"

IF AQI/PM threshold exceeded
THEN create advisory: "Flag environmental condition for monitoring"
```

### 16.2 Recommendation lifecycle

```text
forecast/scenario evidence
        ↓
rule condition met
        ↓
recommendation created (advisory)
        ↓
visible in UI with evidence/provenance
        ↓
optional user acknowledgement/status update
        ↓
never sent to physical actuator
```

### 16.3 Required fields

- Recommendation ID/type/status.
- Target entity.
- Trigger/rule ID.
- Source mode and data-quality/confidence.
- Evidence links to forecast/observation/scenario run.
- Suggested action.
- Human approval requirement.
- Created/acknowledged timestamps.

---

## 17. SUMO and scenario architecture

### 17.1 Network creation

```text
OpenStreetMap study-area boundary
        ↓
OSM extract / validation
        ↓
SUMO netconvert / network editing
        ↓
Traffic-light/junction configuration
        ↓
Route/demand generation
        ↓
SUMO network version
```

### 17.2 Scenario service responsibilities

- Validate requested scenario against predefined safe templates.
- Create immutable run record before execution.
- Run baseline and intervention scenarios with controlled seed/demand.
- Use TraCI to query state/control allowed simulated signal parameters.
- Compute/store KPIs.
- Stream progress to WebSocket clients.
- Save artifacts such as configuration files, tripinfo, summary, queues, and result JSON.
- Prevent scenario data from changing current observed twin state.

### 17.3 Initial scenario templates

| Template | Parameter | Purpose |
|---|---|---|
| `baseline_peak` | demand profile, seed | Reference congestion behavior |
| `signal_timing_adjustment` | phase durations/offsets within allowed range | Compare delay/queue reduction |
| `turn_restriction` | selected movement disabled | Test movement-management impact |
| `demand_surge` | demand multiplier | Test resilience under peak load |

### 17.4 Scenario output contract

```json
{
  "scenarioRunId": "scenario-run-001",
  "scenarioTemplate": "signal_timing_adjustment",
  "networkVersion": "v0.1",
  "seed": 42,
  "status": "completed",
  "baseline": {
    "avgTravelTimeSec": 210.4,
    "avgDelaySec": 79.2,
    "maxQueueVehicles": 42,
    "throughputVehicles": 530
  },
  "intervention": {
    "avgTravelTimeSec": 185.8,
    "avgDelaySec": 60.1,
    "maxQueueVehicles": 31,
    "throughputVehicles": 552
  },
  "delta": {
    "avgTravelTimeSec": -24.6,
    "avgDelaySec": -19.1,
    "maxQueueVehicles": -11,
    "throughputVehicles": 22
  },
  "sourceMode": "simulation"
}
```

---

## 18. Frontend architecture

### 18.1 Frontend responsibilities

The React frontend must:

- Render the corridor and entity layers on MapLibre.
- Subscribe to current state/forecast/recommendation events.
- Query historical data on demand.
- Display data provenance, freshness, quality, timestamp, unit, and model/scenario metadata.
- Support scenario template selection and execution status.
- Render baseline/intervention KPI comparisons.
- Keep analytical 2D workflow primary.

### 18.2 Suggested frontend module structure

```text
src/
  app/                # application bootstrap, routes, providers
  api/                # REST/WebSocket clients and typed contracts
  features/
    operations-map/   # MapLibre layers, selection, legend
    entity-detail/    # entity drawer/panel and charts
    traffic/          # traffic view and forecast display
    energy/           # energy view and forecast display
    environment/      # environment context/alerts
    scenarios/        # scenario selection/progress/results
    recommendations/  # advisory cards/evidence
    system-status/    # health/freshness/provenance status
  components/         # reusable UI components
  design-system/      # tokens, typography, buttons, badges, charts
  types/              # canonical frontend types
```

### 18.3 Map layer ordering

```text
1. Basemap (OpenStreetMap via approved tile provider)
2. Study-area boundary
3. Road-segment base geometry
4. Traffic state overlay
5. Scenario/simulation overlay (only when selected)
6. Sensor/entity markers
7. Building/energy entities
8. Alerts/recommendations
9. Labels/legend/controls
```

### 18.4 Optional 3D architecture

If added after MVP:

```text
CesiumJS
  ├── Optional Google Photorealistic 3D Tiles OR allowed open 3D source
  ├── Custom road/vehicle/sensor/forecast overlays from backend
  └── Same REST/WebSocket data contracts as MapLibre
```

The 3D layer is a visualization client. It does not own twin state, perform ML, alter simulation, or replace the 2D operator dashboard.

---

## 19. Deployment architecture

### 19.1 Docker Compose services

```text
compose.yaml
  ├── frontend          # React static app/dev server
  ├── backend           # FastAPI API + internal modules
  ├── worker            # optional replay/inference/scheduled jobs
  ├── mosquitto         # MQTT broker
  ├── postgres          # PostgreSQL + TimescaleDB + PostGIS image
  ├── minio             # optional artifacts/raw storage
  ├── mlflow            # optional local tracking server
  └── sumo-worker       # scenario execution environment
```

### 19.2 Local development

- Run all dependencies via Docker Compose.
- Mount source directories for development where appropriate.
- Use `.env` locally but commit only `.env.example`.
- Store development artifacts in a local ignored directory or MinIO bucket.
- Keep configuration values explicit: study area, update interval, freshness threshold, model version, simulation network version.

### 19.3 Demo deployment

- One small VM is adequate for MVP demonstration.
- Use reverse proxy/TLS if exposed externally.
- Use a non-production dataset/credentials profile.
- Keep MapLibre/OSM 2D mode as a fallback if optional 3D service/API/billing is unavailable.

### 19.4 Production migration path

Only after requirements justify it:

```text
MVP Compose
  → separate worker processes
  → managed Postgres/object storage
  → optional Orion-LD/Ditto integration
  → optional Kafka for high-volume event streams
  → observability stack
  → container orchestration if multi-node requirements arise
```

---

## 20. Security architecture

### 20.1 Authentication and authorization

| Layer | MVP approach | Future extension |
|---|---|---|
| Dashboard/API | Basic JWT/session token for remote demo; role concept | OAuth2/OIDC, fine-grained roles |
| MQTT | Username/password; TLS if real remote source | Client certificates/device identity |
| Database | Per-service credentials; network isolation | Secret manager/rotation |
| Object storage | Bucket credentials; private artifacts | IAM policies/versioned artifact governance |

### 20.2 Roles

| Role | Permissions |
|---|---|
| Viewer | Read map, state, forecasts, completed scenarios, recommendations |
| Analyst | Viewer + run approved scenario templates + export results |
| Admin/Developer | Manage source configuration, templates, thresholds, deployment |

### 20.3 Security rules

- No secret in Git, logs, screenshots, or Markdown samples.
- No unrestricted scenario parameter injection from unauthenticated clients.
- No endpoint may send commands to public infrastructure.
- Validate all external source payloads.
- Enforce request limits/size limits for APIs where practical.
- Retain data provenance/audit events for important state, model, and scenario operations.

---

## 21. Observability and failure handling

### 21.1 Minimum observability

| Signal | Required MVP implementation |
|---|---|
| Application health | `/health` and dependency readiness checks |
| Logs | Structured application/container logs |
| Ingestion | accepted/rejected/duplicate counts and errors |
| Data freshness | last observed timestamp by source/entity |
| Model inference | run status, latency, failed/missing-feature count |
| Scenario execution | queued/running/completed/failed + runtime |
| Database | basic connection/readiness monitoring |
| Dashboard | clear stale/unavailable state rather than silent blank screen |

### 21.2 Failure behavior

| Failure | Required behavior |
|---|---|
| MQTT unavailable | Mark source unavailable; retain last known state; retry connection |
| Invalid event | Store structured validation error; do not update current state |
| Duplicate event | Ignore/mark duplicate; do not double-count |
| Database unavailable | Return degraded health; queue/retry only if safely implemented; do not claim freshness |
| Model unavailable | Return last valid forecast metadata or explicit unavailable state |
| Missing features | Skip forecast for target; record reason |
| SUMO failure | Mark scenario run failed; preserve logs/config; do not present partial output as completed |
| Weather/AQI API limit/failure | Mark context stale; do not block traffic twin operation |
| Optional 3D failure | Keep 2D dashboard fully functional |

---

## 22. Testing architecture

### 22.1 Required test layers

| Test layer | Examples |
|---|---|
| Unit | Schema validation, feature functions, rule evaluation, KPI calculations |
| Integration | MQTT → ingest → DB; API → DB; SUMO → scenario record; model → forecast storage |
| End-to-end | Replay event appears on map; run scenario and render comparison |
| Data quality | Missing timestamp, invalid range, duplicate, stale event, unknown entity |
| ML | Chronological split, no leakage, baseline comparison, model serialization/loading |
| UI | Provenance labels visible, scenario outputs separated, legend present |
| Failure | Broker off, model missing, bad payload, scenario timeout |

### 22.2 Acceptance test scenario

```text
Given: Docker Compose stack is running
And: a replay dataset is available
When: replay is started
Then: MQTT events are validated and written to observations
And: current state is updated
And: map shows REPLAY values with timestamp
And: scheduled model produces PREDICTED traffic forecast
And: recommendation appears if threshold condition is met
When: user runs approved scenario
Then: SUMO baseline/intervention run completes
And: KPI comparison is rendered as SIMULATION output
```

---

## 23. Performance and capacity assumptions

These are MVP planning assumptions, not performance claims.

| Dimension | Assumption |
|---|---|
| Road segments | 8–15 |
| Main intersections | 2 |
| Logical sensors/entities | 5–15 traffic; 1+ energy; optional weather/AQI |
| Event rate | Approximately 1–6 messages/sec during MVP demonstration |
| Message size | Few hundred bytes JSON |
| Dashboard users | 1–5 concurrent users |
| Forecast schedule | Every 5 minutes |
| Scenario runs | A few per day during development/demo |
| Retention | 3–6 months of prototype data unless revised |

Likely MVP bottlenecks are:

1. SUMO runtime for larger networks/scenarios.
2. Incorrect/overly complex OSM-to-SUMO network conversion.
3. Frontend rendering if sending too much time-series data at once.
4. Model/data quality, not database throughput.

Mitigations:

- Freeze small boundary and routes.
- Preprocess/validate SUMO network manually.
- Downsample chart data and paginate/filter API responses.
- Build simple baselines before advanced models.

---

## 24. Architecture constraints and invariants

These are mandatory rules.

1. The authoritative study area is the versioned Viman Nagar–Somnath Nagar boundary.
2. MQTT is transport; PostgreSQL is the system of record.
3. All source modes use the same canonical observation contract after transformation.
4. Observed, predicted, and scenario state are separate.
5. Every externally visible value includes provenance and time context.
6. Simulation output is never shown as a live city measurement.
7. Forecasts are never written as observations.
8. A recommendation is advisory and cannot actuate infrastructure.
9. No PII/video/plate/face data is accepted.
10. XGBoost and simple baselines are the required initial forecasting approach.
11. A model must be evaluated before it becomes the active dashboard model.
12. The 2D dashboard is the required user interface; 3D is optional.
13. New infrastructure requires a documented reason and architecture decision.
14. Schema/API changes must be versioned and backward-aware.
15. Documentation changes accompany code changes that alter behavior.

---

## 25. Future architecture extensions

| Extension | Trigger for adoption | Architectural change |
|---|---|---|
| FIWARE Orion-LD | Need external context interoperability/demo | Add context broker adapter and synchronize canonical entities |
| Eclipse Ditto | Real device twin/desired-state/policy need | Add Ditto connector as device/twin middleware |
| Kafka | Sustained high event rate, replay scale, multiple consumers | Add event backbone while retaining canonical schema |
| Graph database | Deep dynamic network/relationship queries prove necessary | Replicate selected entities/relations; do not replace Postgres blindly |
| Cesium/3D | 3D improves user decision or presentation | Add second visualization client using same APIs |
| EnergyPlus | Building metadata/HVAC data becomes available | Add offline building simulation pipeline and scenario adapter |
| STGNN/GNN | Multiple validated road sensors + topology + data history | Add research comparison model, not replacement by default |
| Edge inference | Real sensor latency/privacy need | Deploy validated lightweight inference component near source |
| Kubernetes | Multi-node/high availability/multi-team workload | Container orchestration after operational need demonstrated |

---

## 26. Relationship to existing files

### 26.1 Keep existing architecture/tech-stack report

The earlier Claude-generated `Digital-Twin-Architecture-and-Tech-Stack.md` is useful as a **research and decision background artifact**. Keep it in a `docs/reference/` or `docs/archive/` directory, for example:

```text
docs/reference/Digital-Twin-Architecture-and-Tech-Stack.md
```

It contains useful competitor analysis, alternatives, and decision rationale. It must not override the current implementation decisions in this document without an explicit update.

### 26.2 Keep the comprehensive documentation-plan file

Keep `Digital-Twin-Project-Documentation-Plan.md` as a **future documentation inventory**, not as a current mandatory task list. Recommended location:

```text
docs/reference/Digital-Twin-Project-Documentation-Plan.md
```

The project currently uses a compact active documentation set:

```text
PROJECT_CONTEXT.md
PRD.md
TECHNICAL_ARCHITECTURE.md
DATA_AND_ML_PLAN.md
UI_UX_SPEC.md
ROADMAP.md
DELIVERABLES.md
```

The larger plan becomes useful when the project expands, multiple agents contribute, a paper is prepared, or production/research-grade extensions are added.

---

## 27. Implementation sequence

Build modules in this order:

1. Repository, Docker Compose, environment configuration, Postgres extensions.
2. Study-area GeoJSON, OSM extraction, static PostGIS asset registry.
3. Canonical schemas, database migrations, core REST API.
4. MQTT broker, simulation/replay publisher, validation/ingestion pipeline.
5. Current/historical twin-state APIs and MapLibre operations map.
6. SUMO network, baseline scenario, TraCI integration, KPI persistence.
7. Traffic baseline/XGBoost training and scheduled forecasting.
8. Energy replay/synthetic pipeline and energy baseline/XGBoost forecasting.
9. Rule-based recommendations and evidence links.
10. Scenario UI and baseline/intervention comparison.
11. MLflow, tests, health/status view, GitHub Actions.
12. Optional weather/AQI, SHAP visualization, 3D client, live source adapter.

---

## 28. Next technical documents

Create these next, in order:

1. `DATA_AND_ML_PLAN.md` — exact datasets, licenses, data model fields, model-training and evaluation protocol.
2. `UI_UX_SPEC.md` — information architecture, dashboard screens, interaction rules, visual/provenance requirements.
3. `ROADMAP.md` — phased tasks, dependencies, milestones, ownership.
4. `DELIVERABLES.md` — acceptance evidence per module and agent.

---

## 29. Final architecture statement

> NagarRoad Twin is implemented as a modular FastAPI-based urban digital-twin application using MQTT for input transport, PostgreSQL with TimescaleDB and PostGIS for authoritative state, SUMO/TraCI for traffic what-if simulation, XGBoost for initial traffic and energy forecasting, rule-based advisory recommendations, and a React/MapLibre operations dashboard. Simulation, replay, live, and predicted data remain explicitly separated by provenance and storage semantics. The architecture prioritizes correctness, reproducibility, explainability, and a credible migration path over unnecessary enterprise complexity.
