# Local Semantic Retrieval Design

**Date:** 2026-04-20

## Goal

Add a local-only semantic retrieval layer to the forecasting harness so evidence drafting can combine lexical match, semantic similarity, metadata filters, and freshness without any external API.

## Constraints

Verified current state:

- The corpus is stored locally in SQLite with an FTS5 `chunks` table.
- Ingestion already normalizes local files into chunk rows.
- Search currently uses lexical FTS plus metadata filters and freshness weighting.
- The product direction is local-first and repo-owned.

So the new retrieval layer must:

- stay fully local
- work inside the existing SQLite corpus flow
- avoid external embedding APIs
- keep the current lexical path working

## Approaches Considered

### 1. External embedding API

Rejected because it violates the local-only requirement.

### 2. Local neural embeddings

Use a local transformer or sentence embedding model.

Pros:
- better semantic quality

Cons:
- heavier dependencies
- large model downloads
- more fragile setup for a small local-first prototype

### 3. Local semantic hashing vectors

Build deterministic local vectors from token features, phrase expansion, and character n-grams, then store them in the local corpus and use cosine similarity for retrieval.

Pros:
- fully local
- no model downloads
- easy to store and version in the existing DB
- good enough to add meaning-aware retrieval beyond exact keyword match

Cons:
- weaker than modern neural embeddings
- must be described honestly as a baseline semantic layer

## Recommendation

Approach `3`.

This milestone will implement:

- deterministic local vector encoding in repo code
- a semantic index stored in the local corpus DB
- hybrid retrieval in `SearchEngine`
- tests proving semantic-only hits can be retrieved even when FTS alone would miss them

## Design

### Local encoder

Create a new retrieval module that:

- lowercases and tokenizes text
- performs light phrase expansion from a built-in alias table
- builds hashed feature vectors from:
  - normalized tokens
  - token bigrams
  - character trigrams
- normalizes vectors for cosine similarity

This is not a neural model. It is a deterministic semantic-hashing baseline.

### Corpus storage

Extend the corpus DB with a new `chunk_vectors` table:

- `source_id`
- `chunk_id`
- `embedding_version`
- `vector_json`
- `token_count`

When a document is registered, chunk vectors are generated and stored alongside the FTS rows.

### Search behavior

`SearchEngine.search()` should become hybrid:

1. lexical hits from the existing FTS path
2. semantic hits from the vector table
3. metadata filtering
4. freshness/domain weighting
5. rank fusion into a single sorted result list

The simplest acceptable fusion for this milestone is weighted score fusion over:

- lexical score
- semantic score
- freshness multiplier
- domain freshness weight

### Output compatibility

The returned hit objects should remain backward-compatible, but may include:

- `lexical_score`
- `semantic_score`
- `score`

Existing workflow evidence drafting should continue to work unchanged.

## Non-goals

- no external API
- no transformer model dependency
- no ANN index
- no semantic reranking across reports or belief states
- no automatic rule extraction

## Expected Outcome

After this milestone:

- local corpus ingestion also builds local semantic vectors
- hybrid retrieval works through the existing search API
- evidence drafting can benefit from local semantic matching
- the repo has a credible local-only path toward richer semantic retrieval later
