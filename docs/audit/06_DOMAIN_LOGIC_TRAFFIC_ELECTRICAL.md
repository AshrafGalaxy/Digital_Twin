# 06. Domain Logic: Traffic Engineering and Electrical Infrastructure

All formulas are in plain-text notation.

---

## A. Signal timing (Webster optimizer)

Reference: Webster (1958); HCM signalized intersection methodology.

- `C_0 = (1.5 * L + 5) / (1 - Y)`
- `Y = sum over critical phases i of max_j(q_ij / s_ij)`
- `L = sum over critical phases of (l_1 + l_2)`, where `l_1` is start-up lost time (typically 2 s) and `l_2` is clearance lost time (yellow plus all-red minus extension of effective green, typically 2 s)
- `g_i = (C_0 - L) * y_i / Y`

### DOM-01 (CRITICAL) Y is summed over approaches, not over critical phases
- **Location:** `backend/services/signal_optimizer.py` ~176-199.
- **Evidence:** One flow ratio is computed per approach, then `y_sum = sum(flow_ratios_y)`.
- **Impact:** Opposing approaches that run in the same phase (for example eastbound and westbound through) are added together instead of taking the larger one. Y is overstated, `C_0` is inflated, and intersections are reported as oversaturated when they are not.
- **Fix:**
  - Model `phases -> movements`.
  - For each phase, `y_phase = max(q/s over movements served in that phase)`.
  - `Y = sum(y_phase)`.
  - The API request should accept a phase plan (movement-to-phase mapping), taken from the signal registry or SPaT phase table.

### DOM-02 (HIGH) Lost time computed per approach
- **Location:** `signal_optimizer.py` ~176-177 (`total_lost_time = ceil((yellow + all_red) * m)` with `m = number of approaches`).
- **Fix:** `L = n_critical_phases * (startup_lost + clearance_lost)`. Make startup and clearance lost times configurable per deployment.

### DOM-03 (HIGH) Y capped at 0.85 before computing C_0
- **Location:** `signal_optimizer.py` ~200-204 (`effective_y = min(0.85, max(0.10, y_sum))`).
- **Impact:** When Y >= 0.85, the formula is clamped and the cycle is understated. Oversaturation only appears as a note.
- **Fix:**
  - Compute with the real Y when Y < 1.
  - If Y >= 0.90 (configurable), return `status: "OVERSATURATED"`, use the maximum cycle, and add an advisory that demand exceeds capacity.
  - If Y >= 1.0, Webster is undefined; return no optimal cycle.

### DOM-04 (HIGH) Green floor ignores minimum green, and `minGreenSatisfied` is hardcoded
- **Location:** `signal_optimizer.py` ~218 (floors by pedestrian clearance only) and ~326 (`minGreenSatisfied: True`).
- **Fix:** Floor each phase at `max(ped_clearance, min_green)`, recompute the cycle if the floors exceed the available green, and compute the boolean.

### DOM-05 (MEDIUM) Pedestrian clearance formula is simplified
- **Location:** `signal_optimizer.py` ~193 (`ceil(width / walking_speed)`).
- **Fix:** Use the MUTCD/IRC-style `ped_green = walk_interval (approx. 4-7 s) + crossing_distance / walking_speed`, with `walking_speed` configurable (1.0-1.2 m/s, lower near schools or hospitals).

### DOM-06 (MEDIUM) Saturation flow hardcoded at 1800 vph/lane
- **Location:** `signal_optimizer.py` ~27.
- **Fix:** Use a configurable base saturation flow with adjustment factors (lane width, heavy vehicles, grade, turning, mixed traffic PCU for Indian conditions per IRC:SP:41 or Indo-HCM). Store it per approach in the registry.

### DOM-07 (MEDIUM) Delay model
- **Fix:** Use Webster's uniform delay `d_1 = 0.5 * C * (1 - g/C)^2 / (1 - min(1, X) * g/C)`, plus an incremental delay term (HCM `d_2`) for X near 1. Report intersection LOS from control delay (HCM signalized thresholds: A <= 10 s, B <= 20, C <= 35, D <= 55, E <= 80, F > 80 s/veh).

---

## B. Level of Service (LOS)

### DOM-08 (HIGH) `CUSTOM_DISTRICT` policy silently uses US HCM thresholds
- **Location:** `backend/services/los_engine.py` line 167 (`INDO_HCM_THRESHOLDS if policy == INDO_HCM else US_HCM_THRESHOLDS`).
- **Fix:** Load custom thresholds from the deployment config. Raise a validation error for unknown policies.

