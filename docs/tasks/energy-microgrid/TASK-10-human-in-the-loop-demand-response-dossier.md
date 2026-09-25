# Task 10: Human-in-the-Loop Demand-Response Advisory Dossier & Audit UI

- **Task Identifier:** `TASK-10`
- **Domain:** Energy Management & Microgrid Optimization
- **Specification Reference:** [`ENERGY_MANAGEMENT.md`](../../FuturePlans/ENERGY_MANAGEMENT.md) Section 9.2, 10, 11
- **Primary Assignee:** Engineer 5 (Frontend & Governance UI)
- **Priority:** High
- **Type:** UI/UX & Governance Audit Workflow

---

## 1. Context & Objective

Per Non-Negotiable Architectural Invariant #3 (`AGENTS.md`):
> **Strict Non-Actuation:** The platform is read-only decision support. Recommendations are advisory and require human authorization outside the platform before any field action.

When the digital twin's optimization engine suggests a battery discharge schedule, pre-cooling cycle, or peak curtailment action, the system must present a **transparent, evidence-backed decision dossier** to the chief facility engineer or microgrid operator.

This task implements the **Human-in-the-Loop Demand-Response Advisory Dossier & Audit UI** (`DemandResponseDossierModal.tsx`). It details the economic cost savings, battery cycle wear, grid safety interlock checks, and generates an audited, cryptographically hashed OpenADR / Modbus dispatch ticket upon dual-key operator authorization.

---

## 2. Visual Architecture & Component Specification

### 2.1 Advisory Dossier Card (`DemandResponseCard.tsx`)
1. **Proposed Dispatch Action:**
   - E.g. *"Discharge 450 kW from BESS-PHOENIX-01 and apply +1.0°C thermal setback to Food Court between 18:30–21:00 IST to avert ₹42,000 peak demand surcharge."*
2. **Economic & Carbon Impact Breakdown:**
   - Projected Net Cost Savings: ₹18,450.
   - Peak Demand Shaved: $-840\text{ kW}$ (from 6,120 kW down to 5,280 kW).
   - Battery Equivalent Degradation Wear: $0.082$ cycles.
   - Avoided Grid Carbon Emissions: $620\text{ kg CO}_2\text{e}$.
3. **Physical Safety Interlock Verification Checklist:**
   - [x] Feeder voltage within statutory limits ($415\text{V} \pm 6\%$).
   - [x] Inverter slew rate throttled $\le 10\%/\text{min}$.
   - [x] Battery SoC bounded ($32\% \ge SoC_{\min} = 20\%$).
   - [x] Zone indoor temperature preserves ASHRAE 55 comfort ($\le 25.5^\circ\text{C}$).

### 2.2 Dual-Key Authorization & Audit Trail
- **Operator Signature:** Requires Operator Name / Badge ID and optional justification notes.
- **Strict Non-Actuation Notice:**
  - Clearly displayed banner: *"Advisory Decision Support Only. Emits an audited OpenADR / Modbus dispatch work order. Local BMS/BESS safety logic remains authoritative."*
- **Action Button:** `Authorize Municipal Energy Dispatch Ticket`.
- **Audit Persistence:**
  - Calls `POST /api/v1/energy/advisories/{id}/authorize`.
  - Computes SHA-256 hash of the authorized payload and appends to the immutable audit trail.
  - Enables instant export of formatted dispatch ticket (JSON / print-ready PDF).

### 2.3 Strict Aesthetic Rules
- **Strictly No Emojis:** Use Lucide React vector icons (`ShieldCheck`, `Zap`, `CheckCircle2`, `FileText`, `AlertTriangle`, `TrendingDown`).
- **Dark Control-Room Design:** High contrast slate typography with clean borders.

---

## 3. Data Contracts & State Types

```typescript
export interface EnergyAdvisoryDossier {
  advisoryId: string;
  facilityId: string;
  facilityName: string;
  generatedAt: string;
  recommendedAction: string;
  projectedSavingsInr: number;
  peakReductionKw: number;
  batteryWearCycles: number;
  safetyChecks: {
    voltageCompliant: boolean;
    rampRateCompliant: boolean;
    socBounded: boolean;
    comfortPreserved: boolean;
  };
  schedule: Array<{
    timeSlot: string;
    bessAction: 'CHARGE' | 'DISCHARGE' | 'IDLE';
    bessKw: number;
    hvacSetbackDeltaC: number;
  }>;
  status: 'PENDING_REVIEW' | 'AUTHORIZED' | 'REJECTED' | 'EXPIRED';
  auditHash?: string;
}
```

---

## 4. Step-by-Step Implementation Guide

1. **Modal Component:** Build `frontend/src/components/Energy/DemandResponseDossierModal.tsx`.
2. **Impact Breakdown Widget:** Implement financial and carbon savings comparative charts.
3. **Safety Verification Section:** Render dynamic interlock compliance indicators.
4. **Backend Authorization Endpoint:** Implement `POST /api/v1/energy/advisories/{id}/authorize` in `backend/api/v1/endpoints/recommendations.py`.
5. **Automated Tests:** Add component tests and backend audit trail tests in `tests/test_energy_advisory_audit.py`.

---

## 5. Architectural Invariants Checklist (`AGENTS.md`)
- [ ] **Strict Non-Actuation Invariant:** Dispatches require human confirmation; platform never actuates field devices autonomously.
- [ ] **Strictly Zero Emojis:** Zero emojis in components, buttons, tooltips, or modals.
- [ ] **Clean Build:** `npm --prefix frontend run build` completes with 0 errors.
