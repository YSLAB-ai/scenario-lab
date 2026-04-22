# Knowledge Compiler V1

Date: 2026-04-22

## Summary

- Added a deterministic knowledge compiler in [packages/core/src/forecasting_harness/knowledge/compiler.py](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/src/forecasting_harness/knowledge/compiler.py).
- Approved revision artifacts can now be compiled into candidate:
  - evidence-category terms
  - semantic aliases
  - action-bias suggestions when the top action language is directly reinforced by approved evidence
- Replay misses can now be compiled into candidate:
  - action-bias suggestions
  - state-field term suggestions
- Compiler candidates are stored through the existing protected domain-evolution suggestion path with stable compiler-owned ids, so reruns are idempotent instead of duplicating rows.
- Added explicit CLI entrypoints:
  - `forecast-harness compile-revision-knowledge`
  - `forecast-harness compile-replay-knowledge`

## Boundary

- The compiler does not rewrite manifests or pack code directly.
- It only proposes reusable knowledge and routes those proposals into the existing domain-evolution store.
- Manifest mutation still happens later through `run-domain-evolution`, behind the protected review and replay gate.

## Verification

- Focused compiler/evolution tests:
  - `PYTHONPATH=packages/core/src .venv/bin/python -m pytest packages/core/tests/test_knowledge_compiler.py packages/core/tests/test_domain_evolution_service.py packages/core/tests/test_domain_evolution_cli.py -q`
  - `15 passed in 0.91s`
- Full suite:
  - `PYTHONPATH=packages/core/src .venv/bin/python -m pytest packages/core -q`
  - `296 passed in 9.96s`
- Checked-in smoke campaign:
  - `PYTHONPATH=packages/core/src .venv/bin/python -m pytest packages/core/tests/test_smoke_campaign.py -q`
  - `16 passed in 2.84s`
- Built-in replay retuning smoke:
  - `PYTHONPATH=packages/core/src .venv/bin/python -m forecasting_harness.cli run-builtin-replay-retuning --workspace-root /tmp/phase6-compiler-retune --no-branch`
  - returned:
    - `domain_count = 7`
    - `case_count = 40`
    - `weak_domain_count = 0`
    - `generated_suggestion_count = 0`
