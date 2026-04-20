from pathlib import Path

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
