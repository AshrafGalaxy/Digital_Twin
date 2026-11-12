"""
civil_time.py

Shared civil-timezone conversion and canonical diurnal boundary helpers
used across corridor traffic and building energy synthesis, offline feature
engineering, and online inference.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import pandas as pd


DEFAULT_CORRIDOR_UTC_OFFSET_MINUTES: int = 330


def get_corridor_utc_offset_minutes(offset_minutes: Optional[int] = None) -> int:
    """
    Resolves the configured corridor civil UTC offset in minutes.
    Falls back to DEFAULT_CORRIDOR_UTC_OFFSET_MINUTES (+330 / UTC+05:30)
    if backend settings cannot be imported.
    """
    if offset_minutes is not None:
        return int(offset_minutes)
    try:
        from backend.core.config import settings
        return int(settings.CORRIDOR_UTC_OFFSET_MINUTES)
    except Exception:
        return DEFAULT_CORRIDOR_UTC_OFFSET_MINUTES


def get_corridor_timezone(offset_minutes: Optional[int] = None) -> timezone:
    """Returns a fixed-offset timezone instance matching the corridor civil offset."""
    minutes = get_corridor_utc_offset_minutes(offset_minutes)
    return timezone(timedelta(minutes=minutes))


def ensure_utc_datetime(dt: Optional[datetime] = None) -> datetime:
    """
    Normalizes an instant to UTC. Naive datetimes are interpreted deterministically as UTC.
    Accepts Python datetime or pandas Timestamp objects.
    """
    if dt is None:
        return datetime.now(timezone.utc)
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_civil_datetime(dt: datetime, offset_minutes: Optional[int] = None) -> datetime:
    """
    Converts an instant (naive interpreted as UTC, UTC-aware, or localized)
    into the configured corridor local civil timezone.
    """
    utc_dt = ensure_utc_datetime(dt)
    return utc_dt.astimezone(get_corridor_timezone(offset_minutes))


def series_to_civil_time(
    ts_series: pd.Series,
    offset_minutes: Optional[int] = None,
) -> pd.Series:
    """
    Converts a pandas Series of timestamps (naive assumed UTC, UTC-aware, or mixed offsets)
    into corridor local civil time without mutating the caller's original column dtype.
    """
    utc_series = pd.to_datetime(ts_series, utc=True)
    return utc_series.dt.tz_convert(get_corridor_timezone(offset_minutes))


def is_traffic_peak_hour(hour_float: float) -> int:
    """
    Canonical corridor rush-hour indicator evaluated on local civil hour:
    Morning peak: 08:30 - 11:00 (harmonized with traffic history generator)
    Evening peak: 17:30 - 21:00
    """
    return 1 if (8.5 <= hour_float <= 11.0 or 17.5 <= hour_float <= 21.0) else 0


def is_commercial_mall_open(hour_float: float) -> int:
    """Canonical commercial operating window evaluated on local civil hour (10:00 - 22:00)."""
    return 1 if 10.0 <= hour_float <= 22.0 else 0

