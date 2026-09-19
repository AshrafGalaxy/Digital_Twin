# Deliverables and Acceptance Criteria
## Digital Twin-Enabled Smart City Analytics Platform

> **Document status:** Baseline delivery contract  
> **Companion documents:** `PROJECT_CONTEXT.md`, `PRD.md`, `TECHNICAL_ARCHITECTURE.md`, `DATA_AND_ML_PLAN.md`, `UI_UX_SPEC.md`, `ROADMAP.md`  
> **Pilot study area:** Viman Nagar Chowk (Phoenix Mall) ↔ Somnath Nagar Chowk corridor, Pune  
> **Purpose:** Define exactly what each workstream must deliver, what evidence is required, and what qualifies as complete.

---

## 1. Purpose

This document is the delivery contract for the project. It converts requirements and roadmap phases into reviewable outputs.

Use it to answer:

- What must be built?
- Who owns each output?
- What artifacts prove completion?
- What quality checks are required?
- What must not be claimed?
- What is the minimum demonstration package?
- When is the pilot ready for academic, technical, or stakeholder review?

A feature is not complete when code merely exists. It is complete only when its required artifact, evidence, documentation, and acceptance checks are available.

---

## 2. Delivery principles

1. **Evidence over assertion:** “Working” requires screenshots, API responses, logs, metrics, tests, artifacts, or reproducible steps.
2. **Provenance always:** Every data-facing deliverable visibly distinguishes `LIVE`, `REPLAY`, `SIMULATION`, and `PREDICTED`.
3. **No hidden claims:** Locality, synthetic-data, benchmark-data, and simulation limitations must be documented.
4. **Reproducibility required:** A new contributor must be able to run the primary demo using documented steps.
5. **Safety by design:** No deliverable may control real public infrastructure.
6. **Documentation travels with code:** Any behavior/schema/model/UI change updates the relevant active Markdown file.
7. **Small correct pilot first:** Optional 3D, advanced models, context brokers, and enterprise tooling cannot block MVP delivery.
8. **Reviewable modules:** Each workstream produces a stand-alone artifact that can be assessed independently.

---

## 3. Ownership model

| Delivery owner | Core responsibility | Required coordination |
|---|---|---|
| Product/governance owner | Scope, institutional user value, safety boundaries, advisory rules | All workstreams |
| GIS/data owner | Study area, OSM assets, datasets, manifests, licenses, data mapping | Simulation, backend, ML, UI |
| Backend/twin-core owner | APIs, schemas, state storage, validation, WebSockets, recommendations | Data, ML, simulation, UI |
| Simulation owner | SUMO network, scenarios, TraCI runs, KPI artifacts | GIS, backend, UI, research |
| ML/analytics owner | Features, baselines, XGBoost, evaluation, MLflow, model cards | Data, backend, UI, research |
| UI/UX owner | Dashboard, provenance display, scenarios, accessibility, usability evidence | Backend, product, ML, simulation |
| Platform owner | Docker, CI, configuration, security, observability, runbook | All workstreams |
| Research/delivery owner | Evaluation, metrics, figures, report/paper, demo, limitations | All workstreams |

A single person may hold multiple roles, but the deliverable evidence remains required.

---

## 4. Master deliverables index

| ID | Deliverable | Owner | Priority | Roadmap phase |
|---|---|---|---:|---:|
| D-01 | Project foundation and repository baseline | Product + platform | Must | 0 |
| D-02 | Pilot study-area and GIS asset package | GIS/data | Must | 1 |
| D-03 | Dataset catalog, manifests, licenses, and provenance package | Data/governance | Must | 1 |
| D-04 | Core database, canonical schema, and twin-state package | Backend/twin core | Must | 2 |
| D-05 | Ingestion, validation, replay, and simulation-stream package | Data + backend | Must | 2–3 |
| D-06 | 2D operations dashboard package | UI/UX + backend | Must | 3 |
| D-07 | SUMO network and scenario-comparison package | Simulation | Must | 4 |
| D-08 | Traffic forecasting package | ML/analytics | Must | 5 |
| D-09 | Energy forecasting package | ML/analytics | Must | 5 |
| D-10 | Advisory recommendation and governance workflow package | Backend + UI + product | Must | 6 |
| D-11 | Platform reliability, security, CI, and runbook package | Platform | Must | 6 |
| D-12 | Evaluation, research evidence, and final demo package | Research/delivery | Must | 7 |
| D-13 | Optional 3D presentation package | UI/UX | Could | 8 |
| D-14 | Optional interoperability/advanced research package | Architecture/ML | Could | 8 |

