---
name: forecast-harness
description: Use the local forecasting harness CLI to create and inspect forecast runs from curated evidence.
---

1. From the checked-out forecasting harness repo/workspace, create or activate a Python 3.12+ virtualenv and install the shared core package with `pip install -e 'packages/core[dev]'`.
2. Run `forecast-harness demo-run` or start a workflow slice with `forecast-harness start-run`.
3. Persist structured drafts with `forecast-harness save-intake-draft` and `forecast-harness save-evidence-draft`, then approve them with `forecast-harness approve-revision`.
4. Use `forecast-harness simulate` and `forecast-harness generate-report` to refresh revision outputs.
5. Read `.forecast/runs/<run-id>/reports/<revision-id>.report.md` or use narrow artifact reads instead of loading the full workbench by default.
