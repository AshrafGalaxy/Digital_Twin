"""
traffic_features.py

Feature engineering pipeline and dataset preparation for the 15-minute traffic speed forecasting model.
Strictly enforces chronological ordering and zero feature leakage.
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "speed_lag_5m",
    "speed_lag_10m",
    "speed_lag_15m",
    "speed_lag_30m",
    "speed_lag_60m",
    "speed_roll_mean_30m",
    "speed_roll_std_30m",
    "speed_roll_mean_60m",
    "speed_roll_min_60m",
    "speed_roll_max_60m",
    "sin_hour",
    "cos_hour",
    "day_of_week",
    "is_weekend",
    "is_peak_hour",
    "ambient_temp_c"
]

TARGET_COLUMN = "target_speed_15m"


def generate_corridor_traffic_history(
    segment_id: str = "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
    days: int = 14,
    interval_minutes: int = 5,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a realistic 5-minute interval historical traffic series for the Viman Nagar EB corridor.
    Models diurnal rhythm, morning rush (08:30-10:30), heavy evening rush (18:00-20:30),
    weekend Phoenix Mall traffic surges, and realistic speed variance.
    """
    rng = np.random.default_rng(seed)
    n_steps = (days * 24 * 60) // interval_minutes
    start_time = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
    
    records = []
    for step in range(n_steps):
        dt = start_time + timedelta(minutes=step * interval_minutes)
        hour = dt.hour + (dt.minute / 60.0)
        day_of_week = dt.weekday()
        is_weekend = 1 if day_of_week in [5, 6] else 0

        # Base free-flow speed on Nagar Road EB is 48.0 km/h
        base_speed = 46.0

        # Diurnal pattern
        # Night (00:00 to 06:00): near free-flow (44 - 49 km/h)
        if 0 <= hour < 6:
            mean_speed = 46.5
        # Morning rush (08:30 to 11:00): moderate congestion (26 - 34 km/h)
        elif 8.5 <= hour <= 11.0:
            mean_speed = 28.5 if not is_weekend else 38.0
        # Evening rush (17:30 to 21:00): severe congestion near Phoenix Mall (14 - 24 km/h)
        elif 17.5 <= hour <= 21.0:
            mean_speed = 18.0 if not is_weekend else 20.5
        # Weekend mall rush (13:00 to 17:30)
        elif is_weekend and 13.0 <= hour < 17.5:
            mean_speed = 24.0
        # Midday off-peak
        else:
            mean_speed = 37.0

        # Stochastic fluctuations
        speed = float(np.clip(mean_speed + rng.normal(0, 3.5), 8.0, 52.0))

        # Ambient temperature in Pune (22°C to 36°C)
        temp_c = 24.0 + 8.0 * math.sin((hour - 8.0) * math.pi / 12.0) + rng.normal(0, 0.8)

        records.append({
            "timestamp": dt,
            "segment_id": segment_id,
            "speed_kmh": round(speed, 2),
            "ambient_temp_c": round(temp_c, 1)
        })

    return pd.DataFrame(records)


