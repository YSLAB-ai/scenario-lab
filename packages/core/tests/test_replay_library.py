from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.cli import app
from forecasting_harness.replay import CalibrationSummary, ReplaySuiteResult, run_replay_suite, summarize_calibration
from forecasting_harness.knowledge import load_builtin_replay_cases, summarize_builtin_replay_corpus


def test_builtin_replay_library_covers_repo_owned_domains() -> None:
    cases = load_builtin_replay_cases()
    corpus = summarize_builtin_replay_corpus()

    assert len(cases) == 12
    assert {case.domain_pack for case in cases} == {
        "company-action",
        "election-shock",
        "interstate-crisis",
        "market-shock",
        "pandemic-response",
        "regulatory-enforcement",
        "supply-chain-disruption",
    }
    assert len({case.run_id for case in cases}) == 12
    assert corpus.case_count == 12
    assert corpus.domain_counts["interstate-crisis"] == 3
    assert corpus.domain_counts["company-action"] == 2
    assert corpus.domain_counts["pandemic-response"] == 2
    assert len(corpus.files) == 7
    assert corpus.files["interstate-crisis.json"] == 3
    assert corpus.files["pandemic-response.json"] == 2


def test_builtin_replay_suite_and_calibration_summary_are_structured(tmp_path: Path) -> None:
    result = run_replay_suite(load_builtin_replay_cases(), workspace_root=tmp_path)
    summary = summarize_calibration(result)

    assert isinstance(result, ReplaySuiteResult)
    assert result.case_count == 12
    assert isinstance(summary, CalibrationSummary)
    assert summary.case_count == 12
    assert summary.overall_root_strategy_accuracy == 1.0
    assert summary.domains_needing_attention == []
    assert summary.domain_breakdown["interstate-crisis"]["count"] == 3
    assert summary.domain_breakdown["company-action"]["count"] == 2
    assert summary.domain_breakdown["pandemic-response"]["count"] == 2


def test_builtin_replay_cli_commands_emit_structured_payloads(tmp_path: Path) -> None:
    runner = CliRunner()

    replay_result = runner.invoke(app, ["run-builtin-replay-suite"])
    assert replay_result.exit_code == 0
    replay_payload = ReplaySuiteResult.model_validate_json(replay_result.stdout)
    assert replay_payload.case_count == 12

    summary_result = runner.invoke(app, ["summarize-replay-calibration"])
    assert summary_result.exit_code == 0
    summary_payload = CalibrationSummary.model_validate_json(summary_result.stdout)
    assert summary_payload.case_count == 12
    assert summary_payload.domains_needing_attention == []

    corpus_result = runner.invoke(app, ["summarize-builtin-replay-corpus"])
    assert corpus_result.exit_code == 0
    corpus_payload = json.loads(corpus_result.stdout)
    assert corpus_payload["case_count"] == 12
    assert corpus_payload["domain_counts"]["supply-chain-disruption"] == 2
    assert corpus_payload["domain_counts"]["pandemic-response"] == 2
