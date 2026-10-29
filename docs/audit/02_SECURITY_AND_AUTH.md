# 02. Security and Authentication

## Summary

There are two separate authentication stacks:
- JWT in `backend/api/v1/endpoints/auth.py`
- HTTP Basic / API key in `backend/core/auth.py`

**Neither is enforced on any business endpoint.** `require_role` and `get_current_user` are defined in `backend/core/auth.py` (lines 45 and 76) and imported nowhere else. On the frontend, role checks are client-side only, and the JWT is never sent with API calls.

---

## Findings

### SEC-01 (CRITICAL) Mutating governance endpoints are unauthenticated
| Endpoint | File |
|---|---|
| `POST /api/v1/recommendations/{id}/authorize` | `backend/api/v1/endpoints/recommendations.py` ~167 |
| `POST /api/v1/recommendations/{id}/review`, `/dispatch-order` | same file |
| `POST /api/v1/energy/advisories/{id}/authorize` | `backend/api/v1/endpoints/energy.py` ~333 |
| `POST /api/v1/inquiries/{id}/approve` and `/reject` | `backend/api/v1/endpoints/inquiries.py` ~182 |
| `POST /api/v1/stream/simulator/control`, `/replay/control` | `backend/api/v1/endpoints/stream.py` ~154 |
| `POST /api/v1/energy/telemetry/tick`, `/power-balance/snapshot` | `energy.py` |
| `POST /api/v1/traffic/.../spat/ingest` | `traffic.py` |
| `POST /api/v1/analytics/rollups/compute` | `analytics.py` |

- **Impact:** Anyone who can reach the API can sign advisory authorizations (which makes the human-in-the-loop audit trail meaningless), approve access requests, mint magic links, and start or stop the data feed.
- **Fix:**
  - Add a single `Depends(require_role([...]))` per route.
  - Define a role matrix, for example: Viewer read-only; Analyst runs scenarios; Traffic/Energy Operator authorizes advisories in their own domain; Administrator approves inquiries and controls the feed.
  - Add tests that assert 401 without a token and 403 with the wrong role.

### SEC-02 (CRITICAL) Default JWT signing secret committed in source
- **Location:** `backend/api/v1/endpoints/auth.py` line 27: `JWT_SECRET_KEY = os.getenv("MUNICIPAL_JWT_SECRET", "pune-dt-corridor-key-2026-viman-nagar")`.
- **Impact:** If the env var is unset, anyone can forge tokens.
- **Fix:** Move the secret to `Settings` with no default, and fail startup when `ENVIRONMENT=production` and the secret is missing or shorter than 32 bytes. Rotate any secret that has ever been deployed.

### SEC-03 (CRITICAL) Hardcoded demo credentials
- **Location:**
  - `backend/api/v1/endpoints/auth.py` ~65-96 (`traffic123`, `energy123`, `audit123`, `analyst123`)
  - `backend/core/auth.py` ~29-33 (`admin123`, `analyst123`, `viewer123`)
  - `backend/core/auth.py` ~59 (`DEMO_API_KEY` default `twin-demo-secret-key-2026`)
  - `frontend/src/components/views/AuthPageView.tsx` ~49-81 (the same passwords shown in the UI)
  - `.env.example` line ~51
- **Fix:** Remove all in-source credentials. Create demo users only through a dev-only seed command that reads passwords from env. Remove the demo credential panel from the production UI build (gate it on `import.meta.env.DEV`).

### SEC-04 (CRITICAL) Open self-registration with role selection
- **Location:** `backend/api/v1/endpoints/auth.py` ~248-310 (`POST /auth/register`).
- **Impact:** Any client can register as `Municipal Analyst` or any operator role.
- **Fix:** Disable public registration. Access goes through the inquiry and approval flow only. If registration is kept, force the lowest role and require admin promotion.

### SEC-05 (CRITICAL) Inquiry approval mints magic links without authentication and returns the token
- **Location:** `backend/api/v1/endpoints/inquiries.py` ~182-220.
- **Fix:** Require the Administrator role. Deliver the link out of band (email via SMTP provider) and never return it in the response body. Store only a hash of the token.

### SEC-06 (CRITICAL) `AUTH_ENABLED` defaults to false, which grants admin
- **Location:** `backend/core/auth.py` ~53-56 (when auth is disabled, every caller is admin). `DEBUG` also defaults to true in `config.py`.
- **Fix:** Default `AUTH_ENABLED=true`. Refuse to start with auth disabled unless `ENVIRONMENT=development`.

