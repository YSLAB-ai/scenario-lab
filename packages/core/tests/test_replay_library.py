from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.cli import app
from forecasting_harness.replay import CalibrationSummary, ReplaySuiteResult, run_replay_suite, summarize_calibration
from forecasting_harness.knowledge import (
    list_builtin_replay_cases,
    load_builtin_replay_cases,
    summarize_builtin_replay_corpus,
)


def test_builtin_replay_library_covers_repo_owned_domains() -> None:
    cases = load_builtin_replay_cases()
    corpus = summarize_builtin_replay_corpus()
    catalog = list_builtin_replay_cases()

    assert len(cases) == 22
    assert {case.domain_pack for case in cases} == {
        "company-action",
        "election-shock",
        "interstate-crisis",
        "market-shock",
        "pandemic-response",
        "regulatory-enforcement",
        "supply-chain-disruption",
    }
    assert len({case.run_id for case in cases}) == 22
    assert corpus.case_count == 22
    assert corpus.anchored_case_count == 10
    assert corpus.domain_counts["interstate-crisis"] == 4
    assert corpus.domain_counts["company-action"] == 4
    assert corpus.domain_counts["election-shock"] == 2
    assert corpus.domain_counts["market-shock"] == 3
    assert corpus.domain_counts["pandemic-response"] == 3
    assert corpus.domain_counts["regulatory-enforcement"] == 3
    assert len(corpus.files) == 7
    assert corpus.files["interstate-crisis.json"] == 4
    assert corpus.files["company-action.json"] == 4
    assert corpus.files["election-shock.json"] == 2
    assert corpus.files["market-shock.json"] == 3
    assert corpus.files["pandemic-response.json"] == 3
    assert corpus.files["regulatory-enforcement.json"] == 3
    assert any(item.run_id == "svb-btfp-2023" and item.source_count == 2 for item in catalog)
    assert any(item.run_id == "taiwan-drills-2022" and item.time_anchor == "2022-08" for item in catalog)
    assert any(item.run_id == "south-africa-gnu-2024" and item.source_count == 2 for item in catalog)
    assert any(item.run_id == "uk-gilt-intervention-2022" and item.source_count == 2 for item in catalog)
    assert any(item.run_id == "td-bank-aml-2024" and item.source_count == 2 for item in catalog)
    assert any(item.run_id == "boeing-max9-2024" and item.source_count == 2 for item in catalog)


def test_builtin_replay_suite_and_calibration_summary_are_structured(tmp_path: Path) -> None:
    result = run_replay_suite(load_builtin_replay_cases(), workspace_root=tmp_path)
    summary = summarize_calibration(result)

    assert isinstance(result, ReplaySuiteResult)
    assert result.case_count == 22
    assert isinstance(summary, CalibrationSummary)
    assert summary.case_count == 22
    assert summary.overall_root_strategy_accuracy == 1.0
    assert summary.domains_needing_attention == []
    assert summary.attention_items == []
    assert summary.failure_type_counts == {}
    assert summary.historically_anchored_case_count == 10
    assert summary.domain_breakdown["interstate-crisis"]["count"] == 4
    assert summary.domain_breakdown["company-action"]["count"] == 4
    assert summary.domain_breakdown["election-shock"]["count"] == 2
    assert summary.domain_breakdown["market-shock"]["count"] == 3
    assert summary.domain_breakdown["pandemic-response"]["count"] == 3
    assert summary.domain_breakdown["regulatory-enforcement"]["count"] == 3


def test_builtin_replay_cli_commands_emit_structured_payloads(tmp_path: Path) -> None:
    runner = CliRunner()

    replay_result = runner.invoke(app, ["run-builtin-replay-suite"])
    assert replay_result.exit_code == 0
    replay_payload = ReplaySuiteResult.model_validate_json(replay_result.stdout)
    assert replay_payload.case_count == 22

    summary_result = runner.invoke(app, ["summarize-replay-calibration"])
    assert summary_result.exit_code == 0
    summary_payload = CalibrationSummary.model_validate_json(summary_result.stdout)
    assert summary_payload.case_count == 22
    assert summary_payload.domains_needing_attention == []
    assert summary_payload.historically_anchored_case_count == 10
    assert summary_payload.failure_type_counts == {}

    corpus_result = runner.invoke(app, ["summarize-builtin-replay-corpus"])
    assert corpus_result.exit_code == 0
    corpus_payload = json.loads(corpus_result.stdout)
    assert corpus_payload["case_count"] == 22
    assert corpus_payload["anchored_case_count"] == 10
    assert corpus_payload["domain_counts"]["supply-chain-disruption"] == 3
    assert corpus_payload["domain_counts"]["pandemic-response"] == 3
    assert corpus_payload["domain_counts"]["election-shock"] == 2
    assert corpus_payload["domain_counts"]["market-shock"] == 3
    assert corpus_payload["domain_counts"]["regulatory-enforcement"] == 3
    assert corpus_payload["domain_counts"]["company-action"] == 4

    case_list_result = runner.invoke(app, ["list-builtin-replay-cases"])
    assert case_list_result.exit_code == 0
    case_list_payload = json.loads(case_list_result.stdout)
    assert len(case_list_payload) == 22
    assert any(item["run_id"] == "binance-settlement-2023" and item["source_count"] == 2 for item in case_list_payload)
