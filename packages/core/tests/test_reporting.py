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
                    "confidence_bucket": "medium",
                    "calibrated_confidence": 0.667,
                    "calibration_case_count": 3,
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
                    "confidence_bucket": "low",
                    "calibrated_confidence": 0.333,
                    "calibration_case_count": 2,
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
    assert "Calibrated confidence: medium (0.667 from 3 replay cases)" in report
    assert "- Signal resolve -> settlement-stalemate" in report


def test_render_report_humanizes_interstate_crisis_branches_and_families() -> None:
    report = render_report(
        revision_id="r1",
        domain_pack="interstate-crisis",
        simulation={
            "search_mode": "mcts",
            "node_count": 133,
            "transposition_hits": 111,
            "branches": [
                {
                    "branch_id": "alliance-consultation-2",
                    "label": "Alliance consultation (coordinated signaling)",
                    "score": 0.2894457915831681,
                    "confidence_signal": 0.2,
                    "confidence_bucket": "low",
                    "calibrated_confidence": 0.875,
                    "calibration_case_count": 6,
                    "terminal_phase": "settlement-stalemate",
                    "key_drivers": ["alliance_pressure", "diplomatic_channel", "mediation_window"],
                    "aggregate_score_breakdown": {
                        "actors": 0.167,
                        "system": 0.122,
                        "destabilization_penalty": 0.0,
                    },
                    "path": [
                        {"label": "Alliance consultation (coordinated signaling)", "phase": "negotiation-deescalation"},
                        {"label": "Signal resolve", "phase": "settlement-stalemate"},
                    ],
                },
                {
                    "branch_id": "signal",
                    "label": "Signal resolve (managed signal)",
                    "score": 0.2887236102403397,
                    "confidence_signal": 0.191,
                    "confidence_bucket": "low",
                    "calibrated_confidence": 0.875,
                    "calibration_case_count": 6,
                    "terminal_phase": "settlement-stalemate",
                    "key_drivers": ["diplomatic_channel", "leader_style", "mediation_window"],
                    "path": [{"label": "Signal resolve (managed signal)", "phase": "signaling"}],
                },
                {
                    "branch_id": "open-negotiation",
                    "label": "Open negotiation",
                    "score": 0.28652269436203087,
                    "confidence_signal": 0.337,
                    "confidence_bucket": "low",
                    "calibrated_confidence": 0.875,
                    "calibration_case_count": 6,
                    "terminal_phase": "settlement-stalemate",
                    "key_drivers": ["diplomatic_channel", "leader_style", "mediation_window"],
                    "path": [{"label": "Open negotiation", "phase": "negotiation-deescalation"}],
                },
            ],
        },
        evidence_count=7,
        unsupported_count=5,
    )

    assert "No full-scale war; allies step in and talks stay alive." in report
    assert "Engine label: Alliance consultation (coordinated signaling)" in report
    assert "Why it ranks high: Outside powers put pressure on both sides, while diplomacy stays alive long enough to avoid a wider war." in report
    assert "More warning signals, but still no break into war." in report
    assert "Engine label: Signal resolve (managed signal)" in report
    assert "Negotiations remain on the table." in report
    assert "Engine label: Open negotiation" in report
    assert "Allies step in, then the crisis freezes into a tense stalemate." in report
    assert "Engine label: Alliance consultation -> settlement-stalemate" in report
    assert "Both sides trade warnings, then the crisis freezes into a tense stalemate." in report
    assert "Negotiations stay open, then the crisis freezes into a tense stalemate." in report


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
                    "confidence_bucket": "low",
                    "calibrated_confidence": 0.333,
                    "calibration_case_count": 2,
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
                    "confidence_bucket": "medium",
                    "calibrated_confidence": 0.667,
                    "calibration_case_count": 3,
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

    assert "- Signal resolve (0.8); calibrated confidence: medium (0.667 from 3 replay cases);" in report
    assert "- Terminal phase: settlement-stalemate" in report
    assert "- Confidence signal: 0.55" in report
    assert "Signal resolve -> Confidence measures" in report
    assert "- united-states: domestic_sensitivity=0.84, alliance_dependence=0.86" in report
    assert "- Path: Limited response" not in report


