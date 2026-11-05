"""
shm_service.py

Critical Infrastructure Structural Health Monitoring (SHM) Telemetry Pipeline (TASK-07 / Section 10.1).
Processes continuous tri-axial vibration, FBG strain gauges, resonant natural frequency peak shifts,
and Weigh-in-Motion (WIM) dynamic axle impact load streams for flyovers, bridges, and elevated viaducts.
"""

from datetime import datetime, timezone, timedelta
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.constants import (
    SHM_HCV_AXLE_LIMIT_TONNES,
    SHM_PPV_HARD_MAX_MMS,
    SHM_PPV_MAX_MMS,
    SHM_PPV_MIN_MMS,
    SHM_RESONANT_DRIFT_THRESHOLD_PCT,
    SHM_STRAIN_MAX_MICROSTRAIN,
    SHM_STRAIN_MIN_MICROSTRAIN,
    SHM_STRAIN_YIELD_ALERT,
    EntityType,
    SourceMode,
    StructuralIntegrityStatus,
)
from backend.schemas.shm import (
    SHMStructureStatus,
    SHMStructureSummary,
    SHMTelemetryPayload,
    SHMTelemetryRecord,
)

logger = logging.getLogger("digital_twin.shm")

# Installed gauge ids. A client may label a packet LIVE only when the sensor is one of these.
REGISTERED_SHM_SENSOR_IDS = frozenset({
    "SENSOR-SHM-EB-03",
    "SENSOR-SHM-SN-01",
})
DRIFT_AGREEMENT_TOLERANCE_PCT = 0.05
FUTURE_TIMESTAMP_SKEW = timedelta(seconds=5)


def compute_resonant_drift_pct(measured_hz: float, baseline_hz: float) -> float:
    """Server drift: ((measured - baseline) / baseline) * 100."""
    if baseline_hz <= 0.0:
        raise ValueError("INVALID: resonant baseline must be positive")
    return round(((measured_hz - baseline_hz) / baseline_hz) * 100.0, 2)


def resolve_shm_source_mode(claimed_mode: Optional[str], sensor_id: str) -> str:
    """
    LIVE is stored only for a registered sensor. Any other LIVE claim uses the
    stream mode, which is SIMULATION or REPLAY.
    """
    claimed = (claimed_mode or "").strip().upper()
    if claimed == SourceMode.LIVE.value and sensor_id in REGISTERED_SHM_SENSOR_IDS:
        return SourceMode.LIVE.value
    if claimed in (SourceMode.SIMULATION.value, SourceMode.REPLAY.value):
        return claimed
    stream_mode = str(getattr(settings, "TELEMETRY_STREAMER_MODE", SourceMode.SIMULATION.value)).strip().upper()
    if stream_mode in (SourceMode.SIMULATION.value, SourceMode.REPLAY.value):
        return stream_mode
    return SourceMode.SIMULATION.value

# Initial canonical registered structural assets for corridor demonstration
DEFAULT_STRUCTURES = [
    {
        "structureId": "STR-VN-FLY-01",
        "structureName": "Viman Nagar Corridor Flyover",
        "spans": ["SPAN-01-EB", "SPAN-02-EB", "SPAN-03-EB", "SPAN-01-WB", "SPAN-02-WB", "SPAN-03-WB"],
        "baselineFreqHz": 4.25,
        "sensorCount": 6,
    },
    {
        "structureId": "STR-SN-BRG-01",
        "structureName": "Somnath Nagar River Span Bridge",
        "spans": ["SPAN-01-CENTRAL", "SPAN-02-APPROACH"],
        "baselineFreqHz": 3.80,
        "sensorCount": 4,
    },
]


