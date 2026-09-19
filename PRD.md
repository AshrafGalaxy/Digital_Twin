# Product Requirements Document (PRD)
## Digital Twin-Enabled Smart City Analytics Platform

> **Document status:** Baseline MVP requirements  
> **Project context:** See `PROJECT_CONTEXT.md`  
> **Pilot study area:** Viman Nagar Chowk (Phoenix Mall) ↔ Somnath Nagar Chowk corridor, Nagar Road, Pune  
> **Product type:** AI-enabled urban digital twin and government decision-support platform  
> **Primary institutional users:** Municipal corporations, Smart City SPVs, Integrated Command and Control Centres, traffic-management agencies, urban planners, infrastructure departments, utilities, and environmental authorities  
> **Pilot focus:** Smart transportation analytics, traffic forecasting/simulation, energy-demand forecasting, environmental context, and explainable decision support  
> **Version:** 2.0

---

## 1. Purpose

This document defines the product requirements for the **Digital Twin-Enabled Smart City Analytics Platform**.

The platform is intended to support **data-driven urban governance**. It combines city assets, geospatial context, real-time/replayed/simulated observations, AI/ML forecasts, what-if simulation, and explainable recommendations into one decision-support workflow.

The initial Pune corridor is a **pilot validation area**. It is not the intended boundary of the product. The pilot is used to validate the architecture, data model, forecasting pipeline, simulation capability, UI/UX, and governance-support workflow before future extension to additional city zones and domains.

This PRD defines:

- The governance problems the platform addresses.
- Product vision, institutional users, beneficiaries, and stakeholders.
- MVP scope, non-goals, user stories, and acceptance criteria.
- Functional and non-functional product requirements.
- Requirements for data provenance, forecasting, simulation, decision support, security, and evaluation.
- The definition of a successful pilot release.

---

## 2. Product summary

The Digital Twin-Enabled Smart City Analytics Platform is a modular, AI-enabled urban digital twin designed for city governments and public agencies to:

1. Observe current urban conditions.
2. Integrate fragmented data from mobility, energy, environment, infrastructure, and external systems.
3. Maintain a digital representation of city assets, relationships, and changing state.
4. Forecast near-future traffic and energy conditions.
5. Simulate interventions before real-world implementation.
6. Compare policy or operational options using measurable KPIs.
7. Generate explainable, human-approved recommendations.
8. Improve transparency, resilience, efficiency, and sustainability of urban services.

The MVP validates these capabilities through a limited Pune pilot focused on mobility, one representative energy entity, environmental context, and scenario-based decision support.

---

## 3. Product vision

> Enable evidence-based urban governance by combining digital twin state, real-time data intelligence, AI forecasting, and simulation into a transparent, interoperable, and human-governed decision-support platform.

The long-term vision is a platform that can represent multiple urban systems—including transportation, energy, environment, water, infrastructure, public safety, land use, and municipal services—while allowing authorized government teams to understand conditions, test alternatives, coordinate decisions, and communicate outcomes.

The product must remain:

- Human-governed rather than autonomously controlling public systems.
- Standards-aware rather than vendor-locked.
- Explainable rather than opaque.
- Modular rather than tied to one city department.
- Privacy-conscious and suitable for responsible public-sector use.
- Usable by non-ML/non-software government stakeholders.

---

## 4. Urban governance problems addressed

| Governance problem | Product response |
|---|---|
| Data is fragmented across municipal departments, sensors, maps, utilities, traffic systems, and external APIs | Normalize data through a canonical urban entity model and shared ingestion pipeline |
| City teams often make decisions from delayed reports or isolated dashboards | Maintain current, historical, predicted, and simulated twin state in one system |
| Traffic congestion is handled reactively rather than predictively | Forecast short-horizon corridor conditions and surface future risk |
| Infrastructure decisions are difficult to test before implementation | Run baseline versus intervention simulations and compare KPIs |
| Departments work in silos | Support a shared view of mobility, energy, environment, assets, and scenario evidence |
| Recommendations from AI may be hard to trust | Use transparent rules, model explanations, confidence/quality context, and human approval |
| Public infrastructure decisions affect citizens but may lack visible evidence | Preserve scenario, data, and recommendation provenance for auditability and communication |
| City platforms can be expensive and complex | Demonstrate a lightweight, modular architecture that can scale only when justified |
| Smart-city demonstrations can confuse simulations with reality | Require visible labels for live, replayed, simulated, and predicted data |

---

## 5. Product scope

### 5.1 Platform scope

The product is designed as a general urban governance and digital-twin platform with future applicability to:

- Smart transportation and public mobility.
- Traffic prediction and optimization.
- Energy-demand forecasting.
- Urban environment monitoring.
- Infrastructure planning and maintenance.
- Emergency-response planning.
- Water, waste, and utility monitoring.
- Climate resilience and sustainability planning.
- AI-driven decision support across city departments.

### 5.2 Pilot scope

The initial pilot implements a constrained but complete workflow:

- **Pilot geography:** Viman Nagar Chowk ↔ Somnath Nagar Chowk corridor, Pune.
- **Mobility:** road segments, intersections, traffic observations, congestion forecast, SUMO scenario evaluation.
- **Energy:** one representative building/zone energy entity using permitted, replayed, benchmark, or synthetic data.
- **Environment:** weather and available AQI/air-quality context.
- **Decision support:** transparent rules based on forecast, data quality, and scenario KPIs.
- **Visualization:** 2D map-centered operations dashboard; optional 3D presentation layer only after core workflow is complete.

