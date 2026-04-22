from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.cli import app


def test_record_domain_suggestion_command(tmp_path: Path) -> None:
    manifest_root = tmp_path / "knowledge" / "domains"
    manifest_root.mkdir(parents=True)
    (manifest_root / "company-action.json").write_text(
        json.dumps({"slug": "company-action", "description": "test manifest"}),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        [
            "record-domain-suggestion",
            "--workspace-root",
            str(tmp_path),
            "--domain-pack",
            "company-action",
            "--text",
            "Board reassurance should favor containment messaging.",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "pending"
    assert payload["domain_slug"] == "company-action"


def test_run_domain_evolution_writes_summary(tmp_path: Path) -> None:
    manifest_root = tmp_path / "knowledge" / "domains"
    manifest_root.mkdir(parents=True)
    (manifest_root / "company-action.json").write_text(
        json.dumps({"slug": "company-action", "description": "test manifest"}),
        encoding="utf-8",
    )

    runner = CliRunner()
    runner.invoke(
        app,
        [
            "record-domain-suggestion",
            "--workspace-root",
            str(tmp_path),
            "--domain-pack",
            "company-action",
            "--target",
            "contain-message",
            "--category",
            "action-bias",
            "--text",
            "Board reassurance should favor containment messaging.",
            "--term",
            "board reassurance",
        ],
    )

    result = runner.invoke(
        app,
        [
            "run-domain-evolution",
            "--workspace-root",
            str(tmp_path),
            "--domain-pack",
            "company-action",
            "--no-branch",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["promotion_decision"] in {"promoted", "rejected"}
    assert payload["domain_slug"] == "company-action"


def test_run_replay_retuning_command_reports_structured_summary(tmp_path: Path) -> None:
    manifest_root = tmp_path / "knowledge" / "domains"
    manifest_root.mkdir(parents=True)
    (manifest_root / "company-action.json").write_text(
        json.dumps({"slug": "company-action", "description": "test manifest"}),
        encoding="utf-8",
    )
    replay_path = tmp_path / "retune-cases.json"
    replay_path.write_text(
        json.dumps(
            [
                {
                    "run_id": "openai-governance-retune",
                    "domain_pack": "company-action",
                    "intake": {
                        "event_framing": "Assess OpenAI strategy after a board-driven leadership crisis.",
                        "focus_entities": ["OpenAI"],
                        "current_development": "OpenAI faces leadership turnover, governance questions, and partner pressure.",
                        "current_stage": "trigger",
                        "time_horizon": "120d",
                        "suggested_entities": ["Board", "Enterprise Customers"],
                    },
                    "assumptions": {
                        "summary": ["The company will prioritize stakeholder reassurance."],
                        "suggested_actors": ["Board", "Enterprise Customers"],
                    },
                    "documents": {
                        "leadership-transition.md": "OpenAI leadership turnover created partner pressure and governance concern.",
                        "board-reset.md": "Board reset and stakeholder reassurance dominate the next strategic move."
                    },
                    "expected_top_branch": "Nonexistent branch",
                    "expected_root_strategy": "Nonexistent strategy"
                }
            ]
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        [
            "run-replay-retuning",
            "--workspace-root",
            str(tmp_path),
            "--domain-pack",
            "company-action",
            "--input",
            str(replay_path),
            "--no-branch",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["domain_slug"] == "company-action"
    assert payload["case_count"] == 1
    assert payload["weak_case_count"] == 1
    assert payload["generated_suggestion_count"] >= 1
    assert payload["evolution_summary"]["promotion_decision"] == "promoted"


def test_run_builtin_replay_retuning_command_reports_multi_domain_summary(tmp_path: Path) -> None:
    manifest_root = tmp_path / "knowledge" / "domains"
    manifest_root.mkdir(parents=True)
    for slug in ("market-shock", "regulatory-enforcement"):
        (manifest_root / f"{slug}.json").write_text(
            json.dumps({"slug": slug, "description": "test manifest"}),
            encoding="utf-8",
        )

    result = CliRunner().invoke(
        app,
        [
            "run-builtin-replay-retuning",
            "--workspace-root",
            str(tmp_path),
            "--domain-pack",
            "market-shock",
            "--domain-pack",
            "regulatory-enforcement",
            "--no-branch",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["domain_count"] == 2
    assert payload["case_count"] == 6
    assert payload["weak_domain_count"] == 0
    assert payload["domains"] == ["market-shock", "regulatory-enforcement"]
    assert payload["generated_suggestion_count"] == 0
    assert set(payload["per_domain"]) == {"market-shock", "regulatory-enforcement"}
