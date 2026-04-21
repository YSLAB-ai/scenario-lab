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
            "actor_utility_summary": [
                {
                    "actor_id": "united-states",
                    "actor_name": "United States",
                    "preferences": {
                        "domestic_sensitivity": 0.84,
                        "alliance_dependence": 0.86,
                    },
                }
            ],
            "aggregation_lens": {
                "name": "domestic-politics-first",
                "aggregation_mode": "focal-actor",
                "focal_actor_id": "united-states",
                "destabilization_penalty": 0.15,
                "metric_weights": {
                    "escalation": -0.4,
                    "negotiation": 0.3,
                    "economic_stress": -0.3,
                },
                "actor_metric_weights": {
                    "domestic_sensitivity": 0.6,
                    "alliance_dependence": 0.05,
                },
                "actor_weights": {"united-states": 1.0},
            },
            "branches": [
                {
                    "branch_id": "signal",
                    "label": "Signal resolve",
                    "score": 0.8,
                    "confidence_signal": 0.55,
                    "terminal_phase": "settlement-stalemate",
                    "key_drivers": ["diplomatic_channel", "tension_index"],
                    "aggregate_score_breakdown": {
                        "system": 0.42,
                        "actors": 0.48,
                        "destabilization_penalty": -0.1,
                    },
                    "terminal_actor_metrics": {
                        "united-states": {
                            "domestic_sensitivity": 0.84,
                            "alliance_dependence": 0.86,
                        }
                    },
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
    assert "## Actor Utility Summary" in report
    assert "## Aggregation Lens" in report
    assert "## Top Branch Aggregate Breakdown" in report
    assert "## Search Summary" in report
    assert "diplomatic_channel, tension_index" in report
    assert "Signal resolve -> Confidence measures" in report
    assert "United States: domestic_sensitivity=0.84, alliance_dependence=0.86" in report
    assert "Lens: domestic-politics-first" in report
    assert "system=0.42, actors=0.48, destabilization_penalty=-0.1" in report


def test_render_report_top_branch_detail_matches_sorted_top_branch_list() -> None:
    report = render_report(
        revision_id="r1",
        simulation={
            "search_mode": "mcts",
            "node_count": 40,
            "transposition_hits": 12,
            "branches": [
                {
                    "branch_id": "limited-response",
                    "label": "Limited response",
                    "score": 0.2,
                    "confidence_signal": 0.25,
                    "terminal_phase": "limited-response",
                    "key_drivers": ["military_posture", "tension_index"],
                    "aggregate_score_breakdown": {
                        "system": 0.15,
                        "actors": 0.1,
                    },
                    "terminal_actor_metrics": {
                        "iran": {"coercive_bias": 0.6},
                    },
                    "path": [{"label": "Limited response", "phase": "limited-response"}],
                },
                {
                    "branch_id": "signal",
                    "label": "Signal resolve",
                    "score": 0.8,
                    "confidence_signal": 0.55,
                    "terminal_phase": "settlement-stalemate",
                    "key_drivers": ["diplomatic_channel", "tension_index"],
                    "aggregate_score_breakdown": {
                        "system": 0.42,
                        "actors": 0.48,
                        "destabilization_penalty": -0.1,
                    },
                    "terminal_actor_metrics": {
                        "united-states": {
                            "domestic_sensitivity": 0.84,
                            "alliance_dependence": 0.86,
                        }
                    },
                    "path": [
                        {"label": "Signal resolve", "phase": "signaling"},
                        {"label": "Confidence measures", "phase": "settlement-stalemate"},
                    ],
                },
            ],
        },
        evidence_count=2,
        unsupported_count=1,
    )

    assert "- Signal resolve (0.8);" in report
    assert "- Terminal phase: settlement-stalemate" in report
    assert "Signal resolve -> Confidence measures" in report
    assert "- united-states: domestic_sensitivity=0.84, alliance_dependence=0.86" in report
    assert "Limited response ->" not in report


def test_render_report_includes_recommended_lens_when_it_differs_from_selected_lens() -> None:
    report = render_report(
        revision_id="r1",
        simulation={
            "aggregation_lens": {
                "name": "balanced-system",
                "aggregation_mode": "balanced-system",
                "metric_weights": {"escalation": -0.4},
                "actor_metric_weights": {"domestic_sensitivity": 0.25},
                "actor_weights": {},
                "destabilization_penalty": 0.1,
            },
            "recommended_run_lens": {
                "name": "domestic-politics-first",
                "aggregation_mode": "focal-actor",
                "focal_actor_id": "united-states",
                "metric_weights": {"escalation": -0.4},
                "actor_metric_weights": {"domestic_sensitivity": 0.6},
                "actor_weights": {},
                "destabilization_penalty": 0.15,
            },
            "branches": [],
        },
        evidence_count=1,
        unsupported_count=0,
    )

    assert "## Aggregation Lens" in report
    assert "Lens: balanced-system" in report
    assert "Recommended lens: domestic-politics-first" in report
    assert "Recommended focal actor: united-states" in report
