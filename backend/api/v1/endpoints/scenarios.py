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
        ProposeAdvisoryRequest,
    )
except ImportError:
    from backend.services.scenario_service import ScenarioService
    from backend.schemas.scenarios import (
        ScenarioTemplateResponse,
        RunScenarioRequest,
        ScenarioRunResponse,
        ProposeAdvisoryRequest,
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
            coordination_offset_sec=request.coordinationOffsetSec if request.coordinationOffsetSec is not None else 35.0,
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


@router.post("/runs/{run_id}/propose-advisory")
def propose_advisory(run_id: str, request: ProposeAdvisoryRequest = ProposeAdvisoryRequest()):
    """
    Transforms a positive simulation run into a formal AdvisoryRecommendation.
    Advisory requires human authorization outside the platform and produces audit logs.
    """
    try:
        advisory = service.propose_advisory_from_run(
            run_id=run_id,
            reviewer=request.reviewer,
            notes=request.notes or ""
        )
        return advisory
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Scenario run '{run_id}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to propose advisory: {str(e)}")
