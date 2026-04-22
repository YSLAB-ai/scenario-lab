# Adapter Runtime V1

Date: 2026-04-21

## Summary

- Added a packaged adapter runtime command: `forecast-harness run-adapter-action`
- The runtime executes one approved workflow mutation and returns the next deterministic conversation turn in the same payload.
- Codex and Claude install guides and skills now point at the packaged runtime rather than telling the adapter to manually chain raw workflow commands.

## Verified Behavior

- `run-adapter-action --action start-run` returns the intake turn for the requested run and revision.
- `run-adapter-action --action save-intake-draft` applies structured intake input and returns the evidence-stage turn.
- `run-adapter-action --action batch-ingest-recommended`, `draft-evidence-packet`, `approve-revision`, and `simulate` all advance the loop and return the next turn.
- `run-adapter-action --action begin-revision-update` creates a child revision and returns the child revision turn.

## Verification

- `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core/tests/test_adapter_runtime_cli.py -q`
- `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core/tests/test_adapter_docs.py -q`
- `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core -q`
- Direct module-path smoke using `/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m forecasting_harness.cli` with `PYTHONPATH=packages/core/src`

## Smoke Facts

- start stage: `intake`
- post-intake `recommended_runtime_action`: `batch-ingest-recommended`
- ingested count: `1`
- post-evidence stage: `approval`
- post-approval stage: `simulation`
- post-simulate stage: `report`
- smoke top branch at `250` iterations: `Signal resolve (managed signal)`

The packaged runtime is local-first and deterministic. It does not turn the Codex or Claude adapters into a marketplace-distributed plugin runtime; it gives those thin adapters a single real execution surface in the shared core.
