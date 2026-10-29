# 10. Tests, CI and Infrastructure

**Test inventory at audit date:** 183 test functions across 25 files in `tests/`. None are skipped or marked xfail.

---

## A. Test hermeticity

### TST-01 (CRITICAL) Tests share the developer database file
- **Location:** `tests/conftest.py` (sets `DATABASE_BACKEND=sqlite` but never sets `SQLITE_DB_PATH`); `backend/core/config.py` line 19 (default `data/digital_twin.db`).
- **Impact:** Results depend on whatever is in the local DB. This violates AGENTS.md Section 6 and makes failures irreproducible.
- **Fix:**
  - At the top of `conftest.py`, set `SQLITE_DB_PATH` to a `tmp_path_factory` session directory before importing backend modules.
  - Also force `TELEMETRY_STREAMER_ENABLED=false` and clear any Supabase `DATABASE_URL` from the environment.

### TST-02 (HIGH) Network-dependent test
- **Location:** `tests/test_fidelity_extensions.py` ~173-181 (calls Open-Meteo).
- **Fix:** Mock the HTTP client (`respx` or `monkeypatch`) for both the success and failure paths.

### TST-03 (HIGH) Session-scoped shared DB for mutating tests
- **Fix:** Use a function-scoped transactional fixture (begin, then rollback), or a fresh temp DB per module for mutating suites (provisioning, audit, scenarios).

### TST-04 (MEDIUM) Env leakage from local `.env`
- **Evidence:** `Settings` reads `.env`, which contains real Supabase credentials locally. A test that imports settings before conftest overrides could hit the cloud DB.
- **Fix:** In tests, set `env_file=None` through `Settings(_env_file=None)`, or set the `ENV_FILE` env var to empty.

---

## B. Test quality

### TST-05 (HIGH) Tautological assertions on hardcoded values
| Test | Problem |
|---|---|
| `test_energy_advisory_audit.py` ~34-39 | Asserts canned IDs and values that are literals in the service |
| `test_ml_forecasting.py` ~77 | `modelTestMae < persistenceMae` passes on hardcoded fallback numbers |
| `test_pilot_evaluation.py` ~50-53 | Asserts pilot name strings, length 1.8, report ID prefix |
| `test_persistence_adapter.py` ~100-118 | Asserts city name and exact pilot entity counts |
| `test_persistence_adapter.py` ~141 | Allows SIMULATION in `entity_current_state` |

**Fix:** Assert behaviors and invariants (for example "advisory references an existing entity", "MAE computed from artifact residuals", "current state only contains LIVE/REPLAY").

### TST-06 (HIGH) Missing invariant tests
Add tests for:
- SIMULATION and PREDICTED writes never reach `entity_current_state` (all writers)
- every mutating route returns 401 without a token and 403 with the wrong role
- an 80/10/10 chronological split with no index overlap
- empirical conformal coverage on test within +/- 3 points of nominal
- PSI labels STABLE / WARNING / DRIFT at the boundary values 0.0999, 0.10, 0.2499, 0.25
- Webster textbook case (DOM-01 acceptance)
- power balance with missing telemetry (DOM-16)
- no fabricated fallback (empty DB returns EMPTY quality and null values on state, LOS, power balance, report)

### TST-07 (MEDIUM) Schema test covers only 18 of 34 tables
- **Location:** `tests/test_persistence_adapter.py` (`test_schema_migrator_all_eighteen_tables`, `>= 18`).
- **Fix:** Compare against the full metadata list in both dialects.

### TST-08 (MEDIUM) No frontend tests
- **Location:** `frontend/package.json` has no `test` script.
- **Fix:** Add Vitest and React Testing Library. Minimum: an auth route guard, `ProvenancedMetric` rendering, the WS reconnect logic, and views rendering empty states with empty API responses.

### TST-09 (MEDIUM) No end-to-end smoke test
- **Fix:** Add a Playwright smoke test (login, operations view renders, select segment, run scenario, authorize advisory as operator) against compose.

