# Deterministic MCTS Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the one-step simulation enumerator with a deterministic multi-step MCTS engine that preserves the current workflow/report contract.

**Architecture:** Extend the simulation core with deterministic search config, node expansion, rollout, and backpropagation while keeping `DomainPack` generic. Upgrade the reference domain packs just enough to supply causal multi-step transitions, and preserve `simulation["branches"]` for workflow compatibility.

**Tech Stack:** Python, pytest, Typer CLI, existing `BeliefState` / `DomainPack` / workflow services

---

### Task 1: Lock the Expected MCTS Behavior in Tests

**Files:**
- Modify: `packages/core/tests/test_simulation.py`

- [ ] **Step 1: Write failing tests for multi-step backed-up search output**

Add tests covering:
- root branch ranking based on deeper rollout/backpropagated value, not immediate child score
- returned payload metadata: `search_mode`, `iterations`, `node_count`, `max_depth_reached`
- root branches including `visits` and aggregated `metrics`
- deterministic terminal/depth-limited evaluation

- [ ] **Step 2: Run the focused simulation tests and verify they fail for the right reason**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_simulation.py -q`

Expected:
- failures showing missing MCTS metadata and one-step branch behavior

- [ ] **Step 3: Commit the red tests**

```bash
git add packages/core/tests/test_simulation.py
git commit -m "test: define deterministic mcts engine behavior"
```

### Task 2: Implement Deterministic Search Core

**Files:**
- Modify: `packages/core/src/forecasting_harness/simulation/engine.py`
- Modify: `packages/core/src/forecasting_harness/simulation/__init__.py`

- [ ] **Step 1: Add internal search config, node, action, and outcome normalization helpers**

Implement:
- stable config defaults
- child prior normalization
- deterministic state hashing from structured state content
- root-branch aggregation helpers

- [ ] **Step 2: Replace the one-step `run()` loop with selection / expansion / evaluation / backpropagation**

Implement:
- root validation
- node expansion from `propose_actions()` + `sample_transition()`
- PUCT child selection
- deterministic rollout policy
- backed-up scalar value and metric aggregation

- [ ] **Step 3: Preserve workflow compatibility in the returned payload**

Ensure `run()` returns:
- top-level `branches`
- `search_mode`
- `iterations`
- `node_count`
- `max_depth_reached`

- [ ] **Step 4: Run the focused simulation tests and make them pass**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_simulation.py -q`

Expected:
- PASS

- [ ] **Step 5: Commit the engine implementation**

```bash
git add packages/core/src/forecasting_harness/simulation/engine.py packages/core/src/forecasting_harness/simulation/__init__.py packages/core/tests/test_simulation.py
git commit -m "feat: add deterministic mcts simulation engine"
```

### Task 3: Extend Domain Pack Hooks Without Breaking Generic Use

**Files:**
- Modify: `packages/core/src/forecasting_harness/domain/base.py`
- Modify: `packages/core/tests/test_workflow_evidence.py`

- [ ] **Step 1: Add minimal optional search hooks to `DomainPack`**

Implement optional defaults for:
- `search_config()`
- `is_terminal(state, depth)`

Do not introduce LLM-specific hooks or actor-agent abstractions.

- [ ] **Step 2: Add or update tests for default hook behavior**

Verify:
- packs without overrides still work
- existing stubs remain valid

- [ ] **Step 3: Run the focused affected tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_workflow_evidence.py packages/core/tests/test_simulation.py -q`

Expected:
- PASS

- [ ] **Step 4: Commit the generic hook extension**

```bash
git add packages/core/src/forecasting_harness/domain/base.py packages/core/tests/test_workflow_evidence.py packages/core/tests/test_simulation.py
git commit -m "feat: add generic domain search hooks"
```

### Task 4: Make the Reference Packs Exercise Multi-Step Causality

**Files:**
- Modify: `packages/core/src/forecasting_harness/domain/generic_event.py`
- Modify: `packages/core/src/forecasting_harness/domain/interstate_crisis.py`
- Modify: `packages/core/tests/test_cli_workflow.py`

- [ ] **Step 1: Write failing tests for phase-sensitive or field-sensitive multi-step behavior**

Add tests showing:
- different next actions after different prior actions or phases
- simulation still yields stable top-level `branches` for workflow consumers

- [ ] **Step 2: Run the targeted tests and verify failure**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_cli_workflow.py packages/core/tests/test_simulation.py -q`

Expected:
- failures due to stubbed single-step transitions

- [ ] **Step 3: Implement deterministic state-updating transitions in the reference packs**

Keep this minimal:
- update `phase`
- update a few normalized fields
- make later actions differ from earlier ones

- [ ] **Step 4: Re-run targeted tests until green**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_cli_workflow.py packages/core/tests/test_simulation.py -q`

Expected:
- PASS

- [ ] **Step 5: Commit the reference-pack upgrade**

```bash
git add packages/core/src/forecasting_harness/domain/generic_event.py packages/core/src/forecasting_harness/domain/interstate_crisis.py packages/core/tests/test_cli_workflow.py packages/core/tests/test_simulation.py
git commit -m "feat: add deterministic multi-step reference transitions"
```

### Task 5: Verify Workflow Compatibility End to End

**Files:**
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

- [ ] **Step 1: Run the full test suite**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core -q`

Expected:
- PASS with updated total count

- [ ] **Step 2: Run a fresh Python 3.13 smoke test using the real CLI**

Verify:
- `start-run`
- `save-intake-draft`
- `draft-evidence-packet`
- `approve-revision`
- `simulate`
- `summarize-revision`

And confirm:
- simulation payload has `search_mode = "mcts"`
- root branches still exist for reporting
- top branch label is stable

- [ ] **Step 3: Update README and status note with verified new engine facts**

Document only verified changes:
- deterministic MCTS
- multi-step search
- preserved workflow compatibility
- new passing test count

- [ ] **Step 4: Commit verification and docs**

```bash
git add README.md docs/status/2026-04-20-project-status.md
git commit -m "docs: record deterministic mcts engine status"
```