### 5.3 Pilot-to-platform distinction

```text
Platform vision:
A multi-domain, government decision-support digital twin for urban governance.

Pilot implementation:
A limited Pune corridor that proves the system’s mobility, energy,
environmental-context, forecasting, simulation, and recommendation workflow.
```

No document, screen, presentation, or paper may imply that the platform is only a Viman Nagar traffic application.

---

## 6. Users, stakeholders, and beneficiaries

### 6.1 Primary institutional users

| User group | Role | Primary platform use |
|---|---|---|
| Municipal corporation / city-governance teams | Coordinate urban services, planning, and policy | Review city/corridor conditions, evidence, forecasts, and intervention outcomes |
| Smart City SPV / ICCC teams | Monitor and coordinate smart-city operations | View state, alerts, data freshness, forecasts, incidents, and recommendations |
| Traffic police / traffic-management agencies | Manage mobility and corridor operations | Monitor congestion, compare turn/signal/routing scenarios, assess traffic impacts |
| Urban planners / transport planners | Plan roads, junctions, mobility, land use, and infrastructure | Test future interventions before physical changes |
| Public works / roads / infrastructure departments | Maintain and improve urban assets | Identify pressure points, closures, maintenance scenarios, and corridor performance |
| Energy / utility departments | Manage demand, service reliability, and efficiency | View load patterns, forecast peaks, assess demand-management options |
| Environment departments | Monitor air quality, weather, climate, and environmental compliance | Review environmental context, threshold alerts, and future extensions |
| Emergency-management teams | Coordinate resilience and incident response | Future use: routing, evacuation, infrastructure-risk and service-disruption scenarios |

### 6.2 Secondary users

| User group | Role |
|---|---|
| Researchers and universities | Validate models, data pipelines, simulations, interoperability, and limitations |
| System administrators / technical teams | Configure sources, models, thresholds, scenarios, access, and platform operations |
| Engineering consultants / infrastructure partners | Use evidence for planning, design, and scenario studies under authorized access |
| Facility/building managers | Provide or interpret building/zone energy data in relevant deployments |

### 6.3 Beneficiaries

| Beneficiary | Expected indirect value |
|---|---|
| Citizens and commuters | Potentially lower delays, safer interventions, more responsive urban services |
| Businesses and logistics operators | Better mobility reliability and infrastructure planning over time |
| Public-service users | More transparent, evidence-based allocation of city resources |
| Municipal workforce | Better coordination and a shared operational picture |
| Environment and public health stakeholders | Better visibility into environmental conditions and future sustainable-planning options |

### 6.4 Academic role

Academic evaluators, faculty, reviewers, and research venues are important for **validation, publication, and evaluation**, but they are not the primary product users. Their needs are addressed through reproducibility, metrics, documented assumptions, and transparent limitations.

---

## 7. Product goals

### 7.1 Governance and operational goals

1. Give authorized public-sector users a unified, spatially grounded view of urban conditions.
2. Enable proactive rather than purely reactive mobility and infrastructure decision-making.
3. Let users test interventions safely in simulation before considering real-world adoption.
4. Make forecasts, recommendations, assumptions, and uncertainty understandable to decision-makers.
5. Preserve evidence and provenance so decisions can be reviewed later.
6. Support future cross-department collaboration through shared entity models and APIs.

### 7.2 Pilot delivery goals

1. Implement a stateful corridor-scale digital twin, not only a map/dashboard.
2. Support simulation and replay through one ingestion/twin pipeline.
3. Train and evaluate traffic and energy forecasts.
4. Run at least one baseline-versus-intervention SUMO simulation.
5. Produce advisory recommendations with linked evidence.
6. Demonstrate data provenance and quality status visibly.
7. Deliver a reproducible Docker-based prototype.
8. Produce evidence suitable for a project report and research-paper draft.

### 7.3 Success principles

The product prioritizes:

- Correctness before visual complexity.
- Measured evidence before claims.
- Human approval before action.
- Interoperability before vendor lock-in.
- Useful small-scale implementation before unproven citywide scope.
- Explainability before autonomous AI behavior.

---

## 8. Non-goals and restrictions

### 8.1 Pilot non-goals

The MVP does not require:

- Citywide Pune coverage.
- Direct access to Pune Smart City ATMS, ICCC, CCTV, or live signal-control systems.
- Autonomous traffic-signal control.
- Direct control of utility, building, energy, water, or emergency systems.
- CCTV/video ingestion, face recognition, vehicle plate recognition, or other PII processing.
- Citizen tracking or individual mobility profiling.
- Full building-physics energy simulation.
- Full 3D city modeling as a core requirement.
- Deep learning, graph neural networks, reinforcement learning, federated learning, blockchain, LLM agents, Kafka, Kubernetes, or a graph database.
- Municipal production-scale SLA/high availability claims.

### 8.2 Safety boundaries

- All recommendations are **advisory**.
- A human authority must review any intervention outside the platform.
- The platform must not send commands to public infrastructure.
- Simulation results must never be shown as measured real-world outcomes.
- No real policy or operations decision should rely solely on MVP output.

