from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.cli import app
from forecasting_harness.domain.registry import build_default_registry
from forecasting_harness.knowledge import load_builtin_replay_cases
from forecasting_harness.replay import (
    CalibrationSummary,
    ReplayCase,
    ReplayCaseResult,
    ReplaySource,
    ReplaySuiteResult,
    run_replay_suite,
    summarize_calibration,
)
from forecasting_harness.retrieval import CorpusRegistry
from forecasting_harness.workflow.models import AssumptionSummary, IntakeDraft
from forecasting_harness.workflow.service import WorkflowService


def _replay_case() -> ReplayCase:
    return ReplayCase(
        run_id="apple-transition",
        domain_pack="company-action",
        case_title="Apple succession stress test",
        time_anchor="synthetic",
        historical_outcome="Stakeholder reset preserved the core franchise while the board stabilized leadership messaging.",
        sources=[
            ReplaySource(title="Internal scenario source", publisher="repo", url="https://example.invalid/apple-1"),
        ],
        intake=IntakeDraft(
            event_framing="Assess Apple strategy after a sudden CEO transition during product delays and margin pressure.",
            focus_entities=["Apple"],
            current_development="Apple faces a sudden CEO transition after product delays, investor concern, and supplier anxiety.",
            current_stage="trigger",
            time_horizon="180d",
            suggested_entities=["Board", "Key Customers"],
        ),
        assumptions=AssumptionSummary(
            summary=["The board wants stability before the next product cycle"],
            suggested_actors=["Board", "Key Customers"],
        ),
        documents={
            "apple-succession.md": "Analysts focus on Apple succession clarity, supplier reassurance, and investor concern after product delays.",
            "apple-roadmap.md": "Apple product roadmap credibility and premium brand messaging are central to calming customers and suppliers.",
        },
        expected_top_branch="Stakeholder reset",
        expected_evidence_sources=["apple-roadmap", "apple-succession"],
        expected_inferred_fields=[
            "board_cohesion",
            "brand_sentiment",
            "cash_runway_months",
            "operational_stability",
            "regulatory_pressure",
        ],
        expected_root_strategy="Stakeholder reset",
    )


def _market_replay_case() -> ReplayCase:
    return ReplayCase(
        run_id="market-rate-shock",
        domain_pack="market-shock",
        intake=IntakeDraft(
            event_framing="Assess market scenarios after an unexpected emergency rate hike.",
            focus_entities=["Central Bank", "Global Equity Market"],
            current_development="An emergency rate hike shocks funding markets, credit spreads, and rate expectations.",
            current_stage="trigger",
            time_horizon="14d",
            suggested_entities=["Banks", "Treasury Market"],
        ),
        assumptions=AssumptionSummary(
            summary=["Authorities will prioritize market functioning if stress worsens"],
            suggested_actors=["Banks", "Treasury Market"],
        ),
        documents={
            "rate-shock.md": "The emergency rate hike triggers repricing across bonds and equities while liquidity stress rises.",
            "funding-stress.md": "Funding markets widen immediately and investors debate whether policy credibility has improved or deteriorated.",
        },
        expected_top_branch="Emergency liquidity",
        expected_evidence_sources=["funding-stress", "rate-shock"],
        expected_inferred_fields=[
            "contagion_risk",
            "liquidity_stress",
            "policy_credibility",
            "policy_optionality",
            "rate_pressure",
        ],
        expected_root_strategy="Emergency liquidity",
    )


def _regulatory_replay_case() -> ReplayCase:
    return ReplayCase(
        run_id="regulator-adtech",
        domain_pack="regulatory-enforcement",
        intake=IntakeDraft(
            event_framing="Assess a large ad-tech platform response to an escalating enforcement case.",
            focus_entities=["AdTech Platform", "Competition Regulator"],
            current_development="A competition regulator escalates an ad-tech case and signals possible structural remedies.",
            current_stage="trigger",
            time_horizon="120d",
            suggested_entities=["Publishers", "Major Advertisers"],
        ),
        assumptions=AssumptionSummary(
            summary=["A negotiated remedy is preferable to protracted litigation"],
            suggested_actors=["Publishers", "Major Advertisers"],
        ),
        documents={
            "adtech-remedies.md": "Regulators signal willingness to seek structural remedies while industry partners brace for disruption.",
            "adtech-remediation.md": "The ad-tech platform expands internal remediation and coordinates with external counsel as enforcement momentum builds.",
        },
        expected_top_branch="Internal remediation",
        expected_evidence_sources=["adtech-remediation", "adtech-remedies"],
        expected_inferred_fields=[
            "compliance_posture",
            "enforcement_momentum",
            "litigation_readiness",
            "public_attention",
            "remedy_severity",
        ],
        expected_root_strategy="Internal remediation",
    )


