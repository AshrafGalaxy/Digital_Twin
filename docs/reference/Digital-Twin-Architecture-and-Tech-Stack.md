# Digital Twin-Enabled Smart City Analytics — Architecture & Technology Decision Report

*Scope: one-semester prototype for a limited area (campus / corridor / district in Pune), extensible to a full academic-year build. Confidence levels and sources are marked throughout. Where public evidence is absent, this is stated explicitly rather than estimated.*

---

## Executive recommendation

| Layer | Choice (Semester MVP) |
|---|---|
| Frontend | React + Vite, MapLibre GL JS |
| 2D map | MapLibre GL JS + OpenStreetMap/OSM tiles |
| 3D | None in prototype (see justification) |
| Backend | Python, FastAPI (modular monolith) |
| Real-time transport | MQTT (Eclipse Mosquitto) → WebSockets to frontend |
| Database | **One** PostgreSQL instance with **TimescaleDB + PostGIS** extensions |
| Context/twin model | Custom JSON entities modeled on **NGSI-LD / FIWARE Smart Data Models** vocabulary (no full context broker running yet) |
| Object storage | Local filesystem / MinIO (single container) |
| Traffic model | Baseline: historical average → **XGBoost/LightGBM** tabular model |
| Energy model | Baseline: persistence → **XGBoost/LightGBM** |
| Environment model | Rule-based thresholds + Isolation Forest for anomalies |
| Simulation | **SUMO + TraCI** (traffic), simple Python energy approximation |
| Deployment | Docker Compose on a laptop / single cheap VM |
| MLOps | Git + MLflow (local) |

**Central architectural decision:** collapse the layer count. Requirements analysis (below) shows that for a one-semester, single-area prototype, the "one database per data type" pattern used by production smart-city platforms (relational + time-series + geospatial + graph + object store, often 4–5 separate systems) is unjustified complexity. **PostgreSQL with the TimescaleDB and PostGIS extensions in a single instance** covers relational, time-series, and geospatial needs together, supports SQL joins across all three, and is confirmed by current (2026) comparative benchmarking to hold its own against purpose-built time-series stores for the query complexity this project needs — while eliminating a second/third database to operate, back up, and secure.<br>*(Confidence: high for the database decision at this scale; medium for downstream ML model choices, which depend on data actually collected — see Data strategy.)*

The second central decision is **no dedicated context broker (FIWARE Orion-LD, Eclipse Ditto) and no message-broker-plus-stream-processor pair (Kafka+Flink) in the MVP.** These are real, well-evidenced technologies used by production platforms (see competitor analysis), but at the sensor/message volumes a semester prototype will actually see (tens to low hundreds of messages/sec, not thousands), MQTT → a FastAPI ingestion service → Postgres is sufficient and removes two entire operational subsystems. The **data model** (NGSI-LD-style entities) is adopted now, even without the broker, so migrating to Orion-LD or Ditto later is a schema-compatible upgrade, not a rewrite.

---

## Problem and scope

**Problems being solved in the prototype:**
- Data fragmentation across a small set of real/simulated sources is unified into one canonical schema (problem 1, 7, 8).
- A synchronized twin state (not just a dashboard) is maintained for a defined set of entities: roads/intersections, one or two buildings/meters, optionally one environmental sensor (problem 2).
- Short-horizon forecasting (traffic speed/volume, energy load) replaces pure description (problem 3, 4).
- A what-if simulation loop (SUMO scenario compare) lets a user test one intervention (e.g., signal timing change) before any real-world action (problem 5).
- Explainability is provided via feature importance (SHAP or model-native) rather than opaque predictions (problem 10).

**Explicitly out of scope for the semester prototype:** city-wide coverage, CCTV/video analytics, multi-agency data governance, real actuation of physical infrastructure, blockchain provenance, federated learning, LLM/agentic interfaces, Kubernetes, and any claim of production readiness.

**What "digital twin" means here (and what is actually implemented):**