### DOM-09 (HIGH) Two LOS implementations disagree
- **Location:** `backend/api/v1/endpoints/state.py` ~279-289 (speed-only) vs `los_engine.py` (V/C plus speed ratio).
- **Fix:** Use `los_engine` only.

### DOM-10 (MEDIUM) Arterial LOS methodology mix
- **Evidence:** The engine grades by both V/C and speed ratio (`los_engine.py` ~142-170). HCM urban street segment LOS is defined by travel speed as a percentage of base free-flow speed (A > 85%, B > 67%, C > 50%, D > 40%, E > 30%, F <= 30% or V/C > 1.0). V/C is used only as the F override.
- **Fix:** Document the policy explicitly:
  - for `US_HCM`: grade on the speed ratio, with an F override when V/C > 1.0
  - for `INDO_HCM`: use the Indo-HCM urban arterial speed bands, with PCU-based V/C
  - expose the rule used in the response (`losMethod`)

### DOM-11 (MEDIUM) Density units
- **Location:** `los_engine.py` ~131 (`density = flow / speed`).
- **Evidence:** This is the fundamental relation `k = q / v` (correct), but `q` is total segment flow, so `k` is veh/km over all lanes. HCM uses pc/km/ln.
- **Fix:** Divide by the lane count and convert to PCU where mixed traffic factors apply. Label the unit explicitly.

### DOM-12 (MEDIUM) Free-flow speed defaults to 50 km/h
- **Location:** `los_engine.py` ~118, ~191, ~264; `validator.py` ~113.
- **Fix:** Store it per segment in the registry (posted speed limit or the observed 85th percentile off-peak speed).

### DOM-13 (LOW) Congestion index is a heuristic
- `CI = 1 - v / v_ff` is acceptable but should be labeled "speed reduction index", not as an HCM metric.

---

## C. SPaT and signal state

### DOM-14 (MEDIUM) SPaT freshness thresholds differ from the platform contract without documentation
- **Location:** `backend/services/spat_adapter.py` ~115-126 (3 s / 10 s) vs `backend/core/constants.py` ~47 (180 s).
- **Evidence:** A short SPaT freshness window is domain-correct, because a signal state that is 10 s old is useless.
- **Fix:** Keep the short window, but define it as a named constant `SPAT_STALE_SECONDS` in `constants.py`, document it in AGENTS.md, and emit STALE in `qualityStatus` (not `sourceMode`).

### DOM-15 (MEDIUM) Phase tables hardcoded per pilot intersection
- **Location:** `spat_adapter.py` ~161-212.
- **Fix:** Load the phase plan from the signal registry (`/spatial/signals`).

---

## D. Electrical: power balance and feeder thermal loading

Reference relations:
- Three-phase active power: `P = sqrt(3) * V_LL * I * PF`
- Apparent current: `I = S / (sqrt(3) * V_LL)`
- Three-phase conductor loss: `P_loss = 3 * I^2 * R_phase`
- Bus balance: `P_grid_import + P_pv + P_bess_discharge = P_load + P_loss + P_bess_charge + P_grid_export`

The headroom formula `sqrt(3) * V * (I_rated - I) * PF / 1000` and the loss formula `3 * I^2 * R / 1000` in `backend/services/power_balance_service.py` (lines 52-76) are correct.

### DOM-16 (HIGH) Missing telemetry is treated as zero current, which reads as NOMINAL
- **Location:** `power_balance_service.py` ~150 (`actual_current = float(telem.get("currentA", 0.0))`), ~160-161 (voltage defaults to nominal, PF defaults to 0.95).
- **Impact:** A feeder with a dead meter shows 0% loading and NOMINAL status, which is a dangerous false negative.
- **Fix:** If the telemetry is missing or stale (> 900 s), set the feeder `qualityStatus: "STALE"`, set the loading to `null`, and use status `UNKNOWN`. Exclude it from `max_loading_ratio`, but flag it at corridor level.

### DOM-17 (HIGH) Kirchhoff closure fabricates grid import and makes the residual tautological
- **Location:** `power_balance_service.py` ~239-246.
- **Evidence:** When `p_grid_import == 0`, it is set to `sinks - sources`, so `residual_kw` becomes about 0 by construction. The response then implies the balance is verified.
- **Fix:**
  - Treat zero as a measured value only if the meter quality is VALID.
  - Otherwise, report `pccGridImportKw: null`, add `derivedGridImportKw` with `derivation: "KIRCHHOFF_CLOSURE"`, and set `residualKw: null`.
  - When metered, the residual is a real meter-consistency check: alarm if it exceeds a configurable percentage (for example 3%) of load.