### 8.3 Data restrictions

The platform must not ingest:

- CCTV video.
- Facial imagery or biometric data.
- Vehicle registration/number plate data.
- Individual GPS traces.
- Individual energy records.
- Personal travel histories.
- Any sensitive government or citizen data without written authorization, legal review, and appropriate safeguards.

---

## 9. Digital-twin definition

The product must meet the following digital-twin requirements.

| Capability | Required for pilot | Product meaning |
|---|---:|---|
| Physical asset representation | Yes | Roads, junctions, logical sensors, building/zone energy entity, environment station/context |
| Digital entity model | Yes | Structured, persistent, geospatially referenced entities |
| Relationships | Yes | Road-to-junction, sensor-to-road, meter-to-building/zone, scenario-to-run links |
| Current state | Yes | Latest valid source observation |
| Historical state | Yes | Retained time-series observations |
| Predicted state | Yes | Versioned forecast records |
| Simulated state | Yes | Separate SUMO scenario outputs |
| Behavioral model | Yes | SUMO traffic model; energy replay/synthetic behavior model |
| Synchronization | Yes | Ingestion from simulation/replay/optional live modes |
| Scenario analysis | Yes | Baseline vs intervention comparison |
| Explainability | Yes | Model attribution and rule evidence |
| Desired state / physical actuation | No | Future governance-controlled extension only |

A static map, 3D city model, or dashboard without state synchronization, history, forecast, relationships, and simulation does not satisfy the project definition of a digital twin.

---

## 10. User stories

### 10.1 Governance and city-operations users

| ID | User story | Priority |
|---|---|---:|
| US-01 | As a city-governance user, I want to view a shared spatial picture of the pilot area so that I can understand conditions before discussing an intervention. | Must |
| US-02 | As an ICCC/Smart City user, I want to see current state, freshness, alerts, and source provenance so that I know whether information is operationally trustworthy. | Must |
| US-03 | As a traffic-management user, I want to see congestion and predicted traffic conditions by road segment so that I can identify emerging corridor stress. | Must |
| US-04 | As a transport planner, I want to compare a baseline and intervention scenario so that I can evaluate trade-offs before recommending a physical change. | Must |
| US-05 | As a public-works/planning user, I want scenario evidence and KPI comparisons retained so that a proposal can be reviewed and justified. | Must |
| US-06 | As an energy/utility user, I want to view current/replayed/synthetic demand and a short-horizon forecast so that I can identify likely peaks. | Must |
| US-07 | As an environment user, I want to view weather/AQI context and threshold alerts so that mobility decisions can be interpreted with environmental context. | Should |
| US-08 | As an authorized user, I want recommendations to show evidence and uncertainty so that I can exercise human judgment rather than follow an opaque system. | Must |
| US-09 | As an authorized user, I want all recommendations to remain advisory so that the system cannot autonomously alter public infrastructure. | Must |

### 10.2 Cross-department collaboration users

| ID | User story | Priority |
|---|---|---:|
| US-10 | As a city department user, I want shared entity identifiers and a common data vocabulary so that future departments can integrate data without rebuilding the platform. | Should |
| US-11 | As a planning user, I want data source and scenario provenance so that evidence can be reviewed across departments. | Must |
| US-12 | As a city administrator, I want basic role-based access so that viewers, analysts, and administrators have appropriate permissions. | Should |

### 10.3 Technical and research users

| ID | User story | Priority |
|---|---|---:|
| US-13 | As a developer, I want simulation, replay, and live modes to use the same downstream pipeline so that integrations are testable and extensible. | Must |
| US-14 | As a data/ML engineer, I want chronological model evaluation against simple baselines so that performance claims are credible. | Must |
| US-15 | As a researcher, I want experiments, data versions, model versions, scenario configurations, and metrics recorded so that findings are reproducible. | Must |
| US-16 | As a reviewer, I want documented limitations, especially data geography and simulation-to-real limitations, so that the pilot is not overclaimed. | Must |

### 10.4 Citizen/public benefit stories

| ID | User story | Priority |
|---|---|---:|
| US-17 | As a citizen or commuter, I benefit when city authorities can test mobility interventions before implementing them in public space. | Outcome |
| US-18 | As a citizen, I benefit when public decisions are supported by transparent evidence rather than unexplained claims. | Outcome |
| US-19 | As a citizen, I should not have my personal data, camera imagery, or movement history ingested by this MVP. | Must |

---

## 11. MVP functional requirements

### 11.1 Governance dashboard and shared operational view

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---:|---|
| FR-01 | The system must display the pilot corridor, boundary, road segments, intersections, and registered entities on a 2D map. | Must | Map loads versioned study-area geometry and assets. |
| FR-02 | The system must provide a corridor-level current-condition view for authorized users. | Must | Current traffic/energy/environment status is visible with timestamp and provenance. |
| FR-03 | The system must show data freshness and quality state for operationally relevant values. | Must | UI/API display last-update time and quality status. |
| FR-04 | The system must support viewing traffic, energy, environment, forecasts, alerts, and scenarios through a shared interface. | Must | Required views are accessible through consistent navigation. |
| FR-05 | The system should support viewer, analyst, and administrator roles. | Should | Role behavior is documented and enforced for scenario/configuration actions. |

