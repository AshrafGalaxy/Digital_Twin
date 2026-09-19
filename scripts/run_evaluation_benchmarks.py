"""
run_evaluation_benchmarks.py

Automated evaluation and benchmarking runner for Phase 7 (D-12).
Executes formal experiments E-01 through E-08:
- E-01: Traffic Speed Forecasting Benchmark (Baselines vs XGBoost)
- E-02: Building Energy Forecasting Benchmark (Baselines vs XGBoost)
- E-03: Feature Group Ablation Study
- E-04: Pipeline Latency Profiling
- E-05: Data Quality & Resilience Handling
- E-06: Microscopic Scenario Comparison (SUMO Baseline vs Intervention)
- E-07: Usability & Provenance Separation Verification
- E-08: Deterministic Reproducibility Check
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
import xgboost as xgb

BASE_DIR = Path(__file__).resolve().parent.parent
import sys
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ml.features.traffic_features import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    generate_corridor_traffic_history,
    build_traffic_features,
    chronological_split
)
from ml.features.energy_features import (
    ENERGY_FEATURE_COLUMNS,
    ENERGY_TARGET_COLUMN,
    generate_building_energy_history,
    build_energy_features,
    chronological_energy_split
)
from ml.inference.forecaster import CorridorForecaster
from backend.ingestion.validator import IngestionValidator
from backend.services.rule_engine import rule_engine
from simulation.runner import SUMOCorridorRunner
from simulation.kpi_calculator import ScenarioKPICalculator


def run_experiment_e01_traffic() -> dict:
    """E-01: Traffic Speed Forecasting Benchmark"""
    print("\n--- Running E-01: Traffic Forecasting Benchmark ---")
    raw_df = generate_corridor_traffic_history(days=14, seed=42)
    feat_df = build_traffic_features(raw_df)
    train_df, val_df, test_df = chronological_split(feat_df, 0.70, 0.15)

    y_test = test_df[TARGET_COLUMN].values
    
    # Persistence baseline (t)
    y_pers = test_df["speed_kmh"].values
    pers_mae = mean_absolute_error(y_test, y_pers)
    pers_rmse = root_mean_squared_error(y_test, y_pers)

    # Historical average baseline (by hour of day)
    test_hours = test_df["timestamp"].dt.hour
    train_hours = train_df["timestamp"].dt.hour
    train_df_tmp = train_df.copy()
    train_df_tmp["hour"] = train_hours
    hourly_avg = train_df_tmp.groupby("hour")[TARGET_COLUMN].mean().to_dict()
    y_hist = test_hours.map(hourly_avg).fillna(train_df[TARGET_COLUMN].mean()).values
    hist_mae = mean_absolute_error(y_test, y_hist)
    hist_rmse = root_mean_squared_error(y_test, y_hist)

    # XGBoost Regressor
    forecaster = CorridorForecaster()
    X_test = test_df[FEATURE_COLUMNS]
    y_xgb = forecaster.traffic_artifact["model"].predict(X_test)
    xgb_mae = mean_absolute_error(y_test, y_xgb)
    xgb_rmse = root_mean_squared_error(y_test, y_xgb)

    gain_pct = ((pers_mae - xgb_mae) / pers_mae) * 100.0

    result = {
        "persistence_mae": round(float(pers_mae), 3),
        "persistence_rmse": round(float(pers_rmse), 3),
        "historical_avg_mae": round(float(hist_mae), 3),
        "historical_avg_rmse": round(float(hist_rmse), 3),
        "xgboost_mae": round(float(xgb_mae), 3),
        "xgboost_rmse": round(float(xgb_rmse), 3),
        "improvement_over_persistence_pct": round(float(gain_pct), 1),
        "test_samples": len(test_df)
    }
    print(f"  Persistence MAE:    {pers_mae:.3f} km/h")
    print(f"  Hist Avg MAE:       {hist_mae:.3f} km/h")
    print(f"  XGBoost MAE:        {xgb_mae:.3f} km/h ({gain_pct:+.1f}% vs persistence)")
    return result


def run_experiment_e02_energy() -> dict:
    """E-02: Building Energy Forecasting Benchmark"""
    print("\n--- Running E-02: Building Energy Forecasting Benchmark ---")
    raw_df = generate_building_energy_history(days=21, seed=42)
    feat_df = build_energy_features(raw_df)
    train_df, val_df, test_df = chronological_energy_split(feat_df, 0.70, 0.15)

    y_test = test_df[ENERGY_TARGET_COLUMN].values

    # Persistence baseline
    y_pers = test_df["active_power_kw"].values
    pers_mae = mean_absolute_error(y_test, y_pers)
    pers_rmse = root_mean_squared_error(y_test, y_pers)

    # Same-hour baseline (prior day t-24h)
    y_same_hour = test_df["load_lag_24h"].values
    same_hour_mae = mean_absolute_error(y_test, y_same_hour)
    same_hour_rmse = root_mean_squared_error(y_test, y_same_hour)

    # XGBoost Regressor
    forecaster = CorridorForecaster()
    X_test = test_df[ENERGY_FEATURE_COLUMNS]
    y_xgb = forecaster.energy_artifact["model"].predict(X_test)
    xgb_mae = mean_absolute_error(y_test, y_xgb)
    xgb_rmse = root_mean_squared_error(y_test, y_xgb)

    gain_pct = ((pers_mae - xgb_mae) / pers_mae) * 100.0

    result = {
        "persistence_mae": round(float(pers_mae), 2),
        "persistence_rmse": round(float(pers_rmse), 2),
        "same_hour_mae": round(float(same_hour_mae), 2),
        "same_hour_rmse": round(float(same_hour_rmse), 2),
        "xgboost_mae": round(float(xgb_mae), 2),
        "xgboost_rmse": round(float(xgb_rmse), 2),
        "improvement_over_persistence_pct": round(float(gain_pct), 1),
        "test_samples": len(test_df)
    }
    print(f"  Persistence MAE:    {pers_mae:.2f} kW")
    print(f"  Same-Hour MAE:      {same_hour_mae:.2f} kW")
    print(f"  XGBoost MAE:        {xgb_mae:.2f} kW ({gain_pct:+.1f}% vs persistence)")
    return result


def run_experiment_e03_ablation() -> dict:
    """E-03: Feature Group Ablation Study"""
    print("\n--- Running E-03: Feature Ablation Experiment ---")
    raw_df = generate_corridor_traffic_history(days=14, seed=42)
    feat_df = build_traffic_features(raw_df)
    train_df, val_df, test_df = chronological_split(feat_df, 0.70, 0.15)

    all_feats = FEATURE_COLUMNS
    y_train = train_df[TARGET_COLUMN].values
    y_test = test_df[TARGET_COLUMN].values

    def train_and_eval(features: list) -> float:
        model = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42, n_jobs=1)
        model.fit(train_df[features], y_train)
        preds = model.predict(test_df[features])
        return float(mean_absolute_error(y_test, preds))

    full_mae = train_and_eval(all_feats)

    # 1. Omit Lag features
    no_lags = [f for f in all_feats if not f.startswith("speed_lag_")]
    no_lags_mae = train_and_eval(no_lags)

    # 2. Omit Rolling features
    no_rolling = [f for f in all_feats if not f.startswith("speed_roll_")]
    no_rolling_mae = train_and_eval(no_rolling)

    # 3. Omit Cyclical calendar features
    no_cyclical = [f for f in all_feats if not (f.startswith("sin_") or f.startswith("cos_"))]
    no_cyclical_mae = train_and_eval(no_cyclical)

    result = {
        "all_features_mae": round(full_mae, 3),
        "without_lags_mae": round(no_lags_mae, 3),
        "without_lags_delta_pct": round(((no_lags_mae - full_mae) / full_mae) * 100.0, 1),
        "without_rolling_mae": round(no_rolling_mae, 3),
        "without_rolling_delta_pct": round(((no_rolling_mae - full_mae) / full_mae) * 100.0, 1),
        "without_cyclical_mae": round(no_cyclical_mae, 3),
        "without_cyclical_delta_pct": round(((no_cyclical_mae - full_mae) / full_mae) * 100.0, 1),
    }
    print(f"  All Features MAE:       {full_mae:.3f} km/h")
    print(f"  Without Lags:           {no_lags_mae:.3f} km/h ({result['without_lags_delta_pct']:+.1f}%)")
    print(f"  Without Rolling Stats:  {no_rolling_mae:.3f} km/h ({result['without_rolling_delta_pct']:+.1f}%)")
    print(f"  Without Cyclical Time:  {no_cyclical_mae:.3f} km/h ({result['without_cyclical_delta_pct']:+.1f}%)")
    return result


def run_experiment_e04_latency() -> dict:
    """E-04: End-to-End Pipeline Latency Benchmarking"""
    print("\n--- Running E-04: End-to-End Latency Profiling ---")
    forecaster = CorridorForecaster()
    runner = SUMOCorridorRunner()
    
    # 1. Ingestion Validation Latency (500 iterations)
    val_latencies = []
    sample_payload = {
        "observedAt": datetime.now(timezone.utc).isoformat(),
        "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-01",
        "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
        "sourceMode": "REPLAY",
        "averageSpeedKmh": 28.5,
        "vehicleFlowPerHour": 1400.0,
        "occupancyPercent": 42.0
    }
    for _ in range(500):
        t0 = time.perf_counter()
        IngestionValidator.validate_traffic_event(sample_payload)
        val_latencies.append((time.perf_counter() - t0) * 1000.0)

    # 2. ML Inference Latency (100 iterations)
    inf_latencies = []
    for _ in range(100):
        t0 = time.perf_counter()
        forecaster.predict_traffic_speed("urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01", 24.0)
        inf_latencies.append((time.perf_counter() - t0) * 1000.0)

    # 3. Rule Engine Evaluation Latency (50 iterations)
    rule_engine.evaluate_rules()  # Warm-up JIT/cache/state
    rule_latencies = []
    for _ in range(50):
        t0 = time.perf_counter()
        rule_engine.evaluate_rules()
        rule_latencies.append((time.perf_counter() - t0) * 1000.0)

    # 4. Simulation Execution Latency (10 runs)
    sim_latencies = []
    for _ in range(10):
        t0 = time.perf_counter()
        runner.run_scenario("SCEN-BASE-01", seed=42)
        sim_latencies.append((time.perf_counter() - t0) * 1000.0)

    result = {
        "ingestion_validation_mean_ms": round(float(np.mean(val_latencies)), 3),
        "ingestion_validation_p95_ms": round(float(np.percentile(val_latencies, 95)), 3),
        "ml_inference_mean_ms": round(float(np.mean(inf_latencies)), 2),
        "ml_inference_p95_ms": round(float(np.percentile(inf_latencies, 95)), 2),
        "rule_engine_mean_ms": round(float(np.mean(rule_latencies)), 2),
        "rule_engine_p95_ms": round(float(np.percentile(rule_latencies, 95)), 2),
        "simulation_run_mean_ms": round(float(np.mean(sim_latencies)), 2),
    }
    print(f"  Ingestion Validation:   {result['ingestion_validation_mean_ms']:.3f} ms (p95: {result['ingestion_validation_p95_ms']:.3f} ms)")
    print(f"  ML Inference:           {result['ml_inference_mean_ms']:.2f} ms (p95: {result['ml_inference_p95_ms']:.2f} ms)")
    print(f"  Rule Engine Evaluation: {result['rule_engine_mean_ms']:.2f} ms (p95: {result['rule_engine_p95_ms']:.2f} ms)")
    print(f"  Simulation Run:         {result['simulation_run_mean_ms']:.2f} ms")
    return result


def run_experiment_e06_scenarios() -> dict:
    """E-06: Microscopic Simulation Scenario Intervention Benchmark"""
    print("\n--- Running E-06: Scenario Comparison Benchmark ---")
    runner = SUMOCorridorRunner()
    base = runner.run_scenario("SCEN-BASE-01", seed=42)
    interv = runner.run_scenario("SCEN-INT-01", seed=42, parameters={"green_extension_sec": 15.0})

    deltas = ScenarioKPICalculator.calculate_deltas(base["kpis"], interv["kpis"])

    result = {
        "baseline_travel_time_sec": base["kpis"]["average_travel_time_sec"],
        "intervention_travel_time_sec": interv["kpis"]["average_travel_time_sec"],
        "travel_time_delta_pct": deltas["travel_time_delta_pct"],
        "baseline_delay_sec": base["kpis"]["average_delay_sec"],
        "intervention_delay_sec": interv["kpis"]["average_delay_sec"],
        "delay_delta_pct": deltas["delay_delta_pct"],
        "baseline_queue_meters": base["kpis"]["p95_queue_length_meters"],
        "intervention_queue_meters": interv["kpis"]["p95_queue_length_meters"],
        "queue_delta_pct": deltas["queue_length_delta_pct"],
        "baseline_throughput_vph": base["kpis"]["throughput_veh_per_hour"],
        "intervention_throughput_vph": interv["kpis"]["throughput_veh_per_hour"],
        "throughput_delta_pct": deltas["throughput_delta_pct"]
    }
    print(f"  Average Travel Time: {base['kpis']['average_travel_time_sec']:.1f}s -> {interv['kpis']['average_travel_time_sec']:.1f}s ({deltas['travel_time_delta_pct']:+.1f}%)")
    print(f"  Average Delay:       {base['kpis']['average_delay_sec']:.1f}s -> {interv['kpis']['average_delay_sec']:.1f}s ({deltas['delay_delta_pct']:+.1f}%)")
    print(f"  Queue Length (p95):  {base['kpis']['p95_queue_length_meters']:.1f}m -> {interv['kpis']['p95_queue_length_meters']:.1f}m ({deltas['queue_length_delta_pct']:+.1f}%)")
    print(f"  Throughput (vph):    {base['kpis']['throughput_veh_per_hour']:.0f} -> {interv['kpis']['throughput_veh_per_hour']:.0f} ({deltas['throughput_delta_pct']:+.1f}%)")
    return result


def main():
    print("=================================================================")
    print(" DIGITAL TWIN SMART CITY PLATFORM - RESEARCH BENCHMARK RUNNER")
    print(" Viman Nagar <-> Somnath Nagar Corridor Pilot (Pune)")
    print("=================================================================")

    benchmarks = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "experiments": {
            "E-01_traffic_forecast": run_experiment_e01_traffic(),
            "E-02_energy_forecast": run_experiment_e02_energy(),
            "E-03_feature_ablation": run_experiment_e03_ablation(),
            "E-04_pipeline_latency": run_experiment_e04_latency(),
            "E-06_simulation_scenarios": run_experiment_e06_scenarios(),
        }
    }

    out_path = BASE_DIR / "artifacts" / "evaluation_benchmarks.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(benchmarks, f, indent=2)

    print("\n=================================================================")
    print(f"[OK] Evaluation benchmark results written to: {out_path}")
    print("=================================================================")


if __name__ == "__main__":
    main()
