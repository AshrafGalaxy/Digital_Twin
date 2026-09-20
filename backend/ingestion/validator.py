"""
validator.py

Ingestion validation pipeline enforcing schema, range, timestamp, and source-mode checks.
Integrates with QuarantineManager (P3-B) to record all rejected events into the formal
quarantine_observations dead-letter queue.
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
    from ingestion.quarantine import quarantine_manager
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
    from backend.ingestion.quarantine import quarantine_manager


def _extract_rejection_reason_from_pydantic(err: ValidationError) -> Tuple[str, str]:
    """Derives a standardized rejection reason code and detail message from Pydantic errors."""
    first_err = err.errors()[0]
    loc = first_err.get("loc", ())
    msg = first_err.get("msg", "Validation error")
    err_type = first_err.get("type", "")
    field_name = str(loc[-1]) if loc else ""

    if "missing" in msg.lower() or "missing" in err_type.lower() or "required" in msg.lower():
        return "SCHEMA_VALIDATION_FAILED", f"Missing mandatory field '{field_name}'"
    if field_name in ("averageSpeedKmh", "speedKmh"):
        return "SPEED_OUT_OF_BOUNDS", f"Speed metric failed validation: {msg}"
    if field_name == "occupancyPercent":
        return "OCCUPANCY_OUT_OF_BOUNDS", f"Occupancy metric failed validation: {msg}"
    if field_name == "activePowerKw":
        return "POWER_OUT_OF_BOUNDS", f"Active power failed validation: {msg}"
    if field_name == "observedAt":
        return "TIMESTAMP_FORMAT_INVALID", f"Timestamp failed validation: {msg}"
    return "SCHEMA_VALIDATION_FAILED", f"Schema validation failed on '{field_name}': {msg}"


class IngestionValidator:
    @staticmethod
    def validate_traffic_event(raw_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[TrafficObservationEvent]]:
        try:
            event = TrafficObservationEvent(**raw_data)
        except ValidationError as err:
            reason, detail = _extract_rejection_reason_from_pydantic(err)
            quarantine_manager.record_quarantine(
                raw_payload=raw_data,
                rejection_reason=reason,
                entity_id=raw_data.get("segmentId") or raw_data.get("sensorId"),
                entity_type="RoadSegment",
                source_mode=str(raw_data.get("sourceMode", "UNKNOWN")),
                validation_details={"error": detail, "pydanticErrors": err.errors()}
            )
            return False, detail, None
        except Exception as exc:
            detail = f"Malformed traffic payload: {str(exc)}"
            quarantine_manager.record_quarantine(
                raw_payload=raw_data,
                rejection_reason="MALFORMED_PAYLOAD",
                entity_id=raw_data.get("segmentId") if isinstance(raw_data, dict) else None,
                entity_type="RoadSegment",
                validation_details={"error": detail}
            )
            return False, detail, None

        # Check timestamp sanity (cannot be far future)
        now_utc = datetime.now(timezone.utc)
        time_diff = (now_utc - event.observedAt).total_seconds()

        if time_diff < -60.0:  # More than 1 minute in the future
            detail = f"Observation timestamp is in future: {event.observedAt.isoformat()}"
            quarantine_manager.record_quarantine(
                raw_payload=raw_data,
                rejection_reason="FUTURE_TIMESTAMP_REJECTED",
                entity_id=event.segmentId,
                entity_type="RoadSegment",
                source_mode=event.sourceMode.value,
                observed_at=event.observedAt,
                validation_details={"error": detail, "timeDifferenceSeconds": round(time_diff, 1)}
            )
            return False, detail, None

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
            reason, detail = _extract_rejection_reason_from_pydantic(err)
            quarantine_manager.record_quarantine(
                raw_payload=raw_data,
                rejection_reason=reason,
                entity_id=raw_data.get("buildingId"),
                entity_type="Building",
                source_mode=str(raw_data.get("sourceMode", "UNKNOWN")),
                validation_details={"error": detail, "pydanticErrors": err.errors()}
            )
            return False, detail, None
        except Exception as exc:
            detail = f"Malformed energy payload: {str(exc)}"
            quarantine_manager.record_quarantine(
                raw_payload=raw_data,
                rejection_reason="MALFORMED_PAYLOAD",
                entity_id=raw_data.get("buildingId") if isinstance(raw_data, dict) else None,
                entity_type="Building",
                validation_details={"error": detail}
            )
            return False, detail, None

        now_utc = datetime.now(timezone.utc)
        time_diff = (now_utc - event.observedAt).total_seconds()
        if time_diff < -60.0:
            detail = f"Observation timestamp is in future: {event.observedAt.isoformat()}"
            quarantine_manager.record_quarantine(
                raw_payload=raw_data,
                rejection_reason="FUTURE_TIMESTAMP_REJECTED",
                entity_id=event.buildingId,
                entity_type="Building",
                source_mode=event.sourceMode.value,
                observed_at=event.observedAt,
                validation_details={"error": detail, "timeDifferenceSeconds": round(time_diff, 1)}
            )
            return False, detail, None

        if time_diff > ENERGY_FRESHNESS_THRESHOLD_SEC and event.sourceMode == SourceMode.LIVE:
            event.qualityFlag = QualityStatus.STALE

        return True, None, event

    @staticmethod
    def validate_environment_event(raw_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[EnvironmentObservationEvent]]:
        try:
            event = EnvironmentObservationEvent(**raw_data)
        except ValidationError as err:
            reason, detail = _extract_rejection_reason_from_pydantic(err)
            quarantine_manager.record_quarantine(
                raw_payload=raw_data,
                rejection_reason=reason,
                entity_id=raw_data.get("stationId"),
                entity_type="EnvironmentStation",
                source_mode=str(raw_data.get("sourceMode", "UNKNOWN")),
                validation_details={"error": detail, "pydanticErrors": err.errors()}
            )
            return False, detail, None
        except Exception as exc:
            detail = f"Malformed environment payload: {str(exc)}"
            quarantine_manager.record_quarantine(
                raw_payload=raw_data,
                rejection_reason="MALFORMED_PAYLOAD",
                entity_id=raw_data.get("stationId") if isinstance(raw_data, dict) else None,
                entity_type="EnvironmentStation",
                validation_details={"error": detail}
            )
            return False, detail, None

        return True, None, event
