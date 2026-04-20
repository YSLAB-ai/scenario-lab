# Forecasting Harness V1 Design

## Summary

This document defines `v1` of a local-first, interactive forecasting harness for Codex and Claude Code. The product is a `scenario exploration and probabilistic forecasting engine`, not a system that claims to predict reality with certainty.

The design separates:

- a shared `core harness` that owns retrieval, run artifacts, belief-state compilation, simulation, and reporting
- thin `agent adapters` for Codex and Claude Code that own the analyst-facing workflow
- `domain packs` that inject domain-specific schema extensions, action generation, transition logic, and heuristic scoring

`v1` is designed around curated local corpora, explicit provenance, user approval before simulation, saved rerunnable forecast artifacts, and transparent scenario reporting.

## Product Goals

- Provide an interactive analyst workflow inside Codex or Claude Code.
- Build a structured belief state from user input plus curated evidence.
- Run heuristic-guided MCTS over the approved belief state.
- Return ranked scenario families, assumptions, and cited drivers.
- Preserve enough artifact history to audit, reopen, and update runs when the user supplies new developments.
- Keep the framework generic at the workflow and interface level while allowing domain-specific logic through domain packs.
- Model bounded rationality and actor-specific behavior instead of assuming that theoretical playbooks are followed mechanically.

## V1 Non-Goals

- Automatic rule extraction from books or other sources.
- Open-web retrieval.
- Claims that MCTS visit counts are real-world probabilities.
- A single universal ontology that is highly accurate across all domains without domain specialization.
- Fully autonomous forecasting without analyst approval.

## Fixed V1 Constraints

The following constraints were chosen during design discussion:

- `local-first`
- `interactive analyst workflow`
- `curated corpus only`
- `PDF + Markdown + CSV/JSON datasets`
- `approval gate before simulation`
- `scenario report` as the primary output
- `analyst workbench` as a required transparency output
- `saved, updateable runs`
- `user-supplied updates only`

## Core Modeling Principle

The engine must not treat economic, diplomatic, or strategic theories as absolute laws.

In this system, theories are treated as:

- structured heuristics
- causal hints
- candidate constraints
- candidate scoring signals

They are not treated as guarantees of behavior.

The design therefore assumes `bounded rationality`, incomplete information, institutional friction, misperception, domestic incentives, and actor-specific style as normal conditions rather than edge cases.

## Product Shape

The product is one forecasting harness with two supported agent front ends:

- a `Codex adapter`
- a `Claude Code adapter`

The adapters should expose different installation instructions because the host environments differ. The core harness remains shared.

The repository should read as one product with two installation paths, not as two unrelated products.

Recommended high-level layout:

```text
packages/
  core/
adapters/
  codex/
  claude/
docs/
  quickstart.md
  install-codex.md
  install-claude-code.md
  architecture.md
.forecast/
```

## Architecture

### Layering

The system has three main layers:

1. `Agent adapters`
2. `Core harness`
3. `Local artifact store`

The adapters own user interaction. The core owns deterministic logic and durable artifacts. The artifact store preserves provenance and replay state.

### Agent Adapters

The Codex and Claude adapters are thin orchestration layers. They are responsible for:

- intake questioning
- follow-up clarification
- evidence review prompts
- assumption approval prompts
- run commands into the core harness
- report presentation in the host agent environment

They are not responsible for:

- retrieval index ownership
- belief-state persistence
- simulation logic
- artifact schema definition

### Core Harness

The core harness owns:

- corpus registry and retrieval
- forecast run artifact management
- belief-state compilation
- domain-pack coordination
- simulation execution
- scenario aggregation
- report and workbench generation
- query-oriented summaries for progressive disclosure in the agent adapters

### Local Artifact Store

The local artifact store keeps state under a project-local directory so both adapters use the same durable data.

Recommended root:

```text
.forecast/
```

## Core Interfaces

`v1` should be organized around five explicit core objects.

### CorpusRegistry

