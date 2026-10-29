# 07. Frontend (React, TypeScript, Mapbox, Cesium)

## Summary

The UI is visually mature and free of emojis and em dashes. The problems are:
- client-side fabricated values
- hardcoded fallback KPIs
- client-only authorization
- dead components and API clients
- inconsistent provenance display

---

## A. Fabricated or hardcoded data shown as real

### FE-01 (CRITICAL) Telemetry heartbeat jitter with Math.random
- **Location:** `frontend/src/App.tsx` lines 393-433.
- **Fix:** Delete it. See SP-11.

### FE-02 (CRITICAL) Seed KPI values
- **Location:** `App.tsx` ~169-170 (`4862.0` kW, `10` sensors), ~446-447 (`avgSpeed` default `42.5`).
- **Fix:** Use `null` initial state with "Awaiting data" UI.

### FE-03 (HIGH) Environment view fallback values stamped as fresh
- **Location:** `frontend/src/components/views/EnvironmentContextView.tsx` ~74-101 (hardcoded AQI, PM, temperature, `observedAt: new Date().toISOString()`, `lastSynced: 'Just now'`).
- **Fix:** Show an error state with a retry button.

### FE-04 (HIGH) Energy view default facilities and fallback numbers
- **Location:** `frontend/src/components/views/EnergyAnalyticsView.tsx`:
  - ~49-100 (`DEFAULT_FACILITIES` with pilot building URNs)
  - ~160
  - ~281-295 (synthetic time-of-day kW)
  - ~313-323 (`768.4`, `5940.2`, `5171.8`, `summaryFreq = 50.02`)
- **Fix:** Load facilities from `/assets/energy` and render empty states when data is missing.

### FE-05 (HIGH) Traffic view fallback speed and flow
- **Location:** `frontend/src/components/views/TrafficAnalyticsView.tsx` ~124-125 (`24.5` km/h, `1250` vph).
- **Fix:** Render `--` with STALE/EMPTY quality.

### FE-06 (HIGH) Landing and command showcase KPIs look operational
- **Location:** `landing/AgencyCommandShowcase.tsx` ~47-95 (`18.4%`, `380 kW`), `LandingPageView.tsx` ~890-915 (`10` segments, `2` signals, `4862 kW`).
- **Fix:** Either fetch them from `/study-area` and `/health`, or label them "Illustrative" in visible text.

### FE-07 (MEDIUM) ContactAccessModal invents inquiry IDs on failure
- **Location:** `landing/ContactAccessModal.tsx` lines 170 and 184 (`INQ-YYYY-####` via `Math.random`, persisted as success).
- **Fix:** Delete the component (it is unused, FE-12), or show a failure state.

### FE-08 (MEDIUM) Hardcoded map geometry
- **Location:**
  - `MapOperationsView.tsx` ~27-205 (stop lines, junctions, zebra crossings), ~299 (center `[73.9220, 18.5615]`)
  - `CesiumCorridorViewer.tsx` ~754-796 (metro viaduct polyline), ~175-199 (bundled fallback JSON)
- **Fix:** Serve geometry from `/spatial/layers/{layer}` and compute the map center from the study-area bounding box.

### FE-09 (LOW) Replay status failure returns a synthetic object
- **Location:** `frontend/src/services/api.ts` ~116-119.
- **Fix:** Throw the error and let the caller show an error state.

---

## B. Disconnected or dead UI

### FE-10 (HIGH) Scenario Studio and Advisory Center modals can never open
- **Location:** `App.tsx` ~163-164 (`isScenarioStudioOpen`, `isAdvisoryCenterOpen` are never set to true), ~697-718.
- **Fix:** Remove the modals and state, or add triggers. The tab views already cover the functionality.

### FE-11 (HIGH) `RoleAuthModal.tsx` never imported
- **Fix:** Delete it.

### FE-12 (HIGH) `ContactAccessModal.tsx` never imported
- **Fix:** Delete it.

### FE-13 (MEDIUM) `ScenarioStudio.tsx` duplicates `ScenarioStudioView.tsx`
- **Fix:** Delete the unused modal version.

### FE-14 (MEDIUM) API clients defined but unused
- `fetchSensors`
- `fetchHistoricalSnapshot`
- `fetchForecastModels`
- `fetchTrafficRollups`
- `fetchEnvironmentStations`
- `fetchSPaTHistory`
- `fetchFeederThermalMargins`
- `fetchPowerBalanceHistory`
- `fetchSpatialRegistry`
- `fetchSpatialLayer`
- `resolveSpatialEntity`

**Fix:** Wire the operationally valuable ones (see [08_INTEGRATION_GAPS.md](08_INTEGRATION_GAPS.md)) and delete the rest.

---

## C. Bugs and React issues

### FE-15 (HIGH) WebSocket double reconnect
- **Location:** `frontend/src/services/api.ts` ~370-380 (`onerror` cleans up and schedules a reconnect, then `onclose` schedules another).
- **Fix:** Only schedule from `onclose`. In `onerror`, just log. Guard with a `reconnectTimer` ref.

### FE-16 (HIGH) Freshness computed from client time
- **Location:** `App.tsx` WS handler sets `updatedAt: new Date().toISOString()`, `freshnessSeconds: 1.0` and `qualityStatus: 'VALID'` for every message.
- **Fix:** Take `qualityStatus` and `observedAt` from the server, and compute freshness as `now - observedAt` in a single ticking hook.

