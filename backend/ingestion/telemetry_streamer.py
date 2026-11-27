"""
telemetry_streamer.py

Embedded In-Process Corridor Telemetry Simulator Worker for the Digital Twin Platform (P4-B).
Provides autonomous, physics-grounded telemetry generation and WebSocket streaming
when an external MQTT broker is not reachable, ensuring zero-configuration local execution.
"""

import asyncio
import inspect
import json
import logging
import math
import random
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, TypedDict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.database import AsyncSessionLocal
from backend.schemas.canonical import SourceMode
from backend.services.los_engine import los_engine
from backend.services.spat_adapter import spat_adapter

logger = logging.getLogger("digital_twin.streamer")

CORRIDOR_INTERSECTIONS = [
    "urn:ngsi-ld:Intersection:PUNE:INT-VN-01",
    "urn:ngsi-ld:Intersection:PUNE:INT-SN-01"
]

# Approach storage is the segment length from the corridor asset register.
# A queue longer than this storage is spillback into the upstream link.
LINK_CYCLE_SEC = 120.0
LINK_BASE_GREEN_SEC = 35.0
VEHICLE_SPACING_M = 7.5
SPEED_VALID_MAX_KMH = 120.0

# Corridor Segment Topology
class CorridorSegmentDict(TypedDict):
    id: str
    name: str
    speedLimit: float
    baseSpeed: float
    capacity: int
    approachStorageMeters: float


class CommercialFacilityDict(TypedDict):
    id: str
    aliases: List[str]
    base_load: float
    peak_delta: float
    contract_kw: float


class BuildingMetricEntry(TypedDict):
    entityId: str
    aliases: List[str]
    metrics: Dict[str, Any]


CORRIDOR_SEGMENTS: List[CorridorSegmentDict] = [
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01", "name": "Nagar Road EB Approach", "speedLimit": 50.0, "baseSpeed": 42.0, "capacity": 2400, "approachStorageMeters": 480.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-02", "name": "Nagar Road EB Central", "speedLimit": 50.0, "baseSpeed": 38.0, "capacity": 2400, "approachStorageMeters": 1180.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-03", "name": "Nagar Road EB Somnath", "speedLimit": 50.0, "baseSpeed": 44.0, "capacity": 2400, "approachStorageMeters": 450.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-01", "name": "Nagar Road WB Somnath", "speedLimit": 50.0, "baseSpeed": 41.0, "capacity": 2400, "approachStorageMeters": 450.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-02", "name": "Nagar Road WB Central", "speedLimit": 50.0, "baseSpeed": 36.0, "capacity": 2400, "approachStorageMeters": 1180.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-03", "name": "Nagar Road WB Approach", "speedLimit": 50.0, "baseSpeed": 43.0, "capacity": 2400, "approachStorageMeters": 480.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-VN-NB-01", "name": "Viman Nagar Northbound", "speedLimit": 40.0, "baseSpeed": 28.0, "capacity": 1400, "approachStorageMeters": 350.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-VN-SB-01", "name": "Viman Nagar Southbound", "speedLimit": 40.0, "baseSpeed": 32.0, "capacity": 1400, "approachStorageMeters": 400.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-SN-NB-01", "name": "Somnath Nagar Northbound", "speedLimit": 40.0, "baseSpeed": 30.0, "capacity": 1200, "approachStorageMeters": 300.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-SN-SB-01", "name": "Somnath Nagar Southbound", "speedLimit": 40.0, "baseSpeed": 34.0, "capacity": 1200, "approachStorageMeters": 320.0},
]


