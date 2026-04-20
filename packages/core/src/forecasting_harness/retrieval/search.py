from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from forecasting_harness.retrieval.registry import CorpusRegistry


@dataclass(frozen=True)
class RetrievalQuery:
    text: str
    filters: dict[str, str] = field(default_factory=dict)


class SearchEngine:
    def __init__(self, registry: CorpusRegistry):
        self.registry = registry

    def freshness_multiplier(self, published_at: str) -> float:
        try:
            published_date = datetime.strptime(published_at, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError(f"invalid published_at date: {published_at!r}") from exc

        age_days = (date.today() - published_date).days
        return min(1.0, max(0.2, 1 - (age_days / 365)))

    def search(self, query: RetrievalQuery) -> list[dict[str, Any]]:
        hits: list[dict[str, Any]] = []
        for row in self.registry.search_chunks(query.text):
            tags = row.get("tags") or {}
            if any(tags.get(key) != value for key, value in query.filters.items()):
                continue

            result = dict(row)
            result["score"] = self.freshness_multiplier(result["published_at"])
            hits.append(result)

        hits.sort(key=lambda item: (-item["score"], item["source_id"]))
        return hits
