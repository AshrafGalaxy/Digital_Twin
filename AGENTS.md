# Agent Operating Rules
## Digital Twin-Enabled Smart City Analytics Platform

> **Document Status:** Mandatory Execution Contract  
> **Core Principle:** Build an evidence-backed urban decision-support pilot. Never overclaim, never overengineer, never hide limitations, and never violate approved architectural invariants.

---

## 1. Operating Scope & Boundaries

- **Corridor Boundary:** Viman Nagar Chowk ↔ Somnath Nagar Chowk (1.8 km arterial, Nagar Road, Pune, Maharashtra).
- **Physical Assets:** 2 signalized intersections (`INT-VN-01`, `INT-SN-01`), 10 road segments (`SEG-NR-EB-01..03`, `SEG-NR-WB-01..03`, approach legs), 1 commercial building entity (`BLD-PHOENIX-01`).
- **Telemetry Modes:** `REPLAY` (historical corridor telemetry) and `SIMULATION` (SUMO physics feeds).
- **Strict Prohibitions:** Physical traffic signal actuation, CCTV/video ingestion, facial/plate recognition, individual GPS traces, blockchain, and LLM-driven autonomous actuation.

---

## 2. Non-Negotiable Architectural Invariants

1. **System of Record:** PostgreSQL/TimescaleDB (or resilient local SQLite engine) is authoritative. MQTT is transport only.
2. **State Separation Invariant:** Observed (`LIVE`/`REPLAY`), `SIMULATION`, and `PREDICTED` records are strictly separated into distinct tables. Predictions and simulations must **never** overwrite observed twin state.
3. **Strict Non-Actuation:** The platform is read-only decision support. Recommendations are advisory and require human authorization outside the platform before any field action.
4. **Mandatory Provenance:** Every dynamic value returned by APIs or displayed in the UI must specify `sourceMode`, `observedAt`/`generatedAt`, unit, and quality status.
5. **Strictly No Emojis:** Never use emojis in UI components, toolbars, buttons, badges, tables, tooltips, or alerts. Use professional vector iconography (Lucide React) or clean, professional text instead.

---

## 3. Provenance Modes & Data Honesty

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

## 4. Machine Learning & Simulation Standards

- **Splits:** Strict chronological 80/10/10 split. Random shuffling is strictly prohibited.
- **Baselines:** Every model must be evaluated against a persistence baseline on the chronological holdout test set (MAE & RMSE required).
- **Uncertainty & XAI:** Predictions must provide conformal confidence intervals (80%/90%) and top-5 TreeSHAP feature attributions.
- **Drift Monitoring:** Evaluate Population Stability Index (PSI) against training distribution (`STABLE` < 0.10, `WARNING` 0.10–0.25, `DRIFT` $\ge$ 0.25).
- **Simulation Rules:** Use only approved scenario templates. Results are tagged `SIMULATION` and kept separate from operational state.

---

## 5. Workspace Hygiene & Script Lifecycle

- **No Transient Scripts:** Never store one-off or throwaway utility scripts in `scripts/` or any repository directory.
- **Ephemeral Scratch:** All exploratory or debugging scripts must be run ephemerally and deleted immediately upon completion.
- **Zero Cache Check-in:** Always purge transient caches (`__pycache__`, `.pytest_cache`, `dist/`) before committing.
- **Standardized Structure & Pre-Approval:** Maintain standard directory conventions; never introduce non-standard folder names or major structural changes without detailing them in the implementation plan and securing explicit user approval.

---

## 6. Test Hermeticity & CI Invariants

- **Hermetic Test Isolation:** Tests must be 100% self-contained and order-invariant. Never rely on alphabetical file execution order or pre-existing local database files (`data/digital_twin.db`).
- **Session-Scoped Schema Provisioning:** All test runs on clean CI environments must provision schemas and authoritative seed records via a session-scoped fixture in `tests/conftest.py` (`autouse=True`) invoking `init_db_schema()`.
- **Order-Invariance Contract:** Every individual test file must pass when executed in total isolation (`pytest tests/<file>.py`) on a fresh checkout with no pre-existing `.db` files.

---

## 7. Definition of Done Checklist

A contribution is complete only when:
- [ ] It maps to an approved requirement and preserves all architectural invariants.
- [ ] It handles normal, stale, empty, and error failure states.
- [ ] It strictly separates observed, predicted, and simulated state classes.
- [ ] All automated tests pass (`pytest tests/` 100% pass rate hermetically on clean runners).
- [ ] Frontend builds cleanly with 0 TypeScript/build errors (`npm run build`).
- [ ] Transient scripts, scratch files, and caches are deleted immediately after execution.
- [ ] Contains zero emojis in frontend components, toolbars, and alerts (vector icons or plain text only).
- [ ] It contains zero hardcoded secrets or unlicensed data.
- [ ] Commit messages follow concise conventional syntax (<60 chars). Strictly NEVER include the word "phase" or phase tags (e.g. "Phase 8", "P4B").
