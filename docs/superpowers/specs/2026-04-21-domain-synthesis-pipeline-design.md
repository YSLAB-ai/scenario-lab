# Domain Synthesis Pipeline Design

Date: 2026-04-21

## Goal

Extend the forecasting harness so it can create a brand-new domain from zero on a standalone review branch, without modifying the shared simulation/workflow/retrieval algorithm.

The pipeline should:

- accept a structured domain blueprint
- generate the initial domain manifest
- generate a template-backed Python domain pack file
- register the new pack in the repo
- generate starter tests and optional replay seed files
- verify the repo still passes
- stop at a review branch and commit

## Constraints

- only use verified facts
- no automatic merge to `main`
- shared algorithm remains protected
- new domains should start in a `template-backed` form first
- generation must be deterministic from the blueprint input

## Approach

### 1. Structured Blueprint Input

The synthesis path will not try to infer a domain from raw prose inside the core.

Instead, it accepts a deterministic `DomainBlueprint` with fields such as:

- `slug`
- `class_name`
- `description`
- `focus_entity_rule`
- `canonical_stages`
- `suggested_related_actors`
- `follow_up_questions`
- `field_schema`
- `starter_sources`
- `evidence_categories`
- `evidence_category_terms`
- `semantic_alias_groups`
- `field_inference_rules`
- `action_templates`
- `transition_templates`

This lets the AI adapter draft the blueprint while the core stays deterministic.

### 2. Template-Backed Generated Pack

New domains should not require hand-written search logic for v1.

Add one shared runtime base for generated packs:

- `GeneratedTemplatePack`

The generated per-domain Python file will mostly declare constants and subclass that runtime.

The runtime owns:

- intake validation
- schema exposure
- state inference from rule tables
- action prior computation from rule tables
- deterministic transitions from template definitions
- basic metric scoring

This keeps the new-domain path reusable while avoiding edits to the simulation engine.

### 3. Generated Repo Artifacts

For a new domain `foo-bar`, synthesis writes:

- `packages/core/src/forecasting_harness/domain/foo_bar.py`
- `knowledge/domains/foo-bar.json`
- `knowledge/replays/foo-bar.json`
- `packages/core/tests/test_foo_bar_pack.py`
- `packages/core/src/forecasting_harness/domain/registry.py`

The replay file may start empty if the blueprint does not include seed replay cases.

### 4. Promotion Model

Synthesis creates a review branch:

- `codex/domain-synthesis-<slug>-<YYYYMMDD>`

It commits only the generated domain artifacts and supporting docs.

It does not merge into `main`.

### 5. Verification

Required verification:

- generated-pack test
- full `packages/core` suite
- `list-domain-packs` includes the new slug
- direct import of the generated pack works

## Non-Goals

- automatic blueprint drafting from raw chat inside the deterministic core
- direct editing of shared MCTS code
- auto-merge to `main`
- guaranteed real-world quality for a newly synthesized domain

## Expected Outcome

After this feature lands, the harness can create a new reviewable domain from a structured blueprint without bespoke manual scaffolding, and future users can expand the engine by adding new domains on isolated branches.
