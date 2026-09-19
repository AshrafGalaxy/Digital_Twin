"""
constants.py

Standardized enums, provenance categories, and topic definitions for the Digital Twin.
"""

from enum import Enum

class SourceMode(str, Enum):
    LIVE = "LIVE"
    REPLAY = "REPLAY"
    SIMULATION = "SIMULATION"
    PREDICTED = "PREDICTED"
    STALE = "STALE"
    INVALID = "INVALID"

class QualityStatus(str, Enum):
    VALID = "VALID"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    INVALID = "INVALID"

class EntityType(str, Enum):
    STUDY_AREA = "StudyArea"
    INTERSECTION = "Intersection"
    ROAD_SEGMENT = "RoadSegment"
    TRAFFIC_SENSOR = "TrafficSensor"
    BUILDING = "Building"

class Direction(str, Enum):
    EASTBOUND = "EASTBOUND"
    WESTBOUND = "WESTBOUND"
    NORTHBOUND = "NORTHBOUND"
    SOUTHBOUND = "SOUTHBOUND"

# MQTT Topics
MQTT_TOPIC_TRAFFIC_OBS = "dt/v1/corridor/traffic/observations"
MQTT_TOPIC_ENERGY_OBS = "dt/v1/corridor/energy/observations"
MQTT_TOPIC_ENV_OBS = "dt/v1/corridor/environment/observations"
MQTT_TOPIC_ALL = "dt/v1/corridor/#"

# Sanity & Freshness Thresholds
TRAFFIC_FRESHNESS_THRESHOLD_SEC = 180.0
ENERGY_FRESHNESS_THRESHOLD_SEC = 900.0
SPEED_MIN_KMH = 0.0
SPEED_MAX_KMH = 120.0
OCCUPANCY_MIN_PCT = 0.0
OCCUPANCY_MAX_PCT = 100.0
