import json
import zipfile
from pathlib import Path
import sqlite3

import pytest

from forecasting_harness.query_api import get_evidence_for_assumption, summarize_top_branches
from typer.testing import CliRunner

from forecasting_harness.cli import app
from forecasting_harness.retrieval import CorpusRegistry, RetrievalQuery, SearchEngine
from forecasting_harness.retrieval.ingest import ingest_file
from forecasting_harness.retrieval.semantic import deserialize_vector


def _register_markdown_source(
    registry: CorpusRegistry,
    *,
    source_id: str = "src-1",
    title: str = "Recent logistics report",
    published_at: str | None = "2026-04-18",
    tags: dict[str, str] | None = None,
    content: str = "Fuel stockpiles are strained.",
    location: str = "heading:Report",
) -> None:
    registry.register_document(
        source_id=source_id,
        title=title,
        source_type="markdown",
        path=f"/tmp/{source_id}.md",
        published_at=published_at,
        tags=tags or {"domain": "conflict", "actor": "state-a"},
        chunks=[{"chunk_id": "1", "location": location, "content": content}],
    )


def _write_minimal_xlsx(path: Path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
""",
        )
        archive.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="/xl/workbook.xml"/>
</Relationships>
""",
        )
        archive.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Signals" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
""",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="/xl/worksheets/sheet1.xml"/>
</Relationships>
""",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" t="inlineStr"><is><t>Overview</t></is></c>
      <c r="B1" t="inlineStr"><is><t>Inventory shortage</t></is></c>
    </row>
  </sheetData>