### 11.2 Pilot area and asset representation

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---:|---|
| FR-06 | The system must store a versioned GeoJSON boundary for the Viman Nagar–Somnath Nagar pilot corridor. | Must | Boundary is versioned in repository and loaded in PostGIS. |
| FR-07 | The system must represent at least 2 primary intersections and 8–15 road segments. | Must | Entities are queryable and visible on map. |
| FR-08 | The system must register at least 5–15 logical traffic sensors/source points. | Must | Each source has ID, source mode, link to asset, and location/reference. |
| FR-09 | The system must represent at least one building/zone energy entity. | Must | Energy entity has identifier, metadata, and time-series association. |
| FR-10 | The system must record relationships among roads, intersections, sensors, and building/energy entities. | Must | API/database returns valid relationship links. |

### 11.3 Data acquisition, ingestion, and quality

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---:|---|
| FR-11 | The system must support simulation-mode data ingestion. | Must | SUMO/synthetic publisher produces canonical events accepted by ingestion pipeline. |
| FR-12 | The system must support replay-mode data ingestion. | Must | Historical file/API dump replays through the same pipeline. |
| FR-13 | The system may support approved live API/sensor input. | Could | Live adapter works without changing downstream state/model/UI logic. |
| FR-14 | Simulation, replay, and live data must converge to one canonical data contract. | Must | Same validation/storage contract is used after transformation. |
| FR-15 | The system must validate required fields, data types, units, timestamps, ranges, identity, and geometry references. | Must | Invalid event is rejected/flagged with structured reason. |
| FR-16 | The system must preserve source, source mode, observed time, received time, and quality metadata. | Must | Provenance fields are stored and returned. |
| FR-17 | The system must detect or safely handle duplicate, stale, missing, and invalid observations. | Must | Quality status is surfaced through API/UI. |

### 11.4 Twin-state management

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---:|---|
| FR-18 | The system must maintain current state for mutable entities. | Must | Latest valid state is retrievable by entity ID. |
| FR-19 | The system must retain historical observations for supported metrics. | Must | Time-range API returns chronological history. |
| FR-20 | The system must store observed, predicted, and simulated states separately. | Must | Forecast/scenario records cannot overwrite observations. |
| FR-21 | The system must expose entity relationships and data provenance. | Must | Entity detail includes related assets/sources and provenance. |
| FR-22 | The system should retain relevant audit events for scenarios, model changes, recommendation creation, and configuration changes. | Should | Authorized reviewer can inspect audit metadata. |

### 11.5 Traffic analytics and forecasting

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---:|---|
| FR-23 | The system must display current speed, count, and/or congestion index on selected road segments. | Must | Map/detail view displays valid metric and unit. |
| FR-24 | The system must implement a traffic persistence baseline. | Must | Baseline predictions and metrics are logged. |
| FR-25 | The system must train and use an XGBoost traffic forecasting model. | Must | Versioned model artifact produces forecast through inference path. |
| FR-26 | The system must produce a selected traffic target forecast at a 15-minute horizon. | Must | Forecast has target, horizon, value, interval, timestamp, model version. |
| FR-27 | The system must evaluate traffic model against a chronological held-out test set. | Must | Baseline and model MAE/RMSE are recorded. |
| FR-28 | The system should show feature importance or SHAP explanation for traffic forecasts. | Should | At least global importance exists; selected forecast explanation preferred. |
| FR-29 | The system must document that training data collected at other Pune intersections does not establish local Viman Nagar accuracy. | Must | Limitation appears in evaluation and UI/model metadata where relevant. |

### 11.6 Energy analytics and forecasting

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---:|---|
| FR-30 | The system must ingest/replay/simulate timestamped energy-demand values for a representative entity. | Must | Values are stored and charted. |
| FR-31 | The system must visibly label energy data as measured, replayed, benchmark, or synthetic. | Must | Provenance appears in UI/API. |
| FR-32 | The system must implement a persistence/same-hour energy baseline. | Must | Baseline metrics are logged. |
| FR-33 | The system must train and use an XGBoost energy forecasting model. | Must | Versioned artifact produces 60-minute forecast. |
| FR-34 | The system must evaluate energy forecasting using MAE and RMSE. | Must | Evaluation output exists. |
| FR-35 | The system should create an advisory when forecasted demand crosses a configured peak threshold. | Should | Recommendation includes evidence and provenance. |

### 11.7 Environmental context

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---:|---|
| FR-36 | The system should display weather context relevant to the study area. | Should | Temperature plus at least one additional weather variable visible. |
| FR-37 | The system should display available AQI/air-quality readings with source station metadata. | Should | Reading includes station/source, timestamp, and geographic caveat. |
| FR-38 | The system should generate transparent threshold-based environmental alerts. | Should | Configured threshold triggers visible advisory/alert. |
| FR-39 | The system may add anomaly detection only after sufficient data is available for validation. | Could | Addition is justified by documented data/evaluation evidence. |