---

## 5. D-01: Project foundation and repository baseline

### 5.1 Objective

Create a controlled development environment with approved project context, active documentation, reference materials, repository conventions, and clear scope boundaries.

### 5.2 Required artifacts

- [ ] Repository created and accessible to contributors.
- [ ] Root active files present:

```text
PROJECT_CONTEXT.md
PRD.md
TECHNICAL_ARCHITECTURE.md
DATA_AND_ML_PLAN.md
UI_UX_SPEC.md
ROADMAP.md
DELIVERABLES.md
README.md
```

- [ ] Existing historical documents retained under `docs/reference/`:

```text
docs/reference/Digital-Twin-Architecture-and-Tech-Stack.md
docs/reference/Digital-Twin-Project-Documentation-Plan.md
```

- [ ] Repository directory structure created.
- [ ] `.gitignore` created for environment files, large data, artifacts, logs, and model files as appropriate.
- [ ] `.env.example` created with no secrets.
- [ ] Contributor/branch/PR conventions documented in README or `CONTRIBUTING.md`.
- [ ] Initial decision log or ADR index created.
- [ ] Initial issue/backlog structure created.

### 5.3 Evidence required

- Repository tree screenshot or listing.
- Link/path to active documents.
- Link/path to reference documents.
- Example `.env.example` without credentials.
- Initial README quick-start placeholder.

### 5.4 Acceptance criteria

- [ ] Active documentation is clearly distinguished from reference/archive material.
- [ ] No unapproved product name is used as the official platform identity.
- [ ] Scope and safety boundaries are visible to contributors.
- [ ] No secrets, private data, or large raw datasets are committed.

---

## 6. D-02: Pilot study-area and GIS asset package

### 6.1 Objective

Create the authoritative spatial representation of the Viman Nagar–Somnath Nagar pilot corridor.

### 6.2 Required artifacts

- [ ] Versioned `study_area.geojson`.
- [ ] Study-area metadata file containing:
  - boundary version;
  - capture date;
  - coordinate reference system;
  - bounding box;
  - OSM extraction/source method;
  - rationale for included/excluded roads.
- [ ] OSM raw extract or reproducible extraction script.
- [ ] Curated road-segment inventory: 8–15 segments.
- [ ] Intersection inventory: at least 2 core intersections.
- [ ] Logical traffic-source/sensor inventory: 5–15 sources.
- [ ] One building/zone energy entity.
- [ ] Stable URN-style IDs for all pilot assets.
- [ ] PostGIS import script/migration.
- [ ] GIS validation notes: directionality, turns, lane/signal assumptions, geometry corrections.

### 6.3 Minimum asset inventory fields

| Asset | Required fields |
|---|---|
| Study area | ID, version, polygon, capture date, source |
| Road segment | ID, name, line geometry, from/to intersection, direction, lane/capacity assumption |
| Intersection | ID, name, point geometry, connected segments, signal/priority assumption |
| Traffic source | ID, linked asset, source mode, supported metrics, location/reference |
| Energy zone | ID, linked geometry/reference, source type, metric/unit |

### 6.4 Evidence required

- Map screenshot showing corridor boundary, roads, intersections, and entities.
- GeoJSON validation output.
- Database query/API response returning registered assets.
- Asset inventory CSV/JSON/Markdown table.
- Notes documenting OSM limitations and assumptions.

### 6.5 Acceptance criteria

- [ ] Study area is limited to pilot boundary; no unplanned whole-city expansion.
- [ ] Every static asset has a stable ID.
- [ ] Roads and intersections are usable in MapLibre and SUMO workflows.
- [ ] Assumptions are documented rather than hidden.
- [ ] Geometry source/attribution is documented.

---

## 7. D-03: Dataset catalog, manifests, licenses, and provenance package

### 7.1 Objective

Ensure every data source is traceable, legally/ethically understood, and correctly characterized before use.

### 7.2 Required artifacts

