# Replay And Supply Pass

Date: 2026-04-21

## Verified Scope

- Deepened evidence-conditioned modeling in:
  - `election-shock`
  - `supply-chain-disruption`
- Expanded replay metrics to track:
  - exact `top_branch_accuracy`
  - coarser `root_strategy_accuracy`
  - per-domain breakdown metrics
- Fixed root-branch reporting so unvisited children do not outrank explored branches simply because their default score was `0.0`.

## Verified Outcomes

- Focused replay and smoke tests:
  - `packages/core/.venv/bin/python -m pytest packages/core/tests/test_replay.py packages/core/tests/test_smoke_campaign.py -q`
  - Result: `15 passed`
- Full test suite:
  - `packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `194 passed`
- Direct 10-scenario smoke rerun on 2026-04-21 verified these top branches:
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

- `election-shock` now infers and uses:
  - `coalition_fragility`
  - `donor_confidence`
- `supply-chain-disruption` now distinguishes `source` and `transport` disruption modes from approved evidence and lets those modes reshape both trigger-stage priors and follow-on transitions.
- Replay results now surface:
  - `root_strategy`
  - `expected_root_strategy`
  - `root_strategy_match`
  - `root_strategy_accuracy`
  - `domain_breakdown`
- Simulation branch ranking now prefers explored root branches before using deterministic fallback scores for unvisited children.

## Remaining Gap

- The replay scaffolding is now better aligned with how users read scenarios, but the repository still lacks a broad, curated historical replay library and a calibration loop that tunes domain-pack behavior against real outcomes.
