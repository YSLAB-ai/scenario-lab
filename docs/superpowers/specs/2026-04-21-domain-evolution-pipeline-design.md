# Domain Evolution Pipeline Design

Date: 2026-04-21

## Goal

Add a repo-owned, domain-scoped self-improvement pipeline that can:

- accept explicit user suggestions
- detect replay/calibration weaknesses
- synthesize candidate domain knowledge changes
- verify those changes against tests and replay metrics
- promote only verified domain-only changes onto a standalone review branch

The core search/retrieval/workflow algorithm remains protected. The pipeline may improve domain knowledge, not the generic harness.

## Design Constraints

- `only use verified facts`
- one domain at a time
- no automatic merge to `main`
- algorithmic core must not be edited by evolution runs
- promotion requires non-regression plus measurable improvement or meaningful new coverage

## Editable Surface

Evolution runs may write only domain-owned assets:

- `packages/core/src/forecasting_harness/domain/<slug>.py`
- `knowledge/domains/<slug>.json`
- `knowledge/replays/<slug>.json`
- domain-specific tests and status notes

The first implementation will prefer manifest-owned overlays so most evolution runs can improve behavior without rewriting Python pack code.

Protected surfaces:

- `packages/core/src/forecasting_harness/simulation/*`
- `packages/core/src/forecasting_harness/retrieval/*`
- `packages/core/src/forecasting_harness/workflow/*`
- `packages/core/src/forecasting_harness/replay.py`
- generic shared models

If an evolution run appears to require those files, the run is rejected as out of scope.

## Architecture

### 1. Suggestion Store

Store user and self-detected inputs under `knowledge/evolution/`:

- `suggestions/<slug>.jsonl`
- `baselines/<slug>/...`
- `reports/<slug>/...`
- `failed/<slug>/...`

Each suggestion record contains:

- `suggestion_id`
- `timestamp`
- `domain_slug`
- `provenance` (`user` or `self-detected`)
- `category`
- `target`
- `text`
- `terms`
- `status`

Categories for v1:

- `state-field`
- `action-bias`
- `evidence-category`
- `semantic-alias`
- `replay-gap`

### 2. Manifest-Owned Adaptive Overlays

Extend `knowledge/domains/<slug>.json` with optional adaptive sections:

- `adaptive_state_terms`
- `adaptive_action_biases`
- `adaptive_semantic_alias_groups`

These overlays let a built-in pack improve without editing the MCTS core.

Example intent:

- a new phrase can strengthen inference of an existing state field
- a replay miss can bias one root strategy upward when certain terms appear
- a user-provided synonym can improve semantic retrieval and evidence packet quality

### 3. Domain Pack Integration

Domain packs continue to own their domain logic, but selected packs will read adaptive manifest overlays through shared helpers.

For v1:

- state inference can receive manifest-driven term boosts
- action priors can receive manifest-driven bias deltas
- semantic alias groups can expand retrieval automatically

This keeps evolution localized to domain knowledge while preserving deterministic behavior.

### 4. Weakness Analysis

Replay/calibration weaknesses are analyzed per domain.

Inputs:

- builtin replay corpus for that domain
- current calibration summary
- per-case misses

Outputs:

- weakness brief with failing root strategies, missing coverage, and candidate term sources

Self-detected weaknesses become suggestion records with provenance `self-detected`.

### 5. Evolution Run

`run-domain-evolution` flow:

1. load pending suggestions for one domain
2. analyze replay weaknesses for the same domain
3. synthesize candidate manifest updates from both inputs
4. snapshot pre-change metrics
5. apply candidate updates in the current working tree
6. run targeted tests, full suite, domain replay, and calibration summary
7. compare before/after metrics
8. if promotion criteria pass, create/update a dedicated branch and commit
9. write a report and baseline diff

### 6. Promotion Rule

Hard requirements:

- all verification commands pass
- no regression in existing domain replay accuracy
- no regression in existing root-strategy accuracy
- no regression in evidence-source accuracy

Promotion allowed only when at least one is true:

- replay accuracy improves
- root-strategy accuracy improves
- inferred-field coverage improves
- new replay or capability coverage is added without regression

## CLI Surface

### `forecast-harness record-domain-suggestion`

Append one suggestion record to the domain suggestion log.

### `forecast-harness analyze-domain-weakness`

Run replay analysis for one domain and emit a weakness brief plus any self-detected suggestions.

### `forecast-harness run-domain-evolution`

Run one evolution pass for one domain, verify it, and if successful promote it to a standalone review branch.

### `forecast-harness summarize-domain-evolution`

Show latest baselines, candidate metrics, branch name, and promotion outcome for one domain.

## Git Promotion Model

Branch naming:

- `codex/domain-evolution-<slug>-<YYYYMMDD>`

The pipeline may:

- create or update that branch
- commit only domain-owned changes plus evolution notes

The pipeline may not:

- merge to `main`
- push unrelated files

## Verification

Required verification for each successful evolution run:

- targeted domain tests
- full `packages/core` test suite
- domain replay evaluation
- calibration summary before and after

## Non-Goals

- automatic merge to `main`
- automatic changes to the MCTS algorithm
- open-web knowledge acquisition
- neural retraining
- silent editing of generic framework files

## Expected Outcome

After this feature lands, future domain-pack improvement can happen through repo-owned knowledge overlays and replay-driven branch promotion, instead of ad hoc manual edits to the built-in packs.
