# Manifest Planning V1 Design

Date: 2026-04-20

## Goal

Make the repo-owned domain manifests drive two explicit backend planning steps:

- retrieval planning
- ingestion planning

This reduces adapter guesswork and makes `draft-evidence-packet` usable even when no explicit query string is supplied.

## Design

### Retrieval Plan

Add a typed `RetrievalPlan` that the core can draft from:

- the approved intake draft
- the selected domain pack
- the repo-owned domain manifest
- an optional user-supplied query string

The retrieval plan returns:

- `base_query`
- `query_variants`
- domain filters
- target evidence categories

Query variants are deterministic and manifest-aware. They expand the intake into a small ordered set of search strings instead of requiring the adapter to invent them.

### Ingestion Plan

Add a typed `IngestionPlan` that compares the manifest against the current filtered local corpus.

The ingestion plan returns:

- current corpus sources for the domain
- covered evidence categories
- missing evidence categories
- recommended source types
- starter sources
- ingestion priorities

This gives the adapter a deterministic way to tell the user what the corpus is still missing.

### Evidence Drafting

`draft-evidence-packet` should accept an optional `query_text`.

If no query is supplied, it should use the retrieval plan’s generated query variants.
If a query is supplied, it should still expand that query with manifest-aware variants rather than searching exactly one string.

The engine should merge search results across query variants by chunk identity, keeping the best score while preserving the existing manifest-aware evidence packet logic.

## Scope Boundaries

This milestone does not add:

- open-web search
- automatic file ingestion from manifests
- automatic per-domain query decomposition beyond deterministic variant generation
- neural retrieval planning

## Verification

Verification should cover:

- retrieval plan generation
- ingestion plan generation
- evidence drafting without explicit query text
- CLI commands for the new planning surfaces
- full `packages/core` test suite
