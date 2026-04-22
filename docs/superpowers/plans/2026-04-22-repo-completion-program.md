# Repo Completion Program Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the accepted repo gaps in a fixed order and reach a stable “done” state without letting the target expand every time the repo improves.

**Architecture:** Treat the remaining work as one bounded program with eight phases. Each phase must land green on `main` before the next phase starts. Scope is frozen up front: spreadsheet/web-archive ingestion, knowledge compilation, replay expansion and calibration, remaining structured workflow cleanup, richer domain synthesis, and packaged local adapter integrations are in scope; OCR-backed PDF ingestion is explicitly deferred because the repo already supports text-extractable PDFs and the user wants Codex/Claude-side PDF handling to cover image-heavy cases for now.

**Tech Stack:** Python, Pydantic, Typer CLI, pytest, SQLite/FTS5, local semantic search, repo-owned JSON manifests/replays, optional `sentence-transformers`

---

## Fixed Completion Criteria

This program is **done** only when all of these are true on accepted `main`:

- [ ] `README.md` and `docs/status/2026-04-20-project-status.md` no longer list any open gaps except the explicitly deferred OCR note.
- [ ] Full suite passes on merged `main`.
- [ ] Checked-in smoke campaign passes on merged `main`.
- [ ] Built-in replay corpus reaches at least `40` cases with meaningful multi-domain coverage and green calibration.
- [x] Simulation output exposes calibrated branch probability fields or calibrated confidence buckets instead of raw ranking only.
- [ ] Spreadsheet ingestion and web-archive ingestion are implemented and documented.
- [ ] Remaining file-backed bulk-edit workflow paths are replaced by structured CLI/runtime inputs.
- [x] Knowledge compiler / rule extraction exists and feeds reusable domain knowledge back into the repo-owned evolution path.
- [ ] New-domain synthesis can generate richer bespoke Python behavior than the current template-only starter.
- [ ] Codex and Claude local integrations are packaged enough to run the end-to-end workflow through repo-owned installable bundles, not just thin skill docs.
- [ ] `packages/core/.venv` and the documented local verification flow use Python `>=3.12`.

## Out Of Scope For This Program

- [ ] OCR-backed PDF ingestion is deferred unless a later phase proves that adapter-side PDF handling is insufficient for the actual workflow.
- [ ] Public marketplace publication is deferred; the target is a repo-owned packaged local integration with reproducible install and smoke coverage.

---

### Task 1: Freeze Scope And Repair Local Tooling Baseline

