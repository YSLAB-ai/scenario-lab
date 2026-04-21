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
        expected_inferred_fields=["brand_sentiment", "cash_runway_months", "regulatory_pressure"],
    )


def test_run_replay_suite_reports_accuracy_and_field_coverage(tmp_path: Path) -> None:
    result = run_replay_suite([_replay_case()], workspace_root=tmp_path)

    assert isinstance(result, ReplaySuiteResult)
    assert result.case_count == 1
    assert result.top_branch_accuracy == 1.0
    assert result.evidence_source_accuracy == 1.0
    assert result.average_inferred_field_coverage == 1.0
    assert isinstance(result.results[0], ReplayCaseResult)
    assert result.results[0].top_branch == "Stakeholder reset"


def test_run_replay_suite_command_outputs_structured_metrics(tmp_path: Path) -> None:
    runner = CliRunner()
    replay_path = tmp_path / "replay-suite.json"
    replay_path.write_text(json.dumps([_replay_case().model_dump(mode="json")]), encoding="utf-8")

    result = runner.invoke(
        app,
        ["run-replay-suite", "--input", str(replay_path)],
    )

    assert result.exit_code == 0
    payload = ReplaySuiteResult.model_validate_json(result.stdout)
    assert payload.case_count == 1
    assert payload.results[0].expected_top_branch == "Stakeholder reset"
