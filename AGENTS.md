# Agent Operating Rules
## Digital Twin-Enabled Smart City Analytics Platform

> **Document Status:** Mandatory Execution Contract  
> **Core Principle:** Build an evidence-backed urban decision-support pilot. Never overclaim, never overengineer, never hide limitations, and never violate approved architectural invariants.

---

## 1. Approved MVP Scope & Pilot Boundary

- **Pilot Corridor:** Viman Nagar Chowk ↔ Somnath Nagar Chowk (1.8 km arterial, Nagar Road, Pune, Maharashtra).
- **Assets:** 2 signalized intersections (`INT-VN-01`, `INT-SN-01`), 10 road segments (`SEG-NR-EB-01..03`, `SEG-NR-WB-01..03`, approach legs), 1 commercial building entity (`BLD-PHOENIX-01`).
- **Modes:** `REPLAY` and `SIMULATION` (with optional `LIVE` stream if permitted sensor exists).
- **Prohibited in MVP:** Physical traffic signal actuation, CCTV/video ingestion, facial/plate recognition, individual GPS traces, blockchain, and LLM-driven autonomous control.

---

## 2. Approved Technical Stack

Do not replace any approved component without an approved Architecture Decision Record (ADR):

| Layer | Approved Technology | Role |
|---|---|---|
| **Frontend** | React 18 + TypeScript + Vite | Civic operations dashboard |
| **Geospatial Map** | MapLibre GL JS + OpenStreetMap | 2D vector map canvas (3D is strictly deferred) |
| **Backend Core** | Python 3.11 + FastAPI modular monolith | Async REST APIs (`/api/v1`), WebSockets, background consumers |
| **Message Transport**| Eclipse Mosquitto (MQTT 3.1.1/5.0) | Sensor telemetry transport (`nagartwin/#`, `dt/v1/corridor/#`) |
| **Persistence** | PostgreSQL 16 + TimescaleDB + PostGIS | Canonical entity store, spatial queries, hypertable time-series |
| **Local Resilient** | SQLite 3 (WAL mode) + aiosqlite | Zero-dependency local persistence with automatic failover |
| **Simulation** | Eclipse SUMO 1.20+ via TraCI | Baseline (`SCEN-BASE-01`) vs adaptive green (`SCEN-INT-01`) simulation |
| **Traffic ML** | Persistence baseline + XGBoost Regressor | 15-minute speed forecast with conformal bounds & TreeSHAP |
| **Energy ML** | Same-hour baseline + XGBoost Regressor | 60-minute commercial power forecast with conformal bounds |
| **Decision Support** | Deterministic Python Rule Engine | Transparent rules with mandatory human authorization |
| **Deployment** | Docker Compose with profiles | Containerized stack (`--profile full` for MinIO/MLflow) |

---

## 3. Non-Negotiable Architectural Invariants

1. **System of Record:** PostgreSQL/TimescaleDB (or resilient local SQLite engine) is authoritative. MQTT is transport only.
2. **State Separation Invariant:** Observed (`LIVE`/`REPLAY`), `SIMULATION`, and `PREDICTED` records are strictly separated in distinct tables. Forecasts and simulations must **never** overwrite observed twin state.
3. **Strict Non-Actuation:** The platform is read-only decision support. Recommendations are advisory and require human authorization outside the platform before any field action.
4. **Mandatory Provenance:** Every dynamic value returned by APIs or displayed in the UI must specify `sourceMode`, `observedAt`/`generatedAt`, unit, and quality status.

---

## 4. Provenance Modes & Data Honesty

Use only these standardized provenance source modes:
- `LIVE`: Verified direct feed from on-corridor sensor or permitted real-time API.
- `REPLAY`: Historical corridor telemetry played back chronologically.
- `SIMULATION`: Output of behavioral/physics simulation (e.g. SUMO). Never claim as observed reality.
- `PREDICTED`: Machine learning forecast output. Never call a prediction a measurement.
- `STALE`: Valid observation exceeding freshness threshold (>180s traffic, >900s energy).
- `INVALID`: Rejected by schema, physical bounds (speed 0–120 km/h), or future timestamp validation.

**Data Honesty Rules:**
- Never call replayed data "live".
- Never call regional Pune survey counts (Alankar/Jehangir/RTO) exact Viman Nagar counts.
- Never call UCI electricity benchmark data live building meter readings.
- Never claim SUMO simulation outputs prove real-world commuter outcomes.

---

## 5. Machine Learning & Simulation Standards

- **Splits:** Strict chronological 80/10/10 split. Random shuffling is strictly prohibited.
- **Baselines:** Every model must be evaluated against a persistence baseline on the chronological holdout test set (MAE & RMSE required).
- **Uncertainty & XAI:** Predictions must provide conformal confidence intervals (80%/90%) and top-5 TreeSHAP feature attributions.
- **Drift Monitoring:** Evaluate Population Stability Index (PSI) against training distribution (`STABLE` < 0.10, `WARNING` 0.10–0.25, `DRIFT` $\ge$ 0.25).
- **Simulation Rules:** Use only approved scenario templates. Results are tagged `SIMULATION` and kept separate from operational state.

---

## 6. Frontend & Design System Invariants

- **Aesthetic:** Civic decision-support infrastructure (neutral surfaces, deep teal primary `#006B6F` / `#3FB4B8`).
- **Typography:** Satoshi font stack with tabular numerals (`font-variant-numeric: tabular-nums lining-nums;`). Strictly **no text under 12px**.
- **Spacing:** 4px base scale (`--space-1: 4px` to `--space-16: 64px`).
- **Accessibility:** WCAG 2.2 AA compliant (minimum 4.5:1 text contrast, visible 2px focus rings, `@media (prefers-reduced-motion)`).
- **Prohibited UI Gimmicks:** Purple AI gradients, glowing blobs/orbs, neon grids, 3D charts, or "AI decided" command copy.

---

## 7. Definition of Done Checklist

A contribution is complete only when:
- [ ] It maps to an approved requirement and preserves all architectural invariants.
- [ ] It handles normal, stale, empty, and error failure states.
- [ ] It strictly separates observed, predicted, and simulated state classes.
- [ ] All automated tests pass (`pytest tests/` 100% pass rate).
- [ ] Frontend builds cleanly with 0 TypeScript/build errors (`npm run build`).
- [ ] It contains zero hardcoded secrets or unlicensed data.
