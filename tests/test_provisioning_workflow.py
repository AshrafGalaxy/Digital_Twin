"""
test_provisioning_workflow.py

Hermetic automated test suite for end-to-end access inquiry intake,
admin review, single-use cryptographic magic link issuance, and redemption.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_submit_access_inquiry_and_admin_lifecycle(client):
    """
    Verifies that:
    1. A prospective agency can submit an access inquiry.
    2. Admin can list pending inquiries from the database.
    3. Admin can approve the inquiry with a specific municipal role.
    4. System issues a single-use cryptographic magic access token and email payload.
    5. The magic link can be redeemed to receive an authentic JWT session.
    6. Re-using the same magic token is strictly rejected.
    """
    # Step 1: Submit Inquiry
    payload = {
        "organization": "Metropolitan Transit Authority",
        "work_email": "ops.director@mta-corridor.gov",
        "contact_name": "Director Sarah Chen",
        "jurisdiction": "Central Arterial Network",
        "domain": "Mobility & Signal Optimization",
        "infrastructure_scale": "10-25 Intersections",
        "message": "Requesting operational digital twin access for corridor timing optimization."
    }
    submit_resp = client.post("/api/v1/inquiries/request-access", json=payload)
    assert submit_resp.status_code == 201
    submit_data = submit_resp.json()
    inquiry_id = submit_data["inquiry_id"]
    assert inquiry_id.startswith("INQ-")
    assert submit_data["status"] == "received"

    # Step 2: Admin lists inquiries and locates the submitted request
    list_resp = client.get("/api/v1/inquiries?status_filter=PENDING")
    assert list_resp.status_code == 200
    inquiries = list_resp.json()
    assert any(inq["id"] == inquiry_id for inq in inquiries)

    matching_inq = next(inq for inq in inquiries if inq["id"] == inquiry_id)
    assert matching_inq["organization"] == "Metropolitan Transit Authority"
    assert matching_inq["contact_name"] == "Director Sarah Chen"
    assert matching_inq["status"] == "PENDING"

    # Step 3: Admin approves inquiry with designated role
    approve_payload = {
        "assigned_role": "Traffic Systems Engineer",
        "expiry_days": 14,
        "reviewer_notes": "Approved for metropolitan timing demonstration."
    }
    approve_resp = client.post(f"/api/v1/inquiries/{inquiry_id}/approve", json=approve_payload)
    assert approve_resp.status_code == 200
    approve_data = approve_resp.json()
    assert approve_data["status"] == "APPROVED"
    assert approve_data["assigned_role"] == "Traffic Systems Engineer"
    magic_token = approve_data["magic_token"]
    assert len(magic_token) > 20
    assert "access-token=" in approve_data["magic_link"]
    assert approve_data["email_payload"]["to"] == "ops.director@mta-corridor.gov"
    assert "Traffic Systems Engineer" in approve_data["email_payload"]["body"]

    # Step 4: Requester redeems magic token via /api/v1/auth/magic-link
    redeem_resp = client.post("/api/v1/auth/magic-link", json={"token": magic_token})
    assert redeem_resp.status_code == 200
    auth_data = redeem_resp.json()
    assert auth_data["name"] == "Director Sarah Chen"
    assert auth_data["email"] == "ops.director@mta-corridor.gov"
    assert auth_data["role"] == "Traffic Systems Engineer"
    assert auth_data["token"] is not None
    assert "Operations Map" in auth_data["workspaces"]

    # Step 5: Single-use enforcement: Attempting to redeem the same token again must fail
    replay_resp = client.post("/api/v1/auth/magic-link", json={"token": magic_token})
    assert replay_resp.status_code == 400
    assert "already been used" in replay_resp.json()["detail"].lower()


def test_reject_access_inquiry(client):
    """
    Verifies that admin can reject an access inquiry with a stated reason.
    """
    payload = {
        "organization": "Unauthorized Commercial Scraper Inc",
        "work_email": "bot@unverified-domain.com",
        "contact_name": "Anonymous Requester",
        "jurisdiction": "Unknown Jurisdiction",
        "domain": "Commercial Scraping",
        "infrastructure_scale": "Unknown",
        "message": "Testing access limits."
    }
    submit_resp = client.post("/api/v1/inquiries/request-access", json=payload)
    assert submit_resp.status_code == 201
    inquiry_id = submit_resp.json()["inquiry_id"]

    reject_resp = client.post(
        f"/api/v1/inquiries/{inquiry_id}/reject",
        json={"rejection_reason": "Unverified municipal jurisdiction and non-authorized domain."}
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "REJECTED"

    # Confirm status in admin list
    list_resp = client.get("/api/v1/inquiries?status_filter=REJECTED")
    assert list_resp.status_code == 200
    inquiries = list_resp.json()
    assert any(inq["id"] == inquiry_id for inq in inquiries)


def test_magic_link_invalid_token(client):
    """
    Verifies that invalid or non-existent magic tokens are properly rejected.
    """
    redeem_resp = client.post("/api/v1/auth/magic-link", json={"token": "completely-invalid-nonexistent-token"})
    assert redeem_resp.status_code == 404
