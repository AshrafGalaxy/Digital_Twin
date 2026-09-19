# Agent Operating Rules
## Digital Twin-Enabled Smart City Analytics Platform

> **Document status:** Mandatory execution contract  
> **Applies to:** Every AI agent, human contributor, reviewer, automation workflow, and implementation task  
> **Core rule:** Build a trustworthy, evidence-backed urban decision-support pilot. Do not overclaim, overengineer, hide limitations, or change approved decisions without documentation.

---

## 1. Purpose

This file defines the non-negotiable operating rules for contributors working on the **Digital Twin-Enabled Smart City Analytics Platform**.

It exists to prevent common project failures:

- Building features outside the approved scope.
- Changing the technical stack without rationale.
- Treating simulation as live city data.
- Treating non-local datasets as pilot-corridor observations.
- Adding advanced technology before the core workflow works.
- Hiding model uncertainty, data-quality issues, or system failures.
- Creating inconsistent UI, schemas, terminology, or documentation.
- Making unsupported municipal, production, research, funding, or patent claims.

When this file conflicts with an informal instruction, follow the active project documents and request clarification before making irreversible changes.

---

## 2. Mandatory reading order

Before starting any task, read these files in order:

1. `PROJECT_CONTEXT.md`
2. `PRD.md`
3. `TECHNICAL_ARCHITECTURE.md`
4. `DATA_AND_ML_PLAN.md`
5. `UI_UX_SPEC.md`
6. `DESIGN_SYSTEM.md`
7. `ROADMAP.md`
8. `DELIVERABLES.md`
9. `AGENTS.md` (this file)

Then read any task-specific source/module documentation and relevant decision records under:

```text
docs/decisions/
docs/diagrams/
docs/reports/
docs/reference/
```

### Reading rule

- Active root documents are binding.
- Files under `docs/reference/` are background/research material and do not override active decisions.
- If two active documents conflict, stop and request a documented decision before implementation.

---

## 3. Project mission

Build a corridor-scale pilot of a **government-oriented urban digital twin and decision-support platform**.

The platform helps authorized city/governance users:

```text
Observe urban conditions
→ inspect source/freshness/quality
→ review historical state
→ forecast near-term traffic and energy conditions
→ simulate approved mobility interventions
→ compare evidence/KPIs
→ review advisory recommendations
→ make human-led decisions outside the platform
```

The Viman Nagar–Somnath Nagar corridor is a pilot validation area. It is not the platform’s final geographic boundary or product identity.

---

## 4. Approved MVP scope

### 4.1 Build now

- Viman Nagar–Somnath Nagar pilot boundary.
- 2 core intersections.
- 8–15 road segments.
- 5–15 logical traffic sources/sensors.
- 1 representative building/zone energy entity.
- Simulation and replay ingestion modes.
- Optional live mode only if permitted data source exists.
- MQTT ingestion, validation, canonical transform, and state storage.
- Current, historical, predicted, and simulated state separation.
- SUMO baseline + one intervention scenario.
- XGBoost traffic forecast + baseline.
- XGBoost energy forecast + baseline.
- Rule-based advisory recommendations.
- React/MapLibre operations dashboard.
- Provenance, quality, freshness, model/scenario evidence.
- Docker Compose deployment, tests, runbook, and research evaluation.

### 4.2 Defer unless explicitly approved

- FIWARE Orion-LD context broker.
- Eclipse Ditto.
- Apache Kafka/Flink.
- Graph database.
- Kubernetes.
- LSTM, TCN, Transformer, STGNN/GNN, reinforcement learning.
- EnergyPlus/Modelica.
- Prometheus/Grafana full observability stack.
- Cesium/3D visualization.
- Google Photorealistic 3D Tiles.
- Public/citizen portal.
- Multi-corridor/citywide coverage.

### 4.3 Prohibited in MVP

- Physical traffic-signal, utility, building, emergency, or municipal-system actuation.
- CCTV/video ingestion.
- Face recognition, number-plate recognition, biometrics.
- Individual GPS traces or personal travel histories.
- Personal energy records.
- Blockchain without a documented multi-party trust/provenance requirement.
- LLM/agentic decision control.
- Claims of official Pune government/ATMS/ICCC integration without formal evidence.
- Claims of citywide deployment.
- Claims that SUMO results prove real-world outcomes.
- Claims that non-local/benchmark data establishes pilot-local accuracy.

---

