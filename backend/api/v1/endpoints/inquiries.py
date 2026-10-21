"""
inquiries.py

Intake endpoint for municipal, enterprise, and research digital twin
access requests and pilot provisioning inquiries.
Supports full admin review, approval, role assignment, and magic access token issuance.
"""

from datetime import datetime, timezone, timedelta
import uuid
import secrets
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter()


class AccessInquiryRequest(BaseModel):
    organization: str = Field(..., min_length=2, max_length=200, description="Agency, municipality, or company name")
    work_email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Official business or government email address")
    contact_name: str = Field(..., min_length=2, max_length=120, description="Full name and title of representative")
    jurisdiction: str = Field(..., min_length=2, max_length=150, description="City, municipality, campus, or corridor")
    domain: str = Field(default="Integrated Multi-Domain Digital Twin", max_length=100, description="Primary domain of interest")
    infrastructure_scale: Optional[str] = Field(default="1-10 Intersections / Corridors", max_length=100)
    message: Optional[str] = Field(default="", max_length=2000, description="Deployment timeline and telemetry requirements")


class AccessInquiryResponse(BaseModel):
    inquiry_id: str
    status: str
    received_at: str
    message: str


class AccessInquiryRecord(BaseModel):
    id: str
    organization: str
    work_email: str
    contact_name: str
    jurisdiction: str
    domain: str
    infrastructure_scale: Optional[str] = None
    message: Optional[str] = None
    status: str
    assigned_role: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: str


class ApproveInquiryRequest(BaseModel):
    assigned_role: str = Field(default="Municipal Analyst", description="Authorized municipal role")
    expiry_days: int = Field(default=7, ge=1, le=90, description="Validity period in days")
    reviewer_notes: Optional[str] = Field(default=None, max_length=500)


class ApproveInquiryResponse(BaseModel):
    inquiry_id: str
    status: str
    assigned_role: str
    magic_token: str
    magic_link: str
    expires_at: str
    email_payload: Dict[str, str]


class RejectInquiryRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=3, max_length=500, description="Reason for inquiry rejection")


@router.post(
    "/request-access",
    response_model=AccessInquiryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an agency access or pilot provisioning inquiry",
)
async def submit_access_inquiry(
    payload: AccessInquiryRequest,
    session: AsyncSession = Depends(get_db_session)
) -> AccessInquiryResponse:
    inquiry_id = f"INQ-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:6].upper()}"
    received_at = datetime.now(timezone.utc).isoformat()

    stmt = text("""
        INSERT INTO access_inquiries (
            id, organization, work_email, contact_name, jurisdiction,
            domain, infrastructure_scale, message, status, assigned_role
        ) VALUES (
            :id, :organization, :work_email, :contact_name, :jurisdiction,
            :domain, :infrastructure_scale, :message, 'PENDING', 'Municipal Analyst'
        )
    """)
    await session.execute(stmt, {
        "id": inquiry_id,
        "organization": payload.organization.strip(),
        "work_email": payload.work_email.strip().lower(),
        "contact_name": payload.contact_name.strip(),
        "jurisdiction": payload.jurisdiction.strip(),
        "domain": payload.domain.strip(),
        "infrastructure_scale": (payload.infrastructure_scale or "").strip(),
        "message": (payload.message or "").strip()
    })
    await session.commit()

    logger.info(
        "Persisted access inquiry %s from %s (%s) for jurisdiction %s [Domain: %s]",
        inquiry_id,
        payload.contact_name,
        payload.organization,
        payload.jurisdiction,
        payload.domain,
    )

    return AccessInquiryResponse(
        inquiry_id=inquiry_id,
        status="received",
        received_at=received_at,
        message="Inquiry recorded successfully. Provisioning evaluation is underway.",
    )


@router.get(
    "",
    response_model=List[AccessInquiryRecord],
    summary="List all provisioning access inquiries for administrator review",
)
async def list_access_inquiries(
    status_filter: Optional[str] = Query(None, description="Filter by status: PENDING, APPROVED, REJECTED"),
    session: AsyncSession = Depends(get_db_session)
) -> List[AccessInquiryRecord]:
    if status_filter:
        query = text("""
            SELECT id, organization, work_email, contact_name, jurisdiction,
                   domain, infrastructure_scale, message, status, assigned_role,
                   reviewed_by, reviewed_at, rejection_reason, created_at
            FROM access_inquiries
            WHERE status = :status
            ORDER BY created_at DESC
        """)
        res = await session.execute(query, {"status": status_filter.upper()})
    else:
        query = text("""
            SELECT id, organization, work_email, contact_name, jurisdiction,
                   domain, infrastructure_scale, message, status, assigned_role,
                   reviewed_by, reviewed_at, rejection_reason, created_at
            FROM access_inquiries
            ORDER BY created_at DESC
        """)
        res = await session.execute(query)

    rows = res.mappings().all()
    records = []
    for r in rows:
        records.append(AccessInquiryRecord(
            id=r["id"],
            organization=r["organization"],
            work_email=r["work_email"],
            contact_name=r["contact_name"],
            jurisdiction=r["jurisdiction"],
            domain=r["domain"],
            infrastructure_scale=r["infrastructure_scale"],
            message=r["message"],
            status=r["status"],
            assigned_role=r["assigned_role"],
            reviewed_by=r["reviewed_by"],
            reviewed_at=str(r["reviewed_at"]) if r["reviewed_at"] else None,
            rejection_reason=r["rejection_reason"],
            created_at=str(r["created_at"]) if r["created_at"] else datetime.now(timezone.utc).isoformat()
        ))
    return records


