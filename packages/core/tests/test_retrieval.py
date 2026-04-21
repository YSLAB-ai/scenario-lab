from pathlib import Path
import sqlite3

import pytest

from forecasting_harness.query_api import get_evidence_for_assumption, summarize_top_branches
from forecasting_harness.retrieval import CorpusRegistry, RetrievalQuery, SearchEngine


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
    ) == [{"branch_id": "b1", "label": "de-escalation", "score": 0.7}]


def test_registry_search_chunks_handles_punctuation_queries(tmp_path: Path):
    registry = CorpusRegistry(tmp_path / "corpus.db")
    _register_markdown_source(registry)

    assert registry.search_chunks("state-a") == []
    assert registry.search_chunks("(") == []
    assert registry.search_chunks("-") == []


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
        {"branch_id": "b1", "label": "de-escalation", "score": 0.7},
        {"branch_id": "b2", "label": "limited strike", "score": 0},
    ]


def test_query_api_normalizes_none_scores_before_sorting():
    assert summarize_top_branches(
        [
            {"branch_id": "b1", "score": None, "label": "de-escalation"},
            {"branch_id": "b2", "score": 0.3, "label": "limited strike"},
        ],
        limit=2,
    ) == [
        {"branch_id": "b2", "label": "limited strike", "score": 0.3},
        {"branch_id": "b1", "label": "de-escalation", "score": 0},
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
