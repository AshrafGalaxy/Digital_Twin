# 04. Backend Services and API

## Summary

All endpoint modules are registered in `backend/api/v1/router.py`. The main problems are:
- silent fallbacks that fabricate values
- swallowed exceptions
- sync calls in async paths
- in-memory state
- inconsistent WebSocket lifecycle handling

---

## Findings

### BE-01 (CRITICAL) Silent fabricating fallbacks across services
| Service | Location | Fabrication |
|---|---|---|
| State history | `api/v1/endpoints/state.py` ~151-225 | Diurnal curve labeled REPLAY |
| Traffic LOS | `api/v1/endpoints/traffic.py` ~83-90, ~175-176 | `FALLBACK_SEGMENTS`, default speed/flow |
| Corridor LOS | `services/los_engine.py` ~245-256 | LOS C, 35 km/h, V/C 0.50 |
| Forecast service | `services/forecast_service.py` ~25, ~53 | 24.5 km/h, 4200 kW defaults |
| Power balance | `services/power_balance_service.py` ~190-232, ~239-242 | Static feeders, grid import from balance |
| Rule engine | `services/rule_engine.py` ~51-215 | Seeded narrative advisories with fixed values |
| Energy advisory | `services/energy_advisory_service.py` ~50-61 | Canned advisory (18450.0, 840.0, fixed ID) |
| Report generator | `services/report_generator.py` ~49-55, ~76 | Invented LIVE/REPLAY/PREDICTED counts |
| Continuous aggregator | `services/continuous_aggregator.py` ~178+ | Synthetic history seed on empty DB |
| Anomaly detector | `services/anomaly_detector.py` ~29-38, ~56-57 | Gaussian training data, fixed mean 45 and std 12 |

- **Fix pattern:**
  - Each service returns an explicit `EMPTY` / `DEGRADED` quality result with null values, and the UI renders an empty state.
  - Rule engine and advisory services only generate items from real current state or forecasts, and persist them (DB-06).
  - Demo content belongs to a dev-only demo seed that writes SIMULATION records.

### BE-02 (HIGH) Exceptions swallowed hide failures
- **Location:**
  - `traffic.py` ~456-457
  - `scenario_service.py` ~359-360
  - `canonical_resources.py` ~189-195 (`pass`)
  - `schema_migrator.py` ~640
  - `runner.py` ~108-112 (TraCI program set)
- **Fix:** Log at `error` with context and surface a `warnings` array or a non-2xx status. Only catch specific exceptions.

### BE-03 (HIGH) Blocking calls inside async lifespan and handlers
- **Location:** `backend/ingestion/mqtt_consumer.py` ~202-208 (`socket.connect_ex`); the raw `sqlite3` calls in the scenario and report services run on the event loop; `simulation/runner.py` is CPU bound and is invoked from request handlers.
- **Fix:** Use `asyncio.open_connection` with a timeout for the probe, run SUMO and kinematic simulations through `run_in_executor` or a background job queue, and remove the raw sqlite3 calls (DB-02).

### BE-04 (HIGH) WebSocket endpoints are not tracked by the connection manager
- **Location:** `backend/main.py` ~161-208 (`/ws/system`, `/ws/scenarios` accept connections but never register with `manager`, and have no disconnect cleanup).
- **Fix:** Register every socket and handle `WebSocketDisconnect`. Add a heartbeat ping/pong and server-side idle timeout.

### BE-05 (HIGH) Streamer, energy topology and SPaT synthetic writers coupled to the startup lifecycle
- **Location:** `backend/main.py` lifespan (~50-69) starts the streamer when enabled (default true).
- **Fix:** Make simulation generators an explicit, authenticated control (SEC-01) and keep them off by default.

### BE-06 (HIGH) Long-running scenario runs execute synchronously in the request
- **Location:** `POST /scenarios/run` to `scenario_service` to `simulation/runner.py`.
- **Fix:** Return `202 Accepted` with a run ID, execute in a worker, stream progress over `/ws/scenarios`, and persist the result.