</worksheet>
""",
        )


def test_registry_registers_documents_and_returns_chunk_hits(tmp_path: Path):
    registry = CorpusRegistry(tmp_path / "corpus.db")
    _register_markdown_source(registry)

    hits = SearchEngine(registry).search(
        RetrievalQuery(text="fuel stockpiles", filters={"domain": "conflict"})
    )

    assert hits[0]["source_id"] == "src-1"
    assert hits[0]["chunk_id"] == "1"
    assert hits[0]["location"] == "heading:Report"


def test_query_api_summarizes_top_branches_without_loading_full_tree():
    assert summarize_top_branches(
        [
            {"branch_id": "b1", "score": 0.7, "label": "de-escalation"},
            {"branch_id": "b2", "score": 0.3, "label": "limited strike"},
        ],
        limit=1,
    ) == [
        {
            "branch_id": "b1",
            "label": "de-escalation",
            "score": 0.7,
            "confidence_signal": 0.0,
            "confidence_bucket": "",
            "calibrated_confidence": 0.0,
            "calibration_case_count": 0,
        }
    ]


def test_query_api_can_return_detailed_top_branch_data():
    assert summarize_top_branches(
        [
            {
                "branch_id": "b1",
                "score": 0.7,
                "label": "de-escalation",
                "terminal_phase": "settlement",
                "aggregate_score_breakdown": {"system": 0.4},
            }
        ],
        detailed=True,
    ) == [
        {
            "branch_id": "b1",
            "label": "de-escalation",
            "score": 0.7,
            "aggregate_score_breakdown": {"system": 0.4},
            "terminal_phase": "settlement",
            "confidence_signal": 0.0,
            "confidence_bucket": "",
            "calibrated_confidence": 0.0,
            "calibration_case_count": 0,
        }
    ]


def test_query_api_keeps_explored_branches_ahead_of_unexplored_higher_score_branches():
    assert summarize_top_branches(
        [
            {
                "branch_id": "visited",
                "label": "Visited branch",
                "score": 0.5,
                "visits": 10,
                "prior": 0.2,
            },
            {
                "branch_id": "unvisited",
                "label": "Unvisited branch",
                "score": 0.9,
                "visits": 0,
                "prior": 0.9,
            },
        ],
        limit=2,
    ) == [
        {
            "branch_id": "visited",
            "label": "Visited branch",
            "score": 0.5,
            "confidence_signal": 0.0,
            "confidence_bucket": "",
            "calibrated_confidence": 0.0,
            "calibration_case_count": 0,
        },
        {
            "branch_id": "unvisited",
            "label": "Unvisited branch",
            "score": 0.9,
            "confidence_signal": 0.0,
            "confidence_bucket": "",
            "calibrated_confidence": 0.0,
            "calibration_case_count": 0,
        },
    ]


def test_registry_search_chunks_handles_punctuation_queries(tmp_path: Path):
    registry = CorpusRegistry(tmp_path / "corpus.db")
    _register_markdown_source(registry)

    assert registry.search_chunks("state-a") == []
    assert registry.search_chunks("(") == []
    assert registry.search_chunks("-") == []


def test_search_engine_finds_ingested_spreadsheet_and_web_archive_chunks(tmp_path: Path) -> None:
    registry = CorpusRegistry(tmp_path / "corpus.db")

    xlsx_path = tmp_path / "signals.xlsx"
    _write_minimal_xlsx(xlsx_path)
    spreadsheet_document = ingest_file(xlsx_path)
    registry.register_document(
        source_id=spreadsheet_document.source_id,
        title=spreadsheet_document.title,
        source_type=spreadsheet_document.source_type,
        path=spreadsheet_document.path,
        published_at=spreadsheet_document.published_at,
        tags={"domain": "supply-chain-disruption"},
        chunks=[chunk.__dict__ for chunk in spreadsheet_document.chunks],
    )

    html_path = tmp_path / "saved.webarchive"
    html_path.write_bytes(
        b"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\">
<dict>
  <key>WebMainResource</key>
  <dict>
    <key>WebResourceData</key>
    <data>PCFkb2N0eXBlIGh0bWw+CjxodG1sPgo8aGVhZD4KICA8dGl0bGU+QXJjaGl2ZWQgUGFnZTwvdGl0bGU+CjwvaGVhZD4KPGJvZHk+CiAgPGgxPlNpZ25hbHM8L2gxPgogIDxwPkNoaWVmIGV4ZWN1dGl2ZSByZXNwb25zZSBzdGFiaWxpemVkIHF1aWNrbHkuPC9wPgo8L2JvZHk+CjwvaHRtbD4K</data>
    <key>WebResourceMIMEType</key>
    <string>text/html</string>
    <key>WebResourceTextEncodingName</key>
    <string>utf-8</string>
    <key>WebResourceURL</key>
    <string>https://example.com/archived-page</string>
  </dict>
</dict>
</plist>
"""
    )
    archive_document = ingest_file(html_path)
    registry.register_document(
        source_id=archive_document.source_id,
        title=archive_document.title,
        source_type=archive_document.source_type,
        path=archive_document.path,
        published_at=archive_document.published_at,
        tags={"domain": "company-action"},
        chunks=[chunk.__dict__ for chunk in archive_document.chunks],
    )

    spreadsheet_hits = SearchEngine(registry).search(
        RetrievalQuery(text="Inventory shortage", filters={"domain": "supply-chain-disruption"})
    )
    semantic_hits = SearchEngine(registry).search(
        RetrievalQuery(text="ceo response", filters={"domain": "company-action"})
    )

    assert spreadsheet_hits[0]["source_type"] == "spreadsheet"
    assert spreadsheet_hits[0]["location"] == "sheet:Signals!A1:B1"
    assert semantic_hits[0]["source_type"] == "web-archive"
    assert semantic_hits[0]["semantic_score"] > 0


def test_registry_search_chunks_raises_for_malformed_schema(tmp_path: Path):
    registry = CorpusRegistry(tmp_path / "corpus.db")
    with registry._connect() as connection:
        connection.execute("DROP TABLE chunks")
        connection.execute("CREATE TABLE chunks (source_id TEXT)")

    with pytest.raises(sqlite3.OperationalError):
        registry.search_chunks("fuel")


