"""
mqtt_consumer.py

MQTT background listener subscribing to corridor observation topics,
validating incoming payloads, and invoking state projection.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

import paho.mqtt.client as mqtt

from ..core.config import settings
from ..core.constants import (
    MQTT_TOPIC_ALL,
    MQTT_TOPIC_ENERGY_OBS,
    MQTT_TOPIC_ENV_OBS,
    MQTT_TOPIC_TRAFFIC_OBS
)
from ..core.database import AsyncSessionLocal
from .state_projector import StateProjector
from .validator import IngestionValidator

logger = logging.getLogger(__name__)

class MQTTConsumer:
    def __init__(self, broadcast_callback: Optional[Callable[[Dict[str, Any]], Any]] = None):
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=settings.MQTT_CLIENT_ID
        )
        if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
            
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.broadcast_callback = broadcast_callback
        self.loop = None
        self._is_running = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("Successfully connected to MQTT Broker at %s:%d", settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT)
            client.subscribe(MQTT_TOPIC_ALL)
            logger.info("Subscribed to wildcard topic: %s", MQTT_TOPIC_ALL)
        else:
            logger.error("Failed to connect to MQTT broker, return code: %d", rc)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            topic = msg.topic
            if self.loop and self._is_running:
                asyncio.run_coroutine_threadsafe(self._process_message(topic, payload), self.loop)
        except Exception as exc:
            logger.error("Error decoding MQTT message on topic %s: %s", msg.topic, exc)

    async def _process_message(self, topic: str, payload: Dict[str, Any]):
        async with AsyncSessionLocal() as session:
            try:
                if topic == MQTT_TOPIC_TRAFFIC_OBS:
                    is_valid, error, event = IngestionValidator.validate_traffic_event(payload)
                    if not is_valid:
                        logger.warning("Ingestion validation error on %s: %s", topic, error)
                        await StateProjector.record_ingestion_error(
                            session, topic, payload.get("sourceMode"), payload, error or "Validation failed"
                        )
                        await session.commit()
                        return

                    await StateProjector.project_traffic_observation(session, event, payload)
                    await session.commit()

                    # Broadcast state update to connected WebSocket clients
                    if self.broadcast_callback:
                        update_msg = {
                            "eventType": "TRAFFIC_STATE_UPDATED",
                            "entityId": event.segmentId,
                            "sourceMode": event.sourceMode.value,
                            "observedAt": event.observedAt.isoformat(),
                            "metrics": {
                                "averageSpeedKmh": event.averageSpeedKmh,
                                "congestionIndex": event.congestionIndex,
                                "queueLengthMeters": event.queueLengthMeters
                            }
                        }
                        if asyncio.iscoroutinefunction(self.broadcast_callback):
                            await self.broadcast_callback(update_msg)
                        else:
                            self.broadcast_callback(update_msg)

            except Exception as exc:
                await session.rollback()
                logger.error("Database error processing message from %s: %s", topic, exc)

    def start(self):
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
        self._is_running = True
        logger.info("Starting MQTT consumer thread connecting to %s:%d...", settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT)
        try:
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
            self.client.loop_start()
        except Exception as exc:
            logger.warning("Could not connect to MQTT broker on startup: %s. Continuing in offline mode.", exc)

    def stop(self):
        self._is_running = False
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("MQTT consumer stopped.")
