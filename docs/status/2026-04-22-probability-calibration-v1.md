# Probability Calibration V1

Date: 2026-04-22

## Summary

- Added replay-backed confidence calibration as a deterministic post-search layer.
- Simulation payloads now keep the raw visit-share `confidence_signal` and also attach:
  - `confidence_bucket`
  - `calibrated_confidence`
  - `calibration_case_count`
- Simulation payloads now also include a top-level `confidence_calibration` block describing the domain replay profile used to annotate branch confidence.
- Revision summaries and generated reports now surface the calibrated branch confidence fields instead of relying on raw ranking alone.

## Verification

- Full suite:
  - `PYTHONPATH=packages/core/src .venv/bin/python -m pytest packages/core -q`
  - `291 passed in 9.51s`
- Checked-in smoke campaign:
  - `PYTHONPATH=packages/core/src .venv/bin/python -m pytest packages/core/tests/test_smoke_campaign.py -q`
  - `16 passed in 2.57s`
- Focused phase tests:
  - `PYTHONPATH=packages/core/src .venv/bin/python -m pytest packages/core/tests/test_replay.py packages/core/tests/test_simulation.py packages/core/tests/test_reporting.py packages/core/tests/test_workflow_service.py packages/core/tests/test_retrieval.py -q`
  - `119 passed in 1.76s`
- Replay calibration CLI smoke:
  - `PYTHONPATH=packages/core/src .venv/bin/python -m forecasting_harness.cli summarize-replay-calibration`
  - returned `40` cases, `28` historically anchored cases, and replay-backed confidence profiles for all seven replay-covered built-in domains
- Direct simulation smoke on `philippines-china-shoal` with `250` iterations returned a top branch payload containing:
  - `label = Signal resolve (managed signal)`
  - `confidence_signal = 0.276`
  - `confidence_bucket = low`
  - `calibrated_confidence = 0.875`
  - `calibration_case_count = 6`

## Scope Boundary

- This pass does not change MCTS selection or backpropagation.
- Calibration is attached after search from the built-in replay corpus.
- OCR-backed PDF ingestion remains deferred and untouched by this phase.
