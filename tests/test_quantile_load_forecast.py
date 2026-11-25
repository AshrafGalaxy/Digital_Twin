"""
test_quantile_load_forecast.py

Hermetic QA verification suite for Issue #17 (ENERGY-04):
- Dimensionless load normalization and cross-facility linear scaling portability
- Cooling/Heating Degree Days (CDD/HDD) and civil-time cyclical feature formulas
- Chronological 80/10/10 splitting with >= 96-step purge embargo gap (zero leakage)
- Holdout MAE superiority vs persistence baseline across [15, 60, 240, 1440] minutes
- Strict quantile monotonicity (p10Kw <= p50Kw <= p90Kw) and conformal interval enclosure
- Empirical 90% conformal coverage validity on chronological holdout test split
- Top-5 TreeSHAP attribution validation
- FastAPI GET /api/v1/energy/forecasts/load/{building_id} contract, capacity resolution,
  404 handling, and State Separation Invariant on persist=True
- Zero-emoji and zero-em/en-dash character scan across all Issue #17 files
"""

import asyncio
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.metrics import mean_absolute_error
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.core.database import AsyncSessionLocal
from backend.main import app
from backend.schemas.forecasts import MultiHorizonLoadForecastResponse
from ml.explainer import LocalModelExplainer
from ml.features.quantile_load_features import (
    QUANTILE_HORIZONS_MINUTES,
    QUANTILE_LOAD_FEATURE_COLUMNS,
    QUANTILE_TARGET_COLUMNS,
    build_quantile_load_features,
    chronological_quantile_split,
    compute_degree_days,
    extract_quantile_load_features_row,
    generate_multi_facility_load_dataset,
)
from ml.inference.quantile_load_service import QuantileLoadForecaster, quantile_load_forecaster

client = TestClient(app)


def _run_async(coro: Any) -> Any:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        return loop.run_until_complete(coro)
    return asyncio.run(coro)


def test_dimensionless_load_normalization_and_cross_facility_portability():
    """Verifies dimensionless norm_load engineering and exact linear capacity scaling across facilities."""
    ts = pd.date_range("2026-08-01 00:00", periods=800, freq="15min", tz="UTC")
    base_pattern = [0.35 + 0.25 * math.sin(2.0 * math.pi * (i % 96) / 96.0) for i in range(len(ts))]

    df_large = pd.DataFrame({
        "timestamp": ts,
        "building_id": "BLD-PORTABLE-6800",
        "contract_kw": 6800.0,
        "active_power_kw": [round(p * 6800.0, 2) for p in base_pattern],
        "ambient_temp_c": 29.0,
    })
    df_small = pd.DataFrame({
        "timestamp": ts,
        "building_id": "BLD-PORTABLE-2400",
        "contract_kw": 2400.0,
        "active_power_kw": [round(p * 2400.0, 2) for p in base_pattern],
        "ambient_temp_c": 29.0,
    })

    feat_large = build_quantile_load_features(df_large)
    feat_small = build_quantile_load_features(df_small)
    assert len(feat_large) > 0
    assert len(feat_large) == len(feat_small)
    assert np.allclose(
        feat_large["norm_load_current"].to_numpy(dtype=float),
        feat_small["norm_load_current"].to_numpy(dtype=float),
        atol=1e-4,
    )

    fixed_now = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)
    hist_norm = [0.40 + 0.15 * math.sin(2.0 * math.pi * i / 96.0) for i in range(673)]
    hist_6800 = [val * 6800.0 for val in hist_norm]
    hist_2400 = [val * 2400.0 for val in hist_norm]

    pred_6800 = quantile_load_forecaster.predict_multi_horizon_load(
        building_id="BLD-SCALE-6800",
        capacity_kw=6800.0,
        current_kw=3400.0,
        kw_history=hist_6800,
        ambient_temp_c=31.0,
        now_utc=fixed_now,
    )
    pred_2400 = quantile_load_forecaster.predict_multi_horizon_load(
        building_id="BLD-SCALE-2400",
        capacity_kw=2400.0,
        current_kw=1200.0,
        kw_history=hist_2400,
        ambient_temp_c=31.0,
        now_utc=fixed_now,
    )

    scale_ratio = 6800.0 / 2400.0
    horizons_6800 = pred_6800["horizons"]
    horizons_2400 = pred_2400["horizons"]
    assert len(horizons_6800) == 4
    assert len(horizons_2400) == 4

    for h_large, h_small in zip(horizons_6800, horizons_2400):
        assert int(h_large["horizonMinutes"]) == int(h_small["horizonMinutes"])
        for key in ("p10Kw", "p50Kw", "p90Kw"):
            expected_kw = float(h_small[key]) * scale_ratio
            assert abs(float(h_large[key]) - expected_kw) <= 0.35

        conf_large = h_large["conformalInterval90"]
        conf_small = h_small["conformalInterval90"]
        assert abs(float(conf_large[0]) - float(conf_small[0]) * scale_ratio) <= 0.45
        assert abs(float(conf_large[1]) - float(conf_small[1]) * scale_ratio) <= 0.45


