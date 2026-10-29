# 05. Machine Learning and Simulation

## Artifact inventory at audit date

| Path | Content | Status |
|---|---|---|
| `artifacts/models/traffic_xgb_v1.joblib` | XGBoost point model plus p10/p90 quantile models | Present (MAE 2.936, RMSE 3.688) |
| `artifacts/models/energy_xgb_v1.joblib` | Same structure | Present (MAE 93.61, RMSE 126.78) |
| `artifacts/mlflow/mlflow.db` | Local MLflow tracking | Present |
| `artifacts/evaluation_benchmarks.json` | E-01..E-06 outputs | Present, not read by API |
| `data/gold/features/*` | Feature store parquet/csv | Present (synthetic origin) |
| `data/raw/traffic/*.csv`, `data/raw/energy/uci_electricity_sample.csv` | Registered raw datasets | Present, **never used by training** |

## Summary

The pipeline is chronological and uses real XGBoost and TreeSHAP. But it falls short of the platform ML contract in four places:
1. the split ratio
2. conformal calibration
3. evaluation honesty
4. the training data source

The simulation path is rarely SUMO, and even when it is, the KPIs are constants.

---

## ML findings

### ML-01 (CRITICAL) Split is 70/15/15, not 80/10/10
- **Location:**
  - `ml/features/traffic_features.py` ~137-154 (defaults 0.70/0.15)
  - `ml/features/energy_features.py` ~126-129
  - `ml/training/train_traffic_model.py` ~80-81
  - `ml/training/train_energy_model.py` ~79-80
  - `ml/training/ablation_study.py` ~68-69
  - `scripts/run_evaluation_benchmarks.py` ~56
  - `tests/test_ml_forecasting.py` ~37, ~53
- **Fix:** Change defaults to `train_pct=0.80, val_pct=0.10`, retrain, re-register, and update tests. Add an assertion that indices are strictly increasing across splits.

### ML-02 (CRITICAL) Conformal intervals are hardcoded constants at the wrong levels
- **Location:** `ml/conformal_calibrator.py` lines ~20-74 and ~100-107.
- **Evidence:** `TRAFFIC_Q90 = 4.80`, `TRAFFIC_Q95 = 5.66`, `ENERGY_Q90 = 125.4`, `ENERGY_Q95 = 168.2`, `empiricalTestCoverage: 0.909 / 0.952`. The correct method `calibrate_from_residuals` (finite-sample quantile at level `ceil((n + 1) * (1 - a)) / n`) exists but is never called.
- **Fix:**
  1. After training, compute absolute residuals on the **validation (calibration) split**.
  2. For a = 0.20 and a = 0.10, take `q_a` = the `ceil((n + 1) * (1 - a))`-th smallest residual.
  3. Store `q_0.20` and `q_0.10` in the artifact.
  4. Measure empirical coverage on the **test split**, and store that in the artifact too.
  5. At inference, return the interval `[y_hat - q_a, y_hat + q_a]` for 80% and 90%.
  6. The UI "80% interval" must be this conformal interval, not the p10/p90 quantile models.

### ML-03 (CRITICAL) Evaluation fabricates 30m and 60m horizons
- **Location:** `backend/services/evaluation_service.py` ~71-89.
- **Evidence:** `y_test_30m = y_test_15m * 0.97 + rng.normal(0, 0.5, ...)`, `y_xgb_60m = 0.68 * y_xgb_15m + 0.32 * mean_roll_60m + noise_60m`.
- **Fix:** Delete it. Either train real 30m and 60m models (targets `shift(-6)`, `shift(-12)` at 5 min resolution) or report only 15m.

### ML-04 (CRITICAL) Evaluation coverage is computed on the same residuals used to set the quantile
- **Location:** `backend/services/evaluation_service.py` ~121-128 (`q90 = np.quantile(residuals, 0.90); cov_90 = mean(residuals <= q90)`).
- **Impact:** Coverage is tautologically close to nominal.
- **Fix:** Read the calibrated quantiles from the artifact (ML-02) and compute coverage on test.

### ML-05 (CRITICAL) Models are trained on RNG-generated series
- **Location:** `ml/features/traffic_features.py` ~48-80 (`generate_corridor_traffic_history` with `rng.normal`), and `ml/features/energy_features.py` (the equivalent generator). The registered raw datasets are never loaded.
- **Impact:** The reported MAE/RMSE measure the model's ability to learn the generator, not the real world.
- **Fix:**
  - Build the gold feature store from `data/raw/*` through `ml/features/feature_pipeline.py`, keeping the dataset manifests' honesty caveats.
  - Train from gold.
  - Record the dataset ID and hash in `model_versions`.
  - If only synthetic data is available, label the artifact `trainingDataProvenance: "SIMULATION"` and show that in the UI.