### 11.8 Simulation and intervention evaluation

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---:|---|
| FR-40 | The system must include a SUMO network for the selected pilot corridor. | Must | Network starts and completes from documented configuration. |
| FR-41 | The system must support one baseline scenario. | Must | Baseline KPI record is produced and stored. |
| FR-42 | The system must support at least one approved intervention scenario. | Must | Intervention differs from baseline through documented parameter/configuration. |
| FR-43 | The system must use comparable controlled seed/demand inputs for fair baseline/intervention comparison. | Must | Run records include seed and input versions. |
| FR-44 | The system must calculate average travel time, average delay, queue length, and throughput. | Must | KPI comparison is stored and visualized. |
| FR-45 | The first intervention should be signal timing adjustment, turn restriction, reroute, or demand surge. | Should | One predefined scenario template is selectable. |
| FR-46 | Simulation output must be explicitly labeled and isolated from observed state. | Must | UI/API identify `SIMULATION` and scenario run ID. |

### 11.9 Explainable advisory decision support

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---:|---|
| FR-47 | The system must create rule-based advisory recommendations. | Must | At least one documented rule can create a recommendation. |
| FR-48 | Every recommendation must show trigger, evidence, source/provenance, quality/confidence, suggested action, and timestamp. | Must | All fields appear in API/UI. |
| FR-49 | Recommendations must remain human-approved and non-actuating. | Must | No physical control integration exists. |
| FR-50 | Recommendations should link to relevant forecast/model/scenario evidence. | Should | User can navigate to supporting evidence. |
| FR-51 | Recommendations should support acknowledgement/review status by authorized users. | Should | Status can be updated without altering original evidence. |

### 11.10 Platform delivery and interoperability foundation

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---:|---|
| FR-52 | The system must run locally using Docker Compose. | Must | Fresh setup works with documented commands. |
| FR-53 | The system must provide health/readiness endpoint(s). | Must | API reports application and dependency readiness. |
| FR-54 | The system must document environment variables and provide `.env.example`. | Must | No secrets are committed. |
| FR-55 | The system must log ingestion, validation, forecast, scenario, recommendation, and error events. | Must | Logs support basic diagnosis. |
| FR-56 | The system should run lint/unit/integration checks via GitHub Actions. | Should | Workflow runs on push/PR. |
| FR-57 | The system must use an NGSI-LD-inspired canonical entity model with explicit migration path toward standards-based interoperability. | Must | Schema documentation and examples exist. |
| FR-58 | The system must include reproducible demo and evaluation instructions. | Must | Another contributor can reproduce core flow. |

---

## 12. Non-functional requirements

### 12.1 Governance quality and trust

| ID | Requirement |
|---|---|
| NFR-01 | The platform must make data origin, time, quality, and simulation/forecast status understandable to non-technical decision-makers. |
| NFR-02 | The platform must preserve evidence links for forecasts, recommendations, scenarios, and important configuration changes. |
| NFR-03 | The platform must not represent experimental output as official municipal instruction or verified live city state. |
| NFR-04 | The platform must expose meaningful limitations instead of hiding uncertainty. |
| NFR-05 | The platform must support human review and accountability for every recommendation. |

### 12.2 Performance

These are MVP targets, not municipal service-level agreements.

| ID | Requirement | Target |
|---|---|---|
| NFR-06 | Ingestion-to-current-state latency in replay/simulation mode | Target p95 under 5 seconds at MVP load |
| NFR-07 | Dashboard state refresh | Target within 5 seconds of processed event |
| NFR-08 | Scheduled forecast cycle | Every 5 minutes or configured interval |
| NFR-09 | Entity detail response | Target under 2 seconds in local/demo environment |
| NFR-10 | Scenario runtime | Show progress, record duration, optimize after correctness |
| NFR-11 | Initial network scale | 2 junctions, 8–15 segments, 5–15 logical sensors |

### 12.3 Reliability and correctness

| ID | Requirement |
|---|---|
| NFR-12 | Invalid messages must not update authoritative current state. |
| NFR-13 | Duplicate events must not double-count observations or corrupt state. |
| NFR-14 | Forecast and scenario records must never overwrite source observations. |
| NFR-15 | Each displayable value must have explicit unit, time context, and provenance. |
| NFR-16 | Scenario comparisons must retain configuration, seed, input versions, and outputs. |
| NFR-17 | Model output must fail safely when required features are missing. |

### 12.4 Security, privacy, and access

| ID | Requirement |
|---|---|
| NFR-18 | No secrets may be committed to source control. |
| NFR-19 | MQTT must use authentication; TLS is required for real remote devices/sources. |
| NFR-20 | Any remote dashboard/API deployment must use application authentication. |
| NFR-21 | No PII, camera imagery, plates, faces, or individual traces may be stored. |
| NFR-22 | Dataset licenses, attribution, retention, and usage restrictions must be documented. |
| NFR-23 | Role-based permissions must restrict scenario/configuration actions where implemented. |

### 12.5 Usability and accessibility

| ID | Requirement |
|---|---|
| NFR-24 | Map legends, units, timestamps, source labels, and freshness indicators must be visible. |
| NFR-25 | Critical status must not rely only on red/green colors. |
| NFR-26 | The dashboard must be usable at standard desktop width and remain understandable on tablet/mobile widths. |
| NFR-27 | The dashboard must visibly distinguish `LIVE`, `REPLAY`, `SIMULATION`, and `PREDICTED`. |
| NFR-28 | Basic keyboard focus, readable contrast, and reduced-motion considerations must be applied. |