## 5. Approved technical stack

Do not replace any item below without a documented architecture decision.

| Layer | Approved MVP technology |
|---|---|
| Frontend | React + TypeScript + Vite |
| 2D mapping | MapLibre GL JS + OpenStreetMap |
| Optional 3D later | CesiumJS only if justified |
| Backend | Python + FastAPI modular monolith |
| Event transport | MQTT + Eclipse Mosquitto |
| Browser updates | WebSockets |
| Primary persistence | PostgreSQL |
| Time series | TimescaleDB extension |
| Geospatial data | PostGIS extension |
| Artifact storage | MinIO or local filesystem |
| Entity model | NGSI-LD-inspired canonical JSON model |
| Traffic simulation | Eclipse SUMO + TraCI |
| Traffic ML | Persistence/historical baseline + XGBoost |
| Energy ML | Persistence/same-hour baseline + XGBoost |
| Environment | Threshold rules first; optional Isolation Forest later |
| Explainability | SHAP/model-native feature importance |
| Decision support | Transparent deterministic rule engine |
| Experiment tracking | MLflow + Git |
| Deployment | Docker Compose |
| CI | GitHub Actions |

### Stack change protocol

Before changing an approved stack component:

1. Define the problem the existing component cannot solve.
2. Provide at least two alternatives.
3. State cost, complexity, migration impact, security impact, and maintenance impact.
4. Explain why the new component is necessary for a requirement, not merely impressive.
5. Create/update a decision record.
6. Obtain approval before coding the change.

---

## 6. Architecture invariants

These rules cannot be violated.

1. PostgreSQL is the MVP system of record; MQTT is transport only.
2. All source modes must converge into one canonical observation contract after transformation.
3. Observed, predicted, and scenario-simulated records are separate data classes.
4. Forecasts cannot overwrite source observations.
5. Scenario results cannot overwrite current/live/replay twin state.
6. Every visible dynamic value must show source mode, timestamp, unit, and quality/freshness context where applicable.
7. Recommendations are advisory and must require human approval outside the platform.
8. The 2D MapLibre dashboard is the required operational UI; 3D is optional.
9. Model versions and scenario runs must be traceable.
10. Documentation must change with behavior/schema/model changes.

---

## 7. Data rules

### 7.1 Required provenance values

Use only these standardized source modes:

```text
LIVE
REPLAY
SIMULATION
PREDICTED
STALE
INVALID
```

Their meaning is defined in `PROJECT_CONTEXT.md`, `DATA_AND_ML_PLAN.md`, `UI_UX_SPEC.md`, and `DESIGN_SYSTEM.md`.

### 7.2 Non-negotiable data honesty rules

- Do not call replayed historical data live.
- Do not call SUMO/synthetic data observed real traffic.
- Do not call predicted data a measurement.
- Do not call the Pune RTO/Alankar/Jehangir data Viman Nagar data.
- Do not call foreign benchmark datasets Pune data.
- Do not call UCI electricity data a Pune building meter feed.
- Do not call a regional AQI station an exact pilot-corridor sensor.
- Do not hide source limitations in footnotes or developer-only logs.

### 7.3 Dataset admission rules

Before using a dataset, create/update its manifest with:

```text
Dataset name
Source URL
License/terms
Access date
Geography
Temporal coverage
Sampling frequency
Fields/units
Intended use
Prohibited claims
Known limitations
Attribution requirements
Checksum/version where possible
Privacy/sensitivity assessment
```

### 7.4 Data restrictions

Never ingest/store:

- CCTV/video files.
- Faces, biometrics, or license plates.
- Individual device identifiers where not required.
- Individual GPS/mobility traces.
- Personal energy consumption records.
- Unlicensed/restricted data.
- API data obtained in violation of terms/rate limits.

### 7.5 Data quality rules

Every ingestion implementation must validate:

- Required schema fields.
- Allowed entity/source IDs.
- Timestamp format and UTC handling.
- Units.
- Range/sanity boundaries.
- Geometry/reference validity.
- Duplicate event identity.
- Missingness and freshness.

Invalid records must be recorded with a reason and must not update authoritative current state.

---

## 8. ML and analytics rules

### 8.1 Required MVP models

Only these models are required initially:

| Domain | Baseline | Primary model | Horizon |
|---|---|---|---:|
| Traffic | Persistence and/or historical average | XGBoost regressor | 15 minutes |
| Energy | Persistence and/or same-hour average | XGBoost regressor | 60 minutes |