Responsibilities:

- register local sources
- store source metadata
- manage chunk metadata
- manage embedding/index references
- support citation-safe passage retrieval

The registry does not interpret sources as rules in `v1`. It only makes evidence discoverable and traceable.

### ForecastRun

Responsibilities:

- represent one analyst session as a durable artifact bundle
- link intake, evidence, assumptions, belief state, search configuration, scenarios, and output documents
- preserve rerun lineage across updates

### BeliefState

Responsibilities:

- represent the structured world snapshot the engine actually searches
- store observed fields, inferred fields, and explicit unknowns
- tie important fields to evidence and confidence metadata
- represent actors, objectives, capabilities, constraints, and time horizon
- store warm-start-critical fields in normalized typed form rather than relying on raw prose

### DomainPack

Responsibilities:

- extend the generic schema for a domain
- help propose analyst questions
- generate plausible next actions
- provide transition logic
- provide heuristic scoring logic
- validate domain-specific state consistency

Domain packs do not own workflow, retrieval storage, or global artifact schemas.

### SimulationEngine

Responsibilities:

- selection
- expansion
- transition sampling
- rollout or leaf evaluation
- backpropagation
- scenario family aggregation

## Domain-Pack Contract

The minimum `v1` domain-pack interface should include:

- `extend_schema()`
- `interaction_model()`
- `suggest_questions()`
- `propose_actions(state)`
- `sample_transition(state, action_context)`
- `score_state(state)`
- `validate_state(state)`

Purpose of each method:

- `extend_schema()`: add domain-specific state fields to the generic belief-state schema
- `interaction_model()`: declare whether the domain uses `event_driven`, `sequential_turn`, or `simultaneous_move` mechanics
- `suggest_questions()`: recommend domain-specific follow-up questions to improve the intake workflow
- `propose_actions(state)`: return plausible next actions with priors and justifications
- `sample_transition(state, action_context)`: generate possible next states and uncertainty notes using an action context that can include an initiating event, participating actors, simultaneous actions, contingent responses, and a time window
- `score_state(state)`: return a multi-metric heuristic vector for evaluation
- `validate_state(state)`: flag contradictions, unsupported assumptions, and missing critical fields

Optional `v1` domain-pack hooks may include:

- `freshness_policy()`: define field-specific temporal weighting for retrieval and state drafting
- `default_objective_profile()`: define domain defaults for scalarizing multi-metric evaluation vectors

## Generic Shared Ontology

The generic layer should stay narrow and reusable. It should include shared concepts such as:

- `Actor`
- `BehaviorProfile`
- `Objective`
- `Capability`
- `Constraint`
- `StateVariable`
- `Action`
- `Observation`
- `Hypothesis`
- `RuleReference`
- `Scenario`
- `OutcomeMetric`

This ontology is meant to support workflow and interfaces, not to replace domain-specific modeling.

### BehaviorProfile

`BehaviorProfile` is a first-class concept in the generic layer. It exists to prevent the engine from collapsing into a rational-actor-only model.

A behavior profile may include:

- documented decision style traits
- risk tolerance or risk asymmetry
- escalation tolerance
- responsiveness to domestic political pressure
- responsiveness to prestige, ego, or status threats
- preference for improvisation versus process
- institutional discipline versus personalization of decisions
- history of bluffing, delay, or overreaction

These fields should be evidence-backed where possible and explicitly marked as inferred when they are not directly observed.

## Execution Model

The engine does not search over raw text or reality. It searches over an approved structured belief state.

### Interaction Mechanics

The engine must not assume a strictly alternating turn structure.

Each domain pack must declare an explicit interaction model:

- `event_driven`
- `sequential_turn`
- `simultaneous_move`

The recommended default for real-world forecasting is `event_driven`, because many domains are better represented as timelines of decisions, reactions, and external events rather than clean alternating turns.

When a domain requires same-epoch conflict between actors, the transition layer should be able to resolve:

- single-actor initiated events
- joint actions by multiple actors
- contingent responses within a time window

This keeps the search model aligned with real systems such as crises, markets, and negotiations where multiple actors can act effectively at once.

### End-to-End Flow

1. The adapter gathers user framing and scope.
2. The core retrieves candidate evidence from the curated local corpus.
3. The core drafts actors, objectives, capabilities, constraints, unknowns, and assumptions.
4. The adapter presents evidence and assumptions for user approval.
5. The core compiles an approved `BeliefState`.
6. The simulation engine runs heuristic-guided MCTS from that root state.
7. The core aggregates branches into scenario families.
8. The adapter presents a scenario report and analyst workbench.
9. The run is saved so it can be reopened and updated later.

### Root State

Each root `BeliefState` should contain:

- observed variables
- uncertain variables with confidence
- active actors
- actor behavior profiles
- actor objectives
- actor capabilities
- hard and soft constraints
- explicit unknowns
- time horizon and current epoch
- evidence links for important fields

### Action Generation

At each step, the active domain pack proposes plausible next actions or events. Hard constraints remove impossible actions. Heuristic priors rank the remaining actions.

Those priors must be allowed to depend on:

- structural conditions
- actor-specific behavior profiles
- institutional context
- retrieved historical analogs
- recent update artifacts that change incentives or perceptions

This prevents the action model from assuming that every actor behaves as a clean utility maximizer.

The action generator should emit contexts consistent with the chosen interaction model. In practice, that means the engine may expand:

- a single next event
- a joint action bundle
- an initiating action plus a response window

### MCTS Loop

`v1` should use a conservative MCTS variant such as a `PUCT-like` loop:

- select nodes using priors and accumulated value
- expand the top `k` actions instead of the full branching set
- sample next states from an explicit transition model
- run a cheap rollout policy or leaf evaluation
- backpropagate scalarized value while preserving the full evaluation vector for reporting and audit

### Leaf Evaluation

Leaves should be scored on a vector rather than a single scalar win/loss metric. Example dimensions may include:

- escalation level
- political survivability
- economic stress
- military advantage
- negotiation probability

Domain packs may adjust these dimensions, but the core should support multi-metric scoring by default.

Standard PUCT-style selection still needs a scalar for node selection and backpropagation. For `v1`, the engine should:

- keep the full evaluation vector at each node
- compute a scalarized search value from that vector during selection and backpropagation
- preserve both the raw vector and the scalarization policy in run artifacts

The scalarization policy should come from an explicit `objective profile` rather than being hidden in code.

The evaluator should also support a distinction between:

- `normative expectation`: what formal models would favor
- `behavioral expectation`: what the specific actor is more likely to do

When these diverge, the workbench should show that divergence explicitly.

### Objective Profiles

Every run should carry an analyst-visible objective profile that defines how the search prioritizes tradeoffs.

An objective profile may include:

- metric weights
- hard veto thresholds
- risk tolerance
- asymmetry penalties

If the analyst does not choose custom weights, the engine may use domain-pack defaults, but those defaults must still be visible in the run artifacts.

### Scenario Aggregation

Similar terminal branches should be merged into scenario families. The user-facing output is a ranked scenario report, not a single predicted answer.

### Probability Semantics

The system must not present MCTS visit counts as real-world probabilities. In `v1`, reported likelihoods are derived from the model's own branch mass and transition assumptions. Historical calibration is a future validation layer, not a solved `v1` feature.

## Search Controls

To keep the engine usable in `v1`, the simulation layer should support:

- discrete time buckets such as `day`, `week`, or `phase`
- top-`k` action pruning
- depth limits
- state hashing and transposition handling
- explicit `unknown` markers instead of forcing false precision
- configurable rollout budgets and heuristic weights
- explicit objective weights or named objective profiles
- optional warm-start reuse of compatible prior search trees

## Artifact Model

Each forecast run should be stored under:

```text
.forecast/runs/<run-id>/
```

