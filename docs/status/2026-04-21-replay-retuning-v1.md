# Replay Retuning V1

Date: 2026-04-21

## Summary

- Added a one-domain replay retuning loop: `forecast-harness run-replay-retuning`
- The loop accepts either built-in replay cases for a domain or a custom replay-case file.
- Replay misses now feed idempotent self-detected suggestions instead of appending duplicate suggestion rows on repeated runs.

## Verified Behavior

- `run-replay-retuning` returns a structured summary with:
  - `case_count`
  - `weak_case_count`
  - `generated_suggestion_count`
  - `calibration_summary`
  - `weakness_brief`
  - `evolution_summary`
- repeated `analyze_domain_weakness` calls for the same missed replay case now preserve one self-detected suggestion record instead of duplicating it
- the retuning loop stays one domain at a time and reuses the existing protected domain-evolution boundary

## Verification

- focused retuning tests:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core/tests/test_evolution_storage.py packages/core/tests/test_domain_evolution_service.py packages/core/tests/test_domain_evolution_cli.py -q`
  - result: `10 passed in 0.20s`
- full suite:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core -q`
  - result: `266 passed in 3.40s`
- direct custom-case retuning smoke through `run-replay-retuning --domain-pack company-action --input <file> --no-branch`
  - result:
    - `case_count = 1`
    - `weak_case_count = 1`
    - `generated_suggestion_count = 1`
    - `promotion_decision = promoted`

## Boundary

- this is a closed replay-to-suggestion-to-evolution loop for one domain at a time
- it does not yet retune multiple domains in one pass
- it does not yet provide a large historical replay library by itself