def compute_link_kinematics(
    *,
    speed_limit_kmh: float,
    base_speed_kmh: float,
    capacity_vph: float,
    approach_storage_m: float,
    rush_intensity: float,
    speed_jitter: float = 0.0,
    flow_jitter: float = 0.0,
    demand_vph: Optional[float] = None,
    discharge_vph: Optional[float] = None,
) -> Dict[str, float]:
    """
    One speed, one throughput, and one queue for a generated tick.

    Demand rises with the rush factor. Speed falls as demand exceeds capacity and
    stays inside 0 to 120 km/h, with no 14 km/h floor. Throughput is the lesser of
    demand and discharge, so a blocked approach can be near zero vehicles per hour.
    Queue uses the same residual as the kinematic scenario: unserved arrivals in one
    120 s cycle, plus the red-period arrival, times 7.5 m per vehicle. The result is
    not capped at 120 m or at approach storage. Meters above storage are spillback.
    """
    capacity = max(float(capacity_vph), 1.0)
    limit = max(float(speed_limit_kmh), 1.0)
    storage = max(float(approach_storage_m), 1.0)
    rush = max(0.0, min(1.0, float(rush_intensity)))

    demand = float(demand_vph) if demand_vph is not None else capacity * (0.35 + 0.90 * rush)
    demand = max(0.0, demand)
    pressure = demand / capacity
    raw_speed = float(base_speed_kmh) * (1.15 - 0.85 * min(pressure, 1.6)) + float(speed_jitter)
    speed = max(0.0, min(SPEED_VALID_MAX_KMH, min(limit, raw_speed)))

    if discharge_vph is None:
        discharge = max(0.0, capacity * (speed / limit) + float(flow_jitter))
    else:
        discharge = max(0.0, float(discharge_vph))
    flow = max(0.0, min(demand, discharge))

    green_ratio = LINK_BASE_GREEN_SEC / LINK_CYCLE_SEC
    arrival_per_cycle = demand * (LINK_CYCLE_SEC / 3600.0)
    served_per_cycle = discharge * (LINK_CYCLE_SEC / 3600.0)
    overflow_vehicles = max(0.0, arrival_per_cycle - served_per_cycle)
    red_queue_vehicles = arrival_per_cycle * (1.0 - green_ratio) * 0.5
    queue = max(0.0, (overflow_vehicles + red_queue_vehicles) * VEHICLE_SPACING_M)
    spillback = max(0.0, queue - storage)

    # Moving density is flow / speed. A stopped approach uses the queued vehicles
    # spread over the storage length so the record still has a density.
    if speed >= 1.0:
        density = flow / speed
    else:
        density = (queue / VEHICLE_SPACING_M) / (storage / 1000.0)

    return {
        "averageSpeedKmh": round(speed, 2),
        "vehicleFlowPerHour": round(flow, 1),
        "queueLengthMeters": round(queue, 1),
        "approachStorageMeters": round(storage, 1),
        "spillbackMeters": round(spillback, 1),
        "densityVehKm": round(density, 2),
        "demandVehPerHour": round(demand, 1),
    }

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
        self.history_write_failures_count: int = 0
        self.last_tick_at: Optional[str] = None
        self._task: Optional[asyncio.Task] = None
        self._stop_event: Optional[asyncio.Event] = None
        from backend.ingestion.weather_client import OpenMeteoWeatherClient
        self.weather_client = OpenMeteoWeatherClient()

    def get_status(self) -> Dict[str, Any]:
        return {
            "isRunning": self.is_running,
            "isPaused": self.is_paused,
            "ticksCount": self.ticks_count,
            "historyWriteFailuresCount": self.history_write_failures_count,
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
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("In-process telemetry streamer worker started (interval: %.1fs, mode: %s).", self.interval_sec, self.mode)

    def stop(self) -> None:
        self.is_running = False
        if self._stop_event is not None:
            self._stop_event.set()
        elif self._task and not self._task.done():
            self._task.cancel()
        logger.info("In-process telemetry streamer worker stopped.")

    async def stop_async(self) -> None:
        self.is_running = False
        if self._stop_event is not None:
            self._stop_event.set()
        if self._task and not self._task.done():
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError, Exception):
                if not self._task.done():
                    self._task.cancel()
                    try:
                        await self._task
                    except (asyncio.CancelledError, Exception):
                        pass
        self._task = None
        self._stop_event = None
        logger.info("In-process telemetry streamer worker stopped cleanly.")

    async def _run_loop(self) -> None:
        stop_event = self._stop_event
        while self.is_running:
            try:
                if not self.is_paused:
                    await self.tick_once()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Error in telemetry streamer tick: %s", exc, exc_info=False)

            if not self.is_running:
                break
            if stop_event is not None:
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=self.interval_sec)
                    break
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break
            else:
                await asyncio.sleep(self.interval_sec)

    def _record_los_history_failure(
        self,
        *,
        hist_params: Dict[str, Any],
        payload_meta: Dict[str, Any],
        now_dt: datetime,
        now_iso: str,
        exc: Exception,
    ) -> None:
        seg_id = str(hist_params["segment_id"])
        self.history_write_failures_count += 1
        logger.error(
            "Failed to persist segment_los_history for segment %s (%s): %s",
            seg_id,
            type(exc).__name__,
            exc,
        )
        try:
            from backend.ingestion.quarantine import quarantine_manager

            quarantine_manager.record_quarantine(
                raw_payload={
                    "segmentId": seg_id,
                    "observedAt": now_iso,
                    "volumeCapacityRatio": payload_meta.get("volumeCapacityRatio"),
                    "densityVehKm": payload_meta.get("densityVehKm"),
                    "congestionIndex": payload_meta.get("congestionIndex"),
                    "losGrade": payload_meta.get("levelOfService"),
                    "operationalCondition": payload_meta.get("operationalCondition"),
                    "policyStandard": payload_meta.get("policyStandard"),
                    "sourceMode": self.mode,
                    "qualityScore": hist_params["quality_score"],
                },
                rejection_reason="SEGMENT_HISTORY_WRITE_FAILURE",
                entity_id=seg_id,
                entity_type="RoadSegment",
                source_mode=self.mode,
                observed_at=now_dt,
                validation_details={
                    "exceptionType": type(exc).__name__,
                    "errorMessage": str(exc),
                    "targetTable": "segment_los_history",
                },
            )
        except Exception as q_err:
            logger.error("Failed to quarantine segment_los_history write failure: %s", q_err)

    def _compute_tick_payload(
        self,
        *,
        now_dt: datetime,
        now_iso: str,
        weather: Dict[str, Any],
        rng: Optional[random.Random] = None,
    ) -> Dict[str, Any]:
        """Pure-Python physics computation and batch parameter assembly run off the event loop."""
        sampler = rng if rng is not None else random
        hour = now_dt.hour + (now_dt.minute / 60.0)

        # Diurnal rush hour multiplier (morning 8-10am peak, evening 17-20pm peak)
        morning_peak = math.exp(-0.5 * ((hour - 9.0) / 1.5) ** 2)
        evening_peak = math.exp(-0.5 * ((hour - 18.5) / 1.8) ** 2)
        rush_intensity = max(0.2, min(1.0, 0.25 + 0.55 * morning_peak + 0.65 * evening_peak))

        sensor_lookup = {s["segmentId"]: s["sensorId"] for s in SENSOR_STATIONS}
        hist_quality_score = 0.70 if self.mode.upper() == "SIMULATION" else 0.95

        traffic_obs_rows: List[Dict[str, Any]] = []
        los_hist_rows: List[Dict[str, Any]] = []
        los_hist_meta: List[Dict[str, Any]] = []
        current_state_rows: List[Dict[str, Any]] = []
        segment_metrics_list: List[Dict[str, Any]] = []

        total_speed = 0.0
        total_flow = 0.0
        total_queue = 0.0

        # 1. Traffic segment kinematics, LOS grading, and observation rows
        for seg in CORRIDOR_SEGMENTS:
            seg_id = seg["id"]
            kinematics = compute_link_kinematics(
                speed_limit_kmh=seg["speedLimit"],
                base_speed_kmh=seg["baseSpeed"],
                capacity_vph=seg["capacity"],
                approach_storage_m=seg["approachStorageMeters"],
                rush_intensity=rush_intensity,
                speed_jitter=sampler.uniform(-2.5, 2.5),
                flow_jitter=sampler.uniform(-80.0, 80.0),
            )
            speed = kinematics["averageSpeedKmh"]
            flow = kinematics["vehicleFlowPerHour"]
            queue = kinematics["queueLengthMeters"]
            occ = max(0.0, min(100.0, (1.0 - (speed / seg["speedLimit"])) * 75.0 + sampler.uniform(-3, 3)))
            cong = max(0.0, min(1.0, (1.0 - (speed / seg["speedLimit"]))))

            total_speed += speed
            total_flow += flow
            total_queue += queue

            sensor_id = sensor_lookup.get(seg_id, "urn:ngsi-ld:TrafficSensor:PUNE:GEN-01")
            traffic_obs_rows.append({
                "observed_at": now_dt,
                "sensor_id": sensor_id,
                "segment_id": seg_id,
                "source_mode": self.mode,
                "average_speed_kmh": round(speed, 2),
                "vehicle_flow_per_hour": round(flow, 1),
                "occupancy_percent": round(occ, 1),
                "queue_length_meters": round(queue, 1),
                "congestion_index": round(cong, 3),
            })

            los_data = los_engine.compute_segment_los(
                segment_id=seg_id,
                speed_kmh=speed,
                flow_vph=flow,
                capacity_vph=seg.get("capacity", 2400.0),
                free_flow_speed_kmh=seg.get("speedLimit", 50.0),
                source_mode=self.mode,
                observed_at=now_iso,
            )

            metrics = {
                "averageSpeedKmh": round(speed, 1),
                "vehicleFlowPerHour": round(flow, 0),
                "occupancyPercent": round(occ, 1),
                "queueLengthMeters": round(queue, 1),
                "approachStorageMeters": kinematics["approachStorageMeters"],
                "spillbackMeters": kinematics["spillbackMeters"],
                "congestionIndex": round(cong, 3),
                "volumeCapacityRatio": los_data["volumeCapacityRatio"],
                "densityVehKm": los_data["densityVehKm"],
                "levelOfService": los_data["levelOfService"],
                "operationalCondition": los_data["operationalCondition"],
                "policyStandard": los_data["policyStandard"],
            }
            current_state_rows.append({
                "entity_id": seg_id,
                "entity_type": "RoadSegment",
                "source_mode": self.mode,
                "observed_at": now_dt,
                "updated_at": now_dt,
                "metrics": json.dumps(metrics),
            })

            los_hist_rows.append({
                "segment_id": seg_id,
                "observed_at": now_dt,
                "volume_capacity_ratio": los_data["volumeCapacityRatio"],
                "density_veh_km": los_data["densityVehKm"],
                "congestion_index": los_data["congestionIndex"],
                "los_grade": los_data["levelOfService"],
                "operational_condition": los_data["operationalCondition"],
                "policy_standard": los_data["policyStandard"],
                "source_mode": self.mode,
                "quality_score": hist_quality_score,
            })
            los_hist_meta.append(los_data)

            segment_metrics_list.append({
                "entityId": seg_id,
                "metrics": metrics,
            })

        # 2. Commercial building energy observation rows
        commercial_facilities: List[CommercialFacilityDict] = [
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

        energy_obs_rows: List[Dict[str, Any]] = []
        primary_energy_load_kw = 4420.0
        building_metrics_list: List[BuildingMetricEntry] = []
        for fac in commercial_facilities:
            fac_load_kw = max(
                fac["base_load"] * 0.7,
                min(fac["contract_kw"] * 0.95, fac["base_load"] + fac["peak_delta"] * rush_intensity + sampler.uniform(-40, 40)),
            )
            if fac["id"] == "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01":
                primary_energy_load_kw = fac_load_kw
            reactive_kvar = fac_load_kw * 0.32
            power_factor = round(sampler.uniform(0.94, 0.97), 3)

            all_ids = [fac["id"]] + [a for a in fac["aliases"] if a != fac["id"]]
            for b_id in all_ids:
                energy_obs_rows.append({
                    "observed_at": now_dt,
                    "building_id": b_id,
                    "source_mode": self.mode,
                    "active_power_kw": round(fac_load_kw, 2),
                    "reactive_power_kvar": round(reactive_kvar, 2),
                    "power_factor": power_factor,
                    "energy_consumption_kwh": round(fac_load_kw * 24.0, 1),
                })

            bld_metrics = {
                "activePowerKw": round(fac_load_kw, 1),
                "reactivePowerKvar": round(reactive_kvar, 1),
                "powerFactor": power_factor,
                "energyConsumptionKwh": round(fac_load_kw * 24.0, 1),
            }
            building_metrics_list.append({
                "entityId": fac["id"],
                "aliases": fac["aliases"],
                "metrics": bld_metrics,
            })
            bld_metrics_json = json.dumps(bld_metrics)
            current_state_rows.append({
                "entity_id": fac["id"],
                "entity_type": "Building",
                "source_mode": self.mode,
                "observed_at": now_dt,
                "updated_at": now_dt,
                "metrics": bld_metrics_json,
            })
            for a_id in fac["aliases"]:
                current_state_rows.append({
                    "entity_id": a_id,
                    "entity_type": "BuildingZone",
                    "source_mode": self.mode,
                    "observed_at": now_dt,
                    "updated_at": now_dt,
                    "metrics": bld_metrics_json,
                })

        # 3. Environmental air quality and weather observation rows
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
        precip_mm = weather.get("precipitation_mm", 0.0)

        primary_station_id = "urn:ngsi-ld:AirQualityStation:PUNE:STATION-VIMAN-AQI-01"
        corridor_station_id = "urn:ngsi-ld:AirQualityStation:PUNE:STATION-CORRIDOR-AQI-01"
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
            "co": co,
        }
        env_metrics_json = json.dumps(env_metrics)

        env_obs_rows: List[Dict[str, Any]] = []
        for st_id in (primary_station_id, corridor_station_id):
            env_obs_rows.append({
                "observed_at": now_dt,
                "station_id": st_id,
                "source_mode": weather_mode,
                "aqi_value": aqi,
                "pm25": pm25,
                "pm10": pm10,
                "temperature_c": temp,
                "relative_humidity_pct": humidity,
                "precipitation_mm": precip_mm,
            })
            current_state_rows.append({
                "entity_id": st_id,
                "entity_type": "AirQualityStation",
                "source_mode": weather_mode,
                "observed_at": now_dt,
                "updated_at": now_dt,
                "metrics": env_metrics_json,
            })

        # 3b. Virtual SPaT signal controller state rows
        spat_states_list: List[Dict[str, Any]] = []
        for int_id in CORRIDOR_INTERSECTIONS:
            try:
                spat_state = spat_adapter.generate_synthetic_tick(
                    intersection_id=int_id,
                    elapsed_delta_sec=float(self.interval_sec),
                    source_mode=self.mode,
                )
                if spat_state is not None:
                    spat_dict = spat_state.to_dict()
                    spat_states_list.append(spat_dict)
                    spat_metrics = {
                        "activePhase": spat_dict["activePhase"],
                        "activePhaseName": spat_dict["activePhaseName"],
                        "phaseColor": spat_dict["phaseColor"],
                        "timeToNextPhaseSec": spat_dict["timeToNextPhaseSec"],
                        "cycleLengthSec": spat_dict["cycleLengthSec"],
                        "controllerMode": spat_dict["controllerMode"],
                    }
                    current_state_rows.append({
                        "entity_id": int_id,
                        "entity_type": "TrafficSignal",
                        "source_mode": self.mode,
                        "observed_at": now_dt,
                        "updated_at": now_dt,
                        "metrics": json.dumps(spat_metrics),
                    })
            except Exception as spat_err:
                logger.debug("Virtual SPaT tick notice: %s", spat_err)

        return {
            "traffic_obs_rows": traffic_obs_rows,
            "los_hist_rows": los_hist_rows,
            "los_hist_meta": los_hist_meta,
            "energy_obs_rows": energy_obs_rows,
            "env_obs_rows": env_obs_rows,
            "current_state_rows": current_state_rows,
            "segment_metrics_list": segment_metrics_list,
            "building_metrics_list": building_metrics_list,
            "spat_states_list": spat_states_list,
            "total_speed": total_speed,
            "total_flow": total_flow,
            "total_queue": total_queue,
            "segment_count": len(CORRIDOR_SEGMENTS),
            "energy_load_kw": primary_energy_load_kw,
            "aqi": aqi,
            "aqi_category": aqi_category,
            "temp": temp,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "wind_dir": wind_dir,
            "pm25": pm25,
            "pm10": pm10,
            "no2": no2,
            "co": co,
            "weather_mode": weather_mode,
            "corridor_station_id": corridor_station_id,
        }

    async def tick_once(
        self,
        *,
        now: Optional[datetime] = None,
        rng: Optional[random.Random] = None,
    ) -> Dict[str, Any]:
        """
        Executes a single physics-grounded telemetry generation pass across all entities,
        computing row batches off the event loop, persisting one batch per table, and
        dispatching WebSocket updates.
        """
        now_dt = now if now is not None else datetime.now(timezone.utc)
        if now_dt.tzinfo is None:
            now_dt = now_dt.replace(tzinfo=timezone.utc)
        now_iso = now_dt.isoformat()

        # Fetch ambient weather before opening the DB session to avoid holding connections on HTTP I/O
        weather = await self.weather_client.get_current_weather()

        # Offload physics calculations and payload assembly off the asyncio event loop
        payload = await asyncio.to_thread(
            self._compute_tick_payload,
            now_dt=now_dt,
            now_iso=now_iso,
            weather=weather,
            rng=rng,
        )

        # Invariant 2 (State Separation): SIMULATION ticks must never overwrite LIVE or REPLAY state
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
                freshness_seconds = 0.0
            WHERE (
                EXCLUDED.source_mode IN ('LIVE', 'REPLAY')
                OR entity_current_state.source_mode NOT IN ('LIVE', 'REPLAY')
            );
        """)
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
        los_hist_stmt = text("""
            INSERT INTO segment_los_history (
                segment_id, observed_at, volume_capacity_ratio,
                density_veh_km, congestion_index, los_grade,
                operational_condition, policy_standard, source_mode, quality_score
            ) VALUES (
                :segment_id, :observed_at, :volume_capacity_ratio,
                :density_veh_km, :congestion_index, :los_grade,
                :operational_condition, :policy_standard, :source_mode, :quality_score
            )
        """)
        energy_stmt = text("""
            INSERT INTO energy_observations (
                observed_at, building_id, source_mode, active_power_kw,
                reactive_power_kvar, power_factor, energy_consumption_kwh, quality_flag
            ) VALUES (
                :observed_at, :building_id, :source_mode, :active_power_kw,
                :reactive_power_kvar, :power_factor, :energy_consumption_kwh, 'VALID'
            )
        """)
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

        async with AsyncSessionLocal() as session:
            try:
                if payload["traffic_obs_rows"]:
                    await session.execute(obs_stmt, payload["traffic_obs_rows"])

                # Batch persist segment_los_history with per-row savepoint quarantine fallback (BUG-31)
                if payload["los_hist_rows"]:
                    try:
                        async with session.begin_nested():
                            await session.execute(los_hist_stmt, payload["los_hist_rows"])
                    except Exception:
                        for hist_params, payload_meta in zip(
                            payload["los_hist_rows"], payload["los_hist_meta"]
                        ):
                            try:
                                async with session.begin_nested():
                                    await session.execute(los_hist_stmt, hist_params)
                            except Exception as los_err:
                                self._record_los_history_failure(
                                    hist_params=hist_params,
                                    payload_meta=payload_meta,
                                    now_dt=now_dt,
                                    now_iso=now_iso,
                                    exc=los_err,
                                )

                if payload["energy_obs_rows"]:
                    await session.execute(energy_stmt, payload["energy_obs_rows"])

                if payload["env_obs_rows"]:
                    await session.execute(env_stmt, payload["env_obs_rows"])

                if payload["current_state_rows"]:
                    await session.execute(upsert_state, payload["current_state_rows"])

                # 3c. Advance Canonical Multi-Asset Microgrid Telemetry inside an isolated savepoint
                energy_telemetry_records: List[Dict[str, Any]] = []
                try:
                    from backend.services.energy_topology_service import energy_topology_service

                    async with session.begin_nested():
                        energy_telemetry_records = await energy_topology_service.generate_telemetry_tick(
                            session=session,
                            commit=False,
                        )
                except Exception as energy_err:
                    logger.debug("Microgrid telemetry tick notice: %s", energy_err)

                await session.commit()

                # Update Internal Telemetry State
                self.ticks_count += 1
                self.last_tick_at = now_iso

                segment_metrics_list = payload["segment_metrics_list"]
                building_metrics_list = payload["building_metrics_list"]
                spat_states_list = payload["spat_states_list"]
                energy_load_kw = float(payload["energy_load_kw"])
                aqi = payload["aqi"]

                # 4. Dispatch WebSocket Broadcast Messages
                if self.broadcast_callback:
                    n_segs = max(1, int(payload["segment_count"]))
                    avg_speed = round(float(payload["total_speed"]) / n_segs, 1)
                    cong_idx = round(max(0.05, min(0.95, 1.0 - (avg_speed / 50.0))), 3)
                    corridor_summary = {
                        "eventType": "CORRIDOR_METRICS_UPDATED",
                        "timestamp": now_iso,
                        "sourceMode": self.mode,
                        "averageSpeedKmh": avg_speed,
                        "congestionIndex": cong_idx,
                        "totalFlowPerHour": round(float(payload["total_flow"]), 0),
                        "averageQueueLengthMeters": round(float(payload["total_queue"]) / n_segs, 1),
                        "energyActivePowerKw": round(energy_load_kw, 1),
                        "activeSensors": len(SENSOR_STATIONS),
                        "aqi": aqi,
                        "environment": {
                            "stationId": payload["corridor_station_id"],
                            "aqi": aqi,
                            "aqiCategory": payload["aqi_category"],
                            "temperatureC": payload["temp"],
                            "humidityPct": payload["humidity"],
                            "windSpeedKmh": payload["wind_speed"],
                            "windDir": payload["wind_dir"],
                            "pm25": payload["pm25"],
                            "pm10": payload["pm10"],
                            "no2": payload["no2"],
                            "co": payload["co"],
                            "sourceMode": payload["weather_mode"],
                            "observedAt": now_iso,
                        },
                    }
                    if inspect.iscoroutinefunction(self.broadcast_callback):
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
                        if inspect.iscoroutinefunction(self.broadcast_callback):
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
                            if inspect.iscoroutinefunction(self.broadcast_callback):
                                await self.broadcast_callback(energy_msg)
                            else:
                                self.broadcast_callback(energy_msg)

                    # Also broadcast real-time SPaT signal phase states
                    for spat_item in spat_states_list:
                        spat_msg = {
                            "eventType": "SPAT_PHASE_CHANGED",
                            "intersectionId": spat_item["intersectionId"],
                            "activePhase": spat_item["activePhase"],
                            "activePhaseName": spat_item["activePhaseName"],
                            "phaseColor": spat_item["phaseColor"],
                            "timeToNextPhaseSec": spat_item["timeToNextPhaseSec"],
                            "cycleLengthSec": spat_item["cycleLengthSec"],
                            "elapsedCycleSec": spat_item["elapsedCycleSec"],
                            "freshnessStatus": spat_item["freshnessStatus"],
                            "sourceMode": spat_item["sourceMode"],
                            "timestamp": now_iso
                        }
                        if inspect.iscoroutinefunction(self.broadcast_callback):
                            await self.broadcast_callback(spat_msg)
                        else:
                            self.broadcast_callback(spat_msg)

                    # Broadcast real-time canonical microgrid telemetry (Energy TASK-01)
                    if energy_telemetry_records:
                        microgrid_msg = {
                            "eventType": "MICROGRID_TELEMETRY_UPDATED",
                            "observedAt": now_iso,
                            "sourceMode": self.mode,
                            "records": energy_telemetry_records
                        }
                        if inspect.iscoroutinefunction(self.broadcast_callback):
                            await self.broadcast_callback(microgrid_msg)
                        else:
                            self.broadcast_callback(microgrid_msg)

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