### 12.6 Reproducibility and research quality

| ID | Requirement |
|---|---|
| NFR-29 | Datasets, imports, model runs, and scenario runs must use versioned/configured inputs. |
| NFR-30 | ML metadata must include input dataset version, split logic, seed, parameters, metrics, and artifact reference. |
| NFR-31 | The primary demo must be reproducible from documented setup steps. |
| NFR-32 | Results must distinguish local measurement, cross-location training, simulation, replay, and synthetic evidence. |

---

## 13. Data and provenance requirements

### 13.1 Mandatory provenance classes

| Label | Meaning |
|---|---|
| `LIVE` | Approved real API/sensor source data |
| `REPLAY` | Historical data republished as a stream |
| `SIMULATION` | SUMO or synthetic-generator output, including scenario results |
| `PREDICTED` | Forecast from a trained model |
| `STALE` | Data older than configured freshness threshold |
| `INVALID` | Data failing validation/not fit for trusted use |

### 13.2 Minimum canonical observation contract

```json
{
  "id": "urn:ngsi-ld:EntityType:entity-id",
  "type": "TrafficFlowObserved | EnergyConsumptionObserved | AirQualityObserved | WeatherObserved",
  "observedAt": "ISO-8601 timestamp",
  "location": {"type": "Point | LineString | Polygon", "coordinates": []},
  "sourceMode": "simulation | replay | live | predicted",
  "sourceId": "source-name-or-run-id",
  "dataQualityScore": 0.0,
  "payload": {},
  "ingestedAt": "ISO-8601 timestamp"
}
```

### 13.3 Dataset governance requirements

Every dataset used by the platform must have recorded:

- Dataset name and source URL.
- License or terms of use.
- Download/access date.
- Geographic coverage.
- Temporal coverage and sampling frequency.
- Data fields/units.
- Quality limitations.
- Intended use: training, benchmark, replay, context, simulation calibration, or visualization.
- Required attribution.
- Known gaps and restrictions.

### 13.4 Data honesty requirements

- Traffic data from RTO Chowk, Alankar Chowk, or Jehangir Chowk must not be described as Viman Nagar measurements.
- Foreign benchmark datasets must not be used to claim Pune-local accuracy.
- Synthetic energy data must be labeled synthetic.
- SUMO outputs must be labeled simulated.
- A regional AQI station must not be presented as exact corridor-level air quality without supporting evidence.

---

## 14. AI/ML requirements

### 14.1 Required trained models

The MVP requires exactly two primary trained models.

| Model | Target | Horizon | Baselines | Primary model | Required output |
|---|---|---:|---|---|---|
| Traffic forecast | Average speed or congestion index | 15 minutes | Persistence, historical average | XGBoost regressor | Forecast, interval, quality, model version, explanation metadata |
| Energy forecast | Building/zone demand/load | 60 minutes | Persistence/same-hour average | XGBoost regressor | Forecast, interval, quality, model version, explanation metadata |

### 14.2 Optional models

| Model | Condition for use |
|---|---|
| Isolation Forest environmental anomaly detection | Only after sufficient environmental time series exists for evaluation |
| LSTM/TCN/Transformer | Only as documented research comparison after baseline/data maturity |
| STGNN/GNN | Only after multi-segment topology and adequate time-series data exist |
| Reinforcement learning | Only after calibrated simulator, safety constraints, and a legitimate research question exist |

### 14.3 Model quality requirements

- Use chronological train/validation/test splits.
- Prevent leakage from future observations into training features.
- Compare against baseline(s).
- Report MAE and RMSE; use sMAPE/MAPE only where meaningful.
- Track data version, code version, seed, features, parameters, metrics, model artifact, and environment.
- Provide model explanation/feature importance.
- Return `unavailable`/`low-quality` forecast status when inputs are insufficient.
- Do not use prediction accuracy alone as a governance-quality claim.

---

## 15. Simulation and intervention requirements

### 15.1 Required scenario workflow

```text
Select approved scenario
→ initialize baseline input/configuration
→ run baseline SUMO simulation
→ run intervention SUMO simulation
→ compute comparable KPIs
→ store seed/configuration/artifacts
→ show result as SIMULATION
→ optionally create advisory recommendation
→ require human review outside the platform
```

### 15.2 Minimum scenario evidence

Each scenario run must retain:

- Scenario ID/name/version.
- Study-area/network version.
- Demand input version.
- Signal/turn/routing configuration.
- Random seed.
- Baseline/intervention status.
- Start/end time and run status.
- KPI outputs.
- Artifact locations/logs.
- User/request metadata where applicable.

### 15.3 Required KPIs

- Average travel time.
- Average delay.
- Maximum or average queue length.
- Throughput/vehicles completed.
- Optional emissions only if the simulation configuration supports and documents them.

### 15.4 First intervention

The first intervention must be selected from:

1. Signal timing adjustment.
2. Turn restriction.
3. Rerouting/diversion.
4. Peak-demand surge scenario.

A scenario result is valid even if it does not improve traffic KPIs. Negative or mixed outcomes must be reported honestly.

---

## 16. Decision-support requirements

### 16.1 Advisory recommendation design

Each recommendation must include:

- Recommendation ID/type/status.
- Target entity or corridor.
- Rule/trigger that generated it.
- Current and/or forecast evidence.
- Source mode/provenance.
- Data quality/confidence.
- Suggested action.
- Linked scenario run/model version where applicable.
- Timestamp.
- Explicit human approval requirement.

### 16.2 Example advisory logic

```text
IF predicted corridor congestion exceeds configured threshold
AND data quality meets configured minimum
THEN recommend evaluation of approved traffic scenario.

IF energy forecast exceeds configured peak threshold
THEN recommend review of demand-management scenario.

IF environmental threshold is exceeded
THEN flag condition for department monitoring.
```

### 16.3 Governance safeguards

- Rules must be documented and reviewable.
- Recommendations are not commands.
- Recommendation evidence must be inspectable by users.
- An acknowledged/dismissed recommendation must preserve the original evidence trail.
- The MVP does not optimize public services automatically.

---

## 17. UI/UX requirements

### 17.1 Product experience

The main interface is an authorized **city operations and planning dashboard**, not a consumer navigation map.

The product must make it easy for public-sector users to move from:

```text
Condition observed
→ evidence inspected
→ forecast understood
→ scenario tested
→ recommendation reviewed
→ decision considered by authorized human
```

### 17.2 Required views

| View | Required content | Priority |
|---|---|---:|
| Operations map | Study area, roads, junctions, state overlays, legend, provenance | Must |
| Corridor/entity detail | Current state, history, forecast, quality, related assets | Must |
| Traffic analytics | Trend, 15-minute forecast, model/explanation context | Must |
| Energy analytics | Load trend, 60-minute forecast, source/synthetic label | Must |
| Environment context | Weather/AQI source, threshold status, caveats | Should |
| Alerts/recommendations | Advisory list with evidence and review state | Must |
| Scenario workspace | Approved scenario templates, progress, KPI comparison | Must |
| Governance/system status | Data freshness, source health, model/scenario versioning | Should |
| Optional 3D explorer | Visual presentation of same twin overlays | Could |

### 17.3 UI integrity rules

- Use visible legends and units.
- Show measurement/forecast timestamps.
- Display source labels on all dynamic values.
- Never make scenario output look like current measured traffic.
- Do not use color alone for critical status.
- Make uncertainty/quality understandable, not hidden in developer-only logs.
- Provide an accessible fallback when optional 3D is unavailable.

---

## 18. Release criteria / Definition of Done

The pilot MVP is ready for review only when all statements below are true.

### 18.1 Platform and governance workflow

- [ ] Pilot area boundary is finalized, versioned, and displayed.
- [ ] Authorized user can inspect a shared corridor operations view.
- [ ] Current, historical, predicted, and simulated states are separate.
- [ ] All dynamic values expose source/provenance, time, quality, and unit.
- [ ] Recommendations are advisory and evidence-backed.
- [ ] No physical actuation capability exists.

### 18.2 Data and digital twin

- [ ] Roads, intersections, logical sensors, and one energy entity are registered.
- [ ] Simulation and replay modes work through the same ingestion path.
- [ ] Canonical entity contract and data-validation rules are implemented.
- [ ] Current state and historical time series are persisted.
- [ ] Data-quality and freshness status are visible.

### 18.3 AI and simulation

- [ ] Traffic baseline and XGBoost model are trained/evaluated.
- [ ] Energy baseline and XGBoost model are trained/evaluated.
- [ ] Model metrics are compared with baselines.
- [ ] One SUMO baseline scenario runs.
- [ ] One intervention scenario runs with controlled assumptions.
- [ ] KPI comparison is persisted and displayed.
- [ ] At least one recommendation links to forecast/scenario evidence.

### 18.4 Engineering and research quality

- [ ] System runs through Docker Compose from documented setup.
- [ ] Dataset sources/licenses/limitations are documented.
- [ ] Model/scenario artifacts and metadata are retained.
- [ ] Key tests pass.
- [ ] Demo script can be followed by another contributor.
- [ ] Limitations, including the Viman Nagar/local-data and simulation-to-real gap, are stated clearly.
- [ ] No unsupported claim of live city integration, citywide coverage, or autonomous governance appears in product material.

---

## 19. Prioritization

### Must-have MVP

- Government/city-operations framing and authorized user workflow.
- Pilot corridor spatial representation.
- Simulation and replay modes.
- MQTT ingestion and validation.
- Current/historical/predicted/simulated state separation.
- Traffic and energy XGBoost models with baselines.
- SUMO baseline vs intervention comparison.
- Rule-based evidence-backed advisory recommendations.
- React + MapLibre dashboard.
- Provenance, freshness, quality, and unit visibility.
- Docker Compose reproducibility.

### Should-have

- Weather/AQI context.
- SHAP visualization.
- Recommendation acknowledgement status.
- Basic user roles.
- GitHub Actions tests.
- System health and governance-status view.
- Scenario-to-recommendation evidence linking.

### Could-have

- Permitted live source adapter.
- Optional Cesium/3D visual presentation.
- Isolation Forest anomaly detection.
- Additional scenario templates.
- Read-only public transparency/citizen view.
- Initial interoperability demonstration with FIWARE/Orion-LD.

### Explicitly excluded from MVP

