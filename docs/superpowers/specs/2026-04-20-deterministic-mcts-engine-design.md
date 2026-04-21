# Deterministic MCTS Engine Design

## Goal

Replace the current one-step branch enumerator with a deterministic multi-step search engine over `BeliefState` while preserving the existing workflow/report contract that expects a simulation payload with root-level `branches`.

## Verified Current State

- [SimulationEngine](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/mcts-engine-v1/packages/core/src/forecasting_harness/simulation/engine.py) currently validates the state, enumerates one layer of actions, scores each returned state once, and sorts the resulting branches.
- [DomainPack](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/mcts-engine-v1/packages/core/src/forecasting_harness/domain/base.py) already defines the causal boundaries needed for search:
  - `propose_actions`
  - `sample_transition`
  - `score_state`
  - `validate_state`
- [BeliefState](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/mcts-engine-v1/packages/core/src/forecasting_harness/models.py) already carries structured actors, fields, phase, epoch, horizon, and approved evidence ids.
- The workflow/report layer depends on `simulation["branches"]` and summarizes only root-level branch labels and scores.

## Design Summary

The new engine remains deterministic and testable:

- tree nodes hold structured `BeliefState`, not free text
- action generation and transitions come from the active `DomainPack`
- search uses a PUCT-style MCTS loop
- leaf evaluation uses deterministic rollouts plus existing `score_state` metric vectors
- root output remains a sorted `branches` list so the workflow/report layer stays compatible

The engine will not use separate AI agents to role-play actors inside the search loop. Actor-to-actor causality is represented by state transitions: one actor action changes the `BeliefState`, and the changed state alters later available actions, priors, and outcomes.

## Search Model

### Search Config

The engine should accept a small deterministic config:

- `iterations`
- `max_depth`
- `rollout_depth`
- `c_puct`

The engine may provide stable defaults, while domain packs may override them with an optional `search_config()` hook.

### Node Model

Each internal node needs:

- `node_id`
- `state`
- `state_hash`
- `depth`
- `visits`
- `value_sum`
- `prior`
- `children`
- `dependencies`
- aggregated metric sums for mean branch metrics

The search tree is internal implementation detail; the public workflow still receives a compact simulation summary.

### Action / Outcome Normalization

To avoid a breaking rewrite of every domain pack at once, the engine should normalize existing loose action and transition payloads.

Actions:

- accept current dict-shaped action contexts
- support optional keys:
  - `prior`
  - `actor_id`
  - `dependencies`

Outcomes:

- accept current raw next-state returns
- also support richer dict outcomes:
  - `next_state`
  - `weight`
  - `outcome_id`
  - `outcome_label`
  - `dependencies`

If a pack returns only raw states, the engine treats them as deterministic outcomes with equal/default weights.

## MCTS Loop

For each iteration:

1. Validate root state and interaction model.
2. Start at the root node.
3. While the node is expanded and not terminal, select the child with the highest PUCT score.
4. If the selected node is expandable and below depth limit, expand its child set from domain actions and outcomes.
5. Evaluate the chosen leaf:
   - if terminal or depth-limited, score that state directly
   - otherwise run a deterministic rollout policy until terminal or rollout limit
6. Backpropagate scalarized value and metric sums through the selected path.

This yields stable tree statistics for root branches:

- `visits`
- `score` as mean backed-up value
- `metrics` as mean metric vector
- `prior`

## Deterministic Rollouts

The first version should use deterministic rollouts, not stochastic simulation and not LLM actor policies.

Default rollout policy:

- choose the highest-prior action
- choose the highest-weight outcome for that action
- continue until terminal or rollout depth limit

Domain packs may later override rollout behavior with an optional `rollout_policy()` hook, but the core should ship with a deterministic default.

## Domain Pack Extensions

The generic engine should add only minimal optional hooks:

- `search_config() -> dict[str, int | float]`
- `is_terminal(state: BeliefState, depth: int) -> bool`

Existing required methods remain:

- `propose_actions`
- `sample_transition`
- `score_state`
- `validate_state`

This keeps the framework generic. Domain packs supply domain-specific causality; the engine supplies the search algorithm.

## Causality Representation

The engine represents causality through state updates:

- actor A action changes the current state
- changed state changes actor B action priors, legal action set, or outcomes
- later search layers operate on that new state

The engine does not “reason about causality” symbolically. It searches over causal rules already encoded in domain transitions.

## Output Contract

The simulation payload must remain compatible with the workflow:

- keep `branches` at the top level
- each branch represents a root child of the search tree

Recommended branch fields:

- `branch_id`
- `label`
- `score`
- `visits`
- `prior`
- `metrics`
- `dependencies`

Recommended top-level metadata:

- `search_mode: "mcts"`
- `iterations`
- `node_count`
- `max_depth_reached`

The workflow/report layer can ignore the new metadata until needed.

## Reference Pack Upgrade

The `interstate-crisis` pack remains a reference pack, but it must stop being a pure one-step stub. For this milestone it should:

- provide phase-dependent actions
- update phase and a small number of normalized fields during transitions
- produce different follow-on actions after different prior actions
- remain deterministic and testable

This is not a realism milestone. It is a causality-and-search milestone.

## Non-Goals

- no LLM agents inside the search loop
- no open-web reasoning
- no full warm-start subtree reuse in this milestone
- no mature war model
- no multi-domain expansion work beyond maintaining generic engine interfaces

## Verification

This milestone is complete when verified facts show:

- search expands beyond one depth layer
- root branches are ranked from backed-up multi-step values, not single-step scores
- domain packs can change later action availability/probability via state transitions
- existing workflow/report tests still pass with the new simulation payload
