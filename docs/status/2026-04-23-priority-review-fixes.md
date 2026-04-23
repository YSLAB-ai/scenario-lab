# Priority Review Fixes

Date: 2026-04-23

## Scope

This pass implemented only the two highest-risk defects from the latest runtime review:

- behavior-profile inference leakage in the workflow compiler
- replay-confidence fallback presentation that could outrank real replay-backed buckets in the report surface

Everything else from the runtime review was left out of the code patch and recorded separately in [2026-04-23-runtime-known-issues.md](2026-04-23-runtime-known-issues.md).

## What Changed

- [packages/core/src/forecasting_harness/workflow/compiler.py](../../packages/core/src/forecasting_harness/workflow/compiler.py)
  - actor behavior inference is now compiled from actor-anchored clauses instead of any segment that merely mentions the actor
  - China alias coverage now explicitly includes `PLA` / `PRC` / `Beijing`
  - Japan alias coverage now explicitly includes `Japanese` / `Tokyo`
  - this prevents coalition / alliance language from bleeding into the wrong actor when that actor is only the target of the passage

- [packages/core/src/forecasting_harness/replay.py](../../packages/core/src/forecasting_harness/replay.py)
  - fallback confidence now surfaces as `fallback` / `Fallback baseline` instead of inheriting a normal calibrated low/medium/high bucket
  - fallback confidence still preserves the baseline value, but it no longer presents as replay-backed calibration

- [packages/core/src/forecasting_harness/workflow/reporting.py](../../packages/core/src/forecasting_harness/workflow/reporting.py)
  - report formatting now renders fallback confidence as `fallback baseline (..., 0 replay cases)` so it cannot visually outrank replay-backed branches

## Verification

- targeted behavior tests cover:
  - actor-trait attribution for Japan / China / Taiwan in mixed coalition passages
  - fallback-confidence normalization in replay calibration
  - fallback-confidence report rendering

- full suite:
  - `PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest packages/core -q`
  - `325 passed in 13.60s`
- smoke campaign:
  - `PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest packages/core/tests/test_smoke_campaign.py -q`
  - `20 passed in 3.08s`
- targeted runtime smoke:
  - actor-profile smoke compiled `China`, `Japan`, and `Taiwan` with:
    - `China -> domestic_sensitivity=0.84, reputational_sensitivity=0.75, coercive_bias=0.75`
    - `Japan -> alliance_dependence=1.0`
    - `Taiwan -> None`
  - fallback-confidence smoke rendered:
    - `Signal resolve ... calibrated confidence: fallback baseline (0.875, 0 replay cases)`
    - `Crisis talks ... calibrated confidence: low (0.875 from 6 replay cases)`
