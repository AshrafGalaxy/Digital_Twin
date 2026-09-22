"""
auth.py

API endpoints for Municipal Role-Based Authentication and Session Issuance.
Enforces role boundaries across transportation engineering, energy grid,
executive auditing, and municipal intelligence operations.
"""

from datetime import datetime, timezone
import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()

VALID_MUNICIPAL_ROLES = [
    "Municipal Analyst",
    "Traffic Systems Engineer",
    "Energy Grid Manager",
    "Executive Auditor"
]

ROLE_METADATA: Dict[str, Dict[str, Any]] = {
    "Traffic Systems Engineer": {
        "badge": "TRAFFIC COMMAND",
        "clearance": "Level 2 • Operational Kinematics & Signal Control",
        "department": "Transportation Operations Division",
        "workspaces": ["Operations Map", "Traffic Analytics", "Scenario Studio", "Traffic Recommendations"]
    },
    "Energy Grid Manager": {
        "badge": "GRID UTILITY",
        "clearance": "Level 2 • Substation Feeder & Peak Governance",
        "department": "Municipal Utilities & Commercial Grid",
        "workspaces": ["Operations Map", "Energy Analytics", "Environment Context", "Energy Recommendations"]
    },
    "Executive Auditor": {
        "badge": "ALGORITHMIC GOVERNANCE",
        "clearance": "Level 3 • Independent Audit & Compliance Verification",
        "department": "Civic Governance & Oversight Council",
        "workspaces": ["Evaluation & Reports", "System & Data Health", "Advisory Governance"]
    },
    "Municipal Analyst": {
        "badge": "CROSS-DOMAIN COMMAND",
        "clearance": "Level 1 • Comprehensive Master Command",
        "department": "Urban Development & Smart City Mission",
        "workspaces": ["All 8 Workspaces (Full Master Console)"]
    }
}

# Pre-seeded authorized municipal demo accounts
DEMO_USERS: Dict[str, Dict[str, Any]] = {
    "traffic.engineer@pmc.gov.in": {
        "id": "usr-traffic-01",
        "name": "Vikram Desai",
        "password": "traffic123",
        "role": "Traffic Systems Engineer",
        "department": "Transportation Operations Division",
        "username": "traffic"
    },
    "grid.manager@pmc.gov.in": {
        "id": "usr-grid-01",
        "name": "Pooja Kulkarni",
        "password": "energy123",
        "role": "Energy Grid Manager",
        "department": "Municipal Utilities & Commercial Grid",
        "username": "energy"
    },
    "auditor@pmc.gov.in": {
        "id": "usr-audit-01",
        "name": "Dr. Aris Thorne",
        "password": "audit123",
        "role": "Executive Auditor",
        "department": "Civic Governance & Oversight Council",
        "username": "auditor"
    },
    "analyst@pmc.gov.in": {
        "id": "usr-analyst-01",
        "name": "Aditi Sharma",
        "password": "analyst123",
        "role": "Municipal Analyst",
        "department": "Urban Development & Smart City Mission",
        "username": "analyst"
    }
}

# In-memory registered user repository for dynamic signups during runtime
REGISTERED_USERS: Dict[str, Dict[str, Any]] = {}


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Municipal email or username callsign")
    password: str = Field(..., min_length=4, description="Password")


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Officer full name")
    email: str = Field(..., min_length=5, description="Municipal email address")
    password: str = Field(..., min_length=6, description="Password")
    role: str = Field(..., description="Designated municipal role")
    department: Optional[str] = Field(None, description="Department or division")


class AuthUserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    department: str
    token: str
    authenticatedAt: str
    clearance: str
    workspaces: List[str]


@router.post("/login", response_model=AuthUserResponse)
def login(payload: LoginRequest):
    """
    Authenticates municipal credentials and issues a secure session token.
    Supports standard municipal emails, usernames, and registered accounts.
    """
    query = payload.username_or_email.strip().lower()
    
    # 1. Check demo accounts by email or username
    matched_user = None
    for email, user in DEMO_USERS.items():
        if email.lower() == query or user["username"].lower() == query:
            matched_user = user
            break
            
    # 2. Check dynamic registrations
    if not matched_user and query in REGISTERED_USERS:
        matched_user = REGISTERED_USERS[query]

    if not matched_user or matched_user["password"] != payload.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid municipal credentials. Please check your email and password."
        )

    role = matched_user["role"]
    meta = ROLE_METADATA.get(role, ROLE_METADATA["Municipal Analyst"])
    token = f"pune-dt-token-{uuid.uuid4().hex[:16]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    return AuthUserResponse(
        id=matched_user["id"],
        name=matched_user["name"],
        email=matched_user.get("email", query),
        role=role,
        department=matched_user.get("department", meta["department"]),
        token=token,
        authenticatedAt=now_iso,
        clearance=meta["clearance"],
        workspaces=meta["workspaces"]
    )


@router.post("/register", response_model=AuthUserResponse)
def register(payload: RegisterRequest):
    """
    Registers a new municipal official with a validated role assignment.
    """
    email_clean = payload.email.strip().lower()
    
    if payload.role not in VALID_MUNICIPAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid municipal role '{payload.role}'. Must be one of: {VALID_MUNICIPAL_ROLES}"
        )

    if email_clean in DEMO_USERS or email_clean in REGISTERED_USERS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this municipal email address is already registered."
        )

    user_id = f"usr-{uuid.uuid4().hex[:8]}"
    meta = ROLE_METADATA[payload.role]
    dept = payload.department or meta["department"]

    new_user = {
        "id": user_id,
        "name": payload.name.strip(),
        "email": email_clean,
        "password": payload.password,
        "role": payload.role,
        "department": dept,
        "username": email_clean.split("@")[0]
    }

    REGISTERED_USERS[email_clean] = new_user
    token = f"pune-dt-token-{uuid.uuid4().hex[:16]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    return AuthUserResponse(
        id=user_id,
        name=new_user["name"],
        email=email_clean,
        role=payload.role,
        department=dept,
        token=token,
        authenticatedAt=now_iso,
        clearance=meta["clearance"],
        workspaces=meta["workspaces"]
    )


@router.get("/roles")
def get_roles():
    """
    Returns available municipal roles, their security clearances, and workspace permissions.
    """
    return {
        "roles": VALID_MUNICIPAL_ROLES,
        "metadata": ROLE_METADATA
    }
