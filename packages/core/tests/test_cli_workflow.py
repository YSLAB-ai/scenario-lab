from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.cli import app


def test_demo_run_creates_report_and_workbench(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["demo-run", "--root", str(tmp_path / ".forecast")])

    assert result.exit_code == 0
    run_dir = tmp_path / ".forecast" / "runs" / "demo-run"
    assert (run_dir / "report.md").exists()
    assert (run_dir / "workbench.md").exists()
