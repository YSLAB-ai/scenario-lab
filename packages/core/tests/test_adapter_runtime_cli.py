import json
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.cli import app


def test_run_adapter_action_executes_the_normal_adapter_loop(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    corpus_db = tmp_path / "corpus.db"
    source_dir = tmp_path / "incoming"
    source_dir.mkdir()
    (source_dir / "official-warning.md").write_text(
        "# Foreign Ministry\nOfficial statement and warning to the other state.\n",
        encoding="utf-8",
    )

    start_result = runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "start-run",
            "--domain-pack",
            "interstate-crisis",
        ],
    )

    assert start_result.exit_code == 0
    start_payload = json.loads(start_result.stdout)
    assert start_payload["turn"]["stage"] == "intake"
    assert start_payload["turn"]["recommended_runtime_action"] == "save-intake-draft"

    intake_result = runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--candidate-path",
            str(source_dir),
            "--run-id",
            "crisis-1",
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
    )

    assert intake_result.exit_code == 0
    intake_payload = json.loads(intake_result.stdout)
    assert intake_payload["turn"]["stage"] == "evidence"
    assert intake_payload["turn"]["recommended_runtime_action"] == "batch-ingest-recommended"

    ingest_result = runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--candidate-path",
            str(source_dir),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "batch-ingest-recommended",
        ],
    )

    assert ingest_result.exit_code == 0
    ingest_payload = json.loads(ingest_result.stdout)
    assert ingest_payload["action_result"]["ingested_count"] == 1
    assert ingest_payload["turn"]["stage"] == "evidence"
    assert ingest_payload["turn"]["recommended_runtime_action"] == "draft-evidence-packet"

    evidence_result = runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "draft-evidence-packet",
        ],
    )

    assert evidence_result.exit_code == 0
    evidence_payload = json.loads(evidence_result.stdout)
    assert evidence_payload["turn"]["stage"] == "approval"
    assert evidence_payload["turn"]["recommended_runtime_action"] == "approve-revision"

    approval_result = runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "approve-revision",
            "--assumption",
            "Maintain limited signaling",
        ],
    )

    assert approval_result.exit_code == 0
    approval_payload = json.loads(approval_result.stdout)
    assert approval_payload["turn"]["stage"] == "simulation"
    assert approval_payload["turn"]["recommended_runtime_action"] == "simulate"

    simulation_result = runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "simulate",
            "--iterations",
            "100",
        ],
    )

    assert simulation_result.exit_code == 0
    simulation_payload = json.loads(simulation_result.stdout)
    assert simulation_payload["action_result"]["iterations"] == 100
    assert simulation_payload["turn"]["stage"] == "report"
    assert simulation_payload["turn"]["recommended_runtime_action"] == "begin-revision-update"


def test_run_adapter_action_simulate_defaults_to_cli_iteration_budget(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"

    assert runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "start-run",
            "--domain-pack",
            "interstate-crisis",
        ],
    ).exit_code == 0
    assert runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
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
            "Official warning and deployment activity around the Taiwan Strait",
            "--current-stage",
            "trigger",
            "--time-horizon",
            "30d",
        ],
    ).exit_code == 0
    assert runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "save-evidence-draft",
            "--item-json",
            json.dumps(
                {
                    "evidence_id": "r1-ev-1",
                    "source_id": "doc-1",
                    "source_title": "Doc 1",
                    "reason": "Relevant context",
                }
            ),
        ],
    ).exit_code == 0
    assert runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "approve-revision",
            "--assumption",
            "Maintain limited signaling",
        ],
    ).exit_code == 0

    result = runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "simulate",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["action_result"]["iterations"] == 10000


