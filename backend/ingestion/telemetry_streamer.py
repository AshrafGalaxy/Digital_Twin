"""
telemetry_streamer.py

Embedded In-Process Corridor Telemetry Simulator Worker for the Digital Twin Platform (P4-B).
Provides autonomous, physics-grounded telemetry generation and WebSocket streaming
when an external MQTT broker is not reachable, ensuring zero-configuration local execution.
"""

import asyncio
import json
import logging
import math
import random
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.database import AsyncSessionLocal
from backend.schemas.canonical import SourceMode

logger = logging.getLogger("digital_twin.streamer")

# Corridor Segment Topology
CORRIDOR_SEGMENTS = [
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01", "name": "Nagar Road EB Approach", "speedLimit": 50.0, "baseSpeed": 42.0, "capacity": 2400},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-02", "name": "Nagar Road EB Central", "speedLimit": 50.0, "baseSpeed": 38.0, "capacity": 2400},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-03", "name": "Nagar Road EB Somnath", "speedLimit": 50.0, "baseSpeed": 44.0, "capacity": 2400},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-01", "name": "Nagar Road WB Somnath", "speedLimit": 50.0, "baseSpeed": 41.0, "capacity": 2400},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-02", "name": "Nagar Road WB Central", "speedLimit": 50.0, "baseSpeed": 36.0, "capacity": 2400},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-03", "name": "Nagar Road WB Approach", "speedLimit": 50.0, "baseSpeed": 43.0, "capacity": 2400},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-VN-NB-01", "name": "Viman Nagar Northbound", "speedLimit": 40.0, "baseSpeed": 28.0, "capacity": 1400},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-VN-SB-01", "name": "Viman Nagar Southbound", "speedLimit": 40.0, "baseSpeed": 32.0, "capacity": 1400},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-SN-NB-01", "name": "Somnath Nagar Northbound", "speedLimit": 40.0, "baseSpeed": 30.0, "capacity": 1200},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-SN-SB-01", "name": "Somnath Nagar Southbound", "speedLimit": 40.0, "baseSpeed": 34.0, "capacity": 1200},
]

# Paired Sensor Stations
SENSOR_STATIONS = [
    {"sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-01", "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01"},
    {"sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-02", "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-02"},
    {"sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-03", "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-03"},
    {"sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-WB-01", "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-01"},
    {"sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-WB-02", "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-02"},
    {"sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-WB-03", "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-03"},
    {"sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-NB-01", "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-VN-NB-01"},
    {"sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-SB-01", "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-VN-SB-01"},
    {"sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-SN-NB-01", "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-SN-NB-01"},
    {"sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-SN-SB-01", "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-SN-SB-01"},
]


