from __future__ import annotations

from typing import Any


def _normalize_score(branch: dict[str, Any]) -> float:
    score = branch.get("score")
    return 0 if score is None else score


def summarize_top_branches(branches: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    top_branches = sorted(branches, key=_normalize_score, reverse=True)[:limit]
    return [
        {
            "branch_id": branch["branch_id"],
            "label": branch["label"],
            "score": _normalize_score(branch),
        }
        for branch in top_branches
    ]


def get_evidence_for_assumption(
    evidence_items: list[dict[str, Any]],
    assumption_id: str,
) -> list[dict[str, Any]]:
    return [item for item in evidence_items if item.get("assumption_id") == assumption_id]
