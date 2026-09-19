# Master Solidification & Completion Plan
## Closing the Contract Gaps Across Foundation, UI/UX, Data, and Architecture

> **Document Class:** Comprehensive Implementation & Solidification Plan  
> **Source Documents:** `PROJECT_CONTEXT.md`, `PRD.md`, `TECHNICAL_ARCHITECTURE.md`, `DATA_AND_ML_PLAN.md`, `UI_UX_SPEC.md`, `DESIGN_SYSTEM.md`, `ROADMAP.md`, `DELIVERABLES.md`  
> **Goal:** Transition the platform from a foundational critical-path prototype to 100% faithful execution of all approved contract documents.

---

## 1. Audit Findings: Prototype Reality vs. Contract Specifications

An honest audit of the current codebase against the root contract files confirms that **the basic skeleton and critical path are operational, but several major functional, architectural, and visual requirements remain incomplete or mocked**:

| Domain | Contract Specification | Current Reality in Code | Completion Level |
|---|---|---|:---:|
| **Primary Views** (`UI_UX_SPEC.md` §5) | 7 standalone dedicated views: Operations, Traffic Analytics, Energy Analytics, Environment Context, Scenario Studio, Recommendations, System Health. | Single dashboard screen with Operations map; Scenarios and Advisories opened as modal popups. Dedicated analytics pages are missing. | ~30% |
| **Theme System** (`DESIGN_SYSTEM.md` §4) | Mandatory Light theme, Dark theme, and manual user toggle with tokens (`[data-theme="light"]`, `[data-theme="dark"]`). | Hardcoded dark mode only. No theme switcher exists. | ~40% |
| **Accessibility (WCAG 2.1 AA)** (`DESIGN_SYSTEM.md` §11) | ARIA live regions for WebSocket tickers, "Skip to main content" link, focus trapping in dialogs, `prefers-reduced-motion` media queries. | Semantic HTML and contrast exist, but live regions, skip links, and motion suppression are missing. | ~35% |
| **Temporal Playback & Scrubber** (`UI_UX_SPEC.md` §7.3) | Interactive timeline scrubber to rewind and inspect historical corridor states at specific past timestamps. | Real-time current state and static sparklines only; no interactive playback slider. | ~15% |
| **Multi-Segment Comparison** (`UI_UX_SPEC.md` §7.4) | Side-by-side comparison matrix for multiple selected road segments. | Drawer only inspects one entity at a time. | ~20% |
| **Data Manifests & Pipeline** (`DATA_AND_ML_PLAN.md` §3, §4) | Explicit YAML/JSON dataset manifests in `data/manifests/` for each ingested source with license, access date, and geography. | Raw data files exist in `data/samples/`, but formal manifest catalog is incomplete. | ~40% |
| **Data Quarantine Table** (`DATA_AND_ML_PLAN.md` §5.4) | Dead-letter database table (`quarantine_observations`) capturing and tracking malformed/stale/out-of-bounds telemetry. | Validator logs rejection to console, but records are not persisted in a formal quarantine schema. | ~30% |
| **Backend Multi-Container Stack** (`TECHNICAL_ARCHITECTURE.md` §3) | Live PostgreSQL + TimescaleDB + PostGIS + Mosquitto MQTT container cluster running via Docker. | Running on local SQLite / JSON file fallbacks with in-memory rolling statistics. | ~50% |

---

## 2. Master Task List for Full Solidification

### Track 1: Complete UI/UX Navigation & Dedicated Views (`UI_UX_SPEC.md`)
* [x] **P1-A: Top-Level Navigation Shell & 7 Dedicated Views** *(COMPLETED — Commit 67d2802)*
  - Refactor `frontend/src/App.tsx` and `Header.tsx` to introduce a primary navigation bar supporting the 7 mandatory views:
    1. **Operations** (Map, corridor overview, drawer, live tickers)
    2. **Traffic Analytics** (Dedicated speed history, 15m forecast horizon, sensor health, segment rankings)
    3. **Energy Analytics** (Building power demand, commercial mall load breakdown, peak tariff warnings)
    4. **Environment Context** (AQI station gauges, PM2.5/PM10 spikes, ambient weather correlations)
    5. **Scenario Studio** (Full-page sandbox comparing baseline vs coordinated signals with TraCI runs)
    6. **Recommendations & Governance** (Full-page advisory audit log, human review modal, institutional memorandum export)
    7. **System & Data Health** (Ingestion latency telemetry, schema compliance rates, subsystem uptime indicators)

