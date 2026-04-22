# Replay Calibration V2

Date: 2026-04-21

## Scope

This pass strengthened the repo-owned replay and calibration surface instead of adding more workflow scaffolding.

Changes:

- expanded the built-in replay corpus from `12` to `18` cases
- added `6` source-attributed historically anchored cases
- added replay catalog listing support
- added structured calibration attention reporting

## Implementation

Core code:

- `packages/core/src/forecasting_harness/replay.py`
- `packages/core/src/forecasting_harness/knowledge/replays.py`
- `packages/core/src/forecasting_harness/knowledge/__init__.py`
- `packages/core/src/forecasting_harness/cli.py`

Replay corpus updates:

- `knowledge/replays/company-action.json`
- `knowledge/replays/interstate-crisis.json`
- `knowledge/replays/market-shock.json`
- `knowledge/replays/pandemic-response.json`
- `knowledge/replays/regulatory-enforcement.json`
- `knowledge/replays/supply-chain-disruption.json`

Tests:

- `packages/core/tests/test_replay.py`
- `packages/core/tests/test_replay_library.py`

## New Historical Cases

- `openai-governance-crisis-2023`
- `taiwan-drills-2022`
- `svb-btfp-2023`
- `omicron-boosters-2021`
- `binance-settlement-2023`
- `baltimore-port-closure-2024`

## Verification

Replay-focused tests:

- `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core/tests/test_replay.py packages/core/tests/test_replay_library.py -q`
- result: `8 passed`

Built-in replay corpus summary:

- `forecast-harness summarize-builtin-replay-corpus`
- result:
  - `case_count = 18`
  - `anchored_case_count = 6`

Built-in replay calibration summary:

- `forecast-harness summarize-replay-calibration`
- result:
  - `overall_top_branch_accuracy = 1.0`
  - `overall_root_strategy_accuracy = 1.0`
  - `historically_anchored_case_count = 6`
  - `failure_type_counts = {}`
  - `domains_needing_attention = []`

## Result

The replay system is still not a broad historical benchmark, but it is now materially more useful for validation:

- replay cases can carry explicit provenance
- reviewers can list the built-in corpus directly from the CLI
- calibration output can now identify concrete failing cases when the suite is not green
- the built-in corpus now covers more realistic historical situations without requiring changes to the shared search algorithm
