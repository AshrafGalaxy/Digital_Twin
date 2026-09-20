"""
state_projector.py

Projects incoming validated events into TimescaleDB observation tables
and updates authoritative entity_current_state.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from core.constants import EntityType, QualityStatus, SourceMode
    from schemas.canonical import (
        EnergyObservationEvent,
        EnvironmentObservationEvent,
        TrafficObservationEvent
    )
except ImportError:
    from backend.core.constants import EntityType, QualityStatus, SourceMode
    from backend.schemas.canonical import (
        EnergyObservationEvent,
        EnvironmentObservationEvent,
        TrafficObservationEvent
    )

logger = logging.getLogger(__name__)

class StateProjector:
    @staticmethod
    async def project_traffic_observation(
        session: AsyncSession,
        event: TrafficObservationEvent,
        raw_payload: Optional[Dict[str, Any]] = None
    ) -> None:
        # 1. Insert into TimescaleDB traffic_observations hypertable
        insert_obs_sql = text("""
            INSERT INTO traffic_observations (
                observed_at, sensor_id, segment_id, source_mode,
                average_speed_kmh, vehicle_flow_per_hour, occupancy_percent,
                queue_length_meters, congestion_index, quality_flag, raw_payload
            ) VALUES (
                :observed_at, :sensor_id, :segment_id, :source_mode,
                :average_speed_kmh, :vehicle_flow_per_hour, :occupancy_percent,
                :queue_length_meters, :congestion_index, :quality_flag, :raw_payload
            )
        """)
        
        await session.execute(insert_obs_sql, {
            "observed_at": event.observedAt,
            "sensor_id": event.sensorId,
            "segment_id": event.segmentId,
            "source_mode": event.sourceMode.value,
            "average_speed_kmh": event.averageSpeedKmh,
            "vehicle_flow_per_hour": event.vehicleFlowPerHour,
            "occupancy_percent": event.occupancyPercent,
            "queue_length_meters": event.queueLengthMeters,
            "congestion_index": event.congestionIndex,
            "quality_flag": event.qualityFlag.value,
            "raw_payload": json.dumps(raw_payload) if raw_payload else None
        })

        # 2. State Separation Invariant:
        # ONLY LIVE and REPLAY observations can update authoritative twin_current_state!
        # SIMULATION observations cannot overwrite current state.
        if event.sourceMode in (SourceMode.LIVE, SourceMode.REPLAY):
            metrics = {
                "averageSpeedKmh": event.averageSpeedKmh,
                "vehicleFlowPerHour": event.vehicleFlowPerHour,
                "occupancyPercent": event.occupancyPercent,
                "queueLengthMeters": event.queueLengthMeters,
                "congestionIndex": event.congestionIndex
            }
            
            upsert_state_sql = text("""
                INSERT INTO entity_current_state (
                    entity_id, entity_type, source_mode, observed_at,
                    updated_at, metrics, quality_status, freshness_seconds
                ) VALUES (
                    :entity_id, :entity_type, :source_mode, :observed_at,
                    NOW(), :metrics, :quality_status, :freshness_seconds
                )
                ON CONFLICT (entity_id) DO UPDATE SET
                    source_mode = EXCLUDED.source_mode,
                    observed_at = EXCLUDED.observed_at,
                    updated_at = NOW(),
                    metrics = EXCLUDED.metrics,
                    quality_status = EXCLUDED.quality_status,
                    freshness_seconds = EXCLUDED.freshness_seconds
                WHERE EXCLUDED.observed_at >= entity_current_state.observed_at
            """)

            now_utc = datetime.now(timezone.utc)
            freshness = max(0.0, (now_utc - event.observedAt).total_seconds())

            # Update segment state
            await session.execute(upsert_state_sql, {
                "entity_id": event.segmentId,
                "entity_type": EntityType.ROAD_SEGMENT.value,
                "source_mode": event.sourceMode.value,
                "observed_at": event.observedAt,
                "metrics": json.dumps(metrics),
                "quality_status": event.qualityFlag.value,
                "freshness_seconds": round(freshness, 1)
            })

            # Update sensor state
            await session.execute(upsert_state_sql, {
                "entity_id": event.sensorId,
                "entity_type": EntityType.TRAFFIC_SENSOR.value,
                "source_mode": event.sourceMode.value,
                "observed_at": event.observedAt,
                "metrics": json.dumps(metrics),
                "quality_status": event.qualityFlag.value,
                "freshness_seconds": round(freshness, 1)
            })

    @staticmethod
    async def project_energy_observation(
        session: AsyncSession,
        event: EnergyObservationEvent,
        raw_payload: Optional[Dict[str, Any]] = None
    ) -> None:
        insert_obs_sql = text("""
            INSERT INTO energy_observations (
                observed_at, building_id, source_mode, active_power_kw,
                reactive_power_kvar, power_factor, energy_consumption_kwh,
                quality_flag, raw_payload
            ) VALUES (
                :observed_at, :building_id, :source_mode, :active_power_kw,
                :reactive_power_kvar, :power_factor, :energy_consumption_kwh,
                :quality_flag, :raw_payload
            )
        """)
        await session.execute(insert_obs_sql, {
            "observed_at": event.observedAt,
            "building_id": event.buildingId,
            "source_mode": event.sourceMode.value,
            "active_power_kw": event.activePowerKw,
            "reactive_power_kvar": event.reactivePowerKvar,
            "power_factor": event.powerFactor,
            "energy_consumption_kwh": event.energyConsumptionKwh,
            "quality_flag": event.qualityFlag.value,
            "raw_payload": json.dumps(raw_payload) if raw_payload else None
        })

        if event.sourceMode in (SourceMode.LIVE, SourceMode.REPLAY):
            metrics = {
                "activePowerKw": event.activePowerKw,
                "reactivePowerKvar": event.reactivePowerKvar,
                "powerFactor": event.powerFactor,
                "energyConsumptionKwh": event.energyConsumptionKwh
            }
            upsert_state_sql = text("""
                INSERT INTO entity_current_state (
                    entity_id, entity_type, source_mode, observed_at,
                    updated_at, metrics, quality_status, freshness_seconds
                ) VALUES (
                    :entity_id, :entity_type, :source_mode, :observed_at,
                    NOW(), :metrics, :quality_status, :freshness_seconds
                )
                ON CONFLICT (entity_id) DO UPDATE SET
                    source_mode = EXCLUDED.source_mode,
                    observed_at = EXCLUDED.observed_at,
                    updated_at = NOW(),
                    metrics = EXCLUDED.metrics,
                    quality_status = EXCLUDED.quality_status,
                    freshness_seconds = EXCLUDED.freshness_seconds
                WHERE EXCLUDED.observed_at >= entity_current_state.observed_at
            """)
            now_utc = datetime.now(timezone.utc)
            freshness = max(0.0, (now_utc - event.observedAt).total_seconds())
            await session.execute(upsert_state_sql, {
                "entity_id": event.buildingId,
                "entity_type": EntityType.BUILDING.value,
                "source_mode": event.sourceMode.value,
                "observed_at": event.observedAt,
                "metrics": json.dumps(metrics),
                "quality_status": event.qualityFlag.value,
                "freshness_seconds": round(freshness, 1)
            })

    @staticmethod
    async def project_environment_observation(
        session: AsyncSession,
        event: EnvironmentObservationEvent,
        raw_payload: Optional[Dict[str, Any]] = None
    ) -> None:
        insert_obs_sql = text("""
            INSERT INTO environment_observations (
                observed_at, station_id, source_mode, aqi_value,
                pm25, pm10, temperature_c, relative_humidity_pct,
                precipitation_mm, quality_flag
            ) VALUES (
                :observed_at, :station_id, :source_mode, :aqi_value,
                :pm25, :pm10, :temperature_c, :relative_humidity_pct,
                :precipitation_mm, :quality_flag
            )
        """)
        await session.execute(insert_obs_sql, {
            "observed_at": event.observedAt,
            "station_id": event.stationId,
            "source_mode": event.sourceMode.value,
            "aqi_value": event.aqiValue,
            "pm25": event.pm25,
            "pm10": event.pm10,
            "temperature_c": event.temperatureC,
            "relative_humidity_pct": event.relativeHumidityPct,
            "precipitation_mm": event.precipitationMm,
            "quality_flag": event.qualityFlag.value
        })

    @staticmethod
    async def record_ingestion_error(
        session: AsyncSession,
        topic: str,
        source_mode: Optional[str],
        raw_payload: Dict[str, Any],
        error_reason: str
    ) -> None:
        error_sql = text("""
            INSERT INTO ingestion_errors (
                occurred_at, topic, source_mode, raw_payload, error_reason
            ) VALUES (
                NOW(), :topic, :source_mode, :raw_payload, :error_reason
            )
        """)
        await session.execute(error_sql, {
            "topic": topic,
            "source_mode": source_mode,
            "raw_payload": json.dumps(raw_payload),
            "error_reason": error_reason
        })
