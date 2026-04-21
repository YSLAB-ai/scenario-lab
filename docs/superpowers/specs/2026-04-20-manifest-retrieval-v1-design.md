# Manifest Retrieval V1 Design

Date: 2026-04-20

## Goal

Make the repo-owned domain manifests influence retrieval directly instead of serving only as documentation.

This milestone is intentionally narrow:

- load machine-usable domain manifests from `knowledge/domains/`
- let manifests contribute domain-specific semantic alias groups during search
- let manifests bias evidence packets toward coverage across evidence categories

## Design

### Manifest Loader

Add a small typed loader in `forecasting_harness.knowledge.manifests` that reads `knowledge/domains/<slug>.json` and returns a `DomainManifest`.

The loader owns two new machine-usable fields:

- `semantic_alias_groups`
- `evidence_category_terms`

### Semantic Retrieval

The existing local semantic hashing encoder stays local-only and deterministic.

Search gains optional manifest alias groups:

- if no alias groups are provided, use the persisted default vectors
- if alias groups are provided, compute the query vector and candidate chunk vectors with those groups during semantic search

This keeps the stored index format stable while allowing domain-specific semantic expansion at search time.

### Evidence Packet Coverage

Evidence drafting keeps the current source balancing, then adds category coverage:

- classify hits against manifest evidence categories using manifest category terms
- preferentially include the best hit for each category, in manifest order
- fill remaining slots by the existing score-based ranking

Packet reasons become category-aware when classification succeeds, for example:

- `Candidate passage for approved evidence packet: force posture`

## Scope Boundaries

This milestone does not add:

- neural embeddings
- automatic corpus ingestion from manifests
- open-web retrieval
- domain-specific query planners
- knowledge extraction or rule compilation

## Verification

Verification should cover:

- manifest loading
- manifest-driven semantic-only retrieval
- manifest-driven evidence packet category coverage
- full `packages/core` test suite
