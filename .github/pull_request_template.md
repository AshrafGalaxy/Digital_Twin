## Description
<!-- Provide a clear summary of the changes and the problem/feature they address. -->

## Changes Included
- 

## Architectural Invariants Checklist
<!-- Please check all that apply -->
- [ ] **State Separation Invariant:** Observed (`LIVE`/`REPLAY`), `SIMULATION`, and `PREDICTED` records remain strictly isolated. Predictions/simulations do not overwrite observed state.
- [ ] **Strict Non-Actuation:** Recommendations are advisory decision support and require external human authorization.
- [ ] **Mandatory Provenance:** Dynamic outputs include `sourceMode`, `observedAt`/`generatedAt`, unit, and quality status.
- [ ] **Zero Emojis:** No emojis are present in UI components, toolbars, buttons, badges, tables, tooltips, or alerts (vector icons or plain text only).
- [ ] **Data Honesty:** No replayed data is labeled "live", and simulation outputs are accurately classified.

## Verification & Testing
- [ ] `pytest tests/` executed locally (100% pass rate).
- [ ] `npm --prefix frontend run build` executed locally (0 TypeScript/Vite errors).
- [ ] Hermetic isolation verified (independent of local database artifacts).

## Related Issues
<!-- Link related issues or domain task references (e.g., Fixes #12, References TASK-01) -->
