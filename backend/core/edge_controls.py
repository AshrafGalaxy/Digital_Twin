"""
edge_controls.py

API edge controls implementing:
1. Thread-safe, bounded sliding-window per-IP rate limiting for auth and heavy compute routes.
2. Dynamic Host header validation when exposed beyond localhost.
3. Standalone FastAPI auth rate-limit dependency with zero double-counting.
"""

from collections import deque
import json
import math
import threading
import time
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple
from fastapi import HTTPException, Request, status

from backend.core.config import settings


AUTH_RATE_LIMITED_PATHS = (
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/magic-link",
)

HEAVY_COMPUTE_PATH_PREFIXES = (
    "/api/v1/forecasts",
    "/api/v1/energy/forecasts/",
    "/api/v1/energy/solar/",
    "/api/v1/energy/optimize-bess",
    "/api/v1/energy/bess/optimize",
    "/api/v1/analytics/",
    "/api/v1/traffic/corridor/los",
    "/api/v1/traffic/optimizer/",
    "/api/v1/scenarios/run",
    "/api/v1/reports/",
    "/api/v1/export/",
)


def is_auth_rate_limited_path(path: str) -> bool:
    norm = path.rstrip("/") or "/"
    return norm in AUTH_RATE_LIMITED_PATHS


def is_heavy_compute_path(path: str) -> bool:
    norm = path.rstrip("/") or "/"
    for prefix in HEAVY_COMPUTE_PATH_PREFIXES:
        if prefix.endswith("/") and path.startswith(prefix):
            return True
        if not prefix.endswith("/") and (norm == prefix or norm.startswith(f"{prefix}/")):
            return True
    if norm.startswith("/api/v1/traffic/segment/") and norm.endswith("/los"):
        return True
    if norm.startswith("/api/v1/energy/zones/") and norm.endswith("/simulate-precooling"):
        return True
    return False


def extract_hostname(host_header: Optional[str]) -> str:
    """
    Extracts normalized hostname from an HTTP Host header, stripping optional port
    while supporting IPv6 bracketed literals (e.g. '[::1]:8000' -> '::1').
    """
    if not host_header:
        return ""
    raw = host_header.strip().lower()
    if not raw:
        return ""
    if raw.startswith("["):
        closing = raw.find("]")
        if closing != -1:
            return raw[1:closing]
        return raw
    if ":" in raw:
        return raw.rsplit(":", 1)[0]
    return raw


def is_host_allowed(host_header: Optional[str], allowed_hosts: List[str]) -> bool:
    """Validates normalized hostname against configured allowed hosts (supports '*.domain')."""
    if not allowed_hosts:
        return False
    if "*" in allowed_hosts:
        return True
    hostname = extract_hostname(host_header)
    if not hostname:
        return False
    for pattern in allowed_hosts:
        pat = pattern.strip().lower()
        if not pat:
            continue
        if pat.startswith("*."):
            suffix = pat[1:]  # '.example.com'
            if hostname.endswith(suffix) and len(hostname) > len(suffix):
                return True
        elif hostname == pat:
            return True
    return False


def extract_client_ip_from_headers_and_client(
    client_host: Optional[str],
    headers: Dict[str, str],
) -> str:
    """
    Resolves client IP address. Honors X-Forwarded-For only when TRUST_PROXY_HEADERS
    is enabled to prevent trivial rate-limit bypass via header spoofing.
    """
    if getattr(settings, "TRUST_PROXY_HEADERS", False):
        xff = headers.get("x-forwarded-for", "")
        if xff:
            first_ip = xff.split(",")[0].strip()
            if first_ip:
                return first_ip
    return (client_host or "unknown").strip() or "unknown"


class SlidingWindowRateLimiter:
    """
    Thread-safe bounded sliding-window rate limiter keyed by (tier, client_ip).
    Evicts old timestamps per access and bounds total tracked keys to protect memory.
    """

    def __init__(self, max_keys: int = 10000):
        self._lock = threading.Lock()
        self._max_keys = max(100, int(max_keys))
        self._buckets: Dict[Tuple[str, str], Deque[float]] = {}

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()

    def check_and_consume(
        self,
        tier: str,
        client_ip: str,
        limit: int,
        window_seconds: int,
        now_monotonic: Optional[float] = None,
    ) -> Tuple[bool, int, int]:
        """
        Records or rejects one request attempt.
        Returns (allowed, remaining_requests, retry_after_seconds).
        """
        now = float(now_monotonic) if now_monotonic is not None else time.monotonic()
        win = max(1, int(window_seconds))
        cap = max(1, int(limit))
        cutoff = now - float(win)
        key = (tier, client_ip)

        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                if len(self._buckets) >= self._max_keys:
                    # Evict oldest inserted key to keep memory strictly bounded
                    oldest_key = next(iter(self._buckets))
                    del self._buckets[oldest_key]
                bucket = deque()
                self._buckets[key] = bucket

            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= cap:
                oldest_in_window = bucket[0]
                retry_after = max(1, int(math.ceil((oldest_in_window + float(win)) - now)))
                return False, 0, retry_after

            bucket.append(now)
            remaining = max(0, cap - len(bucket))
            return True, remaining, 0


rate_limiter = SlidingWindowRateLimiter()


