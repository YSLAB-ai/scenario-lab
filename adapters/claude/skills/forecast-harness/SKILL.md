---
name: forecast-harness
description: Use the local forecasting harness CLI from Claude Code without loading full run artifacts into active context.
---

1. From the checked-out forecasting harness repo/workspace, create or activate a Python 3.12+ virtualenv and install the shared core package with `pip install -e 'packages/core[dev]'`.
2. Run `forecast-harness demo-run` or start a workflow slice with `forecast-harness start-run`.
3. Persist structured drafts with `forecast-harness save-intake-draft` and `forecast-harness save-evidence-draft`, then approve them with `forecast-harness approve-revision`.
4. Use `forecast-harness simulate` and `forecast-harness generate-report` to refresh revision outputs.
5. Prefer narrow artifact reads over loading full revision artifacts into active context.
