# Generalized Harness V2 Design

Date: 2026-04-20

## Summary

This milestone turns the current workflow prototype into a genuinely reusable forecasting harness without attempting to solve forecast realism yet.

Verified current baseline on `main`:

- the repository already has a reusable run repository, workflow service, revisioned CLI flow, domain-pack base class, and retrieval scaffolding
- the current test suite passes with `84 passed`
- the current gaps are mostly integration gaps, not missing folders or missing architecture

The goal of this milestone is to activate the generic seams that already exist so future domains can plug into the same workflow without editing core code for each new pack.

## Goal

Deliver a generic harness milestone that:

1. discovers domain packs through a registry instead of hardcoded CLI lookup
2. supports pack-driven intake extensions on top of a generic intake schema
3. drafts evidence packets from the local corpus through a deterministic core workflow step
4. persists first-class revision lineage instead of treating revision ids as filenames only

## Non-Goals

This milestone does not attempt to deliver:

- a realistic interstate-crisis simulator
- full MCTS or warm-start tree reuse
- automatic rule extraction from sources
- a polished conversational adapter for Codex or Claude
- open-web retrieval
- multiple mature domain packs

## Why This Milestone Exists

The current repository already has the right top-level architecture:

- `RunRepository` persists revisioned artifacts
- `WorkflowService` owns deterministic run transitions
- `DomainPack` exposes reusable hooks
- `CorpusRegistry` and `SearchEngine` provide local retrieval scaffolding

But several important generic promises are still not true in practice:

- the CLI hardcodes built-in packs
- the intake schema is still shaped around exactly two primary actors
- pack extension hooks are mostly type signatures, not workflow behavior
- evidence packets are still supplied by JSON instead of drafted from retrieval
- revision lineage is implicit rather than stored as a first-class graph

So the next milestone should be integration-focused, not architecture-focused.

## Chosen Approach

This milestone uses a `generic core with pack-owned specialization`.

That means:

- the workflow core stays domain-neutral
- domain packs define extensions, suggestions, and retrieval filters
- the core executes those hooks in deterministic steps
- the reference interstate pack remains only a validation pack

This approach is preferred over:

- adding more interstate-specific sophistication first
- redesigning the whole schema from scratch before wiring existing hooks

Both of those would repeat work instead of converting the existing scaffold into a reusable system.

## Product Boundary

After this milestone, the harness should still be a local deterministic core that an adapter can drive.

The core is responsible for:

- run creation
- revision storage
- pack lookup
- intake validation
- evidence drafting from retrieval
- approval transitions
- belief-state compilation
- simulation and report generation

The adapter remains responsible for:

- natural-language questioning
- drafting candidate answers
- presenting grouped approvals
- deciding when to call core operations

This preserves the architecture already chosen earlier: conversational shell, deterministic core.

## Domain-Pack Discovery

The current CLI uses hardcoded logic for `generic-event` and `interstate-crisis`. That blocks reuse.

### Required change

Introduce a `DomainPackRegistry` that:

- registers pack factories by slug
- lists available slugs
- resolves one pack by slug
- raises a deterministic error for unknown slugs

### Initial scope

`v2` only needs in-process registration for built-in packs. It does not need dynamic plugin loading from arbitrary Python packages yet.

That means the first implementation can register:

- `generic-event`
- `interstate-crisis`

through a central registry module. Future plugin loading can build on the same interface later.

### CLI impact

The CLI should stop using a hardcoded `_pack_for_slug()` function and instead rely on the registry.

It should also expose a simple `list-domain-packs` command so adapters and users can discover supported packs without reading code.

## Generic Intake Schema

The current `IntakeDraft` is still partly reference-pack-shaped:

- `primary_actors` requires exactly two entries
- `trigger` and `current_phase` are named for the interstate pack
- there is no first-class place for pack-specific extension data

### Required change

The workflow should move to a generic intake model with these core sections:

- `event_framing`
- `focus_entities`
- `current_development`
- `current_stage`
- `time_horizon`
- `known_constraints`
- `known_unknowns`
- `suggested_entities`
- `pack_fields`

### Compatibility rule

The model should accept the current interstate-oriented names as input aliases:

- `primary_actors` -> `focus_entities`
- `trigger` -> `current_development`
- `current_phase` -> `current_stage`
- `suggested_actors` -> `suggested_entities`

That keeps the existing workflow slice and tests migratable without breaking every caller at once.

### Pack extensions

`pack_fields` stores pack-specific structured values. The core does not interpret their meaning beyond validation.

`DomainPack.extend_schema()` should remain the source of truth for extension field declarations. For this milestone, the declaration format can stay intentionally small:

- key: field name
- value: simple type name such as `str`, `int`, `float`, or `bool`

The core should validate:

- unknown extension fields are rejected
- declared extension fields are type-checked
- missing extension fields are allowed unless a pack later makes them mandatory

### Pack-level validation

Generic intake validation should stay minimal. Pack-specific structural rules should be enforced by pack hooks.

