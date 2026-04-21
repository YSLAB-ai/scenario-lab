# Ingestion Orchestration V1 Design

Date: 2026-04-20

## Goal

Turn manifest-driven ingestion planning into a concrete local orchestration path.

This milestone adds three backend capabilities:

- concrete ingest tasks for missing evidence categories
- deterministic local file recommendations with mapped source roles
- prioritized batch ingestion using those recommendations

## Design

### Ingest Tasks

`IngestionPlan` should no longer stop at listing missing categories.

For each missing evidence category, the core should produce an `IngestionTask` that includes:

- `evidence_category`
- `priority_rank`
- `source_role`
- the selected starter source
- recommended source types

The source role is inferred from manifest starter sources and category-term overlap.

### File Recommendations

Add a deterministic recommendation pass over a local directory of candidate files.

For each supported file:

1. ingest it in memory only
2. classify it against missing evidence categories
3. map it to a domain/source role
4. attach recommended tags such as:
   - `domain`
   - `source_role`
   - top `evidence_category`

Only files that match at least one target evidence category should be recommended.

### Batch Ingestion

Add a batch-ingest operation that:

- uses the recommendation pass
- takes the top `N` recommended files
- registers them into the local corpus
- writes the recommended tags into the stored document metadata

Unsupported or non-matching files should be counted as skipped.

## Scope Boundaries

This milestone does not add:

- open-web acquisition
- OCR
- automatic scheduling of future ingestion work
- automatic conflict resolution between duplicate sources

## Verification

Verification should cover:

- ingest task generation inside `draft-ingestion-plan`
- source-role mapping for local files
- batch ingestion tagging stored documents with domain/source-role metadata
- CLI coverage for recommendation and batch-ingest commands
- full `packages/core` test suite