### BE-07 (HIGH) SQLite-specific SQL in shared endpoints
- **Location:** `backend/api/v1/endpoints/analytics.py` ~109 (`datetime('now', ...)`).
- **Fix:** Use parameterized `observed_at >= :since`, with `since` computed in Python.

### BE-08 (MEDIUM) Historical drift endpoint self-compares the reference set
- See ML-08 in [05_ML_AND_SIMULATION.md](05_ML_AND_SIMULATION.md).

### BE-09 (MEDIUM) `CUSTOM_DISTRICT` LOS policy silently maps to US HCM
- **Location:** `backend/services/los_engine.py` ~167. See DOM-05.

### BE-10 (MEDIUM) Parallel speed-only LOS implementation
- **Location:** `backend/api/v1/endpoints/state.py` ~279-289 (`_compute_los`).
- **Fix:** Delete it and call `los_engine`.

### BE-11 (MEDIUM) Magic numbers belong in config
- Includes saturation flow 1800, cycle bounds, free-flow speed 50, capacities 2400/1400, thermal thresholds 0.75/0.90, and the peak factor 0.85. See [09_HARDCODING_AND_GENERALIZATION.md](09_HARDCODING_AND_GENERALIZATION.md).

### BE-12 (MEDIUM) Weather client hardcodes coordinates
- **Location:** `backend/ingestion/weather_client.py` ~92-93 (`18.5679, 73.9143`).
- **Fix:** Read the study-area centroid from the registry.

### BE-13 (MEDIUM) No pagination or limits on list endpoints
- **Location:** `/observations`, `/recommendations`, `/recommendations/audit/logs`, `/inquiries`, `/energy/telemetry/history`.
- **Fix:** Add `limit` (default 100, max 1000) and cursor or `before` timestamp parameters.

### BE-14 (MEDIUM) Inconsistent response casing and envelopes
- Some endpoints return snake_case (for example `inquiry_id`) and others camelCase. Some wrap the result in `{data, provenance}`, and others return bare objects.
- **Fix:** Pick camelCase with Pydantic `alias_generator`, use `response_model` on every route, and use one envelope.

### BE-15 (MEDIUM) Missing `response_model` on many routes
- **Impact:** No schema validation of outputs, and the OpenAPI docs are inaccurate, so the frontend types drift.
- **Fix:** Add response models and generate TS types from OpenAPI (`openapi-typescript`) in CI.

### BE-16 (MEDIUM) Health endpoint does not reflect dependencies honestly
- **Fix:** `/health` should report DB connectivity, schema version, Timescale availability, MQTT connectivity, streamer mode, model artifact load status and last-ingest age.

### BE-17 (LOW) `datetime.utcnow()` usage
- **Location:** `recommendations.py` ~93, ~97 and others.
- **Fix:** Use `datetime.now(timezone.utc)`.

### BE-18 (LOW) Webster `minGreenSatisfied` hardcoded True
- See DOM-03.

### BE-19 (LOW) No structured logging or request IDs
- **Fix:** JSON logs with a request ID middleware, and log provenance mode on ingestion.

### BE-20 (LOW) No API versioning policy beyond `/api/v1`
- **Fix:** Document the deprecation policy.

### BE-21 (LOW) FIWARE adapter defaults to pilot coordinates
- **Location:** `backend/services/fiware_adapter.py` ~47, ~81, ~120.
- **Fix:** Require coordinates from the registry, and skip the entity if they are missing.

### BE-22 (LOW) Explainer returns `baseValue: 0.0` on failure without an invalid flag
- **Location:** `ml/explainer.py` ~80-85.
- **Fix:** Return `explanationStatus: "UNAVAILABLE"`.

## Acceptance criteria
- `rg "except Exception:\s*$" -A1 backend | rg "pass"` returns nothing.
- Every route has `response_model`, and the OpenAPI-generated TS types compile against the frontend.
