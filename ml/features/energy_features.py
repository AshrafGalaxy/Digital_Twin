"""
energy_features.py

Feature engineering pipeline and dataset preparation for the 60-minute commercial building energy forecasting model.
Strictly enforces chronological ordering and zero feature leakage.
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd


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
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a 15-minute interval historical load profile for Phoenix Marketcity commercial building.
    Models base nighttime load (~1,400 kW), retail/HVAC ramp up (10:00 to 14:00),
    afternoon cooling peak (3,800 - 5,400 kW), weekend entertainment crowd surges,
    and temperature-driven chiller demand.
    """
    rng = np.random.default_rng(seed)
    n_steps = (days * 24 * 60) // interval_minutes
    start_time = datetime(2026, 8, 20, 0, 0, tzinfo=timezone.utc)

    records = []
    for step in range(n_steps):
        dt = start_time + timedelta(minutes=step * interval_minutes)
        hour = dt.hour + (dt.minute / 60.0)
        day_of_week = dt.weekday()
        is_weekend = 1 if day_of_week in [5, 6] else 0

        # Ambient temperature (diurnal curve: min 23°C at 05:00, max 35°C at 14:30)
        temp_c = 24.0 + 9.5 * math.sin((hour - 8.5) * math.pi / 12.0) + rng.normal(0, 0.6)

        # Base load (security, data center, lighting, base ventilation): 1,200 kW
        base_kw = 1250.0

        # Commercial operating hours: 10:00 to 22:00
        if 10.0 <= hour <= 22.0:
            is_mall_open = 1
            # HVAC & retail lighting load
            operational_load = 2200.0 + (1200.0 * (1 if is_weekend else 0.75))
            # Temperature-dependent chiller load (+90 kW per degree above 28°C)
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


def build_energy_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw 15-minute building load records into feature matrices.
    Target: active power shifted 4 steps (60 minutes) into the future.
    Features: calculated strictly using observations at or prior to time t.
    """
    df = df.copy().sort_values("timestamp").reset_index(drop=True)

    # Target: 60-min forward active power (4 steps for 15-minute series)
    df[ENERGY_TARGET_COLUMN] = df["active_power_kw"].shift(-4)

    # Lags (4 steps = 1h, 8 steps = 2h, 12 steps = 3h, 96 steps = 24h)
    df["load_lag_1h"] = df["active_power_kw"].shift(4)
    df["load_lag_2h"] = df["active_power_kw"].shift(8)
    df["load_lag_3h"] = df["active_power_kw"].shift(12)
    df["load_lag_24h"] = df["active_power_kw"].shift(96)

    # Rolling statistics over prior 6 hours (24 steps of 15m)
    df["load_roll_mean_6h"] = df["active_power_kw"].rolling(window=24, closed="left").mean()
    df["load_roll_max_6h"] = df["active_power_kw"].rolling(window=24, closed="left").max()
    df["load_roll_std_6h"] = df["active_power_kw"].rolling(window=24, closed="left").std().fillna(0.0)

    # Calendar cyclical features
    hour_float = df["timestamp"].dt.hour + df["timestamp"].dt.minute / 60.0
    df["sin_hour"] = np.sin(2 * np.pi * hour_float / 24.0)
    df["cos_hour"] = np.cos(2 * np.pi * hour_float / 24.0)
    df["day_of_week"] = df["timestamp"].dt.weekday
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    df = df.dropna().reset_index(drop=True)
    return df


def chronological_energy_split(
    df: pd.DataFrame,
    train_pct: float = 0.70,
    val_pct: float = 0.15
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits building load time-series chronologically into train, validation, and test splits.
    """
    n = len(df)
    train_idx = int(n * train_pct)
    val_idx = int(n * (train_pct + val_pct))

    return df.iloc[:train_idx].copy(), df.iloc[train_idx:val_idx].copy(), df.iloc[val_idx:].copy()