Example:

- the interstate pack may require exactly two focus entities
- a future market pack may allow one company plus optional sectors

That keeps the workflow reusable while still letting packs be strict where needed.

## Pack-Owned Intake Assistance

Several `DomainPack` hooks already exist but are not consistently used by the workflow.

### Required workflow behavior

The workflow should expose deterministic assistance operations that adapters can call:

- `draft-related-entities`
- `draft-intake-questions`
- `draft-evidence-packet`

The first two are thin wrappers around pack hooks:

- `suggest_related_actors()` becomes related-entity drafting
- `suggest_questions()` becomes pack follow-up drafting

This keeps the adapter thin. The adapter no longer needs to re-implement pack logic in prompts.

### Naming

The hook names can remain unchanged in `DomainPack` for now to minimize churn, but the workflow and docs should present them as generic capabilities, not interstate-only capabilities.

## Retrieval-Backed Evidence Drafting

The repository already has:

- `CorpusRegistry`
- `SearchEngine`
- `draft_evidence_packet()`

but the workflow does not connect them into a real run step.

### Required change

Add a deterministic workflow operation that:

1. loads the intake draft for a revision
2. resolves the domain pack for the run
3. builds a retrieval query from caller input plus pack filters
4. searches the local corpus
5. drafts an evidence packet
6. persists that packet as the revision’s evidence draft
7. records an event

### Query boundary

The caller may provide a free-text retrieval query, but the core must always apply pack-owned filters from `retrieval_filters(intake)`.

This allows a future conversational adapter to say:

- “search for Japan-China Taiwan Strait posture and alliance signaling”

while the core still applies domain-pack constraints consistently.

### Freshness handling

The current `SearchEngine` already uses time-based ranking. This milestone should let the pack influence that ranking through `freshness_policy()`, but keep the implementation simple:

- the search layer may use pack-provided per-tag or per-domain weights
- it does not need a full conflict-aware reranking engine yet

The important change is that freshness becomes part of workflow-backed evidence drafting rather than a dormant hook.

### Persistence

The resulting evidence packet should still store:

- source id
- source title
- reason
- passage ids
- citation refs
- raw passages

The workflow should continue to reason over raw approved passages, not summaries.

## First-Class Revision Lineage

The repository already stores revision-scoped files and a `current_revision_id`, but revision lineage is not persisted as a first-class artifact.

### Required change

Each revision should have a stored metadata record in a dedicated `revisions/` section.

Each record should include:

- `revision_id`
- `status`
- `parent_revision_id`
- `created_at`
- `approved_at`
- `simulated_at`

### Lifecycle behavior

- `start-run` creates only the run record
- the first time a draft is saved for a revision, the revision record is created if it does not already exist
- `approve-revision` updates the revision status to `approved`
- `simulate` updates the revision status to `simulated`

### Rerun lineage

When a new revision is created from an earlier one, callers should be able to pass an optional `parent_revision_id`.

This milestone does not require automatic diffing between revisions. It only requires the lineage metadata to exist and be queryable.

### Repository impact

The repository should provide explicit helpers for:

- saving a revision record
- loading one revision record
- listing revision records for a run in deterministic order

This removes the need to infer revision state indirectly from filenames.

## Belief-State Compilation Changes

The compiler should become intake-schema-aware rather than interstate-name-aware.

### Required change

`compile_belief_state()` should consume the generic intake names:

- `focus_entities`
- `current_development`
- `current_stage`
- `suggested_entities`

It should also carry approved `pack_fields` into the belief state so simulation code can see the extension values without reopening intake artifacts.

### Pack validation

Canonical stage validation should still use `pack.canonical_phases()` until the interface is generalized further.

That means the name `canonical_phases()` can stay for now, but it should be treated as the current pack-level stage vocabulary rather than a core interstate concept.

## CLI Surface

The CLI should keep the existing verified workflow commands, but `v2` should add:

- `list-domain-packs`
- `draft-evidence-packet`

It should also update existing commands to work with:

- the registry-backed pack lookup
- the generic intake schema
- optional `parent_revision_id` where applicable

The CLI remains intentionally file-backed in this milestone. That is acceptable because the goal here is deterministic generic workflow wiring, not the full conversational adapter experience.

## Testing

This milestone should add or update tests for:

- domain-pack registry discovery and unknown-pack failure
- generic intake aliases and normalized field access
- pack-field validation for accepted and rejected values
- workflow-backed evidence drafting from a local corpus
- revision record creation and lifecycle transitions
- parent-child revision lineage
- CLI coverage for new commands

The existing end-to-end workflow tests should remain green after the schema migration.

## Out of Scope but Preserved

The following future work should remain explicitly possible after this milestone:

- real MCTS search
- smarter domain packs
- conversational adapters that call the new deterministic core operations
- richer schema declarations for pack fields
- dynamic external domain-pack plugins
- true warm-start reuse and compatibility scoring

This milestone should make those additions easier by solidifying the reusable workflow surface first.
