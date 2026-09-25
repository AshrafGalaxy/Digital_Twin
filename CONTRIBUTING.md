# Contributing to Digital Twin

Welcome! We are a 5-member college project team collaborating on this **Digital Twin** platform. This document establishes guidelines, architectural invariants, and collaborative workflows for our team.

---

## 1. Team Code of Conduct

As classmates collaborating on this joint project, all team members follow our [Team Code of Conduct & Working Agreement](CODE_OF_CONDUCT.md). We prioritize open communication, mutual respect, peer support, and academic/engineering integrity across all contributions.

---

## 2. Core Architectural Invariants

Every contribution must honor the non-negotiable architectural principles established in [AGENTS.md](AGENTS.md):

1. **System of Record Invariant:** PostgreSQL/TimescaleDB (or resilient local SQLite engine in WAL mode) is the authoritative persistence layer. MQTT is strictly a transport bus.
2. **State Separation Invariant:** Observed (`LIVE`/`REPLAY`), `SIMULATION`, and `PREDICTED` state classes are strictly partitioned into distinct tables and schemas. Simulation and prediction outputs must **never** overwrite or mutate observed twin state.
3. **Strict Non-Actuation:** The platform is a read-only municipal decision-support system. Recommendations are advisory and require human authorization outside the platform prior to any field action.
4. **Mandatory Provenance:** Every dynamic telemetry record, forecast, or simulation result returned via APIs or displayed in the UI must specify `sourceMode`, `observedAt`/`generatedAt`, unit, and quality status.
5. **Data Honesty:**
   - Never label historical or simulated telemetry as `LIVE`.
   - Never represent simulation outputs as guaranteed commuter outcomes.
   - Never call external benchmark datasets live building meter observations.
6. **Strictly No Emojis:** Do not use emojis in UI components, toolbars, buttons, badges, tables, tooltips, or alerts. Use Lucide React vector icons or clear, professional typography instead.

---

## 3. Development Environment Setup

### Prerequisites

- **Python:** 3.11.x
- **Node.js:** 22.x (Active LTS) with npm 10+
- **Git:** 2.40+
- **Docker & Docker Compose:** (Optional, for containerized services like Mosquitto or TimescaleDB)

### Step-by-Step Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/AshrafGalaxy/Digital_Twin.git
   cd Digital_Twin
   ```

2. **Backend Setup (Python):**
   ```bash
   # Create virtual environment
   python -m venv .venv

   # Activate virtual environment
   # On Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source .venv/bin/activate

   # Install dependencies
   pip install --upgrade pip
   pip install -r backend/requirements.txt
   ```

3. **Frontend Setup (Node.js):**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Environment Variables:**
   Copy `.env.example` to `.env` if local customizations are required:
   ```bash
   cp .env.example .env
   ```

5. **Start Development Services:**
   - **Windows PowerShell (One-Click):**
     ```powershell
     .\start_dev.ps1
     ```
   - **Manual Start:**
     - Backend: `uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload`
     - Frontend: `npm --prefix frontend run dev`
   - **Docker Compose:**
     ```bash
     docker compose up -d
     ```

6. **Access Interfaces:**
   - Operations Dashboard: http://localhost:5173
   - Interactive API Docs: http://localhost:8000/docs
   - System Health Check: http://localhost:8000/health

---

## 4. Branching & Git Workflow

We follow a structured trunk-based feature branching model:

### Branch Naming Conventions

Always branch from the latest `main`:

```bash
git checkout main
git pull origin main
git checkout -b <type>/<short-description>
```

Approved branch prefix types:
- `feat/`: New feature or capability (e.g., `feat/webster-signal-optimizer`)
- `fix/`: Bug fix or defect correction (e.g., `fix/quarantine-filter-bounds`)
- `docs/`: Documentation additions or revisions (e.g., `docs/contributing-guidelines`)
- `refactor/`: Code improvements without behavior changes (e.g., `refactor/scenario-cache`)
- `test/`: New automated test suites or fixture improvements (e.g., `test/conformal-bounds`)
- `chore/`: Build configurations, dependencies, or repository hygiene (e.g., `chore/upgrade-deps`)

### Commit Message Conventions

Commit messages must be concise, imperative, and follow standard conventional commit syntax:

- Format: `<type>(<scope>): <subject>` or `<type>: <subject>`
- Maximum length: Under 60 characters
- **Rule:** Strictly NEVER include the word `phase` or phase numbers (e.g., do not use `Phase 8` or `P4B`).

**Examples:**
```text
feat(scenarios): add coordination offset support to studio
fix(schemas): harmonize scenarioTemplateId in run request
docs: add contributing guidelines and code of conduct
test(eval): add multi-horizon benchmark verification
```

---

## 5. Coding & Quality Standards

### Python & Backend Standards
- Target **Python 3.11**.
- Write typed Python using type hints (`typing.Optional`, `typing.List`, `typing.Dict`).
- Use **Pydantic v2** models for request/response serialization and validation.
- All database queries must be parameter-bound to prevent SQL injection.
- Ensure asynchronous endpoints and database transactions handle rollback cleanly.
- Never check in temporary or throwaway scripts to `scripts/`. Keep scripts intentional and documented.

### Frontend & UI Standards
- Built with **React 18**, **TypeScript**, and **Vite**.
- Strict TypeScript: Ensure zero `any` leaks where types can be defined.
- Design System: Dark-mode-first aesthetic with slate/zinc neutral tones, cyan/indigo telemetry accents, and crisp borders.
- Iconography: Use **Lucide React** vector icons exclusively. Never use emojis.
- Resilience: Implement explicit loading, empty, and error fallback states for all widgets and panels.

---

## 6. Testing & CI Requirements

Before submitting code for review or pushing to GitHub, you must verify that all automated checks pass locally.

### 1. Pytest Test Suite
Run the test suite with hermetic isolation:
```bash
# Using local virtual environment
.\.venv\Scripts\pytest.exe tests/ -v
```
- 100% test pass rate is mandatory.
- Tests must be order-invariant and hermetic (never depend on existing `.db` files).

### 2. Frontend Type-Check & Bundle Build
```bash
npm --prefix frontend run build
```
- Must compile cleanly with 0 TypeScript errors.

### 3. Repository Hygiene
- Delete transient caches (`__pycache__`, `.pytest_cache`, `dist/`) before committing.
- Ensure no sensitive credentials, `.env` files, or `.db` files are staged.

---

## 7. Pull Request Process

1. **Open a Pull Request:** Push your feature branch and open a PR against `main`.
2. **PR Description:** Fill out the pull request template describing:
   - What changes were made and why
   - How architectural invariants and state separation are preserved
   - Verification commands executed (pytest results, frontend build)
3. **Automated CI Validation:** GitHub Actions CI must pass:
   - Backend & Simulation Tests (`pytest tests/ -v`)
   - Frontend TypeScript & Vite Build (`npm run build`)
   - GIS Corridor Assets & Data Manifest Integrity
4. **Peer Review:** At least one review approval is required prior to merging.
5. **Merge Strategy:** Use **Squash and Merge** or **Rebase and Merge** to maintain a clean git history.

---

## 8. Questions and Contact

For questions, architectural guidance, or feature suggestions:
- Check existing documentation in [docs/architecture.md](docs/architecture.md) and [PRD.md](PRD.md).
- Browse future task roadmaps in [FuturePlans/](FuturePlans/) and [docs/tasks/](docs/tasks/).
- Open an Issue using our domain task template.