### ML-06 (CRITICAL) Heuristic forecasts are labeled PREDICTED and carry fabricated metrics
- **Location:**
  - `ml/inference/forecaster.py` ~78-101 (traffic `current_speed * 0.95`), ~191-215 (energy `current_kw * 1.02`)
  - `backend/services/forecast_service.py` ~78-90, ~108-120 (fake FALLBACK metrics)
  - The uncommitted change adds `modelTestMae: 3.8, persistenceMae: 4.5, accuracyGainPct: 15.6`; see WIP-01.
- **Fix:** Return `modelVersion: "persistence-fallback"`, `inputQualityStatus: "DEGRADED"`, and `baselineComparison: null`. The UI must show "Model unavailable, persistence fallback".

### ML-07 (CRITICAL) Evaluation uses heuristic predictions when the artifact is missing
- **Location:** `backend/services/evaluation_service.py` ~66-69 (`y_pers * 0.95 + 1.2`) and ~140-141 (`y_energy_pers * 0.94 + 50.0`).
- **Fix:** Return `status: "MODEL_UNAVAILABLE"` and no metrics.

### ML-08 (HIGH) Drift endpoint compares the reference set to itself
- **Location:** `backend/api/v1/endpoints/analytics.py` ~130-132 (`sample_df = detector.reference_df.sample(...)`).
- **Fix:** If the recent window has fewer than N rows (for example 200), return `status: "INSUFFICIENT_DATA"`.

### ML-09 (HIGH) Drift features mix segments
- **Location:** `ml/features/traffic_features.py` ~101-111 (sorts by timestamp only, then `shift`); `analytics.py` ~104-128 selects all segments.
- **Fix:** Use `df.groupby("segment_id", group_keys=False).apply(build_features)` so lags and rolls stay inside each entity.

### ML-10 (HIGH) PSI labels differ from the contract
- **Location:** `ml/drift_detector.py` ~122-150 (`SIGNIFICANT_DRIFT`, `MODERATE_DRIFT`, `DRIFT_DETECTED`, `EARLY_WARNING`).
- **Fix:** Use `STABLE` (PSI < 0.10), `WARNING` (0.10 <= PSI < 0.25) and `DRIFT` (PSI >= 0.25), per feature and overall (worst-of).

### ML-11 (HIGH) Baseline fallback leaks test labels
- **Location:** `ml/training/train_traffic_model.py` line ~61 and `train_energy_model.py` ~61 (`hist_map.get((h, w), np.mean(y_true))`).
- **Fix:** Fall back to the training-set global mean.

### ML-12 (HIGH) Two different uncertainty products disagree
- **Location:** `ml/inference/forecaster.py` ~72-74 (docstring claims an 80% PI) and ~132-161 (returns p10/p90 as `confidenceLower/Upper` plus separate conformal 90/95).
- **Fix:** Keep the quantile models for internal comparison only, and expose conformal 80/90 as the interval contract.

### ML-13 (HIGH) Duplicate, conflicting E-03 ablation implementations
- **Location:** `ml/training/ablation_study.py` (progressive groups) and `scripts/run_evaluation_benchmarks.py` `run_experiment_e03_ablation` (leave-one-group-out). Both write `evaluation_benchmarks.json`.
- **Fix:** Keep one implementation (leave-one-group-out is more informative) and give it one schema.

### ML-14 (HIGH) Benchmark JSON is not served by the API
- **Location:** `artifacts/evaluation_benchmarks.json` is produced, but `/analytics/evaluation/benchmarks` recomputes in memory.
- **Fix:** Have the API read the versioned benchmark file (or the `model_versions` table), and show the generation timestamp.

### ML-15 (HIGH) MLflow params differ from the trained model
- **Location:** `ml/training/train_energy_model.py` ~100-101 (trains 160 estimators) vs ~187 (logs 140).
- **Fix:** Log the params dict that was actually passed to the estimator.

### ML-16 (HIGH) Benchmark script crashes when artifacts are missing
- **Location:** `scripts/run_evaluation_benchmarks.py` ~76-78, ~120-122.
- **Fix:** Guard for missing artifacts, and exit non-zero with a clear message.

### ML-17 (MEDIUM) Padding missing lag history while reporting VALID
- **Location:** `ml/inference/forecaster.py` ~104-108, ~165, ~218-220.
- **Fix:** If more than 20% of the lag window is padded, set `inputQualityStatus: "DEGRADED"` and widen or suppress the intervals.

### ML-18 (MEDIUM) PSI edge cases
- **Location:** `ml/drift_detector.py` ~62-84.
- **Evidence:** It returns 0.0 for small n. `np.unique` on percentile edges collapses bins for discrete features and returns 0.0.
- **Fix:** Return `None` with `INSUFFICIENT_DATA`. Use category frequencies for discrete features, fixed reference bins for continuous ones, and `eps = 1e-6` without renormalizing.

