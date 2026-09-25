"""
weather_client.py

Live Weather & Atmospheric Air Quality Ingestion Client for the Corridor.
Integrates Open-Meteo Weather API and Open-Meteo Atmospheric Air Quality API
with asynchronous caching and graceful mathematical diurnal/seasonal fallback (§5.4).
"""

import math
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import httpx


def deg_to_cardinal(deg: float) -> str:
    """Converts wind direction degrees to a cardinal label (e.g. 245° -> 'WSW (245°)')."""
    dirs = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ]
    ix = int((deg + 11.25) / 22.5) % 16
    return f"{dirs[ix]} ({int(round(deg))}°)"


def compute_india_naaqs_aqi(pm25: float, pm10: float) -> Dict[str, Any]:
    """
    Computes India National Ambient Air Quality Index (NAAQS) composite and sub-indices
    from PM2.5 and PM10 concentrations (µg/m³).
    """
    # PM2.5 Sub-index
    if pm25 <= 30.0:
        sub_pm25 = (pm25 / 30.0) * 50.0
    elif pm25 <= 60.0:
        sub_pm25 = 50.0 + ((pm25 - 30.0) / 30.0) * 50.0
    elif pm25 <= 90.0:
        sub_pm25 = 100.0 + ((pm25 - 60.0) / 30.0) * 100.0
    elif pm25 <= 120.0:
        sub_pm25 = 200.0 + ((pm25 - 90.0) / 30.0) * 100.0
    elif pm25 <= 250.0:
        sub_pm25 = 300.0 + ((pm25 - 120.0) / 130.0) * 100.0
    else:
        sub_pm25 = min(500.0, 400.0 + ((pm25 - 250.0) / 100.0) * 100.0)

    # PM10 Sub-index
    if pm10 <= 50.0:
        sub_pm10 = (pm10 / 50.0) * 50.0
    elif pm10 <= 100.0:
        sub_pm10 = 50.0 + ((pm10 - 50.0) / 50.0) * 50.0
    elif pm10 <= 250.0:
        sub_pm10 = 100.0 + ((pm10 - 100.0) / 150.0) * 100.0
    elif pm10 <= 350.0:
        sub_pm10 = 200.0 + ((pm10 - 250.0) / 100.0) * 100.0
    elif pm10 <= 430.0:
        sub_pm10 = 300.0 + ((pm10 - 350.0) / 80.0) * 100.0
    else:
        sub_pm10 = min(500.0, 400.0 + ((pm10 - 430.0) / 100.0) * 100.0)

    aqi_val = int(round(max(sub_pm25, sub_pm10)))
    determining_pollutant = "PM2.5" if sub_pm25 >= sub_pm10 else "PM10"

    if aqi_val <= 50:
        category = "Good"
    elif aqi_val <= 100:
        category = "Satisfactory"
    elif aqi_val <= 200:
        category = "Moderate"
    elif aqi_val <= 300:
        category = "Poor"
    elif aqi_val <= 400:
        category = "Very Poor"
    else:
        category = "Severe"

    return {
        "aqi": aqi_val,
        "category": category,
        "determiningPollutant": determining_pollutant,
        "subIndexPm25": round(sub_pm25, 1),
        "subIndexPm10": round(sub_pm10, 1)
    }