def test_degree_days_and_civil_time_cyclical_features():
    """Verifies CDD/HDD threshold formulas, civil-time cyclical encodings, and online/offline feature parity."""
    cdd_hot, hdd_hot = compute_degree_days(32.0)
    assert cdd_hot == pytest.approx(8.0, abs=1e-9)
    assert hdd_hot == pytest.approx(0.0, abs=1e-9)

    cdd_neutral, hdd_neutral = compute_degree_days(21.0)
    assert cdd_neutral == pytest.approx(0.0, abs=1e-9)
    assert hdd_neutral == pytest.approx(0.0, abs=1e-9)

    cdd_cold, hdd_cold = compute_degree_days(12.5)
    assert cdd_cold == pytest.approx(0.0, abs=1e-9)
    assert hdd_cold == pytest.approx(5.5, abs=1e-9)

    hist = [0.5] * 673

    # 00:30 UTC + 330m = 06:00 civil time (quarter cycle -> sin=1.0, cos=0.0)
    dt_morning = datetime(2026, 8, 10, 0, 30, tzinfo=timezone.utc)
    row_morning = extract_quantile_load_features_row(
        norm_hist=hist,
        dt=dt_morning,
        ambient_temp_c=28.0,
        utc_offset_minutes=330,
    )
    assert row_morning["sin_time"] == pytest.approx(1.0, abs=1e-6)
    assert row_morning["cos_time"] == pytest.approx(0.0, abs=1e-6)
    assert row_morning["cdd_degree_days"] == pytest.approx(4.0, abs=1e-6)
    assert row_morning["hdd_degree_days"] == pytest.approx(0.0, abs=1e-6)
    assert row_morning["day_of_week"] == 0
    assert row_morning["is_weekend"] == 0

    # 06:30 UTC + 330m = 12:00 civil time (half cycle -> sin=0.0, cos=-1.0)
    dt_noon = datetime(2026, 8, 10, 6, 30, tzinfo=timezone.utc)
    row_noon = extract_quantile_load_features_row(
        norm_hist=hist,
        dt=dt_noon,
        ambient_temp_c=15.0,
        utc_offset_minutes=330,
    )
    assert row_noon["sin_time"] == pytest.approx(0.0, abs=1e-6)
    assert row_noon["cos_time"] == pytest.approx(-1.0, abs=1e-6)
    assert row_noon["cdd_degree_days"] == pytest.approx(0.0, abs=1e-6)
    assert row_noon["hdd_degree_days"] == pytest.approx(3.0, abs=1e-6)

    # Saturday 18:00 civil time (2026-08-15 12:30 UTC)
    dt_sat = datetime(2026, 8, 15, 12, 30, tzinfo=timezone.utc)
    row_sat = extract_quantile_load_features_row(
        norm_hist=hist,
        dt=dt_sat,
        ambient_temp_c=25.0,
        utc_offset_minutes=330,
    )
    assert row_sat["sin_time"] == pytest.approx(-1.0, abs=1e-6)
    assert row_sat["cos_time"] == pytest.approx(0.0, abs=1e-6)
    assert row_sat["day_of_week"] == 5
    assert row_sat["is_weekend"] == 1

    # Verify exact parity between batch build_quantile_load_features and single-row extractor
    raw_df = generate_multi_facility_load_dataset(days=12, seed=7, utc_offset_minutes=330)
    single_id = str(raw_df["building_id"].iloc[0])
    sub_raw = raw_df[raw_df["building_id"] == single_id].sort_values("timestamp").reset_index(drop=True)
    feat_df = build_quantile_load_features(sub_raw, utc_offset_minutes=330)
    assert len(feat_df) > 0

    probe_row = feat_df.iloc[10]
    probe_ts = pd.Timestamp(probe_row["timestamp"]).to_pydatetime()
    sub_raw_indexed = sub_raw.set_index("timestamp")
    pos = int(sub_raw_indexed.index.get_loc(probe_row["timestamp"]))
    hist_slice = sub_raw_indexed["norm_load"].iloc[pos - 672 : pos + 1].astype(float).tolist()
    raw_match = sub_raw_indexed.iloc[pos]

    online_row = extract_quantile_load_features_row(
        norm_hist=hist_slice,
        dt=probe_ts,
        ambient_temp_c=float(raw_match["ambient_temp_c"]),
        relative_humidity_pct=float(raw_match["relative_humidity_pct"]),
        solar_irradiance_wm2=float(raw_match["solar_irradiance_wm2"]),
        is_holiday_flag=int(raw_match["is_holiday_flag"]),
        utc_offset_minutes=330,
    )

    for col in QUANTILE_LOAD_FEATURE_COLUMNS:
        assert float(online_row[col]) == pytest.approx(float(probe_row[col]), abs=1e-6)


