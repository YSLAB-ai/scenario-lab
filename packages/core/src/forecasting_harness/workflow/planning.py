from __future__ import annotations

import re
from typing import Iterable

from forecasting_harness.knowledge.manifests import DomainManifest, StarterSource
from forecasting_harness.workflow.models import IngestionTask, IntakeDraft


def normalize_text(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def compact_query(parts: Iterable[str]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def classify_text(
    text: str,
    *,
    category_terms: dict[str, list[str]],
) -> str | None:
    normalized_text = normalize_text(text)
    best_match: tuple[int, str] | None = None
    for category, terms in category_terms.items():
        score = sum(1 for term in terms if normalize_text(term) in normalized_text)
        if score <= 0:
            continue
        if best_match is None or score > best_match[0]:
            best_match = (score, category)
    return None if best_match is None else best_match[1]


def category_match_scores(
    text: str,
    *,
    category_terms: dict[str, list[str]],
) -> dict[str, int]:
    normalized_text = normalize_text(text)
    scores: dict[str, int] = {}
    for category, terms in category_terms.items():
        score = sum(1 for term in terms if normalize_text(term) in normalized_text)
        if score > 0:
            scores[category] = score
    return scores


def starter_source_score(source: StarterSource, *, text: str, category_terms: list[str]) -> int:
    normalized_text = normalize_text(text)
    source_text = normalize_text(f"{source.kind} {source.description}")
    score = 0
    for term in category_terms:
        normalized_term = normalize_text(term)
        if normalized_term and normalized_term in source_text:
            score += 2
        if normalized_term and normalized_term in normalized_text:
            score += 1

    for token in normalize_text(source.kind).split():
        if token and token in normalized_text:
            score += 2
    for token in normalize_text(source.description).split():
        if token and token in normalized_text:
            score += 1
    return score


def select_source_role(
    manifest: DomainManifest,
    *,
    text: str,
    matched_categories: list[str],
) -> StarterSource:
    category_terms = manifest.category_terms()
    best_source = manifest.starter_sources[0]
    best_score = -1
    for source in manifest.starter_sources:
        score = 0
        for category in matched_categories:
            score += starter_source_score(source, text=text, category_terms=category_terms.get(category, [category]))
        if not matched_categories:
            score = starter_source_score(source, text=text, category_terms=[source.kind])
        if score > best_score:
            best_score = score
            best_source = source
    return best_source


def build_ingest_tasks(manifest: DomainManifest, *, missing_categories: list[str]) -> list[IngestionTask]:
    tasks: list[IngestionTask] = []
    category_terms = manifest.category_terms()
    for priority_rank, category in enumerate(missing_categories, start=1):
        source = select_source_role(manifest, text=category, matched_categories=[category])
        tasks.append(
            IngestionTask(
                evidence_category=category,
                priority_rank=priority_rank,
                source_role=source.kind,
                starter_source=source.model_dump(mode="json"),
                recommended_source_types=list(manifest.recommended_source_types),
            )
        )
    return tasks


def build_query_variants(
    intake: IntakeDraft,
    manifest: DomainManifest,
    *,
    query_text: str | None = None,
) -> list[str]:
    entity_text = " ".join(intake.focus_entities)
    variants: list[str] = []

    if query_text:
        variants.append(compact_query([query_text]))
        variants.append(compact_query([entity_text, query_text]))

    variants.append(compact_query([entity_text, intake.current_development, intake.current_stage]))

    for category in manifest.evidence_categories:
        variants.append(compact_query([entity_text, intake.current_development, category]))

    deduped: list[str] = []
    seen: set[str] = set()
    for value in variants:
        if value and value not in seen:
            deduped.append(value)
            seen.add(value)
    return deduped