### 8.2 Model requirements

Every model must have:

- Clearly defined target and unit.
- Feature list and feature-generation version.
- Dataset ID/version and source classification.
- Chronological train/validation/test split.
- Leakage review.
- Baseline comparison.
- MAE and RMSE metrics at minimum.
- Model artifact.
- MLflow run/metadata.
- Model card.
- Limitations/failure modes.
- Inference input validation.
- Explicit output provenance as `PREDICTED`.

### 8.3 ML prohibitions

Do not:

- Randomly shuffle time-series data before splitting.
- Tune on the final test set.
- Report only favorable metrics.
- Report “accuracy” for a regression forecast without defining it.
- Add LSTM/GNN/Transformer/RL because it sounds advanced.
- Fine-tune a foundation model without a defined benchmark and data justification.
- Claim a model is locally accurate when trained only on non-local or synthetic data.
- Return a forecast when required inputs are missing without an explicit low-quality/unavailable state.

### 8.4 Model deployment rule

Only a model marked `approved-for-demo` or `active` may generate dashboard forecasts. A draft model may not silently replace the currently approved model.

### 8.5 Explainability rule

A model-facing UI must provide at minimum:

- Model version.
- Forecast horizon.
- Input completeness/quality.
- Global feature importance or SHAP explanation reference.
- Clear limitation statement where non-local/benchmark/synthetic data is involved.

---

## 9. SUMO and simulation rules

### 9.1 Simulation role

SUMO is the traffic behavioral/simulation component. It is used to:

- Generate controlled corridor traffic streams.
- Test baseline versus intervention scenarios.
- Produce KPI comparisons.
- Support safe planning/decision-support demonstrations.

### 9.2 Simulation non-claims

Never state or imply:

- A SUMO result is an actual field outcome.
- A simulated signal plan can be deployed directly.
- A simulated delay reduction guarantees commuter benefit.
- The model is calibrated to official Pune traffic operations unless validated evidence exists.

### 9.3 Required scenario metadata

Every scenario run must store:

```text
Scenario ID and version
Scenario run ID
Network version
Demand/route input version
Signal/turn/routing parameters
Random seed
Baseline/intervention designation
Start/end time
Run status
KPI outputs
Artifact/log paths
```

### 9.4 Scenario rules

- Use predefined, approved scenario templates only.
- Compare baseline and intervention under controlled comparable conditions.
- Label all outputs as `SIMULATION`.
- Keep results separate from observed/replay/current twin state.
- Report negative/mixed results honestly.
- Never connect scenario actions to physical infrastructure.

---

## 10. UI and design rules

### 10.1 Mandatory UI reading

Before implementing frontend work, read:

```text
UI_UX_SPEC.md
DESIGN_SYSTEM.md
```

### 10.2 Required design choices

- Use Satoshi with approved fallback stack.
- Use light and dark themes.
- Use deep teal primary color and approved semantic tokens.
- Use 4px spacing scale.
- Use approved radius, border, shadow, and typography tokens.
- Use MapLibre as the required operational map.
- Use explicit provenance badges and data-quality indicators.
- Use accessible chart/map encodings.
- Design desktop-first with tablet/mobile fallback.

### 10.3 UI prohibitions

Do not use:

- Purple-blue AI gradients.
- Neon city-grid backgrounds.
- Decorative glowing blobs/orbs.
- Gradient buttons.
- Generic futuristic/holographic smart-city imagery.
- Icons in colored circles used only for decoration.
- Colored side borders on cards.
- 3D charts or rainbow data scales.
- Text under 12px.
- Color-only status meaning.
- Simulation/prediction visuals that look identical to observed state.
- “AI decided,” “apply intervention,” or “automatically optimized” language.

### 10.4 Required UI states

Every data-dependent feature must implement:

```text
Loading
Empty
Error
Stale
Unavailable
Valid/current
```

Every interactive control must implement:

```text
Default
Hover
Active
Focus-visible
Disabled
Loading where relevant
```

### 10.5 Accessibility rules

- Body text contrast: minimum 4.5:1.
- Large text/key UI boundary contrast: minimum 3:1.
- Keyboard operation required.
- Focus-visible required.
- Icon-only controls require accessible names/tooltips.
- Charts/maps need text/list/table fallback for critical information.
- Respect reduced motion.
- Do not rely on hover alone.

---