- [ ] Dataset catalog containing all used/planned sources.
- [ ] One manifest per dataset.
- [ ] Data directory structure: raw/bronze/silver/gold/synthetic/samples.
- [ ] Download/import scripts or reproducible instructions.
- [ ] Source licenses/terms/attribution notes.
- [ ] Locality classification for each source:
  - pilot-local;
  - Pune non-local;
  - regional context;
  - benchmark;
  - synthetic;
  - simulation;
  - replay;
  - optional live.
- [ ] Privacy/sensitivity assessment.
- [ ] Data-retention and access notes.

### 7.3 Mandatory sources to document

- [ ] OpenStreetMap / OSMnx.
- [ ] Pune heterogeneous traffic count dataset.
- [ ] Weather source: Meteostat and/or Open-Meteo.
- [ ] Pune AQI/environment source if included.
- [ ] Energy source: permitted/replay/benchmark/synthetic.
- [ ] SUMO-generated source.
- [ ] Any benchmark dataset used for model comparisons.

### 7.4 Evidence required

- Dataset catalog table.
- Dataset manifest files.
- Direct URLs and download/access date.
- Example source/raw file checksum or hash where possible.
- Sample records with units and timestamps.
- Written prohibited-claims list for non-local/synthetic/benchmark data.

### 7.5 Acceptance criteria

- [ ] Every dataset has a known allowed use.
- [ ] Every dataset has an explicit limitation statement.
- [ ] No non-local dataset is labeled as pilot-corridor observation.
- [ ] No synthetic/replay/simulation data is displayed without provenance labels.
- [ ] No PII/CCTV/plates/faces/individual traces are included.
- [ ] Data imports are repeatable from scripts or instructions.

---

## 8. D-04: Core database, canonical schema, and twin-state package

### 8.1 Objective

Implement the authoritative data foundation for entities, observations, current state, forecasts, scenarios, and recommendations.

### 8.2 Required artifacts

- [ ] PostgreSQL instance with TimescaleDB and PostGIS enabled.
- [ ] Versioned database migrations.
- [ ] Canonical Pydantic/data schemas.
- [ ] Core entity tables.
- [ ] TimescaleDB observation hypertables.
- [ ] Current-state projection table/process.
- [ ] Forecast tables.
- [ ] Scenario templates/runs/KPIs tables.
- [ ] Recommendation tables.
- [ ] Ingestion-error and audit-event tables.
- [ ] Static GIS seed data import.
- [ ] Entity and relationship API contracts.

### 8.3 Required logical tables

```text
study_areas
road_segments
intersections
sensors
building_zones
entity_current_state
traffic_observations
energy_observations
environment_observations
forecasts
model_versions
scenario_templates
scenario_runs
scenario_kpis
recommendations
ingestion_errors
audit_events
```

### 8.4 State-separation acceptance test

The system must prove:

```text
Observed event      → historical observation + current state
Forecast result     → forecast record only
Scenario output     → scenario run/KPI records only
Recommendation      → evidence-linked advisory record only
```

No type may overwrite the other.

### 8.5 Evidence required

- Migration files.
- Schema diagram or table listing.
- Database initialization logs.
- Example entity, observation, forecast, scenario, and recommendation records.
- API response showing current/history/forecast separation.
- Test proving scenario output cannot overwrite observation state.

### 8.6 Acceptance criteria

- [ ] Database starts via Docker Compose.
- [ ] PostGIS geometry queries work.
- [ ] Time-series insertion/query works.
- [ ] Entity relationships are queryable.
- [ ] Provenance, units, timestamps, and quality fields persist.
- [ ] Schema is compatible with canonical NGSI-LD-inspired entity approach.

---

## 9. D-05: Ingestion, validation, replay, and simulation-stream package

### 9.1 Objective

Create a unified, reliable pathway from source data to twin state.

### 9.2 Required artifacts

- [ ] Eclipse Mosquitto service in Docker Compose.
- [ ] MQTT topic convention documentation.
- [ ] Source adapter/publisher for replay traffic data.
- [ ] Source adapter/publisher for synthetic/SUMO traffic data.
- [ ] Source adapter/publisher for energy replay/synthetic data.
- [ ] Optional weather/AQI poller adapter.
- [ ] Ingestion consumer/service.
- [ ] Validation module.
- [ ] Canonical transformation module.
- [ ] Duplicate/idempotency handling.
- [ ] Data-quality status calculation.
- [ ] Rejection/error logging.
- [ ] WebSocket state-update event emission.

