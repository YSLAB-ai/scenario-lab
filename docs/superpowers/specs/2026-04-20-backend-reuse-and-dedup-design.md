# Backend Reuse and Dedup Design

## Goal

Improve repeated-run backend efficiency by adding:

- warm-start subtree reuse across compatible reruns
- transposition-table dedup for equivalent non-root states inside a run

while preserving the current simulation contract that the workflow/report layer consumes.

## Verified Current State

- [SimulationEngine](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/backend-reuse-v1/packages/core/src/forecasting_harness/simulation/engine.py) now runs deterministic multi-step MCTS and returns root-level `branches`.
- [should_reuse_node](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/backend-reuse-v1/packages/core/src/forecasting_harness/simulation/cache.py) already supports dependency-based invalidation from `dependencies.fields`.
- [compare_state_slices](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/backend-reuse-v1/packages/core/src/forecasting_harness/compatibility.py) already compares normalized field values and reports `changed_fields`.
- [WorkflowService.simulate_revision](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/backend-reuse-v1/packages/core/src/forecasting_harness/workflow/service.py) currently compiles a new `BeliefState`, runs the engine from scratch, and writes only the resulting simulation payload.
- Revision lineage already exists through `parent_revision_id` in [RevisionRecord](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/backend-reuse-v1/packages/core/src/forecasting_harness/workflow/models.py).

## Design Summary

The new backend layer should stay deterministic.

Warm start:
- if a revision has a simulated parent revision
- and the new compiled `BeliefState` is structurally reusable against the parent state
- seed matching nodes from the parent simulation tree before the new search iterations run

Transposition dedup:
- within a run, if two different non-root paths reach the same canonical `state_hash`
- share one statistics bucket for that equivalent state
- keep separate root branch outputs so workflow/report behavior stays stable

## Warm-Start Compatibility

The current `compare_state_slices()` result is too narrow for rerun reuse because it only reports field-level compatibility and does not distinguish:

- fully identical state
- structurally reusable state with some changed fields
- incompatible state shape

The new compatibility object should include:

- `compatible`
  - full state compatibility for strict equality / zero-risk reuse
- `reusable`
  - whether subtree reuse is allowed at all
- `changed_fields`
  - normalized field names that changed
- `reasons`
  - structural incompatibility reasons when reuse is blocked

Reuse should be blocked if any of these change:

- `interaction_model`
- `domain_pack`
- actor identity set
- phase
- current epoch
- constraints
- capabilities
- objectives
- unknowns

If those remain stable, field changes alone should still allow subtree reuse for nodes whose dependencies do not overlap those fields.

## Node Reuse Rules

Each cached tree node snapshot should store:

- `node_id`
- `state_hash`
- `depth`
- `branch_id`
- `label`
- `prior`
- `dependencies`
- `visits`
- `value_sum`
- `metric_sums`

When a new child node is created during expansion:

1. Look for a cached node snapshot with the same `node_id`.
2. Require:
   - `state_hash` match
   - `should_reuse_node(snapshot, compatibility)` returns true
3. If both pass, seed the new node statistics from the cached snapshot.

This gives partial subtree reuse without requiring the entire prior tree to be rebuilt up front.

## Transposition Table

The search core should introduce shared statistics buckets for equivalent non-root states.

Important constraint:
- root children must remain separate output branches
- dedup starts below root children

Implementation model:

- each `_SearchNode` keeps path-specific metadata (`node_id`, `branch_id`, `label`)
- statistics move into a shared `_NodeStats` object
- for depth `>= 2`, equivalent `state_hash` values share the same `_NodeStats`

This means:

- separate paths can still appear in the tree
- but they no longer learn independently if they reach the same effective state

## Simulation Payload Additions

The top-level simulation payload should remain workflow-compatible and add backend metadata:

- `search_mode`
- `iterations`
- `node_count`
- `max_depth_reached`
- `state_table_size`
- `transposition_hits`
- `reuse_summary`
- `tree_nodes`

`tree_nodes` should contain compact node snapshots needed for warm-start seeding on later reruns.

`reuse_summary` should contain:

- `enabled`
- `source_revision_id`
- `reusable`
- `changed_fields`
- `reused_nodes`
- `skipped_nodes`

The workflow/report layer can continue to ignore these additions and read only `branches`.

## Workflow Integration

`WorkflowService.simulate_revision()` should:

1. Compile the current approved belief state.
2. Check whether the revision has a simulated parent revision.
3. If so:
   - load parent approved belief state
   - load parent simulation payload
   - build a reuse compatibility object
   - pass a reuse context into `SimulationEngine.run()`
4. Persist the new simulation payload including reuse metadata.

This keeps the search reuse fully backend-driven and invisible to the user-facing workflow.

## Non-Goals

- no UI changes
- no native adapter automation work
- no calibrated real-world probability model
- no validated geopolitical model expansion
- no persistence of a global multi-run transposition database across different runs

## Verification

This milestone is complete when verified facts show:

- a rerun with a compatible parent revision reports `reused_nodes > 0`
- incompatible parent revisions do not reuse nodes
- equivalent non-root states produce `transposition_hits > 0`
- workflow/report tests still pass without changing their basic contracts