def test_registry_re_registering_source_id_replaces_existing_rows(tmp_path: Path):
    registry = CorpusRegistry(tmp_path / "corpus.db")
    _register_markdown_source(registry)
    registry.register_document(
        source_id="src-1",
        title="Updated logistics report",
        source_type="markdown",
        path="/tmp/src-1.md",
        published_at="2026-04-19",
        tags={"domain": "conflict", "actor": "state-a"},
        chunks=[
            {
                "chunk_id": "1",
                "location": "heading:Report",
                "content": "Fuel stockpiles are still strained.",
            }
        ],
    )

    hits = SearchEngine(registry).search(
        RetrievalQuery(text="fuel stockpiles", filters={"domain": "conflict"})
    )

    assert [hit["source_id"] for hit in hits] == ["src-1"]
    assert hits[0]["title"] == "Updated logistics report"


def test_registry_disambiguates_colliding_source_ids_for_distinct_paths(tmp_path: Path) -> None:
    registry = CorpusRegistry(tmp_path / "corpus.db")

    first_id = registry.register_document(
        source_id="doc-1",
        title="First note",
        source_type="markdown",
        path="/tmp/a/doc-1.md",
        published_at="2026-04-19",
        tags={"domain": "conflict"},
        chunks=[{"chunk_id": "1", "location": "heading:A", "content": "alpha"}],
    )
    second_id = registry.register_document(
        source_id="doc-1",
        title="Second note",
        source_type="markdown",
        path="/tmp/b/doc-1.md",
        published_at="2026-04-20",
        tags={"domain": "conflict"},
        chunks=[{"chunk_id": "1", "location": "heading:B", "content": "beta"}],
    )

    docs = registry.list_documents()

    assert first_id == "doc-1"
    assert second_id.startswith("doc-1-")
    assert second_id != first_id
    assert {doc["source_id"] for doc in docs} == {first_id, second_id}


def test_freshness_multiplier_clamps_future_dates_and_rejects_malformed_dates(tmp_path: Path):
    registry = CorpusRegistry(tmp_path / "corpus.db")
    engine = SearchEngine(registry)

    assert engine.freshness_multiplier("2100-01-01") == 1.0

    with pytest.raises(ValueError):
        engine.freshness_multiplier("not-a-date")


def test_registry_rejects_malformed_published_at_during_registration(tmp_path: Path):
    registry = CorpusRegistry(tmp_path / "corpus.db")

    with pytest.raises(ValueError, match="invalid published_at date"):
        registry.register_document(
            source_id="src-1",
            title="Recent logistics report",
            source_type="markdown",
            path="/tmp/src-1.md",
            published_at="not-a-date",
            tags={"domain": "conflict", "actor": "state-a"},
            chunks=[{"chunk_id": "1", "location": "heading:Report", "content": "Fuel stockpiles are strained."}],
        )

    assert SearchEngine(registry).search(RetrievalQuery(text="fuel")) == []


def test_registry_persists_document_rows_and_chunk_rows(tmp_path: Path) -> None:
    registry = CorpusRegistry(tmp_path / "corpus.db")
    registry.register_document(
        source_id="src-1",
        title="Signals",
        source_type="markdown",
        path="/tmp/signals.md",
        published_at=None,
        tags={"domain": "interstate-crisis"},
        chunks=[{"chunk_id": "1", "location": "heading:Overview", "content": "Alpha"}],
    )

    docs = registry.list_documents()
    hits = registry.search_chunks("Alpha")

    assert docs[0]["chunk_count"] == 1
    assert docs[0]["published_at"] is None
    assert hits[0]["location"] == "heading:Overview"
    assert hits[0]["chunk_id"] == "1"


def test_registry_persists_chunk_vector_rows(tmp_path: Path) -> None:
    registry = CorpusRegistry(tmp_path / "corpus.db")
    registry.register_document(
        source_id="src-1",
        title="Leadership response",
        source_type="markdown",
        path="/tmp/leadership.md",
        published_at="2026-04-20",
        tags={"domain": "company-action"},
        chunks=[
            {"chunk_id": "1", "location": "heading:Overview", "content": "The chief executive stabilized messaging quickly."}
        ],
    )

    with registry._connect() as connection:
        rows = connection.execute(
            "SELECT source_id, chunk_id, embedding_version, token_count, vector_json FROM chunk_vectors"
        ).fetchall()

    assert len(rows) == 1
    assert rows[0]["source_id"] == "src-1"
    assert rows[0]["chunk_id"] == "1"
    assert rows[0]["embedding_version"]
    assert rows[0]["token_count"] > 0
    assert rows[0]["vector_json"]


