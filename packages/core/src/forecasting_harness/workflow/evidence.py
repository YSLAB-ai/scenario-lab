from __future__ import annotations

from collections import defaultdict

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


def draft_evidence_packet(
    revision_id: str,
    hits: list[dict[str, object]],
    *,
    max_per_source: int = 2,
    max_total: int = 6,
) -> EvidencePacket:
    grouped_hits: dict[str, list[dict[str, object]]] = defaultdict(list)
    for hit in hits:
        source_id = str(hit["source_id"])
        grouped_hits[source_id].append(hit)

    items: list[EvidencePacketItem] = []
    for source_id in sorted(grouped_hits):
        source_hits = sorted(grouped_hits[source_id], key=_sort_key)
        for index, hit in enumerate(source_hits[:max_per_source], start=1):
            if len(items) >= max_total:
                return EvidencePacket(revision_id=revision_id, items=items)
            passage_id = f"{source_id}:{index}"
            items.append(
                EvidencePacketItem(
                    evidence_id=f"{revision_id}:{source_id}:{index}",
                    source_id=source_id,
                    source_title=str(hit.get("title", source_id)),
                    reason="Candidate passage for approved evidence packet",
                    passage_ids=[passage_id],
                    citation_refs=[passage_id],
                    raw_passages=[str(hit.get("content", ""))],
                )
            )

    return EvidencePacket(revision_id=revision_id, items=items)
