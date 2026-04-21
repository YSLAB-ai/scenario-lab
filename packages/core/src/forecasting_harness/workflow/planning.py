from __future__ import annotations

import re
from typing import Iterable

from forecasting_harness.knowledge.manifests import DomainManifest
from forecasting_harness.workflow.models import IntakeDraft


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
