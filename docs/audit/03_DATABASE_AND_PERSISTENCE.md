# 03. Database and Persistence

## Summary

The platform keeps two schema definitions: `infrastructure/postgres/init.sql` and the SQLite DDL in `backend/core/schema_migrator.py`. They have drifted. Some services bypass the async SQLAlchemy layer and write raw `sqlite3` files even when PostgreSQL is primary, which causes split-brain persistence. Several tables are dead.

---

## Findings

### DB-01 (CRITICAL) `timing_recommendations` columns differ per dialect, and Postgres inserts fail silently
- **Location:**
  - `infrastructure/postgres/init.sql` lines 435-455 (columns `quality_status`, `applied_status`)
  - `backend/core/schema_migrator.py` lines 435-453 (columns `status`, `reviewed_by`, `reviewed_at`)
  - `backend/api/v1/endpoints/traffic.py` ~409-421 (INSERT uses `status`), ~456-457 (`except Exception: logger.warning(...)`)
- **Impact:** On PostgreSQL, Webster recommendations are never persisted, and nothing visible reports the failure.
- **Fix:** Define a single canonical column set: `status`, `quality_status`, `reviewed_by`, `reviewed_at`, `applied_status`. Migrate both dialects. Let persistence errors propagate as 500, or at minimum set a `persisted: false` field.

### DB-02 (CRITICAL) Split-brain persistence through raw sqlite3
- **Location:**
  - `backend/services/scenario_service.py` ~274-405 (`sqlite3.connect(settings.resolved_sqlite_path)`)
  - `backend/services/report_generator.py` ~36-40
  - `backend/ingestion/quarantine.py` ~24-27, ~41-44 (separate `data/quarantine.db`)
- **Impact:** With PostgreSQL primary:
  - scenario runs, report counts and quarantined records go to a local file that other replicas cannot see
  - health endpoints that read `quarantine_observations` from the main DB disagree with what the validator wrote
- **Fix:** Route all I/O through `AsyncSessionLocal` and dialect-neutral SQLAlchemy Core statements. Delete the `quarantine.db` path.

### DB-03 (CRITICAL) `entity_current_state` constraint allows every mode
- See SP-04 in [01_STATE_SEPARATION_AND_PROVENANCE.md](01_STATE_SEPARATION_AND_PROVENANCE.md).

### DB-04 (HIGH) PostgreSQL migrator is fragile and swallows errors
- **Location:** `backend/core/schema_migrator.py` ~630-645.
- **Evidence:**
  - it splits `init.sql` on `;`, which breaks `DO $$ ... $$` PL/pgSQL blocks
  - every failure is caught as `logger.debug("PostgreSQL statement notice")`
  - the function returns a hardcoded `31`
- **Impact:** The schema can be partially created and the app still starts.
- **Fix:** Adopt Alembic with one migration history that targets both dialects (with dialect-conditional ops where needed). As an interim step, execute `init.sql` as a single script through `asyncpg` and fail fast on error.

### DB-05 (HIGH) SQLite-only seed SQL runs on PostgreSQL
- **Location:** `backend/core/schema_migrator.py` ~935, ~979, ~1054 (`INSERT OR IGNORE`).
- **Fix:** Use SQLAlchemy `insert().on_conflict_do_nothing()` per dialect (`sqlalchemy.dialects.postgresql.insert` / `sqlite.insert`).

### DB-06 (HIGH) Dead or one-sided tables
| Table | Written | Read | Action |
|---|---|---|---|
| `forecasts` | no | no | Persist every served forecast (PREDICTED) with model version, horizon and interval. Serve history from here. |
| `model_versions` | no | no | Register each trained artifact with metrics, split ratios and conformal quantiles. |
| `recommendations` | no | no | Persist rule engine output (currently in memory). |
| `segment_los_history` | yes (`telemetry_streamer.py` ~254) | no | Expose through `/traffic/segment/{id}/los/history` or drop. |
| `environment_observations` | yes | barely | Serve history endpoint and index it (DB-10). |

### DB-07 (HIGH) In-memory state for governance records
- **Location:** `REGISTERED_USERS` (`auth.py` ~100), `rule_engine._recommendations`, `energy_advisory_service._advisories`.
- **Fix:** Add tables `users`, `recommendations` (already exists), `energy_advisories`. Load and update through the DB.