def test_search_engine_returns_semantic_hit_without_exact_lexical_match(tmp_path: Path) -> None:
    registry = CorpusRegistry(tmp_path / "corpus.db")
    registry.register_document(
        source_id="src-1",
        title="Leadership response",
        source_type="markdown",
        path="/tmp/leadership.md",
        published_at="2026-04-20",
        tags={"domain": "company-action"},
        chunks=[
            {"chunk_id": "1", "location": "heading:Overview", "content": "The chief executive stabilized messaging quickly."}
        ],
    )

    hits = SearchEngine(registry).search(
        RetrievalQuery(text="ceo response", filters={"domain": "company-action"})
    )

    assert hits
    assert hits[0]["source_id"] == "src-1"
    assert hits[0]["semantic_score"] > 0
    assert hits[0]["lexical_score"] == 0.0


def test_search_engine_accepts_manifest_alias_groups_for_semantic_hits(tmp_path: Path) -> None:
    registry = CorpusRegistry(tmp_path / "corpus.db")
    registry.register_document(
        source_id="src-1",
        title="Strait posture",
        source_type="markdown",
        path="/tmp/posture.md",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis"},
        chunks=[
            {"chunk_id": "1", "location": "heading:Overview", "content": "Force posture hardens near the strait."}
        ],
    )

    hits = SearchEngine(registry).search(
        RetrievalQuery(text="military buildup", filters={"domain": "interstate-crisis"}),
        alias_groups=[("military buildup", "force posture")],
    )

    assert hits
    assert hits[0]["source_id"] == "src-1"
    assert hits[0]["semantic_score"] > 0
    assert hits[0]["lexical_score"] == 0.0