def test_chronological_split_80_10_10_and_purge_embargo_no_leakage():
    """Verifies chronological 80/10/10 split integrity with >= 96-step purge embargo gap."""
    raw_df = generate_multi_facility_load_dataset(days=42, seed=42)
    featured_df = build_quantile_load_features(raw_df)

    required_cols = QUANTILE_LOAD_FEATURE_COLUMNS + list(QUANTILE_TARGET_COLUMNS.values())
    assert featured_df[required_cols].isna().sum().sum() == 0

    train_df, val_df, test_df = chronological_quantile_split(
        featured_df,
        train_pct=0.80,
        val_pct=0.10,
        embargo_steps=96,
    )

    assert len(train_df) > 0
    assert len(val_df) > 0
    assert len(test_df) > 0

    train_ts = pd.to_datetime(train_df["timestamp"], utc=True)
    val_ts = pd.to_datetime(val_df["timestamp"], utc=True)
    test_ts = pd.to_datetime(test_df["timestamp"], utc=True)

    assert train_ts.max() < val_ts.min()
    assert val_ts.max() < test_ts.min()

    # Minimum 96-step (24-hour) purge embargo gap between splits
    embargo_delta = pd.Timedelta(minutes=96 * 15)
    assert (val_ts.min() - train_ts.max()) >= embargo_delta
    assert (test_ts.min() - val_ts.max()) >= embargo_delta

    # Verify timestamp partition sets are strictly disjoint
    assert set(train_ts).isdisjoint(set(val_ts))
    assert set(val_ts).isdisjoint(set(test_ts))
    assert set(train_ts).isdisjoint(set(test_ts))

    # Verify all facilities at each timestamp stay aligned in the same split
    n_facilities = featured_df["building_id"].nunique()
    assert len(train_df) % n_facilities == 0
    assert len(val_df) % n_facilities == 0
    assert len(test_df) % n_facilities == 0