class SHMTelemetryService:
    """
    Ingestion, physical bounds validation, fatigue drift analysis,
    and structural integrity evaluation engine for highway infrastructure.
    """

    def evaluate_integrity_status(
        self,
        strain_val: float,
        resonant_drift_pct: float,
        hcv_axle_load: Optional[float] = None,
        vibration_ppv: float = 0.0,
    ) -> Tuple[str, List[str]]:
        """
        Evaluates structural integrity status against safety invariants.
        Returns a tuple of (status_enum_str, active_alerts_list).
        """
        alerts: List[str] = []
        is_overload = False
        is_fatigue = False

        # 1. Overload / Elastic Yield Checks
        if strain_val > SHM_STRAIN_YIELD_ALERT:
            alerts.append(
                f"Elastic yield advisory alert: tension strain {strain_val:.1f} uE exceeds {SHM_STRAIN_YIELD_ALERT:.0f} uE limit"
            )
            is_overload = True

        if hcv_axle_load is not None and hcv_axle_load > SHM_HCV_AXLE_LIMIT_TONNES:
            alerts.append(
                f"Weigh-in-Motion overload alert: detected axle load {hcv_axle_load:.1f} tonnes exceeds legal limit {SHM_HCV_AXLE_LIMIT_TONNES:.1f} tonnes"
            )
            is_overload = True

        # 2. Resonant Frequency Degradation / Fatigue Checks
        if abs(resonant_drift_pct) > SHM_RESONANT_DRIFT_THRESHOLD_PCT:
            alerts.append(
                f"Structural stiffness fatigue warning: resonant frequency drift {resonant_drift_pct:+.2f}% exceeds {SHM_RESONANT_DRIFT_THRESHOLD_PCT:.1f}% threshold"
            )
            is_fatigue = True

        if strain_val > 600.0 and not is_overload:
            alerts.append(
                f"Elevated microstrain warning: flange strain {strain_val:.1f} uE exceeds nominal 600 uE threshold"
            )
            is_fatigue = True

        if vibration_ppv > SHM_PPV_MAX_MMS:
            alerts.append(
                f"Excess dynamic vibration: PPV {vibration_ppv:.2f} mm/s exceeds operational envelope {SHM_PPV_MAX_MMS:.1f} mm/s"
            )
            is_fatigue = True

        # 3. Final Status Classification
        if is_overload:
            return StructuralIntegrityStatus.ALERT_OVERLOAD.value, alerts
        elif is_fatigue:
            return StructuralIntegrityStatus.ADVISORY_FATIGUE.value, alerts
        else:
            return StructuralIntegrityStatus.NOMINAL.value, alerts

    async def ingest_shm_payload(
        self, session: AsyncSession, payload_data: Any
    ) -> SHMTelemetryRecord:
        """
        Ingests, validates, evaluates, and persists an SHM telemetry packet.
        Updates shm_telemetry time-series and entity_current_state cache.
        """
        if isinstance(payload_data, dict):
            payload = SHMTelemetryPayload(**payload_data)
        elif isinstance(payload_data, SHMTelemetryPayload):
            payload = payload_data
        else:
            raise ValueError("Invalid payload type for SHM telemetry ingestion")

        # Physical bounds hard validation
        vibration_val = payload.vibrationPPV.value
        strain_val = payload.strain.value
        f0_val = payload.resonantFreqHz.value
        baseline_f0 = payload.resonantFreqHz.baselineHz
        drift_pct = compute_resonant_drift_pct(f0_val, baseline_f0)
        caller_drift = payload.resonantFreqHz.driftPct
        if abs(caller_drift - drift_pct) > DRIFT_AGREEMENT_TOLERANCE_PCT:
            logger.info(
                "Caller resonant drift %.4f discarded. Stored computed drift %.4f.",
                caller_drift,
                drift_pct,
            )

        observed_at = payload.observedAt
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        if observed_at > datetime.now(timezone.utc) + FUTURE_TIMESTAMP_SKEW:
            raise ValueError("INVALID: observedAt is in the future")

        if vibration_val < SHM_PPV_MIN_MMS or vibration_val > SHM_PPV_HARD_MAX_MMS:
            raise ValueError(
                f"Vibration PPV {vibration_val} mm/s violates physical bounds [{SHM_PPV_MIN_MMS}, {SHM_PPV_HARD_MAX_MMS}]"
            )
        if strain_val < SHM_STRAIN_MIN_MICROSTRAIN or strain_val > SHM_STRAIN_MAX_MICROSTRAIN:
            raise ValueError(
                f"Flange microstrain {strain_val} violates physical bounds [{SHM_STRAIN_MIN_MICROSTRAIN}, {SHM_STRAIN_MAX_MICROSTRAIN}]"
            )

        # Evaluate safety invariants
        evaluated_status, alerts = self.evaluate_integrity_status(
            strain_val=strain_val,
            resonant_drift_pct=drift_pct,
            hcv_axle_load=payload.hcvAxleLoadTonnes,
            vibration_ppv=vibration_val,
        )

        obs_iso = observed_at.isoformat()
        now_utc = datetime.now(timezone.utc).isoformat()
        provenance = dict(payload.provenance or {})
        sensor_id = payload.sensorId or "SENSOR-SHM-01"
        source_mode = resolve_shm_source_mode(provenance.get("sourceMode"), sensor_id)
        provenance["sourceMode"] = source_mode
        provenance["resonantDriftPctComputed"] = drift_pct
        quality_score = payload.strain.qualityScore
        structure_name = payload.structureName or payload.structureId

        existing = await session.execute(
            text("SELECT entity_type, metrics FROM entity_current_state WHERE entity_id = :entity_id"),
            {"entity_id": payload.structureId},
        )
        existing_row = existing.fetchone()
        if existing_row is not None and existing_row[0] != EntityType.STRUCTURAL_ASSET.value:
            raise ValueError(
                f"SHM ingest cannot replace current state for entity type {existing_row[0]}"
            )

        # Insert into shm_telemetry table
        insert_stmt = text("""
            INSERT INTO shm_telemetry (
                structure_id, structure_name, span_id, sensor_id, observed_at,
                vibration_ppv_mms, strain_microstrain, resonant_freq_hz,
                resonant_baseline_hz, resonant_drift_pct, temperature_celsius,
                hcv_axle_load_tonnes, integrity_status, source_mode,
                quality_score, provenance_metadata, created_at
            ) VALUES (
                :structure_id, :structure_name, :span_id, :sensor_id, :observed_at,
                :vibration_ppv_mms, :strain_microstrain, :resonant_freq_hz,
                :resonant_baseline_hz, :resonant_drift_pct, :temperature_celsius,
                :hcv_axle_load_tonnes, :integrity_status, :source_mode,
                :quality_score, :provenance_metadata, :created_at
            )
        """)

        await session.execute(
            insert_stmt,
            {
                "structure_id": payload.structureId,
                "structure_name": structure_name,
                "span_id": payload.spanId,
                "sensor_id": sensor_id,
                "observed_at": obs_iso,
                "vibration_ppv_mms": vibration_val,
                "strain_microstrain": strain_val,
                "resonant_freq_hz": f0_val,
                "resonant_baseline_hz": baseline_f0,
                "resonant_drift_pct": drift_pct,
                "temperature_celsius": payload.ambientTempC,
                "hcv_axle_load_tonnes": payload.hcvAxleLoadTonnes,
                "integrity_status": evaluated_status,
                "source_mode": source_mode,
                "quality_score": quality_score,
                "provenance_metadata": json.dumps(provenance),
                "created_at": now_utc,
            },
        )

        # Upsert into entity_current_state cache
        current_metrics = {
            "vibrationPpvMms": vibration_val,
            "strainMicrostrain": strain_val,
            "resonantFreqHz": f0_val,
            "resonantBaselineHz": baseline_f0,
            "resonantDriftPct": drift_pct,
            "temperatureCelsius": payload.ambientTempC,
            "hcvAxleLoadTonnes": payload.hcvAxleLoadTonnes,
            "integrityStatus": evaluated_status,
            "activeAlerts": alerts,
            "spanId": payload.spanId,
            "structureName": structure_name,
        }

        upsert_stmt = text("""
            INSERT INTO entity_current_state (
                entity_id, entity_type, source_mode, observed_at, updated_at,
                metrics, quality_status, freshness_seconds
            ) VALUES (
                :entity_id, :entity_type, :source_mode, :observed_at, :updated_at,
                :metrics, :quality_status, 0.0
            )
            ON CONFLICT (entity_id) DO UPDATE SET
                source_mode = excluded.source_mode,
                observed_at = excluded.observed_at,
                updated_at = excluded.updated_at,
                metrics = excluded.metrics,
                quality_status = excluded.quality_status,
                freshness_seconds = 0.0
        """)

        await session.execute(
            upsert_stmt,
            {
                "entity_id": payload.structureId,
                "entity_type": EntityType.STRUCTURAL_ASSET.value,
                "source_mode": source_mode,
                "observed_at": obs_iso,
                "updated_at": now_utc,
                "metrics": json.dumps(current_metrics),
                "quality_status": "VALID",
            },
        )

        await session.commit()

        return SHMTelemetryRecord(
            structureId=payload.structureId,
            structureName=structure_name,
            spanId=payload.spanId,
            sensorId=sensor_id,
            observedAt=obs_iso,
            vibrationPpvMms=vibration_val,
            strainMicrostrain=strain_val,
            resonantFreqHz=f0_val,
            resonantBaselineHz=baseline_f0,
            resonantDriftPct=drift_pct,
            temperatureCelsius=payload.ambientTempC,
            hcvAxleLoadTonnes=payload.hcvAxleLoadTonnes,
            integrityStatus=evaluated_status,
            sourceMode=source_mode,
            qualityScore=quality_score,
            provenanceMetadata=provenance,
        )

    async def get_monitored_structures(
        self, session: AsyncSession
    ) -> List[SHMStructureSummary]:
        """
        Lists all monitored bridges/flyovers along with current health summary.
        """
        query = text("""
            SELECT 
                structure_id,
                MAX(structure_name) AS structure_name,
                COUNT(DISTINCT span_id) AS total_spans,
                COUNT(DISTINCT sensor_id) AS sensor_count,
                MAX(observed_at) AS last_observed_at,
                MAX(vibration_ppv_mms) AS peak_ppv,
                MAX(strain_microstrain) AS peak_strain
            FROM shm_telemetry
            GROUP BY structure_id
            ORDER BY structure_id ASC
        """)
        res = await session.execute(query)
        rows = res.fetchall()

        summaries: List[SHMStructureSummary] = []
        if rows:
            for r in rows:
                struct_id = r[0]
                latest_record = await self.get_structure_latest(session, struct_id)
                status = latest_record.integrityStatus if latest_record else "NOMINAL"
                freq = latest_record.resonantFreqHz if latest_record else 4.25
                drift = latest_record.resonantDriftPct if latest_record else 0.0

                summaries.append(
                    SHMStructureSummary(
                        structureId=struct_id,
                        structureName=r[1] or struct_id,
                        totalSpans=max(1, r[2]),
                        sensorCount=max(1, r[3]),
                        latestStatus=status,
                        lastObservedAt=r[4],
                        peakVibrationMms=round(float(r[5] or 0.0), 3),
                        peakStrainMicrostrain=round(float(r[6] or 0.0), 2),
                        resonantFrequencyHz=round(float(freq), 3),
                        resonantDriftPct=round(float(drift), 2),
                    )
                )
        else:
            # Fallback to configured study area structure assets
            for default_s in DEFAULT_STRUCTURES:
                summaries.append(
                    SHMStructureSummary(
                        structureId=default_s["structureId"],
                        structureName=default_s["structureName"],
                        totalSpans=len(default_s["spans"]),
                        sensorCount=default_s["sensorCount"],
                        latestStatus="NOMINAL",
                        lastObservedAt=datetime.now(timezone.utc).isoformat(),
                        peakVibrationMms=3.42,
                        peakStrainMicrostrain=520.5,
                        resonantFrequencyHz=default_s["baselineFreqHz"],
                        resonantDriftPct=-1.18,
                    )
                )

        return summaries

    async def get_structure_latest(
        self, session: AsyncSession, structure_id: str
    ) -> Optional[SHMTelemetryRecord]:
        """
        Retrieves the latest telemetry point for a specific structure.
        """
        query = text("""
            SELECT 
                id, structure_id, structure_name, span_id, sensor_id, observed_at,
                vibration_ppv_mms, strain_microstrain, resonant_freq_hz,
                resonant_baseline_hz, resonant_drift_pct, temperature_celsius,
                hcv_axle_load_tonnes, integrity_status, source_mode,
                quality_score, provenance_metadata
            FROM shm_telemetry
            WHERE structure_id = :structure_id
            ORDER BY observed_at DESC
            LIMIT 1
        """)
        res = await session.execute(query, {"structure_id": structure_id})
        r = res.fetchone()
        if not r:
            return None

        prov = {}
        if r[16]:
            try:
                prov = json.loads(r[16]) if isinstance(r[16], str) else r[16]
            except Exception:
                prov = {}

        return SHMTelemetryRecord(
            id=r[0],
            structureId=r[1],
            structureName=r[2],
            spanId=r[3],
            sensorId=r[4],
            observedAt=r[5] if isinstance(r[5], str) else r[5].isoformat(),
            vibrationPpvMms=float(r[6]),
            strainMicrostrain=float(r[7]),
            resonantFreqHz=float(r[8]),
            resonantBaselineHz=float(r[9]),
            resonantDriftPct=float(r[10]),
            temperatureCelsius=float(r[11]),
            hcvAxleLoadTonnes=float(r[12]) if r[12] is not None else None,
            integrityStatus=r[13],
            sourceMode=r[14],
            qualityScore=float(r[15]),
            provenanceMetadata=prov,
        )

    async def get_structure_status(
        self, session: AsyncSession, structure_id: str
    ) -> SHMStructureStatus:
        """
        Retrieves real-time operational status, active fatigue/overload flags,
        and threshold comparison metrics for a structure.
        """
        latest = await self.get_structure_latest(session, structure_id)
        if not latest:
            # Baseline nominal default response
            struct_info = next(
                (s for s in DEFAULT_STRUCTURES if s["structureId"] == structure_id),
                {
                    "structureId": structure_id,
                    "structureName": structure_id,
                    "baselineFreqHz": 4.25,
                    "spans": ["SPAN-01-EB"],
                },
            )
            return SHMStructureStatus(
                structureId=structure_id,
                structureName=struct_info["structureName"],
                spanId=struct_info["spans"][0],
                integrityStatus="NOMINAL",
                isFatigueAlert=False,
                isOverloadAlert=False,
                activeAlerts=[],
                currentMetrics={
                    "vibrationPpvMms": 2.85,
                    "strainMicrostrain": 480.0,
                    "resonantFreqHz": struct_info["baselineFreqHz"],
                    "resonantBaselineHz": struct_info["baselineFreqHz"],
                    "resonantDriftPct": 0.0,
                    "temperatureCelsius": 28.5,
                    "hcvAxleLoadTonnes": None,
                },
                safetyThresholds={
                    "maxPpvMms": SHM_PPV_MAX_MMS,
                    "yieldStrainMicrostrain": SHM_STRAIN_YIELD_ALERT,
                    "maxResonantDriftPct": SHM_RESONANT_DRIFT_THRESHOLD_PCT,
                    "maxAxleLoadTonnes": SHM_HCV_AXLE_LIMIT_TONNES,
                },
                lastUpdated=datetime.now(timezone.utc).isoformat(),
            )

        status, alerts = self.evaluate_integrity_status(
            strain_val=latest.strainMicrostrain,
            resonant_drift_pct=latest.resonantDriftPct,
            hcv_axle_load=latest.hcvAxleLoadTonnes,
            vibration_ppv=latest.vibrationPpvMms,
        )

        return SHMStructureStatus(
            structureId=latest.structureId,
            structureName=latest.structureName or latest.structureId,
            spanId=latest.spanId,
            integrityStatus=status,
            isFatigueAlert=(status == StructuralIntegrityStatus.ADVISORY_FATIGUE.value),
            isOverloadAlert=(status == StructuralIntegrityStatus.ALERT_OVERLOAD.value),
            activeAlerts=alerts,
            currentMetrics={
                "vibrationPpvMms": latest.vibrationPpvMms,
                "strainMicrostrain": latest.strainMicrostrain,
                "resonantFreqHz": latest.resonantFreqHz,
                "resonantBaselineHz": latest.resonantBaselineHz,
                "resonantDriftPct": latest.resonantDriftPct,
                "temperatureCelsius": latest.temperatureCelsius,
                "hcvAxleLoadTonnes": latest.hcvAxleLoadTonnes,
            },
            safetyThresholds={
                "maxPpvMms": SHM_PPV_MAX_MMS,
                "yieldStrainMicrostrain": SHM_STRAIN_YIELD_ALERT,
                "maxResonantDriftPct": SHM_RESONANT_DRIFT_THRESHOLD_PCT,
                "maxAxleLoadTonnes": SHM_HCV_AXLE_LIMIT_TONNES,
            },
            lastUpdated=latest.observedAt,
        )

    async def get_structure_history(
        self,
        session: AsyncSession,
        structure_id: str,
        limit: int = 50,
        hours: Optional[float] = None,
    ) -> List[SHMTelemetryRecord]:
        """
        Retrieves historical time-series points for a structure, optionally bounded by hours.
        Uses universal ISO-8601 parameter binding for dual-database compatibility.
        """
        if hours:
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=abs(hours))).isoformat()
            query = text("""
                SELECT 
                    id, structure_id, structure_name, span_id, sensor_id, observed_at,
                    vibration_ppv_mms, strain_microstrain, resonant_freq_hz,
                    resonant_baseline_hz, resonant_drift_pct, temperature_celsius,
                    hcv_axle_load_tonnes, integrity_status, source_mode,
                    quality_score, provenance_metadata
                FROM shm_telemetry
                WHERE structure_id = :structure_id AND observed_at >= :cutoff
                ORDER BY observed_at DESC
                LIMIT :limit
            """)
            params = {"structure_id": structure_id, "cutoff": cutoff, "limit": limit}
        else:
            query = text("""
                SELECT 
                    id, structure_id, structure_name, span_id, sensor_id, observed_at,
                    vibration_ppv_mms, strain_microstrain, resonant_freq_hz,
                    resonant_baseline_hz, resonant_drift_pct, temperature_celsius,
                    hcv_axle_load_tonnes, integrity_status, source_mode,
                    quality_score, provenance_metadata
                FROM shm_telemetry
                WHERE structure_id = :structure_id
                ORDER BY observed_at DESC
                LIMIT :limit
            """)
            params = {"structure_id": structure_id, "limit": limit}

        res = await session.execute(query, params)
        rows = res.fetchall()

        records: List[SHMTelemetryRecord] = []
        for r in rows:
            prov = {}
            if r[16]:
                try:
                    prov = json.loads(r[16]) if isinstance(r[16], str) else r[16]
                except Exception:
                    prov = {}
            records.append(
                SHMTelemetryRecord(
                    id=r[0],
                    structureId=r[1],
                    structureName=r[2],
                    spanId=r[3],
                    sensorId=r[4],
                    observedAt=r[5] if isinstance(r[5], str) else r[5].isoformat(),
                    vibrationPpvMms=float(r[6]),
                    strainMicrostrain=float(r[7]),
                    resonantFreqHz=float(r[8]),
                    resonantBaselineHz=float(r[9]),
                    resonantDriftPct=float(r[10]),
                    temperatureCelsius=float(r[11]),
                    hcvAxleLoadTonnes=float(r[12]) if r[12] is not None else None,
                    integrityStatus=r[13],
                    sourceMode=r[14],
                    qualityScore=float(r[15]),
                    provenanceMetadata=prov,
                )
            )

        return records


shm_service = SHMTelemetryService()

