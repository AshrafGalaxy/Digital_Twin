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

from ..core.constants import EntityType, QualityStatus, SourceMode
from ..schemas.canonical import (
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
