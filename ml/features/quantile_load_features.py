"""
quantile_load_features.py

Multi-horizon normalized quantile load feature engineering pipeline for commercial facilities.
Supports 15m, 60m, 240m (4h), and 1440m (24h) horizons with P10/P50/P90 quantiles,
strictly causal lags, degree-day weather features, and local civil-time cyclical encodings.
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ml.features.civil_time import series_to_civil_time, to_civil_datetime


QUANTILE_HORIZONS_MINUTES: List[int] = [15, 60, 240, 1440]

QUANTILE_ALPHAS: List[float] = [0.10, 0.50, 0.90]

QUANTILE_LOAD_FEATURE_COLUMNS: List[str] = [
    "norm_load_current",
    "norm_load_lag_15m",
    "norm_load_lag_30m",
    "norm_load_lag_60m",
    "norm_load_lag_24h",
    "norm_load_lag_168h",
    "norm_load_roll_mean_4h",
    "norm_load_roll_peak_4h",
    "cdd_degree_days",
    "hdd_degree_days",
    "relative_humidity_pct",
    "solar_irradiance_wm2",
    "sin_time",
    "cos_time",
    "day_of_week",
    "is_weekend",
    "is_holiday_flag",
]

QUANTILE_TARGET_COLUMNS: Dict[int, str] = {
    15: "target_norm_load_15m",
    60: "target_norm_load_60m",
    240: "target_norm_load_240m",
    1440: "target_norm_load_1440m",
}

_HORIZON_STEPS: Dict[int, int] = {
    15: 1,
    60: 4,
    240: 16,
    1440: 96,
}

_DEFAULT_FACILITY_PROFILES: List[Dict[str, Any]] = [
    {
        "building_id": "BLD-COMM-RETAIL-01",
        "contract_kw": 6800.0,
        "base_norm": 0.22,
        "peak_norm": 0.48,
        "open_hour": 10.0,
        "close_hour": 22.0,
        "weekend_mult": 1.15,
        "cooling_sens": 0.018,
    },
    {
        "building_id": "BLD-COMM-OFFICE-02",
        "contract_kw": 6010.0,
        "base_norm": 0.18,
        "peak_norm": 0.54,
        "open_hour": 8.5,
        "close_hour": 19.5,
        "weekend_mult": 0.35,
        "cooling_sens": 0.016,
    },
    {
        "building_id": "BLD-COMM-MIXED-03",
        "contract_kw": 4990.0,
        "base_norm": 0.25,
        "peak_norm": 0.44,
        "open_hour": 7.0,
        "close_hour": 23.0,
        "weekend_mult": 0.90,
        "cooling_sens": 0.014,
    },
]


def compute_degree_days(ambient_temp_c: float) -> Tuple[float, float]:
    """
    Computes Cooling Degree Days (base 24.0 C) and Heating Degree Days (base 18.0 C)
    from ambient temperature in Celsius.
    """
    temp = float(ambient_temp_c)
    cdd = max(0.0, temp - 24.0)
    hdd = max(0.0, 18.0 - temp)
    return (cdd, hdd)


def _estimate_solar_irradiance(hour_float: float) -> float:
    """
    Deterministic clear-sky diurnal solar irradiance curve (W/m2) in local civil time.
    Daylight window runs from 06:00 to 18:30 with midday peak around 12:15.
    """
    if 6.0 <= hour_float <= 18.5:
        phase = (hour_float - 6.0) / 12.5
        return round(float(900.0 * math.sin(math.pi * phase)), 2)
    return 0.0


def generate_multi_facility_load_dataset(
    days: int = 42,
    interval_minutes: int = 15,
    seed: int = 42,
    utc_offset_minutes: Optional[int] = None,
) -> pd.DataFrame:
    """
    Synthesizes 15-minute interval multi-facility commercial load and weather telemetry
    stamped in UTC, with diurnal operating schedules evaluated in local civil time.
    """
    rng = np.random.default_rng(seed)
    n_steps = (days * 24 * 60) // interval_minutes
    start_time = datetime(2026, 8, 1, 0, 0, tzinfo=timezone.utc)
    holiday_day_offsets = {14, 35}

    records: List[Dict[str, Any]] = []
    for step in range(n_steps):
        dt = start_time + timedelta(minutes=step * interval_minutes)
        civil_dt = to_civil_datetime(dt, utc_offset_minutes)
        hour_float = civil_dt.hour + (civil_dt.minute / 60.0)
        day_of_week = civil_dt.weekday()
        is_weekend = 1 if day_of_week in (5, 6) else 0
        day_index = (civil_dt.date() - to_civil_datetime(start_time, utc_offset_minutes).date()).days
        is_holiday_flag = 1 if day_index in holiday_day_offsets else 0

        # Shared corridor-level weather with stochastic micro-variation
        seasonal_shift = 1.5 * math.sin(2.0 * math.pi * (step / max(1, n_steps)))
        ambient_temp_c = (
            24.5
            + seasonal_shift
            + 9.0 * math.sin((hour_float - 8.5) * math.pi / 12.0)
            + float(rng.normal(0.0, 0.5))
        )
        relative_humidity_pct = float(
            np.clip(
                62.0
                - 18.0 * math.sin((hour_float - 8.5) * math.pi / 12.0)
                + float(rng.normal(0.0, 2.5)),
                20.0,
                95.0,
            )
        )
        clear_sky_solar = _estimate_solar_irradiance(hour_float)
        cloud_factor = float(np.clip(1.0 + rng.normal(0.0, 0.06), 0.70, 1.05))
        solar_irradiance_wm2 = round(clear_sky_solar * cloud_factor, 2) if clear_sky_solar > 0.0 else 0.0

        cdd, hdd = compute_degree_days(ambient_temp_c)

        for profile in _DEFAULT_FACILITY_PROFILES:
            building_id = str(profile["building_id"])
            contract_kw = float(profile["contract_kw"])
            base_norm = float(profile["base_norm"])
            peak_norm = float(profile["peak_norm"])
            open_hour = float(profile["open_hour"])
            close_hour = float(profile["close_hour"])
            weekend_mult = float(profile["weekend_mult"])
            cooling_sens = float(profile["cooling_sens"])

            if is_holiday_flag == 1:
                occ_mult = 0.40
            elif is_weekend == 1:
                occ_mult = weekend_mult
            else:
                occ_mult = 1.0

            if open_hour <= hour_float <= close_hour:
                mid_span = (close_hour - open_hour) / 2.0
                center = open_hour + mid_span
                diurnal_shape = 0.65 + 0.35 * math.cos(math.pi * (hour_float - center) / max(1.0, mid_span))
                op_norm = peak_norm * diurnal_shape * occ_mult
                thermal_norm = cooling_sens * cdd + 0.008 * hdd
            elif (open_hour - 1.5) <= hour_float < open_hour or close_hour < hour_float <= (close_hour + 1.0):
                op_norm = 0.25 * peak_norm * occ_mult
                thermal_norm = 0.4 * cooling_sens * cdd
            else:
                op_norm = 0.0
                thermal_norm = 0.0

            noise_norm = float(rng.normal(0.0, 0.018))
            norm_load = float(np.clip(base_norm + op_norm + thermal_norm + noise_norm, 0.10, 1.05))
            active_power_kw = round(norm_load * contract_kw, 2)

            records.append({
                "timestamp": dt,
                "building_id": building_id,
                "contract_kw": contract_kw,
                "active_power_kw": active_power_kw,
                "norm_load": round(active_power_kw / contract_kw, 6),
                "ambient_temp_c": round(ambient_temp_c, 2),
                "relative_humidity_pct": round(relative_humidity_pct, 2),
                "solar_irradiance_wm2": solar_irradiance_wm2,
                "is_holiday_flag": is_holiday_flag,
            })

    out_df = pd.DataFrame(records)
    if len(out_df) > 0:
        out_df = out_df.sort_values(["timestamp", "building_id"]).reset_index(drop=True)
    return out_df


def _build_single_quantile_load_features(
    df: pd.DataFrame,
    utc_offset_minutes: Optional[int] = None,
) -> pd.DataFrame:
    """
    Builds multi-horizon quantile load features and targets for a single facility.
    Reindexes onto a contiguous 15-minute grid so time gaps do not bridge causal lags.
    """
    if len(df) == 0:
        return pd.DataFrame()

    work = df.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], utc=True)
    work = work.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)

    full_grid = pd.DataFrame({
        "timestamp": pd.date_range(
            start=work["timestamp"].min(),
            end=work["timestamp"].max(),
            freq="15min",
        )
    })
    merged = pd.merge(full_grid, work, on="timestamp", how="left")

    if "building_id" in work.columns and len(work["building_id"].dropna()) > 0:
        merged["building_id"] = str(work["building_id"].dropna().iloc[0])

    if "contract_kw" in work.columns and len(work["contract_kw"].dropna()) > 0:
        contract_val = max(float(work["contract_kw"].dropna().iloc[0]), 1e-6)
        merged["contract_kw"] = contract_val
    elif "contract_kw" in merged.columns:
        merged["contract_kw"] = merged["contract_kw"].ffill().bfill().astype(float).clip(lower=1e-6)

    if "active_power_kw" in merged.columns and "contract_kw" in merged.columns:
        merged["norm_load"] = (
            merged["active_power_kw"].astype(float)
            / merged["contract_kw"].astype(float).clip(lower=1e-6)
        )
    elif "norm_load" in merged.columns:
        merged["norm_load"] = merged["norm_load"].astype(float)
    else:
        raise ValueError("Input DataFrame must contain active_power_kw with contract_kw, or norm_load.")

    # Multi-horizon targets via future shifts
    for horizon_min, target_col in QUANTILE_TARGET_COLUMNS.items():
        steps = _HORIZON_STEPS[horizon_min]
        merged[target_col] = merged["norm_load"].shift(-steps)

    # Strictly causal lags
    merged["norm_load_current"] = merged["norm_load"].shift(0)
    merged["norm_load_lag_15m"] = merged["norm_load"].shift(1)
    merged["norm_load_lag_30m"] = merged["norm_load"].shift(2)
    merged["norm_load_lag_60m"] = merged["norm_load"].shift(4)
    merged["norm_load_lag_24h"] = merged["norm_load"].shift(96)
    merged["norm_load_lag_168h"] = merged["norm_load"].shift(672)

    # 4-hour prior rolling statistics (16 steps of 15 min, strictly prior to time t)
    merged["norm_load_roll_mean_4h"] = merged["norm_load"].rolling(window=16, closed="left").mean()
    merged["norm_load_roll_peak_4h"] = merged["norm_load"].rolling(window=16, closed="left").max()

    # Local civil time cyclical and calendar features
    civil_dt = pd.DatetimeIndex(series_to_civil_time(merged["timestamp"], utc_offset_minutes))
    minutes_of_day = pd.Series(
        civil_dt.hour * 60.0 + civil_dt.minute + civil_dt.second / 60.0,
        index=merged.index,
    )
    hour_float = minutes_of_day / 60.0
    merged["sin_time"] = np.sin(2.0 * np.pi * minutes_of_day / 1440.0)
    merged["cos_time"] = np.cos(2.0 * np.pi * minutes_of_day / 1440.0)
    merged["day_of_week"] = civil_dt.weekday.astype(int)
    merged["is_weekend"] = merged["day_of_week"].isin([5, 6]).astype(int)

    if "is_holiday_flag" in merged.columns:
        merged["is_holiday_flag"] = merged["is_holiday_flag"].fillna(0).astype(int)
    else:
        merged["is_holiday_flag"] = 0

    if "ambient_temp_c" not in merged.columns or merged["ambient_temp_c"].isna().any():
        derived_temp = 24.5 + 9.0 * np.sin((hour_float - 8.5) * np.pi / 12.0)
        merged["ambient_temp_c"] = (
            merged["ambient_temp_c"].fillna(derived_temp)
            if "ambient_temp_c" in merged.columns
            else derived_temp
        )

    temp_series = merged["ambient_temp_c"].astype(float)
    merged["cdd_degree_days"] = np.maximum(0.0, temp_series - 24.0)
    merged["hdd_degree_days"] = np.maximum(0.0, 18.0 - temp_series)

    if "relative_humidity_pct" not in merged.columns or merged["relative_humidity_pct"].isna().any():
        merged["relative_humidity_pct"] = (
            merged["relative_humidity_pct"].fillna(55.0)
            if "relative_humidity_pct" in merged.columns
            else 55.0
        )

    if "solar_irradiance_wm2" not in merged.columns or merged["solar_irradiance_wm2"].isna().any():
        derived_solar = hour_float.apply(_estimate_solar_irradiance)
        merged["solar_irradiance_wm2"] = (
            merged["solar_irradiance_wm2"].fillna(derived_solar)
            if "solar_irradiance_wm2" in merged.columns
            else derived_solar
        )

    merged = merged.dropna().reset_index(drop=True)
    return merged


def build_quantile_load_features(
    df: pd.DataFrame,
    utc_offset_minutes: Optional[int] = None,
) -> pd.DataFrame:
    """
    Transforms 15-minute building load records into multi-horizon normalized quantile
    feature and target matrices. Enforces facility isolation across contiguous grids
    and drops rows with incomplete lag windows or future targets.
    """
    expected_cols = (
        QUANTILE_LOAD_FEATURE_COLUMNS
        + list(QUANTILE_TARGET_COLUMNS.values())
        + ["timestamp", "building_id", "active_power_kw", "contract_kw", "norm_load"]
    )
    if len(df) == 0:
        return pd.DataFrame(columns=expected_cols)

    if "building_id" in df.columns:
        groups: List[pd.DataFrame] = []
        for _, group_df in df.groupby("building_id", as_index=False):
            res = _build_single_quantile_load_features(group_df, utc_offset_minutes=utc_offset_minutes)
            if len(res) > 0:
                groups.append(res)
        if not groups:
            return pd.DataFrame(columns=expected_cols)
        combined = pd.concat(groups, ignore_index=True)
        return combined.sort_values(["timestamp", "building_id"]).reset_index(drop=True)

    single = _build_single_quantile_load_features(df, utc_offset_minutes=utc_offset_minutes)
    if len(single) == 0:
        return pd.DataFrame(columns=[c for c in expected_cols if c != "building_id"])
    return single.sort_values(["timestamp"]).reset_index(drop=True)


def extract_quantile_load_features_row(
    norm_hist: List[float],
    dt: datetime,
    ambient_temp_c: float,
    relative_humidity_pct: float = 55.0,
    solar_irradiance_wm2: Optional[float] = None,
    is_holiday_flag: int = 0,
    utc_offset_minutes: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Extracts a single-row normalized quantile load feature dictionary for time step t,
    strictly matching build_quantile_load_features().
    norm_hist[-1] corresponds to time t, [-2] to t-15m, [-3] to t-30m, [-5] to t-60m,
    [-97] to t-24h, [-673] to t-168h, and 4h rolling window uses norm_hist[-17:-1].
    """
    if not norm_hist:
        raise ValueError("norm_hist must contain at least one normalized load observation.")

    if len(norm_hist) < 673:
        pad_val = float(norm_hist[0])
        padded_hist: List[float] = [pad_val] * (673 - len(norm_hist)) + [float(x) for x in norm_hist]
    else:
        padded_hist = [float(x) for x in norm_hist]

    roll_window = padded_hist[-17:-1]
    cdd_val, hdd_val = compute_degree_days(ambient_temp_c)

    civil_dt = to_civil_datetime(dt, utc_offset_minutes)
    minutes_of_day = civil_dt.hour * 60.0 + civil_dt.minute + civil_dt.second / 60.0
    hour_float = minutes_of_day / 60.0
    solar_val = (
        float(solar_irradiance_wm2)
        if solar_irradiance_wm2 is not None
        else _estimate_solar_irradiance(hour_float)
    )
    day_of_week = int(civil_dt.weekday())
    is_weekend = 1 if day_of_week in (5, 6) else 0

    return {
        "norm_load_current": float(padded_hist[-1]),
        "norm_load_lag_15m": float(padded_hist[-2]),
        "norm_load_lag_30m": float(padded_hist[-3]),
        "norm_load_lag_60m": float(padded_hist[-5]),
        "norm_load_lag_24h": float(padded_hist[-97]),
        "norm_load_lag_168h": float(padded_hist[-673]),
        "norm_load_roll_mean_4h": float(np.mean(roll_window)),
        "norm_load_roll_peak_4h": float(np.max(roll_window)),
        "cdd_degree_days": float(cdd_val),
        "hdd_degree_days": float(hdd_val),
        "relative_humidity_pct": float(relative_humidity_pct),
        "solar_irradiance_wm2": float(solar_val),
        "sin_time": float(math.sin(2.0 * math.pi * minutes_of_day / 1440.0)),
        "cos_time": float(math.cos(2.0 * math.pi * minutes_of_day / 1440.0)),
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "is_holiday_flag": int(is_holiday_flag),
    }