| Digital-twin capability | Implemented in prototype? |
|---|---|
| Physical entities (roads, intersections, one building) | Yes — a fixed, small registry |
| Digital entities (JSON representations) | Yes |
| Relationships (road→intersection, meter→building) | Yes, as foreign keys / entity references |
| Current state | Yes — latest reading per entity in Postgres |
| Historical state | Yes — TimescaleDB hypertable |
| Desired/target state | No — no control setpoints in MVP |
| Behavioral/simulation model | Yes — SUMO for traffic only |
| Synchronization mechanism | Polling/MQTT push at a fixed interval (see real-time architecture) |
| Event/command model | Read-only; no command channel to physical devices |
| Feedback loop to the physical asset | No — recommendation is displayed to a human, never auto-applied |
| Confidence/uncertainty on predictions | Partial — prediction intervals for the traffic/energy model |
| Human approval before any action | Yes, by design (no actuation exists) |

A dashboard with static maps and stored logs would **not** qualify as a digital twin under this definition — the differentiator here is the maintained entity state plus the simulation loop, however small.

---

## Competitor technology analysis

Public evidence quality is uneven across these projects — degrees of disclosure vary and figures below are only included where a primary source states them.

| Platform | Type | Core tech | Standards used | Digital twin depth | Open source? | Public evidence |
|---|---|---|---|---|---|---|
| **FIWARE / Orion-LD + Smart Data Models** | Framework/middleware | Context Broker (Orion-LD), NGSI-LD | NGSI-LD, JSON-LD, Smart Data Models | Entities carry reported/current context state; broker is the twin's live-state store | Yes | Documentation and academic use (e.g., marine/coastal digital twin, smart-farm tutorials) are well documented; deployment scale per city not disclosed here |
| **Snap4City / DISIT Lab (Univ. of Florence)** | Platform | Km4City ontology, own middleware, FIWARE-compatible, 70+ protocol adapters claimed | Km4City ontology, NGSI, GDPR-compliant claim | Dashboards + KPI computation + what-if analysis modules described | Yes, "100% open source" per own materials | Vendor/developer-authored sources (DISIT, own papers); independent third-party verification of deployment scale not found in this search — treat scale claims as **vendor-stated, not independently audited** |
| **Eclipse Ditto** | Open-source DT middleware | Java/Akka, HTTP/WebSocket/AMQP/MQTT/Kafka connectors | W3C Web of Things (TD/TM) integration | Explicit reported-vs-desired-vs-current state model; policy-based per-twin access control | Yes (Eclipse Foundation) | Adopted by Bosch, Siemens, SAP, Deutsche Telekom, Vodafone per Eclipse Foundation-published adopter list; active release cadence through 2025–2026 confirmed on the project's own governance page |
| **Azure Digital Twins (DTDL)** | Managed cloud service | DTDL (JSON-LD/RDF-based twin modeling language), Azure IoT Hub integration | DTDL v2, open to community | Full twin graph with relationships, used to model interfaces/entities | No (proprietary Microsoft service; DTDL spec itself is open) | Enterprise adoption widely documented; targets customers already invested in Azure |
| **Bentley iTwin** | Commercial platform | iTwin.js, IoT connectors | IFC/BIM-adjacent | 3D/visualization-centric; can integrate with Ditto for backend twin state and Azure/DTDL | Partially (iTwin.js core is open) | Integration patterns (iTwin + Ditto, iTwin + Azure/DTDL) documented in academic surveys of open-source DT frameworks |
| **Eclipse SUMO** | Open-source simulator, not a twin platform | Microscopic traffic simulation, TraCI API | — | Used *as the behavioral-model component* inside many published digital-twin traffic prototypes (bidirectional Python control via TraCI) | Yes | Extensively documented, active PyPI packages (`traci`, `sumolib`, `libsumo`), used in multiple 2025–2026 peer-reviewed digital-twin traffic-signal studies |
| **OGC CityGML / CityJSON / 3D Tiles / SensorThings API** | Open standards, not platforms | Geospatial/3D city model exchange formats; SensorThings for IoT observations | OGC standards | Provide *data exchange*, not twin state management by themselves | Standards are open; tooling varies | Standards bodies are the authoritative source; adoption depends on tooling chosen (Cesium, QGIS, etc.) |
| **Virtual Singapore / Helsinki 3D (Kalasatama)** | Municipal 3D digital-twin programs | City-scale 3D + GIS platforms, national government-funded | CityGML-family in Helsinki's case (documented in municipal literature) | High visual fidelity; degree of live IoT synchronization vs. static 3D model is not independently disclosed in this search | Not open source | Government/municipal-published sources; **do not assume live sensor synchronization matches the visual fidelity** — many public city "digital twins" are strong on 3D visualization and comparatively thin on live state sync (a documented critique in the DT literature) |
| **Cityzenith SmartWorldOS** | Commercial product | Proprietary 3D twin OS | — | Vendor marketing describes decision-support and carbon-analytics features | No | Vendor-sourced; independent, quantified deployment evidence not found in this search — **treat as vendor claim** |

