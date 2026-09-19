"""
recommendations.py

REST API endpoints for Advisory Decision Support and Governance Review Workflow (D-10).
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from backend.schemas.recommendations import (
    AdvisoryRecommendation,
    AdvisorySummary,
    RecommendationDomain,
    RecommendationStatus,
    ReviewRecommendationRequest
)
from backend.services.rule_engine import rule_engine

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("", response_model=List[AdvisoryRecommendation])
async def list_recommendations(
    domain: Optional[RecommendationDomain] = Query(None, description="Filter by domain: TRAFFIC, ENERGY, ENVIRONMENT"),
    status: Optional[RecommendationStatus] = Query(None, description="Filter by review status: ACTIVE, UNDER_REVIEW, ACKNOWLEDGED, DISMISSED")
):
    """
    Lists all advisory recommendations with optional domain and review status filters.
    """
    return rule_engine.list_recommendations(domain=domain, status=status)


@router.get("/summary", response_model=AdvisorySummary)
async def get_advisory_summary():
    """
    Returns aggregated metrics on active recommendations by domain and severity.
    """
    return rule_engine.get_summary()


@router.get("/{rec_id}", response_model=AdvisoryRecommendation)
async def get_recommendation_detail(rec_id: str):
    """
    Retrieves a single advisory recommendation with complete evidence and audit history.
    """
    rec = rule_engine.get_recommendation(rec_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Advisory recommendation '{rec_id}' not found."
        )
    return rec


@router.post("/{rec_id}/review", response_model=AdvisoryRecommendation)
async def review_recommendation(rec_id: str, request: ReviewRecommendationRequest):
    """
    Executes a human governance review transition (UNDER_REVIEW, ACKNOWLEDGED, DISMISSED)
    with reviewer name and justification notes, recording a permanent audit trail entry.
    """
    updated_rec = rule_engine.review_recommendation(
        rec_id=rec_id,
        new_status=request.newStatus,
        reviewer=request.reviewer,
        notes=request.notes
    )
    if not updated_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Advisory recommendation '{rec_id}' not found."
        )
    return updated_rec


@router.post("/evaluate", response_model=List[AdvisoryRecommendation])
async def trigger_rule_evaluation():
    """
    Triggers an immediate re-evaluation of corridor state and active XGBoost forecasts
    against deterministic rules to refresh recommendations.
    """
    return rule_engine.evaluate_rules()
