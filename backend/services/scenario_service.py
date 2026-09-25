import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from simulation.runner import SUMOCorridorRunner
from simulation.kpi_calculator import ScenarioKPICalculator
from backend.core.constants import SourceMode
from backend.core.config import settings
from backend.schemas.recommendations import (
    AdvisoryRecommendation,
    AuditLogEntry,
    RecommendationDomain,
    RecommendationEvidence,
    RecommendationSeverity,
    RecommendationStatus,
)
from backend.services.rule_engine import rule_engine

# Pre-registered scenario templates approved per ADR-004
APPROVED_TEMPLATES = [
    {
        "id": "SCEN-BASE-01",
        "name": "Evening Peak Fixed-Time Baseline (Viman Nagar Chowk)",
        "description": "Calibrated 4-phase fixed-time control (120s cycle, 35s Nagar Rd EB green) under evening peak commuter demand (18:00–19:30).",
        "category": "MOBILITY_SIGNAL",
        "parametersSchema": {
            "demandMultiplier": {"type": "number", "minimum": 0.5, "maximum": 2.0, "default": 1.0},
            "randomSeed": {"type": "integer", "default": 42}
        },
        "defaultParameters": {
            "demandMultiplier": 1.0,
            "randomSeed": 42
        }
    },
    {
        "id": "SCEN-INT-01",
        "name": "Dynamic Green Split Re-allocation (Viman Nagar Chowk)",
        "description": "Dynamic green extension (+15s green, 50s total) for Nagar Road Eastbound approach during peak queue spillback. Cycle length maintained at 120s.",
        "category": "MOBILITY_SIGNAL",
        "parametersSchema": {
            "greenExtensionSec": {"type": "number", "minimum": 5.0, "maximum": 25.0, "default": 15.0},
            "demandMultiplier": {"type": "number", "minimum": 0.5, "maximum": 2.0, "default": 1.0},
            "randomSeed": {"type": "integer", "default": 42}
        },
        "defaultParameters": {
            "greenExtensionSec": 15.0,
            "demandMultiplier": 1.0,
            "randomSeed": 42
        }
    },
    {
        "id": "SCEN-INT-02",
        "name": "Arterial Two-Junction Progression (VN-01 <-> SN-01)",
        "description": "Progression offset optimization (35s green wave window) between Viman Nagar and Somnath Nagar Chowk to minimize mid-link arterial stops.",
        "category": "CORRIDOR_COORDINATION",
        "parametersSchema": {
            "coordinationOffsetSec": {"type": "number", "minimum": 10.0, "maximum": 60.0, "default": 35.0},
            "randomSeed": {"type": "integer", "default": 42}
        },
        "defaultParameters": {
            "coordinationOffsetSec": 35.0,
            "randomSeed": 42
        }
    }
]

# Thread-safe in-memory cache of scenario run results (persisted to DB when session available)
_RUNS_CACHE: Dict[str, Dict[str, Any]] = {}


