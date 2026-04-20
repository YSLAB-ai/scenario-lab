# Forecasting Harness Status

Date: 2026-04-20

## Verified Progress

- The shared Python core exists under `packages/core/src/forecasting_harness/`.
- The repository includes typed state and objective models, artifact storage, retrieval scaffolding, query helpers, a simulation engine, one generic domain pack, and thin Codex and Claude adapter scaffolding.
- The test suite passed on 2026-04-20 with:
  - `packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `39 passed in 0.14s`
- A clean install worked on 2026-04-20 in a fresh Python 3.13 virtual environment with:
  - `pip install -e 'packages/core[dev]'`
  - `forecast-harness version`
  - `forecast-harness demo-run --root <temp-dir>`
- The clean install run produced these artifacts:
  - `belief-state.json`
  - `tree-summary.json`
  - `report.md`
  - `workbench.md`
- Codex and Claude install notes exist:
  - `docs/install-codex.md`
  - `docs/install-claude-code.md`
- The design spec and the vertical-slice implementation plan are present:
  - `docs/superpowers/specs/2026-04-19-forecasting-harness-design.md`
  - `docs/superpowers/plans/2026-04-19-forecasting-harness-core-vertical-slice.md`

## Current Gaps

- The current CLI is a vertical-slice prototype, not a full analyst workflow. Verified commands are limited to `version` and `demo-run`.
- The only shipped domain pack is `generic-event`. It is a stub:
  - action generation is hardcoded
  - transition sampling returns the input state
  - scoring is fixed
- The retrieval layer is local SQLite/FTS scaffolding. There is no end-user ingestion workflow yet for curated PDF, Markdown, CSV, and JSON corpora.
- The adapters are scaffolding and install instructions, not seamless end-user integrations for Codex or Claude Code.
- The system does not yet implement the full product described in the design:
  - interactive intake and approval workflow
  - evidence review loop
  - mature multi-domain packs
  - historical replay and calibration workflow
  - rule extraction / knowledge compiler

## Known Issues and Risks

- The existing local virtual environment at `packages/core/.venv` is Python 3.11. It can run the current tests, but it does not satisfy the documented Python `>=3.12` package requirement for a clean install.
- The clean package install was verified separately with `/usr/local/bin/python3.13`.
- Before publish setup, this repository had no `origin` remote configured.
- `gh` CLI is not installed in this workspace environment.
- Local git identity is currently configured as:
  - `user.name = Codex`
  - `user.email = codex@example.com`
  This is a placeholder identity, not a verified GitHub email.

## Relevant Commits Before This Status Note

- `74cb4d7404f23a1ff61f5f7c96232f55a4628526` `fix: make simulation branch ids globally unique`
- `de1539e` `fix: address final review issues in engine and retrieval`
- `7374a0b` `docs: generalize quickstart python interpreter guidance`
- `ff4881f` `docs: add quickstart and verify vertical slice`

## Current Assessment

The repository is a verified, runnable vertical slice of the forecasting harness core. It is not yet a fully functional version of the end-user forecasting product.
