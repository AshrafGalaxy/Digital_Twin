# Project Master Task List & Endpoint Implementation Tracker
## Digital Twin-Enabled Smart City Analytics Platform

> **Document Class:** Active Task & Endpoint Tracking Ledger  
> **Repository:** `AshrafGalaxy/Digital_Twin`  
> **Last Updated:** Post-P1-A Completion (`Commit 67d2802`)  
> **Status:** Tracks all completed deliverables, pending contract features, and endpoint-wise backend readiness.

---

## 1. Overall Solidification & Feature Progress

```text
[████████████████████████░░░░░░░░░░░░░░░░] 60% Total Scope Completed
```

- **Foundational Pipeline (Phases 0–6):** 100% Complete (`[x]`)
- **Evaluation & Benchmarks (Phase 7):** 100% Complete (`[x]`)
- **Phase 8 Core Algorithms & 3D Extrusions:** 100% Complete (`[x]`)
- **Track 1 UI/UX Dedicated Views (P1-A):** 100% Complete (`[x]`)
- **Track 1 Temporal Scrubber & Comparison (P1-B, P1-C):** Pending (`[ ]`)
- **Track 2 Theming & Accessibility (P2-A, P2-B):** Pending (`[ ]`)
- **Track 3 Data Manifests & Quarantine Schema (P3-A, P3-B):** Pending (`[ ]`)
- **Track 4 Persistence & Telemetry Streamer (P4-A, P4-B):** Pending (`[ ]`)

---

## 2. Solidification Task List (Tick Mark Tracker)

### Track 1: UI/UX Navigation & Dedicated Views (`UI_UX_SPEC.md`)
- [x] **P1-A: Top-Level Navigation Shell & 7 Dedicated Views** *(Completed)*
  - [x] Persistent 7-tab navigation bar in `Header.tsx` with active states and badge counters.
  - [x] Stateful view routing in `App.tsx` maintaining real-time telemetry and WebSocket state.
  - [x] Operations View layout with 2D/3D map, corridor metrics strip, and drawer.
  - [x] Traffic Analytics View (`TrafficAnalyticsView.tsx`) with 15m forecast, TreeSHAP, and congestion rankings.
  - [x] Energy Analytics View (`EnergyAnalyticsView.tsx`) with Phoenix load profile, 60m forecast, and UI_UX_SPEC §10.3 caveat.
  - [x] Environment Context View (`EnvironmentContextView.tsx`) with NAAQS AQI, PM2.5/PM10, Isolation Forest surge detection, and regional caveat.
  - [x] Scenario Studio View (`ScenarioStudioView.tsx`) with full-page simulation sandbox, green split / demand sliders, and KPI delta table.
  - [x] Recommendations View (`RecommendationsView.tsx`) with advisory filters, human review form, and immutable audit logs.
  - [x] System Health View (`SystemHealthView.tsx`) with subsystem health, NGSI-LD schema validation rates (100%), and provenance matrix.
- [x] **P1-B: Interactive Historical Time Scrubber** *(Completed)*
  - [x] Bottom playback bar on Operations View allowing operators to rewind up to 12 hours.
  - [x] Interactive timeline scrubber slider with play/pause and playback speed multipliers (1x, 2x, 5x, 10x).
  - [x] Backend historical snapshot endpoint (`GET /api/v1/state/snapshot`) updating segment colors and metrics dynamically.
- [ ] **P1-C: Multi-Segment Comparative Drawer** *(NEXT)*
  - [ ] Multi-select toggle for road segments (e.g., Nagar Road EB vs. Nagar Road WB).
  - [ ] Side-by-side comparative speed, delay, and queue-length charts.

---

### Track 2: Design System & WCAG 2.1 AA Accessibility (`DESIGN_SYSTEM.md`)
- [ ] **P2-A: Dual Light / Dark Theme Switcher**
  - [ ] Implement complete token set for `:root, [data-theme="light"]` and `[data-theme="dark"]` in `index.css`.
  - [ ] Interactive theme switcher toggle in `Header.tsx` with `localStorage` persistence and OS preference detection.
  - [ ] MapLibre GL style switcher toggling between light civic basemap and dark operations tiles.
