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
- `forecast-harness draft-retrieval-plan`
- `forecast-harness draft-ingestion-plan`
- `forecast-harness recommend-ingestion-files`
- `forecast-harness batch-ingest-recommended`
- `forecast-harness draft-evidence-packet`
- `forecast-harness curate-evidence-draft`
- `forecast-harness draft-approval-packet`
- `forecast-harness approve-revision`
- `forecast-harness begin-revision-update`
- `forecast-harness simulate`
- `forecast-harness generate-report`

Verified current progress:

- The reusable workflow core now supports registry-backed domain-pack discovery, local corpus ingestion, revisioned runs, direct structured intake/approval inputs, draft/approved artifacts, retrieval-backed evidence drafting, deterministic intake/approval guidance, conversation-stage turn drafting, in-place evidence curation, revision updates from approved parents, belief-state compilation, revisioned simulation outputs, and report generation.
- The repository now includes seven built-in domain packs:
  - `company-action`
  - `election-shock`
  - `generic-event`
  - `interstate-crisis`
  - `market-shock`
  - `regulatory-enforcement`
  - `supply-chain-disruption`
- The current workflow slice test suite passes with `163 passed` under `packages/core/.venv/bin/python -m pytest packages/core -q`.
- The workflow slice persists artifacts locally under `.forecast/runs/<run-id>/`, including revision-specific files such as `belief-state/<revision>.approved.json`, `simulation/<revision>.approved.json`, `reports/<revision>.report.md`, and `revisions/<revision>.json`, while the summary and curation commands let adapters inspect and revise runs without loading or rewriting those full artifacts by default.
- The adapter-facing path can now call `forecast-harness draft-conversation-turn` after each workflow mutation to retrieve the verified current stage, next-step message, recommended command, and narrow context payload.
- The intake schema now accepts generic fields such as `focus_entities`, `current_development`, `current_stage`, and `pack_fields`, while still accepting the older interstate-oriented aliases.
- The local corpus can now ingest curated `Markdown`, `CSV`, `JSON`, and text-extractable `PDF` files into a searchable SQLite/FTS corpus with citation-friendly chunk locations.
- The local corpus now also persists local semantic vectors per chunk and uses hybrid lexical + semantic retrieval with no external API.
- The repo now includes source-manifest scaffolding under `knowledge/domains/` for:
  - `company-action`
  - `election-shock`
  - `interstate-crisis`
  - `market-shock`
  - `regulatory-enforcement`
  - `supply-chain-disruption`
- The repo-owned domain manifests now affect retrieval directly by supplying:
  - domain-specific semantic alias groups for local semantic search
  - evidence-category term maps used to diversify drafted evidence packets
- The workflow core can now draft deterministic manifest-aware planning payloads for:
  - retrieval query expansion
  - corpus ingestion gaps
- The workflow core can now also turn ingestion gaps into:
  - concrete ingest tasks
  - ranked local file recommendations
  - prioritized batch ingestion into the corpus
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
- A direct CLI check now verifies `forecast-harness list-domain-packs` returns all seven built-in domain templates.
- The retrieval layer now supports semantic-only local matches where exact FTS terms would miss, for example `ceo response` retrieving a chunk about a `chief executive`.
- The workflow can now use manifest-specific semantic aliases, for example matching `military buildup` to a chunk about `force posture` inside the `interstate-crisis` domain without exact lexical overlap.
- Evidence drafting can now label and diversify packets using manifest evidence categories such as `force posture` and `diplomatic signaling`.
- Evidence drafting can now also run with no explicit `query_text`; the core generates deterministic manifest-aware query variants from the intake.
- The CLI now exposes `draft-retrieval-plan` and `draft-ingestion-plan` so adapters can ask the core what to search for and what the local corpus is still missing.
- The CLI now exposes `recommend-ingestion-files` and `batch-ingest-recommended` so the core can map local files to domain/source roles and ingest the highest-priority candidates directly.
- Batch ingestion now stores recommended tags such as `domain`, `source_role`, and top `evidence_category` on the ingested document rows.
- A direct CLI smoke check now verifies:
  - `draft-retrieval-plan` returns deterministic `query_variants` for the current intake
  - `draft-ingestion-plan` reports covered and missing manifest evidence categories from the local corpus
  - `draft-evidence-packet` succeeds without `--query-text`

## Remaining Gaps

- The broader analyst workflow is still a local filesystem slice, not the full product described in the design spec.
- The deterministic core now supports a direct structured input path for intake and approvals and a conversation-stage turn contract, but there is not yet a finished conversational adapter loop that drafts and approves them end to end inside Codex or Claude Code.
- Manual file-backed paths still exist for evidence replacement and bulk edits.
- The repository still relies on curated local inputs rather than open-web retrieval.
- The semantic retrieval layer is a deterministic local baseline, not a neural embedding model.
- The built-in domain packs are templates, not mature validated forecasting models.
- The source manifests define what to ingest, but they do not yet populate the local corpus automatically.
- The source manifests now guide retrieval planning and ingestion-gap reporting, but they do not yet trigger automatic ingestion or open-web acquisition.
- The source manifests now guide ingestion orchestration, but they do not yet schedule ingestion work automatically or acquire files from outside the local workspace.
- Corpus ingestion does not yet support OCR PDFs, spreadsheets, or web archives.
