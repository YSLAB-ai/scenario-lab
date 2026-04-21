# Replay Corpus Structure Pass

Date: 2026-04-21

## Verified Scope

- Split the built-in replay library into domain-scoped files under `knowledge/replays/`.
- Added typed corpus-summary loading through `forecasting_harness.knowledge`.
- Added CLI support for inspecting the built-in replay corpus structure directly.

## Verified Outcomes

- Full test suite:
  - `packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `197 passed`
- Replay-library tests:
  - `packages/core/.venv/bin/python -m pytest packages/core/tests/test_replay_library.py -q`
  - Result: `3 passed`
- Direct corpus-summary verification:
  - `forecast-harness summarize-builtin-replay-corpus`
  - `case_count = 10`
  - `files = 6`
  - `domain_counts["interstate-crisis"] = 3`
  - `domain_counts["company-action"] = 2`
- Direct calibration verification still remained green after the split:
  - `forecast-harness summarize-replay-calibration`
  - `domains_needing_attention = []`

## Changes Made

- The replay corpus now lives in:
  - `knowledge/replays/interstate-crisis.json`
  - `knowledge/replays/company-action.json`
  - `knowledge/replays/election-shock.json`
  - `knowledge/replays/market-shock.json`
  - `knowledge/replays/regulatory-enforcement.json`
  - `knowledge/replays/supply-chain-disruption.json`
- The core now exposes a typed corpus summary with:
  - total case count
  - domains present
  - case counts by domain
  - case counts by replay file
- The CLI now exposes:
  - `forecast-harness summarize-builtin-replay-corpus`

## Remaining Gap

- The replay corpus is now structured to grow cleanly by domain, but it still contains only the current 10 curated cases and is not yet a broad historically anchored library.
