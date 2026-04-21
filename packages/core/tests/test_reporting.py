from forecasting_harness.query_api import summarize_scenario_families
from forecasting_harness.workflow.reporting import render_report


def test_summarize_scenario_families_keeps_distinct_root_routes_separate() -> None:
    families = summarize_scenario_families(
        [
            {
                "branch_id": "signal",
                "label": "Signal resolve",
                "score": 0.8,
                "terminal_phase": "settlement-stalemate",
                "key_drivers": ["diplomatic_channel", "tension_index"],
                "path": [{"label": "Signal resolve", "phase": "signaling"}],
            },
            {
                "branch_id": "open-negotiation",
                "label": "Open negotiation",
                "score": 0.7,
                "terminal_phase": "settlement-stalemate",
                "key_drivers": ["diplomatic_channel"],
                "path": [{"label": "Open negotiation", "phase": "negotiation-deescalation"}],
            },
            {
                "branch_id": "retaliate",
                "label": "Retaliate",
                "score": -0.1,
                "terminal_phase": "escalation",
                "key_drivers": ["military_posture", "tension_index"],
                "path": [{"label": "Retaliate", "phase": "escalation"}],
            },
        ]
    )

    assert families[0]["terminal_phase"] == "settlement-stalemate"
    assert families[0]["branch_count"] == 1
    assert families[0]["representative_label"] == "Signal resolve"
    assert {family["representative_label"] for family in families[:2]} == {"Signal resolve", "Open negotiation"}


def test_render_report_includes_scenario_families_key_drivers_and_search_summary() -> None:
    report = render_report(
        revision_id="r1",
        simulation={
            "search_mode": "mcts",
            "node_count": 40,
            "transposition_hits": 12,
            "branches": [
                {
                    "branch_id": "signal",
                    "label": "Signal resolve",
                    "score": 0.8,
                    "confidence_signal": 0.55,
                    "terminal_phase": "settlement-stalemate",
                    "key_drivers": ["diplomatic_channel", "tension_index"],
                    "path": [
                        {"label": "Signal resolve", "phase": "signaling"},
                        {"label": "Confidence measures", "phase": "settlement-stalemate"},
                    ],
                },
                {
                    "branch_id": "limited-response",
                    "label": "Limited response",
                    "score": 0.2,
                    "confidence_signal": 0.25,
                    "terminal_phase": "limited-response",
                    "key_drivers": ["military_posture", "tension_index"],
                    "path": [{"label": "Limited response", "phase": "limited-response"}],
                },
            ],
        },
        evidence_count=2,
        unsupported_count=1,
    )

    assert "## Scenario Families" in report
    assert "## Top Branch Detail" in report
    assert "## Search Summary" in report
    assert "diplomatic_channel, tension_index" in report
    assert "Signal resolve -> Confidence measures" in report