class TelemetryStreamerWorker:
    """
    Autonomous background streaming worker that generates realistic physics-informed
    traffic, energy, and air-quality telemetry ticks and persists them to the active database.
    """

    def __init__(self, broadcast_callback: Optional[Callable[[Dict[str, Any]], Any]] = None):
        self.broadcast_callback = broadcast_callback
        self.interval_sec: float = settings.TELEMETRY_STREAMER_INTERVAL_SEC
        self.mode: str = settings.TELEMETRY_STREAMER_MODE
        self.is_running: bool = False
        self.is_paused: bool = False
        self.ticks_count: int = 0
        self.last_tick_at: Optional[str] = None
        self._task: Optional[asyncio.Task] = None
        from backend.ingestion.weather_client import OpenMeteoWeatherClient
        self.weather_client = OpenMeteoWeatherClient()

    def get_status(self) -> Dict[str, Any]:
        return {
            "isRunning": self.is_running,
            "isPaused": self.is_paused,
            "ticksCount": self.ticks_count,
            "intervalSec": self.interval_sec,
            "lastTickAt": self.last_tick_at,
            "sourceMode": self.mode
        }

    def set_interval(self, seconds: float) -> None:
        self.interval_sec = max(1.0, min(60.0, float(seconds)))

    def pause(self) -> None:
        self.is_paused = True
        logger.info("Telemetry streamer paused.")

    def resume(self) -> None:
        self.is_paused = False
        logger.info("Telemetry streamer resumed.")

    def start(self, broadcast_callback: Optional[Callable[[Dict[str, Any]], Any]] = None) -> None:
        if self.is_running:
            return
        if broadcast_callback:
            self.broadcast_callback = broadcast_callback
        self.is_running = True
        self.is_paused = False
        self._task = asyncio.create_task(self._run_loop())
        logger.info("In-process telemetry streamer worker started (interval: %.1fs, mode: %s).", self.interval_sec, self.mode)

    def stop(self) -> None:
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("In-process telemetry streamer worker stopped.")

    async def stop_async(self) -> None:
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
        logger.info("In-process telemetry streamer worker stopped cleanly.")

    async def _run_loop(self) -> None:
        while self.is_running:
            try:
                if not self.is_paused:
                    await self.tick_once()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Error in telemetry streamer tick: %s", exc, exc_info=False)

            await asyncio.sleep(self.interval_sec)

    async def tick_once(self) -> Dict[str, Any]:
        """
        Executes a single physics-grounded telemetry generation pass across all entities,
        persisting records to database and dispatching WebSocket updates.
        """
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        hour = now_dt.hour + (now_dt.minute / 60.0)

        # Diurnal rush hour multiplier (morning 8-10am peak, evening 17-20pm peak)
        morning_peak = math.exp(-0.5 * ((hour - 9.0) / 1.5) ** 2)
        evening_peak = math.exp(-0.5 * ((hour - 18.5) / 1.8) ** 2)
        rush_intensity = max(0.2, min(1.0, 0.25 + 0.55 * morning_peak + 0.65 * evening_peak))

        async with AsyncSessionLocal() as session:
            try:
                # 1. Generate & Persist Traffic Observations
                segment_metrics_list = []
                total_speed = 0.0
                total_flow = 0.0
                total_queue = 0.0

                for seg in CORRIDOR_SEGMENTS:
                    seg_id = seg["id"]
                    base_speed = seg["baseSpeed"]
                    # Speed decreases during rush hour with small random stochastic jitter
                    jitter = random.uniform(-2.5, 2.5)
                    speed = max(14.0, min(seg["speedLimit"], base_speed * (1.1 - 0.45 * rush_intensity) + jitter))
                    flow = max(400.0, min(seg["capacity"], seg["capacity"] * (0.35 + 0.60 * rush_intensity) + random.uniform(-100, 100)))
                    occ = max(10.0, min(90.0, (1.0 - (speed / seg["speedLimit"])) * 75.0 + random.uniform(-3, 3)))
                    queue = max(2.0, min(120.0, (1.0 - (speed / seg["speedLimit"])) * 85.0 + random.uniform(-5, 5)))
                    cong = max(0.05, min(0.95, (1.0 - (speed / seg["speedLimit"]))))

                    total_speed += speed
                    total_flow += flow
                    total_queue += queue

                    # Insert observation
                    obs_stmt = text("""
                        INSERT INTO traffic_observations (
                            observed_at, sensor_id, segment_id, source_mode,
                            average_speed_kmh, vehicle_flow_per_hour, occupancy_percent,
                            queue_length_meters, congestion_index, quality_flag
                        ) VALUES (
                            :observed_at, :sensor_id, :segment_id, :source_mode,
                            :average_speed_kmh, :vehicle_flow_per_hour, :occupancy_percent,
                            :queue_length_meters, :congestion_index, 'VALID'
                        )
                    """)
                    sensor_id = next((s["sensorId"] for s in SENSOR_STATIONS if s["segmentId"] == seg_id), "urn:ngsi-ld:TrafficSensor:PUNE:GEN-01")
                    await session.execute(obs_stmt, {
                        "observed_at": now_iso,
                        "sensor_id": sensor_id,
                        "segment_id": seg_id,
                        "source_mode": self.mode,
                        "average_speed_kmh": round(speed, 2),
                        "vehicle_flow_per_hour": round(flow, 1),
                        "occupancy_percent": round(occ, 1),
                        "queue_length_meters": round(queue, 1),
                        "congestion_index": round(cong, 3)
                    })

                    # Update entity current state
                    metrics = {
                        "averageSpeedKmh": round(speed, 1),
                        "vehicleFlowPerHour": round(flow, 0),
                        "occupancyPercent": round(occ, 1),
                        "queueLengthMeters": round(queue, 1),
                        "congestionIndex": round(cong, 3)
                    }
                    upsert_state = text("""
                        INSERT INTO entity_current_state (
                            entity_id, entity_type, source_mode, observed_at,
                            updated_at, metrics, quality_status, freshness_seconds
                        ) VALUES (
                            :entity_id, :entity_type, :source_mode, :observed_at,
                            :updated_at, :metrics, 'VALID', 0.0
                        )
                        ON CONFLICT (entity_id) DO UPDATE SET
                            entity_type = EXCLUDED.entity_type,
                            source_mode = EXCLUDED.source_mode,
                            observed_at = EXCLUDED.observed_at,
                            updated_at = EXCLUDED.updated_at,
                            metrics = EXCLUDED.metrics,
                            quality_status = 'VALID',
                            freshness_seconds = 0.0;
                    """)
                    await session.execute(upsert_state, {
                        "entity_id": seg_id,
                        "entity_type": "RoadSegment",
                        "source_mode": self.mode,
                        "observed_at": now_iso,
                        "updated_at": now_iso,
                        "metrics": json.dumps(metrics)
                    })

                    segment_metrics_list.append({
                        "entityId": seg_id,
                        "metrics": metrics
                    })

                # 2. Generate & Persist Commercial Building Energy Observations for Corridor Facilities
                commercial_facilities = [
                    {
                        "id": "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
                        "aliases": ["urn:ngsi-ld:BuildingZone:PUNE:PHOENIX-01", "urn:ngsi-ld:BuildingZone:PUNE:BLD-PHOENIX-01"],
                        "base_load": 2400.0,
                        "peak_delta": 2200.0,
                        "contract_kw": 6800.0,
                    },
                    {
                        "id": "urn:ngsi-ld:Building:PUNE:BLD-SOLITAIRE-01",
                        "aliases": ["urn:ngsi-ld:BuildingZone:PUNE:BLD-SOLITAIRE-01"],
                        "base_load": 2100.0,
                        "peak_delta": 2000.0,
                        "contract_kw": 6010.0,
                    },
                    {
                        "id": "urn:ngsi-ld:Building:PUNE:BLD-HYATT-01",
                        "aliases": ["urn:ngsi-ld:BuildingZone:PUNE:BLD-HYATT-01"],
                        "base_load": 1800.0,
                        "peak_delta": 1700.0,
                        "contract_kw": 4990.0,
                    },
                    {
                        "id": "urn:ngsi-ld:Building:PUNE:BLD-SOLITAIRE-03",
                        "aliases": ["urn:ngsi-ld:BuildingZone:PUNE:BLD-SOLITAIRE-03"],
                        "base_load": 900.0,
                        "peak_delta": 850.0,
                        "contract_kw": 2400.0,
                    },
                ]

                energy_stmt = text("""
                    INSERT INTO energy_observations (
                        observed_at, building_id, source_mode, active_power_kw,
                        reactive_power_kvar, power_factor, energy_consumption_kwh, quality_flag
                    ) VALUES (
                        :observed_at, :building_id, :source_mode, :active_power_kw,
                        :reactive_power_kvar, :power_factor, :energy_consumption_kwh, 'VALID'
                    )
                """)

                primary_energy_load_kw = 4420.0
                building_metrics_list = []
                for fac in commercial_facilities:
                    fac_load_kw = max(
                        fac["base_load"] * 0.7,
                        min(fac["contract_kw"] * 0.95, fac["base_load"] + fac["peak_delta"] * rush_intensity + random.uniform(-40, 40))
                    )
                    if fac["id"] == "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01":
                        primary_energy_load_kw = fac_load_kw
                    reactive_kvar = fac_load_kw * 0.32
                    power_factor = round(random.uniform(0.94, 0.97), 3)

                    # Insert observation for canonical ID and legacy/spatial aliases
                    all_ids = [fac["id"]] + [a for a in fac["aliases"] if a != fac["id"]]
                    for b_id in all_ids:
                        await session.execute(energy_stmt, {
                            "observed_at": now_iso,
                            "building_id": b_id,
                            "source_mode": self.mode,
                            "active_power_kw": round(fac_load_kw, 2),
                            "reactive_power_kvar": round(reactive_kvar, 2),
                            "power_factor": power_factor,
                            "energy_consumption_kwh": round(fac_load_kw * 24.0, 1)
                        })

                    # Update Building Current State for canonical and alias URNs
                    bld_metrics = {
                        "activePowerKw": round(fac_load_kw, 1),
                        "reactivePowerKvar": round(reactive_kvar, 1),
                        "powerFactor": power_factor,
                        "energyConsumptionKwh": round(fac_load_kw * 24.0, 1)
                    }
                    building_metrics_list.append({
                        "entityId": fac["id"],
                        "aliases": fac["aliases"],
                        "metrics": bld_metrics
                    })
                    for b_id in [fac["id"]]:
                        await session.execute(upsert_state, {
                            "entity_id": b_id,
                            "entity_type": "Building",
                            "source_mode": self.mode,
                            "observed_at": now_iso,
                            "updated_at": now_iso,
                            "metrics": json.dumps(bld_metrics),
                            "quality_status": "VALID",
                            "freshness_seconds": 0.0
                        })
                    for a_id in fac["aliases"]:
                        await session.execute(upsert_state, {
                            "entity_id": a_id,
                            "entity_type": "BuildingZone",
                            "source_mode": self.mode,
                            "observed_at": now_iso,
                            "updated_at": now_iso,
                            "metrics": json.dumps(bld_metrics),
                            "quality_status": "VALID",
                            "freshness_seconds": 0.0
                        })

                energy_load_kw = primary_energy_load_kw

                # 3. Generate & Persist Environmental Air Quality & Weather Observation
                weather = await self.weather_client.get_current_weather()
                temp = weather.get("temperature_c", 28.5)
                humidity = weather.get("humidity_pct", 56.0)
                wind_speed = weather.get("wind_speed_kmh", 11.2)
                wind_dir = weather.get("wind_direction_cardinal", "WSW (240°)")
                pm25 = weather.get("pm25", 48.0)
                pm10 = weather.get("pm10", 90.0)
                no2 = weather.get("no2", 36.0)
                co = weather.get("co", 410.0)
                aqi = weather.get("aqi", 135)
                aqi_category = weather.get("aqi_category", "Moderate")
                weather_mode = weather.get("source_mode", self.mode)

                env_stmt = text("""
                    INSERT INTO environment_observations (
                        observed_at, station_id, source_mode, aqi_value,
                        pm25, pm10, temperature_c, relative_humidity_pct,
                        precipitation_mm, quality_flag
                    ) VALUES (
                        :observed_at, :station_id, :source_mode, :aqi_value,
                        :pm25, :pm10, :temperature_c, :relative_humidity_pct,
                        :precipitation_mm, 'VALID'
                    )
                """)

                primary_station_id = "urn:ngsi-ld:AirQualityStation:PUNE:STATION-VIMAN-AQI-01"
                corridor_station_id = "urn:ngsi-ld:AirQualityStation:PUNE:STATION-CORRIDOR-AQI-01"

                for st_id in (primary_station_id, corridor_station_id):
                    await session.execute(env_stmt, {
                        "observed_at": now_iso,
                        "station_id": st_id,
                        "source_mode": weather_mode,
                        "aqi_value": aqi,
                        "pm25": pm25,
                        "pm10": pm10,
                        "temperature_c": temp,
                        "relative_humidity_pct": humidity,
                        "precipitation_mm": weather.get("precipitation_mm", 0.0)
                    })

                # Update Building/Station Current State for AirQualityStation
                env_metrics = {
                    "aqi": aqi,
                    "aqiCategory": aqi_category,
                    "temperatureC": temp,
                    "humidityPct": humidity,
                    "windSpeedKmh": wind_speed,
                    "windDirection": wind_dir,
                    "pm25": pm25,
                    "pm10": pm10,
                    "no2": no2,
                    "co": co
                }
                for st_id in (primary_station_id, corridor_station_id):
                    await session.execute(upsert_state, {
                        "entity_id": st_id,
                        "entity_type": "AirQualityStation",
                        "source_mode": weather_mode,
                        "observed_at": now_iso,
                        "updated_at": now_iso,
                        "metrics": json.dumps(env_metrics),
                        "quality_status": "VALID",
                        "freshness_seconds": 0.0
                    })

                await session.commit()

                # Update Internal Telemetry State
                self.ticks_count += 1
                self.last_tick_at = now_iso

                # 4. Dispatch WebSocket Broadcast Messages
                if self.broadcast_callback:
                    n_segs = max(1, len(CORRIDOR_SEGMENTS))
                    avg_speed = round(total_speed / n_segs, 1)
                    cong_idx = round(max(0.05, min(0.95, 1.0 - (avg_speed / 50.0))), 3)
                    corridor_summary = {
                        "eventType": "CORRIDOR_METRICS_UPDATED",
                        "timestamp": now_iso,
                        "sourceMode": self.mode,
                        "averageSpeedKmh": avg_speed,
                        "congestionIndex": cong_idx,
                        "totalFlowPerHour": round(total_flow, 0),
                        "averageQueueLengthMeters": round(total_queue / n_segs, 1),
                        "energyActivePowerKw": round(energy_load_kw, 1),
                        "activeSensors": len(SENSOR_STATIONS),
                        "aqi": aqi,
                        "environment": {
                            "stationId": corridor_station_id,
                            "aqi": aqi,
                            "aqiCategory": aqi_category,
                            "temperatureC": temp,
                            "humidityPct": humidity,
                            "windSpeedKmh": wind_speed,
                            "windDir": wind_dir,
                            "pm25": pm25,
                            "pm10": pm10,
                            "no2": no2,
                            "co": co,
                            "sourceMode": weather_mode,
                            "observedAt": now_iso
                        }
                    }
                    if asyncio.iscoroutinefunction(self.broadcast_callback):
                        await self.broadcast_callback(corridor_summary)
                    else:
                        self.broadcast_callback(corridor_summary)

                    # Also broadcast individual segment updates so segment colors on map stay live
                    for seg_item in segment_metrics_list:
                        msg = {
                            "eventType": "TRAFFIC_STATE_UPDATED",
                            "entityId": seg_item["entityId"],
                            "observedAt": now_iso,
                            "sourceMode": self.mode,
                            "metrics": seg_item["metrics"]
                        }
                        if asyncio.iscoroutinefunction(self.broadcast_callback):
                            await self.broadcast_callback(msg)
                        else:
                            self.broadcast_callback(msg)

                    # Also broadcast individual building energy updates so energy analytics and 3D buildings stay live
                    for bld_item in building_metrics_list:
                        all_target_ids = [bld_item["entityId"]] + bld_item.get("aliases", [])
                        for target_id in set(all_target_ids):
                            energy_msg = {
                                "eventType": "ENERGY_STATE_UPDATED",
                                "entityId": target_id,
                                "observedAt": now_iso,
                                "sourceMode": self.mode,
                                "metrics": bld_item["metrics"]
                            }
                            if asyncio.iscoroutinefunction(self.broadcast_callback):
                                await self.broadcast_callback(energy_msg)
                            else:
                                self.broadcast_callback(energy_msg)

                return {
                    "status": "TICK_SUCCESS",
                    "tickNumber": self.ticks_count,
                    "timestamp": now_iso,
                    "segmentsUpdated": len(segment_metrics_list),
                    "buildingPowerKw": round(energy_load_kw, 1),
                    "aqi": aqi
                }

            except Exception as e:
                await session.rollback()
                logger.error("Failed to commit simulated telemetry tick: %s", e)
                raise


# Global singleton streamer worker instance
telemetry_streamer = TelemetryStreamerWorker()

import sys
if __name__ in sys.modules:
    sys.modules.setdefault("backend.ingestion.telemetry_streamer", sys.modules[__name__])
    sys.modules.setdefault("ingestion.telemetry_streamer", sys.modules[__name__])
