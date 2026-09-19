"""
run_tests.py

Test runner utilizing standard library unittest to verify schemas and validation logic.
"""

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

try:
    from pydantic import ValidationError
    from backend.core.constants import QualityStatus, SourceMode
    from backend.schemas.canonical import (
        EnergyObservationEvent,
        ForecastRecord,
        TrafficObservationEvent
    )
    from backend.ingestion.validator import IngestionValidator
    HAS_DEPENDENCIES = True
except ImportError as err:
    print(f"Dependencies not installed in local environment ({err}). Skipping in-process execution.")
    HAS_DEPENDENCIES = False

class TestCanonicalSchemas(unittest.TestCase):
    @unittest.skipUnless(HAS_DEPENDENCIES, "Requires pydantic")
    def test_valid_traffic_observation(self):
        now = datetime.now(timezone.utc)
        event = TrafficObservationEvent(
            observedAt=now,
            sensorId="urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-01",
            segmentId="urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
            sourceMode=SourceMode.REPLAY,
            averageSpeedKmh=38.5,
            vehicleFlowPerHour=1420.0,
            occupancyPercent=45.2,
            queueLengthMeters=65.0
        )
        self.assertEqual(event.averageSpeedKmh, 38.5)
        self.assertEqual(event.sourceMode, SourceMode.REPLAY)
        self.assertEqual(event.qualityFlag, QualityStatus.VALID)

    @unittest.skipUnless(HAS_DEPENDENCIES, "Requires pydantic")
    def test_invalid_speed_bounds(self):
        now = datetime.now(timezone.utc)
        with self.assertRaises(ValidationError):
            TrafficObservationEvent(
                observedAt=now,
                sensorId="urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-01",
                segmentId="urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
                sourceMode=SourceMode.LIVE,
                averageSpeedKmh=195.0,  # exceeds 120 km/h bound
                vehicleFlowPerHour=100.0
            )

    @unittest.skipUnless(HAS_DEPENDENCIES, "Requires pydantic")
    def test_forecast_source_mode_invariant(self):
        now = datetime.now(timezone.utc)
        record = ForecastRecord(
            targetTimestamp=now,
            entityId="urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
            domain="TRAFFIC",
            modelVersionId="XGBoost_Traffic_v1.0",
            horizonMinutes=15,
            predictedValue=32.4,
            unit="km/h"
        )
        self.assertEqual(record.sourceMode, SourceMode.PREDICTED)

class TestIngestionValidation(unittest.TestCase):
    @unittest.skipUnless(HAS_DEPENDENCIES, "Requires pydantic")
    def test_valid_ingestion(self):
        now_utc = datetime.now(timezone.utc)
        payload = {
            "observedAt": now_utc.isoformat(),
            "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-01",
            "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
            "sourceMode": "REPLAY",
            "averageSpeedKmh": 25.0,
            "vehicleFlowPerHour": 1800.0,
            "occupancyPercent": 60.0
        }
        is_valid, error, event = IngestionValidator.validate_traffic_event(payload)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        self.assertEqual(event.congestionIndex, 0.5)

    @unittest.skipUnless(HAS_DEPENDENCIES, "Requires pydantic")
    def test_future_timestamp_rejected(self):
        future = datetime.now(timezone.utc) + timedelta(minutes=10)
        payload = {
            "observedAt": future.isoformat(),
            "sensorId": "urn:ngsi-ld:TrafficSensor:PUNE:DS-VN-EB-01",
            "segmentId": "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01",
            "sourceMode": "LIVE",
            "averageSpeedKmh": 45.0,
            "vehicleFlowPerHour": 800.0
        }
        is_valid, error, event = IngestionValidator.validate_traffic_event(payload)
        self.assertFalse(is_valid)
        self.assertIn("in future", error)

if __name__ == "__main__":
    unittest.main()
