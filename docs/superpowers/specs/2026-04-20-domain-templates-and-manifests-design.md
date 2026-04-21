# Domain Templates And Manifests Design

**Date:** 2026-04-20

## Goal

Add repo-owned domain templates for the forecasting harness so the workflow can be reused across several high-value domains without inventing a full knowledge compiler or downloading a large corpus into the repository.

## Context

Verified current state:

- The reusable `DomainPack` interface already exists in `packages/core/src/forecasting_harness/domain/base.py`.
- The registry currently exposes only `generic-event` and `interstate-crisis`.
- The retrieval layer already supports local corpus ingestion and filtered search.
- The repo already has deterministic workflow, evidence, and MCTS plumbing.

So the missing layer is not generic infrastructure. It is a reusable set of domain pack templates plus a repo-owned way to express what each domain should ingest later.

## Approaches Considered

### 1. Add more domain packs only

Create new `DomainPack` implementations and register them.

Pros:
- Smallest code change
- Immediately usable in CLI and workflow

Cons:
- No knowledge-base structure for each domain
- Pushes source selection back into ad hoc user behavior

### 2. Add domain packs plus source manifests

Create new `DomainPack` implementations and add repo-owned manifest files describing source categories, evidence types, suggested canonical references, and ingestion priorities for each domain.

Pros:
- Keeps knowledge ownership local and structured
- Gives each domain a reusable intake/retrieval/scoring template
- Provides a stable base for later semantic retrieval and knowledge compilation

Cons:
- Slightly more work than pack-only scaffolding

### 3. Build a large downloaded corpus now

Try to ingest books, papers, and datasets immediately as part of the same milestone.

Pros:
- Makes the repo feel more complete in the short term

Cons:
- Too much scope
- Copyright/licensing risk
- Pollutes the repo with heavy data before the manifest structure is stable

## Recommendation

Approach `2`.

This milestone should build:

- reusable domain pack templates
- repo-owned source manifests per domain
- light documentation for how to populate those manifests with licensed or user-supplied materials later

It should not build:

- automatic rule extraction
- a giant downloaded corpus
- NotebookLM integration as a source of truth

## Domains

This milestone will add templates for the domains that fit the current framework best:

1. `company-action`
2. `election-shock`
3. `market-shock`
4. `supply-chain-disruption`
5. `regulatory-enforcement`

The existing `interstate-crisis` pack remains the reference geopolitical template.

## Pack Requirements

Each new domain pack should provide:

- a slug
- canonical stages
- validation for the generic intake schema
- related-entity suggestions when obvious
- retrieval filters
- a small pack-specific schema via `extend_schema()`
- deterministic action proposals
- deterministic state transitions
- a scoring function over the existing metric vector shape

The packs are templates, not validated forecasting models. They should be:

- structurally coherent
- deterministic
- minimal but reusable
- explicit about their intended evidence categories

## Source Manifest Requirements

Each domain gets a repo-owned manifest file under a new domain knowledge area. Each manifest should include:

- domain slug
- description
- actor categories
- evidence categories
- key state fields
- canonical stages
- recommended source types
- starter source suggestions
- ingestion priorities
- freshness notes

These manifests should describe what the user should ingest later. They should not bundle copyrighted source content into the repo.

## File Layout

New or changed areas:

- `packages/core/src/forecasting_harness/domain/`
  - new domain pack modules
  - updated registry
- `packages/core/tests/`
  - registry coverage
  - pack behavior coverage
  - CLI coverage for `list-domain-packs`
- `knowledge/domains/`
  - one manifest per domain
- `README.md`
  - new domain-template and knowledge-manifest notes
- `docs/status/2026-04-20-project-status.md`
  - verified updated project status

## Non-Goals

- No semantic vector engine changes in this milestone
- No automatic corpus download
- No OCR or expanded ingestion formats
- No domain calibration or historical replay
- No changes to the core workflow artifact model

## Expected Outcome

After this milestone:

- the harness can list and instantiate multiple reusable domain templates
- each domain has a repo-owned knowledge manifest describing how to populate the local corpus
- the project has a clearer path to local semantic retrieval without outsourcing knowledge ownership to an external tool