**Lessons for this project:**
- Adopt the **NGSI-LD/Smart Data Models vocabulary** (entity types, attribute naming) even without running Orion-LD, so migration is possible later — this is the single highest-leverage, lowest-cost decision from the competitor review.
- Learn from Eclipse Ditto's explicit **reported vs. desired vs. current state** distinction — copy that state model even in the simple Postgres schema.
- Learn from SUMO+TraCI's proven pattern (Python control loop around a running simulation) rather than inventing a custom traffic simulator.
- **Avoid** conflating a 3D visualization layer with an actual synchronized twin — several municipal projects show that gap; this project should be explicit that it is not doing 3D unless it earns its place (see Geospatial section).
- **Avoid** claiming interoperability across "70+ protocols" or similar broad vendor language without evidence — state exactly which protocols are implemented (MQTT, HTTP/REST) and nothing more.

---

## Architecture decision

**Logical data flow (text-based, since correctness matters more than diagram rendering):**

1. **Source** — simulation generator, CSV replay, or a real API/sensor (mode-selectable, see Data strategy).
2. **Ingestion gateway** — a small FastAPI/Python service subscribes to MQTT topics (simulation and, if used, real sensors publish here) or polls external APIs on a schedule.
3. **Validation** — a lightweight function layer checks schema, ranges, and timestamps; invalid records are logged with a data-quality flag, not silently dropped.
4. **Canonical transform** — raw payload → canonical entity JSON (NGSI-LD-style attributes).
5. **Storage** — canonical record written to a Postgres/TimescaleDB hypertable (`observations`) and the "current state" row is upserted in a `entities_current` table (PostGIS geometry column where spatial).
6. **Feature generation** — a scheduled job (every N minutes) computes rolling features (last hour average speed, etc.) from TimescaleDB continuous aggregates.
7. **Inference** — the trained XGBoost/LightGBM model is loaded in a small inference service; batch inference runs on the schedule, online inference serves the dashboard's "next 15/30/60 min" request.
8. **Twin update** — prediction + confidence written back to `entities_current` as a `forecast` attribute, keeping current/historical/predicted state cleanly separated.
9. **Alerting/recommendation** — rule engine compares forecast to thresholds; if breached, a recommendation record is created (e.g., "reroute suggested for corridor X").
10. **Dashboard** — React frontend polls REST/WebSocket for current state, forecast, and recommendations; renders on MapLibre.
11. **Simulation loop (what-if)** — user selects a scenario in the dashboard → backend launches a SUMO run via TraCI with the intervention parameters → KPIs (average travel time, queue length) are compared against a baseline run → result stored and shown alongside the live twin, clearly labeled as *simulated*, never overwriting live state.