Recommended files:

```text
.forecast/
  corpus/
    registry.json
    chunks/
    embeddings/
  domains/
    shared/
    conflict/
    elections/
  runs/
    run-2026-04-19-example/
      intake.json
      evidence.json
      assumptions.json
      belief-state.json
      tree-config.json
      tree-summary.json
      tree-cache/
      report.md
      workbench.md
      updates/
```

### File Responsibilities

- `intake.json`: original user framing, scope, horizon, and selected domain packs
- `evidence.json`: the exact retrieved passages used during state building, each tied to source metadata and stable citation locations
- `assumptions.json`: user-approved assumptions and their lifecycle state
- `belief-state.json`: the approved structured state used by the engine
- `tree-config.json`: search parameters such as horizon, branching cap, heuristic weights, rollout budget, seed policy, interaction model, and objective profile
- `tree-summary.json`: a compact summary of explored branches, scenario families, visit counts, and branch mass
- `tree-cache/`: optional machine-oriented cached search state used for compatible warm-start updates
- `report.md`: the user-facing scenario report
- `workbench.md`: the analyst-facing trace of evidence, assumptions, branching logic, and main drivers
- `updates/`: timestamped user-supplied developments appended after the initial run

## Field-Level Provenance

Important belief-state fields should carry metadata such as:

- `value`
- `normalized_value`
- `status`: `observed`, `inferred`, or `unknown`
- `supporting_evidence_ids`
- `confidence`
- `last_updated_at`

This keeps the engine auditable and prevents uncited fields from being treated as facts.

For fields that matter to simulation compatibility, `normalized_value` should prefer:

- numeric scales
- bounded ordinals
- enums
- canonical structured objects

over free-text descriptions. Free text may still exist for analyst readability, but compatibility decisions should be based on the normalized form whenever possible.

For actor behavior fields, the artifact model should also support:

- `evidence_type`: direct quote, historical action, secondary analysis, or analyst inference
- `time_scope`
- `applicability_notes`

This reduces the risk of turning a loose character judgment into a permanent engine assumption.

## Update Model

Updates should append, not overwrite.

When a user supplies a new development:

1. ingest the new material as a new update artifact
2. identify which assumptions or state fields are affected
3. draft a revised belief state
4. require user approval again
5. decide whether the update is compatible with warm-start tree reuse or requires a cold restart
6. rerun the simulation from the revised root
7. preserve linkage to previous runs and superseded assumptions

This creates an evolving forecast history instead of one mutable blob.

### Cold Start vs Warm Start

The engine should be explicit about whether an update triggers:

- a `cold start`, which discards prior search state
- a `warm start`, which reuses compatible portions of the prior search tree

Warm start is preferred when:

- the revised belief state can be mapped onto prior node state hashes with acceptable compatibility
- the interaction model is unchanged
- the objective profile is unchanged or compatible
- the update changes only a local portion of the prior scenario space

Cold start is required when:

- the update invalidates core state assumptions
- the domain pack changes
- the objective profile changes materially
- prior cached subtrees cannot be trusted under the revised state

This matters because analysts will often inject minor developments, and throwing away every prior tree would make the interactive loop slower and more expensive than necessary.

### State Compatibility

Warm-start compatibility must not be defined by brittle exact hashing over raw belief-state text.

The engine should instead use a schema-aware compatibility procedure:

1. compare normalized typed state fields rather than display text
2. classify changed fields by domain importance and dependency scope
3. measure change magnitude using field-specific rules
4. invalidate only the cached nodes whose dependency sets intersect materially changed fields
5. reuse unaffected cached nodes when compatibility remains above domain-defined thresholds

This means a wording change such as `high` to `very high` should not automatically force a cold restart if both values normalize to a nearby ordinal or numeric range and the affected field does not materially alter most of the explored tree.

### Compatibility Inputs

The compatibility decision should consider:

- normalized field deltas
- domain-pack-defined tolerance thresholds
- interaction model compatibility
- objective profile compatibility
- dependency masks for expansion, transition, and scoring logic
- confidence shifts in critical fields

### Dependency-Aware Invalidation

Each cached subtree should record which state fields or derived features materially influenced:

- action generation
- transition sampling
- heuristic scoring
- scalarized search value

When an update arrives, the engine should invalidate cached nodes based on those recorded dependencies rather than treating the belief state as one indivisible blob.

### Hashing Strategy

Cryptographic hashes may still be used for exact cache keys after canonicalization, but they should operate on normalized structured state slices rather than raw prose.

Approximate similarity methods such as semantic hashing, vector similarity, or locality-sensitive hashing may be used to find candidate reusable nodes faster, but they should be treated as accelerators only.

They should not be the sole correctness criterion for tree reuse, because semantically similar states can still have materially different transition behavior in a domain-specific model.

## Retrieval Architecture

`v1` retrieval is `evidence-first`, not `answer-first`. The goal is to retrieve defensible passages that help build or revise the belief state.

### Retrieval Layers

#### Document Registry

The document registry should store:

- author
- title
- edition or version
- publication date
- source type
- domain tags
- geography tags
- time coverage
- trust tier

For behavior-aware forecasting, the registry should also support tagging for:

- actor identity
- institution identity
- event type
- decision episode

#### Citation-Safe Chunking

Each chunk must map back to an exact location:

- page range for PDF
- heading or section for Markdown
- row range for CSV/JSON-derived tables

No chunk should exist without a stable citation target.

#### Hybrid Retrieval

Use semantic search plus structured filters.

Semantic search finds conceptually relevant passages.

Structured filters narrow by:

- domain pack
- source type
- date range
- actor
- geography
- trust tier
- event type
- institution

Hybrid retrieval should also support field-specific temporal weighting. The ranking model should not treat recency as a universal rule, but it also should not let stale evidence dominate fast-changing fields.

The retrieval layer should therefore support:

- freshness-sensitive ranking by field or evidence type
- stronger recency penalties for rapidly changing signals such as inventory levels, supply chains, market conditions, and battlefield disposition
- slower decay for longer-lived signals such as doctrine, institutional style, and some legal or treaty constraints
- conflict-aware reranking so newer evidence usually outranks older conflicting evidence for the same field when the field is freshness-sensitive

#### Run-Scoped Evidence Selection

Retrieved passages are candidate evidence, not automatic inputs. Only selected evidence should enter `evidence.json` for a run.

### Retrieval Modes

`v1` should distinguish:

- background corpus indexing
- interactive retrieval during intake and state drafting
- update retrieval against user-supplied new materials
- historical analog retrieval for actor and institution behavior priors

### Retrieval Quality Bias

The interactive loop should optimize for precision over recall. Returning one highly relevant passage is better than flooding the analyst with weak evidence that contaminates the state draft.

This is especially important for behavioral modeling. Weakly sourced claims about a leader's personality or a CEO's style can distort the simulation more than a missing low-value datapoint.

It is also important for freshness-sensitive data. Pulling an outdated but semantically relevant source can be worse than missing a marginal source if the outdated source silently drafts obsolete constraints into the belief state.

### Future Compatibility

The retrieval layer should leave room for a later rule-mining pipeline, but `v1` retrieval returns passages and metadata only.

## Approval and Trust Model

`v1` should be conservative by default.

The harness must be allowed to say:

- `insufficient evidence`
- `state too underspecified`
- `domain pack not mature enough`

instead of forcing a forecast.

### Operating Rules

- No critical belief-state field without either evidence or an explicit `inferred` / `unknown` marker.
- No simulation before user approval of evidence-backed state and assumptions.
- No silent overwrite when updates arrive.
- No single-answer framing for outputs.
- No implied certainty from search metrics.
- No treating descriptive theories as deterministic behavioral laws.
- No actor-style field without provenance and scope notes.

### Failure Conditions to Surface

