"""
scenarios.py

API router endpoints for scenario templates, execution, and comparative KPI analysis.
All endpoints strictly tag outputs with SIMULATION provenance and never mutate authoritative current state.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query

try:
    from services.scenario_service import ScenarioService
    from schemas.scenarios import (
        ScenarioTemplateResponse,
        RunScenarioRequest,
        ScenarioRunResponse,
    )
except ImportError:
    from backend.services.scenario_service import ScenarioService
    from backend.schemas.scenarios import (
        ScenarioTemplateResponse,
        RunScenarioRequest,
        ScenarioRunResponse,
    )

router = APIRouter(prefix="/scenarios", tags=["Scenarios & Simulation"])
service = ScenarioService()


@router.get("/templates", response_model=List[ScenarioTemplateResponse])
def get_scenario_templates():
    """Returns all pre-approved simulation scenario templates."""
    return service.list_templates()


@router.post("/run", response_model=ScenarioRunResponse)
def run_scenario(request: RunScenarioRequest):
    """
    Executes a controlled comparative simulation run (baseline vs. intervention)
    under an identical random seed.
    Outputs are labeled SIMULATION and persisted separately from observed twin state.
    """
    try:
        run_record = service.execute_comparative_run(
            intervention_template_id=request.templateId,
            green_extension_sec=request.greenExtensionSec,
            demand_multiplier=request.demandMultiplier,
            random_seed=request.randomSeed
        )
        return run_record
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation execution failed: {str(e)}")


@router.get("/runs", response_model=List[ScenarioRunResponse])
def list_runs(limit: int = Query(10, ge=1, le=50)):
    """Lists recent scenario simulation runs."""
    return service.list_recent_runs(limit=limit)


@router.get("/runs/{run_id}", response_model=ScenarioRunResponse)
def get_run_details(run_id: str):
    """Retrieves metadata and KPIs for a specific scenario run."""
    record = service.get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Scenario run '{run_id}' not found")
    return record


@router.get("/runs/{run_id}/compare")
def compare_run_kpis(run_id: str):
    """Returns side-by-side KPI comparison with delta metrics for a run."""
    record = service.get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Scenario run '{run_id}' not found")
    return {
        "runId": record["runId"],
        "sourceMode": record["sourceMode"],
        "governanceNotice": record["governanceNotice"],
        "baseline": record["baseline"],
        "intervention": record["intervention"],
        "deltas": record["deltas"]
    }