def test_holdout_mae_beats_persistence_baseline_all_horizons():
    """Verifies trained P50 models beat persistence baseline MAE across [15, 60, 240, 1440]m on holdout test split."""
    artifact = quantile_load_forecaster.artifact
    assert isinstance(artifact, dict)
    assert artifact.get("model_id") == "energy-quantile-xgb-v2"

    raw_df = generate_multi_facility_load_dataset(days=42, seed=42)
    featured_df = build_quantile_load_features(raw_df)
    _, _, test_df = chronological_quantile_split(
        featured_df,
        train_pct=0.80,
        val_pct=0.10,
        embargo_steps=96,
    )

    X_test = test_df[QUANTILE_LOAD_FEATURE_COLUMNS]
    y_persist_norm = test_df["norm_load_current"].to_numpy(dtype=float)
    contract_kw = test_df["contract_kw"].to_numpy(dtype=float)

    models_map = artifact["models"]
    metrics_map = artifact["metrics"]

    for horizon_min in QUANTILE_HORIZONS_MINUTES:
        target_col = QUANTILE_TARGET_COLUMNS[horizon_min]
        y_true_norm = test_df[target_col].to_numpy(dtype=float)
        p50_model = models_map[horizon_min]["p50"]
        y_pred_norm = np.asarray(p50_model.predict(X_test), dtype=float)

        model_mae_norm = float(mean_absolute_error(y_true_norm, y_pred_norm))
        persist_mae_norm = float(mean_absolute_error(y_true_norm, y_persist_norm))

        model_mae_kw = float(mean_absolute_error(y_true_norm * contract_kw, y_pred_norm * contract_kw))
        persist_mae_kw = float(mean_absolute_error(y_true_norm * contract_kw, y_persist_norm * contract_kw))

        assert model_mae_norm < persist_mae_norm, (
            f"Horizon {horizon_min}m failed normalized MAE persistence check: "
            f"{model_mae_norm:.6f} >= {persist_mae_norm:.6f}"
        )
        assert model_mae_kw < persist_mae_kw, (
            f"Horizon {horizon_min}m failed kW MAE persistence check: "
            f"{model_mae_kw:.2f} >= {persist_mae_kw:.2f}"
        )

        logged_metrics = metrics_map[horizon_min]
        assert float(logged_metrics["improvementVsPersistencePct"]) > 0.0
        assert model_mae_norm == pytest.approx(float(logged_metrics["testMaeNorm"]), abs=1e-4)


def test_strict_quantile_monotonicity_and_conformal_intervals():
    """Verifies p10Kw <= p50Kw <= p90Kw and non-negative conformal intervals enclosing p50 across regimes."""
    scenarios: List[Dict[str, Any]] = [
        {"current_kw": 800.0, "ambient_temp_c": 16.0, "is_holiday_flag": 1},
        {"current_kw": 3400.0, "ambient_temp_c": 30.5, "is_holiday_flag": 0},
        {"current_kw": 6200.0, "ambient_temp_c": 43.0, "is_holiday_flag": 0},
        {"current_kw": None, "ambient_temp_c": 27.0, "is_holiday_flag": 0},
    ]

    for idx, params in enumerate(scenarios):
        res = quantile_load_forecaster.predict_multi_horizon_load(
            building_id=f"BLD-MONO-{idx}",
            capacity_kw=6800.0,
            current_kw=params["current_kw"],
            ambient_temp_c=float(params["ambient_temp_c"]),
            is_holiday_flag=int(params["is_holiday_flag"]),
        )
        horizons = res["horizons"]
        assert [int(h["horizonMinutes"]) for h in horizons] == QUANTILE_HORIZONS_MINUTES
        for h in horizons:
            p10 = float(h["p10Kw"])
            p50 = float(h["p50Kw"])
            p90 = float(h["p90Kw"])
            conf = h["conformalInterval90"]
            assert len(conf) == 2
            conf_lo = float(conf[0])
            conf_hi = float(conf[1])

            assert 0.0 <= p10 <= p50 <= p90
            assert 0.0 <= conf_lo <= p50 <= conf_hi
            assert conf_lo <= conf_hi

    # Also verify heuristic fallback monotonicity when artifact is absent
    fallback_forecaster = QuantileLoadForecaster(
        artifact_path=BASE_DIR / "artifacts" / "models" / "nonexistent_quantile_artifact.joblib"
    )
    fallback_res = fallback_forecaster.predict_multi_horizon_load(
        building_id="BLD-FALLBACK-TEST",
        capacity_kw=5000.0,
        current_kw=2500.0,
    )
    assert fallback_res["provenance"]["modelVersion"] == "energy-quantile-heuristic-fallback"
    assert fallback_res["provenance"]["qualityStatus"] == "DEGRADED"
    for h in fallback_res["horizons"]:
        conf_lo, conf_hi = float(h["conformalInterval90"][0]), float(h["conformalInterval90"][1])
        assert 0.0 <= float(h["p10Kw"]) <= float(h["p50Kw"]) <= float(h["p90Kw"])
        assert 0.0 <= conf_lo <= float(h["p50Kw"]) <= conf_hi


