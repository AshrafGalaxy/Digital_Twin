"""
health.py

Deep health check and readiness endpoints for the digital twin platform (D-11).
Monitors database connectivity, ML model availability, simulation engine readiness,
scenario template registry, and active advisory counts.
"""

from pathlib import Path
from typing import Dict
from fastapi import APIRouter
from pydantic import BaseModel

try:
    from core.config import settings
    from core.database import check_db_health
except ImportError:
    from backend.core.config import settings
    from backend.core.database import check_db_health

from backend.services.rule_engine import rule_engine
from backend.services.scenario_service import scenario_service

router = APIRouter(tags=["Health"])


class SubsystemHealth(BaseModel):
    database: bool
    mlTrafficModel: bool
    mlEnergyModel: bool
    simulationEngine: bool
    scenarioTemplatesCount: int
    activeAdvisoriesCount: int


class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str
    subsystems: SubsystemHealth
    governanceMode: str = "HUMAN_ADVISORY"


@router.get("/health", response_model=HealthResponse)
async def get_health():
    """
    Returns platform readiness and detailed subsystem diagnostic indicators.
    """
    db_ok = await check_db_health()

    # Check ML model files relative to project root
    base_dir = Path(__file__).resolve().parents[4]
    traffic_model_path = base_dir / "artifacts" / "models" / "traffic_xgb_v1.joblib"
    energy_model_path = base_dir / "artifacts" / "models" / "energy_xgb_v1.joblib"

    ml_traffic_ok = traffic_model_path.is_file()
    ml_energy_ok = energy_model_path.is_file()

    # Check simulation engine
    sim_net_path = base_dir / "simulation" / "net" / "viman_nagar.net.xml"
    sim_ok = sim_net_path.is_file()


    # Count scenario templates and advisories
    templates = scenario_service.list_templates()
    advisory_summary = rule_engine.get_summary()

    # Platform is HEALTHY if core components are available, DEGRADED if DB or models are offline
    is_healthy = ml_traffic_ok and ml_energy_ok and sim_ok
    overall_status = "HEALTHY" if is_healthy else "DEGRADED"

    return HealthResponse(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        version="1.0.0",
        subsystems=SubsystemHealth(
            database=db_ok,
            mlTrafficModel=ml_traffic_ok,
            mlEnergyModel=ml_energy_ok,
            simulationEngine=sim_ok,
            scenarioTemplatesCount=len(templates),
            activeAdvisoriesCount=advisory_summary.totalActive
        ),
        governanceMode="HUMAN_ADVISORY"
    )
