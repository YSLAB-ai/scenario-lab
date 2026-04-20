---
name: forecast-harness
description: Use the local forecasting harness CLI to create and inspect forecast runs from curated evidence.
---

1. From the checked-out forecasting harness repo/workspace, create or activate a Python 3.12+ virtualenv and install the shared core package with `pip install -e 'packages/core[dev]'`.
2. Run `forecast-harness demo-run` or start a workflow slice with `forecast-harness start-run`.
3. Use `forecast-harness simulate` and `forecast-harness generate-report` to refresh revision outputs.
4. Read `.forecast/runs/<run-id>/report.md` or use narrow artifact reads instead of loading the full workbench by default.