**Simulation / Replay / Live modes** — all three converge on the same canonical entity schema before storage, so nothing downstream (validation, storage, features, models, dashboard) needs to know which mode produced a record:
- *Simulation mode*: a Python generator produces synthetic MQTT messages using SUMO output (traffic) and a simple daily-load-curve function (energy), with a fixed random seed for repeatability.
- *Replay mode*: a script reads a historical CSV/API dump and republishes it to the same MQTT topics at accelerated or real-time pace, timestamped as if live.
- *Live mode*: the same ingestion gateway subscribes to a real MQTT broker feed or polls a real API; it must additionally handle missing data, rate limits, and schema drift.

The only difference between modes is **which process publishes to MQTT** — everything from step 3 onward is identical. This is what "same canonical model, same downstream pipeline" means concretely, and it is why the project remains demonstrable even if no real sensors are ever connected.

---

## Technology decision matrix (key layers)

| Layer | Candidates | Decision | Why | Confidence |
|---|---|---|---|---|
| Messaging | MQTT (Mosquitto) / Kafka / Redis Streams / NATS | **MQTT** | Lightweight, standard for IoT, trivial to run in Docker, matches SUMO/sensor-simulation patterns already used in published research; Kafka's ordering/partitioning guarantees are unneeded at this message volume | High |
| Context/twin state | Orion-LD / Eclipse Ditto / custom Postgres table | **Custom Postgres table, NGSI-LD-shaped JSON** | Running a full context broker is one more service to operate for no volume benefit yet; the *data model* is what carries forward, not the broker binary | High |
| Time-series + geo store | InfluxDB / TimescaleDB+PostGIS / MongoDB / separate Influx+Postgres | **TimescaleDB + PostGIS in one Postgres** | 2026 comparative benchmarks show TimescaleDB matches or beats InfluxDB on complex queries (joins, geospatial, window functions) that a digital twin needs, while InfluxDB is faster only on simple single-metric rollups this project doesn't require; one database also means one backup/security surface | High |
| Graph relationships | Neo4j / relational foreign keys | **Relational foreign keys** | The entity relationship graph (road→intersection→district) is shallow and static enough that a graph database adds operational cost without enabling any query the prototype needs | Medium |
| Frontend map | Cesium (3D) / MapLibre (2D) / deck.gl | **MapLibre (2D)** | No requirement in this prototype needs 3D volumetric or terrain reasoning; 2D is faster to build, lighter to run on a laptop, and avoids the "3D as expensive distraction" failure mode seen in some municipal twins | High |
| Traffic simulator | SUMO / CityFlow / MATSim / CARLA | **SUMO (TraCI)** | Most mature open-source option with a proven Python control pattern for exactly this style of prototype; CARLA is 3D-driving-focused and far heavier than needed; MATSim suits large-scale agent-based regional modeling, not a corridor-scale semester project | High |
| Traffic model | Persistence baseline / XGBoost / LSTM / STGNN | **XGBoost/LightGBM as the primary model, persistence as baseline** | Tabular gradient boosting is the documented strong practical choice before deep sequence models; an LSTM or graph neural network requires more data and tuning time than a semester affords and is unlikely to outperform a well-featured XGBoost model at this data volume | Medium (depends on actual dataset size once real/simulated data is generated) |
| Energy model | Persistence / XGBoost / LSTM | **XGBoost/LightGBM** | Same reasoning as traffic; also easier to explain (feature importance) than a neural sequence model, satisfying the explainability requirement | Medium |
| Anomaly detection (environment) | Threshold rules / Isolation Forest / Autoencoder | **Threshold rules first, Isolation Forest as an enhancement** | With one or two environmental sensors and a short data-collection window, a learned anomaly detector cannot be validated meaningfully; thresholds are transparent and immediately usable | High |
| Deployment | Docker Compose / Kubernetes | **Docker Compose** | Single-node laptop/VM deployment; Kubernetes adds orchestration complexity with no scaling requirement this semester | High |
| MLOps | MLflow / DVC / Weights & Biases | **MLflow (local) + Git** | MLflow's local tracking server is enough to log experiments/metrics for the evaluation chapter; DVC adds value mainly once dataset versions multiply, which is a year-2 concern | Medium |

