from __future__ import annotations

from forecasting_harness.query_api import summarize_scenario_families, summarize_top_branches


_INTERSTATE_BRANCH_SUMMARIES: dict[str, tuple[str, str]] = {
    "Alliance consultation (coordinated signaling)": (
        "No major escalation; allies push talks, then a tense stalemate.",
        "Outside powers pressure both sides to keep diplomacy open; the run ends in an "
        "uneasy stalemate, not a settlement.",
    ),
    "Signal resolve (managed signal)": (
        "Warnings increase, then a tense stalemate.",
        "Washington and Tehran keep signaling resolve, but the branch still ends in a contained stalemate.",
    ),
    "Open negotiation": (
        "Talks stay open, but the crisis remains unresolved.",
        "Diplomacy remains available, but it does not fully resolve the crisis in this run.",
    ),
}

_INTERSTATE_FAMILY_SUMMARIES: dict[tuple[str, str], tuple[str, str]] = {
    (
        "Alliance consultation",
        "settlement-stalemate",
    ): (
        "Allies push talks, then a tense stalemate.",
        "Outside powers pressure both sides to keep diplomacy open; the run ends in an "
        "uneasy stalemate, not a settlement.",
    ),
    (
        "Signal resolve",
        "settlement-stalemate",
    ): (
        "Warnings increase, then a tense stalemate.",
        "Washington and Tehran keep signaling resolve, but the branch still ends in a contained stalemate.",
    ),
    (
        "Open negotiation",
        "settlement-stalemate",
    ): (
        "Talks stay open, then a tense stalemate.",
        "Diplomacy remains available, but it does not fully resolve the crisis in this run.",
    ),
}


_MODEL_BOUNDARY_NOTES: dict[str, str] = {
    "interstate-crisis": (
        "This pack models bounded interstate-crisis paths: signaling, limited response, "
        "escalation pressure, negotiation, and stalemate. It does not model full-scale "
        "war as an explicit terminal outcome."
    )
}


