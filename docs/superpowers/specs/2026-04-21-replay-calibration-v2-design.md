# Replay Calibration V2 Design

## Goal

Strengthen the repo-owned historical replay loop so it is useful for model validation rather than only regression protection. This pass should:

- expand the built-in replay corpus with more historically anchored cases
- record source attribution and historical context for those cases
- surface concrete calibration failures and weak domains in structured output
- preserve the existing deterministic replay workflow and CLI ergonomics

## Why This Is The Right Next Step

The accepted `main` branch already has:

- deterministic replay execution
- a built-in replay corpus
- calibration summary output
- multiple domain packs with actor-aware behavior

The main verified gaps are:

- the replay corpus is still small
- calibration output is too high-level to guide tuning
- historically anchored case provenance is not modeled explicitly

That means the highest-value work is not more workflow scaffolding. It is better replay coverage plus calibration output that tells us what to fix.

## Approach Options

### Option 1: Add More JSON Cases Only

Pros:
- fastest to ship
- low code churn

Cons:
- does not make calibration output more actionable
- keeps historical provenance implicit

### Option 2: Add Source-Attributed Replay Cases + Richer Calibration Diagnostics

Pros:
- improves both replay quality and calibration usability
- keeps the system deterministic and local-first
- makes future corpus growth safer because cases carry provenance

Cons:
- touches both models and tests
- requires careful case design to avoid noisy expectations

### Option 3: Build Automatic Heuristic Retuning Now

Pros:
- most ambitious calibration loop

Cons:
- high risk of overfitting the still-small replay corpus
- too much behavioral churn for one pass

## Recommendation

Implement Option 2 now.

This adds the missing structure without making the repo auto-retune itself against a still-limited corpus. It creates a better validation surface first, which is the right order.

## Design

### 1. Replay Cases Become Historically Anchored Records

Extend replay cases with optional historical metadata:

- `case_title`
- `time_anchor`
- `historical_outcome`
- `sources`

Each source record should contain enough information to audit where the case came from:

- `title`
- `publisher`
- `url`

This metadata is descriptive only. It must not change the deterministic replay algorithm.

### 2. Calibration Summary Must Explain Failures

Add structured attention items to the calibration summary so the output can answer:

- which cases missed
- how they missed
- which domains are weakest
- whether the miss was on branch label, root strategy, evidence selection, or inferred fields

This should remain machine-readable and deterministic.

Recommended additions:

- per-case `attention_items`
- `failure_type_counts`
- `historically_anchored_case_count`

### 3. Built-In Replay Corpus Should Grow Modestly But Cleanly

Expand the built-in corpus with historically anchored cases chosen to fit the current domain vocabulary and available verified sources.

This pass should prefer cases where:

- the historical event is easy to verify with official or primary documents
- the current domain pack already has a plausible action vocabulary for the scenario
- the expected outcome can be expressed through existing branch labels without inventing new semantics only for replay

### 4. CLI Surface

Keep the existing commands and add the smallest useful extension:

- enhance `summarize-builtin-replay-corpus`
- enhance `summarize-replay-calibration`
- add `list-builtin-replay-cases`

`list-builtin-replay-cases` should expose the anchored case metadata directly so reviewers can inspect the corpus without opening JSON files manually.

### 5. Testing

Add or extend tests for:

- replay metadata parsing
- corpus summary counts
- calibration attention item generation
- CLI output for the new list command
- end-to-end replay suite on the expanded corpus

### 6. Non-Goals

This pass should not:

- add online APIs
- add probabilistic retuning
- rewrite MCTS
- build a large-scale knowledge compiler
- package the Codex/Claude runtime integration

## Success Criteria

This pass is successful if:

- the built-in replay corpus is larger and source-attributed
- calibration summaries identify concrete misses instead of only aggregate scores
- the full test suite passes
- the built-in replay suite stays green on the accepted expectations after any necessary pack tuning