def _election_replay_case() -> ReplayCase:
    return ReplayCase(
        run_id="election-debate-collapse",
        domain_pack="election-shock",
        intake=IntakeDraft(
            event_framing="Assess how a major debate collapse changes the final month of a national election.",
            focus_entities=["Incumbent Party", "Opposition Party"],
            current_development="A debate collapse forces both campaigns to reset strategy as party leadership scrambles to stabilize messaging.",
            current_stage="trigger",
            time_horizon="30d",
            suggested_entities=["Media", "Party Leadership"],
        ),
        assumptions=AssumptionSummary(
            summary=["Turnout effects may matter more than persuasion"],
            suggested_actors=["Media", "Party Leadership"],
        ),
        documents={
            "debate-fallout.md": "Party leadership scrambles to stabilize messaging after the debate while donor confidence softens.",
            "turnout-rescue.md": "Campaign organizers launch a turnout rescue plan to keep early vote mobilization from collapsing.",
        },
        expected_top_branch="Message reset (reset holds)",
        expected_evidence_sources=["debate-fallout", "turnout-rescue"],
        expected_inferred_fields=[
            "coalition_fragility",
            "donor_confidence",
            "message_discipline",
            "poll_margin",
            "turnout_energy",
        ],
        expected_root_strategy="Message reset",
    )


def _supply_replay_case() -> ReplayCase:
    return ReplayCase(
        run_id="supplier-flooding",
        domain_pack="supply-chain-disruption",
        intake=IntakeDraft(
            event_framing="Assess an auto supply chain after flooding shuts a single-source electronics plant.",
            focus_entities=["Automaker", "Electronics Supplier"],
            current_development="Severe flooding shuts a single-source electronics plant feeding a major automaker.",
            current_stage="trigger",
            time_horizon="60d",
            suggested_entities=["Alternate Suppliers", "Logistics Partners"],
        ),
        assumptions=AssumptionSummary(
            summary=["The automaker will prioritize its highest-margin models"],
            suggested_actors=["Alternate Suppliers", "Logistics Partners"],
        ),
        documents={
            "supplier-flood.md": "Flooding disrupts a single-source electronics plant and leaves the automaker with thin inventory cover.",
            "supplier-reroute.md": "The automaker and logistics partners consider rerouting and alternate suppliers to keep launches alive.",
        },
        expected_top_branch="Reserve logistics",
        expected_evidence_sources=["supplier-flood", "supplier-reroute"],
        expected_inferred_fields=[
            "customer_penalty_pressure",
            "inventory_cover_days",
            "substitution_flexibility",
            "supplier_concentration",
            "transport_reliability",
        ],
        expected_root_strategy="Reserve logistics",
    )


def test_run_replay_suite_reports_accuracy_and_field_coverage(tmp_path: Path) -> None:
    result = run_replay_suite(
        [
            _replay_case(),
            _market_replay_case(),
            _regulatory_replay_case(),
            _election_replay_case(),
            _supply_replay_case(),
        ],
        workspace_root=tmp_path,
    )

    assert isinstance(result, ReplaySuiteResult)
    assert result.case_count == 5
    assert result.top_branch_accuracy == 1.0
    assert result.root_strategy_accuracy == 1.0
    assert result.evidence_source_accuracy == 1.0
    assert result.average_inferred_field_coverage == 1.0
    assert isinstance(result.results[0], ReplayCaseResult)
    assert result.results[0].top_branch == "Stakeholder reset"
    assert {case.run_id for case in result.results} == {
        "apple-transition",
        "election-debate-collapse",
        "market-rate-shock",
        "regulator-adtech",
        "supplier-flooding",
    }
    assert result.domain_breakdown["election-shock"]["count"] == 1
    assert result.domain_breakdown["supply-chain-disruption"]["root_strategy_accuracy"] == 1.0


def test_calibration_summary_surfaces_attention_items_for_missed_cases(tmp_path: Path) -> None:
    case = _replay_case().model_copy(
        update={
            "expected_top_branch": "Contain message",
            "expected_root_strategy": "Contain message",
            "expected_evidence_sources": ["apple-succession"],
            "expected_inferred_fields": ["board_cohesion", "brand_sentiment", "missing_field"],
        }
    )

    result = run_replay_suite([case], workspace_root=tmp_path)
    summary = summarize_calibration(result, attention_threshold=0.99)

    assert isinstance(summary, CalibrationSummary)
    assert len(summary.attention_items) == 1
    attention = summary.attention_items[0]
    assert attention.run_id == "apple-transition"
    assert set(attention.mismatch_types) == {
        "top_branch_mismatch",
        "root_strategy_mismatch",
        "evidence_source_mismatch",
        "inferred_field_gap",
    }
    assert attention.missing_inferred_fields == ["missing_field"]
    assert summary.failure_type_counts["top_branch_mismatch"] == 1
    assert summary.domains_needing_attention == ["company-action"]