- missing critical variables for the chosen domain pack
- conflicting evidence across trusted sources
- unsupported extrapolations beyond source scope
- branching explosion that makes the run low-value
- stale or superseded assumptions after an update
- overreliance on rational-actor assumptions where actor-specific evidence suggests otherwise
- behavioral priors based on weak or stale evidence

## Outputs

### Scenario Report

The primary output is a ranked scenario report that includes:

- scenario families
- relative likelihood inside the model
- key assumptions
- main causal drivers
- supporting citations
- major uncertainty areas

### Analyst Workbench

The analyst workbench is required, not optional. It should show:

- selected evidence
- the approved assumptions set
- the draft and final belief-state structure
- dominant branches
- the main reasons the engine favored those branches
- warnings and maturity caveats

The adapters must use progressive disclosure when presenting this material. They should not load the full workbench or raw tree artifacts into the active context by default.

Instead, the core harness should expose query-oriented views such as:

- `summarize_top_branches(limit)`
- `get_branch(branch_id)`
- `get_evidence_for_assumption(assumption_id)`
- `get_state_field(field_path)`
- `diff_run_updates(previous_run_id, current_run_id)`

This keeps Codex and Claude Code usable under finite context windows while preserving access to full artifacts on demand.

### Reusable Run Artifact

Every run should be reopenable and updateable when the user supplies new information. The artifact store is part of the product, not an implementation detail.

## Validation Strategy

Historical replay and calibration should be part of the architecture even if `v1` contains only limited support for them.

The purpose is not to prove perfect prediction. The purpose is to test whether the framework produces useful ranked scenarios under the information available at the time.

The design should reserve space for:

- replayable historical cases
- baseline comparisons
- calibration metrics
- domain-pack maturity notes
- actor-specific and institution-specific historical behavior libraries

Validation should eventually compare at least three forecasting modes:

- structure-only baselines
- theory-heavy heuristic search
- behavior-aware search using historical analogs and actor profiles

That comparison is important because it tests whether the added behavioral layer improves forecasts instead of only making the outputs sound more realistic.

## Packaging and Installation

The project should ship as:

- one shared local core harness
- one Codex adapter
- one Claude Code adapter

Recommended installation model:

- shared core install instructions
- Codex-specific install instructions
- Claude Code-specific install instructions

This is better than forcing one fake-universal installation path because the host environments use different extension surfaces.

The intended user experience is still seamless:

- install the core harness once
- install the appropriate adapter
- use the same local `.forecast/` artifacts regardless of host agent

## Recommended V1 Technology Direction

This document does not lock the implementation language, but the design assumes:

- a local CLI or library as the shared engine
- local storage for artifacts and indexes
- adapter wrappers that call into the shared engine

The engine should be built so future features such as automatic rule extraction, richer calibration, and additional domain packs can be added without replacing the workflow or artifact model.

## Rationale for the Chosen Approach

Three approaches were considered:

1. workflow-first all-in-one plugin
2. harness core plus interactive plugin adapters
3. ontology platform first

Approach `2` was selected because it:

- preserves the interactive analyst experience
- keeps retrieval, state construction, simulation, and reporting explicit and auditable
- provides a clean integration point for future rule extraction
- avoids both a tangled all-in-one workflow and an overabstract ontology-first project

## V1 Success Criteria

`v1` is successful if it can:

- guide an analyst through event framing and follow-up questions
- retrieve citation-safe evidence from a curated local corpus
- compile an auditable belief state
- require explicit approval before simulation
- run heuristic-guided MCTS over that state
- produce a transparent scenario report and analyst workbench
- save rerunnable forecast artifacts
- accept user-supplied updates and rerun without losing history

## Conclusion

`v1` should be built as a local-first forecasting harness with a shared engine, thin agent adapters, explicit provenance, conservative trust rules, and saved updateable forecast runs. The generic layer should standardize workflow and interfaces, while the real forecasting intelligence remains domain-specific through domain packs.