* [x] **P1-B: Interactive Historical Time Scrubber** *(COMPLETED)*
  - Implement an interactive timeline scrubber bar at the bottom of the map view allowing operators to scrub between $t - 12\text{ hours}$ and live state.
  - Automatically query `/api/v1/state/snapshot` and dynamically render past corridor congestion states on MapLibre.


* [ ] **P1-C: Multi-Segment Comparative Drawer**
  - Allow multi-selection of road segments (e.g. Nagar Road Eastbound vs. Westbound) to render side-by-side comparative speed and delay charts.

---

### Track 2: Complete Design System & WCAG 2.1 AA Accessibility (`DESIGN_SYSTEM.md`)
* [ ] **P2-A: Light / Dark Theme Switcher**
  - Implement the full token set for `:root, [data-theme="light"]` and `[data-theme="dark"]` in `frontend/src/index.css`.
  - Add an interactive theme toggle icon button in `Header.tsx` that persists preference in `localStorage` and respects `prefers-color-scheme`.
  - Update MapLibre GL map style to seamlessly toggle between light cartography and dark operational tiles.

* [ ] **P2-B: Full Accessibility Hardening**
  - Add `aria-live="polite"` live announcement regions for incoming WebSocket updates and alert counters.
  - Add a visible-on-focus "Skip to main content" link (`#main-content`) at the top of the DOM.
  - Add `prefers-reduced-motion` media queries disabling camera flight easing and spinner rotations.
  - Implement full keyboard trapping (`Tab` cycle, `Escape` key close) across all modals and drawers.

---

### Track 3: Data Engineering, Manifests & Quarantine Schema (`DATA_AND_ML_PLAN.md`)
* [ ] **P3-A: Dataset Manifest Catalog (`data/manifests/`)**
  - Create standardized manifest files for:
    - `manifest_osm_network.json` (OpenStreetMap corridor geometry)
    - `manifest_pune_traffic_history.json` (Corridor synthetic/replayed speed series)
    - `manifest_phoenix_energy.json` (Commercial retail load archetype)
    - `manifest_pune_air_quality.json` (Corridor air quality monitoring data)
  - Expose dataset catalog via `GET /api/v1/datasets/manifests`.

* [ ] **P3-B: Formal Data Quarantine Table & Dead-Letter Queue**
  - Create database schema `quarantine_observations` in PostgreSQL/SQLite.
  - Update `IngestionValidator` to write rejected events (out-of-bounds speed, future timestamps, schema errors) to the quarantine table with explicit `rejection_reason`.
  - Expose `GET /api/v1/health/quarantine` to inspect quarantined records in the System Health view.

---

### Track 4: Backend Infrastructure & Production Fallback Hardening (`TECHNICAL_ARCHITECTURE.md`)
* [ ] **P4-A: Multi-Storage Resilient Persistence Layer**
  - Ensure the database layer smoothly migrates between SQLite (zero-dependency local development) and PostgreSQL/TimescaleDB/PostGIS without any manual code edits.
  - Implement automatic database table schema initialization on startup.

* [ ] **P4-B: Native Continuous Aggregates & Background Telemetry Worker**
  - Implement background 15-minute rolling average aggregators in Python that replicate TimescaleDB continuous aggregates when running in SQLite mode.
  - Build an embedded in-process telemetry simulator thread that automatically streams realistic vehicle and sensor updates if an external MQTT broker is not reachable.

---

## 3. Phased Execution Sequence

```text
Phase A: Design System & Full Accessibility (Light/Dark themes, ARIA live, reduced motion, skip-link)
   ↓
Phase B: Complete Navigation & 7 Dedicated Views (Operations, Traffic, Energy, Environment, Scenarios, Advisories, Health)
   ↓
Phase C: Temporal Time Scrubber & Multi-Segment Comparison
   ↓
Phase D: Data Manifests & Dead-Letter Quarantine Engine
   ↓
Phase E: Backend Resilience, In-Process Streamer & Full Validation
```

---

## 4. Verification Plan

* **Visual & Theming:** Toggle Light/Dark modes in the UI; verify all cards, text, badges, and maps adapt without contrast failures.
* **Navigation:** Click through all 7 navigation tabs; verify smooth routing and dedicated analytics views.
* **Accessibility:** Test with screen reader simulator and keyboard navigation (`Tab`, `Escape`, Skip link).
* **Fault Tolerance:** Feed an invalid telemetry payload; verify it appears in the Quarantine inspection drawer.
* **Test Suite:** Execute full `pytest` suite ensuring 100% pass across all new modules.
