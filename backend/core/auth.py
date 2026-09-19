"""
auth.py

Role-Based Access Control (RBAC) and basic demo authentication for the platform (D-11).
Supports viewer, analyst, and admin roles for remote stakeholder demonstrations.
Can be toggled via AUTH_ENABLED in settings (defaults to False for frictionless local dev).
"""

import os
from enum import Enum
from typing import List, Optional
from fastapi import Header, HTTPException, Security, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel


class UserRole(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"


class AuthenticatedUser(BaseModel):
    username: str
    role: UserRole


# Default demo credentials when AUTH_ENABLED=True
DEMO_CREDENTIALS = {
    "admin": ("admin123", UserRole.ADMIN),
    "analyst": ("analyst123", UserRole.ANALYST),
    "viewer": ("viewer123", UserRole.VIEWER),
}

# Role hierarchy: admin > analyst > viewer
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER],
    UserRole.ANALYST: [UserRole.ANALYST, UserRole.VIEWER],
    UserRole.VIEWER: [UserRole.VIEWER],
}

security = HTTPBasic(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPBasicCredentials] = Security(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> AuthenticatedUser:
    """
    Authenticates requests if AUTH_ENABLED is set to true.
    If AUTH_ENABLED is false (default), grants admin access automatically for local dev.
    """
    auth_enabled = os.getenv("AUTH_ENABLED", "false").strip().lower() in ("true", "1", "yes")

    if not auth_enabled:
        return AuthenticatedUser(username="local-dev-operator", role=UserRole.ADMIN)

    # API Key shortcut for automated CI / headless scripts
    master_key = os.getenv("DEMO_API_KEY", "twin-demo-secret-key-2026")
    if x_api_key and x_api_key == master_key:
        return AuthenticatedUser(username="api-client", role=UserRole.ADMIN)

    # HTTP Basic authentication
    if credentials:
        user_info = DEMO_CREDENTIALS.get(credentials.username)
        if user_info and user_info[0] == credentials.password:
            return AuthenticatedUser(username=credentials.username, role=user_info[1])

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials for remote demo access.",
        headers={"WWW-Authenticate": "Basic"}
    )


def require_role(allowed_roles: List[UserRole]):
    """
    Dependency factory verifying that the authenticated user possesses the required role.
    """
    def role_checker(user: AuthenticatedUser = Security(get_current_user)) -> AuthenticatedUser:
        user_permissions = ROLE_PERMISSIONS.get(user.role, [])
        if not any(role in user_permissions for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of roles: {[r.value for r in allowed_roles]}. Current role: '{user.role.value}'."
            )
        return user
    return role_checker
