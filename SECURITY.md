# Security Policy

## 1. Scope & System Classification

The **Digital Twin-Enabled Smart City Analytics Platform** is a read-only municipal decision-support and predictive intelligence system. The platform couples road network mobility, commercial electrical microgrids, and ambient air quality telemetry to provide operational awareness and what-if simulation capabilities for municipal authorities.

### Core Non-Actuation Invariant
The platform is architected with a strict non-actuation constraint: it possesses **zero physical actuation pathways**. It cannot trigger traffic signal controllers, trip electrical substation switchgear, or manipulate physical infrastructure. All recommendations produced by the platform are advisory decision-support dossiers requiring explicit human verification, physical authorization, and out-of-band execution by certified municipal engineers.

---

## 2. Active Development & Security Maintenance

The platform is under active development. Security updates and patches are continuously verified through automated CI quality gates and applied directly to the `main` branch.

---

## 3. Reporting a Vulnerability

We welcome security assessments, audits, and responsible vulnerability disclosures from researchers, municipal partners, and community members.

### Disclosure Protocol
- **Primary Reporting Channel:** Please submit vulnerabilities through **GitHub Private Vulnerability Reporting** via the repository's **Security** tab.
- **Alternative Contact:** If private vulnerability reporting is unavailable, contact the maintainers directly via repository issue triage with a private disclosure request.
- **Do Not Disclose Publicly:** To protect municipal deployments, please do not file public issues or share exploit artifacts publicly until a patch has been triaged, validated, and released.

### What to Include in a Report
To expedite triage, please provide:
1. A clear description of the vulnerability and the affected component (e.g. API endpoint, WebSocket stream, authentication guard, physical sanity bounds firewall).
2. Step-by-step reproduction instructions or a minimal proof of concept (PoC).
3. The potential impact, attack vector, and required privileges (e.g. unauthenticated, low-privilege operator, local attacker).
4. Any proposed remediation or patch.

### Response Timelines (SLA)
- **Acknowledgment:** Within 48 hours of initial report receipt.
- **Triage & Severity Assessment:** Within 5 business days, confirming reproducibility and impact.
- **Remediation & Patch:** Target patch release within 14 to 30 days depending on severity.
- **Public Disclosure:** Coordinated disclosure after the patch has been verified and deployed.

---

## 4. Platform Security Architecture & Invariants

The platform enforces five primary security defense layers:

### 4.1 Ingestion Guard & Physical Sanity Bounds Firewall
All incoming sensor telemetry ingested via MQTT or REST is passed through a strict Pydantic v2 validation layer:
- Packets with impossible physical properties (e.g. vehicle speed < 0 or > 120 km/h, negative active power, future timestamps) are quarantined immediately to `quarantine_observations` with an `INVALID` provenance tag.
- Quarantined payloads are isolated and never propagated to live state tables or analytics models.

### 4.2 Role-Based Access Control (RBAC) & Least Privilege
The API gateway and frontend shell enforce strict role segregation:
- **Traffic Operator:** Access to mobility maps, signal timing advisories, and queue metrics.
- **Grid Operator:** Access to single-line diagrams, substation bus power balance, and feeder headroom.
- **Environmental Analyst:** Access to CAAQMS sensor readings, dispersion plumes, and CPCB AQI analytics.
- **Municipal Commissioner:** Cross-domain executive view, scenario authorization, and compliance audit log inspection.
- **Civic Observer:** Public landing view and civic transparency reports.

All administrative endpoints and operational consoles require cryptographically signed JSON Web Tokens (JWT) using HS256/RS256 algorithms with explicit expiration timestamps.

### 4.3 State Separation & System of Record
- Ground truth observed telemetry (`LIVE`, `REPLAY`), physics simulations (`SIMULATION`), and machine learning predictions (`PREDICTED`) are stored in segregated database tables.
- Machine learning models and simulation engines have read-only access to observed data; predictive or simulated records can never overwrite observed twin reality.

### 4.4 Secrets & Credential Management
- No hardcoded secrets, database credentials, JWT private keys, or API tokens are checked into source control.
- Environment variables (`.env`) are strictly excluded by `.gitignore` and enforced via automated pre-commit and CI git hooks.
- Example templates (`.env.example`) contain only non-sensitive structural configuration placeholders.

### 4.5 Immutable Audit Logging
- Every advisory review, scenario execution, and authorization action produces an immutable audit record containing a SHA-256 integrity hash, operator identity, timestamp, and parameter payload.
- Audit records provide non-repudiation for municipal governance and compliance.