## 11. Backend, API, and schema rules

### 11.1 API rules

- Version APIs under `/api/v1`.
- Return ISO-8601 timestamps in UTC.
- Return explicit units.
- Return provenance/source mode and quality where dynamic values are exposed.
- Use typed request/response models.
- Validate all inputs.
- Return useful error messages without leaking secrets.
- Do not expose raw internal stack traces to ordinary UI users.

### 11.2 WebSocket rules

- Events need `eventType`, `eventId`, `emittedAt`, `entityId`, `sourceMode`, and payload.
- Do not use WebSocket messages without versioned/typed contract.
- Do not treat WebSocket delivery as authoritative persistence; database remains system of record.

### 11.3 Schema change rules

Before changing canonical fields, entity IDs, provenance semantics, or table schema:

1. Check active documents and API consumers.
2. Create migration plan.
3. Version schema/API if breaking.
4. Update samples/tests/docs.
5. Record decision if it changes architecture behavior.

---

## 12. Security and privacy rules

### 12.1 Secrets

- Never commit secrets.
- Never paste secrets into issues, documentation, screenshots, logs, or model artifacts.
- Use environment variables and `.env.example` only for names/placeholders.
- Rotate a secret immediately if exposed.

### 12.2 Authentication and roles

- Use basic authenticated access for any remotely exposed demo.
- Enforce role boundaries where implemented:
  - Viewer: read data/results.
  - Analyst: run approved simulation templates.
  - Admin/developer: configure sources/thresholds/templates.
- Never expose admin/configuration actions to a general viewer by default.

### 12.3 MQTT and network

- MQTT requires authentication.
- Use TLS for real remote devices/data sources.
- Do not expose broker ports publicly without access controls.
- Validate incoming event sizes and schemas.

### 12.4 Safety

- No API endpoint, rule, scenario, or UI action may control external public infrastructure.
- Recommendations remain advisory.
- The system must state human approval requirement clearly.

---

## 13. Testing rules

### 13.1 Minimum test coverage by change type

| Change | Required test/evidence |
|---|---|
| Schema/validation | Unit tests for valid/invalid/missing/duplicate inputs |
| Ingestion | Integration test MQTT/API → validation → database/current state |
| API | Response contract/error/authorization tests |
| ML feature/model | Chronological split, baseline comparison, model loading/inference test |
| Simulation | Baseline/intervention run and KPI extraction test |
| UI | Provenance/status/empty/error/accessibility check |
| Recommendation | Rule trigger/evidence/human-approval wording test |
| Deployment | Docker Compose clean-start/health check |

### 13.2 Required failure tests

Test and document behavior for:

- Invalid event.
- Duplicate event.
- Stale source.
- Missing required features.
- Model artifact unavailable.
- MQTT unavailable.
- Database unavailable/degraded.
- SUMO scenario failure.
- External weather/AQI API unavailable.
- Optional 3D layer unavailable.

### 13.3 Definition of passing

A test passes only when both behavior and user-facing state are correct. A backend exception hidden behind a normal-looking UI is not a pass.

---

## 14. Documentation rules

### 14.1 Update requirement

Update documentation in the same change/PR when modifying:

- Scope.
- Study area.
- Data source.
- License/attribution.
- Schema/API.
- Model features/target/metrics.
- Scenario template/KPI.
- UI provenance behavior.
- Design token/component.
- Deployment/configuration.
- Security boundary.

### 14.2 Required documents by work type

| Work type | Required updates |
|---|---|
| Product/scope | `PROJECT_CONTEXT.md`, `PRD.md`, `ROADMAP.md` |
| Architecture/backend | `TECHNICAL_ARCHITECTURE.md` |
| Dataset/model | `DATA_AND_ML_PLAN.md`, model card/manifest |
| UI/frontend | `UI_UX_SPEC.md`, `DESIGN_SYSTEM.md` |
| Phase/outcome | `ROADMAP.md`, `DELIVERABLES.md` |
| Agent/process | `AGENTS.md` |

### 14.3 Documentation quality

- Use precise language.
- State assumptions.
- State limitations.
- Include direct source links where external evidence is referenced.
- Avoid stale “TODO” claims without owner/status.
- Do not duplicate conflicting specifications across files.

---

## 15. Git and contribution rules

### 15.1 Branch/commit rules