def _build_single_traffic_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms a single entity's 5-minute traffic records into feature matrices.
    Reindexes onto a contiguous 5-minute grid so gaps are not treated as contiguous lags.
    """
    if len(df) == 0:
        return pd.DataFrame()

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)

    # Reindex onto a contiguous 5-minute grid to prevent time gaps from bridging lags
    full_grid = pd.DataFrame({
        "timestamp": pd.date_range(
            start=df["timestamp"].min(),
            end=df["timestamp"].max(),
            freq="5min"
        )
    })
    merged = pd.merge(full_grid, df, on="timestamp", how="left")

    # Preserve entity identifier if present
    if "segment_id" in df.columns and len(df["segment_id"].dropna()) > 0:
        merged["segment_id"] = df["segment_id"].dropna().iloc[0]

    # 1. Target: 15-min forward speed (shift by -3 for 5-minute interval series)
    merged[TARGET_COLUMN] = merged["speed_kmh"].shift(-3)

    # 2. Lags (prior observations only)
    merged["speed_lag_5m"] = merged["speed_kmh"].shift(1)
    merged["speed_lag_10m"] = merged["speed_kmh"].shift(2)
    merged["speed_lag_15m"] = merged["speed_kmh"].shift(3)
    merged["speed_lag_30m"] = merged["speed_kmh"].shift(6)
    merged["speed_lag_60m"] = merged["speed_kmh"].shift(12)

    # 3. Rolling Statistics over past observations (excluding current target)
    merged["speed_roll_mean_30m"] = merged["speed_kmh"].rolling(window=6, closed="left").mean()
    merged["speed_roll_std_30m"] = merged["speed_kmh"].rolling(window=6, closed="left").std().fillna(0.0)
    merged["speed_roll_mean_60m"] = merged["speed_kmh"].rolling(window=12, closed="left").mean()
    merged["speed_roll_min_60m"] = merged["speed_kmh"].rolling(window=12, closed="left").min()
    merged["speed_roll_max_60m"] = merged["speed_kmh"].rolling(window=12, closed="left").max()

    # 4. Calendar Cyclical Features
    hour_float = merged["timestamp"].dt.hour + merged["timestamp"].dt.minute / 60.0
    merged["sin_hour"] = np.sin(2 * np.pi * hour_float / 24.0)
    merged["cos_hour"] = np.cos(2 * np.pi * hour_float / 24.0)
    merged["day_of_week"] = merged["timestamp"].dt.weekday
    merged["is_weekend"] = merged["day_of_week"].isin([5, 6]).astype(int)

    # Peak hour flag (08:30-10:30 or 17:30-21:00)
    merged["is_peak_hour"] = hour_float.apply(
        lambda h: 1 if (8.5 <= h <= 10.5 or 17.5 <= h <= 21.0) else 0
    )

    # 5. Drop rows with NaNs from lags, gaps, or future target shift
    merged = merged.dropna().reset_index(drop=True)
    return merged


def build_traffic_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw 5-minute traffic records into feature matrices.
    Target: speed shifted 3 steps (15 minutes) into the future.
    Features: calculated strictly using observations at or prior to time t.
    Guarantees entity isolation and drops invalid lags across time gaps (§4 of AGENTS.md).
    """
    if "segment_id" in df.columns:
        groups = []
        for _, group_df in df.groupby("segment_id", as_index=False):
            res = _build_single_traffic_features(group_df)
            if len(res) > 0:
                groups.append(res)
        if not groups:
            return pd.DataFrame(columns=FEATURE_COLUMNS + [TARGET_COLUMN, "timestamp", "speed_kmh"])
        return pd.concat(groups, ignore_index=True).sort_values(["timestamp", "segment_id"]).reset_index(drop=True)
    else:
        return _build_single_traffic_features(df)


def extract_traffic_features_row(
    hist: List[float],
    dt: datetime,
    ambient_temp_c: float
) -> Dict[str, Any]:
    """
    Extracts the single-row feature vector for time step t, strictly matching
    the training feature engineering pipeline in build_traffic_features().
    hist is assumed to end at the observation for time t (hist[-1] is S_t).
    Prior observations (hist[-2], hist[-3], etc.) are used for lags and rolling stats.
    """
    if len(hist) < 13:
        hist = [hist[0]] * (13 - len(hist)) + list(hist)

    hour_float = dt.hour + dt.minute / 60.0
    return {
        "speed_lag_5m": float(hist[-2]),
        "speed_lag_10m": float(hist[-3]),
        "speed_lag_15m": float(hist[-4]),
        "speed_lag_30m": float(hist[-7]),
        "speed_lag_60m": float(hist[-13]),
        "speed_roll_mean_30m": float(np.mean(hist[-7:-1])),
        "speed_roll_std_30m": float(np.nan_to_num(np.std(hist[-7:-1], ddof=1), nan=0.0)),
        "speed_roll_mean_60m": float(np.mean(hist[-13:-1])),
        "speed_roll_min_60m": float(np.min(hist[-13:-1])),
        "speed_roll_max_60m": float(np.max(hist[-13:-1])),
        "sin_hour": math.sin(2 * math.pi * hour_float / 24.0),
        "cos_hour": math.cos(2 * math.pi * hour_float / 24.0),
        "day_of_week": dt.weekday(),
        "is_weekend": 1 if dt.weekday() in [5, 6] else 0,
        "is_peak_hour": 1 if (8.5 <= hour_float <= 10.5 or 17.5 <= hour_float <= 21.0) else 0,
        "ambient_temp_c": float(ambient_temp_c)
    }


def chronological_split(
    df: pd.DataFrame,
    train_pct: float = 0.70,
    val_pct: float = 0.15,
    embargo_steps: int = 3
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits time-ordered data chronologically into train, validation, and test splits.
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
