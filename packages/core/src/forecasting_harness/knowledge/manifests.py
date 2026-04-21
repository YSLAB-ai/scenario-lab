from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


def _knowledge_root() -> Path:
    return Path(__file__).resolve().parents[5] / "knowledge" / "domains"


class StarterSource(BaseModel):
    kind: str
    description: str


class DomainManifest(BaseModel):
    slug: str
    description: str
    actor_categories: list[str] = Field(default_factory=list)
    evidence_categories: list[str] = Field(default_factory=list)
    evidence_category_terms: dict[str, list[str]] = Field(default_factory=dict)
    key_state_fields: list[str] = Field(default_factory=list)
    canonical_stages: list[str] = Field(default_factory=list)
    recommended_source_types: list[str] = Field(default_factory=list)
    starter_sources: list[StarterSource] = Field(default_factory=list)
    ingestion_priorities: list[str] = Field(default_factory=list)
    freshness_notes: str = ""
    semantic_alias_groups: list[list[str]] = Field(default_factory=list)

    def alias_groups(self) -> list[tuple[str, ...]]:
        return [tuple(group) for group in self.semantic_alias_groups if group]

    def category_terms(self) -> dict[str, list[str]]:
        merged: dict[str, list[str]] = {}
        for category in self.evidence_categories:
            merged[category] = [category]

        for category, terms in self.evidence_category_terms.items():
            merged.setdefault(category, [category])
            for term in terms:
                if term not in merged[category]:
                    merged[category].append(term)
        return merged


def load_domain_manifest(slug: str) -> DomainManifest:
    manifest_path = _knowledge_root() / f"{slug}.json"
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    return DomainManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