def test_conformal_90_empirical_holdout_coverage():
    """Verifies empirical 90% split-conformal coverage meets >= 90% target on chronological holdout test split."""
    artifact = quantile_load_forecaster.artifact
    assert isinstance(artifact, dict)

    raw_df = generate_multi_facility_load_dataset(days=42, seed=42)
    featured_df = build_quantile_load_features(raw_df)
    _, _, test_df = chronological_quantile_split(
        featured_df,
        train_pct=0.80,
        val_pct=0.10,
        embargo_steps=96,
    )

    X_test = test_df[QUANTILE_LOAD_FEATURE_COLUMNS]
    models_map = artifact["models"]
    conformal_map = artifact["conformal_calibrations"]

    for horizon_min in QUANTILE_HORIZONS_MINUTES:
        cal = conformal_map[horizon_min]
        assert cal["available"] is True
        q90_norm = float(cal["quantiles"]["90"]["quantile"])
        assert q90_norm > 0.0

        logged_cov90 = float(cal["empiricalCoverage"]["90"]["empiricalTestCoveragePct"])
        assert logged_cov90 >= 90.0

        target_col = QUANTILE_TARGET_COLUMNS[horizon_min]
        y_test = test_df[target_col].to_numpy(dtype=float)
        y_pred_p50 = np.asarray(models_map[horizon_min]["p50"].predict(X_test), dtype=float)

        empirical_cov = float(
            np.mean((y_test >= (y_pred_p50 - q90_norm)) & (y_test <= (y_pred_p50 + q90_norm)))
        )
        assert empirical_cov >= 0.90, (
            f"Horizon {horizon_min}m 90% conformal test coverage {empirical_cov:.4f} < 0.90"
        )


def test_top5_treeshap_attributions():
    """Verifies Top-5 TreeSHAP attribution fields, friendliness mapping, and descending magnitude sort."""
    res = quantile_load_forecaster.predict_multi_horizon_load(
        building_id="BLD-SHAP-CHECK",
        capacity_kw=6800.0,
        current_kw=4100.0,
        ambient_temp_c=33.5,
        relative_humidity_pct=62.0,
    )
    top_features = res["topFeatures"]
    assert len(top_features) == 5

    prev_abs = float("inf")
    for item in top_features:
        fname = str(item["feature"])
        shap_val = float(item["shapValue"])
        display_name = str(item["displayName"])
        impact = str(item["impact"])

        assert fname != ""
        assert fname in LocalModelExplainer.FEATURE_FRIENDLY_NAMES
        assert math.isfinite(shap_val)
        assert display_name == LocalModelExplainer.FEATURE_FRIENDLY_NAMES[fname]
        assert impact in ("INCREASES", "DECREASES")
        assert abs(shap_val) <= prev_abs + 1e-9
        prev_abs = abs(shap_val)


