# Local Neural Embeddings V1

Date: 2026-04-22

## Scope

- Added an optional local neural embedding backend for corpus search.
- Kept the deterministic hashed semantic encoder as the stable fallback.
- Added corpus-level backend persistence plus a rebuild command so existing corpora can be upgraded in place.

## Files Changed

- `packages/core/pyproject.toml`
- `packages/core/src/forecasting_harness/cli.py`
- `packages/core/src/forecasting_harness/retrieval/__init__.py`
- `packages/core/src/forecasting_harness/retrieval/registry.py`
- `packages/core/src/forecasting_harness/retrieval/semantic.py`
- `packages/core/tests/test_retrieval.py`
- `README.md`
- `docs/status/2026-04-20-project-status.md`

## Verified Results

- Full suite:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `273 passed in 5.28s`
- Retrieval-focused coverage:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core/tests/test_retrieval.py -q`
  - Result: `21 passed in 0.18s`
- `rebuild-corpus-embeddings` smoke:
  - command: `forecast-harness rebuild-corpus-embeddings --corpus-db /tmp/local-neural-embeddings-v1.db`
  - result:
    - `requested_backend = baseline`
    - `active_backend = baseline`
    - `chunk_count = 0`
    - `updated_chunks = 0`

## Behavior

- A corpus can now persist its preferred semantic backend in its own SQLite metadata table.
- Existing corpora remain readable even when the active embedding version changes:
  - if stored vectors are stale, semantic search recomputes row vectors on the fly with the current backend instead of silently dropping those rows.
- `forecast-harness rebuild-corpus-embeddings` can rebuild all stored chunk vectors and persist the chosen backend for future ingests.
- The optional neural backend is installed through:
  - `pip install -e 'packages/core[dev,semantic-local]'`

## Boundary

- This pass does not add OCR.
- This pass does not add spreadsheet or web-archive ingestion.
- The default behavior remains stable because the hashed local encoder is still the fallback when the neural extra is not installed.