---

## Data strategy

| Source | Availability/cost | Suitable for training? | Suitable for live inference? | Use in prototype? |
|---|---|---|---|---|
| SUMO simulation output | Free, unlimited, repeatable | Yes | Yes (as the "live" feed in simulation mode) | **Yes — primary source** |
| OpenStreetMap road network | Free, open license (ODbL) | N/A (structural) | Yes | **Yes** — road geometry backbone |
| Public traffic/transport APIs (city or Google/OSM-derived) | Variable; often rate-limited, terms-of-service dependent, not guaranteed stable | Limited (short history) | Only if terms allow polling | Optional, replay mode only, with explicit ToS check |
| Weather API | Usually free tier available; rate-limited | Yes (as a feature) | Yes | **Yes** — cheap, reliable feature source |
| Smart-meter/building energy data | Rare for students; may require permission from campus facilities | If obtained: yes | If obtained: yes | **Conditional** — ask campus facilities office for one building's meter export; otherwise simulate a load curve |
| Air-quality API | Often free tier, coarse spatial resolution | Yes | Yes | Optional, secondary domain |
| CCTV/video | Out of scope — high privacy risk, heavy compute | No | No | **Excluded** |
| Synthetic/generator data | Free, unlimited | Yes, for structure/pipeline testing — **not a substitute for real-world validity** | Yes (simulation mode only) | **Yes**, clearly labeled as synthetic in every report |

**Canonical data model decision:** JSON entities shaped like **NGSI-LD/Smart Data Models** (id, type, attributes with `value`/`observedAt`, `location` as GeoJSON), stored as JSONB + generated columns in Postgres, not a running NGSI-LD broker. Migration path: if the project needs multi-party interoperability later, this JSON is already broker-ingestible with Orion-LD with minimal transformation, because the attribute shape matches.

Example objects (abbreviated):

```json
{
  "id": "urn:ngsi-ld:TrafficFlowObserved:corridor1-seg3",
  "type": "TrafficFlowObserved",
  "dateObserved": "2026-09-16T09:15:00Z",
  "averageVehicleSpeed": {"value": 21.4, "unitCode": "KMH"},
  "vehicleCount": {"value": 87},
  "congestionIndex": {"value": 0.62},
  "location": {"type": "LineString", "coordinates": [[79.08,21.15],[79.083,21.152]]},
  "dataQuality": {"value": 0.95},
  "provenance": {"value": "simulation:sumo-run-2026-09-16T09"}
}
```

```json
{
  "id": "urn:ngsi-ld:EnergyMeter:building1-main",
  "type": "EnergyConsumptionObserved",
  "dateObserved": "2026-09-16T09:15:00Z",
  "kWhConsumed": {"value": 12.7},
  "buildingId": {"value": "building1"},
  "provenance": {"value": "replay:campus-meter-2025"}
}
```

```json
{
  "id": "urn:ngsi-ld:RoadSegment:corridor1-seg3",
  "type": "RoadSegment",
  "laneCount": {"value": 2},
  "capacityVehPerHour": {"value": 900},
  "geometry": {"type": "LineString", "coordinates": [[79.08,21.15],[79.083,21.152]]}
}
```

```json
{
  "id": "urn:ngsi-ld:Prediction:corridor1-seg3-2026-09-16T09:30",
  "type": "TrafficPrediction",
  "targetEntity": {"value": "urn:ngsi-ld:TrafficFlowObserved:corridor1-seg3"},
  "horizonMinutes": {"value": 15},
  "predictedCongestionIndex": {"value": 0.71},
  "confidenceInterval": {"value": [0.63, 0.79]},
  "modelVersion": {"value": "xgb-traffic-v0.3"}
}
```

