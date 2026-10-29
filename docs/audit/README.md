# Platform Engineering Audit: Production Readiness

- **Audit date:** 2026-10-29
- **Scope:** backend (FastAPI services, ingestion, API), database (PostgreSQL/TimescaleDB and SQLite dual path), ML and simulation, frontend (React/TypeScript, Cesium, Mapbox), tests, CI, infrastructure, and uncommitted work in progress.
- **Target:** production-ready pilot in under 4 weeks.

## 1. Executive verdict

The platform is broad and well structured at the module level, but it is **not production ready**. The main blocker is data honesty, not missing features:

1. **Synthetic data is written into the authoritative twin state.** The default telemetry streamer (`TELEMETRY_STREAMER_MODE=SIMULATION`, enabled by default), the energy topology engine and the SPaT adapter upsert random-number-generated values into `entity_current_state`. That breaks the state separation invariant.
2. **The frontend fabricates additional motion.** `App.tsx` jitters speeds and kW with `Math.random()` whenever the WebSocket is quiet for 2.2 s, and stamps the values with the client clock.
3. **Several reported metrics are invented**:
   - conformal coverage constants
   - 30m/60m benchmark horizons built from noise
   - report generator LIVE/REPLAY/PREDICTED counts
   - fallback MAE values
   - SUMO KPIs that collapse to the constant `[145.0]`
4. **No API endpoint enforces authentication.** Authorization, approval (magic-link minting), simulator control and self-registration are all open. A default JWT secret is committed.
5. **The persistence layer is split.** Some services write to raw `sqlite3` files even when PostgreSQL is primary. The `timing_recommendations` schema differs between dialects, so Postgres inserts fail silently.
6. **Pilot identifiers are hardcoded across generic code paths** (backend services, seeds, ML, frontend), which violates the corridor generalization invariant.

## 2. Document index

| # | Document | Focus |
|---|---|---|
| 01 | [01_STATE_SEPARATION_AND_PROVENANCE.md](01_STATE_SEPARATION_AND_PROVENANCE.md) | Observed / SIMULATION / PREDICTED separation, provenance mislabeling, fabricated values |
| 02 | [02_SECURITY_AND_AUTH.md](02_SECURITY_AND_AUTH.md) | Authentication, authorization, secrets, tokens, transport security |
| 03 | [03_DATABASE_AND_PERSISTENCE.md](03_DATABASE_AND_PERSISTENCE.md) | Schema drift, migrator, dead tables, timestamps, indexes, seeds |
| 04 | [04_BACKEND_SERVICES_AND_API.md](04_BACKEND_SERVICES_AND_API.md) | Service bugs, async issues, API contract and fallback behavior |
| 05 | [05_ML_AND_SIMULATION.md](05_ML_AND_SIMULATION.md) | Splits, conformal, baselines, drift, SHAP, SUMO, evaluation honesty |
| 06 | [06_DOMAIN_LOGIC_TRAFFIC_ELECTRICAL.md](06_DOMAIN_LOGIC_TRAFFIC_ELECTRICAL.md) | Webster, LOS/HCM, SPaT, power balance, feeder thermal, bounds |
| 07 | [07_FRONTEND.md](07_FRONTEND.md) | Mock data, dead UI, React bugs, provenance display, copy |
| 08 | [08_INTEGRATION_GAPS.md](08_INTEGRATION_GAPS.md) | Frontend to backend to database disconnections |
| 09 | [09_HARDCODING_AND_GENERALIZATION.md](09_HARDCODING_AND_GENERALIZATION.md) | Pilot identifiers, magic numbers, config extraction |
| 10 | [10_TESTS_CI_INFRA.md](10_TESTS_CI_INFRA.md) | Hermeticity, weak tests, CI coverage, compose, hooks |
| 11 | [11_WORK_IN_PROGRESS_REVIEW.md](11_WORK_IN_PROGRESS_REVIEW.md) | Review of the currently uncommitted changes |
| 12 | [12_PRODUCTION_READINESS_ROADMAP.md](12_PRODUCTION_READINESS_ROADMAP.md) | 4 week remediation schedule, exit criteria, issue mapping |

## 3. Severity model

| Severity | Meaning |
|---|---|
| CRITICAL | Violates a non-negotiable invariant, fabricates data shown as real, or allows unauthenticated privileged actions. Blocks any pilot claim. |
| HIGH | Produces wrong results, silent data loss, or major functional disconnection. Must be fixed before production. |
| MEDIUM | Incorrect behavior in edge cases, maintainability or configurability gaps that will hurt operation. |
| LOW | Hygiene, documentation drift, minor UX or code quality. |

## 4. Finding counts (approximate)

| Area | Critical | High | Medium | Low |
|---|---|---|---|---|
| State separation and provenance | 5 | 6 | 4 | 1 |
| Security and auth | 7 | 5 | 5 | 2 |
| Database and persistence | 3 | 7 | 7 | 4 |
| Backend services and API | 1 | 6 | 9 | 6 |
| ML and simulation | 7 | 9 | 7 | 3 |
| Domain logic (traffic, electrical) | 1 | 6 | 7 | 3 |
| Frontend | 3 | 14 | 14 | 7 |
| Integration gaps | 2 | 7 | 6 | 2 |
| Hardcoding and generalization | 0 | 12 | 8 | 2 |
| Tests, CI, infra | 2 | 6 | 7 | 4 |

## 5. Finding ID convention

Each finding has a stable identifier for issue tracking:

- `SP-xx` state separation and provenance
- `SEC-xx` security
- `DB-xx` database and persistence
- `BE-xx` backend services and API
- `ML-xx` machine learning, `SIM-xx` simulation
- `DOM-xx` domain logic
- `FE-xx` frontend
- `INT-xx` integration gaps
- `HC-xx` hardcoding and generalization
- `TST-xx` tests, CI, infra
- `WIP-xx` work in progress review

Line numbers are taken from the working tree at the audit date. Where marked with `~`, the line is approximate and the surrounding block should be inspected.

## 6. What is already correct (keep)

- `StateProjector` gates LIVE/REPLAY only for MQTT-sourced traffic into current state (`backend/ingestion/state_projector.py` ~67-70).
- Speed bounds 0-120 km/h and freshness constants 180 s / 900 s exist in `backend/core/constants.py`.
- Offline feature rolling windows use `closed="left"`, and targets use a forward shift, so there is no contemporaneous leakage in offline features.
- Persistence baseline MAE and RMSE are computed on a chronological holdout.
- TreeSHAP attributions come from real XGBoost `pred_contribs` when the artifact loads.
- Weather offline fallback is honestly tagged `SIMULATION`.
- CORS defaults are scoped to localhost.
- Caches, `.db` files, `dist/` and `.env` are not tracked in git. The pre-commit hook blocks em dashes and emojis.
- CI runs `pytest tests/` and `npm run build`.
