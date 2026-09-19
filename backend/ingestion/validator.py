"""
validator.py

Ingestion validation pipeline enforcing schema, range, timestamp, and source-mode checks.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from pydantic import ValidationError

try:
    from core.constants import (
        ENERGY_FRESHNESS_THRESHOLD_SEC,
        QualityStatus,
        SourceMode,
        TRAFFIC_FRESHNESS_THRESHOLD_SEC
    )
    from schemas.canonical import (
        EnergyObservationEvent,
        EnvironmentObservationEvent,
        TrafficObservationEvent
    )
except ImportError:
    from backend.core.constants import (
        ENERGY_FRESHNESS_THRESHOLD_SEC,
        QualityStatus,
        SourceMode,
        TRAFFIC_FRESHNESS_THRESHOLD_SEC
    )
    from backend.schemas.canonical import (
        EnergyObservationEvent,
        EnvironmentObservationEvent,
        TrafficObservationEvent
    )

class IngestionValidator:
    @staticmethod
    def validate_traffic_event(raw_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[TrafficObservationEvent]]:
        try:
            event = TrafficObservationEvent(**raw_data)
        except ValidationError as err:
            return False, f"Schema validation failed: {err.errors()[0]['msg']}", None
        except Exception as exc:
            return False, f"Malformed traffic payload: {str(exc)}", None

        # Check timestamp sanity (cannot be far future)
        now_utc = datetime.now(timezone.utc)
        time_diff = (now_utc - event.observedAt).total_seconds()
        
        if time_diff < -60.0:  # More than 1 minute in the future
            return False, f"Observation timestamp is in future: {event.observedAt.isoformat()}", None

        # Mark staleness if applicable
        if time_diff > TRAFFIC_FRESHNESS_THRESHOLD_SEC and event.sourceMode == SourceMode.LIVE:
            event.qualityFlag = QualityStatus.STALE

        # Derive congestion index if speed provided and index missing
        if event.congestionIndex is None:
            free_flow = 50.0  # standard arterial free flow speed
            event.congestionIndex = round(max(0.0, min(1.0, 1.0 - (event.averageSpeedKmh / free_flow))), 3)

        return True, None, event

    @staticmethod
    def validate_energy_event(raw_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[EnergyObservationEvent]]:
        try:
            event = EnergyObservationEvent(**raw_data)
        except ValidationError as err:
            return False, f"Schema validation failed: {err.errors()[0]['msg']}", None
        except Exception as exc:
            return False, f"Malformed energy payload: {str(exc)}", None

        now_utc = datetime.now(timezone.utc)
        time_diff = (now_utc - event.observedAt).total_seconds()
        if time_diff < -60.0:
            return False, f"Observation timestamp is in future: {event.observedAt.isoformat()}", None

        if time_diff > ENERGY_FRESHNESS_THRESHOLD_SEC and event.sourceMode == SourceMode.LIVE:
            event.qualityFlag = QualityStatus.STALE

        return True, None, event

    @staticmethod
    def validate_environment_event(raw_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[EnvironmentObservationEvent]]:
        try:
            event = EnvironmentObservationEvent(**raw_data)
        except ValidationError as err:
            return False, f"Schema validation failed: {err.errors()[0]['msg']}", None
        except Exception as exc:
            return False, f"Malformed environment payload: {str(exc)}", None

        return True, None, event
