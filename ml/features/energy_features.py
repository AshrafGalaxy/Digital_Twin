"""
energy_features.py

Feature engineering pipeline and dataset preparation for the 60-minute commercial building energy forecasting model.
Strictly enforces chronological ordering and zero feature leakage.
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from ml.features.civil_time import (
    is_commercial_mall_open,
    series_to_civil_time,
    to_civil_datetime,
)


ENERGY_FEATURE_COLUMNS = [
    "load_lag_1h",
    "load_lag_2h",
    "load_lag_3h",
    "load_lag_24h",
    "load_roll_mean_6h",
    "load_roll_max_6h",
    "load_roll_std_6h",
    "sin_hour",
    "cos_hour",
    "day_of_week",
    "is_weekend",
    "is_mall_open",
    "ambient_temp_c"
]

ENERGY_TARGET_COLUMN = "target_load_60m"


def generate_building_energy_history(
    building_id: str = "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
    days: int = 28,
    interval_minutes: int = 15,
    seed: int = 42,
    utc_offset_minutes: Optional[int] = None,
) -> pd.DataFrame:
    """
    Generates a 15-minute interval historical commercial building load profile stamped in UTC.
    Diurnal temperature, operating hours (10:00-22:00), and weekend occupancy evaluate on
    corridor local civil time via the configured UTC offset.
    """
    rng = np.random.default_rng(seed)
    n_steps = (days * 24 * 60) // interval_minutes
    start_time = datetime(2026, 8, 20, 0, 0, tzinfo=timezone.utc)

    records = []
    for step in range(n_steps):
        dt = start_time + timedelta(minutes=step * interval_minutes)
        civil_dt = to_civil_datetime(dt, utc_offset_minutes)
        hour = civil_dt.hour + (civil_dt.minute / 60.0)
        day_of_week = civil_dt.weekday()
        is_weekend = 1 if day_of_week in [5, 6] else 0

        # Ambient temperature (diurnal curve in civil time: min 23C at 05:00, max 35C at 14:30)
        temp_c = 24.0 + 9.5 * math.sin((hour - 8.5) * math.pi / 12.0) + rng.normal(0, 0.6)

        # Base load (security, data center, lighting, base ventilation): 1,250 kW
        base_kw = 1250.0

        # Commercial operating hours in local civil time: 10:00 to 22:00
        if 10.0 <= hour <= 22.0:
            is_mall_open = 1
            # HVAC & retail lighting load
            operational_load = 2200.0 + (1200.0 * (1 if is_weekend else 0.75))
            # Temperature-dependent chiller load
            cooling_load = max(0.0, (temp_c - 27.0) * 115.0)
        elif 8.0 <= hour < 10.0 or 22.0 < hour <= 23.5:
            is_mall_open = 0
            operational_load = 800.0  # Staff prep / cleaning
            cooling_load = max(0.0, (temp_c - 28.0) * 40.0)
        else:
            is_mall_open = 0
            operational_load = 0.0
            cooling_load = 0.0

        total_kw = base_kw + operational_load + cooling_load + rng.normal(0, 95.0)
        total_kw = float(np.clip(total_kw, 1100.0, 6200.0))

        records.append({
            "timestamp": dt,
            "building_id": building_id,
            "active_power_kw": round(total_kw, 2),
            "ambient_temp_c": round(temp_c, 1),
            "is_mall_open": is_mall_open
        })

    return pd.DataFrame(records)


def _build_single_energy_features(
    df: pd.DataFrame,
    utc_offset_minutes: Optional[int] = None,
) -> pd.DataFrame:
    """
    Transforms a single entity's 15-minute building load records into feature matrices.
    Reindexes onto a contiguous 15-minute grid so gaps are not treated as contiguous lags.
    """
    if len(df) == 0:
        return pd.DataFrame()

    df = df.copy()
    try:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    except (ValueError, TypeError):
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)

    # Reindex onto a contiguous 15-minute grid to prevent time gaps from bridging lags
    full_grid = pd.DataFrame({
        "timestamp": pd.date_range(
            start=df["timestamp"].min(),
            end=df["timestamp"].max(),
            freq="15min"
        )
    })
    merged = pd.merge(full_grid, df, on="timestamp", how="left")

    # Preserve entity identifier if present
    if "building_id" in df.columns and len(df["building_id"].dropna()) > 0:
        merged["building_id"] = df["building_id"].dropna().iloc[0]

    # Target: 60-min forward active power (4 steps for 15-minute series)
    merged[ENERGY_TARGET_COLUMN] = merged["active_power_kw"].shift(-4)

    # Lags (4 steps = 1h, 8 steps = 2h, 12 steps = 3h, 96 steps = 24h)
    merged["load_lag_1h"] = merged["active_power_kw"].shift(4)
    merged["load_lag_2h"] = merged["active_power_kw"].shift(8)
    merged["load_lag_3h"] = merged["active_power_kw"].shift(12)
    merged["load_lag_24h"] = merged["active_power_kw"].shift(96)

    # Rolling statistics over prior 6 hours (24 steps of 15m)
    merged["load_roll_mean_6h"] = merged["active_power_kw"].rolling(window=24, closed="left").mean()
    merged["load_roll_max_6h"] = merged["active_power_kw"].rolling(window=24, closed="left").max()
    merged["load_roll_std_6h"] = merged["active_power_kw"].rolling(window=24, closed="left").std().fillna(0.0)

    # Calendar cyclical features evaluated in corridor local civil time
    civil_ts = series_to_civil_time(merged["timestamp"], utc_offset_minutes)
    hour_float = civil_ts.dt.hour + civil_ts.dt.minute / 60.0
    merged["sin_hour"] = np.sin(2 * np.pi * hour_float / 24.0)
    merged["cos_hour"] = np.cos(2 * np.pi * hour_float / 24.0)
    merged["day_of_week"] = civil_ts.dt.weekday
    merged["is_weekend"] = merged["day_of_week"].isin([5, 6]).astype(int)
    if "is_mall_open" not in merged.columns or merged["is_mall_open"].isna().any():
        merged["is_mall_open"] = hour_float.apply(is_commercial_mall_open)

    merged = merged.dropna().reset_index(drop=True)
    return merged


def build_energy_features(
    df: pd.DataFrame,
    utc_offset_minutes: Optional[int] = None,
) -> pd.DataFrame:
    """
    Transforms raw 15-minute building load records into feature matrices.
    Target: active power shifted 4 steps (60 minutes) into the future.
    Features: calculated strictly using observations at or prior to time t.
    Guarantees entity isolation and drops invalid lags across time gaps (Section 4 of AGENTS.md).
    """
    if "building_id" in df.columns:
        groups = []
        for _, group_df in df.groupby("building_id", as_index=False):
            res = _build_single_energy_features(group_df, utc_offset_minutes=utc_offset_minutes)
            if len(res) > 0:
                groups.append(res)
        if not groups:
            return pd.DataFrame(columns=ENERGY_FEATURE_COLUMNS + [ENERGY_TARGET_COLUMN, "timestamp", "active_power_kw"])
        return pd.concat(groups, ignore_index=True).sort_values(["timestamp", "building_id"]).reset_index(drop=True)
    else:
        return _build_single_energy_features(df, utc_offset_minutes=utc_offset_minutes)


def extract_energy_features_row(
    hist: List[float],
    dt: datetime,
    ambient_temp_c: float,
    utc_offset_minutes: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Extracts the single-row feature vector for time step t, strictly matching
    the training feature engineering pipeline in build_energy_features().
    hist is assumed to end at the observation for time t (hist[-1] is P_t).
    Prior observations are used for hourly lags (4 steps/hour) and rolling stats.
    """
    if len(hist) < 97:
        hist = [hist[0]] * (97 - len(hist)) + list(hist)

    civil_dt = to_civil_datetime(dt, utc_offset_minutes)
    hour_float = civil_dt.hour + civil_dt.minute / 60.0
    return {
        "load_lag_1h": float(hist[-5]),
        "load_lag_2h": float(hist[-9]),
        "load_lag_3h": float(hist[-13]),
        "load_lag_24h": float(hist[-97]),
        "load_roll_mean_6h": float(np.mean(hist[-25:-1])),
        "load_roll_max_6h": float(np.max(hist[-25:-1])),
        "load_roll_std_6h": float(np.nan_to_num(np.std(hist[-25:-1], ddof=1), nan=0.0)),
        "sin_hour": math.sin(2 * math.pi * hour_float / 24.0),
        "cos_hour": math.cos(2 * math.pi * hour_float / 24.0),
        "day_of_week": civil_dt.weekday(),
        "is_weekend": 1 if civil_dt.weekday() in [5, 6] else 0,
        "is_mall_open": is_commercial_mall_open(hour_float),
        "ambient_temp_c": float(ambient_temp_c)
    }


def chronological_energy_split(
    df: pd.DataFrame,
    train_pct: float = 0.80,
    val_pct: float = 0.10,
    embargo_steps: int = 4
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits building load time-series chronologically into train, validation, and test splits.
    Enforces an embargo/purge gap of at least embargo_steps between splits
    to guarantee that training and validation target labels do not leak into subsequent splits.
    """
    n = len(df)
    train_idx = int(n * train_pct)
    val_idx = int(n * (train_pct + val_pct))

    train_end = max(0, train_idx - embargo_steps)
    val_end = max(train_idx, val_idx - embargo_steps)

    train_df = df.iloc[:train_end].copy()
    val_df = df.iloc[train_idx:val_end].copy()
    test_df = df.iloc[val_idx:].copy()

    return train_df, val_df, test_df
