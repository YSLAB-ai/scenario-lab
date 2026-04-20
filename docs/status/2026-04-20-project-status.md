# Forecasting Harness Status

Date: 2026-04-20

## Verified Progress

- The shared Python core exists under `packages/core/src/forecasting_harness/`.
- The repository includes typed state and objective models, artifact storage, retrieval scaffolding, query helpers, a simulation engine, two domain packs (`generic-event` and `interstate-crisis`), thin Codex and Claude adapter scaffolding, and a reusable workflow package under `packages/core/src/forecasting_harness/workflow/`.
- The test suite passed on 2026-04-20 with:
  - `packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `84 passed in 0.19s`
- A clean install worked on 2026-04-20 in a fresh Python 3.13 virtual environment with:
  - `pip install -e 'packages/core[dev]'`
  - `forecast-harness version`
  - `forecast-harness start-run`
  - `forecast-harness save-intake-draft`
  - `forecast-harness save-evidence-draft`
  - `forecast-harness approve-revision`
  - `forecast-harness simulate`
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
- Codex and Claude install notes exist:
  - `docs/install-codex.md`
  - `docs/install-claude-code.md`
- The design and workflow-slice planning docs are present:
  - `docs/superpowers/specs/2026-04-19-forecasting-harness-design.md`
  - `docs/superpowers/plans/2026-04-19-forecasting-harness-core-vertical-slice.md`
  - `docs/superpowers/specs/2026-04-20-interstate-workflow-slice-design.md`
  - `docs/superpowers/plans/2026-04-20-interstate-workflow-slice-implementation.md`

## Current Gaps

- The current analyst workflow is still file-backed. Users provide intake, evidence, and assumptions as JSON inputs rather than through a conversational adapter loop.
- The simulation engine is still a one-step branch enumerator. It is not yet a full MCTS implementation with tree expansion, rollouts, and backpropagation.
- The `interstate-crisis` pack is still a reference pack:
  - action generation is fixed
  - transition sampling returns the input state
  - scoring is fixed
- The retrieval layer is local SQLite/FTS scaffolding. There is no end-user ingestion workflow yet for curated PDF, Markdown, CSV, and JSON corpora, and no evidence-packet drafting from a real corpus.
- The adapters are still documentation and skill scaffolding rather than a seamless conversational analyst experience.
- The system does not yet implement:
  - evidence-backed scenario construction from a curated corpus
  - mature multi-domain packs
  - historical replay and calibration
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

## Current Assessment

The repository is a verified, runnable workflow prototype of the forecasting harness. It supports a full revisioned CLI flow for a reference interstate-crisis scenario, but it is not yet a full forecasting product.
