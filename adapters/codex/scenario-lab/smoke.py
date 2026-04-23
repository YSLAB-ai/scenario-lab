from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.cli import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the packaged Scenario Lab Codex smoke flow.")
    parser.add_argument("--work-dir")
    args = parser.parse_args()

    work_dir = Path(args.work_dir) if args.work_dir else Path(tempfile.mkdtemp(prefix="scenario-lab-codex-smoke-"))
    root = work_dir / ".forecast"
    corpus_db = work_dir / "corpus.db"
    source_dir = work_dir / "incoming"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "official-warning.md").write_text(
        "# Foreign Ministry\nOfficial statement and warning to the other state.\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    actions = [
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "adapter-1",
            "--revision-id",
            "r1",
            "--action",
            "start-run",
            "--domain-pack",
            "interstate-crisis",
        ],
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--candidate-path",
            str(source_dir),
            "--run-id",
            "adapter-1",
            "--revision-id",
            "r1",
            "--action",
            "save-intake-draft",
            "--event-framing",
            "Assess escalation",
            "--focus-entity",
            "Japan",
            "--focus-entity",
            "China",
            "--current-development",
            "Naval transit through the Taiwan Strait",
            "--current-stage",
            "trigger",
            "--time-horizon",
            "30d",
        ],
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--candidate-path",
            str(source_dir),
            "--run-id",
            "adapter-1",
            "--revision-id",
            "r1",
            "--action",
            "batch-ingest-recommended",
        ],
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--run-id",
            "adapter-1",
            "--revision-id",
            "r1",
            "--action",
            "draft-evidence-packet",
        ],
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "adapter-1",
            "--revision-id",
            "r1",
            "--action",
            "approve-revision",
            "--assumption",
            "Maintain limited signaling",
        ],
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "adapter-1",
            "--revision-id",
            "r1",
            "--action",
            "simulate",
            "--iterations",
            "100",
        ],
    ]

    stage_history: list[str] = []
    runtime_actions: list[str | None] = []
    for command in actions:
        result = runner.invoke(app, command)
        if result.exit_code != 0:
            raise SystemExit(result.output)
        payload = json.loads(result.stdout)
        stage_history.append(payload["turn"]["stage"])
        runtime_actions.append(payload["turn"].get("recommended_runtime_action"))

    run_summary = runner.invoke(app, ["summarize-run", "--root", str(root), "--run-id", "adapter-1"])
    revision_summary = runner.invoke(app, ["summarize-revision", "--root", str(root), "--run-id", "adapter-1", "--revision-id", "r1"])
    report_result = runner.invoke(app, ["generate-report", "--root", str(root), "--run-id", "adapter-1", "--revision-id", "r1"])
    report_path = root / "runs" / "adapter-1" / "reports" / "r1.report.md"
    if run_summary.exit_code != 0 or revision_summary.exit_code != 0 or report_result.exit_code != 0:
        raise SystemExit("summary commands failed")

    print(
        json.dumps(
            {
                "adapter": "codex",
                "stages": stage_history,
                "recommended_runtime_actions": runtime_actions,
                "run_summary": json.loads(run_summary.stdout),
                "revision_summary": json.loads(revision_summary.stdout),
                "report_result": report_result.stdout.strip(),
                "report_exists": report_path.exists(),
            }
        )
    )


if __name__ == "__main__":
    main()