### 9.3 Required validations

- [ ] Required schema fields.
- [ ] Source-mode validity.
- [ ] Timestamp format/timezone/freshness.
- [ ] Entity/source identity.
- [ ] Unit compatibility.
- [ ] Range/sanity checks.
- [ ] Geometry/reference validity.
- [ ] Duplicate-event handling.
- [ ] Missing value/quality flag behavior.

### 9.4 Required source modes

| Mode | Required evidence |
|---|---|
| `REPLAY` | Historical traffic/energy source replayed at configurable pace |
| `SIMULATION` | SUMO or synthetic event producer updates twin pipeline |
| `LIVE` | Optional; only if approved source exists |
| `PREDICTED` | Added later by forecast pipeline but must use same provenance semantics |

### 9.5 Evidence required

- MQTT publish/subscribe logs.
- Valid event accepted and stored.
- Invalid event rejected and stored as error.
- Duplicate event safely handled.
- Stale event visibly marked.
- Replay-to-map screenshot/video.
- API/WebSocket sample event.

### 9.6 Acceptance criteria

- [ ] Replay and simulation events use the same downstream validation/storage path.
- [ ] Current state updates only from valid, newer observations.
- [ ] Provenance survives from source to API/UI.
- [ ] Validation failures do not corrupt state.
- [ ] Processing latency can be measured.

---

## 10. D-06: 2D operations dashboard package

### 10.1 Objective

Deliver the authorized city-operations and planning dashboard that makes twin state, evidence, forecasts, scenarios, and advisories understandable.

### 10.2 Required artifacts

- [ ] React + TypeScript + Vite application.
- [ ] MapLibre operations map.
- [ ] Pilot boundary and static asset layers.
- [ ] Traffic state overlay with legend.
- [ ] Intersection/sensor/energy entity layers.
- [ ] Entity detail drawer/panel.
- [ ] Current/historical data view.
- [ ] Global freshness/source/system status.
- [ ] Provenance badge component.
- [ ] Data-quality indicator component.
- [ ] Empty/loading/error states.
- [ ] Responsive desktop/tablet behavior.
- [ ] Accessibility baseline.

### 10.3 Mandatory visible information

Every dynamic view must show as applicable:

- [ ] Timestamp.
- [ ] Unit.
- [ ] Source mode.
- [ ] Source/station/run reference.
- [ ] Freshness/quality status.
- [ ] `SIMULATION`/`PREDICTED` labels where relevant.

### 10.4 Evidence required

- Operations-map screenshot with traffic legend.
- Entity-detail screenshot showing history/provenance.
- Demonstration that replay and simulation modes display differently.
- Screenshot of stale/invalid/error state.
- Accessibility/keyboard check evidence.
- UI test/checklist results.

### 10.5 Acceptance criteria

- [ ] User can identify current corridor state.
- [ ] User can inspect a road/intersection/sensor/energy entity.
- [ ] User can distinguish observed/replay/simulation/prediction classes.
- [ ] Map is not the only source of status; list/card/text alternative exists for key information.
- [ ] UI does not present simulated/replayed state as live municipal data.

---

## 11. D-07: SUMO network and scenario-comparison package

### 11.1 Objective

Implement a reproducible mobility simulation for baseline-versus-intervention analysis.

### 11.2 Required artifacts

- [ ] SUMO installation/container configuration.
- [ ] Versioned pilot network files.
- [ ] Network construction/import script/notes.
- [ ] Baseline demand/routes configuration.
- [ ] Traffic-light/junction assumption documentation.
- [ ] At least one predefined intervention template.
- [ ] TraCI wrapper/service.
- [ ] Scenario-run configuration schema.
- [ ] Baseline run artifacts.
- [ ] Intervention run artifacts.
- [ ] KPI extraction/calculation.
- [ ] Scenario-run persistence/API.
- [ ] Scenario progress event/status.
- [ ] Scenario result UI/comparison view.

### 11.3 Required KPI output

| KPI | Required |
|---|---:|
| Average travel time | Yes |
| Average delay | Yes |
| Queue length | Yes |
| Throughput/vehicles completed | Yes |
| Emissions | Optional only if configured/documented |

