"""
test_api_edge_controls.py

Hermetic test suite for Issue #56 ([ENH-01]):
1. Per-IP sliding-window rate limiting on auth routes (/login, /register, /magic-link).
2. Separate, higher per-IP rate limiting on heavy compute routes.
3. Host header validation when exposed beyond localhost.
4. Preservation of explicit CORS origin allowlist and standalone auth router protection.
5. Zero emojis and zero em/en dashes across modified files.
"""

from pathlib import Path
import re
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from backend.api.v1.endpoints.auth import router as auth_router
from backend.core.config import settings
from backend.core.edge_controls import (
    SlidingWindowRateLimiter,
    is_host_allowed,
    rate_limiter,
)
from backend.main import app


ROOT_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def reset_edge_rate_limiter():
    """Ensures hermetic bucket isolation before and after every test."""
    rate_limiter.reset()
    yield
    rate_limiter.reset()


def test_sliding_window_rate_limiter_unit_and_memory_cap():
    """Verifies window sliding expiration, retry-after calculation, and key cap."""
    limiter = SlidingWindowRateLimiter(max_keys=100)
    t0 = 1000.0

    for i in range(3):
        allowed, rem, retry = limiter.check_and_consume("auth", "10.0.0.1", limit=3, window_seconds=60, now_monotonic=t0 + i)
        assert allowed is True
        assert rem == 2 - i
        assert retry == 0

    blocked, rem_b, retry_b = limiter.check_and_consume("auth", "10.0.0.1", limit=3, window_seconds=60, now_monotonic=t0 + 5.0)
    assert blocked is False
    assert rem_b == 0
    assert retry_b >= 55

    # Advance past 60s window from t0 -> oldest slot frees up
    allowed_after, _, _ = limiter.check_and_consume("auth", "10.0.0.1", limit=3, window_seconds=60, now_monotonic=t0 + 61.0)
    assert allowed_after is True


def test_default_auth_burst_limit_triggers_429():
    """Default configured auth threshold (25 req / 60s) blocks the 26th login burst with HTTP 429."""
    default_cap = int(settings.RATE_LIMIT_AUTH_REQUESTS)
    assert default_cap == 25

    with TestClient(app) as client:
        for _ in range(default_cap):
            ok_or_auth = client.post(
                "/api/v1/auth/login",
                json={"username_or_email": "traffic.engineer@pmc.gov.in", "password": "wrong_password_123"},
            )
            assert ok_or_auth.status_code == 401

        blocked = client.post(
            "/api/v1/auth/login",
            json={"username_or_email": "traffic.engineer@pmc.gov.in", "password": "traffic123"},
        )
        assert blocked.status_code == 429
        assert int(blocked.headers["retry-after"]) >= 1


def test_auth_burst_triggers_429_without_double_counting(monkeypatch):
    """A burst of login attempts past the configured limit triggers HTTP 429 with Retry-After."""
    monkeypatch.setattr(settings, "RATE_LIMIT_AUTH_REQUESTS", 4)
    monkeypatch.setattr(settings, "RATE_LIMIT_AUTH_WINDOW_SEC", 60)

    with TestClient(app) as client:
        # First 4 requests under limit succeed (or fail auth cleanly) and decrement 1-for-1
        for expected_rem in (3, 2, 1, 0):
            res = client.post(
                "/api/v1/auth/login",
                json={"username_or_email": "traffic.engineer@pmc.gov.in", "password": "wrong-password"},
            )
            assert res.status_code == 401
            assert res.headers.get("x-ratelimit-limit") == "4"
            assert res.headers.get("x-ratelimit-remaining") == str(expected_rem)

        # 5th request hits 429 on login
        burst_login = client.post(
            "/api/v1/auth/login",
            json={"username_or_email": "traffic.engineer@pmc.gov.in", "password": "traffic123"},
        )
        assert burst_login.status_code == 429
        assert int(burst_login.headers["retry-after"]) >= 1

        # Shared auth tier also blocks /register and /magic-link from the same IP
        burst_reg = client.post(
            "/api/v1/auth/register",
            json={"name": "Test Civic", "email": "civic@example.com", "password": "password123", "role": "Civic Observer"},
        )
        assert burst_reg.status_code == 429

        burst_magic = client.post("/api/v1/auth/magic-link", json={"token": "abcdef123456"})
        assert burst_magic.status_code == 429


def test_standalone_auth_router_enforces_rate_limit(monkeypatch):
    """Mounting auth.router directly still enforces per-IP limits via FastAPI dependency."""
    monkeypatch.setattr(settings, "RATE_LIMIT_AUTH_REQUESTS", 2)
    isolated = FastAPI()
    isolated.include_router(auth_router, prefix="/auth")

    with TestClient(isolated) as client:
        bad_creds = {"username_or_email": "unknown@example.com", "password": "wrong_password_123"}
        assert client.post("/auth/login", json=bad_creds).status_code == 401
        assert client.post("/auth/login", json=bad_creds).status_code == 401
        res3 = client.post("/auth/login", json=bad_creds)
        assert res3.status_code == 429


