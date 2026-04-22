# Replay Retuning V2

Date: 2026-04-21

## Scope

- Broadened the built-in replay/history corpus with four additional historically anchored cases:
  - `boeing-max9-2024`
  - `south-africa-gnu-2024`
  - `uk-gilt-intervention-2022`
  - `td-bank-aml-2024`
- Added multi-domain built-in replay retuning through:
  - `forecast-harness run-builtin-replay-retuning`
- Retuned `election-shock` coalition-shaping behavior so real coalition bargaining can outrank a pure discipline-message path when the case is actually about cross-party dealmaking.

## Files Changed

- `knowledge/replays/company-action.json`
- `knowledge/replays/election-shock.json`
- `knowledge/replays/market-shock.json`
- `knowledge/replays/regulatory-enforcement.json`
- `packages/core/src/forecasting_harness/cli.py`
- `packages/core/src/forecasting_harness/domain/election_shock.py`
- `packages/core/src/forecasting_harness/evolution/service.py`
- `packages/core/src/forecasting_harness/knowledge/__init__.py`
- `packages/core/src/forecasting_harness/knowledge/replays.py`
- `packages/core/tests/test_domain_evolution_cli.py`
- `packages/core/tests/test_domain_templates.py`
- `packages/core/tests/test_replay_library.py`

## Verified Results

- Full suite:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `270 passed in 4.08s`
- Checked-in smoke campaign:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core/tests/test_smoke_campaign.py -q`
  - Result: `16 passed in 0.63s`
- Targeted replay/retuning coverage:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core/tests/test_domain_templates.py packages/core/tests/test_replay_library.py packages/core/tests/test_domain_evolution_cli.py -q`
  - Result: `21 passed in 1.64s`
- Built-in replay summary:
  - `case_count = 22`
  - `anchored_case_count = 10`
  - `domains = 7`
- Built-in calibration summary:
  - `overall_top_branch_accuracy = 1.0`
  - `overall_root_strategy_accuracy = 1.0`
  - `overall_evidence_source_accuracy = 1.0`
  - `average_inferred_field_coverage = 1.0`
  - `domains_needing_attention = []`
- Built-in retuning smoke:
  - `domain_count = 7`
  - `case_count = 22`
  - `weak_domain_count = 0`
  - `generated_suggestion_count = 0`

## Notes

- The new election replay case initially exposed a real calibration gap: in `election-shock`, `Targeted deal` was structurally available during `coalition-shaping` but still ranked just below `Discipline message` under the shared balanced-system lens.
- That gap was corrected by retuning the `targeted-deal` transition so a real coalition deal produces slightly better systemic stability than a pure discipline message in the coalition phase.
- The multi-domain retuning command preserves the existing protected domain-evolution boundary by aggregating per-domain retuning runs instead of mutating multiple domains in one evolution pass.
