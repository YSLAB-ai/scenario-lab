from pathlib import Path
import sqlite3

import pytest

from forecasting_harness.query_api import summarize_top_branches
from forecasting_harness.retrieval import CorpusRegistry, RetrievalQuery, SearchEngine


def test_registry_registers_documents_and_returns_chunk_hits(tmp_path: Path):
    registry = CorpusRegistry(tmp_path / "corpus.db")
    registry.register_document(
        source_id="src-1",
        title="Recent logistics report",
        source_type="markdown",
        published_at="2026-04-18",
        tags={"domain": "conflict", "actor": "state-a"},
        content="# Report\nFuel stockpiles are strained.\n",
    )

    hits = SearchEngine(registry).search(
        RetrievalQuery(text="fuel stockpiles", filters={"domain": "conflict"})
    )

    assert hits[0]["source_id"] == "src-1"


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
    registry.register_document(
        source_id="src-1",
        title="Recent logistics report",
        source_type="markdown",
        published_at="2026-04-18",
        tags={"domain": "conflict", "actor": "state-a"},
        content="# Report\nFuel stockpiles are strained.\n",
    )

    assert registry.search_chunks("state-a") == []
    assert registry.search_chunks("(") == []
    assert registry.search_chunks("-") == []


def test_registry_search_chunks_raises_for_missing_table(tmp_path: Path):
    registry = CorpusRegistry(tmp_path / "corpus.db")
    with registry._connect() as connection:
        connection.execute("DROP TABLE chunks")

    with pytest.raises(sqlite3.OperationalError):
        registry.search_chunks("fuel")


def test_registry_re_registering_source_id_replaces_existing_rows(tmp_path: Path):
    registry = CorpusRegistry(tmp_path / "corpus.db")
    registry.register_document(
        source_id="src-1",
        title="Recent logistics report",
        source_type="markdown",
        published_at="2026-04-18",
        tags={"domain": "conflict", "actor": "state-a"},
        content="# Report\nFuel stockpiles are strained.\n",
    )
    registry.register_document(
        source_id="src-1",
        title="Updated logistics report",
        source_type="markdown",
        published_at="2026-04-19",
        tags={"domain": "conflict", "actor": "state-a"},
        content="# Report\nFuel stockpiles are still strained.\n",
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