class ScenarioService:
    """Service layer for scenario execution, comparison, and provenance isolation."""
    _RUNS_CACHE = _RUNS_CACHE

    def __init__(self):
        self.runner = SUMOCorridorRunner()

    def list_templates(self) -> List[Dict[str, Any]]:
        """Returns all approved simulation scenario templates."""
        return APPROVED_TEMPLATES

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Finds a template by ID."""
        for t in APPROVED_TEMPLATES:
            if t["id"] == template_id:
                return t
        return None

    def execute_comparative_run(
        self,
        intervention_template_id: str = "SCEN-INT-01",
        green_extension_sec: float = 15.0,
        coordination_offset_sec: float = 35.0,
        demand_multiplier: float = 1.0,
        random_seed: int = 42
    ) -> Dict[str, Any]:
        """
        Executes a paired baseline-versus-intervention simulation under identical seeds.
        Extracts KPIs and comparative deltas.
        """
        run_id = f"urn:ngsi-ld:ScenarioRun:PUNE:{uuid.uuid4().hex[:12].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Run Baseline (SCEN-BASE-01)
        base_result = self.runner.run_scenario(
            template_id="SCEN-BASE-01",
            seed=random_seed,
            parameters={"demand_multiplier": demand_multiplier}
        )

        # 2. Run Intervention
        int_params = {
            "green_extension_sec": green_extension_sec,
            "coordination_offset_sec": coordination_offset_sec,
            "demand_multiplier": demand_multiplier
        }
        int_result = self.runner.run_scenario(
            template_id=intervention_template_id,
            seed=random_seed,
            parameters=int_params
        )

        # 3. Calculate Comparative Deltas
        deltas = ScenarioKPICalculator.calculate_deltas(
            baseline_kpis=base_result["kpis"],
            intervention_kpis=int_result["kpis"]
        )

        # 4. Construct Immutable Run Record
        if intervention_template_id == "SCEN-INT-01":
            scenario_name = f"Signal Split Extension (+{green_extension_sec}s, Seed {random_seed})"
        elif intervention_template_id == "SCEN-INT-02":
            scenario_name = f"Arterial Coordination ({coordination_offset_sec}s offset, Seed {random_seed})"
        elif intervention_template_id == "SCEN-BASE-01":
            scenario_name = f"Evening Peak Fixed-Time Baseline (Seed {random_seed})"
        else:
            scenario_name = f"Corridor Simulation ({intervention_template_id}, Seed {random_seed})"

        record = {
            "runId": run_id,
            "templateId": intervention_template_id,
            "scenarioTemplateId": intervention_template_id,
            "name": scenario_name,
            "status": "COMPLETED",
            "sourceMode": "SIMULATION",
            "governanceNotice": "SIMULATION OUTPUT: Results are model-generated under experimental assumptions. Does not actuate physical traffic signals or guarantee real-world outcomes.",
            "randomSeed": random_seed,
            "networkVersion": "viman_nagar_v1.0",
            "demandVersion": "evening_peak_v1.0",
            "executedAt": now_iso,
            "parameters": {
                "greenExtensionSec": green_extension_sec,
                "coordinationOffsetSec": coordination_offset_sec,
                "demandMultiplier": demand_multiplier,
                "randomSeed": random_seed
            },
            "baseline": {
                "templateId": "SCEN-BASE-01",
                "kpis": base_result["kpis"]
            },
            "intervention": {
                "templateId": intervention_template_id,
                "kpis": int_result["kpis"]
            },
            "deltas": deltas
        }

        _RUNS_CACHE[run_id] = record
        self._persist_run_to_db(record)
        return record

    def propose_advisory_from_run(
        self,
        run_id: str,
        reviewer: str = "Municipal Analyst",
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Transforms a simulation run into a formal AdvisoryRecommendation.
        The advisory is added to the AdvisoryRuleEngine and logged in the audit_events table.
        Advisories remain non-actuating and require human authorization outside the platform.
        """
        run = self.get_run(run_id)
        if not run:
            raise KeyError(f"Scenario run '{run_id}' not found")

        now = datetime.now(timezone.utc)
        template_id = run["templateId"]
        deltas = run.get("deltas", {})
        delay_saved = deltas.get("delay_saved_sec", 0.0)
        delay_pct = deltas.get("delay_delta_pct", 0.0)
        target_entity = (
            "urn:ngsi-ld:Intersection:PUNE:INT-VN-01"
            if template_id == "SCEN-INT-01"
            else "urn:ngsi-ld:RoadSegment:PUNE:SEG-NR-EB-01"
        )

        rec_id = f"REC-SCEN-{uuid.uuid4().hex[:8].upper()}"
        severity = RecommendationSeverity.WARNING if delay_saved >= 10.0 else RecommendationSeverity.INFO
        title = (
            f"Simulated Dynamic Green Extension Proposed for Nagar Rd EB"
            if template_id == "SCEN-INT-01"
            else f"Simulated Arterial Progression Coordination Proposed (VN-01 ↔ SN-01)"
        )
        description = (
            f"Scenario run {run_id} simulated a {delay_pct}% delay reduction ({delay_saved}s saved per vehicle) "
            f"using template {template_id}. Seed: {run['randomSeed']}."
        )
        suggested_action = (
            f"Review proposed timing parameters ({run['parameters']}) in Scenario Studio before municipal dispatch."
        )

        rec = AdvisoryRecommendation(
            recommendationId=rec_id,
            domain=RecommendationDomain.TRAFFIC,
            severity=severity,
            status=RecommendationStatus.ACTIVE,
            targetEntityId=target_entity,
            title=title,
            description=description,
            triggerRule=f"RULE-SIMULATION-{template_id}",
            evidence=RecommendationEvidence(
                sourceMode=SourceMode.SIMULATION,
                metricName="averageDelaySec",
                observedOrPredictedValue=float(run["intervention"]["kpis"]["average_delay_sec"]),
                threshold=float(run["baseline"]["kpis"]["average_delay_sec"]),
                unit="seconds",
                scenarioId=template_id,
                confidenceScore=0.95,
                timestamp=now
            ),
            suggestedAction=suggested_action,
            humanApprovalRequired=True,
            governanceNotice="SIMULATION ADVISORY: Synthesized from microscopic traffic simulation. Physical traffic signals are NOT actuated; requires human authorization before field deployment.",
            auditTrail=[
                AuditLogEntry(
                    timestamp=now,
                    previousStatus=RecommendationStatus.ACTIVE,
                    newStatus=RecommendationStatus.ACTIVE,
                    reviewer=reviewer,
                    notes=notes or f"Proposed advisory synthesized from scenario run {run_id}."
                )
            ],
            createdAt=now,
            updatedAt=now
        )

        # Register into rule engine
        rule_engine.add_custom_recommendation(rec)

        # Record audit event
        self._record_audit_event(
            event_type="ADVISORY_PROPOSED_FROM_SIMULATION",
            source_service="ScenarioStudio",
            details={
                "runId": run_id,
                "recommendationId": rec_id,
                "templateId": template_id,
                "reviewer": reviewer,
                "notes": notes,
                "deltas": deltas,
                "timestamp": now.isoformat()
            }
        )

        return rec.model_dump()

    def _record_audit_event(self, event_type: str, source_service: str, details: Dict[str, Any]) -> None:
        """Best-effort persistence of audit event to database without failing request."""
        try:
            db_path = settings.resolved_sqlite_path
            if db_path.exists():
                with sqlite3.connect(str(db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO audit_events (emitted_at, event_type, source_service, details) VALUES (?, ?, ?, ?)",
                        (datetime.now(timezone.utc).isoformat(), event_type, source_service, json.dumps(details))
                    )
                    conn.commit()
        except Exception:
            pass

    def _persist_run_to_db(self, record: Dict[str, Any]) -> None:
        """Best-effort persistence of scenario run and KPIs to SQLite database."""
        try:
            db_path = settings.resolved_sqlite_path
            if db_path.exists():
                with sqlite3.connect(str(db_path)) as conn:
                    cursor = conn.cursor()
                    # 1. Insert into scenario_runs
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO scenario_runs (
                            id, template_id, name, status, source_mode,
                            network_version, demand_version, random_seed, parameters,
                            started_at, completed_at, artifact_paths
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record["runId"],
                            record["templateId"],
                            record["name"],
                            record["status"],
                            record["sourceMode"],
                            record["networkVersion"],
                            record["demandVersion"],
                            record["randomSeed"],
                            json.dumps(record["parameters"]),
                            record["executedAt"],
                            record["executedAt"],
                            json.dumps({
                                "baseline": record["baseline"],
                                "intervention": record["intervention"],
                                "deltas": record["deltas"],
                                "governanceNotice": record["governanceNotice"]
                            })
                        )
                    )
                    # 2. Insert into scenario_kpis (baseline & intervention)
                    base_kpis = record["baseline"]["kpis"]
                    cursor.execute(
                        """
                        INSERT INTO scenario_kpis (
                            scenario_run_id, is_baseline, average_travel_time_sec,
                            average_delay_sec, p95_queue_length_meters, throughput_veh_per_hour,
                            delta_vs_baseline
                        ) VALUES (?, 1, ?, ?, ?, ?, '{}')
                        """,
                        (
                            record["runId"],
                            base_kpis.get("average_travel_time_sec"),
                            base_kpis.get("average_delay_sec"),
                            base_kpis.get("p95_queue_length_meters"),
                            base_kpis.get("throughput_veh_per_hour")
                        )
                    )
                    int_kpis = record["intervention"]["kpis"]
                    cursor.execute(
                        """
                        INSERT INTO scenario_kpis (
                            scenario_run_id, is_baseline, average_travel_time_sec,
                            average_delay_sec, p95_queue_length_meters, throughput_veh_per_hour,
                            delta_vs_baseline
                        ) VALUES (?, 0, ?, ?, ?, ?, ?)
                        """,
                        (
                            record["runId"],
                            int_kpis.get("average_travel_time_sec"),
                            int_kpis.get("average_delay_sec"),
                            int_kpis.get("p95_queue_length_meters"),
                            int_kpis.get("throughput_veh_per_hour"),
                            json.dumps(record["deltas"])
                        )
                    )
                    conn.commit()
        except Exception:
            pass

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a past scenario run by ID from cache or persistent storage."""
        if run_id in _RUNS_CACHE:
            return _RUNS_CACHE[run_id]

        try:
            db_path = settings.resolved_sqlite_path
            if db_path.exists():
                with sqlite3.connect(str(db_path)) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM scenario_runs WHERE id = ?", (run_id,))
                    row = cursor.fetchone()
                    if row:
                        artifacts = json.loads(row["artifact_paths"] or "{}")
                        rec = {
                            "runId": row["id"],
                            "templateId": row["template_id"],
                            "scenarioTemplateId": row["template_id"],
                            "name": row["name"],
                            "status": row["status"],
                            "sourceMode": row["source_mode"],
                            "governanceNotice": artifacts.get("governanceNotice", "SIMULATION OUTPUT: Results are model-generated under experimental assumptions."),
                            "randomSeed": row["random_seed"],
                            "networkVersion": row["network_version"],
                            "demandVersion": row["demand_version"],
                            "executedAt": row["completed_at"] or row["created_at"],
                            "parameters": json.loads(row["parameters"] or "{}"),
                            "baseline": artifacts.get("baseline", {}),
                            "intervention": artifacts.get("intervention", {}),
                            "deltas": artifacts.get("deltas", {})
                        }
                        _RUNS_CACHE[run_id] = rec
                        return rec
        except Exception:
            pass
        return None

    def list_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns recent scenario runs from cache and persistent storage."""
        try:
            db_path = settings.resolved_sqlite_path
            if db_path.exists():
                with sqlite3.connect(str(db_path)) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id FROM scenario_runs ORDER BY created_at DESC LIMIT ?",
                        (limit,)
                    )
                    rows = cursor.fetchall()
                    for r in rows:
                        run_id = r["id"]
                        if run_id not in _RUNS_CACHE:
                            self.get_run(run_id)
        except Exception:
            pass

        runs = list(_RUNS_CACHE.values())
        return sorted(runs, key=lambda x: x["executedAt"], reverse=True)[:limit]


# Global singleton scenario service instance
scenario_service = ScenarioService()

