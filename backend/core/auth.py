"""
auth.py

Core authentication and Role-Based Access Control (RBAC) dependency provider.
Integrates cryptographic Bearer JWT verification and dual-control operational clearances.
"""

import os
from enum import Enum
from typing import List, Optional, Dict, Any
from fastapi import Header, HTTPException, Security, status, Depends
from pydantic import BaseModel

from backend.api.v1.endpoints.auth import (
    get_current_authenticated_officer,
    require_admin_or_analyst,
    require_operational_officer,
    _verify_jwt_token
)


class UserRole(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"


class AuthenticatedUser(BaseModel):
    username: str
    role: UserRole


def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> AuthenticatedUser:
    """
    Authenticates requests via Bearer JWT session token or administrative API key.
    """
    master_key = os.getenv("DEMO_API_KEY", "twin-demo-secret-key-2026")
    if x_api_key and x_api_key == master_key:
        return AuthenticatedUser(username="api-client", role=UserRole.ADMIN)

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
        claims = _verify_jwt_token(token)
        if claims:
            role_str = claims.get("role", "")
            mapped_role = UserRole.ADMIN if role_str in ("Municipal Analyst", "Executive Auditor") else UserRole.ANALYST
            return AuthenticatedUser(username=claims.get("name", "officer"), role=mapped_role)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"}
    )