- [ ] **P2-B: Full Accessibility Hardening (WCAG 2.1 AA)**
  - [ ] Add `aria-live="polite"` regions for incoming WebSocket updates and alert badges.
  - [ ] Add visible-on-focus "Skip to main content" link (`#main-content`) at DOM root.
  - [ ] Add `prefers-reduced-motion` media queries suppressing camera transitions and spinner animations.
  - [ ] Keyboard focus trapping and `Escape` key listeners on all dialogs and drawers.

---

### Track 3: Data Engineering, Manifests & Quarantine Schema (`DATA_AND_ML_PLAN.md`)
- [ ] **P3-A: Dataset Manifest Catalog (`data/manifests/`)**
  - [ ] Formal JSON/YAML manifests for OSM network, synthetic traffic, commercial energy, and CAAQMS air quality.
  - [ ] Backend API endpoint `GET /api/v1/datasets/manifests` and manifest viewer in System Health view.
- [ ] **P3-B: Formal Data Quarantine Table & Dead-Letter Queue**
  - [ ] Database table `quarantine_observations` in PostgreSQL/SQLite.
  - [ ] Update `IngestionValidator` to persist rejected events (stale, out-of-bounds, invalid schema) with rejection reason.
  - [ ] Backend API endpoint `GET /api/v1/health/quarantine` for operator inspection.

---

### Track 4: Backend Infrastructure & Production Fallback Hardening (`TECHNICAL_ARCHITECTURE.md`)
- [ ] **P4-A: Multi-Storage Resilient Persistence Layer**
  - [ ] Dynamic database adapter switching seamlessly between SQLite (zero-dependency local dev) and PostgreSQL/TimescaleDB/PostGIS.
  - [ ] Automatic database table DDL migration and index creation on startup.
- [ ] **P4-B: Native Continuous Aggregates & Background Telemetry Worker**
  - [ ] Background 15-minute rolling average aggregators replicating TimescaleDB continuous aggregates.
  - [ ] Embedded in-process telemetry simulator thread generating corridor streams if external MQTT broker is offline.

---

## 3. Endpoint-Wise Implementation Status Matrix