### DOM-18 (HIGH) No grid export path
- **Location:** `power_balance_service.py` ~236-242 (import clamped to `max(0, ...)`).
- **Impact:** PV surplus cannot be represented, so the residual hides reverse power flow, which is a protection-relevant condition.
- **Fix:** Use a signed `pccNetPowerKw` (positive import, negative export) and flag reverse power flow.

### DOM-19 (HIGH) Static fallback feeders with pilot names
- **Location:** `power_balance_service.py` ~190-232.
- **Fix:** Remove them (see SP-16).

### DOM-20 (MEDIUM) Generic conductor resistance
- **Location:** `power_balance_service.py` ~164-165 (`0.08 ohm/km`, default length 750 m).
- **Fix:** Store the conductor type, cross-section, `R_ac at 90 C` per km, and route length per feeder in the registry. Correct R for temperature: `R_T = R_20 * (1 + alpha * (T - 20))` with `alpha = 0.00393` for copper and `0.00403` for aluminium.

### DOM-21 (MEDIUM) Thermal loading is instantaneous ampacity ratio only
- **Location:** `power_balance_service.py` ~35-44 (0.75 / 0.90 thresholds).
- **Fix:**
  - Make the thresholds per feeder.
  - Apply ambient temperature derating to the rated ampacity (IEC 60287 / cable manufacturer tables).
  - Optionally add a first-order thermal model `dT/dt = (I^2 * R - (T - T_amb) / R_th) / C_th`, or at least use a 15-minute rolling average current for thermal status so that brief peaks do not trigger alarms.

### DOM-22 (MEDIUM) No ingestion bounds for electrical quantities
- **Location:** `backend/schemas/canonical.py` ~109 (only `activePowerKw >= 0`).
- **Fix:** Mark INVALID when any of these fails:
  - voltage within [0.85, 1.15] pu of nominal (statutory band is typically +/- 6% at LV in India, which should trigger a WARNING)
  - frequency within [47.5, 52.5] Hz (Indian grid code band 49.90-50.05 Hz triggers a WARNING outside it)
  - power factor within [-1, 1]
  - current >= 0
  - `|S| >= |P|`
  - the `S^2 = P^2 + Q^2` consistency check within tolerance

  Note that `activePowerKw >= 0` wrongly rejects PV export and BESS charging measurements. Use signed power with a documented sign convention.

### DOM-23 (MEDIUM) Balance timestamp uses wall clock
- **Location:** `power_balance_service.py` ~252 (`datetime.now(timezone.utc)`).
- **Fix:** Use the oldest `observedAt` among the contributing telemetry (worst-case freshness) and include `generatedAt` separately.

### DOM-24 (MEDIUM) Energy topology synthetic values
- **Location:** `energy_topology_service.py` ~97-147, ~244-247, ~538, ~663-664 (diurnal solar, RNG EV/BESS and frequency).
- **Fix:** Keep these as a SIMULATION generator only (see SP-02). For solar, use a clear-sky model with weather cloud cover (`P_pv = P_rated * (G / 1000) * (1 + gamma * (T_cell - 25))`), labeled SIMULATION.

### DOM-25 (LOW) Contract demand and peak factor hardcoded
- **Location:** `ml/inference/forecaster.py` ~30-44, ~189 (`* 0.85`).
- **Fix:** Store them per facility in the registry (contract demand from the utility agreement).

### DOM-26 (LOW) Building energy treats aliases as separate observations
- **Location:** `telemetry_streamer.py` ~339-345 (writes the same reading for every alias ID).
- **Impact:** Aggregates double count.
- **Fix:** Write once under the canonical ID, and resolve aliases at query time.

## Acceptance criteria
- `tests/test_signal_optimizer.py` includes a textbook two-phase case: phase 1 is EB/WB through with `q = 700/600` and `s = 1800*2`; phase 2 is NB/SB with `q = 400/450` and `s = 1800`. It asserts `Y = 700/3600 + 450/1800 = 0.4444` and `C_0 = (1.5 * 8 + 5) / (1 - 0.4444) = 30.6 s` (before min-cycle clamping), with L = 8 s for 2 phases at 4 s each.
- `tests/test_power_balance.py` asserts that missing feeder telemetry yields `UNKNOWN` status and that grid export is represented with a negative sign.
