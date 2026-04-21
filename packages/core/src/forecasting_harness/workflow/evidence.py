from __future__ import annotations

from collections import defaultdict

from forecasting_harness.workflow.planning import classify_text

from forecasting_harness.workflow.models import EvidencePacket, EvidencePacketItem


def _sort_key(hit: dict[str, object]) -> tuple[float, str, str, str]:
    score = hit.get("score", 0.0)
    try:
        normalized_score = float(score)
    except (TypeError, ValueError):
        normalized_score = 0.0
    return (
        -normalized_score,
        str(hit.get("title", "")),
        str(hit.get("content", "")),
        str(hit.get("published_at", "")),
    )


def _candidate_sort_key(candidate: tuple[str, int, dict[str, object]]) -> tuple[float, str, str, str, str, int]:
    source_id, source_rank, hit = candidate
    return (*_sort_key(hit), source_id, source_rank)

def _classify_hit(
    hit: dict[str, object],
    *,
    category_terms: dict[str, list[str]],
) -> str | None:
    text = " ".join(
        [
            str(hit.get("title", "")),
            str(hit.get("content", "")),
            " ".join(f"{key} {value}" for key, value in (hit.get("tags") or {}).items()),
        ]
    )
    return classify_text(text, category_terms=category_terms)


def draft_evidence_packet(
    revision_id: str,
    hits: list[dict[str, object]],
    *,
    max_per_source: int = 2,
    max_total: int = 6,
    evidence_categories: list[str] | None = None,
    category_terms: dict[str, list[str]] | None = None,
) -> EvidencePacket:
    grouped_hits: dict[str, list[dict[str, object]]] = defaultdict(list)
    for hit in hits:
        source_id = str(hit["source_id"])
        grouped_hits[source_id].append(hit)

    candidates: list[tuple[str, int, dict[str, object], str | None]] = []
    category_terms = category_terms or {}
    for source_id in sorted(grouped_hits):
        source_hits = sorted(grouped_hits[source_id], key=_sort_key)
        for index, hit in enumerate(source_hits[:max_per_source], start=1):
            candidates.append((source_id, index, hit, _classify_hit(hit, category_terms=category_terms)))

    selected: list[tuple[str, int, dict[str, object], str | None]] = []
    seen: set[tuple[str, int]] = set()
    sorted_candidates = sorted(candidates, key=lambda candidate: _candidate_sort_key(candidate[:3]))

    for category in evidence_categories or []:
        for source_id, source_rank, hit, matched_category in sorted_candidates:
            key = (source_id, source_rank)
            if key in seen or matched_category != category:
                continue
            selected.append((source_id, source_rank, hit, matched_category))
            seen.add(key)
            break

    items: list[EvidencePacketItem] = []
    for source_id, source_rank, hit, matched_category in sorted_candidates:
        key = (source_id, source_rank)
        if key in seen:
            continue
        if len(selected) >= max_total:
            break
        selected.append((source_id, source_rank, hit, matched_category))
        seen.add(key)

    for source_id, source_rank, hit, matched_category in sorted(
        selected[:max_total], key=lambda candidate: _candidate_sort_key(candidate[:3])
    ):
        passage_id = f"{source_id}:{source_rank}"
        reason = "Candidate passage for approved evidence packet"
        if matched_category:
            reason = f"{reason}: {matched_category}"
        items.append(
            EvidencePacketItem(
                evidence_id=f"{revision_id}:{source_id}:{source_rank}",
                source_id=source_id,
                source_title=str(hit.get("title", source_id)),
                reason=reason,
                passage_ids=[passage_id],
                citation_refs=[passage_id],
                raw_passages=[str(hit.get("content", ""))],
            )
        )

    return EvidencePacket(revision_id=revision_id, items=items)
