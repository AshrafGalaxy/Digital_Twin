# Product Requirements Document (PRD)
## Digital Twin-Enabled Smart City Analytics Platform

> **Status:** Baseline MVP Product Specification  
> **Pilot Corridor:** Viman Nagar Chowk (Phoenix Marketcity) ↔ Somnath Nagar Chowk, Nagar Road, Pune, Maharashtra  
> **Product Archetype:** AI-Enabled Urban Digital Twin & Municipal Decision-Support Platform  
> **Primary Stakeholders:** Municipal Corporations (PMC), Traffic Police, Urban Planners, Infrastructure SPVs

---

## 1. Product Summary & Vision

The Digital Twin-Enabled Smart City Analytics Platform integrates real-time/replayed sensor observations, spatial infrastructure assets, machine learning forecasts, and micro-simulation into a unified decision-support platform for municipal authorities.

The platform enables authorized public officials to:
1. **Observe** authoritative corridor conditions across mobility, energy, and environment.
2. **Forecast** near-future traffic speeds (15m ahead) and commercial energy demands (60m ahead).
3. **Simulate** proposed signal and mobility interventions in Eclipse SUMO before field deployment.
4. **Compare** baseline vs intervention KPIs (travel time, queue length, delay reduction).
5. **Review** transparent, rule-based advisory recommendations requiring human approval.

---

## 2. Pilot Corridor Scope & Non-Goals

### 2.1 Included in MVP
- **Spatial Boundary:** 1.8 km arterial corridor on Pune-Ahmednagar highway (Nagar Road).
- **Intersections:** 2 key signalized junctions (`INT-VN-01` Viman Nagar Chowk, `INT-SN-01` Somnath Nagar Chowk).
- **Road Segments:** 10 directed arterial segments and immediate approach links.
- **Energy Entity:** Phoenix Marketcity commercial retail facility (`BLD-PHOENIX-01`).
- **Telemetry Modes:** `REPLAY` (historical corridor data) and `SIMULATION` (SUMO feeds).

### 2.2 Explicit Non-Goals & Prohibitions
- **Physical Actuation:** Zero direct control of traffic signal controllers, utility switches, or municipal hardware.
- **PII & Surveillance:** Zero CCTV/video ingestion, facial recognition, ANPR license plate tracking, or individual vehicle GPS traces.
- **Autonomous Control:** The platform never executes decisions automatically; all actions require human verification.

---

## 3. Functional Requirements Matrix (FR-01 to FR-10)

| Requirement ID | Feature Title | Input Data | System Behavior | Output / Deliverable |
|:---:|---|---|---|---|
| **FR-01** | Urban Asset Catalog | OSM GeoJSON, asset metadata | Normalizes spatial assets into NGSI-LD-aligned entities. | Canonical road segment, intersection, and building entities. |
| **FR-02** | Ingestion & Quarantine | MQTT telemetry streams | Validates schemas, physical bounds, and timestamps; isolates invalid events in DLQ. | Verified observation records or `quarantine_observations` log. |
| **FR-03** | Multi-Storage State Store | Validated observations | Persists time-series to hypertables; updates `entity_current_state` with timestamp guards. | Authoritative current state API (`/api/v1/state/current`). |
| **FR-04** | 15m Traffic Forecasting | Speed lags, temporal features | XGBoost regressor predicts speed 15m ahead; calculates conformal 80%/90% bands and SHAP attributions. | Predicted speed, confidence margins, and top-5 contributing features. |
| **FR-05** | 60m Energy Forecasting | Power lags, calendar features | XGBoost regressor predicts active power 60m ahead; triggers peak alerts if > 4,800 kW. | Predicted power (kW), confidence bounds, and peak load warnings. |
| **FR-06** | Scenario Micro-simulation | Scenario parameter overrides | SUMO runs comparative micro-simulation; calculates travel time, delay, and queue deltas. | Side-by-side KPI comparison card (`SCEN-BASE-01` vs `SCEN-INT-01`). |
| **FR-07** | Advisory Rule Engine | State metrics, forecasts, rules | Evaluates deterministic congestion/energy rules; requires human authorization. | Structured advisory recommendations with evidence links and audit trail. |
| **FR-08** | Operations Dashboard | WebSocket stream, REST APIs | Renders 2D MapLibre vector map, speed-coded segments, metric drawer, and dual themes. | Responsive desktop/tablet civic operations interface. |
| **FR-09** | Quality & Drift Monitoring | Raw observation streams | Evaluates Population Stability Index (PSI) and Kolmogorov-Smirnov tests on features. | Real-time drift status API (`/api/v1/analytics/drift`) and data quality metrics. |
| **FR-10** | Continuous Rollups | Ingested hypertable data | Automatically aggregates raw 5s/1m observations into 15m analytical metrics. | Continuous 15m rollups table (`traffic_15m_aggregates`). |

---

## 4. Non-Functional Requirements (NFR-01 to NFR-06)

| NFR ID | Category | Metric / Specification |
|:---:|---|---|
| **NFR-01** | **Latency** | REST API p95 response time < 150 ms; WebSocket state broadcast latency < 500 ms. |
| **NFR-02** | **Resilience** | Zero-downtime persistence failover from PostgreSQL to local SQLite engine if database is unreachable. |
| **NFR-03** | **Data Honesty** | 100% of displayed metrics must include explicit provenance badges (`LIVE`, `REPLAY`, `SIMULATION`, `PREDICTED`). |
| **NFR-04** | **Privacy** | Zero storage of personally identifiable information (PII) or unaggregated vehicle traces. |
| **NFR-05** | **Accessibility** | Strict adherence to WCAG 2.2 AA (text contrast $\ge 4.5:1$, visible focus rings, zero text $< 12$px). |
| **NFR-06** | **Modularity** | Decoupled architecture deployed via standard Docker Compose with independent container scaling. |

---

## 5. Acceptance Criteria

The MVP release is accepted when:
1. All 10 functional requirements (FR-01 to FR-10) pass automated contract and integration tests.
2. The operations dashboard displays live/replayed traffic and energy metrics with verified provenance badges.
3. SUMO baseline vs intervention comparative KPI runs complete successfully with reproducible deltas.
4. XGBoost models outperform persistence baselines on the holdout test set with conformal uncertainty bounds.
5. All 91 automated tests pass cleanly with 0 failures and 0 errors.
