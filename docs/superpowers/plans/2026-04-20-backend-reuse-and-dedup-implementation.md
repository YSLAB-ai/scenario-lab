# Backend Reuse and Dedup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add warm-start subtree reuse and transposition-table dedup to the deterministic MCTS backend so repeated reruns reuse valid work instead of rebuilding all search statistics from scratch.

**Architecture:** Extend compatibility and simulation cache helpers first, then move simulation-node statistics into reusable buckets keyed by `state_hash`, and finally wire parent-revision reuse through the workflow service so reruns automatically seed compatible subtrees.

**Tech Stack:** Python, pytest, existing `BeliefState` / workflow service / simulation engine

---

### Task 1: Define Compatibility and Reuse Expectations in Tests

**Files:**
- Modify: `packages/core/tests/test_compatibility.py`
- Modify: `packages/core/tests/test_simulation.py`

- [ ] **Step 1: Write failing compatibility tests for reusable vs incompatible reruns**
- [ ] **Step 2: Write failing simulation tests for**
  - `reuse_summary`
  - reused node counts
  - transposition hits
  - shared state-table statistics below root
- [ ] **Step 3: Run focused tests and verify failure**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_compatibility.py packages/core/tests/test_simulation.py -q`

- [ ] **Step 4: Commit the red tests**

```bash
git add packages/core/tests/test_compatibility.py packages/core/tests/test_simulation.py
git commit -m "test: define backend reuse and dedup behavior"
```

### Task 2: Implement Compatibility and Cache Helpers

**Files:**
- Modify: `packages/core/src/forecasting_harness/compatibility.py`
- Modify: `packages/core/src/forecasting_harness/simulation/cache.py`

- [ ] **Step 1: Add structured belief-state compatibility comparison**
- [ ] **Step 2: Extend node-reuse logic to understand `reusable` compatibility**
- [ ] **Step 3: Re-run focused tests until green**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_compatibility.py packages/core/tests/test_simulation.py -q`

- [ ] **Step 4: Commit compatibility/cache changes**

```bash
git add packages/core/src/forecasting_harness/compatibility.py packages/core/src/forecasting_harness/simulation/cache.py packages/core/tests/test_compatibility.py packages/core/tests/test_simulation.py
git commit -m "feat: add backend reuse compatibility checks"
```

### Task 3: Add Warm-Start and Transposition Support to the Engine

**Files:**
- Modify: `packages/core/src/forecasting_harness/simulation/engine.py`
- Modify: `packages/core/tests/test_simulation.py`

- [ ] **Step 1: Introduce shared node-stat buckets for non-root equivalent states**
- [ ] **Step 2: Persist compact `tree_nodes` snapshots in simulation output**
- [ ] **Step 3: Accept an optional reuse context in `SimulationEngine.run()`**
- [ ] **Step 4: Seed compatible node stats from prior simulation snapshots**
- [ ] **Step 5: Emit `reuse_summary`, `state_table_size`, and `transposition_hits`**
- [ ] **Step 6: Re-run focused simulation tests until green**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_simulation.py -q`

- [ ] **Step 7: Commit the engine changes**

```bash
git add packages/core/src/forecasting_harness/simulation/engine.py packages/core/tests/test_simulation.py
git commit -m "feat: add warm-start reuse and transposition dedup"
```

### Task 4: Wire Parent-Revision Reuse Through the Workflow

**Files:**
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Modify: `packages/core/tests/test_workflow_service.py`
- Modify: `packages/core/tests/test_cli_workflow.py`

- [ ] **Step 1: Write failing workflow tests for rerun reuse from parent revisions**
- [ ] **Step 2: Load parent belief-state and parent simulation payload when available**
- [ ] **Step 3: Pass reuse context into `SimulationEngine.run()`**
- [ ] **Step 4: Re-run targeted workflow tests until green**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_workflow_service.py packages/core/tests/test_cli_workflow.py -q`

- [ ] **Step 5: Commit workflow integration**

```bash
git add packages/core/src/forecasting_harness/workflow/service.py packages/core/tests/test_workflow_service.py packages/core/tests/test_cli_workflow.py
git commit -m "feat: reuse parent search state during reruns"
```

### Task 5: Final Verification and Status Updates

**Files:**
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

- [ ] **Step 1: Run the full suite**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core -q`

- [ ] **Step 2: Run a fresh Python 3.13 smoke test**

Verify:
- first simulation writes `tree_nodes`
- child revision rerun writes `reuse_summary.reused_nodes > 0`
- repeated state convergence yields `transposition_hits > 0`

- [ ] **Step 3: Update README and status note with verified new backend facts**
- [ ] **Step 4: Commit the final docs**

```bash
git add README.md docs/status/2026-04-20-project-status.md
git commit -m "docs: record backend reuse and dedup status"
```