### 11.4 Required scenario metadata

```text
Scenario template ID/version
Scenario run ID
Network version
Demand/route input version
Signal/turn/routing configuration
Random seed
Baseline/intervention designation
Start/end timestamps
Status
KPI output
Artifact URIs/log paths
```

### 11.5 Evidence required

- Network map/screenshot.
- Baseline simulation result.
- Intervention simulation result.
- Baseline vs intervention KPI table.
- Run configuration and seed.
- UI screenshot labeled `SIMULATION`.
- Failure test or documented failure behavior.

### 11.6 Acceptance criteria

- [ ] Baseline and intervention use comparable inputs/seed unless a difference is part of the scenario definition.
- [ ] Scenario result is reproducible from stored configuration.
- [ ] Scenario output stays separate from observed/current state.
- [ ] UI uses simulated-result language and displays assumptions.
- [ ] No scenario can actuate real traffic signals or infrastructure.

---

## 12. D-08: Traffic forecasting package

### 12.1 Objective

Deliver a defensible 15-minute traffic forecast pipeline based on a baseline-first evaluation approach.

### 12.2 Required artifacts

- [ ] Traffic target decision: average speed or documented congestion index.
- [ ] Time interval decision and rationale.
- [ ] Versioned data-preparation notebook/script.
- [ ] Chronological split implementation.
- [ ] Persistence baseline.
- [ ] Historical-average baseline if data supports it.
- [ ] Lag/rolling/calendar/weather feature pipeline.
- [ ] XGBoost training script/notebook.
- [ ] MLflow run records.
- [ ] Evaluation metrics/report.
- [ ] Prediction-interval method or documented deferral.
- [ ] Model artifact and feature schema.
- [ ] Traffic model card.
- [ ] Scheduled inference job/API integration.
- [ ] Forecast storage and dashboard visualization.
- [ ] Explanation/feature importance output.

### 12.3 Minimum evaluation metrics

- [ ] MAE.
- [ ] RMSE.
- [ ] Baseline comparison.
- [ ] Dataset size/time range/source classification.
- [ ] Input completeness/missingness report.
- [ ] Optional sMAPE where valid.
- [ ] Optional interval coverage/width if intervals are displayed.

### 12.4 Required limitations statement

> Initial traffic-model evaluation uses publicly available Pune intersection data and/or simulated pilot-corridor streams. It validates the forecasting pipeline and prototype behavior but does not establish measured forecasting accuracy for the Viman Nagar–Somnath Nagar corridor unless local ground-truth validation is later added.

### 12.5 Evidence required

- Training command/notebook and data-version reference.
- Chronological split visualization/table.
- Baseline vs XGBoost metrics table.
- MLflow run screenshot/export.
- Model card.
- Forecast JSON/API example.
- Dashboard screenshot with `PREDICTED` badge, horizon, interval/quality, and model version.
- Feature importance/SHAP plot or table.

### 12.6 Acceptance criteria

- [ ] Model is evaluated before dashboard activation.
- [ ] Model does not use future information in training features.
- [ ] Forecast is stored separately from observed state.
- [ ] Missing/low-quality inputs generate explicit status, not fabricated forecast.
- [ ] Baseline remains visible for comparison.
- [ ] Locality limitation appears in report/model documentation/UI context where relevant.

---

## 13. D-09: Energy forecasting package

### 13.1 Objective

Deliver a defensible 60-minute energy-demand forecast for a representative building/zone entity.

### 13.2 Required artifacts

- [ ] Energy source decision record: measured, replayed benchmark, or synthetic.
- [ ] Source license/provenance/limitation record.
- [ ] Energy ingestion/replay/synthetic generator.
- [ ] Versioned data-preparation script/notebook.
- [ ] Persistence and/or same-hour baseline.
- [ ] Lag/calendar/weather feature pipeline.
- [ ] XGBoost training script/notebook.
- [ ] MLflow run records.
- [ ] Evaluation report.
- [ ] Model artifact/feature schema.
- [ ] Energy model card.
- [ ] Scheduled inference/persistence.
- [ ] Dashboard chart and source-type label.
- [ ] Peak advisory rule if included.