def test_search_engine_recomputes_semantic_vectors_when_stored_version_is_stale(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = CorpusRegistry(tmp_path / "corpus.db")
    registry.register_document(
        source_id="src-1",
        title="Leadership response",
        source_type="markdown",
        path="/tmp/leadership.md",
        published_at="2026-04-20",
        tags={"domain": "company-action"},
        chunks=[
            {"chunk_id": "1", "location": "heading:Overview", "content": "The chief executive stabilized messaging quickly."}
        ],
    )

    def fake_encode_text(text: str, *, alias_groups=None, requested_backend=None, model_name=None):
        normalized = text.lower()
        if "chief executive" in normalized or "ceo" in normalized:
            return ([1.0, 0.0], 2)
        return ([0.0, 1.0], 2)

    monkeypatch.setattr(
        "forecasting_harness.retrieval.registry.current_embedding_version",
        lambda **kwargs: "local-neural-v1",
    )
    monkeypatch.setattr("forecasting_harness.retrieval.registry.encode_text", fake_encode_text)

    hits = SearchEngine(registry).search(
        RetrievalQuery(text="ceo response", filters={"domain": "company-action"})
    )

    assert hits
    assert hits[0]["source_id"] == "src-1"
    assert hits[0]["semantic_score"] > 0.0


def test_registry_can_rebuild_chunk_vectors_for_current_backend(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = CorpusRegistry(tmp_path / "corpus.db")
    registry.register_document(
        source_id="src-1",
        title="Leadership response",
        source_type="markdown",
        path="/tmp/leadership.md",
        published_at="2026-04-20",
        tags={"domain": "company-action"},
        chunks=[
            {"chunk_id": "1", "location": "heading:Overview", "content": "The chief executive stabilized messaging quickly."}
        ],
    )

    monkeypatch.setattr(
        "forecasting_harness.retrieval.registry.current_embedding_version",
        lambda **kwargs: "local-neural-v1",
    )
    monkeypatch.setattr(
        "forecasting_harness.retrieval.registry.encode_text",
        lambda text, *, alias_groups=None, requested_backend=None, model_name=None: ([0.6, 0.8], 6),
    )

    summary = registry.rebuild_embeddings()

    with registry._connect() as connection:
        row = connection.execute(
            "SELECT embedding_version, vector_json, token_count FROM chunk_vectors WHERE source_id = 'src-1' AND chunk_id = '1'"
        ).fetchone()

    assert summary["document_count"] == 1
    assert summary["chunk_count"] == 1
    assert summary["updated_chunks"] == 1
    assert row["embedding_version"] == "local-neural-v1"
    assert deserialize_vector(row["vector_json"]) == [0.6, 0.8]
    assert row["token_count"] == 6


def test_rebuild_corpus_embeddings_command_outputs_summary(tmp_path: Path) -> None:
    corpus_db = tmp_path / "corpus.db"
    registry = CorpusRegistry(corpus_db)
    registry.register_document(
        source_id="src-1",
        title="Leadership response",
        source_type="markdown",
        path="/tmp/leadership.md",
        published_at="2026-04-20",
        tags={"domain": "company-action"},
        chunks=[
            {"chunk_id": "1", "location": "heading:Overview", "content": "The chief executive stabilized messaging quickly."}
        ],
    )

    result = CliRunner().invoke(
        app,
        ["rebuild-corpus-embeddings", "--corpus-db", str(corpus_db)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["chunk_count"] == 1
    assert payload["updated_chunks"] == 1
    assert payload["embedding_version"]


def test_freshness_multiplier_is_neutral_without_published_at(tmp_path: Path) -> None:
    registry = CorpusRegistry(tmp_path / "corpus.db")
    engine = SearchEngine(registry)

    assert engine.freshness_multiplier(None) == 1.0


def test_query_api_defaults_missing_scores_consistently():
    assert summarize_top_branches(
        [
            {"branch_id": "b1", "score": 0.7, "label": "de-escalation"},
            {"branch_id": "b2", "label": "limited strike"},
        ],
        limit=2,
    ) == [
        {
            "branch_id": "b1",
            "label": "de-escalation",
            "score": 0.7,
            "confidence_signal": 0.0,
            "confidence_bucket": "",
            "calibrated_confidence": 0.0,
            "calibration_case_count": 0,
        },
        {
            "branch_id": "b2",
            "label": "limited strike",
            "score": 0,
            "confidence_signal": 0.0,
            "confidence_bucket": "",
            "calibrated_confidence": 0.0,
            "calibration_case_count": 0,
        },
    ]


def test_query_api_normalizes_none_scores_before_sorting():
    assert summarize_top_branches(
        [
            {"branch_id": "b1", "score": None, "label": "de-escalation"},
            {"branch_id": "b2", "score": 0.3, "label": "limited strike"},
        ],
        limit=2,
    ) == [
        {
            "branch_id": "b2",
            "label": "limited strike",
            "score": 0.3,
            "confidence_signal": 0.0,
            "confidence_bucket": "",
            "calibrated_confidence": 0.0,
            "calibration_case_count": 0,
        },
        {
            "branch_id": "b1",
            "label": "de-escalation",
            "score": 0,
            "confidence_signal": 0.0,
            "confidence_bucket": "",
            "calibrated_confidence": 0.0,
            "calibration_case_count": 0,
        },
    ]


def test_get_evidence_for_assumption_supports_singular_and_plural_links():
    evidence_items = [
        {"evidence_id": "ev-1", "assumption_id": "a-1"},
        {"evidence_id": "ev-2", "assumption_ids": ["a-1", "a-2"]},
        {"evidence_id": "ev-3", "assumption_ids": ["a-3"]},
    ]

    assert get_evidence_for_assumption(evidence_items, "a-1") == [
        {"evidence_id": "ev-1", "assumption_id": "a-1"},
        {"evidence_id": "ev-2", "assumption_ids": ["a-1", "a-2"]},
    ]