def _parse_asgi_headers(raw_headers: Any) -> Dict[str, str]:
    parsed: Dict[str, str] = {}
    if not raw_headers:
        return parsed
    for k_bytes, v_bytes in raw_headers:
        try:
            k = k_bytes.decode("latin-1").lower()
            v = v_bytes.decode("latin-1")
            parsed[k] = v
        except Exception:
            continue
    return parsed


async def _send_json_error(
    send: Callable[[Dict[str, Any]], Any],
    status_code: int,
    detail: str,
    extra_headers: Optional[List[Tuple[bytes, bytes]]] = None,
) -> None:
    body = json.dumps({"detail": detail}).encode("utf-8")
    headers: List[Tuple[bytes, bytes]] = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode("latin-1")),
    ]
    if extra_headers:
        headers.extend(extra_headers)
    await send({
        "type": "http.response.start",
        "status": status_code,
        "headers": headers,
    })
    await send({
        "type": "http.response.body",
        "body": body,
    })


class TrustedHostControlMiddleware:
    """
    ASGI middleware enforcing Host header validation against settings.allowed_hosts_list
    whenever the service is exposed beyond strict localhost bindings.
    """

    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        scope_type = scope.get("type")
        if scope_type not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        if not settings.is_exposed_beyond_localhost:
            await self.app(scope, receive, send)
            return

        headers = _parse_asgi_headers(scope.get("headers"))
        host_val = headers.get("host")
        if is_host_allowed(host_val, settings.allowed_hosts_list):
            await self.app(scope, receive, send)
            return

        if scope_type == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return

        await _send_json_error(send, status.HTTP_400_BAD_REQUEST, "Invalid host header.")


class RateLimitMiddleware:
    """
    ASGI middleware applying tiered sliding-window per-IP rate limits:
    - 'auth' tier for login, registration, and magic-link redemption.
    - 'compute' tier for forecasting, LOS physics, rollups, optimization, and scenarios.
    """

    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        if scope.get("type") != "http" or not getattr(settings, "RATE_LIMIT_ENABLED", True):
            await self.app(scope, receive, send)
            return

        method = str(scope.get("method", "GET")).upper()
        if method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        path = str(scope.get("path", "/"))
        tier: Optional[str] = None
        limit = 0
        window_sec = 60

        if is_auth_rate_limited_path(path):
            tier = "auth"
            limit = int(getattr(settings, "RATE_LIMIT_AUTH_REQUESTS", 30))
            window_sec = int(getattr(settings, "RATE_LIMIT_AUTH_WINDOW_SEC", 60))
            scope_state = scope.setdefault("state", {})
            if isinstance(scope_state, dict):
                scope_state["rate_limit_checked_auth"] = True
        elif is_heavy_compute_path(path):
            tier = "compute"
            limit = int(getattr(settings, "RATE_LIMIT_COMPUTE_REQUESTS", 120))
            window_sec = int(getattr(settings, "RATE_LIMIT_COMPUTE_WINDOW_SEC", 60))

        if tier is None:
            await self.app(scope, receive, send)
            return

        client_tuple = scope.get("client")
        client_host = str(client_tuple[0]) if client_tuple and len(client_tuple) > 0 else "unknown"
        headers = _parse_asgi_headers(scope.get("headers"))
        client_ip = extract_client_ip_from_headers_and_client(client_host, headers)

        allowed, remaining, retry_after = rate_limiter.check_and_consume(
            tier=tier,
            client_ip=client_ip,
            limit=limit,
            window_seconds=window_sec,
        )
        if not allowed:
            extra = [
                (b"retry-after", str(retry_after).encode("latin-1")),
                (b"x-ratelimit-limit", str(limit).encode("latin-1")),
                (b"x-ratelimit-remaining", b"0"),
            ]
            await _send_json_error(
                send,
                status.HTTP_429_TOO_MANY_REQUESTS,
                f"Rate limit exceeded for {tier} endpoint. Retry after {retry_after} seconds.",
                extra_headers=extra,
            )
            return

        async def send_with_headers(message: Dict[str, Any]) -> None:
            if message.get("type") == "http.response.start":
                raw_hdrs = list(message.get("headers", []))
                raw_hdrs.append((b"x-ratelimit-limit", str(limit).encode("latin-1")))
                raw_hdrs.append((b"x-ratelimit-remaining", str(remaining).encode("latin-1")))
                message = {**message, "headers": raw_hdrs}
            await send(message)

        await self.app(scope, receive, send_with_headers)


def enforce_auth_rate_limit(request: Request) -> None:
    """
    FastAPI route dependency enforcing per-IP auth rate limiting cleanly
    even when auth.router is mounted independently of the root middleware stack.
    Avoids double counting when RateLimitMiddleware already validated the request.
    """
    if not getattr(settings, "RATE_LIMIT_ENABLED", True):
        return
    if getattr(request.state, "rate_limit_checked_auth", False):
        return

    client_host = request.client.host if request.client else "unknown"
    headers = {k.lower(): v for k, v in request.headers.items()}
    client_ip = extract_client_ip_from_headers_and_client(client_host, headers)
    limit = int(getattr(settings, "RATE_LIMIT_AUTH_REQUESTS", 30))
    window_sec = int(getattr(settings, "RATE_LIMIT_AUTH_WINDOW_SEC", 60))

    allowed, _remaining, retry_after = rate_limiter.check_and_consume(
        tier="auth",
        client_ip=client_ip,
        limit=limit,
        window_seconds=window_sec,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for auth endpoint. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