### 13.3 Minimum evaluation metrics

- [ ] MAE.
- [ ] RMSE.
- [ ] Baseline comparison.
- [ ] Dataset/source classification.
- [ ] Data completeness/missingness report.

### 13.4 Required source limitation statement

For non-local/benchmark/synthetic energy:

> This pilot energy stream uses replayed benchmark or synthetic data. It demonstrates the data pipeline and forecasting methodology but is not a measured energy feed from a building in the Pune pilot corridor.

### 13.5 Evidence required

- Source decision record.
- Training/evaluation output.
- MLflow record.
- Model card.
- Forecast JSON/API example.
- Dashboard screenshot with source type, forecast, unit, quality, and model version.
- Peak advisory evidence if implemented.

### 13.6 Acceptance criteria

- [ ] Energy source type is visible throughout UI/API/report.
- [ ] Forecast is separate from observation.
- [ ] Model is compared against baseline.
- [ ] No actual energy savings are claimed without real intervention measurement.

---

## 14. D-10: Advisory recommendation and governance workflow package

### 14.1 Objective

Convert forecasts, quality signals, and scenario results into transparent, human-governed advisory recommendations.

### 14.2 Required artifacts

- [ ] Documented threshold/rule configuration.
- [ ] Rule-engine implementation.
- [ ] Recommendation database records/API.
- [ ] Recommendation evidence links to forecast/observation/scenario/model where relevant.
- [ ] Recommendations dashboard/list/detail view.
- [ ] Provenance/quality/confidence display.
- [ ] Human-approval statement.
- [ ] Recommendation review/acknowledgement lifecycle.
- [ ] Audit trail for rule/version/status changes where implemented.

### 14.3 Mandatory recommendation fields

```text
Recommendation ID
Type/severity/status
Target entity/corridor
Trigger rule and threshold
Observed/forecast/scenario evidence
Source mode and source ID
Data quality/confidence/input completeness
Model/scenario version where relevant
Suggested next step
Created timestamp
Human approval requirement
Review/acknowledgement state
```

### 14.4 Evidence required

- At least one traffic advisory generated from forecast/threshold.
- Optional energy/environment advisory if domain is implemented.
- Recommendation detail screenshot/API JSON.
- Evidence drill-down demonstration.
- Review/acknowledgement action demonstration.
- Statement that no physical action is triggered.

### 14.5 Acceptance criteria

- [ ] Recommendation is traceable to evidence.
- [ ] Recommendation is clearly labeled advisory.
- [ ] Recommendation includes uncertainty/quality context.
- [ ] UI does not use command/control language.
- [ ] Original evidence remains after review status changes.
- [ ] No recommendation can actuate external systems.

---

## 15. D-11: Platform reliability, security, CI, and runbook package

### 15.1 Objective

Make the MVP deployable, testable, secure enough for its data class, observable, and reproducible.

### 15.2 Required artifacts

- [ ] Docker Compose configuration.
- [ ] Service configuration documentation.
- [ ] `.env.example`.
- [ ] Local development instructions.
- [ ] Demo deployment instructions for a laptop/small VM.
- [ ] API health/readiness endpoint.
- [ ] Structured logging.
- [ ] Basic source/model/scenario health indicators.
- [ ] MQTT credentials/configuration.
- [ ] Basic API/dashboard authentication for remote demo.
- [ ] Database backup/export instructions.
- [ ] Unit/integration/end-to-end test suite.
- [ ] GitHub Actions workflow.
- [ ] Operational runbook including start/stop/debug/recovery/demo.

### 15.3 Required tests

| Test type | Minimum cases |
|---|---|
| Unit | Schema validation, rule evaluation, feature generation, KPI calculation |
| Integration | MQTT → ingestion → DB; API → DB; model → forecast storage; SUMO → scenario record |
| End-to-end | Replay update appears on dashboard; scenario run compares KPIs |
| Failure | Invalid event, duplicate event, stale event, broker unavailable, model unavailable, scenario failure |
| UI | Provenance label/legend, scenario simulation labeling, recommendation evidence display |

### 15.4 Evidence required

- `docker compose up` clean-start log.
- Health endpoint response.
- Test output.
- GitHub Actions run.
- Screenshot/log of degraded-state behavior.
- Runbook followed by another contributor or clean environment where possible.
- Security checklist completion.

