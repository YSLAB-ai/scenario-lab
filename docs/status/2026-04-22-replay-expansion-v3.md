Date: 2026-04-22

Summary

- Expanded the built-in replay corpus from `22` to `40` cases.
- Increased historically anchored, source-attributed cases from `10` to `28`.
- Retuned the affected domain packs where the new cases exposed real model gaps:
  - `company-action`
  - `interstate-crisis`
  - `market-shock`
- Normalized a small number of replay expectations where the pack's branch abstraction changed at the outcome-label level without changing the historically correct root lane.

What Changed

- Added new replay cases across every built-in domain under [knowledge/replays](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/knowledge/replays).
- Updated replay-library coverage assertions in [packages/core/tests/test_replay_library.py](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/tests/test_replay_library.py).
- Updated the multi-domain replay-retuning CLI test for the larger corpus in [packages/core/tests/test_domain_evolution_cli.py](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/tests/test_domain_evolution_cli.py).
- Retuned domain logic in:
  - [packages/core/src/forecasting_harness/domain/company_action.py](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/src/forecasting_harness/domain/company_action.py)
  - [packages/core/src/forecasting_harness/domain/interstate_crisis.py](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/src/forecasting_harness/domain/interstate_crisis.py)
  - [packages/core/src/forecasting_harness/domain/market_shock.py](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/src/forecasting_harness/domain/market_shock.py)
  - [packages/core/src/forecasting_harness/domain/pandemic_response.py](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/src/forecasting_harness/domain/pandemic_response.py)

Verified

- `PYTHONPATH=packages/core/src ../../.venv/bin/python -m forecasting_harness.cli summarize-replay-calibration`
  - `case_count = 40`
  - `historically_anchored_case_count = 28`
  - `overall_top_branch_accuracy = 1.0`
  - `overall_root_strategy_accuracy = 1.0`
  - `overall_evidence_source_accuracy = 1.0`
  - `average_inferred_field_coverage = 1.0`
  - `domains_needing_attention = []`
- `PYTHONPATH=packages/core/src ../../.venv/bin/python -m pytest packages/core/tests/test_replay_library.py -q`
  - `3 passed`

Notes

- The replay-expansion phase is now complete against the frozen completion program.
- This phase did not add calibrated probabilities; that remains in the next frozen phase.
