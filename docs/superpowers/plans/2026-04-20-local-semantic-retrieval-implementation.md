# Local Semantic Retrieval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add fully local hybrid semantic retrieval to the corpus and search layers without relying on external APIs.

**Architecture:** Introduce a deterministic local semantic encoder, persist vectors in the corpus database at ingestion time, and fuse lexical and semantic hits inside the existing `SearchEngine`. Keep the workflow and evidence packet interfaces unchanged.

**Tech Stack:** Python, SQLite, existing corpus registry/search modules, pure-Python hashing/vector math

---

### Task 1: Add Red Tests For Semantic Retrieval

**Files:**
- Modify: `packages/core/tests/test_retrieval.py`

- [ ] **Step 1: Write failing semantic retrieval tests**

Add tests for:

- semantic-only hit through a synonym or alias path
- vector rows being stored with document registration
- hybrid search preserving existing lexical behavior

- [ ] **Step 2: Run tests to verify failure**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_retrieval.py -q`

Expected: failures because semantic tables and semantic scoring do not exist yet.

- [ ] **Step 3: Commit**

```bash
git add packages/core/tests/test_retrieval.py
git commit -m "test: define local semantic retrieval behavior"
```

### Task 2: Implement Local Semantic Encoder And Storage

**Files:**
- Create: `packages/core/src/forecasting_harness/retrieval/semantic.py`
- Modify: `packages/core/src/forecasting_harness/retrieval/registry.py`
- Modify: `packages/core/src/forecasting_harness/retrieval/__init__.py`

- [ ] **Step 1: Implement deterministic local vector encoder**

Add:

- token normalization
- light phrase expansion
- hashed feature vector generation
- cosine-similarity helpers
- embedding version constant

- [ ] **Step 2: Extend corpus schema**

Add `chunk_vectors` table creation and vector persistence during `register_document()`.

- [ ] **Step 3: Add semantic retrieval method to the registry**

Implement a method that:

- encodes the query
- loads candidate vectors
- computes similarity locally
- returns chunk rows with `semantic_score`

- [ ] **Step 4: Run focused retrieval tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_retrieval.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/forecasting_harness/retrieval/semantic.py \
        packages/core/src/forecasting_harness/retrieval/registry.py \
        packages/core/src/forecasting_harness/retrieval/__init__.py
git commit -m "feat: add local semantic vector index"
```

### Task 3: Implement Hybrid Search Fusion

**Files:**
- Modify: `packages/core/src/forecasting_harness/retrieval/search.py`
- Modify: `packages/core/tests/test_retrieval.py`

- [ ] **Step 1: Fuse lexical and semantic hit streams**

Update `SearchEngine.search()` to:

- gather lexical hits
- gather semantic hits
- merge duplicate chunk keys
- apply filters and freshness weighting
- emit a final fused `score`

- [ ] **Step 2: Preserve backward-compatible output**

Ensure existing code still sees:

- source metadata
- `score`
- original chunk information

while also adding semantic metadata where available.

- [ ] **Step 3: Run focused tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_retrieval.py packages/core/tests/test_cli_workflow.py -q`

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add packages/core/src/forecasting_harness/retrieval/search.py packages/core/tests/test_retrieval.py
git commit -m "feat: add hybrid lexical semantic search"
```

### Task 4: Update Docs And Run Full Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

- [ ] **Step 1: Update README**

Describe the local-only semantic retrieval layer honestly as a deterministic baseline.

- [ ] **Step 2: Update status note**

Record the semantic index and hybrid retrieval milestone.

- [ ] **Step 3: Run full suite**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core -q`

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/status/2026-04-20-project-status.md
git commit -m "docs: record local semantic retrieval milestone"
```
