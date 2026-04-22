# Evidence Runtime V1

Date: 2026-04-21

## Summary

- Added direct structured evidence saving to both:
  - `forecast-harness save-evidence-draft`
  - `forecast-harness run-adapter-action --action save-evidence-draft`
- Evidence items can now be supplied inline through repeated `--item-json` payloads instead of requiring a file-backed JSON handoff.
- The evidence-stage conversation turn now exposes `save-evidence-draft` as an explicit recovery/edit action alongside `draft-evidence-packet` and `curate-evidence-draft`.

## Verified Behavior

- `save-evidence-draft --item-json ...` writes a valid draft evidence packet without an `--input` file.
- `run-adapter-action --action save-evidence-draft --item-json ...` saves the evidence packet and advances the returned conversation turn to `approval`.
- The legacy `--input <file>` path still remains available as a compatibility fallback.

## Verification

- targeted CLI tests:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core/tests/test_cli_workflow.py -q -k "inline_item_json"`
  - result: `2 passed, 26 deselected in 0.18s`
- full suite:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core -q`
  - result: `268 passed in 3.96s`
- direct runtime smoke:
  - `run-adapter-action --action save-evidence-draft --item-json ...`
  - returned `executed_action = "save-evidence-draft"`
  - returned `turn.stage = "approval"`

## Boundary

- This closes the direct evidence-packet file handoff in the packaged runtime path.
- It does not yet remove every broader bulk-edit file-backed workflow elsewhere in the repo.