### 15.5 Acceptance criteria

- [ ] Fresh clone can start core environment using documented steps.
- [ ] No secrets in repository.
- [ ] Failure is visible rather than silently hidden.
- [ ] Core services are health-checkable.
- [ ] Tests run automatically or through documented command.
- [ ] Remote demo access, if used, requires authentication.

---

## 16. D-12: Evaluation, research evidence, and final demo package

### 16.1 Objective

Produce the evidence needed to demonstrate technical validity, research discipline, governance relevance, and honest limitations.

### 16.2 Required artifacts

- [ ] Traffic baseline vs XGBoost evaluation report.
- [ ] Energy baseline vs XGBoost evaluation report.
- [ ] Feature ablation experiment, where feasible.
- [ ] End-to-end latency report.
- [ ] Data-quality resilience report.
- [ ] SUMO baseline vs intervention report.
- [ ] Usability/provenance comprehension walkthrough results.
- [ ] Architecture diagram.
- [ ] Data flow diagram.
- [ ] Dataset catalog/limitations appendix.
- [ ] Model cards appendix.
- [ ] Scenario assumptions appendix.
- [ ] Final demo script.
- [ ] Final project report or research-paper outline/draft.
- [ ] Limitations/threats-to-validity section.
- [ ] Reproducibility verification report.

### 16.3 Minimum experiments

| ID | Experiment | Required output |
|---|---|---|
| E-01 | Traffic persistence vs XGBoost | MAE/RMSE and limitations |
| E-02 | Energy persistence vs XGBoost | MAE/RMSE and source-type limitation |
| E-03 | Feature ablation | With/without selected feature group result |
| E-04 | Pipeline latency | Event-to-state/dashboard latency summary |
| E-05 | Data-quality resilience | Missing/duplicate/stale validation evidence |
| E-06 | Scenario comparison | Baseline/intervention KPI table and assumptions |
| E-07 | UX walkthrough | Provenance/forecast/scenario comprehension results |
| E-08 | Reproducibility | Clean setup/run evidence |

### 16.4 Final demo sequence

```text
1. Open Operations view and identify pilot corridor.
2. Show current twin state arriving from replay or simulation.
3. Select a road segment and inspect source, history, quality, and forecast.
4. Explain a traffic recommendation and evidence.
5. Show representative energy entity, source type, and forecast.
6. Open Scenario Studio.
7. Run/review baseline vs intervention SUMO simulation.
8. Compare KPI results and show SIMULATION label/assumptions.
9. Show that recommendation requires human review and no real actuation occurs.
10. Open System & Data Health to demonstrate operational transparency.
```

### 16.5 Required limitations section

The final report/demo must clearly state:

- The pilot is corridor-scale, not citywide.
- The project does not integrate with live Pune ATMS/ICCC systems unless formally approved and evidenced.
- Non-local Pune data does not establish local corridor accuracy.
- Benchmark/synthetic energy data does not represent a local meter feed.
- SUMO scenarios are model-dependent simulations, not proof of real-world outcomes.
- Recommendations are advisory, not autonomous public-infrastructure control.

### 16.6 Acceptance criteria

- [ ] Every public claim maps to a dataset, metric, scenario artifact, or system proof.
- [ ] Every limitation is visible and accurate.
- [ ] Demo can be repeated consistently.
- [ ] Figures/tables are sourced and reproducible.
- [ ] Evaluation does not selectively hide baseline/negative/mixed results.

---

## 17. D-13: Optional 3D presentation package

### 17.1 Objective

Add immersive spatial visualization only after the required 2D operational workflow is complete.

### 17.2 Required artifacts if approved

- [ ] CesiumJS integration or documented chosen 3D renderer.
- [ ] Same backend/API contracts as 2D view.
- [ ] Custom overlays for roads, assets, traffic, sensors, forecasts, and scenarios.
- [ ] `SIMULATION` label for moving simulated vehicles/scenario overlays.
- [ ] Fallback 2D path remains complete.
- [ ] If Google tiles are used: billing/key/attribution/policy compliance documentation.

### 17.3 Acceptance criteria

- [ ] 3D does not replace or break required 2D workflow.
- [ ] 3D adds decision/presentation value beyond decoration.
- [ ] No Google/third-party tile geometry is extracted for storage/training.
- [ ] Visual overlays show provenance correctly.

