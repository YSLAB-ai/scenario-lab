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
- `forecast-harness list-domain-packs`
- `forecast-harness ingest-file`
- `forecast-harness ingest-directory`
- `forecast-harness list-corpus-sources`
- `forecast-harness start-run`
- `forecast-harness save-intake-draft`
- `forecast-harness draft-intake-guidance`
- `forecast-harness draft-conversation-turn`
- `forecast-harness summarize-run`
- `forecast-harness summarize-revision`
- `forecast-harness save-evidence-draft`
- `forecast-harness draft-evidence-packet`
- `forecast-harness curate-evidence-draft`
- `forecast-harness draft-approval-packet`
- `forecast-harness approve-revision`
- `forecast-harness begin-revision-update`
- `forecast-harness simulate`
- `forecast-harness generate-report`

Verified current progress:

- The reusable workflow core now supports registry-backed domain-pack discovery, local corpus ingestion, revisioned runs, direct structured intake/approval inputs, draft/approved artifacts, retrieval-backed evidence drafting, deterministic intake/approval guidance, conversation-stage turn drafting, in-place evidence curation, revision updates from approved parents, belief-state compilation, revisioned simulation outputs, and report generation.
- The repository includes two domain packs: `generic-event` and the `interstate-crisis` reference pack.
- The current workflow slice test suite passes with `141 passed` under `packages/core/.venv/bin/python -m pytest packages/core -q`.
- The workflow slice persists artifacts locally under `.forecast/runs/<run-id>/`, including revision-specific files such as `belief-state/<revision>.approved.json`, `simulation/<revision>.approved.json`, `reports/<revision>.report.md`, and `revisions/<revision>.json`, while the summary and curation commands let adapters inspect and revise runs without loading or rewriting those full artifacts by default.
- The adapter-facing path can now call `forecast-harness draft-conversation-turn` after each workflow mutation to retrieve the verified current stage, next-step message, recommended command, and narrow context payload.
- The intake schema now accepts generic fields such as `focus_entities`, `current_development`, `current_stage`, and `pack_fields`, while still accepting the older interstate-oriented aliases.
- The local corpus can now ingest curated `Markdown`, `CSV`, `JSON`, and text-extractable `PDF` files into a searchable SQLite/FTS corpus with citation-friendly chunk locations.
- The simulation engine now runs deterministic multi-step MCTS over `BeliefState` and writes simulation payloads with:
  - `search_mode = "mcts"`
  - `iterations`
  - `node_count`
  - `state_table_size`
  - `transposition_hits`
  - `max_depth_reached`
  - `reuse_summary`
  - `tree_nodes`
  - root `branches` preserved for the workflow/report layer
- Compatible child revisions can now warm-start from an approved parent simulation. The deterministic simulation payload persists enough node metadata for dependency-aware subtree reuse on rerun.
- The reference domain packs now perform deterministic phase-changing transitions instead of replaying the input state unchanged.
- A fresh Python 3.13 install now verifies the deterministic stage progression used by the adapter path:
  - `evidence` after `save-intake-draft`
  - `approval` after `draft-evidence-packet` and curation
  - `simulation` after `approve-revision`
  - `report` after `simulate`
  - `approval` again for a child revision created with `begin-revision-update`
- A fresh Python 3.13 install also verifies the new simulation facts:
  - `simulation/r1.approved.json` contains `search_mode = "mcts"`
  - `simulation/r1.approved.json` contains `iterations = 18` for the `interstate-crisis` pack
  - the top branch remains `Signal resolve`
  - `reports/r1.report.md` exists after simulation
- A fresh Python 3.13 child-revision smoke test now also verifies:
  - `simulation/r2.approved.json` reports `reuse_summary.enabled = true`
  - `simulation/r2.approved.json` reports `source_revision_id = "r1"`
  - the rerun reused cached nodes (`reused_nodes = 7`) and skipped invalidated ones (`skipped_nodes = 9`)
  - the rerun reported transposition metadata (`transposition_hits = 37`, `state_table_size = 14`, `node_count = 40`)

## Remaining Gaps

- The broader analyst workflow is still a local filesystem slice, not the full product described in the design spec.
- The deterministic core now supports a direct structured input path for intake and approvals and a conversation-stage turn contract, but there is not yet a finished conversational adapter loop that drafts and approves them end to end inside Codex or Claude Code.
- Manual file-backed paths still exist for evidence replacement and bulk edits.
- The repository still relies on curated local inputs rather than open-web retrieval.
- The `interstate-crisis` pack is still a reference pack rather than a mature validated geopolitical model.
- Only one concrete reference domain pack is implemented for the new workflow slice; broader multi-domain coverage remains future work.
- Corpus ingestion does not yet support OCR PDFs, spreadsheets, or web archives.
