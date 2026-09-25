# Task 10: Human-in-the-Loop Operator Advisory & Audit Trail UI

- **Task Identifier:** `TASK-10`
- **Domain:** Intelligent Traffic Mobility & Adaptive Corridor Control
- **Specification Reference:** [`TRAFFIC_MANAGEMENT.md`](../../FuturePlans/TRAFFIC_MANAGEMENT.md) Section 9.1 & 9.2
- **Component / Scope:** Frontend & UI
- **Priority:** High
- **Type:** UI/UX & Governance Audit Workflow

---

## 1. Context & Objective

Per Non-Negotiable Architectural Invariant #3 (`AGENTS.md`):
> **Strict Non-Actuation:** The platform is read-only decision support. Recommendations are advisory and require human authorization outside the platform before any field action.

When the digital twin's analytics or simulation engines recommend a timing adjustment (e.g. green split extension, offset retiming for coordination, or transit priority), the platform must present a **rigorous decision-support dossier** to the municipal traffic dispatcher. 

This task implements the **Human-in-the-Loop Advisory & Audit Trail UI**. It displays the recommendation rationale, conformal uncertainty intervals, safety constraints checklist, and provides an audited authorization workflow that generates an official dispatch work order for field technicians.

---

## 2. UI/UX Architecture & Component Specification

### 2.1 Advisory Recommendation Dossier (`AdvisoryCard.tsx`)
1. **Action Proposal:** E.g., *"Extend Nagar Road EB Green Split by +10s at INT-VN-01 to accommodate queued platoon from Ramwadi"*.
2. **Predicted Corridor Impact:**
   - Saved Corridor Delay: $-18.4\%$ ($[-22.1\%, -14.2\%]$ 90% confidence interval).
   - Expected Queue Reduction: $-24.0\text{ meters}$.
   - Estimated Fuel Burn Reduction: $-32.5\text{ Liters/hour}$.
3. **XAI Feature Attribution Bar (`FeatureAttributionMiniChart.tsx`):**
   - Mini horizontal bar chart showing top-5 factors driving the recommendation (e.g., Upstream queue $+34\%$, Rain index $+12\%$, Cross-street demand $-18\%$).
4. **Safety Constraint Checklist:**
   - [x] Pedestrian walk phase preserved ($\ge 14\text{s}$).
   - [x] Maximum cross-street waiting time bounded ($< 90\text{s}$).
   - [x] No emergency vehicle preemption conflict.

### 2.2 Operator Authorization & Audit Workflow
- **Operator Signature:** Requires dispatcher Badge ID and brief operational notes.
- **Strict Non-Actuation Enforcement:**
  - Clearly displays: *"Advisory Decision Support Only. No direct physical actuator signal is emitted."*
  - Action button: `Generate Municipal Dispatch Order` (instead of "Execute" or "Apply").
- **Audit Persistence:**
  - Submits to `POST /api/v1/advisories/{id}/authorize`.
  - Generates immutable record in `advisory_audit_log` table with SHA-256 hash.
  - Allows instant export of municipal dispatch ticket as formatted JSON / print-ready PDF.

### 2.3 Strict Aesthetic & Iconography Rules
- **Strictly Zero Emojis:** Use Lucide React icons (`ShieldCheck`, `FileText`, `CheckCircle2`, `AlertTriangle`, `TrendingDown`, `UserCheck`).
- Clean control-room typography with muted borders and badge pills.

---

## 3. Data Contracts & State Types

```typescript
export interface CorridorAdvisory {
  advisoryId: string;
  intersectionId: string;
  recommendedAction: string;
  proposedChange: {
    phaseId: number;
    parameter: 'greenSplitSec' | 'offsetSec' | 'cycleLengthSec';
    currentValue: number;
    recommendedValue: number;
  };
  predictedImpact: {
    delayDeltaPct: number;
    delayDeltaCI: [number, number];
    queueDeltaMeters: number;
    fuelSavedLitersPerHr: number;
  };
  safetyChecklist: {
    pedestrianPhaseSafe: boolean;
    maxWaitThresholdSafe: boolean;
    emergencyPreemptionClear: boolean;
  };
  topFeatures: Array<{ feature: string; impact: number }>;
  generatedAt: string;
  provenance: {
    sourceMode: 'PREDICTED' | 'SIMULATION';
    modelId: string;
  };
}
```

---

## 4. Implementation Steps

1. **Build Dossier Component (`frontend/src/components/advisory/AdvisoryCard.tsx`):**
   - Render impact metrics, confidence bounds, and safety checks.
2. **Build Feature Attribution Mini-Chart (`frontend/src/components/advisory/FeatureAttributionMiniChart.tsx`):**
   - Render SVG/HTML bars for positive/negative SHAP values.
3. **Build Authorization Modal (`frontend/src/components/advisory/AuthorizeAdvisoryModal.tsx`):**
   - Form capturing dispatcher ID, shift ID, and authorization comment.
   - Confirmation dialog reinforcing non-actuation protocol.
4. **Wire into Scenario Studio & Live Control Room (`ScenarioStudioView.tsx`, `ControlRoomView.tsx`):**
   - Provide "View Advisory Details" button on high-impact scenario outcomes.
5. **Build Verification:**
   - Execute `npm run build` to verify clean compilation with 0 TypeScript/ESLint warnings.

---

## 5. Verification & Acceptance Criteria

- [ ] Clear disclaimer stating decision support / non-actuation nature of the system.
- [ ] Conformal confidence intervals and SHAP attribution bars render crisply.
- [ ] Authorization generates an audited dispatch record with 0 emojis.
- [ ] Clean build: `npm run build` exits with code 0.