| Method | Route Path | Subsystem / Domain | Contract Purpose | Status |
|:---:|---|---|---|:---:|
| `GET` | `/` | Root | Service info and documentation links | [x] Implemented |
| `GET` | `/api/v1/health` | Platform Health | Deep health diagnostics, subsystem indicators | [x] Implemented |
| `GET` | `/api/v1/study-area` | Corridor GIS | GeoJSON pilot corridor boundary polygon | [x] Implemented |
| `GET` | `/api/v1/assets/intersections` | Corridor GIS | Core intersections (Viman Nagar, Somnath Nagar) | [x] Implemented |
| `GET` | `/api/v1/assets/segments` | Corridor GIS | Road segments geometry and speed limits | [x] Implemented |
| `GET` | `/api/v1/assets/sensors` | Ingestion / Assets | Traffic loop detector registry and metadata | [x] Implemented |
| `GET` | `/api/v1/assets/energy` | Ingestion / Assets | Phoenix Marketcity commercial building entity | [x] Implemented |
| `GET` | `/api/v1/state/current` | Twin State | Authoritative current state of all entities | [x] Implemented |
| `GET` | `/api/v1/state/history` | Telemetry History | Time-series query by road segment | [x] Implemented |
| `WS` | `/api/v1/stream/state` | Streaming Transport | Real-time WebSocket state broadcasting | [x] Implemented |
| `GET` | `/api/v1/scenarios/templates` | Simulation | Approved SUMO intervention templates | [x] Implemented |
| `POST` | `/api/v1/scenarios/run` | Simulation | Execute microscopic SUMO simulation with TraCI | [x] Implemented |
| `GET` | `/api/v1/scenarios/runs` | Simulation | Audit trail of past simulation results | [x] Implemented |
| `GET` | `/api/v1/forecasts/traffic/{segment_id}` | ML Forecasting | 15m XGBoost speed forecast + Conformal intervals | [x] Implemented |
| `GET` | `/api/v1/forecasts/energy/{building_id}` | ML Forecasting | 60m XGBoost power demand forecast + TreeSHAP | [x] Implemented |
| `GET` | `/api/v1/forecasts/models` | ML Registry | Active forecasting model metadata & test metrics | [x] Implemented |
| `GET` | `/api/v1/recommendations` | Decision Support | Advisory list with domain and status filtering | [x] Implemented |
| `GET` | `/api/v1/recommendations/summary` | Decision Support | Advisory counts by domain and priority | [x] Implemented |
| `GET` | `/api/v1/recommendations/{id}` | Decision Support | Detailed evidence and audit trail for advisory | [x] Implemented |
| `POST` | `/api/v1/recommendations/{id}/review` | Governance | Submit human governance review decision | [x] Implemented |
| `POST` | `/api/v1/recommendations/evaluate` | Rule Engine | Re-evaluate active state against deterministic rules | [x] Implemented |
| `GET` | `/api/v1/ngsi-ld/entities` | Interoperability | FIWARE / NGSI-LD 1.3 canonical export | [x] Implemented |
| `GET` | `/api/v1/ngsi-ld/entities/{entity_id}` | Interoperability | Single entity NGSI-LD representation | [x] Implemented |
| `GET` | `/api/v1/state/snapshot` | Temporal Playback | Query corridor state snapshot at exact timestamp $t$ | [x] Implemented |
| `POST` | `/api/v1/stream/replay/control` | Telemetry Control | Pause, play, scrub, and speed multiplier control | [ ] **Upcoming** |
| `GET` | `/api/v1/datasets/manifests` | Data Governance | List standardized dataset manifests with licenses | [ ] **Upcoming (P3-A)** |
| `GET` | `/api/v1/datasets/manifests/{id}` | Data Governance | Get specific dataset manifest details | [ ] **Upcoming (P3-A)** |
| `GET` | `/api/v1/health/quarantine` | Quality Assurance | Inspect dead-letter quarantined telemetry events | [ ] **Upcoming (P3-B)** |
| `POST` | `/api/v1/environment/anomaly/evaluate` | Anomaly Detection | Direct API evaluation of ambient air quality readings | [ ] **Upcoming** |

---

## 4. What's Completed vs. What's Left vs. What's Next

### What's Completed:
1. **Full-Page UI Architecture (P1-A):**
   - 7 distinct views deployed and accessible via top-level tab navigation.
   - Dedicated views for Traffic, Energy, Environment, Scenarios, Recommendations, and System Health.
   - Built and verified with TypeScript zero-warning build (`npm run build`).
2. **Interactive Historical Time Scrubber (P1-B):**
   - Docked playback bar on Operations View with timeline slider ($-12\text{ hours}$ to Live).
   - Play/pause auto-advance and speed multipliers (1x, 2x, 5x, 10x).
   - Dedicated backend snapshot API (`GET /api/v1/state/snapshot`) with strict `REPLAY` provenance.
   - Dynamic MapLibre corridor layer recoloring and corridor telemetry aggregates updating upon scrubbing.
3. **Phase 8 Core Mathematical Extensions:**
   - 90% and 95% Conformal Prediction uncertainty intervals calibrated on test residuals.
   - TreeSHAP local feature attribution (`pred_contribs=True`).
   - Multivariate Isolation Forest atmospheric anomaly detector.
   - FIWARE NGSI-LD v1.3 export endpoints.
   - 3D corridor building extrusions in MapLibre.
4. **Backend Test Suite:**
   - 37 of 37 unit, integration, and benchmark tests passing in `pytest`.

### What's Left:
1. **Multi-Segment Comparison Drawer (P1-C)** to compare arterial directions side-by-side.
2. **Light/Dark Theming Engine & Accessibility (P2-A, P2-B)** for complete WCAG 2.1 AA compliance.
3. **Data Manifests & Quarantine Queue (P3-A, P3-B)** for complete data honesty and governance.
4. **Multi-Storage Persistence & In-Process Streamer (P4-A, P4-B)** for resilient zero-dependency deployment.

### What's Next:
> **P1-C: Multi-Segment Comparative Drawer**  
> We will enable multi-segment selection on the Operations map and display side-by-side comparative speed, delay, and Level of Service charts in the inspection drawer.