def _format_float(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _format_metric_map(metrics: dict[str, object]) -> str:
    parts: list[str] = []
    for name, value in metrics.items():
        if isinstance(value, float):
            rendered = _format_float(value)
        else:
            rendered = str(value)
        parts.append(f"{name}={rendered}")
    return ", ".join(parts) if parts else "none"


def _format_calibrated_confidence(branch: dict[str, object]) -> str:
    bucket = str(branch.get("confidence_bucket") or "unavailable")
    bucket_label = str(
        branch.get("confidence_bucket_label")
        or ("Fallback baseline" if bucket == "fallback" else bucket)
    )
    confidence = float(branch.get("calibrated_confidence", 0.0) or 0.0)
    case_count = int(branch.get("calibration_case_count", 0) or 0)
    fallback_used = bool(branch.get("calibration_fallback_used", False))
    if case_count > 0:
        return f"{bucket} ({_format_float(confidence)} from {case_count} replay cases)"
    if fallback_used:
        return f"{bucket_label.lower()} ({_format_float(confidence)}, 0 replay cases)"
    return f"{bucket} ({_format_float(confidence)})"


def _actor_utility_lines(simulation: dict[str, object]) -> list[str]:
    actor_summary = simulation.get("actor_utility_summary", [])
    if not isinstance(actor_summary, list) or not actor_summary:
        return ["- No inferred actor utility preferences were available."]

    lines: list[str] = []
    for actor in actor_summary:
        if not isinstance(actor, dict):
            continue
        actor_name = str(actor.get("actor_name") or actor.get("actor_id") or "unknown")
        preferences = actor.get("preferences")
        preference_map = dict(preferences) if isinstance(preferences, dict) else {}
        lines.append(f"- {actor_name}: {_format_metric_map(preference_map)}")
    return lines or ["- No inferred actor utility preferences were available."]


def _aggregation_lens_lines(simulation: dict[str, object]) -> list[str]:
    lens = simulation.get("aggregation_lens")
    if not isinstance(lens, dict) or not lens:
        return ["- Lens: unavailable"]

    lines = [
        f"- Lens: {lens.get('name', 'unknown')}",
        f"- Aggregation mode: {lens.get('aggregation_mode', 'unknown')}",
    ]
    focal_actor_id = lens.get("focal_actor_id")
    if focal_actor_id:
        lines.append(f"- Focal actor: {focal_actor_id}")
    lines.append(f"- System weights: {_format_metric_map(dict(lens.get('metric_weights', {})))}")
    lines.append(f"- Actor weights: {_format_metric_map(dict(lens.get('actor_metric_weights', {})))}")
    actor_weights = dict(lens.get("actor_weights", {}))
    if actor_weights:
        lines.append(f"- Actor multipliers: {_format_metric_map(actor_weights)}")
    lines.append(f"- Destabilization penalty: {lens.get('destabilization_penalty', 0.0)}")
    recommended_lens = simulation.get("recommended_run_lens")
    if isinstance(recommended_lens, dict) and recommended_lens and recommended_lens != lens:
        lines.append(f"- Recommended lens: {recommended_lens.get('name', 'unknown')}")
        lines.append(f"- Recommended aggregation mode: {recommended_lens.get('aggregation_mode', 'unknown')}")
        recommended_focal_actor = recommended_lens.get("focal_actor_id")
        if recommended_focal_actor:
            lines.append(f"- Recommended focal actor: {recommended_focal_actor}")
    return lines


def _resolve_top_branch(
    branches: list[dict[str, object]],
    top_branches: list[dict[str, object]],
) -> dict[str, object] | None:
    if not top_branches:
        return None
    top_branch_id = top_branches[0].get("branch_id")
    for branch in branches:
        if isinstance(branch, dict) and branch.get("branch_id") == top_branch_id:
            return branch
    return None


def _humanized_branch_summary(
    branch: dict[str, object],
    *,
    domain_pack: str | None,
) -> tuple[str, str | None, str]:
    label = str(branch.get("label") or branch.get("branch_id") or "Scenario")
    if domain_pack == "interstate-crisis":
        summary = _INTERSTATE_BRANCH_SUMMARIES.get(label)
        if summary is not None:
            return summary[0], summary[1], label
    return label, None, label


def _humanized_family_summary(
    family: dict[str, object],
    *,
    domain_pack: str | None,
) -> tuple[str, str | None, str]:
    root_route = str(family.get("root_route") or "Scenario")
    terminal_phase = str(family.get("terminal_phase") or "unknown")
    raw_label = f"{root_route} -> {terminal_phase}"
    if domain_pack == "interstate-crisis":
        summary = _INTERSTATE_FAMILY_SUMMARIES.get((root_route, terminal_phase))
        if summary is not None:
            return summary[0], summary[1], raw_label
    return raw_label, None, raw_label


def _model_boundary_lines(domain_pack: str | None) -> list[str]:
    note = _MODEL_BOUNDARY_NOTES.get(domain_pack or "")
    if note is None:
        return []
    return ["", "## Model Boundary", f"- {note}"]


def render_report(
    *,
    revision_id: str,
    domain_pack: str | None = None,
    simulation: dict[str, object],
    evidence_count: int,
    unsupported_count: int,
) -> str:
    branches = simulation.get("branches", [])
    if not isinstance(branches, list):
        branches = []

    top_branches = summarize_top_branches(branches, limit=3, detailed=True)
    scenario_families = summarize_scenario_families(branches, limit=3)
    lines = [
        "# Scenario Report",
        "",
        f"- Revision: {revision_id}",
        f"- Approved evidence items: {evidence_count}",
        f"- Unsupported assumptions: {unsupported_count}",
        "",
        "## Actor Utility Summary",
        *_actor_utility_lines(simulation),
        "",
        "## Aggregation Lens",
        *_aggregation_lens_lines(simulation),
        *_model_boundary_lines(domain_pack),
        "",
        "## Top Branches",
    ]
    if top_branches:
        for branch in top_branches:
            title, explanation, raw_label = _humanized_branch_summary(branch, domain_pack=domain_pack)
            breakdown = branch.get("aggregate_score_breakdown")
            breakdown_suffix = ""
            if isinstance(breakdown, dict) and breakdown:
                breakdown_suffix = f"; breakdown: {_format_metric_map(breakdown)}"
            lines.append(
                f"- {title} ({_format_float(float(branch['score']))}); calibrated confidence: "
                f"{_format_calibrated_confidence(branch)}{breakdown_suffix}"
            )
            if title != raw_label:
                lines.append(f"  - Engine label: {raw_label}")
            if explanation:
                lines.append(f"  - Why it ranks high: {explanation}")
    else:
        lines.append("- No branches were generated.")

    if scenario_families:
        lines.extend(["", "## Scenario Families"])
        for family in scenario_families:
            title, explanation, raw_label = _humanized_family_summary(family, domain_pack=domain_pack)
            driver_text = ", ".join(family.get("key_drivers", [])) or "none"
            lines.append(f"- {title}")
            if title != raw_label:
                lines.append(f"  - Engine label: {raw_label}")
            lines.append(
                f"  - Branches: {family['branch_count']}; representative: {family['representative_label']} "
                f"({_format_float(float(family['best_score']))}); drivers: {driver_text}; "
                f"calibrated confidence: {_format_calibrated_confidence(family)}"
            )
            if explanation:
                lines.append(f"  - Plain-English reading: {explanation}")

    top_branch = _resolve_top_branch(branches, top_branches)
    if top_branch is not None:
        title, explanation, raw_label = _humanized_branch_summary(top_branch, domain_pack=domain_pack)
        path = top_branch.get("path", [])
        path_labels = " -> ".join(
            item["label"] for item in path if isinstance(item, dict) and isinstance(item.get("label"), str)
        )
        driver_text = ", ".join(str(value) for value in top_branch.get("key_drivers", []) if value) or "none"
        terminal_phase = top_branch.get("terminal_phase") or "unknown"
        lines.extend(
            [
                "",
                "## Top Branch Detail",
                f"- Plain-English outcome: {title}",
                f"- Terminal phase: {terminal_phase}",
                f"- Confidence signal: {_format_float(float(top_branch.get('confidence_signal', 0.0) or 0.0))}",
                f"- Calibrated confidence: {_format_calibrated_confidence(top_branch)}",
                f"- Key drivers: {driver_text}",
            ]
        )
        if title != raw_label:
            lines.append(f"- Engine label: {raw_label}")
        if explanation:
            lines.append(f"- Why it ranks high: {explanation}")
        if path_labels:
            lines.append(f"- Path: {path_labels}")
        breakdown = top_branch.get("aggregate_score_breakdown")
        if isinstance(breakdown, dict) and breakdown:
            lines.extend(["", "## Top Branch Aggregate Breakdown", f"- {_format_metric_map(breakdown)}"])
        actor_impacts = top_branch.get("terminal_actor_metrics")
        if isinstance(actor_impacts, dict) and actor_impacts:
            lines.extend(["", "## Top Branch Actor Impacts"])
            for actor_id, metrics in actor_impacts.items():
                if isinstance(metrics, dict):
                    lines.append(f"- {actor_id}: {_format_metric_map(metrics)}")

    lines.extend(
        [
            "",
            "## Search Summary",
            f"- Search mode: {simulation.get('search_mode', 'unknown')}",
            f"- Node count: {simulation.get('node_count', 0)}",
            f"- Transposition hits: {simulation.get('transposition_hits', 0)}",
        ]
    )

    if evidence_count == 0:
        lines.extend(
            [
                "",
                "## Credibility Note",
                "- No approved evidence items. Treat this as a low-credibility exploratory run.",
            ]
        )

    return "\n".join(lines) + "\n"
