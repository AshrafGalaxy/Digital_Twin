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
    STRUCTURAL_ASSET = "StructuralAsset"

class StructuralIntegrityStatus(str, Enum):
    NOMINAL = "NOMINAL"
    ADVISORY_FATIGUE = "ADVISORY_FATIGUE"
    ALERT_OVERLOAD = "ALERT_OVERLOAD"

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

# Canonical Architecture Hierarchy per TECHNICAL_ARCHITECTURE.md §12.2: nagartwin/{env}/{mode}/{domain}/{id}
MQTT_TOPIC_NAGARTWIN_PREFIX = "nagartwin"
MQTT_TOPIC_NAGARTWIN_ALL = "nagartwin/#"

# SHM Telemetry Topics
MQTT_TOPIC_SHM_TELEMETRY = "citytwin/v1/live/shm/#"
MQTT_TOPIC_SHM_FORMAT = "citytwin/v1/live/shm/flyover/{structure_id}/telemetry"

# Sanity & Freshness Thresholds
TRAFFIC_FRESHNESS_THRESHOLD_SEC = 180.0
ENERGY_FRESHNESS_THRESHOLD_SEC = 900.0
SPEED_MIN_KMH = 0.0
SPEED_MAX_KMH = 120.0
OCCUPANCY_MIN_PCT = 0.0
OCCUPANCY_MAX_PCT = 100.0

# SHM Physical Thresholds (Task 07 / Section 10.1)
SHM_PPV_MIN_MMS = 0.0
SHM_PPV_MAX_MMS = 50.0
SHM_PPV_HARD_MAX_MMS = 100.0
SHM_STRAIN_MIN_MICROSTRAIN = -2000.0
SHM_STRAIN_MAX_MICROSTRAIN = 3000.0
SHM_STRAIN_YIELD_ALERT = 800.0
SHM_HCV_AXLE_LIMIT_TONNES = 10.2
SHM_RESONANT_DRIFT_THRESHOLD_PCT = 5.0
