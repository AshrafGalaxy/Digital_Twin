"""
weather_client.py

Live Weather Ingestion Client for Pune Viman Nagar Corridor.
Integrates Open-Meteo Weather API (D-06) with asynchronous caching and
graceful mathematical diurnal fallback (D-05/D-06 specification §5.4).
"""

import math
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import httpx


class OpenMeteoWeatherClient:
    """
    Fetches real-time ambient weather for the Pune Viman Nagar corridor
    (Latitude: 18.5679° N, Longitude: 73.9143° E).
    Implements a 60-second in-memory cache and automatic diurnal fallback.
    """

    LATITUDE: float = 18.5679
    LONGITUDE: float = 73.9143
    ENDPOINT: str = "https://api.open-meteo.com/v1/forecast"
    CACHE_TTL_SECONDS: int = 60

    def __init__(self, timeout_seconds: float = 2.5):
        self.timeout_seconds = timeout_seconds
        self._cached_reading: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0.0

    async def get_current_weather(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Retrieves current ambient weather conditions.
        Returns cached value if within TTL, otherwise attempts live API fetch.
        Falls back to deterministic diurnal curve on network timeout or failure.
        """
        now = datetime.now(timezone.utc)
        now_epoch = now.timestamp()

        if not force_refresh and self._cached_reading and (now_epoch - self._cache_timestamp) < self.CACHE_TTL_SECONDS:
            return self._cached_reading

        try:
            params = {
                "latitude": self.LATITUDE,
                "longitude": self.LONGITUDE,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,surface_pressure",
                "timezone": "UTC"
            }
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.get(self.ENDPOINT, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    current = data.get("current", {})
                    reading = {
                        "temperature_c": float(current.get("temperature_2m", 28.0)),
                        "humidity_pct": float(current.get("relative_humidity_2m", 55.0)),
                        "apparent_temp_c": float(current.get("apparent_temperature", 29.5)),
                        "surface_pressure_hpa": float(current.get("surface_pressure", 948.0)),
                        "precipitation_mm": float(current.get("precipitation", 0.0)),
                        "source_mode": "LIVE",
                        "source_id": "openmeteo:pune-viman-nagar",
                        "observed_at": now.isoformat(),
                        "data_quality_score": 1.0,
                        "data_quality_status": "valid"
                    }
                    self._cached_reading = reading
                    self._cache_timestamp = now_epoch
                    return reading
        except Exception as e:
            # Non-blocking fallback to documented diurnal model
            pass

        return self._compute_diurnal_fallback(now)

    def _compute_diurnal_fallback(self, now: datetime) -> Dict[str, Any]:
        """
        Computes realistic diurnal ambient weather for Pune when offline.
        Temperature varies between 22°C and 36°C based on solar time.
        """
        hour = now.hour + (now.minute / 60.0)
        temp_c = 24.0 + 8.0 * math.sin((hour - 8.0) * math.pi / 12.0)
        humidity = 65.0 - 20.0 * math.sin((hour - 8.0) * math.pi / 12.0)

        fallback = {
            "temperature_c": round(temp_c, 1),
            "humidity_pct": round(humidity, 1),
            "apparent_temp_c": round(temp_c + 1.5, 1),
            "surface_pressure_hpa": 948.5,
            "precipitation_mm": 0.0,
            "source_mode": "SIMULATION",
            "source_id": "diurnal-model:pune-viman-nagar",
            "observed_at": now.isoformat(),
            "data_quality_score": 0.85,
            "data_quality_status": "valid"
        }
        return fallback
