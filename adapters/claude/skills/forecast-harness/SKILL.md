---
name: forecast-harness
description: Use the local forecasting harness CLI from Claude Code without loading full run artifacts into active context.
---

1. From the checked-out forecasting harness repo/workspace, create or activate a Python 3.12+ virtualenv and install the shared core package with `pip install -e 'packages/core[dev]'`.
2. Use the query-style commands to drive the workflow instead of loading full run artifacts into active context.
3. Start a run with `forecast-harness start-run`, persist the intake with `forecast-harness save-intake-draft`, and request deterministic guidance with `forecast-harness draft-intake-guidance`.
4. Draft curated evidence with `forecast-harness draft-evidence-packet`, persist it with `forecast-harness save-evidence-draft`, and assemble a grouped approval view with `forecast-harness draft-approval-packet`.
5. Finalize the revision with `forecast-harness approve-revision`, refresh outputs with `forecast-harness simulate`, and prefer `forecast-harness summarize-revision` / `forecast-harness summarize-run` before opening full report files.
6. Use `forecast-harness generate-report` only when the adapter needs a refreshed Markdown report artifact in addition to the summary commands.
