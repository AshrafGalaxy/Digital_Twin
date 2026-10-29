# 11. Review of Uncommitted Work in Progress

These are the working tree changes at the audit date, not yet committed:

| File | Change summary |
|---|---|
| `AGENTS.md` | Adds rule 10 (issue tracking and closure dossier) and a checklist item |
| `backend/ingestion/telemetry_streamer.py` | Passes `datetime` objects (`now_dt`) instead of ISO strings to SQL parameters |
| `ml/inference/forecaster.py` | Adds `baselineComparison` metrics and notices to the heuristic fallback |
| `frontend/src/components/common/ErrorBoundary.tsx` (new) | Class error boundary with a recover button |
| `frontend/src/App.tsx` | Wraps the map and drawer in ErrorBoundary, and makes `metrics` access optional |
| `frontend/src/components/EntityDetailDrawer.tsx` | Optional chaining, ErrorBoundary around forecasts, tolerant `connectedSegments` parsing, replaces a Unicode minus with a hyphen |
| `frontend/src/components/ForecastPanel.tsx` | Null-safe rendering, default model and notice strings |
| `frontend/src/components/MapOperationsView.tsx` | Optional chaining, tolerant `connectedSegments` rendering |
| `frontend/src/components/views/TrafficAnalyticsView.tsx` | ErrorBoundary around the forecast |

## Verdict per change

### WIP-01 (CRITICAL, revert) Fabricated metrics added to the heuristic forecast fallback
- **Location:** `ml/inference/forecaster.py` traffic fallback (`modelTestMae: 3.8`, `persistenceMae: 4.5`, `accuracyGainPct: 15.6`) and energy fallback (`180.0`, `225.0`, `20.0`).
- **Problem:** The fallback is a `current * 0.95` / `current * 1.02` heuristic labeled `PREDICTED`. Adding test MAE and accuracy gain numbers that were never measured presents invented evaluation evidence, which violates the data honesty rules.
- **Action:** Keep `persistenceValue` if useful, but set `modelTestMae`, `persistenceMae` and `accuracyGainPct` to `null`. Rename `modelVersion` to `persistence-fallback`. The `localityNotice` / `sourceLimitation` strings are fine.

### WIP-02 (HIGH, change) Default model version strings in ForecastPanel misattribute the model
- **Location:** `frontend/src/components/ForecastPanel.tsx` (`modelVersion || 'traffic-xgb-v1'`, `modelVersion || 'energy-xgb-v1'`).
- **Problem:** When the backend does not report a version (for example, a fallback), the UI claims XGBoost v1.
- **Action:** Render `Unknown` (or hide the row). Keep the other null guards, which are good.

### WIP-03 (MEDIUM, keep with follow-up) ErrorBoundary
- **Assessment:** Good addition. The component is clean, uses Lucide icons, and contains no emojis or em dashes.
- **Follow-up:**
  - Show the raw `error.message` only in development builds (`import.meta.env.DEV`), and use a generic message in production.
  - Report errors to the backend log endpoint or an error tracker.

### WIP-04 (MEDIUM, keep but fix root cause) Tolerant `connectedSegments` parsing in the frontend
- **Location:** `EntityDetailDrawer.tsx` and `MapOperationsView.tsx`.
- **Problem:** The frontend now parses a JSON string because the backend sometimes returns `connected_segments` as raw TEXT (the SQLite JSON column is not deserialized).
- **Action:** Fix the serialization in the backend `/assets/intersections` response (always a list), declare it in the response model, then simplify the frontend back to array handling.

### WIP-05 (LOW, keep) Optional chaining on `metrics`
- **Assessment:** It prevents crashes.
- **Follow-up:** Missing metrics should render an explicit empty state, not fall through to defaults. Two related defaults pre-date this change and should be fixed alongside it:
  - `MapOperationsView.tsx` uses `?? 45.0` speed when state is missing, which paints a segment with no data as free-flowing green. Show grey "No data" instead.
  - `EntityDetailDrawer.tsx` defaults `sourceModeA` to `'SIMULATION'` when state is missing, which mislabels absence as simulation. Use an `EMPTY` quality state.

### WIP-06 (LOW, keep) Datetime parameters in the streamer
- **Assessment:** Passing `datetime` objects is correct for asyncpg and harmless for aiosqlite.
- **Note:** The streamer still writes SIMULATION into `entity_current_state`. This change does not touch that (see SP-01), but it should not ship without it.

### WIP-07 (LOW, keep) AGENTS.md rule 10
- **Assessment:** It is consistent with the existing rules. Note that the GitHub CLI is not authenticated on the workstation (`gh auth login` required), so issue creation and closure dossiers cannot be automated until it is.

## Additional issue noticed in touched files (pre-existing)

### WIP-08 (MEDIUM) A third LOS implementation in the operations table
- **Location:** `MapOperationsView.tsx` ~1294 (`speed >= 42 ? 'A' : speed >= 38 ? 'B' : ...`).
- **Problem:** Hardcoded absolute speed bands that disagree with `los_engine` and with the drawer `_compute_los`.
- **Action:** Use the LOS grade returned by the backend (`/traffic/corridor/los` per segment).

### WIP-09 (LOW) Map color thresholds hardcoded
- **Location:** `MapOperationsView.tsx` ~522-525 (20 / 35 km/h).
- **Action:** Color by LOS grade, or by speed ratio against per-segment free-flow speed.

## Recommended commit split for the WIP
1. `fix(ui): add error boundary and null-safe metric access`: ErrorBoundary plus the optional chaining changes (after WIP-02 and WIP-05 adjustments).
2. `fix(ingest): bind datetime parameters in streamer writes`: the streamer change.
3. Do not commit the forecaster change as is (WIP-01).
4. `docs(config): add issue closure dossier contract`: AGENTS.md.
