"""
tests/test_auth_endpoints.py

Hermetic verification of Municipal Authentication API endpoints:
- Successful login with demo credentials
- Invalid credentials rejection
- Municipal official registration with valid role assignment
- Rejection of unauthorized roles
- Roles and clearance metadata query
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_auth_roles_metadata():
    """Verify metadata returns all 4 municipal roles with clearance scopes."""
    response = client.get("/api/v1/auth/roles")
    assert response.status_code == 200
    data = response.json()
    assert "roles" in data
    assert "metadata" in data
    assert len(data["roles"]) == 4
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
    assert user["name"] == "Vikram Desai"
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


def test_registration_success():
    """Verify new municipal officer registration."""
    payload = {
        "name": "Siddharth Joshi",
        "email": f"siddharth.joshi.test@pmc.gov.in",
        "password": "securepassword123",
        "role": "Energy Grid Manager",
        "department": "Municipal Utilities & Commercial Grid"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200
    user = response.json()
    assert user["name"] == "Siddharth Joshi"
    assert user["role"] == "Energy Grid Manager"
    assert "token" in user


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
