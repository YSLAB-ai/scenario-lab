import json
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.cli import app


def test_list_domain_packs() -> None:
    result = CliRunner().invoke(app, ["list-domain-packs"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == ["generic-event", "interstate-crisis"]


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
    assert RunRepository(tmp_path / ".forecast").load_run_record("demo-run").domain_pack == "generic-event"


def test_demo_run_can_refresh_existing_root(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"

    first = runner.invoke(app, ["demo-run", "--root", str(root)])
    first_run = RunRepository(root).load_run_record("demo-run")
    first_events = (root / "runs" / "demo-run" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    second = runner.invoke(app, ["demo-run", "--root", str(root)])
    second_run = RunRepository(root).load_run_record("demo-run")
    second_events = (root / "runs" / "demo-run" / "events.jsonl").read_text(encoding="utf-8").splitlines()

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert second_run.domain_pack == "generic-event"
    assert second_run.created_at == first_run.created_at
    assert len(first_events) == 1
    assert second_events == first_events


def test_demo_run_repairs_missing_run_record_in_existing_directory(tmp_path: Path) -> None:
    root = tmp_path / ".forecast"
    run_dir = root / "runs" / "demo-run"
    run_dir.mkdir(parents=True)

    result = CliRunner().invoke(app, ["demo-run", "--root", str(root)])

    assert result.exit_code == 0
    assert RunRepository(root).load_run_record("demo-run").domain_pack == "generic-event"
    assert len((run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_start_run_and_simulate_interstate_workflow(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    intake_path = tmp_path / "intake.json"
    evidence_path = tmp_path / "evidence.json"
    assumptions_path = tmp_path / "assumptions.json"

    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "primary_actors": ["US", "Iran"],
                "trigger": "Exchange of strikes",
                "current_phase": "trigger",
                "time_horizon": "30d",
            }
        ),
        encoding="utf-8",
    )
    evidence_path.write_text(
        json.dumps(
            {
                "revision_id": "r1",
                "items": [
                    {
                        "evidence_id": "r1-ev-1",
                        "source_id": "doc-1",
                        "source_title": "Doc 1",
                        "reason": "Relevant context",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assumptions_path.write_text(
        json.dumps({"summary": ["Both sides avoid immediate total war"]}),
        encoding="utf-8",
    )

    start_result = runner.invoke(
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
    assert start_result.exit_code == 0

    intake_result = runner.invoke(
        app,
        [
            "save-intake-draft",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--input",
            str(intake_path),
        ],
    )
    assert intake_result.exit_code == 0

    evidence_result = runner.invoke(
        app,
        [
            "save-evidence-draft",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--input",
            str(evidence_path),
        ],
    )
    assert evidence_result.exit_code == 0

    approval_result = runner.invoke(
        app,
        [
            "approve-revision",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--input",
            str(assumptions_path),
        ],
    )
    assert approval_result.exit_code == 0

    simulation_result = runner.invoke(
        app,
        [
            "simulate",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
        ],
    )
    assert simulation_result.exit_code == 0

    report_result = runner.invoke(
        app,
        [
            "generate-report",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
        ],
    )
    assert report_result.exit_code == 0

    run_dir = root / "runs" / "crisis-1"
    assert (run_dir / "belief-state" / "r1.approved.json").exists()
    assert (run_dir / "simulation" / "r1.approved.json").exists()
    assert (run_dir / "reports" / "r1.report.md").exists()
    assert "- Unsupported assumptions: 1" in (run_dir / "reports" / "r1.report.md").read_text(encoding="utf-8")
