from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from forecasting_harness.retrieval.registry import CorpusRegistry, parse_published_at


@dataclass(frozen=True)
class RetrievalQuery:
    text: str
    filters: dict[str, str] = field(default_factory=dict)


class SearchEngine:
    def __init__(self, registry: CorpusRegistry):
        self.registry = registry

    def freshness_multiplier(self, published_at: str | None) -> float:
        normalized_published_at = parse_published_at(published_at)
        if normalized_published_at is None:
            return 1.0
        published_date = datetime.strptime(normalized_published_at, "%Y-%m-%d").date()
        age_days = (date.today() - published_date).days
        return min(1.0, max(0.2, 1 - (age_days / 365)))

    def search(
        self,
        query: RetrievalQuery,
        *,
        freshness_policy: dict[str, float] | None = None,
    ) -> list[dict[str, Any]]:
        freshness_policy = freshness_policy or {}
        hits: list[dict[str, Any]] = []
        for row in self.registry.search_chunks(query.text):
            tags = row.get("tags") or {}
            if any(tags.get(key) != value for key, value in query.filters.items()):
                continue

            result = dict(row)
            domain_weight = 1.0
            domain_name = tags.get("domain")
            if isinstance(domain_name, str):
                domain_weight = freshness_policy.get(domain_name, 1.0)
            result["score"] = self.freshness_multiplier(result["published_at"]) * domain_weight
            hits.append(result)

        hits.sort(key=lambda item: (-item["score"], item["source_id"]))
        return hits
