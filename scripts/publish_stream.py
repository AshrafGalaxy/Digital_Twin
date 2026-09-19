"""
publish_stream.py

Event streaming worker to publish synthetic or replayed traffic, energy,
and environmental observations to Eclipse Mosquitto MQTT.

Usage:
    python scripts/publish_stream.py [--mode simulation|replay] [--interval 2.0] [--count 50]
"""

import argparse
import json
import logging
import math
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

MQTT_HOST = "localhost"
MQTT_PORT = 1883
TOPIC_TRAFFIC = "dt/v1/corridor/traffic/observations"
TOPIC_ENERGY = "dt/v1/corridor/energy/observations"
TOPIC_ENV = "dt/v1/corridor/environment/observations"

SEGMENTS = [
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01", "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-01", "freeFlow": 45.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-02", "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-02", "freeFlow": 48.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-03", "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-SN-EB-02", "freeFlow": 45.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-01", "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-SN-WB-01", "freeFlow": 45.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-02", "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-SN-WB-02", "freeFlow": 48.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-WB-03", "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-WB-02", "freeFlow": 45.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-VN-NB-01", "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-NB-01", "freeFlow": 35.0},
    {"id": "urn:ngsi-ld:RoadSegment:PUNE:SEG-SN-NB-01", "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-SN-NB-01", "freeFlow": 30.0},
]

def generate_traffic_event(seg: Dict[str, Any], step: int, mode: str) -> Dict[str, Any]:
    # Simulate cyclical congestion variation (e.g. evening peak rush)
    cycle = (math.sin(step * 0.15) + 1.0) / 2.0  # 0.0 to 1.0
    free_flow = seg["freeFlow"]
    speed = round(max(12.0, free_flow - (cycle * 26.0) + random.uniform(-2.5, 2.5)), 1)
    flow = round(800 + (cycle * 1600) + random.uniform(-50, 50), 0)
    occupancy = round(min(95.0, 20.0 + (cycle * 55.0) + random.uniform(-3, 3)), 1)
    queue = round(max(0.0, (cycle * 180.0) + random.uniform(-10, 10)), 1)
    congestion_index = round(max(0.0, min(1.0, 1.0 - (speed / free_flow))), 3)

    return {
        "observedAt": datetime.now(timezone.utc).isoformat(),
        "sensorId": seg["sensorId"],
        "segmentId": seg["id"],
        "sourceMode": "REPLAY" if mode == "replay" else "SIMULATION",
        "averageSpeedKmh": speed,
        "vehicleFlowPerHour": flow,
        "occupancyPercent": occupancy,
        "queueLengthMeters": queue,
        "congestionIndex": congestion_index,
        "qualityFlag": "VALID"
    }

def generate_energy_event(step: int, mode: str) -> Dict[str, Any]:
    cycle = (math.sin(step * 0.1) + 1.0) / 2.0
    active_power = round(3200 + (cycle * 2200) + random.uniform(-80, 80), 1)
    reactive_power = round(active_power * 0.18 + random.uniform(-10, 10), 1)

    return {
        "observedAt": datetime.now(timezone.utc).isoformat(),
        "buildingId": "urn:ngsi-ld:Building:PUNE:BLD-PHOENIX-01",
        "sourceMode": "REPLAY" if mode == "replay" else "SIMULATION",
        "activePowerKw": active_power,
        "reactivePowerKvar": reactive_power,
        "powerFactor": 0.98,
        "qualityFlag": "VALID"
    }

def main():
    parser = argparse.ArgumentParser(description="Publish real-time traffic and energy stream to MQTT")
    parser.add_argument("--mode", choices=["simulation", "replay"], default="simulation", help="Stream source mode")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between emission rounds")
    parser.add_argument("--count", type=int, default=100, help="Total emission cycles (0 for infinite)")
    parser.add_argument("--host", type=str, default=MQTT_HOST, help="MQTT broker host")
    parser.add_argument("--port", type=int, default=MQTT_PORT, help="MQTT broker port")
    args = parser.parse_args()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"stream_publisher_{random.randint(100, 999)}")
    
    try:
        logging.info("Connecting to MQTT broker at %s:%d...", args.host, args.port)
        client.connect(args.host, args.port, 60)
        client.loop_start()
        logging.info("Connected. Starting stream in mode='%s' with interval=%.1fs...", args.mode.upper(), args.interval)
    except Exception as exc:
        logging.warning("Could not connect to MQTT broker (%s). Logging generated sample payloads locally instead.", exc)
        client = None

    step = 0
    while True:
        step += 1
        # Pick 2-3 random segments per step to simulate staggered sensor transmissions
        active_segs = random.sample(SEGMENTS, k=3)
        for seg in active_segs:
            traffic_event = generate_traffic_event(seg, step, args.mode)
            payload_str = json.dumps(traffic_event)
            if client:
                client.publish(TOPIC_TRAFFIC, payload_str)
            logging.info("[%s] Traffic %s: Speed=%.1f km/h, Flow=%.0f veh/h, Congestion=%.2f",
                         args.mode.upper(), seg["id"].split(":")[-1],
                         traffic_event["averageSpeedKmh"], traffic_event["vehicleFlowPerHour"], traffic_event["congestionIndex"])

        # Publish energy event every 2 steps
        if step % 2 == 0:
            energy_event = generate_energy_event(step, args.mode)
            payload_str = json.dumps(energy_event)
            if client:
                client.publish(TOPIC_ENERGY, payload_str)
            logging.info("[%s] Energy BLD-PHOENIX-01: Active Power=%.1f kW", args.mode.upper(), energy_event["activePowerKw"])

        if args.count > 0 and step >= args.count:
            logging.info("Completed %d emission cycles. Exiting.", args.count)
            break

        time.sleep(args.interval)

    if client:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
