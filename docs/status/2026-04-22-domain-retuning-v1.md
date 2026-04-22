# 2026-04-22 Domain Retuning V1

## Summary

Phase 7 of the fixed repo completion program landed on the accepted branch. This pass tightened the protected replay-retuning loop and used the 40-case replay corpus to deepen the weakest replay-justified packs first instead of adding speculative new behavior.

## Verified Changes

- `forecast-harness run-replay-retuning` and `forecast-harness run-builtin-replay-retuning` now treat these as first-class weak-case signals:
  - top-branch mismatches
  - root-strategy mismatches
  - evidence-source mismatches
  - inferred-field coverage below `1.0` when a case declares expected fields
- Built-in retuning now rejects mixed-domain replay payloads so the protected one-domain boundary is enforced by code rather than convention.
- Promotion decisions now reject regressions in:
  - top-branch accuracy
  - root-strategy accuracy
  - evidence-source accuracy
  - inferred-field coverage
- Built-in retuning now returns `prioritized_domains`, ordered from weaker replay-calibration surfaces to stronger ones using replay metrics and compiler candidate counts.
- `election-shock` was deepened with a replay-justified `governing_math_pressure` field and richer coalition-shaping transitions.
- `market-shock` was deepened with a replay-justified `institutional_fragility` field and richer resolution-package transitions.
- The checked-in smoke campaign gained two dedicated phase-7 regressions:
  - `election-hung-parliament`
  - `market-bank-rescue`

## Verification

- `PYTHONPATH=packages/core/src ../../.venv/bin/python -m pytest packages/core -q`
  - `308 passed in 9.33s`
- `PYTHONPATH=packages/core/src ../../.venv/bin/python -m forecasting_harness.cli summarize-replay-calibration`
  - `case_count = 40`
  - `historically_anchored_case_count = 28`
  - `overall_top_branch_accuracy = 1.0`
  - `overall_root_strategy_accuracy = 1.0`
  - `overall_evidence_source_accuracy = 1.0`
  - `average_inferred_field_coverage = 1.0`
  - `failure_type_counts = {}`
  - `attention_items = []`
- `PYTHONPATH=packages/core/src ../../.venv/bin/python -m forecasting_harness.cli run-builtin-replay-retuning --workspace-root /tmp/phase7-retuning-verify-2 --no-branch`
  - `domain_count = 7`
  - `case_count = 40`
  - `weak_domain_count = 0`
  - `generated_suggestion_count = 0`

## Boundary

This pass deepened selected accepted packs and the protected retuning loop. It did not claim that the built-in packs are now mature validated forecasting models, and it did not change the later frozen completion tasks for richer new-domain synthesis or packaged local Codex/Claude integrations.