def test_api_known_facility_quantile_forecast():
    """Verifies GET /api/v1/energy/forecasts/load/{building_id} for known registered facilities."""
    for building_id, expected_cap in (
        ("urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01", 6800.0),
        ("BLD-SOLITAIRE-03", 2400.0),
    ):
        resp = client.get(f"/api/v1/energy/forecasts/load/{building_id}?current_kw=1800")
        assert resp.status_code == 200
        data = resp.json()
        parsed = MultiHorizonLoadForecastResponse(**data)

        assert parsed.buildingId == building_id
        assert parsed.capacityKw == pytest.approx(expected_cap, abs=0.01)
        assert parsed.provenance.sourceMode == "PREDICTED"
        assert parsed.provenance.modelVersion == "energy-quantile-xgb-v2"
        assert [h.horizonMinutes for h in parsed.horizons] == [15, 60, 240, 1440]
        assert len(parsed.topFeatures) == 5
        assert "non-actuating" in parsed.advisoryNotice.lower()


def test_api_arbitrary_facility_capacity_overrides_and_404():
    """Verifies portable ?contract_kw, ?sanctioned_load_kva overrides, and 404 when unknown without override."""
    # Arbitrary facility with contract_kw override
    res_3500 = client.get(
        "/api/v1/energy/forecasts/load/BLD-CUSTOM-PLANT-01?contract_kw=3500&current_kw=1750"
    )
    assert res_3500.status_code == 200
    d_3500 = res_3500.json()
    MultiHorizonLoadForecastResponse(**d_3500)
    assert float(d_3500["capacityKw"]) == pytest.approx(3500.0, abs=0.01)

    res_7000 = client.get(
        "/api/v1/energy/forecasts/load/BLD-CUSTOM-PLANT-01?contract_kw=7000&current_kw=3500"
    )
    assert res_7000.status_code == 200
    d_7000 = res_7000.json()
    assert float(d_7000["capacityKw"]) == pytest.approx(7000.0, abs=0.01)

    # Confirm 2x linear portability across API payloads
    for h_small, h_double in zip(d_3500["horizons"], d_7000["horizons"]):
        assert abs(float(h_double["p50Kw"]) - 2.0 * float(h_small["p50Kw"])) <= 0.3

    # Arbitrary facility with sanctioned_load_kva override (0.85 pf conversion)
    res_kva = client.get(
        "/api/v1/energy/forecasts/load/BLD-CUSTOM-PLANT-02?sanctioned_load_kva=4000&current_kw=1700"
    )
    assert res_kva.status_code == 200
    d_kva = res_kva.json()
    MultiHorizonLoadForecastResponse(**d_kva)
    assert float(d_kva["capacityKw"]) == pytest.approx(3400.0, abs=0.01)

    # Unknown facility without capacity override must return 404 Not Found
    res_404 = client.get("/api/v1/energy/forecasts/load/BLD-UNKNOWN-NO-CAPACITY-999")
    assert res_404.status_code == 404


