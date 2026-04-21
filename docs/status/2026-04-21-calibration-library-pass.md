# Calibration Library Pass

Date: 2026-04-21

## Verified Scope

- Added a repo-owned replay library under `knowledge/replays/builtin-cases.json`.
- Added typed replay-library loading through `forecasting_harness.knowledge`.
- Added deterministic calibration reporting on top of replay results.
- Added CLI commands:
  - `forecast-harness run-builtin-replay-suite`
  - `forecast-harness summarize-replay-calibration`

## Verified Outcomes

- Full test suite:
  - `packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `197 passed`
- Replay-library tests:
  - `packages/core/.venv/bin/python -m pytest packages/core/tests/test_replay_library.py -q`
  - Result: `3 passed`
- Direct calibration CLI verification:
  - `forecast-harness run-builtin-replay-suite`
  - `case_count = 10`
  - `top_branch_accuracy = 1.0`
  - `root_strategy_accuracy = 1.0`
  - `evidence_source_accuracy = 1.0`
  - `average_inferred_field_coverage = 1.0`
- Direct calibration summary verification:
  - `forecast-harness summarize-replay-calibration`
  - `domains_needing_attention = []`
- Direct 10-scenario smoke rerun on the same pass still produced:
  - `US-Iran Gulf` -> `Alliance consultation (coordinated signaling)`
  - `Japan-China Strait` -> `Signal resolve (managed signal)`
  - `India-Pakistan crisis` -> `Signal resolve (backchannel opening)`
  - `Apple CEO transition` -> `Stakeholder reset`
  - `Boeing post-reporting` -> `Contain message (message lands)`
  - `Election debate collapse` -> `Message reset (reset holds)`
  - `Market rate shock` -> `Emergency liquidity`
  - `Regulator ad-tech` -> `Internal remediation`
  - `Supply rare-earth` -> `Expedite alternatives`
  - `Supplier flooding` -> `Reserve logistics`

## Changes Made

- Replay calibration now has a repo-owned default corpus instead of relying on hand-authored JSON for every run.
- Calibration reporting now summarizes:
  - overall top-branch accuracy
  - overall root-strategy accuracy
  - overall evidence-source accuracy
  - average inferred-field coverage
  - strongest and weakest domains
  - domains needing attention
- The knowledge package now lazy-loads replay cases to avoid circular imports when the workflow and replay layers both touch shared knowledge code.

## Remaining Gap

- The calibration layer now has a deterministic, repo-owned baseline, but the library is still only 10 curated cases and does not yet constitute a broad historical replay corpus or an automatic tuning loop against real outcomes.
