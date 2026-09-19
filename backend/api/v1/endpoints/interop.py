"""
interop.py

Smart City Interoperability Endpoints providing NGSI-LD 1.3 / FIWARE Orion-LD
compliant entity exports and JSON-LD context documents (Phase 8, D-14).
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query

from backend.services.fiware_adapter import FIWAREOrionLDAdapter

router = APIRouter(prefix="/interop", tags=["Smart City Interoperability & FIWARE"])


@router.get("/ngsi-ld/context", response_model=Dict[str, Any])
def get_ngsi_ld_context():
    """Returns standard NGSI-LD @context definition for smart city twin data models."""
    return FIWAREOrionLDAdapter.get_core_context()


@router.get("/ngsi-ld/entities", response_model=List[Dict[str, Any]])
def get_ngsi_ld_entities(
    entity_type: Optional[str] = Query(None, alias="type", description="Optional entity type filter (e.g. RoadIntersection, RoadSegment, Building)")
):
    """
    Returns registered digital twin entities formatted as standard NGSI-LD Context Information payloads.
    Directly compatible with FIWARE Orion-LD and ETSI GS CIM 009 context brokers.
    """
    return FIWAREOrionLDAdapter.export_all_entities(entity_type=entity_type)