### DB-08 (HIGH) Observation tables lack referential integrity
- **Location:** `init.sql` ~123-131 and the SQLite counterparts.
- **Evidence:** No foreign keys from `traffic_observations.segment_id`, `energy_observations.building_id` or `environment_observations.station_id` to the asset registry.
- **Fix:** Add FK constraints, or (for hypertables, where FKs are costly) validate entity existence in `Validator` and quarantine unknown IDs.

### DB-09 (HIGH) Seed data is pilot-specific and fabricated
- **Location:**
  - `backend/core/schema_migrator.py` ~686 (`"Pune-Ahmednagar Road"` default), ~905-930 (scenario names), ~956-1020 (segment metrics), ~1202-1206 (substation)
  - `backend/scripts/seed_db.py` ~197 (hardcoded `postgresql://postgres:postgres@localhost:5432/digital_twin`)
- **Fix:** Move all deployment seed data into a deployment package (for example `config/deployments/<deployment_id>/*.json`) loaded by a single idempotent seed command. Remove `seed_db.py` or make it read `DATABASE_URL`.

### DB-10 (MEDIUM) Missing index on environment observations
- **Fix:** Add `CREATE INDEX idx_env_obs_station_time ON environment_observations (station_id, observed_at DESC)` in both dialects.

### DB-11 (MEDIUM) Naive timestamps on SQLite
- **Location:** SQLite DDL uses `TIMESTAMP`; `database.py` ~116-120 registers a `NOW()` that returns an ISO string; `recommendations.py` ~93, ~97 use `datetime.utcnow()`.
- **Fix:** Store ISO-8601 with an explicit `+00:00` offset. Replace `utcnow()` with `datetime.now(timezone.utc)` everywhere. Add a test that round-trips a timestamp in both dialects.

### DB-12 (MEDIUM) Aggregates lack provenance columns
- **Location:** `traffic_15m_aggregates` (`init.sql` ~316-329).
- **Fix:** Add `source_mode`, `sample_count` and `quality_status`, and aggregate per source mode (never mix REPLAY and SIMULATION in one bucket).

### DB-13 (MEDIUM) Session auto-commits on every request
- **Location:** `backend/core/database.py` ~176-186 (`get_db_session` commits after GETs too).
- **Fix:** Commit only in write handlers, or use `session.begin()` in the service layer.

### DB-14 (MEDIUM) Mixed manual sessions and injected sessions
- **Location:** `power_balance_service.py`, `energy_topology_service.py` (manual `AsyncSessionLocal()` plus `close()`).
- **Fix:** Pass the session in from the endpoint, or use `async with AsyncSessionLocal() as s:` consistently.

### DB-15 (MEDIUM) Hypertable creation is best effort
- **Location:** `init.sql` ~126-131 (`EXCEPTION WHEN OTHERS`).
- **Fix:** Log a warning at startup when Timescale is unavailable, and expose it in `/health` so operators know retention and compression are off.

### DB-16 (MEDIUM) No retention or compression policy
- **Fix:** Add Timescale `add_retention_policy` and `add_compression_policy` for observation tables, with config-driven durations.

### DB-17 (MEDIUM) No backup or restore procedure
- **Fix:** Document and automate `pg_dump` / Supabase PITR, and test a restore before go-live.

### DB-18 (LOW) Table count documentation drift
- **Evidence:** The `init.sql` header says 29 tables, the migrator docstring says 18, the migrator returns 31, the README says 25, and the actual count is 34.
- **Fix:** Generate the count from metadata and remove the hardcoded numbers.

### DB-19 (LOW) Geometry stored as TEXT on SQLite
- Expected for the fallback, but any `ST_*` query must be guarded by dialect. Document SQLite as a dev-only backend.

### DB-20 (LOW) `seed_db.py` duplicates migrator seeding
- **Fix:** Keep one seed path.

### DB-21 (LOW) Supabase keep-alive runs only for Postgres
- **Location:** `backend/services/keepalive_service.py`. This is fine, but document it as a free-tier workaround and disable it on paid plans.

## Acceptance criteria
- A CI job runs the full test suite against PostgreSQL/Timescale (service container) and SQLite.
- One migration tool, with no hand-split SQL.
- `rg "sqlite3.connect" backend` returns nothing.