def test_api_persist_state_separation_invariant():
    """Verifies persist=True writes PREDICTED ENERGY rows to forecasts without touching energy_observations."""
    test_building_id = "BLD-HERMETIC-PERSIST-99"

    async def _snapshot_counts() -> Dict[str, int]:
        async with AsyncSessionLocal() as session:
            obs_total_res = await session.execute(text("SELECT COUNT(*) FROM energy_observations"))
            obs_b_res = await session.execute(
                text("SELECT COUNT(*) FROM energy_observations WHERE building_id = :bid"),
                {"bid": test_building_id},
            )
            fc_b_res = await session.execute(
                text("SELECT COUNT(*) FROM forecasts WHERE entity_id = :bid"),
                {"bid": test_building_id},
            )
            return {
                "obs_total": int(obs_total_res.scalar() or 0),
                "obs_building": int(obs_b_res.scalar() or 0),
                "fc_building": int(fc_b_res.scalar() or 0),
            }

    async def _fetch_persisted_rows() -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                text("""
                    SELECT entity_id, domain, model_version_id, horizon_minutes,
                           source_mode, predicted_value, confidence_lower, confidence_upper, unit
                    FROM forecasts
                    WHERE entity_id = :bid
                    ORDER BY horizon_minutes ASC
                """),
                {"bid": test_building_id},
            )
            rows: List[Dict[str, Any]] = []
            for r in res.fetchall():
                rows.append({
                    "entity_id": str(r[0]),
                    "domain": str(r[1]),
                    "model_version_id": str(r[2]),
                    "horizon_minutes": int(r[3]),
                    "source_mode": str(r[4]),
                    "predicted_value": float(r[5]),
                    "confidence_lower": float(r[6]),
                    "confidence_upper": float(r[7]),
                    "unit": str(r[8]),
                })
            return rows

    async def _cleanup_test_rows() -> None:
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("DELETE FROM forecasts WHERE entity_id = :bid"),
                {"bid": test_building_id},
            )
            await session.commit()

    _run_async(_cleanup_test_rows())
    try:
        before = _run_async(_snapshot_counts())
        resp = client.get(
            f"/api/v1/energy/forecasts/load/{test_building_id}?contract_kw=4000&current_kw=2200&persist=true"
        )
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["provenance"]["sourceMode"] == "PREDICTED"

        after = _run_async(_snapshot_counts())
        assert after["obs_total"] == before["obs_total"]
        assert after["obs_building"] == 0
        assert after["fc_building"] == before["fc_building"] + 4

        rows = _run_async(_fetch_persisted_rows())
        assert len(rows) == 4
        assert [r["horizon_minutes"] for r in rows] == [15, 60, 240, 1440]
        for r in rows:
            assert r["domain"] == "ENERGY"
            assert r["source_mode"] == "PREDICTED"
            assert r["model_version_id"] == "energy-quantile-xgb-v2"
            assert r["unit"] == "kW"
            assert r["confidence_lower"] <= r["predicted_value"] <= r["confidence_upper"]
    finally:
        _run_async(_cleanup_test_rows())


def test_zero_emoji_and_zero_em_en_dash_across_issue_17_files():
    """Scans all Issue #17 modified and created files for emojis, em dashes, and en dashes."""
    issue_17_files = [
        BASE_DIR / "ml" / "features" / "quantile_load_features.py",
        BASE_DIR / "ml" / "explainer.py",
        BASE_DIR / "ml" / "training" / "train_quantile_load.py",
        BASE_DIR / "ml" / "inference" / "quantile_load_service.py",
        BASE_DIR / "backend" / "schemas" / "forecasts.py",
        BASE_DIR / "backend" / "core" / "schema_migrator.py",
        BASE_DIR / "backend" / "services" / "forecast_service.py",
        BASE_DIR / "backend" / "api" / "v1" / "endpoints" / "energy.py",
        BASE_DIR / "frontend" / "src" / "services" / "api.ts",
        BASE_DIR / "frontend" / "src" / "components" / "energy" / "QuantileLoadForecastPanel.tsx",
        BASE_DIR / "frontend" / "src" / "components" / "views" / "EnergyAnalyticsView.tsx",
        BASE_DIR / "tests" / "test_quantile_load_forecast.py",
    ]
    forbidden_pattern = re.compile(r"[\u2013\u2014\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F]")
    violations: List[str] = []
    for path in issue_17_files:
        assert path.exists(), f"Expected Issue #17 file missing: {path}"
        content = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(content.splitlines(), start=1):
            for match in forbidden_pattern.finditer(line):
                violations.append(
                    f"{path.relative_to(BASE_DIR)}:{line_no} char={hex(ord(match.group(0)))}"
                )
    assert violations == [], f"Forbidden characters detected: {violations}"