def test_run_adapter_action_batch_ingests_generic_local_brief_and_drafts_evidence(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    corpus_db = tmp_path / "corpus.db"
    source_dir = tmp_path / "incoming"
    source_dir.mkdir()
    (source_dir / "china-taiwan-brief.md").write_text(
        "# China-Taiwan local brief\n\n"
        "Cross-strait signaling has intensified around the Taiwan Strait after a political trigger. "
        "Regional actors emphasize restraint while military activity increases.\n",
        encoding="utf-8",
    )

    assert runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "start-run",
            "--domain-pack",
            "interstate-crisis",
        ],
    ).exit_code == 0

    intake_result = runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--candidate-path",
            str(source_dir),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "save-intake-draft",
            "--event-framing",
            "Assess escalation",
            "--focus-entity",
            "China",
            "--focus-entity",
            "Taiwan",
            "--current-development",
            "Cross-strait signaling intensifies around the Taiwan Strait after a political trigger.",
            "--current-stage",
            "trigger",
            "--time-horizon",
            "30d",
        ],
    )

    assert intake_result.exit_code == 0
    intake_payload = json.loads(intake_result.stdout)
    assert intake_payload["turn"]["recommended_runtime_action"] == "batch-ingest-recommended"

    ingest_result = runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--candidate-path",
            str(source_dir),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "batch-ingest-recommended",
        ],
    )

    assert ingest_result.exit_code == 0
    ingest_payload = json.loads(ingest_result.stdout)
    assert ingest_payload["action_result"]["ingested_count"] == 1
    assert ingest_payload["turn"]["recommended_runtime_action"] == "draft-evidence-packet"

    evidence_result = runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "draft-evidence-packet",
        ],
    )

    assert evidence_result.exit_code == 0
    evidence_payload = json.loads(evidence_result.stdout)
    assert evidence_payload["action_result"]["items"]
    assert evidence_payload["turn"]["stage"] == "approval"


def test_run_adapter_action_can_start_a_child_revision_from_a_report_stage(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    corpus_db = tmp_path / "corpus.db"
    source = tmp_path / "signals.md"
    source.write_text("# Overview\nJapan issues a warning and opens a backchannel.\n", encoding="utf-8")

    assert runner.invoke(
        app,
        [
            "ingest-file",
            "--corpus-db",
            str(corpus_db),
            "--path",
            str(source),
            "--tag",
            "domain=interstate-crisis",
        ],
    ).exit_code == 0
    assert runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "start-run",
            "--domain-pack",
            "interstate-crisis",
        ],
    ).exit_code == 0
    assert runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--run-id",
            "crisis-1",
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
    ).exit_code == 0
    assert runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "draft-evidence-packet",
        ],
    ).exit_code == 0
    assert runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "approve-revision",
            "--assumption",
            "Maintain limited signaling",
        ],
    ).exit_code == 0
    assert runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--action",
            "simulate",
            "--iterations",
            "100",
        ],
    ).exit_code == 0

    update_result = runner.invoke(
        app,
        [
            "run-adapter-action",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r2",
            "--parent-revision-id",
            "r1",
            "--action",
            "begin-revision-update",
        ],
    )

    assert update_result.exit_code == 0
    update_payload = json.loads(update_result.stdout)
    assert update_payload["action_result"]["parent_revision_id"] == "r1"
    assert update_payload["action_result"]["copied_sections"] == ["intake", "evidence", "assumptions"]
    assert update_payload["turn"]["revision_id"] == "r2"
    assert update_payload["turn"]["stage"] == "simulation"
    assert update_payload["turn"]["recommended_runtime_action"] == "simulate"


def test_scenario_command_bootstraps_a_real_workflow_turn(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"

    first_result = runner.invoke(
        app,
        [
            "scenario",
            "--root",
            str(root),
            "--run-id",
            "us-iran-1",
            "--revision-id",
            "r1",
            "--domain-pack",
            "interstate-crisis",
            "/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days",
        ],
    )

    assert first_result.exit_code == 0
    payload = json.loads(first_result.stdout)
    assert payload["command"] == "scenario"
    assert payload["prompt"].startswith("/scenario ")
    assert payload["intake"]["focus_entities"] == ["US", "Iran"]
    assert payload["turn"]["stage"] == "evidence"
    assert payload["turn"]["recommended_runtime_action"] in {
        "batch-ingest-recommended",
        "draft-evidence-packet",
    }
    assert payload["intake"]["current_stage"] == "trigger"

    second_result = runner.invoke(
        app,
        [
            "scenario",
            "--root",
            str(root),
            "--run-id",
            "us-iran-1",
            "--domain-pack",
            "interstate-crisis",
            "/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days",
        ],
    )

    assert second_result.exit_code == 0
    second_payload = json.loads(second_result.stdout)
    assert second_payload["command"] == "scenario"
    assert second_payload["turn"]["stage"] == "evidence"
    assert second_payload["turn"]["recommended_runtime_action"] in {
        "batch-ingest-recommended",
        "draft-evidence-packet",
    }
