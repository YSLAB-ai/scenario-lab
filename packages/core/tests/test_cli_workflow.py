import json
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.cli import app


def test_demo_run_creates_report_and_workbench(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["demo-run", "--root", str(tmp_path / ".forecast")])

    assert result.exit_code == 0
    run_dir = tmp_path / ".forecast" / "runs" / "demo-run"
    assert (run_dir / "belief-state.json").exists()
    assert (run_dir / "tree-summary.json").exists()
    assert (run_dir / "report.md").exists()
    assert (run_dir / "workbench.md").exists()

    tree_summary = json.loads((run_dir / "tree-summary.json").read_text(encoding="utf-8"))
    top_branch_label = tree_summary["branches"][0]["label"]
    assert top_branch_label in (run_dir / "report.md").read_text(encoding="utf-8")
    assert "Objective profile: balanced" in (run_dir / "workbench.md").read_text(encoding="utf-8")


def test_start_run_and_simulate_interstate_workflow(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"

    result = runner.invoke(
        app,
        [
            "start-run",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--domain-pack",
            "interstate-crisis",
        ],
    )
    assert result.exit_code == 0

    result = runner.invoke(
        app,
        [
            "simulate",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
        ],
    )
    assert result.exit_code == 0

    run_dir = root / "runs" / "crisis-1"
    assert (run_dir / "belief-state.json").exists()
    assert (run_dir / "tree-summary.json").exists()
    assert (run_dir / "report.md").exists()
