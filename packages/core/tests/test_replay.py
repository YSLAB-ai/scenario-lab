from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.cli import app
from forecasting_harness.replay import ReplayCase, ReplayCaseResult, ReplaySuiteResult, run_replay_suite
from forecasting_harness.workflow.models import AssumptionSummary, IntakeDraft


def _replay_case() -> ReplayCase:
    return ReplayCase(
        run_id="apple-transition",
        domain_pack="company-action",
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
    )


def test_run_replay_suite_reports_accuracy_and_field_coverage(tmp_path: Path) -> None:
    result = run_replay_suite([_replay_case(), _market_replay_case(), _regulatory_replay_case()], workspace_root=tmp_path)

    assert isinstance(result, ReplaySuiteResult)
    assert result.case_count == 3
    assert result.top_branch_accuracy == 1.0
    assert result.evidence_source_accuracy == 1.0
    assert result.average_inferred_field_coverage == 1.0
    assert isinstance(result.results[0], ReplayCaseResult)
    assert result.results[0].top_branch == "Stakeholder reset"
    assert {case.run_id for case in result.results} == {"apple-transition", "market-rate-shock", "regulator-adtech"}


def test_run_replay_suite_command_outputs_structured_metrics(tmp_path: Path) -> None:
    runner = CliRunner()
    replay_path = tmp_path / "replay-suite.json"
    replay_path.write_text(
        json.dumps(
            [
                _replay_case().model_dump(mode="json"),
                _market_replay_case().model_dump(mode="json"),
                _regulatory_replay_case().model_dump(mode="json"),
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["run-replay-suite", "--input", str(replay_path)],
    )

    assert result.exit_code == 0
    payload = ReplaySuiteResult.model_validate_json(result.stdout)
    assert payload.case_count == 3
    assert {case.expected_top_branch for case in payload.results} == {
        "Stakeholder reset",
        "Emergency liquidity",
        "Internal remediation",
    }