### ML-19 (MEDIUM) Anomaly detector is trained on synthetic Gaussians
- **Location:** `backend/services/anomaly_detector.py` ~29-38.
- **Fix:** Fit IsolationForest on historical observations from the DB at startup (chronological, training window only), or label it a demo detector in the UI.

### ML-20 (MEDIUM) `is_mall_open` feature is not recomputed from timestamps
- **Location:** `ml/features/energy_features.py`.
- **Impact:** A `KeyError` occurs when real raw data lacks the column, and the feature name is facility-specific.
- **Fix:** Derive it from a configurable facility operating calendar, and rename it to `is_facility_open`.

### ML-21 (MEDIUM) Hardcoded horizons, clamps and contract thresholds
- **Location:** `forecaster.py` ~30-44 (contract kW per pilot building), ~138-140 (speed clamp 5-55), ~245-247 (energy clamp 1000-6500), ~189 (peak factor 0.85).
- **Fix:** Store these per entity in the asset registry, and store the clamp ranges in the model artifact (training min/max).

### ML-22 (MEDIUM) Model loading bypasses any registry
- **Location:** `forecaster.py` ~28 (`MODELS_DIR`).
- **Fix:** Load the version marked `production` in `model_versions` (or the MLflow registry), and expose the version in every forecast.

### ML-23 (LOW) Explainer silent failure
- See BE-22.

### ML-24 (LOW) Hyperparameters hardcoded in trainers
- **Fix:** Move them to a YAML config versioned with the artifact.

### ML-25 (LOW) No scheduled retraining or champion/challenger process
- **Fix:** Document a manual retrain runbook for the pilot. Automate after go-live.

---

## Simulation findings

### SIM-01 (CRITICAL) SUMO travel times are never collected, so KPIs collapse to constants
- **Location:** `simulation/runner.py` lines 114 and 142. `completed_travel_times = []` is never appended to, and `aggregate_vehicle_records(completed_travel_times=completed_travel_times or [145.0], waiting_times=... or [55.0], sampled_queue_lengths=... or [180.0])`. Throughput in `simulation/kpi_calculator.py` ~83-84 uses `len(completed_travel_times)`, which is about 1 veh/h.
- **Fix:**
  - Each step, record departures from `traci.simulation.getDepartedIDList()` with `traci.simulation.getTime()`.
  - For each ID in `getArrivedIDList()`, compute `arrival - depart`.
  - Sample `traci.vehicle.getWaitingTime` for active vehicles.
  - Sample queues with `traci.lane.getLastStepHaltingNumber * avg vehicle length`.
  - Never default to constants. If there are no samples, report `null` with a warning.

### SIM-02 (CRITICAL) Kinematic fallback is the usual path and the engine is hidden
- **Location:** `simulation/runner.py` ~149-270 (Webster-style formula plus `rng.uniform`); `scenario_service` drops `engine_used`. Benchmark E-04 shows a mean run time of 0.02 ms, which a SUMO run cannot achieve.
- **Fix:**
  - Persist and return `engineUsed` in {`SUMO_TRACI`, `KINEMATIC_FALLBACK`}.
  - The UI badge must reflect it.
  - In production, either install SUMO in the backend image or label every fallback result clearly.

### SIM-03 (HIGH) SUMO network paths are pilot-specific
- **Location:** `simulation/runner.py` ~33-34 (`viman_nagar.net.xml`).
- **Fix:** Resolve from the deployment config.

### SIM-04 (HIGH) TraCI program switch failure silently ignored
- **Location:** `simulation/runner.py` ~108-112 (`setProgram("VN-01", "1")`).
- **Fix:** Fail the run with a clear error, and take the TLS IDs from the registry.

### SIM-05 (MEDIUM) Kinematic fallback constants
- **Location:** `runner.py` ~167-254 (demand 2400 vph, cycle 120 s, greens 35/50).
- **Fix:** Derive them from the scenario template and registry capacities.

### SIM-06 (MEDIUM) Scenario persistence swallows errors
- See BE-02.

### SIM-07 (MEDIUM) No calibration or validation of the simulation against observed data
- **Fix:** For the pilot, compare simulated baseline speeds against REPLAY observations for the same time window (GEH statistic for flows, where `GEH = sqrt(2 * (M - C)^2 / (M + C))` and the target is GEH < 5 for 85% of links), and publish the result next to the scenario results.

### SIM-08 (LOW) Scenario titles use non-ASCII arrow characters
- **Location:** `scenario_service.py` ~206.
- **Fix:** Use plain ASCII "to".

## Acceptance criteria
- `tests/test_ml_forecasting.py` asserts an 80/10/10 split and empirical conformal coverage within +/- 3 points of nominal on test.
- `tests/test_simulation.py` runs a short SUMO scenario (when SUMO is available in CI) and asserts that travel time samples are greater than 0 and not equal to 145.0.
- No code path returns hardcoded MAE, coverage or KPI values.
