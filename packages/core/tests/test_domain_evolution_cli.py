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