def test_render_report_marks_fallback_calibration_and_rounds_scores() -> None:
    report = render_report(
        revision_id="r1",
        simulation={
            "search_mode": "mcts",
            "node_count": 13,
            "transposition_hits": 0,
            "branches": [
                {
                    "branch_id": "signal",
                    "label": "Signal resolve",
                    "score": 0.15468599999999996,
                    "confidence_signal": 0.21999999999999997,
                    "confidence_bucket": "fallback",
                    "confidence_bucket_label": "Fallback baseline",
                    "calibrated_confidence": 0.875,
                    "calibration_case_count": 0,
                    "calibration_fallback_used": True,
                    "terminal_phase": "settlement-stalemate",
                    "key_drivers": ["diplomatic_channel"],
                    "path": [{"label": "Signal resolve", "phase": "signaling"}],
                },
                {
                    "branch_id": "talks",
                    "label": "Crisis talks",
                    "score": -0.2723123,
                    "confidence_signal": 0.0444444,
                    "confidence_bucket": "low",
                    "calibrated_confidence": 0.875,
                    "calibration_case_count": 6,
                    "terminal_phase": "settlement-stalemate",
                    "key_drivers": ["mediation_window"],
                    "path": [{"label": "Crisis talks", "phase": "negotiation-deescalation"}],
                },
            ],
        },
        evidence_count=1,
        unsupported_count=0,
    )

    assert "Signal resolve (0.155); calibrated confidence: fallback baseline (0.875, 0 replay cases)" in report
    assert "Crisis talks (-0.272); calibrated confidence: low (0.875 from 6 replay cases)" in report
    assert "- Confidence signal: 0.22" in report


def test_render_report_prefers_explored_top_branch_over_unexplored_higher_score_branch() -> None:
    report = render_report(
        revision_id="r1",
        simulation={
            "search_mode": "mcts",
            "node_count": 40,
            "transposition_hits": 12,
            "branches": [
                {
                    "branch_id": "unvisited",
                    "label": "Unvisited branch",
                    "score": 0.9,
                    "visits": 0,
                    "prior": 0.9,
                    "confidence_signal": 0.0,
                    "confidence_bucket": "low",
                    "calibrated_confidence": 0.333,
                    "calibration_case_count": 2,
                    "terminal_phase": "settlement-stalemate",
                    "key_drivers": ["diplomatic_channel"],
                    "path": [{"label": "Unvisited branch", "phase": "signaling"}],
                },
                {
                    "branch_id": "visited",
                    "label": "Visited branch",
                    "score": 0.5,
                    "visits": 10,
                    "prior": 0.2,
                    "confidence_signal": 0.55,
                    "confidence_bucket": "medium",
                    "calibrated_confidence": 0.667,
                    "calibration_case_count": 3,
                    "terminal_phase": "limited-response",
                    "key_drivers": ["military_posture", "tension_index"],
                    "aggregate_score_breakdown": {
                        "system": 0.15,
                        "actors": 0.1,
                    },
                    "path": [{"label": "Visited branch", "phase": "limited-response"}],
                },
            ],
        },
        evidence_count=2,
        unsupported_count=1,
    )

    top_branches_section = report.split("## Top Branches", 1)[1].split("##", 1)[0]
    assert "- Visited branch (0.5); calibrated confidence: medium (0.667 from 3 replay cases);" in report
    assert "- Terminal phase: limited-response" in report
    assert "Visited branch" in report
    assert top_branches_section.index("- Visited branch (0.5);") < top_branches_section.index("- Unvisited branch (0.9)")


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
