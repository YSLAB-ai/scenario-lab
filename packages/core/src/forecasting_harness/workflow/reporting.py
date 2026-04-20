from __future__ import annotations

from forecasting_harness.query_api import summarize_top_branches


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

    if evidence_count == 0:
        lines.extend(
            [
                "",
                "## Credibility Note",
                "- No approved evidence items. Treat this as a low-credibility exploratory run.",
            ]
        )

    return "\n".join(lines) + "\n"
