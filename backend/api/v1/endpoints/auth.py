"""
auth.py

API endpoints for Municipal Role-Based Authentication and Session Issuance.
Enforces role boundaries across transportation engineering, energy grid,
executive auditing, and municipal intelligence operations.
"""

from datetime import datetime, timezone, timedelta
import uuid
import base64
import json
import hmac
import hashlib
import secrets
import os
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel, Field

router = APIRouter()

# Authoritative cryptographic session secret
JWT_SECRET_KEY = os.getenv("MUNICIPAL_JWT_SECRET", "pune-dt-corridor-key-2026-viman-nagar")

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
        "name": "Traffic Systems Engineer",
        "password": "traffic123",
        "role": "Traffic Systems Engineer",
        "department": "Transportation Operations Division",
        "username": "traffic"
    },
    "grid.manager@pmc.gov.in": {
        "id": "usr-grid-01",
        "name": "Energy Grid Manager",
        "password": "energy123",
        "role": "Energy Grid Manager",
        "department": "Municipal Utilities & Commercial Grid",
        "username": "energy"
    },
    "auditor@pmc.gov.in": {
        "id": "usr-audit-01",
        "name": "Executive Auditor",
        "password": "audit123",
        "role": "Executive Auditor",
        "department": "Civic Governance & Oversight Council",
        "username": "auditor"
    },
    "analyst@pmc.gov.in": {
        "id": "usr-analyst-01",
        "name": "Municipal Analyst",
        "password": "analyst123",
        "role": "Municipal Analyst",
        "department": "Urban Development & Smart City Mission",
        "username": "analyst"
    }
}

# In-memory registered user repository for dynamic signups during runtime
REGISTERED_USERS: Dict[str, Dict[str, Any]] = {}


def _hash_password(raw_password: str) -> str:
    """Derives a PBKDF2-HMAC-SHA256 salted hash for credentials."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", raw_password.encode("utf-8"), salt.encode("utf-8"), 20000)
    return f"pbkdf2_sha256$20000${salt}${key.hex()}"


def _verify_password(raw_password: str, stored_password: str) -> bool:
    """Verifies candidate password with constant-time equality check."""
    if stored_password.startswith("pbkdf2_sha256$"):
        parts = stored_password.split("$")
        if len(parts) == 4:
            iterations = int(parts[1])
            salt = parts[2].encode("utf-8")
            expected_key = parts[3]
            candidate_key = hashlib.pbkdf2_hmac("sha256", raw_password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(candidate_key.hex(), expected_key)
    # Fallback constant-time check for pre-seeded demo accounts
    return hmac.compare_digest(raw_password, stored_password)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _b64url_decode(data_str: str) -> bytes:
    padding = 4 - (len(data_str) % 4)
    if padding < 4:
        data_str += '=' * padding
    return base64.urlsafe_b64decode(data_str.encode('ascii'))


def _create_jwt_token(payload: Dict[str, Any]) -> str:
    """Issues an authentic signed HMAC-SHA256 JWT session token."""
    header = {"alg": "HS256", "typ": "JWT"}
    header_str = _b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_str = _b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    msg = f"{header_str}.{payload_str}".encode('utf-8')
    sig = hmac.new(JWT_SECRET_KEY.encode('utf-8'), msg, hashlib.sha256).digest()
    sig_str = _b64url_encode(sig)
    return f"{header_str}.{payload_str}.{sig_str}"


def _verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and cryptographically verifies an HMAC-SHA256 JWT token."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_str, payload_str, sig_str = parts
        msg = f"{header_str}.{payload_str}".encode('utf-8')
        expected_sig = hmac.new(JWT_SECRET_KEY.encode('utf-8'), msg, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_str)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_b64url_decode(payload_str).decode('utf-8'))
        exp = payload.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            return None
        return payload
    except Exception:
        return None


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
    Authenticates municipal credentials and issues a cryptographic JWT session token.
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

    if not matched_user or not _verify_password(payload.password, matched_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid municipal credentials. Please check your email and password."
        )

    role = matched_user["role"]
    meta = ROLE_METADATA.get(role, ROLE_METADATA["Municipal Analyst"])
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    jwt_payload = {
        "sub": matched_user["id"],
        "email": matched_user.get("email", query),
        "name": matched_user["name"],
        "role": role,
        "department": matched_user.get("department", meta["department"]),
        "clearance": meta["clearance"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=8)).timestamp()),
        "iss": "pune-digital-twin-auth"
    }
    token = _create_jwt_token(jwt_payload)

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
    Registers a new municipal official with PBKDF2-hashed credentials and role verification.
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

    hashed_pw = _hash_password(payload.password)

    new_user = {
        "id": user_id,
        "name": payload.name.strip(),
        "email": email_clean,
        "password": hashed_pw,
        "role": payload.role,
        "department": dept,
        "username": email_clean.split("@")[0]
    }

    REGISTERED_USERS[email_clean] = new_user
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    jwt_payload = {
        "sub": user_id,
        "email": email_clean,
        "name": new_user["name"],
        "role": payload.role,
        "department": dept,
        "clearance": meta["clearance"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=8)).timestamp()),
        "iss": "pune-digital-twin-auth"
    }
    token = _create_jwt_token(jwt_payload)

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


@router.get("/verify")
def verify_session(authorization: Optional[str] = Header(None)):
    """
    Validates an incoming Bearer JWT session token and returns officer claims.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header."
        )
    raw_token = authorization.split("Bearer ", 1)[1].strip()
    payload = _verify_jwt_token(raw_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token expired or signature invalid."
        )
    return {
        "valid": True,
        "claims": payload
    }


@router.get("/roles")
def get_roles():
    """
    Returns available municipal roles, their security clearances, and workspace permissions.
    """
    return {
        "roles": VALID_MUNICIPAL_ROLES,
        "metadata": ROLE_METADATA
    }
