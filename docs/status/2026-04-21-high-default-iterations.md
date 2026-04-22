# High Default Iterations

Date: 2026-04-21

## Scope

This pass changed the user-facing simulation default without changing the replay and smoke baselines.

Changes:

- `forecast-harness simulate` now defaults to `10000` MCTS iterations
- `forecast-harness simulate --iterations N` now overrides the runtime budget per run
- the shared `SearchConfig` fallback default is now `10000`
- built-in domain-pack search configs remain unchanged so replay and smoke expectations stay stable

## Why This Boundary

The repo was already fast enough to support much larger interactive runs, but changing every pack default globally caused replay and smoke scenarios to drift away from their verified expectations.

So the accepted behavior is:

- interactive CLI simulation defaults to `10000`
- pack-specific internal defaults stay tuned for deterministic regression coverage

## Verification

- `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core -q`
  - `260 passed in 3.47s`
- `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core/tests/test_smoke_campaign.py -q`
  - `16 passed in 0.67s`
- `forecast-harness summarize-replay-calibration`
  - `overall_top_branch_accuracy = 1.0`
  - `overall_root_strategy_accuracy = 1.0`
  - `domains_needing_attention = []`
