"""
inquiries.py

Intake endpoint for municipal, enterprise, and research digital twin
access requests and pilot provisioning inquiries.
"""

from datetime import datetime, timezone
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class AccessInquiryRequest(BaseModel):
    organization: str = Field(..., min_length=2, max_length=200, description="Agency, municipality, or company name")
    work_email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Official business or government email address")
    contact_name: str = Field(..., min_length=2, max_length=120, description="Full name and title of representative")
    jurisdiction: str = Field(..., min_length=2, max_length=150, description="City, municipality, campus, or highway corridor")
    domain: str = Field(default="Integrated Multi-Domain Digital Twin", max_length=100, description="Primary domain of interest")
    infrastructure_scale: Optional[str] = Field(default="1-10 Intersections / Corridors", max_length=100)
    message: Optional[str] = Field(default="", max_length=2000, description="Deployment timeline and telemetry requirements")


class AccessInquiryResponse(BaseModel):
    inquiry_id: str
    status: str
    received_at: str
    message: str


@router.post(
    "/request-access",
    response_model=AccessInquiryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an agency access or pilot provisioning inquiry",
)
async def submit_access_inquiry(payload: AccessInquiryRequest) -> AccessInquiryResponse:
    inquiry_id = f"INQ-{datetime.now(timezone.utc).year}-{uuid.uuid4().hex[:6].upper()}"
    received_at = datetime.now(timezone.utc).isoformat()

    logger.info(
        "Received access inquiry %s from %s (%s) for jurisdiction %s [Domain: %s]",
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
