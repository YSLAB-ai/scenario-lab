---
name: scenario-lab
description: Use the local Scenario Lab CLI to create and inspect scenario runs from curated evidence.
---

1. From the checked-out Scenario Lab repo/workspace, create or activate a Python 3.12+ virtualenv and install the shared core package with `pip install -e 'packages/core[dev]'`.
2. Use the query-style commands to drive the workflow instead of loading raw run artifacts into active context.
3. Prefer direct structured input over temporary JSON files for the normal adapter path.
4. The underlying raw commands still exist, including `scenario-lab start-run`, `scenario-lab save-intake-draft`, and `scenario-lab draft-conversation-turn`, but the packaged runtime is the normal path.
5. Bootstrap a workflow slice with `scenario-lab run-adapter-action --root <root> --run-id <run> --revision-id r1 --action start-run --domain-pack <slug>`.
6. after each workflow mutation, keep using `scenario-lab run-adapter-action --root <root> --corpus-db <db> [--candidate-path <dir>] --run-id <run> --revision-id <rev> --action <action-name> ...` and treat the returned `turn` as the user-facing next step.
7. Use `turn.recommended_runtime_action` as the default next runtime action and `turn.actions` as the ordered set of allowed next steps. This keeps the conversation loop deterministic without manually sequencing raw workflow commands.
8. Do not manually sequence `scenario-lab draft-intake-guidance`, `scenario-lab draft-retrieval-plan`, or `scenario-lab draft-ingestion-plan` in the normal path. Consume those payloads only through the packaged runtime `turn.context`.
9. When the evidence-stage runtime context includes `ingestion_recommendations`, prefer `--action batch-ingest-recommended` before `--action draft-evidence-packet`. Then trim the packet in place with `--action curate-evidence-draft`.
10. After approval, keep using the packaged runtime to reach simulation, report review, and `begin-revision-update`. Prefer `scenario-lab summarize-revision` / `scenario-lab summarize-run` before reading full report files.
11. Raw commands such as `scenario-lab draft-evidence-packet`, `scenario-lab curate-evidence-draft`, `scenario-lab draft-approval-packet`, `scenario-lab approve-revision`, `scenario-lab begin-revision-update`, `scenario-lab simulate`, `scenario-lab summarize-run`, `scenario-lab summarize-revision`, `scenario-lab save-evidence-draft`, and `scenario-lab generate-report` remain available for inspection or manual recovery outside the packaged runtime path. `save-evidence-draft` now also accepts repeated `--item-json` payloads for direct structured evidence replacement when a file handoff is unnecessary.