**Files:**
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`
- Modify: `packages/core/.python-version` or local tooling files if present
- Create or modify: local setup notes only if needed
- Test: full suite on Python `>=3.12`

- [x] Rewrite the accepted gap list so it matches the frozen completion criteria above and explicitly marks OCR as deferred rather than open-ended.
- [x] Replace the checked-in local verification path so the documented default uses Python `>=3.12`.
- [x] Rebuild the local verification environment and rerun the package suite under Python `>=3.12`.
- [x] Record the verified Python version and commands in the status notes.
- [x] Commit only the tooling/doc baseline repair before moving on.

### Task 2: Add Spreadsheet And Web-Archive Ingestion

**Files:**
- Modify: `packages/core/src/forecasting_harness/retrieval/ingest.py`
- Modify: `packages/core/src/forecasting_harness/retrieval/__init__.py`
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Test: `packages/core/tests/test_retrieval.py`
- Test: `packages/core/tests/test_cli_workflow.py`

- [x] Add `.xlsx` spreadsheet ingestion for text-bearing sheets and stable cell-location chunking.
- [x] Add HTML / web-archive ingestion for saved pages with preserved source metadata and chunk locations.
- [x] Add CLI coverage so both formats flow through `ingest-file` and `ingest-directory`.
- [x] Add retrieval tests showing those ingested chunks are searchable through the existing lexical + semantic path.
- [x] Document the new source types and their limits in `README.md`.

### Task 3: Remove Remaining File-Backed Bulk-Edit Workflow Paths

**Files:**
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Modify: `packages/core/src/forecasting_harness/evolution/service.py`
- Modify: `packages/core/src/forecasting_harness/evolution/models.py` as needed
- Test: `packages/core/tests/test_cli_workflow.py`
- Test: `packages/core/tests/test_domain_evolution_cli.py`

- [x] Audit every CLI path that still requires a JSON file for structured edits instead of direct flags or repeated JSON payloads.
- [x] Convert active analyst-facing flows first:
  - replay suite input
  - domain blueprint input
  - domain suggestion / weakness / retuning surfaces
- [x] Preserve file input only for true import/export use cases, not for routine workflow mutation.
- [x] Extend the packaged runtime where needed so the same structured surfaces are available there too.
- [x] Update docs so the “normal path” examples no longer rely on intermediary JSON files.

### Task 4: Expand Replay Library To A Real Calibration Base

**Files:**
- Modify: `knowledge/replays/*.json`
- Modify: `packages/core/src/forecasting_harness/knowledge/replays.py`
- Modify: `packages/core/tests/test_replay_library.py`
- Modify: `packages/core/tests/test_replay.py`
- Test: replay CLI commands and calibration summaries

- [x] Expand the built-in replay corpus from `22` to at least `40` cases.
- [x] Guarantee minimum coverage for the active built-in domains:
  - `company-action`
  - `election-shock`
  - `interstate-crisis`
  - `market-shock`
  - `pandemic-response`
  - `regulatory-enforcement`
  - `supply-chain-disruption`
- [x] Keep each added case time-anchored and source-attributed.
- [x] Use the replay expansion to expose weak domains instead of hiding misses by loosening expectations.
- [x] Re-run calibration after each domain batch and tune only when a failure reflects a real model issue.

### Task 5: Add Probability Calibration V1

**Files:**
- Modify: `packages/core/src/forecasting_harness/replay.py`
- Modify: `packages/core/src/forecasting_harness/simulation/engine.py`
- Modify: `packages/core/src/forecasting_harness/query_api.py`
- Modify: `packages/core/src/forecasting_harness/workflow/reporting.py`
- Test: `packages/core/tests/test_simulation.py`
- Test: `packages/core/tests/test_replay.py`

- [x] Define a calibrated probability or confidence-bucket layer that uses replay outcomes rather than raw MCTS visits alone.
- [x] Add per-domain calibration summaries that can map branch confidence to replay-backed buckets.
- [x] Surface the calibrated value in:
  - simulation payloads
  - revision summaries
  - generated reports
- [x] Keep the deterministic MCTS core intact; calibration must be a post-search layer, not a hidden stochastic rewrite.
- [x] Add tests proving the calibrated field exists and remains stable for replay-covered domains.

### Task 6: Build Knowledge Compiler / Rule Extraction V1

**Files:**
- Create: `packages/core/src/forecasting_harness/knowledge/compiler.py`
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Modify: `packages/core/src/forecasting_harness/evolution/service.py`
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Test: new compiler-focused tests under `packages/core/tests/`

- [x] Add a deterministic rule-extraction pass that turns approved evidence or replay misses into candidate:
  - evidence categories
  - semantic aliases
  - manifest state terms
  - manifest action biases
- [x] Route those candidates into the existing protected domain-evolution path instead of mutating packs directly.
- [x] Add CLI visibility so the compiler can be run explicitly and its candidates can be inspected.
- [x] Verify idempotence so rerunning the compiler on the same material does not duplicate suggestions.
- [x] Record the compiler boundary in docs: it proposes reusable knowledge, it does not rewrite the core algorithm.

### Task 7: Deepen Domain Packs And Retuning Loop

**Files:**
- Modify: `packages/core/src/forecasting_harness/domain/*.py`
- Modify: `knowledge/domains/*.json`
- Modify: `packages/core/src/forecasting_harness/evolution/service.py`
- Test: `packages/core/tests/test_smoke_campaign.py`
- Test: replay and retuning suites

- [x] Use the larger replay corpus and compiler outputs to deepen the weakest packs first.
- [x] Require every retuning pass to improve or preserve:
  - top-branch accuracy
  - root-strategy accuracy
  - evidence-source accuracy
  - inferred-field coverage
- [x] Expand actions, transitions, or state fields only when replay evidence justifies it.
- [x] Keep the retuning boundary one domain at a time.
- [x] Update smoke scenarios after each substantive domain change so the checked-in campaign remains a realistic regression suite.

### Task 8: Upgrade New-Domain Synthesis Beyond Template Starters

**Files:**
- Modify: `packages/core/src/forecasting_harness/evolution/service.py`
- Modify: `packages/core/src/forecasting_harness/domain/generated_template.py`
- Modify: `packages/core/src/forecasting_harness/domain/registry.py`
- Modify: domain synthesis tests
- Test: `packages/core/tests/test_domain_synthesis_cli.py`

- [x] Extend domain synthesis so generated domains can include richer bespoke Python behavior for:
  - state inference
  - action priors
  - transition logic
  - objective recommendation hooks
- [x] Keep generated packs protected from core-algorithm changes.
- [x] Ensure generated tests pin the synthesized behavior instead of only checking import success.
- [x] Preserve the existing branch-only review gate for promoted synthesized domains.

### Task 9: Package Codex And Claude Local Integrations

**Files:**
- Modify: `adapters/codex/forecast-harness/**`
- Modify: `adapters/claude/**`
- Modify: `docs/install-codex.md`
- Modify: `docs/install-claude-code.md`
- Modify: `README.md`
- Test: adapter CLI/runtime smoke coverage under `packages/core/tests/` or adapter-specific tests

- [ ] Replace the remaining “thin wrapper” status with repo-owned packaged local integrations that can drive the existing runtime end to end.
- [ ] Add install/test flows that verify the packaged local adapter bundle can:
  - start a run
  - save intake
  - ingest/retrieve evidence
  - approve
  - simulate
  - summarize/report
- [ ] Keep marketplace publication explicitly out of scope; the deliverable is a local packaged integration with reproducible install and smoke coverage.
- [ ] Update docs so the adapter status line is no longer an open gap.

### Task 10: Final Cleanup And Stop Condition

**Files:**
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`
- Create: final completion status note for the program

- [ ] Remove or rewrite every accepted gap line that the program closed.
- [ ] Leave only the explicitly deferred OCR note if it still remains deferred.
- [ ] Re-run:
  - full suite
  - smoke campaign
  - built-in replay calibration
  - built-in replay retuning
- [ ] Record exact command outputs in the final status note.
- [ ] Stop opening new roadmap items unless a failing test or verified gap blocks one of the fixed completion criteria above.

---

## Execution Rules For This Program

- [ ] Never start a later phase while an earlier phase is still red.
- [ ] Merge after every green phase; do not let the whole program accumulate on one long-lived branch.
- [ ] Update the accepted docs at the end of each phase so “what’s left” always matches the frozen completion criteria.
- [ ] If a new issue appears that is not required by the fixed completion criteria, record it as deferred instead of expanding this program.
