from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.cli import app
from forecasting_harness.replay import CalibrationSummary, ReplaySuiteResult, run_replay_suite, summarize_calibration
from forecasting_harness.knowledge import load_builtin_replay_cases


def test_builtin_replay_library_covers_repo_owned_domains() -> None:
    cases = load_builtin_replay_cases()

    assert len(cases) == 10
    assert {case.domain_pack for case in cases} == {
        "company-action",
        "election-shock",
        "interstate-crisis",
        "market-shock",
        "regulatory-enforcement",
        "supply-chain-disruption",
    }
    assert len({case.run_id for case in cases}) == 10


def test_builtin_replay_suite_and_calibration_summary_are_structured(tmp_path: Path) -> None:
    result = run_replay_suite(load_builtin_replay_cases(), workspace_root=tmp_path)
    summary = summarize_calibration(result)

    assert isinstance(result, ReplaySuiteResult)
    assert result.case_count == 10
    assert isinstance(summary, CalibrationSummary)
    assert summary.case_count == 10
    assert summary.overall_root_strategy_accuracy == 1.0
    assert summary.domains_needing_attention == []
    assert summary.domain_breakdown["interstate-crisis"]["count"] == 3
    assert summary.domain_breakdown["company-action"]["count"] == 2


def test_builtin_replay_cli_commands_emit_structured_payloads(tmp_path: Path) -> None:
    runner = CliRunner()

    replay_result = runner.invoke(app, ["run-builtin-replay-suite"])
    assert replay_result.exit_code == 0
    replay_payload = ReplaySuiteResult.model_validate_json(replay_result.stdout)
    assert replay_payload.case_count == 10

    summary_result = runner.invoke(app, ["summarize-replay-calibration"])
    assert summary_result.exit_code == 0
    summary_payload = CalibrationSummary.model_validate_json(summary_result.stdout)
    assert summary_payload.case_count == 10
    assert summary_payload.domains_needing_attention == []
