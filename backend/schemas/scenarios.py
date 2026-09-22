"""
scenarios.py

Pydantic schemas for simulation scenarios, run requests, and KPI comparison.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScenarioTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    parametersSchema: Dict[str, Any]
    defaultParameters: Dict[str, Any]


class RunScenarioRequest(BaseModel):
    templateId: str = Field("SCEN-INT-01", description="Intervention template ID to test")
    greenExtensionSec: float = Field(15.0, ge=5.0, le=25.0, description="Green time extension for Nagar Rd EB (seconds)")
    coordinationOffsetSec: Optional[float] = Field(35.0, ge=10.0, le=60.0, description="Progression offset for VN-01 <-> SN-01 (seconds)")
    demandMultiplier: float = Field(1.0, ge=0.5, le=2.0, description="Corridor traffic demand scaling factor")
    randomSeed: int = Field(42, description="Simulation random seed for reproducibility")


class ProposeAdvisoryRequest(BaseModel):
    reviewer: str = Field("Municipal Analyst", description="Name or role of reviewer proposing the intervention")
    notes: Optional[str] = Field("", description="Justification and context for the proposed advisory")


class ScenarioKPIs(BaseModel):
    average_travel_time_sec: float
    average_delay_sec: float
    p95_queue_length_meters: float
    throughput_veh_per_hour: float


class ScenarioRunResponse(BaseModel):
    runId: str
    templateId: str
    name: str
    status: str
    sourceMode: str = "SIMULATION"
    governanceNotice: str
    randomSeed: int
    networkVersion: str
    demandVersion: str
    executedAt: str
    parameters: Dict[str, Any]
    baseline: Dict[str, Any]
    intervention: Dict[str, Any]
    deltas: Dict[str, Any]
