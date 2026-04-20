from __future__ import annotations

from collections import defaultdict

from forecasting_harness.workflow.models import EvidencePacket, EvidencePacketItem


def draft_evidence_packet(
    revision_id: str,
    hits: list[dict[str, object]],
    *,
    max_per_source: int = 2,
) -> EvidencePacket:
    grouped_hits: dict[str, list[dict[str, object]]] = defaultdict(list)
    for hit in hits:
        source_id = str(hit["source_id"])
        grouped_hits[source_id].append(hit)

    items: list[EvidencePacketItem] = []
    for source_id, source_hits in grouped_hits.items():
        for index, hit in enumerate(source_hits[:max_per_source], start=1):
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