```json
{
  "id": "urn:ngsi-ld:Intervention:corridor1-reroute-01",
  "type": "RecommendedIntervention",
  "targetEntity": {"value": "urn:ngsi-ld:RoadSegment:corridor1-seg3"},
  "action": {"value": "suggest_alternate_route"},
  "basedOnPrediction": {"value": "urn:ngsi-ld:Prediction:corridor1-seg3-2026-09-16T09:30"},
  "requiresHumanApproval": {"value": true}
}
```

---

## AI/ML model selection

For every domain: **baseline → selected model → advanced alternative not yet used**.

**Traffic**
- Target: congestion index / average speed, 15-minute horizon.
- Inputs: historical speed/count (lagged), time of day, day of week, weather.
- Baseline: persistence (last observed value).
- Selected: **XGBoost/LightGBM regressor** — interpretable via feature importance, trains in seconds on a laptop, robust to missing values.
- Advanced (not yet used): Spatio-Temporal Graph Neural Network — genuinely justified only once multiple interconnected segments with real topology and enough historical volume exist; premature now given the small entity count.
- Evaluation: MAE, RMSE, and comparison against the persistence baseline (never accuracy alone).
- Deployment: batch inference every 5 minutes; online inference for dashboard on-demand queries.

**Energy**
- Target: building-level kWh, 60-minute horizon.
- Inputs: historical load, temperature/weather, time features.
- Baseline: persistence/daily-average.
- Selected: **XGBoost/LightGBM**.
- Advanced (not yet used): physics-informed model tied to building thermal characteristics — requires building metadata not available this semester.
- Explainability: SHAP values on the trained model.

**Environment**
- Rule-based thresholds against known AQI/weather bands are sufficient for the prototype; **do not add a learned anomaly model** until enough sensor-months of data exist to validate false-positive rate. Isolation Forest is the documented next step, not the day-one choice.

**Decision support**
- Rule-based recommendation (if predicted congestion/energy exceeds threshold → suggest action) for the semester prototype. **Do not use an LLM or agentic layer here** — it would not improve correctness and would obscure the explainability requirement (Selection principle 18).

---

## Simulation and digital twin

- **Traffic simulator: SUMO**, controlled via the Python `traci` package, following the same pattern documented in multiple 2025–2026 peer-reviewed digital-twin traffic studies (Python control loop step-querying the simulation for vehicle counts/speeds/queues).
- **Energy "simulator": a lightweight Python load-curve generator**, not a full EnergyPlus/Modelica model — those tools require building geometry and mechanical-system detail unavailable this semester; EnergyPlus is the recommended future-scale option once real building data exists.
- **Environmental model:** none simulated beyond simple noise-perturbed weather-linked curves.
- **Scenario manager / what-if workflow:** load scenario parameters → run baseline SUMO simulation → run intervention SUMO simulation with the same random seed → compute KPI deltas (average travel time, queue length) → store both runs and the delta for reproducibility → display comparison on dashboard, explicitly labeled as simulated output, not live measurement.

---

## Deployment and operations

- **Local development:** Docker Compose (Postgres/TimescaleDB/PostGIS, Mosquitto, FastAPI backend, React frontend, SUMO container) — runs entirely on an ordinary laptop.
- **Demo/research deployment:** the same Compose stack on one low-cost cloud VM (2–4 vCPU is enough at this scale).
- **Security baseline appropriate to this scope:** HTTPS on the API, a single application-level auth token or basic JWT auth for the dashboard, MQTT broker with username/password auth (TLS if any real device is ever connected), no CCTV/PII ingestion at all so most of the heavier governance requirements (consent, anonymization pipelines) don't apply yet — documented explicitly as a scope boundary, not solved.
- **Observability:** container logs + a simple `/health` endpoint; a full Prometheus/Grafana stack is a research-grade addition, not required for the MVP.
- **CI/CD:** GitHub Actions running lint + unit tests on push; no deployment automation needed for a single-VM demo.

