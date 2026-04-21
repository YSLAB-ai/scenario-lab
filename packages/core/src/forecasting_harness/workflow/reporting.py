from __future__ import annotations

from forecasting_harness.query_api import summarize_scenario_families, summarize_top_branches


def _format_metric_map(metrics: dict[str, object]) -> str:
    parts: list[str] = []
    for name, value in metrics.items():
        if isinstance(value, float):
            rendered = f"{value:.3f}".rstrip("0").rstrip(".")
        else:
            rendered = str(value)
        parts.append(f"{name}={rendered}")
    return ", ".join(parts) if parts else "none"


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


def render_report(
    *,
    revision_id: str,
    simulation: dict[str, object],
    evidence_count: int,
    unsupported_count: int,
) -> str:
    branches = simulation.get("branches", [])
    if not isinstance(branches, list):
        branches = []

    top_branches = summarize_top_branches(branches, limit=3)
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
        "",
        "## Top Branches",
    ]
    if top_branches:
        for branch in top_branches:
            breakdown = branch.get("aggregate_score_breakdown")
            breakdown_suffix = ""
            if isinstance(breakdown, dict) and breakdown:
                breakdown_suffix = f"; breakdown: {_format_metric_map(breakdown)}"
            lines.append(f"- {branch['label']} ({branch['score']}){breakdown_suffix}")
    else:
        lines.append("- No branches were generated.")

    if scenario_families:
        lines.extend(["", "## Scenario Families"])
        for family in scenario_families:
            driver_text = ", ".join(family.get("key_drivers", [])) or "none"
            lines.append(
                f"- {family['terminal_phase']}: {family['branch_count']} branches, "
                f"representative {family['representative_label']} ({family['best_score']}), "
                f"drivers: {driver_text}"
            )

    top_branch = _resolve_top_branch(branches, top_branches)
    if top_branch is not None:
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
                f"- Terminal phase: {terminal_phase}",
                f"- Confidence signal: {top_branch.get('confidence_signal', 0.0)}",
                f"- Key drivers: {driver_text}",
            ]
        )
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
