# Deep Analysis V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the forecasting harness produce deeper and more consistent analysis by improving evidence-conditioned domain behavior, adding replay/calibration scaffolding, and synthesizing richer post-search scenario summaries.

**Architecture:** Keep the existing deterministic workflow and MCTS core, but make the domain packs react more strongly to evidence-derived fields, add a replay harness that exercises the full workflow from fixtures, and enrich simulation outputs with scenario-family and driver summaries that the report and conversation loop can consume directly.

**Tech Stack:** Python 3.11+, Typer CLI, Pydantic models, local SQLite corpus registry, deterministic MCTS engine, pytest.

---

### Task 1: Add Replay And Calibration Scaffolding

**Files:**
- Create: `packages/core/src/forecasting_harness/replay.py`
- Create: `packages/core/tests/test_replay.py`
- Modify: `packages/core/src/forecasting_harness/cli.py`

- [ ] Define replay models and runner that execute the existing workflow deterministically from fixture cases.
- [ ] Add CLI support to run a replay suite from a JSON file.
- [ ] Add regression tests for top-branch accuracy, evidence-source accuracy, and inferred-field coverage.

### Task 2: Strengthen Post-Search Scenario Synthesis

**Files:**
- Modify: `packages/core/src/forecasting_harness/simulation/engine.py`
- Modify: `packages/core/src/forecasting_harness/query_api.py`
- Modify: `packages/core/src/forecasting_harness/workflow/reporting.py`
- Modify: `packages/core/src/forecasting_harness/workflow/models.py`
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Create: `packages/core/tests/test_reporting.py`

- [ ] Extend branch outputs with synthesized path, terminal phase, confidence signal, and driver fields.
- [ ] Add scenario-family summarization helpers.
- [ ] Expose scenario families in revision summaries, reports, and conversation/report context.
- [ ] Add regression tests for report text and summarized scenario families.

### Task 3: Deepen Evidence-Conditioned Domain Behavior

**Files:**
- Modify: `packages/core/src/forecasting_harness/domain/interstate_crisis.py`
- Modify: `packages/core/src/forecasting_harness/domain/company_action.py`
- Modify: `packages/core/src/forecasting_harness/domain/election_shock.py`
- Modify: `packages/core/src/forecasting_harness/domain/market_shock.py`
- Modify: `packages/core/src/forecasting_harness/domain/regulatory_enforcement.py`
- Modify: `packages/core/src/forecasting_harness/domain/supply_chain_disruption.py`
- Modify: `packages/core/src/forecasting_harness/domain/template_utils.py`
- Modify: `packages/core/tests/test_domain_templates.py`
- Modify: `packages/core/tests/test_interstate_crisis_pack.py`

- [ ] Increase action diversity and state sensitivity in each built-in template pack.
- [ ] Add multi-outcome transitions where the pack should branch into multiple plausible states.
- [ ] Preserve current sensible top-branch behavior while making branch trees more differentiated.
- [ ] Add or update focused tests for the new action/transition behavior.

### Task 4: Verify End-To-End And Document

**Files:**
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

- [ ] Run focused tests for replay, reporting, domain templates, workflow, and simulation.
- [ ] Run the full package test suite.
- [ ] Update status notes with the verified new capabilities.
- [ ] Commit, merge to `main`, re-run verification on `main`, and push.