---

## 18. D-14: Optional interoperability and advanced research package

### 18.1 Possible deliverables

| Extension | Required proof if attempted |
|---|---|
| FIWARE/Orion-LD adapter | Canonical entity synchronization and interoperability demo |
| Eclipse Ditto | Device/twin state/policy use case with documented benefit |
| Conformal prediction | Coverage/width evaluation and calibrated interval report |
| Isolation Forest | Data sufficiency, anomaly evaluation, false-positive analysis |
| EnergyPlus | Building assumptions, model files, validation/limitations |
| STGNN/GNN | Benchmark comparison, topology/data justification, reproducible run |
| Local aggregate field counts | Collection protocol, aggregate-only privacy approach, validation use |
| Local aggregate meter data | Permission, data governance, source caveat, model comparison |

### 18.2 Rule

No optional extension may be presented as completed unless it has the same evidence standard as required MVP deliverables.

---

## 19. Definition of done by capability

| Capability | Done only when |
|---|---|
| Data source | Manifest, license, classification, validation, sample, provenance UI behavior exist |
| Backend endpoint | Contract, auth behavior, tests, error behavior, documentation exist |
| Map layer | Data source, legend, interaction, provenance, accessibility fallback exist |
| Model | Baseline, chronological evaluation, artifact, metrics, model card, inference path exist |
| Scenario | Inputs, seed, network/demand version, baseline/intervention, KPIs, artifacts, UI result exist |
| Recommendation | Rule, evidence, provenance, human-approval wording, review state exist |
| UI screen | Loading/empty/error states, desktop behavior, provenance, acceptance check exist |
| Deployment | Compose, env docs, health, tests, runbook, recovery behavior exist |
| Research claim | Dataset/metric/artifact supports it and limitation is documented |

---

## 20. Evidence storage convention

Store evidence in predictable locations.

```text
artifacts/
  models/
  scenarios/
  reports/
  screenshots/
  exports/

docs/
  diagrams/
  reports/
  decisions/

data/
  manifests/
  samples/
```

Suggested naming convention:

```text
{domain}_{artifact-type}_{version-or-date}.{extension}

Examples:
traffic_model_card_v1.md
scenario_signal_timing_run_001.json
report_latency_2026-09-19.md
screenshot_operations_replay_v1.png
```

Every evidence artifact should be traceable to:

- source data/model/scenario version;
- timestamp;
- author/agent where appropriate;
- relevant issue/PR/decision record.

---

## 21. Final MVP delivery checklist

### Platform foundation

- [ ] Repository/documentation/reference setup complete.
- [ ] Docker Compose starts core services.
- [ ] Study-area GIS package complete.
- [ ] Dataset/provenance package complete.

### Digital twin core

- [ ] Canonical schemas and database migrations complete.
- [ ] MQTT ingestion/validation works.
- [ ] Current/history/forecast/scenario state separation proven.
- [ ] APIs/WebSockets work.

### User experience

- [ ] Operations map works.
- [ ] Entity inspection works.
- [ ] Provenance/freshness/quality are visible.
- [ ] Traffic/energy analytics views work.
- [ ] Scenario Studio works.
- [ ] Recommendations view works.

### Intelligence and simulation

- [ ] SUMO baseline/intervention runs work.
- [ ] Traffic baseline/XGBoost model works.
- [ ] Energy baseline/XGBoost model works.
- [ ] Forecasts and evidence reach UI.
- [ ] Advisory recommendation works.

### Quality and research

- [ ] Tests and health checks work.
- [ ] Evaluation experiments complete.
- [ ] Demo script works from clean setup.
- [ ] Limitations are included in all final materials.
- [ ] No unsupported claims remain.

---

## 22. Final delivery statement

> The pilot is complete when it provides a reproducible, evidence-backed workflow in which authorized users can view a corridor-scale urban twin, understand the provenance and quality of data, inspect traffic and energy forecasts, run a clearly labeled simulated intervention, compare baseline and intervention KPIs, and review an advisory recommendation that requires human approval. Completion is demonstrated through working software, versioned artifacts, recorded metrics, explicit limitations, and a repeatable demo—not through visual polish or unsupported claims alone.
