"""
tests/test_auth_endpoints.py

Hermetic verification of Municipal Authentication API endpoints:
- Successful login with demo credentials
- Invalid credentials rejection
- Municipal official registration with valid role assignment (Civic Observer public)
- Rejection of self-assigned operational roles (HTTP 403 Forbidden)
- Rejection of unauthorized roles (HTTP 400 Bad Request)
- Insecure fallback secret refusal (HTTP 500 Internal Server Error)
- Roles and clearance metadata query
"""

import os
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from backend.main import app
from backend.api.v1.endpoints.auth import get_jwt_secret, INSECURE_FALLBACK_JWT_SECRET

client = TestClient(app)


def test_auth_roles_metadata():
    """Verify metadata returns all 5 municipal roles (4 operational + 1 civic observer) with clearance scopes."""
    response = client.get("/api/v1/auth/roles")
    assert response.status_code == 200
    data = response.json()
    assert "roles" in data
    assert "metadata" in data
    assert len(data["roles"]) == 5
    assert "Civic Observer" in data["roles"]
    assert "Traffic Systems Engineer" in data["roles"]
    assert "Energy Grid Manager" in data["roles"]
    assert "Executive Auditor" in data["roles"]
    assert "Municipal Analyst" in data["roles"]


def test_demo_login_success():
    """Verify demo credentials for Traffic Systems Engineer."""
    payload = {
        "username_or_email": "traffic.engineer@pmc.gov.in",
        "password": "traffic123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    user = response.json()
    assert user["name"] == "Traffic Systems Engineer"
    assert user["role"] == "Traffic Systems Engineer"
    assert user["department"] == "Transportation Operations Division"
    assert "token" in user
    assert len(user["workspaces"]) > 0


def test_demo_login_by_username():
    """Verify login using username shortcut."""
    payload = {
        "username_or_email": "auditor",
        "password": "audit123"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    user = response.json()
    assert user["role"] == "Executive Auditor"


def test_login_invalid_password():
    """Verify invalid password returns 401 Unauthorized."""
    payload = {
        "username_or_email": "traffic.engineer@pmc.gov.in",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


def test_registration_success_civic_observer():
    """Verify new civic observer registration is permitted publicly."""
    payload = {
        "name": "Siddharth Joshi",
        "email": "siddharth.joshi.civic@pmc.gov.in",
        "password": "securepassword123",
        "role": "Civic Observer",
        "department": "Public Stakeholder & Community Registry"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    user = response.json()
    assert user["name"] == "Siddharth Joshi"
    assert user["role"] == "Civic Observer"
    assert "token" in user


def test_registration_operational_role_forbidden():
    """Verify self-registration for operational clearance roles is rejected with HTTP 403 Forbidden."""
    for op_role in ["Traffic Systems Engineer", "Energy Grid Manager", "Executive Auditor", "Municipal Analyst"]:
        payload = {
            "name": "Unauthorized Operator",
            "email": f"operator.{op_role.lower().replace(' ', '')}@pmc.gov.in",
            "password": "securepassword123",
            "role": op_role,
            "department": "Operations Division"
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 403
        assert "cannot be self-assigned via public registration" in response.json()["detail"]


def test_registration_invalid_role():
    """Verify rejection when registering with non-municipal role."""
    payload = {
        "name": "Bad Actor",
        "email": "actor@pmc.gov.in",
        "password": "securepassword123",
        "role": "RootSuperuser",
        "department": "External"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400


def test_session_verification_success():
    """Verify valid JWT token is decoded and returns officer claims."""
    # 1. Login to obtain token
    login_res = client.post("/api/v1/auth/login", json={
        "username_or_email": "grid.manager@pmc.gov.in",
        "password": "energy123"
    })
    assert login_res.status_code == 200
    token = login_res.json()["token"]

    # 2. Verify token via /verify endpoint
    verify_res = client.get("/api/v1/auth/verify", headers={"Authorization": f"Bearer {token}"})
    assert verify_res.status_code == 200
    data = verify_res.json()
    assert data["valid"] is True
    assert data["claims"]["role"] == "Energy Grid Manager"
    assert data["claims"]["sub"] == "usr-grid-01"


def test_session_verification_invalid():
    """Verify invalid or tampered token is rejected with 401."""
    response = client.get("/api/v1/auth/verify", headers={"Authorization": "Bearer fake.tampered.token"})
    assert response.status_code == 401


def test_jwt_secret_fallback_refusal(monkeypatch):
    """Verify get_jwt_secret() refuses to execute in production mode if unset or set to insecure fallback."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    # Test missing secret
    monkeypatch.setenv("MUNICIPAL_JWT_SECRET", "")
    with pytest.raises(HTTPException) as excinfo:
        get_jwt_secret()
    assert excinfo.value.status_code == 500

    # Test insecure fallback string
    monkeypatch.setenv("MUNICIPAL_JWT_SECRET", INSECURE_FALLBACK_JWT_SECRET)
    with pytest.raises(HTTPException) as excinfo:
        get_jwt_secret()
    assert excinfo.value.status_code == 500


def test_jwt_secret_dev_mock_allowed_in_development(monkeypatch):
    """Verify get_jwt_secret() supplies development mock secret without crashing when in development mode."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("MUNICIPAL_JWT_SECRET", "")
    secret = get_jwt_secret()
    assert len(secret) > 16
    assert secret != INSECURE_FALLBACK_JWT_SECRET


def test_demo_bypass_login_success_in_dev():
    """Verify dedicated 1-click dev demo account works in development mode."""
    payload = {
        "username_or_email": "demo",
        "password": "demo"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    user = response.json()
    assert user["name"] == "Development Lead Director (Demo)"
    assert user["role"] == "Municipal Analyst"
    assert "token" in user


def test_demo_bypass_login_disabled_in_production(monkeypatch):
    """Verify dedicated dev demo account is strictly blocked in production mode with 403 Forbidden."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    payload = {
        "username_or_email": "demo",
        "password": "demo"
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 403
    assert "Development demo accounts are disabled in production" in response.json()["detail"]


def test_privileged_controls_require_a_session():
    """Review, replay control, and simulator control reject a caller with no session."""
    review = client.post(
        "/api/v1/recommendations/REC-TRF-20260920-001/review",
        json={"newStatus": "DISMISSED", "reviewer": "anonymous"},
    )
    replay = client.post(
        "/api/v1/stream/replay/control",
        json={"action": "seek", "minutes_ago": 30},
    )
    simulator = client.post(
        "/api/v1/stream/simulator/control",
        json={"action": "pause"},
    )
    assert review.status_code == 401
    assert replay.status_code == 401
    assert simulator.status_code == 401
