# Forecasting Harness

Minimal core package for forecasting harness experiments.

## Quickstart

From the repository root, set `PYTHON` to any Python 3.12+ interpreter on your system:

```bash
PYTHON=/path/to/python3.12+-interpreter
"$PYTHON" -m venv .venv
source .venv/bin/activate
pip install -e 'packages/core[dev]'
forecast-harness demo-run
```

Requires Python 3.12+.

## Current Workflow Slice

The local CLI now supports the verified workflow commands:

- `forecast-harness version`
- `forecast-harness demo-run`
- `forecast-harness start-run`
- `forecast-harness simulate`
- `forecast-harness generate-report`

The slice persists run artifacts locally under `.forecast/runs/<run-id>/` and keeps the adapter docs aligned with those commands.

## Remaining Gaps

- The broader analyst workflow is still a local filesystem slice, not the full product described in the design spec.
- The repository still relies on curated local inputs rather than open-web retrieval.
- Only the current core workflow slice and reference packs are implemented here; broader multi-domain coverage remains future work.
