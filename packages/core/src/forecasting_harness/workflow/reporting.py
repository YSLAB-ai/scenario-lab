from __future__ import annotations

from forecasting_harness.query_api import summarize_scenario_families, summarize_top_branches


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
        "## Top Branches",
    ]
    if top_branches:
        for branch in top_branches:
            lines.append(f"- {branch['label']} ({branch['score']})")
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

    if top_branches and isinstance(branches[0], dict):
        top_branch = branches[0]
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
