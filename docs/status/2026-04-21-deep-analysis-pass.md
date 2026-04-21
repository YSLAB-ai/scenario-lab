## Deep Analysis Pass

Date: 2026-04-21

### Verified Scope

- Added deterministic replay-suite support through `forecast-harness run-replay-suite`.
- Added root-route-aware scenario family synthesis and richer generated reports.
- Deepened evidence-conditioned modeling in:
  - `interstate-crisis`
  - `company-action`
- Re-ran the realistic 10-scenario smoke campaign after those changes.

### Verified Outcomes

- Full test suite:
  - `packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `193 passed`
- The realistic smoke campaign still completed end to end across all 10 scenarios.
- The interstate scenarios no longer converged on a single root strategy:
  - `US-Iran Gulf` -> `Alliance consultation (coordinated signaling)`
  - `Japan-China Strait` -> `Signal resolve (managed signal)`
  - `India-Pakistan crisis` -> `Signal resolve (backchannel opening)`
- The company scenarios no longer converged on a single root strategy:
  - `Apple CEO transition` -> `Stakeholder reset`
  - `Boeing post-reporting` -> `Contain message (message lands)`

### Changes Made

- `interstate-crisis` now infers and uses:
  - `alliance_pressure`
  - `mediation_window`
  - `geographic_flashpoint`
- `company-action` now infers and uses:
  - `board_cohesion`
  - `operational_stability`
- Scenario-family grouping now keeps distinct root routes separate instead of collapsing only by terminal phase.
- Reports now expose:
  - scenario families
  - top-branch path detail
  - search summary metadata

### Remaining Gap

- The repo now produces more differentiated and internally coherent analyses, but the built-in domain packs are still heuristic templates rather than validated forecasting models.