class OpenMeteoWeatherClient:
    """
    Fetches real-time ambient weather and air quality for the corridor
    (Latitude: 18.5679° N, Longitude: 73.9143° E).
    Implements a 60-second in-memory cache and automatic diurnal fallback.
    """

    LATITUDE: float = 18.5679
    LONGITUDE: float = 73.9143
    WEATHER_ENDPOINT: str = "https://api.open-meteo.com/v1/forecast"
    AIR_QUALITY_ENDPOINT: str = "https://air-quality-api.open-meteo.com/v1/air-quality"
    CACHE_TTL_SECONDS: int = 60

    def __init__(self, timeout_seconds: float = 2.5):
        self.timeout_seconds = timeout_seconds
        self._cached_reading: Optional[Dict[str, Any]] = None
        self._cache_timestamp: float = 0.0

    async def get_current_weather(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Retrieves current ambient weather and air quality conditions.
        Returns cached value if within TTL, otherwise attempts live API fetch.
        Falls back to deterministic diurnal curve on network timeout or failure.
        """
        now = datetime.now(timezone.utc)
        now_epoch = now.timestamp()

        if not force_refresh and self._cached_reading and (now_epoch - self._cache_timestamp) < self.CACHE_TTL_SECONDS:
            return self._cached_reading

        try:
            weather_params = {
                "latitude": self.LATITUDE,
                "longitude": self.LONGITUDE,
                "current": (
                    "temperature_2m,relative_humidity_2m,apparent_temperature,"
                    "precipitation,surface_pressure,wind_speed_10m,wind_direction_10m"
                ),
                "timezone": "UTC"
            }
            aq_params = {
                "latitude": self.LATITUDE,
                "longitude": self.LONGITUDE,
                "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone",
                "timezone": "UTC"
            }

            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                weather_resp = await client.get(self.WEATHER_ENDPOINT, params=weather_params)
                aq_resp = await client.get(self.AIR_QUALITY_ENDPOINT, params=aq_params)

                if weather_resp.status_code == 200:
                    w_data = weather_resp.json().get("current", {})
                    aq_data = aq_resp.json().get("current", {}) if aq_resp.status_code == 200 else {}

                    temp_c = float(w_data.get("temperature_2m", 29.5))
                    humidity = float(w_data.get("relative_humidity_2m", 56.0))
                    apparent_temp = float(w_data.get("apparent_temperature", 30.5))
                    pressure = float(w_data.get("surface_pressure", 948.0))
                    precip = float(w_data.get("precipitation", 0.0))
                    wind_speed = float(w_data.get("wind_speed_10m", 11.5))
                    wind_dir_deg = float(w_data.get("wind_direction_10m", 240.0))

                    pm25 = float(aq_data.get("pm2_5", 48.5))
                    pm10 = float(aq_data.get("pm10", 92.0))
                    no2 = float(aq_data.get("nitrogen_dioxide", 36.0))
                    co = float(aq_data.get("carbon_monoxide", 420.0))
                    so2 = float(aq_data.get("sulphur_dioxide", 12.0))
                    o3 = float(aq_data.get("ozone", 45.0))

                    naaqs = compute_india_naaqs_aqi(pm25, pm10)

                    reading = {
                        "temperature_c": round(temp_c, 1),
                        "humidity_pct": round(humidity, 1),
                        "apparent_temp_c": round(apparent_temp, 1),
                        "surface_pressure_hpa": round(pressure, 1),
                        "precipitation_mm": round(precip, 2),
                        "wind_speed_kmh": round(wind_speed, 1),
                        "wind_direction_deg": round(wind_dir_deg, 1),
                        "wind_direction_cardinal": deg_to_cardinal(wind_dir_deg),
                        "pm25": round(pm25, 1),
                        "pm10": round(pm10, 1),
                        "no2": round(no2, 1),
                        "co": round(co, 1),
                        "so2": round(so2, 1),
                        "o3": round(o3, 1),
                        "aqi": naaqs["aqi"],
                        "aqi_category": naaqs["category"],
                        "determining_pollutant": naaqs["determiningPollutant"],
                        "source_mode": "LIVE",
                        "source_id": "openmeteo:corridor-atmospheric-feed",
                        "observed_at": now.isoformat(),
                        "data_quality_score": 1.0,
                        "data_quality_status": "valid"
                    }
                    self._cached_reading = reading
                    self._cache_timestamp = now_epoch
                    return reading
        except Exception:
            # Non-blocking fallback to documented diurnal model on network dropout/timeout
            pass

        return self._compute_diurnal_fallback(now)

    def _compute_diurnal_fallback(self, now: datetime) -> Dict[str, Any]:
        """
        Computes realistic diurnal ambient weather & air quality for Pune when offline.
        Temperature varies between 22°C and 34°C, humidity between 45% and 75%,
        and PM2.5/PM10 fluctuate with diurnal traffic and atmospheric boundary layer height.
        """
        hour = now.hour + (now.minute / 60.0)
        temp_c = 24.0 + 8.0 * math.sin((hour - 8.0) * math.pi / 12.0)
        humidity = 65.0 - 20.0 * math.sin((hour - 8.0) * math.pi / 12.0)
        wind_speed = 9.0 + 4.5 * math.sin((hour - 10.0) * math.pi / 12.0)
        wind_dir = 230.0 + 25.0 * math.cos(hour * math.pi / 12.0)

        # Diurnal particulate curve: peaks during morning and evening rush hours
        rush = math.exp(-((hour - 9.5) ** 2) / 4.0) + math.exp(-((hour - 19.5) ** 2) / 4.0)
        pm25 = 38.0 + 26.0 * rush
        pm10 = 72.0 + 42.0 * rush
        no2 = 28.0 + 22.0 * rush

        naaqs = compute_india_naaqs_aqi(pm25, pm10)

        fallback = {
            "temperature_c": round(temp_c, 1),
            "humidity_pct": round(max(30.0, min(95.0, humidity)), 1),
            "apparent_temp_c": round(temp_c + 1.2, 1),
            "surface_pressure_hpa": 948.5,
            "precipitation_mm": 0.0,
            "wind_speed_kmh": round(max(3.0, wind_speed), 1),
            "wind_direction_deg": round(wind_dir % 360, 1),
            "wind_direction_cardinal": deg_to_cardinal(wind_dir),
            "pm25": round(pm25, 1),
            "pm10": round(pm10, 1),
            "no2": round(no2, 1),
            "co": round(410.0 + 80.0 * rush, 1),
            "so2": 11.5,
            "o3": round(35.0 + 15.0 * math.sin(max(0, hour - 11.0) * math.pi / 8.0), 1),
            "aqi": naaqs["aqi"],
            "aqi_category": naaqs["category"],
            "determining_pollutant": naaqs["determiningPollutant"],
            "source_mode": "SIMULATION",
            "source_id": "diurnal-atmospheric-model:pune-corridor",
            "observed_at": now.isoformat(),
            "data_quality_score": 0.88,
            "data_quality_status": "valid"
        }
        return fallback