- Public-infrastructure actuation.
- CCTV/video/PII.
- Citywide deployment.
- Enterprise SLA claims.
- Full context broker deployment.
- Kafka/Kubernetes.
- Deep/GNN/RL models.
- Blockchain, LLM/agentic decision layer, federated learning.

---

## 20. Dependencies

| Dependency | Required for | Constraint/risk |
|---|---|---|
| OpenStreetMap/OSMnx | Pilot geometry, map, SUMO network | Road attributes and turns need validation |
| Pune traffic count dataset | Initial traffic model pipeline/prototyping | Location differs from pilot corridor |
| SUMO + TraCI | Mobility behavior/scenario comparison | Network/demand setup can be complex |
| Weather API/data | Context and forecasting features | Rate limits/coverage/completeness |
| Energy data source | Energy forecast | Local measured data may be unavailable |
| Docker | Reproducible setup | Contributor environment compatibility |
| Postgres/Timescale/PostGIS | Twin persistence | Requires migration/backup discipline |
| Optional Google/Cesium 3D | Presentation layer only | Cost/terms/attribution; never a core dependency |

---

## 21. Open decisions before implementation

| ID | Decision | Owner | Needed before |
|---|---|---|---|
| OD-01 | Exact GeoJSON boundary and road approaches | GIS/project lead | SUMO network creation |
| OD-02 | Primary traffic target: speed or congestion index | ML/project lead | Feature/model pipeline |
| OD-03 | Time interval: 5, 10, or 15 minutes | Data/ML lead | Schema/training |
| OD-04 | First intervention type | Governance/simulation lead | Scenario implementation |
| OD-05 | Energy-source category: permitted meter, replay, benchmark, or synthetic | Data/project lead | Energy pipeline |
| OD-06 | Prediction-interval technique: quantile model, conformal, or bootstrap | ML lead | Model implementation |
| OD-07 | MVP roles/authentication approach | Platform/governance lead | Remote deployment |
| OD-08 | Whether optional 3D is included in final presentation | Product/design lead | UI roadmap, not MVP blocker |
| OD-09 | Review process for recommendation thresholds/rules | Governance/project lead | Rule-engine configuration |

---

## 22. Supporting resources

### Government, smart-city, and Pune context

- [Pune Smart City](https://www.punesmartcity.in/)
- [Pune Smart City Adaptive Traffic Management System document](https://www.punesmartcity.in/assets/PANCITY/Adaptive%20Traffic%20Management%20System.pdf)
- [Pune Smart City / Government open-data portal](https://smartcities.data.gov.in/cities/Pune)
- [Pune Corporation Open Data Portal](https://opendata.pmc.gov.in/)
- [OpenCity Pune data catalog](https://data.opencity.in/dataset/?groups=pune)

### Digital-twin and interoperability resources

- [FIWARE Smart Data Models](https://smart-data-models.github.io/data-models/)
- [NGSI-LD](https://ngsi-ld.org/)
- [FIWARE Digital Twins position paper](https://www.fiware.org/wp-content/uploads/FF_PositionPaper_FIWARE4DigitalTwins.pdf)
- [Eclipse Ditto](https://eclipse.dev/ditto/)
- [Snap4City](https://www.snap4city.org/)
- [OGC CityGML](https://www.ogc.org/standards/citygml/)
- [OGC SensorThings API](https://www.ogc.org/standards/sensorthings/)

### Data, simulation, and ML resources

- [OpenStreetMap](https://www.openstreetmap.org/)
- [OSMnx](https://github.com/gboeing/osmnx)
- [Eclipse SUMO](https://eclipse.dev/sumo/)
- [SUMO TraCI documentation](https://sumo.dlr.de/docs/TraCI.html)
- [Pune heterogeneous traffic count dataset](https://data.mendeley.com/datasets/xnf2k6n288/1)
- [Pune Hourly Air Quality Reports](https://data.opencity.in/dataset/pune-hourly-air-quality-reports)
- [Meteostat](https://dev.meteostat.net/data)
- [Open-Meteo historical weather API](https://open-meteo.com/en/docs/historical-weather-api)
- [UCI Electricity Load Diagrams dataset](https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112014)
- [XGBoost documentation](https://xgboost.readthedocs.io/)
- [MLflow](https://mlflow.org/)
- [SHAP](https://shap.readthedocs.io/)

---

## 23. Change management

A documented approval is required before changing:

- Product/governance positioning.
- Pilot study-area boundary.
- Primary institutional user groups.
- Safety and actuation boundaries.
- Canonical data/provenance contract.
- Core technical stack.
- Model targets, evaluation metrics, or evidence claims.
- Definition of done.

The next active documents are:

1. `TECHNICAL_ARCHITECTURE.md`
2. `DATA_AND_ML_PLAN.md`
3. `UI_UX_SPEC.md`
4. `ROADMAP.md`
5. `DELIVERABLES.md`

---

## 24. Final product statement

> The Digital Twin-Enabled Smart City Analytics Platform is a government-oriented, AI-enabled urban decision-support system. It helps authorized city institutions observe urban conditions, integrate multi-domain data, forecast near-future risk, test interventions safely in simulation, and review transparent recommendations before human-led action. The Viman Nagar–Somnath Nagar pilot is a limited proof of this broader governance platform—not the product’s final geographic or functional boundary.
