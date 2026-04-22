# 2026-04-22 Adapter Packaging V2

## Summary

Phase 9 of the fixed repo completion program replaced the remaining thin-wrapper adapter status with repo-owned packaged local Codex and Claude bundles. The shared core runtime did not change; this pass packaged reproducible local install and smoke flows around the existing runtime.

## Verified Changes

- Codex now ships a repo-owned local bundle with:
  - `adapter.json`
  - `install.py`
  - `smoke.py`
  - the existing `.codex-plugin/plugin.json`
  - the existing `skills/forecast-harness/SKILL.md`
- Claude now ships a repo-owned local bundle with:
  - `adapter.json`
  - `install.py`
  - `smoke.py`
  - `skills/forecast-harness/SKILL.md`
- Both bundle smoke scripts now verify the packaged adapter path can:
  - start a run
  - save intake
  - ingest evidence
  - approve
  - simulate
  - summarize run and revision state
  - generate a report
- Adapter-facing tests now also assert `actions[*].runtime_action` where the packaged local adapters consume the ordered next-step surfaces.

## Verification

- `PYTHONPATH=packages/core/src ../../.venv/bin/python -m pytest packages/core/tests/test_adapter_docs.py packages/core/tests/test_adapter_packages.py packages/core/tests/test_adapter_runtime_cli.py -q`
- `PYTHONPATH=packages/core/src ../../.venv/bin/python -m pytest packages/core/tests/test_workflow_service.py -k runtime_action -q`
- `PYTHONPATH=packages/core/src ../../.venv/bin/python -m pytest packages/core/tests/test_cli_workflow.py -k runtime_action -q`

## Boundary

This pass packaged repo-owned local Codex and Claude integrations and their reproducible install/smoke coverage. Marketplace publication remains out of scope, and the shared forecasting runtime remains in `packages/core`.