@router.post(
    "/{inquiry_id}/approve",
    response_model=ApproveInquiryResponse,
    summary="Approve provisioning inquiry and issue cryptographic single-use magic link",
)
async def approve_access_inquiry(
    inquiry_id: str,
    payload: ApproveInquiryRequest,
    session: AsyncSession = Depends(get_db_session)
) -> ApproveInquiryResponse:
    # 1. Fetch inquiry
    res = await session.execute(
        text("SELECT * FROM access_inquiries WHERE id = :id"),
        {"id": inquiry_id}
    )
    inquiry = res.mappings().first()
    if not inquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found.")

    if inquiry["status"] == "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inquiry is already approved."
        )

    # 2. Generate secure token & expiry
    magic_token = secrets.token_urlsafe(32)
    now_utc = datetime.now(timezone.utc)
    expires_at_dt = now_utc + timedelta(days=payload.expiry_days)
    expires_at_iso = expires_at_dt.isoformat()

    # 3. Store magic token
    token_stmt = text("""
        INSERT INTO magic_access_tokens (
            token, inquiry_id, email, contact_name, assigned_role, department, status, expires_at
        ) VALUES (
            :token, :inquiry_id, :email, :contact_name, :assigned_role, :department, 'ACTIVE', :expires_at
        )
    """)
    await session.execute(token_stmt, {
        "token": magic_token,
        "inquiry_id": inquiry_id,
        "email": inquiry["work_email"],
        "contact_name": inquiry["contact_name"],
        "assigned_role": payload.assigned_role,
        "department": inquiry["organization"],
        "expires_at": expires_at_dt
    })

    # 4. Update inquiry record
    update_stmt = text("""
        UPDATE access_inquiries
        SET status = 'APPROVED',
            assigned_role = :role,
            reviewed_by = 'Platform Administrator',
            reviewed_at = :reviewed_at
        WHERE id = :id
    """)
    await session.execute(update_stmt, {
        "role": payload.assigned_role,
        "reviewed_at": now_utc,
        "id": inquiry_id
    })
    await session.commit()

    magic_link = f"/#access-token={magic_token}"
    email_subject = f"Your Access to the Digital Twin Platform has been Approved [{inquiry_id}]"
    email_body = f"""Dear {inquiry['contact_name']},

Your request for platform provisioning and operational access to the City Operations Center Digital Twin platform has been approved.

Provisioning Details:
- Organization: {inquiry['organization']}
- Jurisdiction: {inquiry['jurisdiction']}
- Authorized Role: {payload.assigned_role}
- Token Validity: {payload.expiry_days} Days (Expires: {expires_at_iso[:10]})

To access the platform, click your personalized single-use access link below:
{magic_link}

This cryptographic link is restricted to your authorized account and will establish an active session. Do not share or forward this token outside your agency.

City Operations Center Platform Administration
"""

    return ApproveInquiryResponse(
        inquiry_id=inquiry_id,
        status="APPROVED",
        assigned_role=payload.assigned_role,
        magic_token=magic_token,
        magic_link=magic_link,
        expires_at=expires_at_iso,
        email_payload={
            "to": inquiry["work_email"],
            "subject": email_subject,
            "body": email_body
        }
    )


@router.post(
    "/{inquiry_id}/reject",
    status_code=status.HTTP_200_OK,
    summary="Reject provisioning access inquiry",
)
async def reject_access_inquiry(
    inquiry_id: str,
    payload: RejectInquiryRequest,
    session: AsyncSession = Depends(get_db_session)
):
    res = await session.execute(
        text("SELECT * FROM access_inquiries WHERE id = :id"),
        {"id": inquiry_id}
    )
    inquiry = res.mappings().first()
    if not inquiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found.")

    update_stmt = text("""
        UPDATE access_inquiries
        SET status = 'REJECTED',
            rejection_reason = :reason,
            reviewed_by = 'Platform Administrator',
            reviewed_at = :reviewed_at
        WHERE id = :id
    """)
    await session.execute(update_stmt, {
        "reason": payload.rejection_reason.strip(),
        "reviewed_at": datetime.now(timezone.utc),
        "id": inquiry_id
    })
    await session.commit()

    return {
        "inquiry_id": inquiry_id,
        "status": "REJECTED",
        "rejection_reason": payload.rejection_reason
    }