### FE-17 (MEDIUM) Effect dependency gaps
- **Location:** `TrafficAnalyticsView.tsx` ~53-68 (missing `selectedIntersectionId`), `energy/FeederThermalLoadingCard.tsx` ~40-42 (`loadData` not stable).
- **Fix:** Use `useCallback` and complete the dependency arrays. Enable `eslint-plugin-react-hooks` in CI.

### FE-18 (MEDIUM) Widespread `any`
- **Location:** `MapOperationsView.tsx` ~291+, `CesiumCorridorViewer.tsx` ~183-1035, `api.ts` (`Promise<any>` for forecasts and scenarios).
- **Fix:** Generate types from OpenAPI (BE-15) and enable `noImplicitAny` plus the `@typescript-eslint/no-explicit-any` warning.

### FE-19 (MEDIUM) Hardcoded default selected entities
- **Location:** `TrafficAnalyticsView.tsx` ~40-43, ~343-344 (pilot segment and intersection IDs).
- **Fix:** Default to the first entity returned by `/assets`.

### FE-20 (MEDIUM) No global error handling or toasts for API failures
- **Fix:** Use a central `apiFetch` with typed errors and a toast/notification region. The new `ErrorBoundary` covers render errors only.

### FE-21 (MEDIUM) No loading skeletons on several views
- **Fix:** Use standard `loading | error | empty | ready` states per data hook.

### FE-22 (LOW) WebSocket URL bypasses the Vite proxy
- **Location:** `api.ts` ~281-283 (connects directly to `:8000`).
- **Fix:** Derive the URL from `window.location` (`ws(s)://host/ws/...`) so that it works behind a reverse proxy and TLS.

### FE-23 (LOW) Bundle size
- Cesium plus Mapbox in one bundle. **Fix:** Use route-level code splitting (`React.lazy`) for the 3D viewer and landing page.

---

## D. Provenance display gaps

### FE-24 (HIGH) KPI cards lack per-value timestamp and quality
- **Location:**
  - `CorridorMetricsCard.tsx` ~56-102
  - `TrafficAnalyticsView.tsx` ~573-602 ("Observed Speed / Flow / Density")
  - `EnvironmentContextView.tsx` ~199-242
  - `EnergyAnalyticsView.tsx` ~313-323
  - `energy/FeederThermalLoadingCard.tsx`
  - `energy/ThreePhaseTelemetryCard.tsx`
- **Fix:** Create a `<ProvenancedMetric value unit sourceMode observedAt qualityStatus />` component and use it for every numeric KPI.

### FE-25 (MEDIUM) Copy claims LIVE regardless of mode
- **Location:**
  - `App.tsx` ~470 (screen reader "Live stream active")
  - `TrafficAnalyticsView.tsx` ~319 ("Real-Time SPaT"), ~567 ("Live State")
  - `LandingPageView.tsx` ~317, ~506 ("LIVE TELEMETRY STREAM")
  - `ThreePhaseTelemetryCard.tsx` ~95 ("LIVE TELEMETRY")
- **Fix:** Render the actual `sourceMode` label (for example "Replay stream active", "Simulation feed").

### FE-26 (MEDIUM) ForecastPanel interval label
- **Location:** `ForecastPanel.tsx` ("80% Confidence Interval" shows the p10/p90 quantile models).
- **Fix:** After ML-02, show conformal 80% and 90% intervals and call them "prediction intervals" (not confidence intervals).

### FE-27 (LOW) ProvenanceBadge LIVE tooltip mentions "mock feed"
- See SP-17.

---

## E. Pilot-specific copy in generic components

### FE-28 (HIGH) Pilot identifiers in generic views
- `TrafficAnalyticsView.tsx` (segment and intersection IDs)
- `EnergyAnalyticsView.tsx` (building URNs)
- `MapOperationsView.tsx` ~302, ~393, ~1035 ("Nagar Road", "Pune Airport / Lohegaon")
- `CesiumCorridorViewer.tsx` (metro line name, comments)
- `ScenarioStudio*.tsx` (segment ID subtitles)
- `AuthPageView.tsx` (`pmc.gov.in` demo emails)

**Fix:** Read names from the registry. Keep pilot narrative only in `PilotEvaluationView`, driven by deployment content (see [09_HARDCODING_AND_GENERALIZATION.md](09_HARDCODING_AND_GENERALIZATION.md)).

---

## F. Security (frontend side)

See SEC-07 and SEC-08 in [02_SECURITY_AND_AUTH.md](02_SECURITY_AND_AUTH.md): token storage, missing Bearer header, client-only role gates, hash route bypass, demo credentials panel.

---

## G. Accessibility and UX

### FE-29 (MEDIUM) Desktop viewport guard blocks tablets used in control rooms
- **Location:** `common/DesktopViewportGuard.tsx`.
- **Fix:** Lower the threshold to 1024 px, or allow dismissal with a warning.

### FE-30 (LOW) Color-only status encoding
- **Fix:** Pair LOS and thermal status colors with text labels (most already do; audit the map legend and feeder bars).

### FE-31 (LOW) No frontend tests
- **Fix:** Add Vitest and React Testing Library for provenance rendering, auth guard and WS reconnect logic. See TST-08.

## Acceptance criteria
- `rg "Math.random" frontend/src` shows only the reconnect jitter and the scenario seed button.
- No numeric literal default is rendered as a metric (enforced by review and by tests that render views with empty API responses and assert `--`).
- Every route except landing and auth requires authentication.
