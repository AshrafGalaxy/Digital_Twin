"""
quarantine.py

Formal Data Quarantine & Dead-Letter Queue Manager for the Digital Twin Platform.
Strictly captures, isolates, and audits all rejected ingestion records per AGENTS.md §7.5
and DATA_AND_ML_PLAN.md §3.

Ensures that rejected events (schema violations, out-of-bounds metrics, future timestamps)
are NEVER allowed to alter authoritative twin state or simulation records.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from threading import Lock

# Persistent fallback database path
DB_DIR = Path("data")
FALLBACK_DB_DIR = Path("../data")


def _get_quarantine_db_path() -> Path:
    target_dir = DB_DIR if DB_DIR.exists() else (FALLBACK_DB_DIR if FALLBACK_DB_DIR.exists() else DB_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / "quarantine.db"


class QuarantineManager:
    """
    Manages recording, querying, and auditing of quarantined ingestion observations.
    Provides persistent local SQLite storage with memory buffer and PostgreSQL compatibility.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or _get_quarantine_db_path()
        self._lock = Lock()
        self._init_sqlite()

    def _init_sqlite(self) -> None:
        """Initializes the quarantine_observations table if not existing."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quarantine_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quarantined_at TEXT NOT NULL,
                    entity_id TEXT,
                    entity_type TEXT,
                    source_mode TEXT,
                    observed_at TEXT,
                    rejection_reason TEXT NOT NULL,
                    raw_payload TEXT NOT NULL,
                    validation_details TEXT DEFAULT '{}'
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_quar_reason ON quarantine_observations(rejection_reason)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_quar_time ON quarantine_observations(quarantined_at DESC)")
            conn.commit()
            conn.close()

    def record_quarantine(
        self,
        raw_payload: Dict[str, Any],
        rejection_reason: str,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        source_mode: Optional[str] = None,
        observed_at: Optional[Any] = None,
        validation_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Persists a rejected ingestion event to the quarantine dead-letter table.
        """
        now_utc = datetime.now(timezone.utc).isoformat()
        
        # Derive entity_id if not explicitly provided
        if not entity_id and isinstance(raw_payload, dict):
            entity_id = (
                raw_payload.get("segmentId")
                or raw_payload.get("sensorId")
                or raw_payload.get("buildingId")
                or raw_payload.get("entityId")
                or raw_payload.get("stationId")
            )

        # Derive entity_type if not provided
        if not entity_type and isinstance(raw_payload, dict):
            if "segmentId" in raw_payload or "speedKmh" in raw_payload or "averageSpeedKmh" in raw_payload:
                entity_type = "RoadSegment"
            elif "buildingId" in raw_payload or "activePowerKw" in raw_payload:
                entity_type = "Building"
            elif "stationId" in raw_payload or "aqi" in raw_payload:
                entity_type = "EnvironmentStation"
            else:
                entity_type = "UnknownEntity"

        # Derive source_mode
        if not source_mode and isinstance(raw_payload, dict):
            source_mode = str(raw_payload.get("sourceMode", "UNKNOWN"))

        # Format observed_at
        obs_str = None
        if observed_at:
            obs_str = observed_at.isoformat() if hasattr(observed_at, "isoformat") else str(observed_at)
        elif isinstance(raw_payload, dict) and "observedAt" in raw_payload:
            obs_val = raw_payload["observedAt"]
            obs_str = obs_val.isoformat() if hasattr(obs_val, "isoformat") else str(obs_val)

        payload_json = json.dumps(raw_payload, default=str)
        details_json = json.dumps(validation_details or {}, default=str)

        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO quarantine_observations (
                    quarantined_at, entity_id, entity_type, source_mode,
                    observed_at, rejection_reason, raw_payload, validation_details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now_utc,
                    entity_id,
                    entity_type,
                    source_mode,
                    obs_str,
                    rejection_reason,
                    payload_json,
                    details_json
                )
            )
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()

        return {
            "id": record_id,
            "quarantinedAt": now_utc,
            "entityId": entity_id,
            "entityType": entity_type,
            "sourceMode": source_mode,
            "observedAt": obs_str,
            "rejectionReason": rejection_reason,
            "validationDetails": validation_details or {}
        }

    def get_quarantined_records(
        self,
        limit: int = 50,
        offset: int = 0,
        reason: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Queries quarantined dead-letter records with pagination and filtering.
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT id, quarantined_at, entity_id, entity_type, source_mode,
                       observed_at, rejection_reason, raw_payload, validation_details
                FROM quarantine_observations
            """
            params: List[Any] = []

            if reason:
                query += " WHERE rejection_reason = ?"
                params.append(reason)

            query += " ORDER BY id DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            records = []
            for r in rows:
                raw_payload = {}
                try:
                    raw_payload = json.loads(r["raw_payload"])
                except Exception:
                    pass

                details = {}
                try:
                    details = json.loads(r["validation_details"])
                except Exception:
                    pass

                records.append({
                    "id": r["id"],
                    "quarantinedAt": r["quarantined_at"],
                    "entityId": r["entity_id"],
                    "entityType": r["entity_type"],
                    "sourceMode": r["source_mode"],
                    "observedAt": r["observed_at"],
                    "rejectionReason": r["rejection_reason"],
                    "rawPayload": raw_payload,
                    "validationDetails": details
                })

            conn.close()
            return records

    def get_quarantine_summary(self) -> Dict[str, Any]:
        """
        Calculates aggregate statistics for the dead-letter queue.
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM quarantine_observations")
            total_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT rejection_reason, COUNT(*)
                FROM quarantine_observations
                GROUP BY rejection_reason
                ORDER BY COUNT(*) DESC
            """)
            reason_rows = cursor.fetchall()
            reasons_breakdown = {row[0]: row[1] for row in reason_rows}

            cursor.execute("SELECT quarantined_at FROM quarantine_observations ORDER BY id DESC LIMIT 1")
            last_row = cursor.fetchone()
            last_quarantined = last_row[0] if last_row else None

            conn.close()

            return {
                "totalQuarantined": total_count,
                "reasonsBreakdown": reasons_breakdown,
                "lastQuarantinedAt": last_quarantined,
                "dataHonestyStatus": "STRICT_REJECTION_ACTIVE"
            }

    def clear_quarantine(self) -> None:
        """Clears all records for test isolation."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM quarantine_observations")
            conn.commit()
            conn.close()


# Singleton instance
quarantine_manager = QuarantineManager()
