# Forecast Harness Claude Bundle

This is the packaged local Claude bundle for the forecasting harness.

Use:

- `python adapters/claude/forecast-harness/install.py --target-dir <claude-root>`
- `PYTHONPATH=packages/core/src .venv/bin/python adapters/claude/forecast-harness/smoke.py`

The installer places the forecast-harness skill in a local Claude root. The smoke script verifies the packaged adapter path can drive the shared runtime end to end.
