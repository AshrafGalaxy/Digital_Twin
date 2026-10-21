"""
recommendations.py

REST API endpoints for Advisory Decision Support, Cryptographic Dispatch Authorization,
and Governance Review Workflow (D-10, TASK-10).
"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db_session
from backend.schemas.recommendations import (
    AdvisoryAuditLogRecord,
    AdvisoryRecommendation,
    AdvisorySummary,
    AuthorizeAdvisoryRequest,
    DispatchWorkOrder,
    RecommendationDomain,
    RecommendationStatus,
    ReviewRecommendationRequest
)
from backend.services.rule_engine import rule_engine

logger = logging.getLogger(__name__)

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


@router.get("/audit/logs", response_model=List[AdvisoryAuditLogRecord])
async def list_advisory_audit_logs(
    limit: int = Query(50, ge=1, le=200, description="Max audit log entries to return"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Returns persistent audit records from advisory_audit_log table in reverse chronological order.
    """
    try:
        res = await session.execute(
            text("""
                SELECT id, audit_id, recommendation_id, target_entity_id, action_type,
                       previous_status, new_status, authorized_by, badge_id, shift_id,
                       justification_notes, dispatch_order_id, dispatch_payload_json,
                       tamper_evident_hash, created_at
                FROM advisory_audit_log
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"limit": limit}
        )
        rows = res.fetchall()
        records = []
        for r in rows:
            payload = r[12]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {}
            elif not isinstance(payload, dict):
                payload = {}

            created_val = r[14]
            if isinstance(created_val, str):
                try:
                    created_dt = datetime.fromisoformat(created_val)
                except Exception:
                    created_dt = datetime.utcnow()
            elif isinstance(created_val, datetime):
                created_dt = created_val
            else:
                created_dt = datetime.utcnow()

            records.append(
                AdvisoryAuditLogRecord(
                    id=r[0],
                    auditId=r[1],
                    recommendationId=r[2],
                    targetEntityId=r[3],
                    actionType=r[4],
                    previousStatus=r[5],
                    newStatus=r[6],
                    authorizedBy=r[7],
                    badgeId=r[8],
                    shiftId=r[9],
                    justificationNotes=r[10],
                    dispatchOrderId=r[11],
                    dispatchPayloadJson=payload,
                    tamperEvidentHash=r[13],
                    createdAt=created_dt
                )
            )
        return records
    except Exception as e:
        logger.warning(f"Could not query advisory_audit_log table: {e}")
        return []


@router.post("/evaluate", response_model=List[AdvisoryRecommendation])
async def trigger_rule_evaluation():
    """
    Triggers an immediate re-evaluation of corridor state and active XGBoost forecasts
    against deterministic rules to refresh recommendations.
    """
    return rule_engine.evaluate_rules()


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


@router.post("/{rec_id}/authorize", response_model=DispatchWorkOrder)
async def authorize_advisory(
    rec_id: str,
    request: AuthorizeAdvisoryRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Authorizes an advisory recommendation by generating an official Municipal Dispatch Order (MDO),
    computing a cryptographic SHA-256 tamper-evident hash, and persisting an immutable audit record.
    Strict non-actuation invariant is preserved: recommendations remain advisory.
    """
    result = rule_engine.authorize_advisory(rec_id, request)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Advisory recommendation '{rec_id}' not found."
        )
    updated_rec, dispatch_order = result

    # Persist immutable audit record to advisory_audit_log table
    try:
        audit_id = f"AUD-{uuid.uuid4().hex[:12].upper()}"
        payload_dict = {
            "dispatchOrderId": dispatch_order.dispatchOrderId,
            "recommendationId": dispatch_order.recommendationId,
            "targetEntityId": dispatch_order.targetEntityId,
            "proposedChange": dispatch_order.proposedChange.model_dump() if dispatch_order.proposedChange else None,
            "predictedImpact": dispatch_order.predictedImpact.model_dump() if dispatch_order.predictedImpact else None,
            "safetyChecklist": dispatch_order.safetyChecklist.model_dump() if dispatch_order.safetyChecklist else None,
            "authorizedBy": dispatch_order.authorizedBy,
            "badgeId": dispatch_order.badgeId,
            "shiftId": dispatch_order.shiftId,
            "issuedAt": dispatch_order.issuedAt.isoformat(),
            "notes": dispatch_order.notes
        }
        await session.execute(
            text("""
                INSERT INTO advisory_audit_log (
                    audit_id, recommendation_id, target_entity_id, action_type,
                    previous_status, new_status, authorized_by, badge_id, shift_id,
                    justification_notes, dispatch_order_id, dispatch_payload_json,
                    tamper_evident_hash
                ) VALUES (
                    :audit_id, :recommendation_id, :target_entity_id, :action_type,
                    :previous_status, :new_status, :authorized_by, :badge_id, :shift_id,
                    :justification_notes, :dispatch_order_id, :dispatch_payload_json,
                    :tamper_evident_hash
                )
            """),
            {
                "audit_id": audit_id,
                "recommendation_id": rec_id,
                "target_entity_id": updated_rec.targetEntityId,
                "action_type": "MUNICIPAL_DISPATCH_AUTHORIZATION",
                "previous_status": "ACTIVE",
                "new_status": request.decision.value if hasattr(request.decision, "value") else str(request.decision),
                "authorized_by": request.reviewer,
                "badge_id": request.badgeId,
                "shift_id": request.shiftId,
                "justification_notes": request.notes or "",
                "dispatch_order_id": dispatch_order.dispatchOrderId,
                "dispatch_payload_json": json.dumps(payload_dict),
                "tamper_evident_hash": dispatch_order.tamperEvidentHash
            }
        )
        await session.commit()
    except Exception as e:
        logger.error(f"Failed to persist advisory_audit_log to database: {e}")

    return dispatch_order


@router.get("/{rec_id}/dispatch-order", response_model=DispatchWorkOrder)
async def get_dispatch_order(rec_id: str):
    """
    Retrieves the generated Municipal Dispatch Work Order for a specific recommendation.
    """
    order = rule_engine.get_dispatch_order(rec_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No municipal dispatch order found for advisory '{rec_id}'."
        )
    return order
