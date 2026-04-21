# Corpus Ingestion V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic local corpus ingestion pipeline for Markdown, CSV, JSON, and PDF so the existing retrieval and evidence-drafting workflow has real curated inputs.

**Architecture:** Extend the current retrieval layer instead of inventing a second corpus path. Add a small ingestion module that parses files into deterministic chunks, upgrade `CorpusRegistry` to persist document metadata plus chunk rows, then expose ingestion through CLI commands that operate on the same local SQLite corpus already used by retrieval and workflow evidence drafting.

**Tech Stack:** Python 3.12+, Typer, Pydantic, sqlite3/FTS5, stdlib `csv`/`json`, `pypdf`, pytest

---

## File Map

- Create: `packages/core/src/forecasting_harness/retrieval/ingest.py`
- Create: `packages/core/tests/test_ingestion.py`
- Modify: `packages/core/pyproject.toml`
- Modify: `packages/core/src/forecasting_harness/retrieval/__init__.py`
- Modify: `packages/core/src/forecasting_harness/retrieval/registry.py`
- Modify: `packages/core/src/forecasting_harness/retrieval/search.py`
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Modify: `packages/core/tests/test_retrieval.py`
- Modify: `packages/core/tests/test_cli_workflow.py`
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

### Task 1: Add Deterministic File Parsers and Chunking

**Files:**
- Modify: `packages/core/pyproject.toml`
- Create: `packages/core/src/forecasting_harness/retrieval/ingest.py`
- Modify: `packages/core/src/forecasting_harness/retrieval/__init__.py`
- Test: `packages/core/tests/test_ingestion.py`

- [ ] **Step 1: Write failing ingestion tests for file-type detection and chunking**

```python
from pathlib import Path

from forecasting_harness.retrieval.ingest import detect_source_type, ingest_file


def test_detect_source_type_maps_supported_suffixes() -> None:
    assert detect_source_type(Path("notes.md")) == "markdown"
    assert detect_source_type(Path("table.csv")) == "csv"
    assert detect_source_type(Path("facts.json")) == "json"
    assert detect_source_type(Path("report.pdf")) == "pdf"


def test_markdown_ingestion_uses_heading_locations(tmp_path: Path) -> None:
    path = tmp_path / "brief.md"
    path.write_text("# Overview\nAlpha\n\n## Constraints\nBeta\n", encoding="utf-8")

    document = ingest_file(path)

    assert document.source_type == "markdown"
    assert [chunk.location for chunk in document.chunks] == ["heading:Overview", "heading:Overview > Constraints"]
```

- [ ] **Step 2: Run the new ingestion tests to verify they fail**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_ingestion.py -q`
Expected: FAIL because `forecasting_harness.retrieval.ingest` does not exist yet.

- [ ] **Step 3: Add `pypdf` as a package dependency**

```toml
[project]
dependencies = [
  "pydantic>=2.7,<3",
  "typer>=0.12,<1",
  "pypdf>=4,<6",
]
```

- [ ] **Step 4: Reinstall the local dev environment after adding the dependency**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/pip" install -e 'packages/core[dev]'`
Expected: `pypdf` installs successfully into the shared local test environment.

- [ ] **Step 5: Implement the ingestion module with parser-specific chunkers**

```python
@dataclass(frozen=True)
class IngestedChunk:
    chunk_id: str
    location: str
    content: str


@dataclass(frozen=True)
class IngestedDocument:
    source_id: str
    title: str
    source_type: str
    path: str
    published_at: str | None
    tags: dict[str, str]
    chunks: list[IngestedChunk]
```

```python
def detect_source_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return "markdown"
    if suffix == ".csv":
        return "csv"
    if suffix == ".json":
        return "json"
    if suffix == ".pdf":
        return "pdf"
    raise ValueError(f"unsupported source type: {path.suffix or path.name}")
```

- [ ] **Step 6: Implement deterministic chunking rules**

```python
def _markdown_chunks(text: str) -> list[IngestedChunk]:
    ...
    return [
        IngestedChunk(chunk_id="1", location="heading:Overview", content="Alpha"),
        IngestedChunk(chunk_id="2", location="heading:Overview > Constraints", content="Beta"),
    ]
```

```python
def _csv_chunks(path: Path) -> list[IngestedChunk]:
    ...
    return [IngestedChunk(chunk_id="1", location="row:1", content="country=Japan, posture=heightened")]
```

```python
def _json_chunks(path: Path) -> list[IngestedChunk]:
    ...
    return [IngestedChunk(chunk_id="1", location="items[0]", content='{"country": "Japan"}')]
```

```python
def _pdf_chunks(path: Path) -> list[IngestedChunk]:
    reader = PdfReader(str(path))
    ...
    return [IngestedChunk(chunk_id="1", location="page:1", content="Extracted page text")]
```

