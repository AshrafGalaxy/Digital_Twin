"""
train_quantile_load.py

Multi-horizon normalized quantile load training script (15m, 60m, 240m, 1440m).
Trains P10, P50, and P90 XGBoost quantile regressors on multi-facility normalized load
features, evaluates against persistence and same-hour prior-week baselines, fits
split-conformal calibration per horizon, and serializes the portable model artifact.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from xgboost import XGBRegressor

from ml.conformal_calibrator import ConformalPredictionCalibrator
from ml.features.quantile_load_features import (
    QUANTILE_ALPHAS,
    QUANTILE_HORIZONS_MINUTES,
    QUANTILE_LOAD_FEATURE_COLUMNS,
    QUANTILE_TARGET_COLUMNS,
    build_quantile_load_features,
    chronological_quantile_split,
    generate_multi_facility_load_dataset,
)

MODELS_DIR = ROOT_DIR / "artifacts" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_FILENAME = "quantile_load_xgb_v2.joblib"


def _build_prior_week_lookup(raw_df: pd.DataFrame) -> Dict[Tuple[str, pd.Timestamp], float]:
    """Builds a strictly causal lookup table mapping (building_id, utc_timestamp) to norm_load."""
    lookup: Dict[Tuple[str, pd.Timestamp], float] = {}
    if len(raw_df) == 0:
        return lookup

    ts_series = pd.to_datetime(raw_df["timestamp"], utc=True)
    b_ids = raw_df["building_id"].astype(str).tolist()
    norm_vals = raw_df["norm_load"].astype(float).tolist()
    for b_id, ts_val, norm_val in zip(b_ids, ts_series.tolist(), norm_vals):
        lookup[(str(b_id), pd.Timestamp(ts_val))] = float(norm_val)
    return lookup


def evaluate_quantile_baselines(
    raw_df: pd.DataFrame,
    test_df: pd.DataFrame,
    horizon_min: int,
    target_col: str,
    prior_week_lookup: Dict[Tuple[str, pd.Timestamp], float],
) -> Dict[str, Dict[str, float]]:
    """
    Evaluates two non-ML baselines on the chronological holdout test split:
      1. Persistence: y_hat_{t+h} = norm_load_current(t)
      2. Same-hour prior-week: y_hat_{t+h} = norm_load(t + h - 168h)
         (computed on contiguous UTC timestamps strictly prior to t, zero leakage).
    """
    y_true_norm = test_df[target_col].to_numpy(dtype=float)
    contract_kw = test_df["contract_kw"].to_numpy(dtype=float)
    y_true_kw = y_true_norm * contract_kw

    # 1. Persistence baseline: norm_load_current at time t
    y_persist_norm = test_df["norm_load_current"].to_numpy(dtype=float)
    y_persist_kw = y_persist_norm * contract_kw
    persist_mae_norm = float(mean_absolute_error(y_true_norm, y_persist_norm))
    persist_rmse_norm = float(root_mean_squared_error(y_true_norm, y_persist_norm))
    persist_mae_kw = float(mean_absolute_error(y_true_kw, y_persist_kw))
    persist_rmse_kw = float(root_mean_squared_error(y_true_kw, y_persist_kw))

    # 2. Same-hour prior-week baseline: norm_load at (t + h - 168h)
    test_ts = pd.to_datetime(test_df["timestamp"], utc=True).tolist()
    test_buildings = test_df["building_id"].astype(str).tolist()
    fallback_lags = test_df["norm_load_lag_168h"].to_numpy(dtype=float)
    delta_target = timedelta(minutes=int(horizon_min))
    delta_week = timedelta(hours=168)

    prior_week_preds: List[float] = []
    for idx, (b_id, ts_val) in enumerate(zip(test_buildings, test_ts)):
        t_cur = pd.Timestamp(ts_val)
        t_ref = t_cur + delta_target - delta_week
        if t_ref >= t_cur:
            raise ValueError(f"Leakage detected in prior-week baseline: t_ref={t_ref} >= t_cur={t_cur}")
        matched = prior_week_lookup.get((str(b_id), t_ref))
        if matched is not None:
            prior_week_preds.append(float(matched))
        else:
            prior_week_preds.append(float(fallback_lags[idx]))

    y_week_norm = np.asarray(prior_week_preds, dtype=float)
    y_week_kw = y_week_norm * contract_kw
    week_mae_norm = float(mean_absolute_error(y_true_norm, y_week_norm))
    week_rmse_norm = float(root_mean_squared_error(y_true_norm, y_week_norm))
    week_mae_kw = float(mean_absolute_error(y_true_kw, y_week_kw))
    week_rmse_kw = float(root_mean_squared_error(y_true_kw, y_week_kw))

    return {
        "persistence": {
            "maeNorm": round(persist_mae_norm, 6),
            "rmseNorm": round(persist_rmse_norm, 6),
            "maeKw": round(persist_mae_kw, 2),
            "rmseKw": round(persist_rmse_kw, 2),
        },
        "sameHourPriorWeek": {
            "maeNorm": round(week_mae_norm, 6),
            "rmseNorm": round(week_rmse_norm, 6),
            "maeKw": round(week_mae_kw, 2),
            "rmseKw": round(week_rmse_kw, 2),
        },
    }


def train_quantile_load_forecaster(days: int = 42, seed: int = 42) -> Dict[str, Any]:
    """
    Trains multi-horizon P10/P50/P90 XGBoost quantile regressors on normalized commercial
    load, validates against baselines, fits split-conformal calibration, and saves artifact.
    """
    print(f"[+] Generating {days}-day multi-facility load dataset (seed={seed})...")
    raw_df = generate_multi_facility_load_dataset(days=days, seed=seed)
    featured_df = build_quantile_load_features(raw_df)
    print(f"[+] Raw rows: {len(raw_df)}, Featured rows: {len(featured_df)}")

    train_df, val_df, test_df = chronological_quantile_split(
        featured_df,
        train_pct=0.80,
        val_pct=0.10,
        embargo_steps=96,
    )
    print(
        f"[+] Chronological split (embargo=96 steps) - "
        f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}"
    )

    X_train = train_df[QUANTILE_LOAD_FEATURE_COLUMNS]
    X_val = val_df[QUANTILE_LOAD_FEATURE_COLUMNS]
    X_test = test_df[QUANTILE_LOAD_FEATURE_COLUMNS]
    test_contract_kw = test_df["contract_kw"].to_numpy(dtype=float)

    prior_week_lookup = _build_prior_week_lookup(raw_df)

    models_by_horizon: Dict[int, Dict[str, XGBRegressor]] = {}
    metrics_by_horizon: Dict[int, Dict[str, Any]] = {}
    baseline_metrics_by_horizon: Dict[int, Dict[str, Dict[str, float]]] = {}
    conformal_by_horizon: Dict[int, Dict[str, Any]] = {}

    for horizon_min in QUANTILE_HORIZONS_MINUTES:
        target_col = QUANTILE_TARGET_COLUMNS[horizon_min]
        y_train = train_df[target_col].to_numpy(dtype=float)
        y_val = val_df[target_col].to_numpy(dtype=float)
        y_test = test_df[target_col].to_numpy(dtype=float)

        print(f"\n[+] Training quantile models for horizon={horizon_min}m ({target_col})...")
        horizon_models: Dict[str, XGBRegressor] = {}
        for alpha in QUANTILE_ALPHAS:
            q_label = f"p{int(round(alpha * 100))}"
            q_model = XGBRegressor(
                n_estimators=180,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.85,
                colsample_bytree=0.85,
                objective="reg:quantileerror",
                quantile_alpha=float(alpha),
                random_state=seed,
                n_jobs=-1,
            )
            q_model.fit(
                X_train,
                y_train,
                eval_set=[(X_val, y_val)],
                verbose=False,
            )
            horizon_models[q_label] = q_model

        models_by_horizon[horizon_min] = horizon_models

        # Evaluate baselines on holdout test split
        baselines = evaluate_quantile_baselines(
            raw_df=raw_df,
            test_df=test_df,
            horizon_min=horizon_min,
            target_col=target_col,
            prior_week_lookup=prior_week_lookup,
        )
        baseline_metrics_by_horizon[horizon_min] = baselines

        # Evaluate P50 median predictions on validation and holdout test splits
        p50_model = horizon_models["p50"]
        y_pred_val_p50 = np.asarray(p50_model.predict(X_val), dtype=float)
        y_pred_test_p50 = np.asarray(p50_model.predict(X_test), dtype=float)

        test_mae_norm = float(mean_absolute_error(y_test, y_pred_test_p50))
        test_rmse_norm = float(root_mean_squared_error(y_test, y_pred_test_p50))

        y_test_kw = y_test * test_contract_kw
        y_pred_test_kw = y_pred_test_p50 * test_contract_kw
        test_mae_kw = float(mean_absolute_error(y_test_kw, y_pred_test_kw))
        test_rmse_kw = float(root_mean_squared_error(y_test_kw, y_pred_test_kw))

        persist_mae_norm = float(baselines["persistence"]["maeNorm"])
        persist_mae_kw = float(baselines["persistence"]["maeKw"])
        week_mae_norm = float(baselines["sameHourPriorWeek"]["maeNorm"])
        week_mae_kw = float(baselines["sameHourPriorWeek"]["maeKw"])

        if test_mae_norm >= persist_mae_norm or test_mae_kw >= persist_mae_kw:
            raise RuntimeError(
                f"Horizon {horizon_min}m P50 model failed to beat persistence baseline: "
                f"model_mae_norm={test_mae_norm:.6f} vs persist_mae_norm={persist_mae_norm:.6f}, "
                f"model_mae_kw={test_mae_kw:.2f} vs persist_mae_kw={persist_mae_kw:.2f}"
            )

        improvement_vs_persist_pct = (
            ((persist_mae_norm - test_mae_norm) / persist_mae_norm) * 100.0
            if persist_mae_norm > 0.0
            else 0.0
        )
        improvement_vs_week_pct = (
            ((week_mae_norm - test_mae_norm) / week_mae_norm) * 100.0
            if week_mae_norm > 0.0
            else 0.0
        )

        # Fit split conformal calibration on normalized residuals
        val_residuals = y_val - y_pred_val_p50
        test_residuals = y_test - y_pred_test_p50
        conformal_summary = ConformalPredictionCalibrator.fit_calibration_summary(
            calibration_residuals=val_residuals,
            test_residuals=test_residuals,
            calibration_split="validation",
            test_split="test",
        )
        conformal_by_horizon[horizon_min] = conformal_summary

        # Empirical quantile coverage check for P10..P90
        y_pred_test_p10 = np.asarray(horizon_models["p10"].predict(X_test), dtype=float)
        y_pred_test_p90 = np.asarray(horizon_models["p90"].predict(X_test), dtype=float)
        p10_p90_cov_pct = float(np.mean((y_test >= y_pred_test_p10) & (y_test <= y_pred_test_p90)) * 100.0)

        metrics_by_horizon[horizon_min] = {
            "horizonMinutes": int(horizon_min),
            "testMaeNorm": round(test_mae_norm, 6),
            "testRmseNorm": round(test_rmse_norm, 6),
            "testMaeKw": round(test_mae_kw, 2),
            "testRmseKw": round(test_rmse_kw, 2),
            "persistenceMaeNorm": round(persist_mae_norm, 6),
            "persistenceMaeKw": round(persist_mae_kw, 2),
            "sameHourPriorWeekMaeNorm": round(week_mae_norm, 6),
            "sameHourPriorWeekMaeKw": round(week_mae_kw, 2),
            "improvementVsPersistencePct": round(improvement_vs_persist_pct, 2),
            "improvementVsPriorWeekPct": round(improvement_vs_week_pct, 2),
            "p10P90EmpiricalCoveragePct": round(p10_p90_cov_pct, 2),
        }

        print(
            f"    P50 Test MAE: {test_mae_norm:.5f} norm ({test_mae_kw:.2f} kW), "
            f"RMSE: {test_rmse_norm:.5f} norm ({test_rmse_kw:.2f} kW)"
        )
        print(
            f"    Persistence MAE: {persist_mae_norm:.5f} norm ({persist_mae_kw:.2f} kW) | "
            f"Prior-Week MAE: {week_mae_norm:.5f} norm ({week_mae_kw:.2f} kW)"
        )
        print(
            f"    Gain vs Persistence: +{improvement_vs_persist_pct:.2f}% | "
            f"P10-P90 Coverage: {p10_p90_cov_pct:.2f}%"
        )
        if conformal_summary.get("available"):
            q80 = float(conformal_summary["quantiles"]["80"]["quantile"])
            q90 = float(conformal_summary["quantiles"]["90"]["quantile"])
            cov80 = float(conformal_summary["empiricalCoverage"]["80"]["empiricalTestCoveragePct"])
            cov90 = float(conformal_summary["empiricalCoverage"]["90"]["empiricalTestCoveragePct"])
            print(
                f"    Conformal (norm) - 80%: +/-{q80:.5f} ({cov80:.2f}% test), "
                f"90%: +/-{q90:.5f} ({cov90:.2f}% test)"
            )

    artifact: Dict[str, Any] = {
        "model_id": "energy-quantile-xgb-v2",
        "domain": "ENERGY",
        "target_metric": "activePowerKw",
        "unit": "kW",
        "horizons_minutes": list(QUANTILE_HORIZONS_MINUTES),
        "quantiles": list(QUANTILE_ALPHAS),
        "features": list(QUANTILE_LOAD_FEATURE_COLUMNS),
        "models": models_by_horizon,
        "metrics": metrics_by_horizon,
        "baselineMetrics": baseline_metrics_by_horizon,
        "conformal_calibrations": conformal_by_horizon,
        "split_sizes": {
            "train": int(len(train_df)),
            "validation": int(len(val_df)),
            "test": int(len(test_df)),
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "status": "APPROVED_FOR_DEMO",
        "source_limitation": (
            "Multi-facility normalized commercial load quantile model trained on synthesized "
            "15-minute facility telemetry patterns. Scales linearly via facility contract_kw "
            "and does not measure live municipal utility meter feeds."
        ),
    }

    artifact_path = MODELS_DIR / ARTIFACT_FILENAME
    joblib.dump(artifact, artifact_path)
    print(f"\n[OK] Saved multi-horizon quantile artifact to: {artifact_path}")
    return artifact


if __name__ == "__main__":
    train_quantile_load_forecaster()
