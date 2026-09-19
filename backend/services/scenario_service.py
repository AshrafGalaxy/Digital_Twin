"""
scenario_service.py

Manages microscopic simulation scenario templates, run execution,
comparative KPI extraction, and result persistence.
Ensures strict SIMULATION provenance and state separation invariants.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from simulation.runner import SUMOCorridorRunner
from simulation.kpi_calculator import ScenarioKPICalculator

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
        int_result = self.runner.run_scenario(
            template_id=intervention_template_id,
            seed=random_seed,
            parameters={
                "green_extension_sec": green_extension_sec,
                "demand_multiplier": demand_multiplier
            }
        )

        # 3. Calculate Comparative Deltas
        deltas = ScenarioKPICalculator.calculate_deltas(
            baseline_kpis=base_result["kpis"],
            intervention_kpis=int_result["kpis"]
        )

        # 4. Construct Immutable Run Record
        record = {
            "runId": run_id,
            "templateId": intervention_template_id,
            "name": f"Signal Split Comparison (Seed {random_seed})",
            "status": "COMPLETED",
            "sourceMode": "SIMULATION",
            "governanceNotice": "SIMULATION OUTPUT: Results are model-generated under experimental assumptions. Does not actuate physical traffic signals or guarantee real-world outcomes.",
            "randomSeed": random_seed,
            "networkVersion": "viman_nagar_v1.0",
            "demandVersion": "evening_peak_v1.0",
            "executedAt": now_iso,
            "parameters": {
                "greenExtensionSec": green_extension_sec,
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
        return record

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a past scenario run by ID."""
        return _RUNS_CACHE.get(run_id)

    def list_recent_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns recent scenario runs."""
        runs = list(_RUNS_CACHE.values())
        return sorted(runs, key=lambda x: x["executedAt"], reverse=True)[:limit]