def chronological_quantile_split(
    df: pd.DataFrame,
    train_pct: float = 0.80,
    val_pct: float = 0.10,
    embargo_steps: int = 96,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits multi-facility time-series data chronologically by unique timestamps so all
    facilities at any given timestamp remain aligned in the same partition, enforcing a
    purge gap of at least embargo_steps timestamp steps between splits.
    """
    if len(df) == 0:
        return df.copy(), df.copy(), df.copy()

    sort_cols = ["timestamp", "building_id"] if "building_id" in df.columns else ["timestamp"]
    ordered = df.sort_values(sort_cols).reset_index(drop=True)

    unique_ts = pd.Series(ordered["timestamp"]).drop_duplicates().sort_values().reset_index(drop=True)
    n_ts = len(unique_ts)

    train_idx = int(n_ts * train_pct)
    val_idx = int(n_ts * (train_pct + val_pct))

    train_end = max(0, train_idx - embargo_steps)
    val_end = max(train_idx, val_idx - embargo_steps)

    train_ts = set(unique_ts.iloc[:train_end].tolist())
    val_ts = set(unique_ts.iloc[train_idx:val_end].tolist())
    test_ts = set(unique_ts.iloc[val_idx:].tolist())

    train_df = ordered[ordered["timestamp"].isin(train_ts)].copy().reset_index(drop=True)
    val_df = ordered[ordered["timestamp"].isin(val_ts)].copy().reset_index(drop=True)
    test_df = ordered[ordered["timestamp"].isin(test_ts)].copy().reset_index(drop=True)

    return train_df, val_df, test_df
