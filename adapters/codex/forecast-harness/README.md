# Forecast Harness Codex Bundle

This is the packaged local Codex bundle for the forecasting harness.

Use:

- `packages/core/.venv/bin/python adapters/codex/forecast-harness/install.py --target-dir /tmp/codex-plugins`
- `packages/core/.venv/bin/python adapters/codex/forecast-harness/smoke.py`

The installer copies or links the bundle into a local Codex plugin root. The smoke script verifies the packaged adapter path can drive the shared runtime end to end.