def test_run_replay_suite_command_outputs_structured_metrics(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run-replay-suite",
            "--replay-case-json",
            _replay_case().model_dump_json(),
            "--replay-case-json",
            _market_replay_case().model_dump_json(),
            "--replay-case-json",
            _regulatory_replay_case().model_dump_json(),
            "--replay-case-json",
            _election_replay_case().model_dump_json(),
            "--replay-case-json",
            _supply_replay_case().model_dump_json(),
        ],
    )

    assert result.exit_code == 0
    payload = ReplaySuiteResult.model_validate_json(result.stdout)
    assert payload.case_count == 5
    assert payload.root_strategy_accuracy == 1.0
    assert {case.expected_top_branch for case in payload.results} == {
        "Stakeholder reset",
        "Emergency liquidity",
        "Internal remediation",
        "Message reset (reset holds)",
        "Reserve logistics",
    }


def test_run_replay_suite_command_rejects_input_file() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("replay-suite.json").write_text(json.dumps([_replay_case().model_dump(mode="json")]), encoding="utf-8")
        result = runner.invoke(app, ["run-replay-suite", "--input", "replay-suite.json"])

    assert result.exit_code != 0


def test_run_replay_suite_command_accepts_replay_case_json(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "run-replay-suite",
            "--replay-case-json",
            _replay_case().model_dump_json(),
            "--replay-case-json",
            _market_replay_case().model_dump_json(),
        ],
    )

    assert result.exit_code == 0
    payload = ReplaySuiteResult.model_validate_json(result.stdout)
    assert payload.case_count == 2
    assert payload.top_branch_accuracy == 1.0
    assert payload.root_strategy_accuracy == 1.0


def test_summarize_replay_calibration_command_rejects_input_file() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("replay-suite.json").write_text(json.dumps([_replay_case().model_dump(mode="json")]), encoding="utf-8")
        result = runner.invoke(app, ["summarize-replay-calibration", "--input", "replay-suite.json"])

    assert result.exit_code != 0


def test_summarize_replay_calibration_command_accepts_replay_case_json(tmp_path: Path) -> None:
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "summarize-replay-calibration",
            "--replay-case-json",
            _replay_case().model_dump_json(),
            "--replay-case-json",
            _market_replay_case().model_dump_json(),
        ],
    )

    assert result.exit_code == 0
    payload = CalibrationSummary.model_validate_json(result.stdout)
    assert payload.case_count == 2
    assert payload.domains_needing_attention == []


def test_builtin_interstate_replay_case_pins_actor_preference_differentiation() -> None:
    cases = load_builtin_replay_cases()

    case = next(case for case in cases if case.run_id == "philippines-china-shoal")

    assert case.domain_pack == "interstate-crisis"
    assert case.expected_top_branch == "Signal resolve (managed signal)"
    assert case.expected_root_strategy == "Signal resolve"
    assert sorted(case.expected_evidence_sources) == [
        "beijing-hotline",
        "shoal-water-cannon",
    ]
    assert sorted(case.expected_inferred_fields) == [
        "alliance_pressure",
        "diplomatic_channel",
        "geographic_flashpoint",
        "leader_style",
        "mediation_window",
        "military_posture",
        "tension_index",
    ]


def test_builtin_interstate_replay_case_exercises_actor_preferences_and_run_lens(tmp_path: Path) -> None:
    case = next(case for case in load_builtin_replay_cases() if case.run_id == "philippines-china-shoal")
    registry = build_default_registry()
    pack = registry.resolve(case.domain_pack)
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()

    service = WorkflowService(
        RunRepository(tmp_path / ".forecast"),
        corpus_registry=CorpusRegistry(tmp_path / "corpus.db"),
        domain_registry=registry,
    )
    service.start_run(case.run_id, case.domain_pack)
    service.save_intake_draft(case.run_id, "r1", case.intake)
    for filename, content in case.documents.items():
        (docs_dir / filename).write_text(content, encoding="utf-8")

    service.batch_ingest_recommended_files(case.run_id, "r1", pack=pack, path=docs_dir, max_files=len(case.documents))
    service.draft_evidence_packet(case.run_id, "r1", pack=pack)
    packet = service.draft_approval_packet(case.run_id, "r1")

    assert packet.actor_preferences
    assert packet.recommended_run_lens["name"] == "domestic-politics-first"
    assert packet.recommended_run_lens["aggregation_mode"] == "focal-actor"
    assert packet.recommended_run_lens["focal_actor_id"] == "united-states"
    assert {item["actor_id"] for item in packet.actor_preferences} >= {"china", "united-states"}

    replay_result = run_replay_suite([case], workspace_root=tmp_path / "suite")

    assert replay_result.case_count == 1
    assert replay_result.top_branch_accuracy == 1.0
    assert replay_result.root_strategy_accuracy == 1.0
    assert replay_result.results[0].top_branch == "Signal resolve (managed signal)"