- [ ] **Step 7: Export ingestion helpers from the retrieval package**

```python
from forecasting_harness.retrieval.ingest import IngestedChunk, IngestedDocument, detect_source_type, ingest_file

__all__ = [
    "CorpusRegistry",
    "RetrievalQuery",
    "SearchEngine",
    "IngestedChunk",
    "IngestedDocument",
    "detect_source_type",
    "ingest_file",
]
```

- [ ] **Step 8: Run focused ingestion tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_ingestion.py -q`
Expected: PASS

- [ ] **Step 9: Commit the parser/chunking slice**

```bash
git add packages/core/pyproject.toml \
        packages/core/src/forecasting_harness/retrieval/ingest.py \
        packages/core/src/forecasting_harness/retrieval/__init__.py \
        packages/core/tests/test_ingestion.py
git commit -m "feat: add corpus ingestion parsers"
```

### Task 2: Upgrade the Corpus Registry to Store Documents and Citation-Friendly Chunks

**Files:**
- Modify: `packages/core/src/forecasting_harness/retrieval/registry.py`
- Modify: `packages/core/src/forecasting_harness/retrieval/search.py`
- Test: `packages/core/tests/test_retrieval.py`

- [ ] **Step 1: Write failing registry tests for document metadata and chunk locations**

```python
def test_registry_persists_document_rows_and_chunk_rows(tmp_path: Path) -> None:
    registry = CorpusRegistry(tmp_path / "corpus.db")
    registry.register_document(
        source_id="src-1",
        title="Signals",
        source_type="markdown",
        published_at=None,
        tags={"domain": "interstate-crisis"},
        path="/tmp/signals.md",
        chunks=[{"chunk_id": "1", "location": "heading:Overview", "content": "Alpha"}],
    )

    docs = registry.list_documents()
    hits = registry.search_chunks("Alpha")

    assert docs[0]["chunk_count"] == 1
    assert hits[0]["location"] == "heading:Overview"
    assert hits[0]["chunk_id"] == "1"
```

- [ ] **Step 2: Run the targeted retrieval tests to verify they fail**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_retrieval.py -q`
Expected: FAIL because the current registry signature and schema do not support chunk metadata.

- [ ] **Step 3: Replace the single-row storage model with `documents` + `chunks`**

```python
connection.execute(
    """
    CREATE TABLE IF NOT EXISTS documents (
        source_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        source_type TEXT NOT NULL,
        path TEXT NOT NULL,
        published_at TEXT,
        tags TEXT NOT NULL,
        chunk_count INTEGER NOT NULL,
        ingested_at TEXT NOT NULL
    )
    """
)
connection.execute(
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS chunks
    USING fts5(source_id, chunk_id, title, published_at, source_type, tags, location, content)
    """
)
```

- [ ] **Step 4: Update `register_document` to persist one document row and many chunk rows**

```python
def register_document(..., path: str, chunks: list[dict[str, str]]) -> None:
    ...
    connection.execute("DELETE FROM documents WHERE source_id = ?", (source_id,))
    connection.execute("DELETE FROM chunks WHERE source_id = ?", (source_id,))
    connection.execute("INSERT INTO documents ...", (..., len(chunks), datetime.now(timezone.utc).isoformat()))
    connection.executemany("INSERT INTO chunks ...", chunk_rows)
```

- [ ] **Step 5: Add `list_documents()` and make `search_chunks()` return chunk metadata**

```python
def list_documents(self) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT source_id, title, source_type, path, published_at, tags, chunk_count, ingested_at FROM documents ORDER BY source_id"
    ).fetchall()
    ...
```

```python
query = (
    "SELECT source_id, chunk_id, title, published_at, source_type, tags, location, content "
    "FROM chunks WHERE chunks MATCH ?"
)
```

- [ ] **Step 6: Make search freshness neutral when `published_at` is missing**

```python
def freshness_multiplier(self, published_at: str | None) -> float:
    if not published_at:
        return 1.0
    ...
```

- [ ] **Step 7: Run focused retrieval tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_retrieval.py -q`
Expected: PASS

- [ ] **Step 8: Commit the registry schema slice**

```bash
git add packages/core/src/forecasting_harness/retrieval/registry.py \
        packages/core/src/forecasting_harness/retrieval/search.py \
        packages/core/tests/test_retrieval.py