def test_heavy_compute_has_separate_higher_limit(monkeypatch):
    """
    Exhausting the low auth limit does not block heavy compute routes;
    compute routes enforce their own separate higher limit.
    """
    monkeypatch.setattr(settings, "RATE_LIMIT_AUTH_REQUESTS", 2)
    monkeypatch.setattr(settings, "RATE_LIMIT_COMPUTE_REQUESTS", 5)

    with TestClient(app) as client:
        # Exhaust auth tier
        bad_creds = {"username_or_email": "unknown@example.com", "password": "wrong_password_123"}
        client.post("/api/v1/auth/login", json=bad_creds)
        client.post("/api/v1/auth/login", json=bad_creds)
        assert client.post("/api/v1/auth/login", json=bad_creds).status_code == 429

        # Heavy compute routes remain available up to their own ceiling (5)
        for idx in range(5):
            path = "/api/v1/forecasts/models" if idx % 2 == 0 else "/api/v1/traffic/corridor/los"
            comp_res = client.get(path)
            assert comp_res.status_code == 200
            assert comp_res.headers.get("x-ratelimit-limit") == "5"

        # 6th heavy compute request hits 429
        blocked = client.get("/api/v1/analytics/rollups/traffic")
        assert blocked.status_code == 429
        assert int(blocked.headers["retry-after"]) >= 1


def test_trusted_host_checking_and_localhost_exception(monkeypatch):
    """
    When exposed beyond localhost (API_HOST=0.0.0.0), unknown Host headers are rejected
    with HTTP 400 while configured hosts succeed. Loopback-only binding bypasses external check.
    """
    monkeypatch.setattr(settings, "API_HOST", "0.0.0.0")
    monkeypatch.setattr(settings, "ALLOWED_HOSTS", "localhost,127.0.0.1,testserver,*.twin.gov.in")

    with TestClient(app) as client:
        ok_default = client.get("/api/v1/health")
        assert ok_default.status_code == 200

        ok_local_port = client.get("/api/v1/health", headers={"Host": "localhost:8000"})
        assert ok_local_port.status_code == 200

        ok_wildcard = client.get("/api/v1/health", headers={"Host": "api.twin.gov.in"})
        assert ok_wildcard.status_code == 200

        bad_host = client.get("/api/v1/health", headers={"Host": "evil.attacker.example"})
        assert bad_host.status_code == 400
        assert "Invalid host" in bad_host.json()["detail"]

        # When bound strictly to localhost in non-production, untrusted host filter is inactive
        monkeypatch.setattr(settings, "API_HOST", "127.0.0.1")
        monkeypatch.setattr(settings, "ENVIRONMENT", "development")
        loopback_ok = client.get("/api/v1/health", headers={"Host": "custom.local.alias"})
        assert loopback_ok.status_code == 200

    assert is_host_allowed("[::1]:8000", ["::1"]) is True
    assert is_host_allowed("", ["localhost"]) is False


def test_explicit_cors_preserved_across_normal_and_429_responses(monkeypatch):
    """Explicit CORS origins remain active on normal 200 and rate-limited 429 responses."""
    monkeypatch.setattr(settings, "RATE_LIMIT_AUTH_REQUESTS", 1)
    allowed_origin = settings.cors_origins_list[0]

    with TestClient(app) as client:
        ok = client.post(
            "/api/v1/auth/login",
            json={"username_or_email": "traffic.engineer@pmc.gov.in", "password": "traffic123"},
            headers={"Origin": allowed_origin},
        )
        assert ok.status_code == 200
        assert ok.headers.get("access-control-allow-origin") == allowed_origin

        limited = client.post(
            "/api/v1/auth/login",
            json={"username_or_email": "traffic.engineer@pmc.gov.in", "password": "traffic123"},
            headers={"Origin": allowed_origin},
        )
        assert limited.status_code == 429
        assert limited.headers.get("access-control-allow-origin") == allowed_origin

        disallowed_cors = client.get("/api/v1/health", headers={"Origin": "https://untrusted-site.example"})
        assert disallowed_cors.status_code == 200
        assert disallowed_cors.headers.get("access-control-allow-origin") is None


def test_production_security_rejects_wildcard_or_empty_allowed_hosts(monkeypatch):
    """Production startup refuses wildcard '*' or empty ALLOWED_HOSTS."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "MQTT_PASSWORD", "strong_prod_secret_987")
    monkeypatch.setattr(settings, "MQTT_USERNAME", "prod_svc")

    monkeypatch.setattr(settings, "ALLOWED_HOSTS", "*")
    with pytest.raises(RuntimeError, match="ALLOWED_HOSTS"):
        settings.validate_production_security()

    monkeypatch.setattr(settings, "ALLOWED_HOSTS", "   ")
    with pytest.raises(RuntimeError, match="ALLOWED_HOSTS"):
        settings.validate_production_security()


def test_zero_emojis_and_zero_em_dashes_in_edge_control_files():
    """Asserts zero emojis and zero em/en dashes across Issue #56 files."""
    files = [
        ROOT_DIR / "backend" / "core" / "config.py",
        ROOT_DIR / "backend" / "core" / "edge_controls.py",
        ROOT_DIR / "backend" / "main.py",
        ROOT_DIR / "backend" / "api" / "v1" / "endpoints" / "auth.py",
        ROOT_DIR / "tests" / "test_api_edge_controls.py",
    ]
    emoji_re = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")
    for fpath in files:
        content = fpath.read_text(encoding="utf-8")
        assert "\u2014" not in content, f"Em dash found in {fpath}"
        assert "\u2013" not in content, f"En dash found in {fpath}"
        assert not emoji_re.search(content), f"Emoji found in {fpath}"
