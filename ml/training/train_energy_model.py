"""
train_energy_model.py

Training script for the 60-minute building energy demand forecasting model.
Implements chronological splitting, persistence & same-hour baselines,
XGBoost primary model, quantile intervals, and artifact serialization.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import Any, Dict
import numpy as np
import pandas as pd
import joblib
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from ml.features.energy_features import (
    ENERGY_FEATURE_COLUMNS,
    ENERGY_TARGET_COLUMN,
    generate_building_energy_history,
    build_energy_features,
    chronological_energy_split
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = ROOT_DIR / "artifacts" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_energy_baselines(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame
) -> Dict[str, Dict[str, float]]:
    """
    Evaluates standard non-ML energy baselines:
    1. Persistence: y_hat_{t+60} = y_t
    2. Same-Hour Average: grouped by (hour, is_weekend) from train split
    """
    y_true = test_df[ENERGY_TARGET_COLUMN].values

    # 1. Persistence Baseline
    y_pred_persist = test_df["active_power_kw"].values
    persist_mae = float(mean_absolute_error(y_true, y_pred_persist))
    persist_rmse = float(root_mean_squared_error(y_true, y_pred_persist))

    # 2. Same-Hour Average Baseline
    train_df = train_df.copy()
    train_df["hour"] = train_df["timestamp"].dt.hour
    hist_map = train_df.groupby(["hour", "is_weekend"])[ENERGY_TARGET_COLUMN].mean().to_dict()

    test_hours = test_df["timestamp"].dt.hour.values
    test_weekends = test_df["is_weekend"].values
    y_pred_same_hour = np.array([hist_map.get((h, w), np.mean(y_true)) for h, w in zip(test_hours, test_weekends)])

    same_hour_mae = float(mean_absolute_error(y_true, y_pred_same_hour))
    same_hour_rmse = float(root_mean_squared_error(y_true, y_pred_same_hour))

    return {
        "persistence": {"mae": round(persist_mae, 2), "rmse": round(persist_rmse, 2)},
        "same_hour_average": {"mae": round(same_hour_mae, 2), "rmse": round(same_hour_rmse, 2)}
    }


def train_energy_forecaster(days: int = 35, seed: int = 42) -> Dict[str, Any]:
    """Trains, validates, and serializes the 60-minute building energy forecaster."""
    print(f"[+] Generating {days}-day building load history dataset...")
    raw_df = generate_building_energy_history(days=days, seed=seed)
    featured_df = build_energy_features(raw_df)
    print(f"[+] Total feature rows: {len(featured_df)}")

    # 1. Chronological Split (70% train, 15% val, 15% test)
    train_df, val_df, test_df = chronological_energy_split(featured_df, train_pct=0.70, val_pct=0.15)
    print(f"[+] Split sizes — Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

    X_train = train_df[ENERGY_FEATURE_COLUMNS]
    y_train = train_df[ENERGY_TARGET_COLUMN]

    X_val = val_df[ENERGY_FEATURE_COLUMNS]
    y_val = val_df[ENERGY_TARGET_COLUMN]

    X_test = test_df[ENERGY_FEATURE_COLUMNS]
    y_test = test_df[ENERGY_TARGET_COLUMN]

    # 2. Baseline Evaluation
    baseline_metrics = evaluate_energy_baselines(train_df, test_df)
    persist_mae = baseline_metrics["persistence"]["mae"]
    print(f"[+] Baseline (Persistence)  — Test MAE: {persist_mae:.2f} kW, RMSE: {baseline_metrics['persistence']['rmse']:.2f} kW")
    print(f"[+] Baseline (Same-Hour)    — Test MAE: {baseline_metrics['same_hour_average']['mae']:.2f} kW, RMSE: {baseline_metrics['same_hour_average']['rmse']:.2f} kW")

    # 3. Train Primary XGBoost Regressor
    print("[+] Training primary XGBoost regressor (energy-xgb-v1)...")
    xgb_model = XGBRegressor(
        n_estimators=160,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=seed,
        n_jobs=-1
    )
    xgb_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )

    # 4. Train Quantile Regressors for 80% Prediction Interval (p10 and p90)
    print("[+] Training quantile regressors for confidence bounds (p10 and p90)...")
    p10_model = XGBRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.07,
        objective="reg:quantileerror",
        quantile_alpha=0.10,
        random_state=seed
    )
    p10_model.fit(X_train, y_train, verbose=False)

    p90_model = XGBRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.07,
        objective="reg:quantileerror",
        quantile_alpha=0.90,
        random_state=seed
    )
    p90_model.fit(X_train, y_train, verbose=False)

    # 5. Evaluate on Test Set
    y_pred_test = xgb_model.predict(X_test)
    test_mae = float(mean_absolute_error(y_test, y_pred_test))
    test_rmse = float(root_mean_squared_error(y_test, y_pred_test))
    improvement_pct = ((persist_mae - test_mae) / persist_mae) * 100.0

    print(f"[+] Primary XGBoost Model   — Test MAE: {test_mae:.2f} kW, RMSE: {test_rmse:.2f} kW")
    print(f"[+] Improvement over Persistence Baseline: +{improvement_pct:.1f}%")

    # 6. Feature Importances
    importances = dict(zip(ENERGY_FEATURE_COLUMNS, [round(float(v), 4) for v in xgb_model.feature_importances_]))
    sorted_importances = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))

    # 7. Package and Serialize Artifact
    artifact = {
        "model_id": "energy-xgb-v1",
        "domain": "ENERGY",
        "target_metric": "activePowerKw",
        "target_entity": "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        "horizon_minutes": 60,
        "unit": "kW",
        "model": xgb_model,
        "model_p10": p10_model,
        "model_p90": p90_model,
        "features": ENERGY_FEATURE_COLUMNS,
        "feature_importances": sorted_importances,
        "metrics": {
            "test_mae": round(test_mae, 2),
            "test_rmse": round(test_rmse, 2),
            "improvement_vs_persistence_pct": round(improvement_pct, 1),
            "persistence_mae": persist_mae,
            "same_hour_mae": baseline_metrics["same_hour_average"]["mae"]
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "status": "APPROVED_FOR_DEMO",
        "source_limitation": "This pilot energy stream uses representative commercial building load patterns. It demonstrates the ML forecasting pipeline but does not measure direct Pune utility meter data."
    }

    artifact_path = MODELS_DIR / "energy_xgb_v1.joblib"
    joblib.dump(artifact, artifact_path)
    print(f"[OK] Saved model artifact to: {artifact_path}")

    # 8. Log into MLflow Local Registry
    try:
        from ml.training.mlflow_tracker import MLflowTracker
        tracker = MLflowTracker(experiment_name="Building_Energy_Forecasting")
        tracker.log_training_run(
            run_name="energy-xgb-v1-60m-load",
            parameters={
                "model_type": "XGBRegressor",
                "n_estimators": 140,
                "max_depth": 5,
                "learning_rate": 0.05,
                "horizon_minutes": 60,
                "training_days": days,
                "random_seed": seed,
                "train_pct": 0.70,
                "val_pct": 0.15,
                "test_pct": 0.15
            },
            metrics={
                "test_mae": round(test_mae, 2),
                "test_rmse": round(test_rmse, 2),
                "improvement_vs_persistence_pct": round(improvement_pct, 1),
                "baseline_persistence_mae": round(persist_mae, 2),
                "baseline_same_hour_mae": round(baseline_metrics["same_hour_average"]["mae"], 2)
            },
            tags={
                "domain": "ENERGY",
                "model_id": "energy-xgb-v1",
                "target_entity": "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
                "locality_caveat": "Representative commercial building load patterns.",
                "source_mode": "PREDICTED"
            },
            artifact_paths={"model_weights": artifact_path},
            feature_names=ENERGY_FEATURE_COLUMNS
        )
    except Exception as e:
        print(f"[!] Warning: MLflow run logging encountered: {e}")

    return artifact


if __name__ == "__main__":
    train_energy_forecaster()
