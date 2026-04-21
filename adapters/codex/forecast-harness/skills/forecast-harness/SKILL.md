---
name: forecast-harness
description: Use the local forecasting harness CLI to create and inspect forecast runs from curated evidence.
---

1. From the checked-out forecasting harness repo/workspace, create or activate a Python 3.12+ virtualenv and install the shared core package with `pip install -e 'packages/core[dev]'`.
2. Use the query-style commands to drive the workflow instead of loading raw run artifacts into active context.
3. Prefer direct structured input over temporary JSON files for the normal adapter path.
4. Start a workflow slice with `forecast-harness start-run`, persist the intake directly with `forecast-harness save-intake-draft --event-framing ... --focus-entity ... --current-development ...`, then switch to the native loop by calling `forecast-harness draft-conversation-turn --corpus-db <db> [--candidate-path <dir>]`.
5. After each workflow mutation, call `forecast-harness draft-conversation-turn` and use its `headline`, `user_message`, `recommended_command`, `actions`, and `context` as the next user-facing prompt instead of inferring the stage yourself. This `after each workflow mutation` rule keeps the conversation loop deterministic.
6. Do not manually sequence `forecast-harness draft-intake-guidance`, `forecast-harness draft-retrieval-plan`, or `forecast-harness draft-ingestion-plan` in the normal path. Consume those payloads only through `forecast-harness draft-conversation-turn` context.
7. When the evidence-stage context includes `ingestion_recommendations`, prefer `forecast-harness batch-ingest-recommended` before `forecast-harness draft-evidence-packet`. Then trim the packet in place with `forecast-harness curate-evidence-draft`.
8. Finalize the revision with `forecast-harness approve-revision --assumption ...`, refresh outputs with `forecast-harness simulate`, and prefer `forecast-harness summarize-revision` / `forecast-harness summarize-run` before reading full report files.
9. Use `forecast-harness begin-revision-update` when new developments or new evidence require a child revision from an approved parent.
10. Use `forecast-harness draft-approval-packet`, `forecast-harness save-evidence-draft`, or `forecast-harness generate-report` only when the adapter needs manual inspection or replacement outside the normal loop.