---

## Bottleneck and capacity assessment

*All figures below are estimates for a semester-scale deployment, not measurements.*

Assumptions: ~10–30 simulated/real entities, messages every 5–15 seconds per entity → **roughly 1–6 messages/second** at peak, message size a few hundred bytes of JSON, 3–6 months retention, forecast recomputed every 5 minutes, 1–5 concurrent dashboard users, a handful of scenario simulations per day.

At this scale: MQTT and a single Postgres instance are not remotely close to their throughput ceilings (Postgres comfortably handles thousands of writes/sec; MQTT brokers handle far more than a handful of messages/sec). The realistic bottleneck is **SUMO simulation wall-clock time** for larger networks/longer horizons, and **frontend map rendering** if the entity count or historical-trail length grows carelessly. Mitigation: cap the simulated network size to the chosen corridor/campus, and downsample historical series for chart rendering rather than sending every raw point to the browser.

---

## Evaluation and research contribution

**Meaningful for a student prototype:** MAE/RMSE against the persistence baseline for traffic and energy, end-to-end latency from ingestion to dashboard update, data completeness rate, and a small ablation (with vs. without weather feature). **Not meaningful/unnecessary at this scale:** p99 latency under load, multi-tenant throughput testing, or city-scale user studies — these belong to a production evaluation, not this semester's.

**Novelty ranking (highest to lowest realistic contribution for a student project):**

| Candidate contribution | Novelty potential | Difficulty | Warning |
|---|---|---|---|
| India-specific / resource-constrained-city architecture design (small footprint, no context broker, single-database pattern) | Medium | Low–Medium | Genuinely under-explored relative to the "full FIWARE stack" pattern in most published smart-city architectures |
| Multi-domain (traffic+energy) twin sharing one canonical schema and one database | Medium | Medium | Reasonable contribution if evaluated rigorously; not novel as a bare combination — the evaluation methodology is where the contribution lives |
| Explainable, uncertainty-aware short-horizon forecasting with a transparent baseline comparison | Medium | Low | Solid, defensible, unglamorous — a fine anchor for a report/paper |
| LLM/agentic interface | Low as a research contribution | High | **Warn explicitly:** adding an LLM chat layer on top of this system is common now and would not by itself support a novelty claim; do not add one "to look advanced" |
| Blockchain provenance | Very low here | High | No clearly defined multi-party trust problem in a single-institution prototype — do not add |
| Federated learning | Low for this scope | High | No multi-site data-holder scenario exists yet |

Any patent-potential discussion requires an actual patent attorney and prior-art search — nothing above should be read as a patentability claim.

---

## Three stack variants

| | Semester MVP | Research-grade | Production-scale |
|---|---|---|---|
| Database | Single Postgres (Timescale+PostGIS) | Same, + read replica, continuous aggregates tuned | Managed Postgres/Timescale cluster + object storage tiering |
| Messaging | MQTT (Mosquitto) | MQTT + basic dead-letter handling | MQTT/Kafka hybrid, at-least-once delivery guarantees |
| Context broker | None (custom table) | Optional Orion-LD sidecar for interoperability demo | Orion-LD or Eclipse Ditto in production |
| Models | XGBoost baseline+model | XGBoost + documented ablations, MLflow tracking | Champion/challenger XGBoost + selectively an LSTM/STGNN if data volume justifies it |
| Simulation | SUMO single scenario | SUMO multi-scenario batch runs, reproducible seeds logged | SUMO/MATSim at scale, scheduled batch simulation service |
| Deployment | Docker Compose, laptop/1 VM | Docker Compose, 1 small VM + CI | Kubernetes only if genuine multi-tenant/multi-region need is demonstrated |
| Excluded | Kafka, K8s, GNNs, LLMs, blockchain | Kafka, K8s, blockchain | Blockchain (unless a real provenance/trust need appears) |

Migration between variants is schema-preserving because the canonical NGSI-LD-style JSON model does not change — only the infrastructure around it does.