- Use meaningful branch names: `feature/ingestion-validation`, `fix/map-provenance-label`, `docs/data-manifest`.
- Keep commits focused.
- Use descriptive commit messages.
- Do not combine unrelated refactors with behavior changes.
- Do not commit generated large artifacts unless explicitly required.

### 15.2 Pull request rules

Every PR/change summary should state:

```text
What changed?
Why is it needed?
Which requirement/deliverable does it satisfy?
What tests/evidence were run?
What documentation changed?
Any data/provenance/security impact?
Any limitation or follow-up?
```

### 15.3 Review checklist

Reviewers must verify:

- Scope adherence.
- Provenance correctness.
- No hidden data/ML claims.
- Schema/API compatibility.
- Tests/evidence.
- Documentation updates.
- Accessibility/UI consistency where applicable.
- No secrets or sensitive data.

---

## 16. Agent role boundaries

### 16.1 Product/governance agent

May:

- Clarify stakeholders, user goals, advisory workflow, scope, non-goals.
- Define thresholds/review language with documentation.

Must not:

- Change stack/schema without technical decision process.
- Claim government partnership/integration without evidence.
- Convert recommendations into physical action.

### 16.2 GIS/data agent

May:

- Extract/validate OSM data.
- Register assets/sources.
- Create manifests and import/replay pipelines.

Must not:

- Claim non-local data is local.
- Ignore license/attribution.
- Insert source records without provenance.

### 16.3 Backend/twin-core agent

May:

- Implement schemas, validation, APIs, persistence, WebSockets.

Must not:

- Mix observed/predicted/simulated states.
- Bypass validation.
- Add unapproved services/infrastructure.

### 16.4 Simulation agent

May:

- Build SUMO network, demand, scenarios, KPI extraction.

Must not:

- Claim simulation is field validation.
- Change current state with scenario output.
- Add physical-control integration.

### 16.5 ML agent

May:

- Build features, baselines, XGBoost models, metrics, uncertainty, explanations.

Must not:

- Skip baseline/evaluation/model card.
- Add deep models without approval/evidence.
- Claim pilot-local performance without local validation.

### 16.6 UI/UX agent

May:

- Build dashboard screens/components based on specifications.

Must not:

- Hide provenance/quality/limitations.
- Change semantic color meanings.
- Use unapproved visual style/typography/spacing.
- Make simulation look live.

### 16.7 Platform agent

May:

- Build Compose, CI, health/logging/security configuration.

Must not:

- Add Kubernetes/Kafka/cloud dependencies without decision record.
- Expose secrets/brokers/databases publicly without controls.

### 16.8 Research/delivery agent

May:

- Design experiments, reports, figures, demo, paper material.

Must not:

- Cherry-pick favorable results.
- Overstate novelty, accuracy, municipal readiness, funding, or patentability.

---

## 17. Escalation rules

Stop implementation and ask for a decision when:

- The study-area boundary changes.
- A required dataset is unavailable, restricted, or incompatible.
- Data licensing is unclear.
- A model cannot be evaluated responsibly.
- A proposed feature requires a new technology/service.
- Schema/API change would be breaking.
- A simulation result conflicts with intended narrative.
- UI requirements conflict with provenance/accessibility rules.
- Security/privacy risk is discovered.
- Requirements suggest physical control or sensitive data processing.

### Escalation response format

```text
Issue:
Affected requirement/module:
What is known:
What is uncertain:
Options:
Recommendation:
Risk if unresolved:
Decision needed from:
```

Do not quietly choose the easiest workaround when it changes validity, safety, scope, or architecture.

---

## 18. Definition of done for any contribution

A contribution is complete only when:

- [ ] It maps to an approved requirement/roadmap task/deliverable.
- [ ] It follows approved architecture and design system.
- [ ] It has relevant tests or verifiable evidence.
- [ ] It handles normal and failure states.
- [ ] It preserves provenance and state separation.
- [ ] It does not create unsupported claims.
- [ ] It updates documentation where needed.
- [ ] It contains no secrets or restricted data.
- [ ] It is reproducible by documented steps.
- [ ] It is reviewed or self-checked against this file.

---

## 19. Final operating statement

> Every contributor must treat this platform as a governance-support research pilot, not as a decorative smart-city demo. Build the smallest correct system that preserves data provenance, evaluates models honestly, separates simulation from reality, supports human review, and produces reproducible evidence. If a feature makes the system look more advanced but weakens clarity, safety, validity, maintainability, or scope discipline, do not add it.