### TST-10 (LOW) Docstrings reference "18 tables"
- **Fix:** Update them.

---

## C. CI

### TST-11 (HIGH) CI runs only SQLite
- **Location:** `.github/workflows/ci.yml`.
- **Fix:** Add a job with a `timescale/timescaledb-ha` (PostGIS) service container that runs the full suite with `DATABASE_BACKEND=postgresql`. This would have caught DB-01 and DB-05.

### TST-12 (HIGH) Frontend has build only, with no lint or tests
- **Fix:** Add `npm run lint` (ESLint with the react-hooks plugin) and `npm test` jobs.

### TST-13 (MEDIUM) Asset validation is syntax only
- **Location:** `ci.yml` ~80-87 (`json.load`).
- **Fix:** Validate deployment packages against a JSON Schema and check referential consistency (every approach references an existing segment, and so on).

### TST-14 (MEDIUM) No pilot-identifier guard in CI
- **Fix:** Add the `rg` guard from [09_HARDCODING_AND_GENERALIZATION.md](09_HARDCODING_AND_GENERALIZATION.md).

### TST-15 (MEDIUM) No dependency or secret scanning
- **Fix:** Add `pip-audit`, `npm audit --omit=dev` and `gitleaks` jobs.

### TST-16 (LOW) No coverage reporting
- **Fix:** Add `pytest --cov` with a floor (for example 70%, rising over time).

---

## D. Infrastructure

### TST-17 (HIGH) Compose host port collision
- **Location:** `compose.yaml` line 31 (`MQTT_WS_PORT:-9001`) and line 91 (`MINIO_CONSOLE_PORT:-9001`).
- **Impact:** `docker compose --profile full up` fails to bind.
- **Fix:** Change the MinIO console default to 9090 (or the MQTT WS default to 9002).

### TST-18 (HIGH) Compose backend env incomplete
- **Evidence:** It does not set `DATABASE_BACKEND`, `DATABASE_URL`, `TELEMETRY_STREAMER_*`, `AUTH_ENABLED` or the JWT secret.
- **Impact:** The container auto-probes the database and runs the SIMULATION streamer into current state.
- **Fix:** Set these explicitly, and add a `compose.prod.yaml` override with no defaults for secrets.

### TST-19 (HIGH) No production deployment artifacts
- **Evidence:** There is no reverse proxy (TLS), production frontend serving (static build behind nginx/caddy), process manager settings (uvicorn workers or gunicorn) or health-check based restart policy.
- **Fix:** Add `infrastructure/nginx/` (or Caddy), a multi-stage frontend Dockerfile, backend `gunicorn -k uvicorn.workers.UvicornWorker` with worker count from env, and compose healthchecks.

### TST-20 (MEDIUM) In-process background workers and multiple replicas
- **Evidence:** The streamer, MQTT consumer and keep-alive run inside each API worker. With multiple workers, they duplicate.
- **Fix:** Run ingestion as a separate service or container (single instance), and keep the API stateless.

### TST-21 (MEDIUM) Mosquitto anonymous access
- See SEC-12.

### TST-22 (MEDIUM) No observability stack
- **Fix:** Expose a Prometheus `/metrics` endpoint (ingest rate, quarantine rate, WS clients, forecast latency, DB pool), structured logs, and an uptime alert on `/health`.

### TST-23 (LOW) No `pyproject.toml`
- **Fix:** Centralize pytest, ruff and mypy configuration, and pin versions with a lock file (`uv` or `pip-tools`).

### TST-24 (LOW) Hooks do not block weak default secrets
- **Location:** `.githooks/check_pre_commit.py`.
- **Fix:** Add a pattern check, or rely on gitleaks (TST-15).

## Acceptance criteria
- `pytest tests/<file>.py` passes for every file in isolation on a fresh clone with no `data/*.db`.
- CI is green on both the SQLite and PostgreSQL jobs, plus frontend lint, test and build.
- `docker compose --profile full up` starts all services without port conflicts.
