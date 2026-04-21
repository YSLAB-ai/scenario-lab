---
name: forecast-harness
description: Use the local forecasting harness CLI to create and inspect forecast runs from curated evidence.
---

1. From the checked-out forecasting harness repo/workspace, create or activate a Python 3.12+ virtualenv and install the shared core package with `pip install -e 'packages/core[dev]'`.
2. Use the query-style commands to drive the workflow instead of loading raw run artifacts into active context.
3. Prefer direct structured input over temporary JSON files for the normal adapter path.
4. Start a workflow slice with `forecast-harness start-run`, persist the intake directly with `forecast-harness save-intake-draft --event-framing ... --focus-entity ... --current-development ...`, and ask the core for next-step guidance with `forecast-harness draft-intake-guidance`.
5. After each workflow mutation, call `forecast-harness draft-conversation-turn` and use its `headline`, `user_message`, and `context` as the next user-facing prompt instead of inferring the stage yourself. This `after each workflow mutation` rule keeps the conversation loop deterministic.
6. Draft curated evidence with `forecast-harness draft-evidence-packet`, trim the packet in place with `forecast-harness curate-evidence-draft`, and build a grouped approval view with `forecast-harness draft-approval-packet`.
7. Finalize the revision with `forecast-harness approve-revision --assumption ...`, refresh outputs with `forecast-harness simulate`, and prefer `forecast-harness summarize-revision` / `forecast-harness summarize-run` before reading full report files.
8. Use `forecast-harness begin-revision-update` when new developments or new evidence require a child revision from an approved parent.
9. Use `forecast-harness save-evidence-draft` or `forecast-harness generate-report` only when the adapter needs a manual evidence-file replacement or a refreshed Markdown report artifact in addition to the summary commands.