git commit -m "feat: persist corpus documents and chunks"
```

### Task 3: Add CLI Ingestion Commands and End-to-End Coverage

**Files:**
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Modify: `packages/core/tests/test_cli_workflow.py`

- [ ] **Step 1: Write failing CLI tests for file and directory ingestion**

```python
def test_ingest_file_command_registers_a_searchable_source(tmp_path: Path) -> None:
    source = tmp_path / "signals.md"
    source.write_text("# Overview\nJapan issues a warning.\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        ["ingest-file", "--corpus-db", str(tmp_path / "corpus.db"), "--path", str(source)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["source_type"] == "markdown"
    assert payload["chunk_count"] == 1
```

```python
def test_ingest_directory_command_reports_ingested_and_skipped_files(tmp_path: Path) -> None:
    ...
    assert payload["ingested"] == 2
    assert payload["skipped"] == 1
```

- [ ] **Step 2: Run the CLI ingestion tests to verify they fail**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_cli_workflow.py -q`
Expected: FAIL because the ingestion commands do not exist yet.

- [ ] **Step 3: Add `ingest-file`, `ingest-directory`, and `list-corpus-sources` to the CLI**

```python
@app.command("ingest-file")
def ingest_file_command(
    corpus_db: Path = typer.Option(...),
    path: Path = typer.Option(...),
    source_id: str | None = typer.Option(None),
    title: str | None = typer.Option(None),
    published_at: str | None = typer.Option(None),
    tag: list[str] = typer.Option(None),
) -> None:
    ...
    print(json.dumps({"source_id": ..., "source_type": ..., "chunk_count": ...}))
```

```python
@app.command("ingest-directory")
def ingest_directory_command(...):
    ...
    print(json.dumps({"ingested": ingested, "failed": failed, "skipped": skipped}))
```

```python
@app.command("list-corpus-sources")
def list_corpus_sources(corpus_db: Path = typer.Option(...)) -> None:
    print(json.dumps(CorpusRegistry(corpus_db).list_documents()))
```

- [ ] **Step 4: Parse repeated `--tag key=value` inputs deterministically**

```python
def _parse_tags(values: list[str]) -> dict[str, str]:
    tags: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise typer.BadParameter("tags must be key=value")
        key, raw_value = value.split("=", 1)
        tags[key] = raw_value
    return tags
```

- [ ] **Step 5: Wire CLI ingestion through `ingest_file()` and `CorpusRegistry.register_document()`**

```python
document = ingest_file(path, source_id=source_id, title=title, published_at=published_at, tags=tags)
registry.register_document(
    source_id=document.source_id,
    title=document.title,
    source_type=document.source_type,
    path=document.path,
    published_at=document.published_at,
    tags=document.tags,
    chunks=[...],
)
```

- [ ] **Step 6: Run focused CLI workflow tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_cli_workflow.py -q`
Expected: PASS

- [ ] **Step 7: Commit the CLI ingestion slice**

```bash
git add packages/core/src/forecasting_harness/cli.py \
        packages/core/tests/test_cli_workflow.py
git commit -m "feat: add corpus ingestion commands"
```

### Task 4: Refresh Docs and Run Full Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

- [ ] **Step 1: Update README to describe corpus ingestion**

```md
- `forecast-harness ingest-file`
- `forecast-harness ingest-directory`
- `forecast-harness list-corpus-sources`
- local corpus ingestion now supports Markdown, CSV, JSON, and PDF
```

- [ ] **Step 2: Update the status note with verified ingestion progress and remaining gaps**

```md
- the corpus now supports document metadata plus citation-friendly chunk rows
- the CLI can ingest curated local files into a searchable corpus
- remaining gaps: no OCR, no spreadsheet ingestion, no conversational adapter
```

- [ ] **Step 3: Run the full test suite**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core -q`
Expected: PASS

- [ ] **Step 4: Smoke-test the ingestion flow**

Run:

```bash
tmpdir="$(mktemp -d)"
cd "$tmpdir"
cat > signals.md <<'EOF'
# Overview
Japan and China exchange warnings in the Taiwan Strait.
EOF
PYTHONPATH="/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/corpus-ingestion-v1/packages/core/src" \
"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m forecasting_harness.cli ingest-file \
  --corpus-db corpus.db \
  --path signals.md \
  --tag domain=interstate-crisis
PYTHONPATH="/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/corpus-ingestion-v1/packages/core/src" \
"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m forecasting_harness.cli list-corpus-sources \
  --corpus-db corpus.db
```

Expected:

- `ingest-file` returns a JSON summary with `chunk_count >= 1`
- `list-corpus-sources` returns the stored document metadata

- [ ] **Step 5: Commit docs and verification updates**

```bash
git add README.md docs/status/2026-04-20-project-status.md
git commit -m "docs: refresh corpus ingestion status"
```

## Self-Review

- Spec coverage: the plan maps directly to the spec sections for parser surface, storage model, retrieval compatibility, CLI surface, and testing.
- Placeholder scan: no `TBD`, `TODO`, or deferred implementation placeholders remain in task steps.
- Type consistency: the plan consistently uses `IngestedDocument`, `IngestedChunk`, `detect_source_type`, `ingest_file`, `documents`, `chunks`, `list_documents`, and `list-corpus-sources` across all tasks.
