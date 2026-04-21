# Actor Utility And Run Lens Design

## Summary

The forecasting harness should stop treating objective selection as a single fixed preset chosen independently of the actors in the case. Instead, each major actor should receive its own inferred utility lens, derived deterministically from approved evidence, case framing, and replay-backed domain defaults. The MCTS engine should continue to use one scalar score for search, but that score should come from a run-level aggregation lens that combines actor-specific utilities plus shared system metrics.

This preserves deterministic search and interpretable ranking while making the tree more realistic: actors no longer implicitly value the same things, and branch differentiation comes from conflicting incentives rather than from a single shared preference vector.

## Goal

Improve analytical depth and causal realism by separating:

- actor-specific motives and sensitivities
- run-level branch ranking

The system should answer two distinct questions:

- what is each actor likely to try to do?
- under this run's aggregation lens, which searched branches rank highest?

## Non-Goals

This change does not:

- remove the need for one scalar branch score in MCTS
- introduce LLM calls inside the search loop
- allow the domain-evolution pipeline to edit shared search logic
- replace the existing deterministic workflow with opaque learned behavior

## Current Problem

The repo currently uses one run-level `ObjectiveProfile` in `packages/core/src/forecasting_harness/objectives.py`. That profile scalarizes terminal metrics for MCTS. This is structurally convenient, but it makes all actors implicitly share the same ranking logic.

That causes two weaknesses:

- actor reactions are too homogeneous because branch incentives are not explicitly differentiated per actor
- the system conflates likely behavior with preferred outcome

For example, in an interstate crisis, China, Taiwan, the United States, and Japan may all tolerate escalation, domestic stress, reputational cost, or negotiation very differently. A single profile can rank branches, but it should not stand in for those distinct motives.

## Core Design

### 1. Actor Utility Lens Per Actor

Each major actor gets an inferred utility lens. This is not a moral judgment or true psychology. It is an explicit modeled assumption derived from approved evidence and domain heuristics.

Initial utility dimensions should include:

- `domestic_sensitivity`
- `economic_pain_tolerance`
- `negotiation_openness`
- `reputational_sensitivity`
- `alliance_dependence`
- `coercive_bias`

Domain packs may extend or specialize these dimensions later, but the first implementation should keep a shared core set so the workflow and reports stay generic.

These values should live on each actor's `BehaviorProfile` or an adjacent actor-owned utility structure inside the `BeliefState`.

### 2. Run-Level Aggregation Lens

The engine still needs one scalar branch score. Per-actor utilities alone are not enough for MCTS because the engine must backpropagate one value.

So each run also has one explicit aggregation lens that combines:

- actor-specific branch utilities
- shared system metrics
- destabilization penalties

Recommended initial aggregation modes:

- `balanced-system`
- `focal-actor`

Deferred modes:

- `fragility-aware`
- `coalition-weighted`

The initial default should be `balanced-system`.

### 3. Separation Of Concerns

The system must keep these concepts separate:

- actor utility lens: what an actor appears to care about
- run aggregation lens: how the harness ranks full branches

This preserves interpretability and avoids treating predicted motives as if they were the user's preferred evaluation rule.

## Inference Model

### Deterministic Preference Inference

Actor utility inference should happen during belief-state compilation, after intake and evidence approval but before simulation.

Inputs:

- approved evidence items
- intake framing
- known constraints and unknowns
- domain heuristics
- replay-backed domain defaults where available

Requirements:

- deterministic
- local-only
- revisioned and auditable
- no LLM in the search loop

This inference should produce explicit actor utility fields stored in the approved belief state.

### System-Recommended Aggregation Lens

The harness should no longer treat run-level lens selection as only a manual preset.

Instead, it should draft a recommended aggregation lens from:

- event framing
- inferred actor utilities
- approved evidence
- domain-pack heuristics

The recommendation remains explicit and user-approvable.

## Search Behavior

### Where Actor Utilities Matter

Actor-specific utilities should primarily affect:

- action priors in `propose_actions()`
- transition branching and weights in `sample_transition()`
- reaction patterns by actor

They should not replace the run-level scalarization step.

### Where Aggregation Matters

The aggregation lens determines the `aggregate_score` used by MCTS. The engine should continue to backpropagate one scalar value.

Each branch should produce:

- `actor_metrics[actor_id]`
- `system_metrics`
- `aggregate_score`

The first implementation can derive `aggregate_score` from:

- weighted focal actor utilities
- weighted external actor utilities
- shared system metrics such as escalation and economic disruption
- a destabilization penalty when one major actor is pushed into an unstable corner

## Workflow Changes

The grouped approval step should gain two explicit sections:

- `Inferred actor preferences`
- `Recommended run lens`

The user should be able to:

- approve both
- edit them
- or override the recommended run lens

The report should then show:

- the inferred utility lens for each major actor
- the run aggregation lens used for ranking
- how the top branch helped or hurt each actor
- how the final branch score was formed

## Repo Integration

### Models

Extend `BehaviorProfile` in `packages/core/src/forecasting_harness/models.py` with explicit utility-preference fields.

### Compiler

Extend `packages/core/src/forecasting_harness/workflow/compiler.py` so belief-state compilation infers actor utilities deterministically from approved evidence and case framing.

### Objectives

Extend `packages/core/src/forecasting_harness/objectives.py` so it can:

- keep named aggregation modes
- recommend a run lens from the compiled state

### Domain Packs

Start with `packages/core/src/forecasting_harness/domain/interstate_crisis.py`.

That pack should consume actor utility signals when:

- proposing actions
- weighting transition outcomes
- shaping same-stage response logic

Other packs can adopt the same pattern incrementally.

## Reporting

Reports should stop presenting the objective profile as if it were the entire preference story.

They should instead expose:

- actor utility summary by major actor
- aggregation lens summary
- branch-level actor impacts
- branch-level aggregate score explanation

This should improve the "story" quality of the report without allowing narrative text to drift away from the searched branch.

## Testing

The first implementation should add tests for:

- deterministic actor utility inference from approved evidence
- aggregation-lens recommendation
- changed action ranking when actor utility inputs change
- unchanged deterministic MCTS behavior given fixed inputs
- reporting of actor utility and aggregate scoring

Replay coverage should include at least one case showing that different actor utility lenses change branch ranking in a sensible way without breaking existing replay infrastructure.

## Risks

### Overfitting Actor Psychology

Risk:

- inferred utilities may look precise while being weakly supported

Mitigation:

- keep utility fields explicit, reviewable, and grounded in approved evidence

### Confusing Actor Utility With User Preference

Risk:

- users may mistake actor motives for the branch-ranking lens

Mitigation:

- present both separately in the workflow and reports

### Complexity Explosion

Risk:

- every pack may start inventing incompatible utility dimensions

Mitigation:

- start with a shared core set of actor utility fields and extend cautiously

## Rollout

Recommended order:

1. extend actor models with utility fields
2. add deterministic inference during compilation
3. add run-level aggregation recommendation
4. thread actor utilities into `interstate-crisis`
5. expose new approval/report sections
6. expand to other packs after the first pack proves stable

## Success Criteria

This design is successful when:

- actor reactions become more differentiated across the same case
- the engine still uses deterministic MCTS with one scalar branch score
- reports explain both actor motives and branch ranking clearly
- deeper runs explore more meaningfully different branches because incentives differ by actor rather than by a single shared objective vector
