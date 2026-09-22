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

try:
    from core.config import settings
    from core.constants import (
        MQTT_TOPIC_ALL,
        MQTT_TOPIC_ENERGY_OBS,
        MQTT_TOPIC_ENV_OBS,
        MQTT_TOPIC_TRAFFIC_OBS,
        MQTT_TOPIC_NAGARTWIN_ALL,
        MQTT_TOPIC_NAGARTWIN_PREFIX
    )
    from core.database import AsyncSessionLocal
    from ingestion.state_projector import StateProjector
    from ingestion.validator import IngestionValidator
except ImportError:
    from backend.core.config import settings
    from backend.core.constants import (
        MQTT_TOPIC_ALL,
        MQTT_TOPIC_ENERGY_OBS,
        MQTT_TOPIC_ENV_OBS,
        MQTT_TOPIC_TRAFFIC_OBS,
        MQTT_TOPIC_NAGARTWIN_ALL,
        MQTT_TOPIC_NAGARTWIN_PREFIX
    )
    from backend.core.database import AsyncSessionLocal
    from backend.ingestion.state_projector import StateProjector
    from backend.ingestion.validator import IngestionValidator

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
            client.subscribe(MQTT_TOPIC_NAGARTWIN_ALL)
            logger.info("Subscribed to MQTT corridor topics: %s and %s", MQTT_TOPIC_ALL, MQTT_TOPIC_NAGARTWIN_ALL)
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
                # 1. Resolve domain from topic
                domain = None
                if topic.startswith(f"{MQTT_TOPIC_NAGARTWIN_PREFIX}/"):
                    # Format: nagartwin/{environment}/{sourceMode}/{domain}/{entityId}
                    parts = topic.split("/")
                    if len(parts) >= 4:
                        domain = parts[3].lower()
                elif topic == MQTT_TOPIC_TRAFFIC_OBS or "/traffic/" in topic:
                    domain = "traffic"
                elif topic == MQTT_TOPIC_ENERGY_OBS or "/energy/" in topic:
                    domain = "energy"
                elif topic == MQTT_TOPIC_ENV_OBS or "/environment/" in topic or "/env/" in topic:
                    domain = "environment"

                # 2. Process by domain
                if domain == "traffic":
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

                elif domain == "energy":
                    is_valid, error, event = IngestionValidator.validate_energy_event(payload)
                    if not is_valid:
                        logger.warning("Energy validation error on %s: %s", topic, error)
                        await StateProjector.record_ingestion_error(
                            session, topic, payload.get("sourceMode"), payload, error or "Validation failed"
                        )
                        await session.commit()
                        return

                    await StateProjector.project_energy_observation(session, event, payload)
                    await session.commit()

                    if self.broadcast_callback:
                        update_msg = {
                            "eventType": "ENERGY_STATE_UPDATED",
                            "entityId": event.buildingId,
                            "sourceMode": event.sourceMode.value,
                            "observedAt": event.observedAt.isoformat(),
                            "metrics": {
                                "activePowerKw": event.activePowerKw,
                                "reactivePowerKvar": event.reactivePowerKvar,
                                "powerFactor": event.powerFactor,
                                "energyConsumptionKwh": event.energyConsumptionKwh
                            }
                        }
                        if asyncio.iscoroutinefunction(self.broadcast_callback):
                            await self.broadcast_callback(update_msg)
                        else:
                            self.broadcast_callback(update_msg)

                elif domain == "environment":
                    is_valid, error, event = IngestionValidator.validate_environment_event(payload)
                    if not is_valid:
                        logger.warning("Environment validation error on %s: %s", topic, error)
                        await StateProjector.record_ingestion_error(
                            session, topic, payload.get("sourceMode"), payload, error or "Validation failed"
                        )
                        await session.commit()
                        return

                    await StateProjector.project_environment_observation(session, event, payload)
                    await session.commit()

                    if self.broadcast_callback:
                        update_msg = {
                            "eventType": "ENVIRONMENT_STATE_UPDATED",
                            "entityId": event.stationId,
                            "sourceMode": event.sourceMode.value,
                            "observedAt": event.observedAt.isoformat(),
                            "metrics": {
                                "aqiValue": event.aqiValue,
                                "pm25": event.pm25,
                                "pm10": event.pm10,
                                "temperatureC": event.temperatureC,
                                "relativeHumidityPct": event.relativeHumidityPct
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
            # Fast non-blocking pre-flight socket probe (0.2s) to avoid 4-second synchronous OS timeout stall
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.2)
            target_host = "127.0.0.1" if settings.MQTT_BROKER_HOST in ("localhost", "") else settings.MQTT_BROKER_HOST
            res = sock.connect_ex((target_host, settings.MQTT_BROKER_PORT))
            sock.close()
            if res != 0:
                logger.info("MQTT broker not active at %s:%d on startup. Continuing in offline mode.", target_host, settings.MQTT_BROKER_PORT)
                return

            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
            self.client.loop_start()
        except Exception as exc:
            logger.warning("Could not connect to MQTT broker on startup: %s. Continuing in offline mode.", exc)

    def stop(self):
        self._is_running = False
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass
        logger.info("MQTT consumer stopped.")