---

## Final implementation plan

**Adopt now:** single Postgres+Timescale+PostGIS database; MQTT ingestion; FastAPI modular monolith; NGSI-LD-shaped canonical schema; SUMO+TraCI for traffic simulation; XGBoost/LightGBM as the traffic and energy models; MapLibre 2D dashboard; Docker Compose.

**Postpone:** context broker (Orion-LD/Ditto), Kafka, graph database, 3D visualization, deep learning models (LSTM/GNN), full MLOps stack (DVC/W&B/Evidently).

**Avoid entirely in this project's current scope:** Kubernetes, blockchain, federated learning, LLM/agentic decision layer, CCTV/video ingestion.

**Most serious technical risk:** the simulation-to-real gap — a model trained purely on SUMO output may not transfer to any real data collected later; mitigate by keeping simulation and replay/live pipelines schema-identical and by validating on any real data as soon as it exists, even a small sample.

**Most serious data risk:** no real campus/city data is secured yet; **fallback** is to run entirely in simulation + replay mode and be explicit in every report that no live deployment claim is being made.

**Most serious research risk:** overclaiming novelty for "combining existing open-source tools" — the honest contribution is the resource-constrained architecture and evaluation methodology, not the tool list itself.

**Fallback if model accuracy is weak:** report the persistence-baseline comparison honestly; a small, well-explained improvement over baseline is a valid result — do not chase reported accuracy by adding an unjustified model.

**Fallback if real-time deployment fails:** the replay mode already demonstrates the full pipeline; the dashboard degrades gracefully to "last known + forecast" rather than requiring live infrastructure to be up during a demo.

**First ten implementation tasks:** (1) stand up Docker Compose skeleton (Postgres+Timescale+PostGIS, Mosquitto); (2) define canonical entity schema and JSON examples; (3) build the SUMO scenario for the chosen corridor/campus; (4) build the simulation-mode publisher; (5) build the FastAPI ingestion + validation service; (6) build feature-generation continuous aggregates; (7) train the XGBoost traffic baseline + model; (8) build the MapLibre dashboard showing current state; (9) add the forecast overlay and threshold-based recommendation; (10) build the what-if scenario comparison UI.

**First five experiments:** (1) persistence vs. XGBoost MAE/RMSE on simulated traffic data; (2) ablation with/without weather feature; (3) end-to-end ingestion-to-dashboard latency measurement; (4) data-completeness rate under injected missing-data conditions; (5) SUMO baseline-vs-intervention KPI comparison for one signal-timing change.

**Minimum viable demonstration:** live (simulation-mode) map showing 5–10 road segments with current speed/congestion, a 15-minute forecast overlay beating the persistence baseline, one threshold-triggered recommendation, and one what-if SUMO comparison shown side-by-side with the baseline.

**Full academic-year extension:** add a second real data source (campus meter or public traffic API) in replay mode; add the Orion-LD context broker as an interoperability demonstration; add EnergyPlus-based energy simulation if building data becomes available; write up the evaluation as a short paper, explicit about the resource-constrained architecture as the contribution.

---

### Key sources referenced
- FIWARE / NGSI-LD documentation and tutorials (fiware.org, GitHub FIWARE tutorials, arXiv marine digital-twin paper)
- Snap4City / DISIT Lab platform documentation (snap4city.org, disit.org)
- Eclipse Ditto project documentation and governance page (eclipse.dev/ditto, projects.eclipse.org)
- Azure DTDL documentation (Microsoft opendigitaltwins-dtdl)
- Peer-reviewed comparison of DTDL/AAS/Ditto/NGSI-LD interoperability (PMC)
- SUMO/TraCI documentation and 2025–2026 peer-reviewed traffic digital-twin studies (PMC, MDPI Sensors)
- 2026 TimescaleDB vs. InfluxDB comparative benchmarking (Tiger Data, DB-Engines, independent comparison sites)
