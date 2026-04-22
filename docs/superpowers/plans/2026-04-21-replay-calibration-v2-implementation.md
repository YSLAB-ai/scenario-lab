# Replay Calibration V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the built-in historical replay corpus and make calibration output actionable through source-attributed case metadata and structured attention reporting.

**Architecture:** Extend the replay data model first, then add richer calibration summaries and a small CLI listing surface, and only then expand the built-in replay files and tune any failing expectations. Keep the replay engine deterministic and local-first.

**Tech Stack:** Python, Pydantic, Typer CLI, pytest, repo-owned JSON replay corpus

---

### Task 1: Extend Replay Models And Corpus Summaries

**Files:**
- Modify: `packages/core/src/forecasting_harness/replay.py`
- Modify: `packages/core/src/forecasting_harness/knowledge/replays.py`
- Test: `packages/core/tests/test_replay_library.py`

- [ ] Add replay source and historical context models, then attach them to `ReplayCase`.
- [ ] Extend built-in corpus summaries to report anchored-case counts and include enough metadata for listing.
- [ ] Update tests to cover the new fields and summary shape.

### Task 2: Add Calibration Attention Reporting

**Files:**
- Modify: `packages/core/src/forecasting_harness/replay.py`
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Test: `packages/core/tests/test_replay_library.py`
- Test: `packages/core/tests/test_replay.py`

- [ ] Add structured per-case attention items and failure-type aggregation to `CalibrationSummary`.
- [ ] Expose the richer summary through the existing replay calibration CLI and add a new `list-builtin-replay-cases` command.
- [ ] Add tests for attention items and the new CLI output.

### Task 3: Expand Built-In Replay Corpus With Anchored Cases

**Files:**
- Modify: `knowledge/replays/*.json`
- Test: `packages/core/tests/test_replay_library.py`

- [ ] Add historically anchored replay cases with source metadata in the existing domain files.
- [ ] Keep case phrasing aligned to the current domain pack vocabulary so expectations are meaningful.
- [ ] Update tests for the new corpus size and per-domain counts.

### Task 4: Tune Any Failing Domain Expectations

**Files:**
- Modify: `packages/core/src/forecasting_harness/domain/*.py` as needed
- Test: `packages/core/tests/test_smoke_campaign.py`
- Test: `packages/core/tests/test_replay_library.py`

- [ ] Run the expanded replay suite.
- [ ] If failures appear, make the smallest domain-pack changes needed to restore historically plausible outcomes.
- [ ] Re-run replay and smoke tests after tuning.

### Task 5: Update Docs And Record Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`
- Create: `docs/status/2026-04-21-replay-calibration-v2.md`

- [ ] Document the expanded replay corpus, anchored case metadata, and richer calibration summary.
- [ ] Record exact verification commands and outcomes.
- [ ] Include the new corpus count and any domain-tuning notes.