### SEC-07 (CRITICAL) Frontend never sends credentials, and authorization is client-side only
- **Location:**
  - `frontend/src/App.tsx` ~174-225 (stores the whole `AuthUser`, including the JWT, in `localStorage`)
  - `frontend/src/services/api.ts` (no `Authorization` header anywhere)
  - `frontend/src/components/Header.tsx` ~42-58 (`ROLE_ALLOWED_TABS` is the only gate)
- **Fix:**
  - Add a single `apiFetch` wrapper that attaches `Authorization: Bearer <token>` and handles 401 by logging out.
  - Prefer an HttpOnly, Secure, SameSite=Strict cookie set by the backend over `localStorage` (this reduces XSS token theft).
  - Validate the session on load with `GET /auth/verify`.

### SEC-08 (HIGH) Hash routes bypass login, and the default role is Analyst
- **Location:** `frontend/src/App.tsx` ~214 (unauthenticated `userRole` defaults to `'Municipal Analyst'`); hash routes like `#operations` render without an auth check.
- **Fix:** Add a route guard. Unauthenticated users go to `#auth` and get no role.

### SEC-09 (HIGH) Inquiry listing exposes PII without authentication
- **Location:** `backend/api/v1/endpoints/inquiries.py` ~131 (`GET /inquiries` returns emails and organizations).
- **Fix:** Administrator only, with pagination.

### SEC-10 (HIGH) Magic-link expiry parse failure extends validity
- **Location:** `backend/api/v1/endpoints/auth.py` ~391-395 (sets `expires_at = now + 1 day` on parse error).
- **Fix:** Treat a parse failure as expired and reject. Store `expires_at` as `TIMESTAMPTZ`.

### SEC-11 (HIGH) WebSockets have no authentication
- **Location:** `backend/main.py` ~161-208 (`/ws/operations`, `/ws/system`, `/ws/scenarios`).
- **Fix:** Require a token in the first message or a cookie. Reject the connection with close code 4401 when it is missing.

### SEC-12 (HIGH) MQTT broker allows anonymous clients
- **Location:** `infrastructure/mosquitto/mosquitto.conf` line 28 (`allow_anonymous true`). Meanwhile `config.py` defines `MQTT_PASSWORD=twin_secret_dev`, which gives a false sense of security.
- **Impact:** Anyone on the network can publish forged LIVE telemetry, which the projector will accept.
- **Fix:** Set `allow_anonymous false`, use a password file or TLS client certs, and add an ACL that restricts publish topics per device.

### SEC-13 (MEDIUM) Weak password hashing parameters
- **Location:** `backend/api/v1/endpoints/auth.py` ~106 (PBKDF2 at 20k iterations).
- **Fix:** Use `argon2-cffi` (argon2id) or PBKDF2-SHA256 with at least 600k iterations.

### SEC-14 (MEDIUM) Custom JWT implementation
- **Location:** `backend/api/v1/endpoints/auth.py` (hand-rolled HS256 encode/verify).
- **Fix:** Use `PyJWT` with `algorithms=["HS256"]`, `exp`, `iat`, `nbf`, `iss` and `aud` validation, and a short expiry (15-60 min) plus refresh.

### SEC-15 (MEDIUM) Users, advisories and recommendations live in process memory
- **Location:** `REGISTERED_USERS` (`auth.py` ~100), `rule_engine._recommendations`, `energy_advisory_service._advisories`.
- **Impact:** A restart wipes accounts and authorization state, and multiple workers hold inconsistent state.
- **Fix:** Persist them to DB tables (see DB-06).

### SEC-16 (MEDIUM) No CORS guard against wildcard with credentials
- **Location:** `backend/main.py` ~99-104.
- **Fix:** Reject `*` when `allow_credentials=True` at startup.

### SEC-17 (MEDIUM) No rate limiting on login, register, magic link or inquiry endpoints
- **Fix:** Add `slowapi` or reverse-proxy rate limits (for example 5/min per IP on login).

### SEC-18 (LOW) Client-exposed Mapbox token
- **Location:** `frontend/.env` (gitignored), used in `MapOperationsView.tsx` and `CesiumCorridorViewer.tsx`.
- **Fix:** This is expected for Mapbox. Restrict the token by URL in the Mapbox dashboard.

### SEC-19 (LOW) No security headers
- **Fix:** Add CSP, HSTS, X-Content-Type-Options and Referrer-Policy at the reverse proxy or through middleware.

## Acceptance criteria
- `tests/test_auth_enforcement.py` asserts 401/403 for every mutating route (generated from the router table).
- Startup fails in production mode if the JWT secret or DB credentials are defaults.
- `rg "123\"|demo-secret|pune-dt-corridor-key" backend frontend/src` returns nothing.
