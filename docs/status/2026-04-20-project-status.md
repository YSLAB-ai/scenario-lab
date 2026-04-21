# Forecasting Harness Status

Date: 2026-04-20

## Verified Progress

- The shared Python core exists under `packages/core/src/forecasting_harness/`.
- The repository includes typed state and objective models, artifact storage, retrieval scaffolding, query helpers, a simulation engine, two domain packs (`generic-event` and `interstate-crisis`), thin Codex and Claude adapter scaffolding, and a reusable workflow package under `packages/core/src/forecasting_harness/workflow/`.
- Domain packs are now discovered through a registry instead of hardcoded CLI branching.
- The workflow now supports generic intake fields with compatibility aliases:
  - `focus_entities`
  - `current_development`
  - `current_stage`
  - `suggested_entities`
  - `pack_fields`
- The corpus now supports document metadata plus citation-friendly chunk rows in the local SQLite/FTS registry.
- The CLI can ingest curated local `Markdown`, `CSV`, `JSON`, and text-extractable `PDF` files into the corpus.
- The workflow can now draft evidence packets from the local corpus through a deterministic core step.
- The workflow can now draft deterministic intake guidance, grouped approval packets, and narrow run/revision summaries for adapters.
- The workflow can now draft deterministic conversation turns so adapters can advance the approval flow by asking the core what stage comes next.
- The CLI now supports direct structured input for intake drafts and approvals, in-place evidence curation, and revision updates from approved parents.
- The CLI now supports `draft-conversation-turn` so the adapter path can query the next user-facing prompt after each workflow mutation.
- Revision lineage is now persisted as first-class metadata under `revisions/<revision>.json`.
- The test suite passed on 2026-04-20 with:
  - `packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `132 passed`
- A clean install worked on 2026-04-20 in a fresh Python 3.13 virtual environment with:
  - `pip install -e 'packages/core[dev]'`
  - `forecast-harness ingest-file`
  - `forecast-harness start-run`
  - `forecast-harness save-intake-draft` with direct structured input
  - `forecast-harness draft-intake-guidance`
  - `forecast-harness draft-evidence-packet`
  - `forecast-harness curate-evidence-draft`
  - `forecast-harness draft-approval-packet`
  - `forecast-harness approve-revision` with direct structured input
  - `forecast-harness begin-revision-update`
  - `forecast-harness simulate`
  - `forecast-harness summarize-revision`
  - `forecast-harness summarize-run`
  - `forecast-harness generate-report`
- The clean install workflow run produced these revisioned artifacts for a test run:
  - `run.json`
  - `events.jsonl`
  - `intake/<revision>.draft.json`
  - `intake/<revision>.approved.json`
  - `evidence/<revision>.draft.json`
  - `evidence/<revision>.approved.json`
  - `assumptions/<revision>.approved.json`
  - `belief-state/<revision>.approved.json`
  - `simulation/<revision>.approved.json`
  - `reports/<revision>.report.md`
  - `revisions/<revision>.json`
- A conversation-stage smoke test can now verify the deterministic stage progression:
  - `evidence` after saving intake
  - `approval` after drafting and curating evidence
  - `simulation` after approving the revision
  - `report` after simulating the revision
  - `approval` again after creating child revision `r2` from approved parent `r1`
- The fresh-install conversation-stage smoke test on 2026-04-20 also verified:
  - `draft-intake-guidance` returned `domain_pack = interstate-crisis`
  - the curated evidence draft retained source id `source`
  - `summarize-revision` returned top branch `Signal resolve`
  - `reports/r1.report.md` existed after simulation
- A smoke test on 2026-04-20 verified:
  - ingesting a Markdown file into `corpus.db`
  - drafting intake guidance for an `interstate-crisis` run
  - drafting an evidence packet for that run from the ingested chunk
  - curating the drafted evidence packet in place
  - building a grouped approval packet
  - simulating the approved revision
  - summarizing both the revision and the run through the new narrow summary commands
  - beginning a child revision update from the approved parent
  - producing a child revision with `intake/r2.draft.json` and `evidence/r2.draft.json`
- Codex and Claude install notes exist:
  - `docs/install-codex.md`
  - `docs/install-claude-code.md`
- The design and workflow-slice planning docs are present:
  - `docs/superpowers/specs/2026-04-19-forecasting-harness-design.md`
  - `docs/superpowers/plans/2026-04-19-forecasting-harness-core-vertical-slice.md`
  - `docs/superpowers/specs/2026-04-20-interstate-workflow-slice-design.md`
  - `docs/superpowers/plans/2026-04-20-interstate-workflow-slice-implementation.md`
  - `docs/superpowers/specs/2026-04-20-generalized-harness-v2-design.md`
  - `docs/superpowers/plans/2026-04-20-generalized-harness-v2-implementation.md`
  - `docs/superpowers/specs/2026-04-20-corpus-ingestion-v1-design.md`
  - `docs/superpowers/plans/2026-04-20-corpus-ingestion-v1-implementation.md`

## Current Gaps

- The current analyst workflow is still not a finished conversational adapter loop.
- The adapters can now query guidance, conversation-turn, and summary payloads and use direct structured input for the normal path, but they are still documentation/skill scaffolding rather than a finished conversational analyst experience.
- Evidence replacement and some bulk-edit workflows still rely on file-backed JSON inputs.
- The simulation engine is still a one-step branch enumerator. It is not yet a full MCTS implementation with tree expansion, rollouts, and backpropagation.
- The `interstate-crisis` pack is still a reference pack:
  - action generation is fixed
  - transition sampling returns the input state
  - scoring is fixed
- The system does not yet implement:
  - OCR-backed PDF ingestion
  - spreadsheet or web archive ingestion
  - mature multi-domain packs
  - historical replay and calibration
  - full MCTS search
  - rule extraction / knowledge compiler

## Known Issues and Risks

- The existing local virtual environment at `packages/core/.venv` is Python 3.11. It can run the current tests, but it does not satisfy the documented Python `>=3.12` package requirement for a clean install.
- The clean package install and CLI workflow run were verified separately with `/usr/local/bin/python3.13`.
- Local git identity is currently configured as:
  - `user.name = Codex`
  - `user.email = codex@example.com`
  This is a placeholder identity, not a verified GitHub email.

## Relevant Commits For This Status Note

- `5bdaf57` `feat: add reusable workflow evidence and compiler hooks`
- `59fbbb8` `feat: add revisioned simulation and reporting flow`
- `b1189b1` `fix: repair partial demo run state`
- `1e47fc1` `feat: add domain pack registry`
- `b3f8ac4` `feat: generalize intake schema`
- `f7b9af7` `feat: draft evidence packets from retrieval`
- `13ffa88` `feat: persist revision lineage`
- `af7d99e` `feat: add corpus ingestion parsers`
- `9666884` `feat: persist corpus documents and chunks`
- `478825b` `feat: add corpus ingestion commands`
- `3da1b02` `feat: add guided workflow models`
- `c3359ce` `feat: add guided workflow summaries`
- `55244fa` `feat: add guided workflow commands`
- `e2091e9` `feat: add adapter workflow service operations`
- `38d066d` `feat: add adapter workflow cli commands`
- `667072a` `feat: add conversation turn model`
- `f4d66e3` `feat: add conversation turn resolution`
- `77b57f4` `feat: add conversation turn command`

## Current Assessment

The repository is a verified, runnable workflow prototype of the forecasting harness. It now supports registry-backed domain selection, generic intake aliases, local corpus ingestion, retrieval-backed evidence packet drafting, deterministic guidance/conversation-turn/summarization surfaces for adapters, direct structured adapter inputs, in-place evidence curation, persisted revision lineage, and a verified conversation-stage progression for the reference interstate-crisis workflow, but it is not yet a full forecasting product.
