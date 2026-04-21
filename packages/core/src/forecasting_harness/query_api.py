from __future__ import annotations

import re
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


def _family_id(terminal_phase: str, key_drivers: list[str]) -> str:
    parts = [terminal_phase, *key_drivers[:2]]
    slug = "-".join(re.findall(r"[a-z0-9]+", " ".join(parts).lower()))
    return slug or "scenario-family"


def _root_route_label(branch: dict[str, Any]) -> str:
    path = branch.get("path")
    if isinstance(path, list) and path:
        first_step = path[0]
        if isinstance(first_step, dict):
            label = first_step.get("label")
            if isinstance(label, str) and label:
                return label.split(" (", 1)[0]
    label = branch.get("label")
    if isinstance(label, str) and label:
        return label.split(" (", 1)[0]
    branch_id = branch.get("branch_id")
    return str(branch_id or "Scenario")


def summarize_scenario_families(branches: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for branch in branches:
        terminal_phase = str(branch.get("terminal_phase") or "unknown")
        key_drivers = [str(value) for value in branch.get("key_drivers", []) if isinstance(value, str) and value]
        root_route = _root_route_label(branch)
        family_key = f"{root_route}|{terminal_phase}"
        entry = grouped.setdefault(
            family_key,
            {
                "root_route": root_route,
                "terminal_phase": terminal_phase,
                "key_drivers": [],
                "branch_count": 0,
                "best_score": float("-inf"),
                "representative_label": "",
                "confidence_signal": 0.0,
            },
        )
        entry["branch_count"] += 1
        for driver in key_drivers:
            if driver not in entry["key_drivers"] and len(entry["key_drivers"]) < 3:
                entry["key_drivers"].append(driver)
        branch_score = _normalize_score(branch)
        if branch_score >= entry["best_score"]:
            entry["best_score"] = branch_score
            entry["representative_label"] = str(branch.get("label") or branch.get("branch_id") or "Scenario")
            entry["confidence_signal"] = float(branch.get("confidence_signal", 0.0) or 0.0)

    families = sorted(
        grouped.values(),
        key=lambda item: (item["best_score"], item["branch_count"], item["representative_label"]),
        reverse=True,
    )
    return [
        {
            "family_id": _family_id(f"{item['root_route']} {item['terminal_phase']}", list(item["key_drivers"])),
            "root_route": item["root_route"],
            "terminal_phase": item["terminal_phase"],
            "branch_count": item["branch_count"],
            "best_score": item["best_score"],
            "representative_label": item["representative_label"],
            "key_drivers": item["key_drivers"],
            "confidence_signal": item["confidence_signal"],
        }
        for item in families[:limit]
    ]


def get_evidence_for_assumption(
    evidence_items: list[dict[str, Any]],
    assumption_id: str,
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for item in evidence_items:
        if item.get("assumption_id") == assumption_id:
            matches.append(item)
            continue

        linked_assumption_ids = item.get("assumption_ids")
        if isinstance(linked_assumption_ids, str) and linked_assumption_ids == assumption_id:
            matches.append(item)
            continue
        if isinstance(linked_assumption_ids, (list, tuple, set)) and assumption_id in linked_assumption_ids:
            matches.append(item)

    return matches


def summarize_revision_change(previous_revision_id: str, next_revision_id: str) -> dict[str, str]:
    return {
        "from_revision": previous_revision_id,
        "to_revision": next_revision_id,
    }
