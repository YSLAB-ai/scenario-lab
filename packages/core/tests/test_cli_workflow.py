import json
import zipfile
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.cli import app
from forecasting_harness.retrieval import CorpusRegistry, RetrievalQuery, SearchEngine
from forecasting_harness.workflow.models import AssumptionSummary, EvidencePacket, IntakeDraft


def _write_minimal_xlsx(path: Path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
""",
        )
        archive.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="/xl/workbook.xml"/>
</Relationships>
""",
        )
        archive.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Signals" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
""",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="/xl/worksheets/sheet1.xml"/>
</Relationships>
""",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" t="inlineStr"><is><t>Overview</t></is></c>
      <c r="B1" t="inlineStr"><is><t>Taiwan Strait warning</t></is></c>
    </row>
  </sheetData>
</worksheet>
""",
        )


def test_list_domain_packs() -> None:
    result = CliRunner().invoke(app, ["list-domain-packs"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == [
        "company-action",
        "election-shock",
        "generic-event",
        "interstate-crisis",
        "market-shock",
        "pandemic-response",
        "regulatory-enforcement",
        "supply-chain-disruption",
    ]


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
    simulation_payload = json.loads(simulation_result.stdout)
    assert simulation_payload["iterations"] == 10000

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
    report = (run_dir / "reports" / "r1.report.md").read_text(encoding="utf-8")
    assert "- Unsupported assumptions: 1" in report
    assert "## Actor Utility Summary" in report
    assert "## Aggregation Lens" in report


def test_simulate_command_accepts_iteration_override(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    intake_path = tmp_path / "intake.json"
    evidence_path = tmp_path / "evidence.json"
    assumptions_path = tmp_path / "assumptions.json"

    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "focus_entities": ["US", "Iran"],
                "current_development": "Exchange of strikes",
                "current_stage": "trigger",
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
    assumptions_path.write_text(json.dumps({"summary": ["Both sides avoid immediate total war"]}), encoding="utf-8")

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-evidence-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(evidence_path)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["approve-revision", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(assumptions_path)],
    ).exit_code == 0

    simulation_result = runner.invoke(
        app,
        ["simulate", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--iterations", "250"],
    )

    assert simulation_result.exit_code == 0
    simulation_payload = json.loads(simulation_result.stdout)
    assert simulation_payload["iterations"] == 250

def test_draft_evidence_packet_command(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    corpus_db = tmp_path / "corpus.db"
    intake_path = tmp_path / "intake.json"

    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "focus_entities": ["Japan", "China"],
                "current_development": "Naval transit through the Taiwan Strait",
                "current_stage": "trigger",
                "time_horizon": "30d",
            }
        ),
        encoding="utf-8",
    )

    from forecasting_harness.retrieval import CorpusRegistry

    corpus = CorpusRegistry(corpus_db)
    corpus.register_document(
        source_id="doc-1",
        title="Taiwan Strait Signals",
        source_type="markdown",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis"},
        content="Japan and China exchange warnings in the Taiwan Strait.",
    )

    assert runner.invoke(
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
    ).exit_code == 0
    assert runner.invoke(
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
    ).exit_code == 0

    result = runner.invoke(
        app,
        [
            "draft-evidence-packet",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--query-text",
            "Taiwan Strait warnings",
        ],
    )

    assert result.exit_code == 0
    assert [item["source_id"] for item in json.loads(result.stdout)["items"]] == ["doc-1"]


def test_draft_evidence_packet_command_can_omit_query_text(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    corpus_db = tmp_path / "corpus.db"
    intake_path = tmp_path / "intake.json"

    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "focus_entities": ["Japan", "China"],
                "current_development": "Naval transit through the Taiwan Strait",
                "current_stage": "trigger",
                "time_horizon": "30d",
            }
        ),
        encoding="utf-8",
    )

    from forecasting_harness.retrieval import CorpusRegistry

    corpus = CorpusRegistry(corpus_db)
    corpus.register_document(
        source_id="doc-1",
        title="Posture shift",
        source_type="markdown",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis"},
        content="Force posture hardens near the strait after the naval transit.",
    )

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0

    result = runner.invoke(
        app,
        [
            "draft-evidence-packet",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
        ],
    )

    assert result.exit_code == 0
    assert [item["source_id"] for item in json.loads(result.stdout)["items"]] == ["doc-1"]


def test_draft_retrieval_plan_command(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    intake_path = tmp_path / "intake.json"
    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "focus_entities": ["Japan", "China"],
                "current_development": "Naval transit through the Taiwan Strait",
                "current_stage": "trigger",
                "time_horizon": "30d",
            }
        ),
        encoding="utf-8",
    )

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0

    result = runner.invoke(
        app,
        ["draft-retrieval-plan", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["domain_pack"] == "interstate-crisis"
    assert "force posture" in payload["target_evidence_categories"]
    assert "Japan China Naval transit through the Taiwan Strait force posture" in payload["query_variants"]


def test_draft_ingestion_plan_command(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    corpus_db = tmp_path / "corpus.db"
    intake_path = tmp_path / "intake.json"
    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "focus_entities": ["Japan", "China"],
                "current_development": "Naval transit through the Taiwan Strait",
                "current_stage": "trigger",
                "time_horizon": "30d",
            }
        ),
        encoding="utf-8",
    )

    from forecasting_harness.retrieval import CorpusRegistry

    corpus = CorpusRegistry(corpus_db)
    corpus.register_document(
        source_id="doc-1",
        title="Posture shift",
        source_type="markdown",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis"},
        content="Japan and China harden force posture near the Taiwan Strait after the naval transit.",
    )

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0

    result = runner.invoke(
        app,
        [
            "draft-ingestion-plan",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["domain_pack"] == "interstate-crisis"
    assert payload["corpus_source_count"] == 1
    assert "diplomatic signaling" in payload["missing_evidence_categories"]


def test_recommend_ingestion_files_command(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    corpus_db = tmp_path / "corpus.db"
    intake_path = tmp_path / "intake.json"
    source_dir = tmp_path / "incoming"
    source_dir.mkdir()
    (source_dir / "official-warning.md").write_text(
        "# Foreign Ministry\nOfficial statement and warning to the other state.\n",
        encoding="utf-8",
    )
    (source_dir / "deployment-notes.md").write_text(
        "# Deployment\nForce posture and readiness changed near the theater.\n",
        encoding="utf-8",
    )
    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "focus_entities": ["Japan", "China"],
                "current_development": "Naval transit through the Taiwan Strait",
                "current_stage": "trigger",
                "time_horizon": "30d",
            }
        ),
        encoding="utf-8",
    )

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0

    result = runner.invoke(
        app,
        [
            "recommend-ingestion-files",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--path",
            str(source_dir),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    by_source_id = {item["source_id"]: item for item in payload}
    assert by_source_id["official-warning"]["source_role"] == "official communications"
    assert by_source_id["official-warning"]["recommended_tags"]["domain"] == "interstate-crisis"
    assert "diplomatic signaling" in by_source_id["official-warning"]["matched_evidence_categories"]


def test_batch_ingest_recommended_command(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    corpus_db = tmp_path / "corpus.db"
    intake_path = tmp_path / "intake.json"
    source_dir = tmp_path / "incoming"
    source_dir.mkdir()
    (source_dir / "official-warning.md").write_text(
        "# Foreign Ministry\nOfficial statement and warning to the other state.\n",
        encoding="utf-8",
    )
    (source_dir / "deployment-notes.md").write_text(
        "# Deployment\nForce posture and readiness changed near the theater.\n",
        encoding="utf-8",
    )
    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "focus_entities": ["Japan", "China"],
                "current_development": "Naval transit through the Taiwan Strait",
                "current_stage": "trigger",
                "time_horizon": "30d",
            }
        ),
        encoding="utf-8",
    )

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0

    result = runner.invoke(
        app,
        [
            "batch-ingest-recommended",
            "--root",
            str(root),
            "--corpus-db",
            str(corpus_db),
            "--path",
            str(source_dir),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--max-files",
            "2",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ingested_count"] == 2
    assert set(payload["ingested_source_ids"]) == {"official-warning", "deployment-notes"}

    documents = CorpusRegistry(corpus_db).list_documents()
    assert documents[0]["tags"]["source_role"] == "force and capability references"
    assert documents[1]["tags"]["source_role"] == "official communications"


def test_draft_intake_guidance_command_returns_pack_guidance(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    intake_path = tmp_path / "intake.json"
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

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0

    result = runner.invoke(
        app,
        ["draft-intake-guidance", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["domain_pack"] == "interstate-crisis"
    assert "China" in payload["suggested_entities"]


def test_save_intake_draft_command_accepts_direct_flags(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0

    result = runner.invoke(
        app,
        [
            "save-intake-draft",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--event-framing",
            "Assess escalation risk",
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
            "--known-unknown",
            "US response posture",
            "--suggested-entity",
            "United States",
            "--pack-field",
            "leader_style=hawkish",
        ],
    )

    assert result.exit_code == 0
    intake = RunRepository(root).load_revision_model("crisis-1", "intake", "r1", IntakeDraft, approved=False)
    assert intake.focus_entities == ["Japan", "China"]
    assert intake.pack_fields == {"leader_style": "hawkish"}


def test_draft_approval_packet_command_returns_grouped_summary(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    intake_path = tmp_path / "intake.json"
    evidence_path = tmp_path / "evidence.json"
    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "primary_actors": ["US", "Iran"],
                "trigger": "Exchange of strikes",
                "current_phase": "trigger",
                "time_horizon": "30d",
                "known_unknowns": ["US response posture"],
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
                        "raw_passages": ["Alpha"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-evidence-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(evidence_path)],
    ).exit_code == 0

    result = runner.invoke(
        app,
        ["draft-approval-packet", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["revision_id"] == "r1"
    assert "warnings" in payload
    assert "actor_preferences" in payload
    assert "recommended_run_lens" in payload
    assert payload["evidence_summary"][0]["source_id"] == "doc-1"


def test_approve_revision_command_accepts_direct_flags(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    intake_path = tmp_path / "intake.json"
    evidence_path = tmp_path / "evidence.json"
    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "focus_entities": ["Japan", "China"],
                "current_development": "Naval transit through the Taiwan Strait",
                "current_stage": "trigger",
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

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-evidence-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(evidence_path)],
    ).exit_code == 0

    result = runner.invoke(
        app,
        [
            "approve-revision",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--assumption",
            "Both sides prefer limited signaling",
            "--suggested-actor",
            "United States",
            "--objective-profile-name",
            "balanced",
        ],
    )

    assert result.exit_code == 0
    approved = RunRepository(root).load_revision_model("crisis-1", "assumptions", "r1", AssumptionSummary, approved=True)
    assert approved.summary == ["Both sides prefer limited signaling"]
    assert approved.suggested_actors == ["United States"]
    assert approved.objective_profile_name == "balanced-system"


def test_approve_revision_command_leaves_objective_profile_unset_when_flag_omitted(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    intake_path = tmp_path / "intake.json"
    evidence_path = tmp_path / "evidence.json"
    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "focus_entities": ["Japan", "China"],
                "current_development": "Naval transit through the Taiwan Strait",
                "current_stage": "trigger",
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

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-evidence-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(evidence_path)],
    ).exit_code == 0

    result = runner.invoke(
        app,
        [
            "approve-revision",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--assumption",
            "Both sides prefer limited signaling",
        ],
    )

    assert result.exit_code == 0
    approved = RunRepository(root).load_revision_model("crisis-1", "assumptions", "r1", AssumptionSummary, approved=True)
    assert approved.summary == ["Both sides prefer limited signaling"]
    assert approved.objective_profile_name == ""


def test_approve_revision_command_rejects_invalid_objective_profile_flag(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    intake_path = tmp_path / "intake.json"
    evidence_path = tmp_path / "evidence.json"
    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "focus_entities": ["Japan", "China"],
                "current_development": "Naval transit through the Taiwan Strait",
                "current_stage": "trigger",
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

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-evidence-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(evidence_path)],
    ).exit_code == 0

    result = runner.invoke(
        app,
        [
            "approve-revision",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--objective-profile-name",
            "typo-lens",
        ],
    )

    assert result.exit_code != 0
    assert "unknown objective profile:" in result.output
    assert "typo-lens" in result.output
    assert not (root / "runs" / "crisis-1" / "assumptions" / "r1.approved.json").exists()


def test_summarize_run_and_revision_commands_return_narrow_json(tmp_path: Path) -> None:
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
            {"revision_id": "r1", "items": [{"evidence_id": "r1-ev-1", "source_id": "doc-1", "source_title": "Doc 1", "reason": "Relevant context"}]},
        ),
        encoding="utf-8",
    )
    assumptions_path.write_text(json.dumps({"summary": ["Both sides avoid immediate total war"]}), encoding="utf-8")

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-evidence-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(evidence_path)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["approve-revision", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(assumptions_path)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["simulate", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1"],
    ).exit_code == 0

    run_result = runner.invoke(app, ["summarize-run", "--root", str(root), "--run-id", "crisis-1"])
    revision_result = runner.invoke(
        app,
        ["summarize-revision", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1"],
    )

    assert run_result.exit_code == 0
    assert revision_result.exit_code == 0
    run_payload = json.loads(run_result.stdout)
    revision_payload = json.loads(revision_result.stdout)
    assert run_payload["current_revision_id"] == "r1"
    assert revision_payload["revision_id"] == "r1"
    assert revision_payload["top_branches"]
    assert revision_payload["scenario_families"]


def test_draft_conversation_turn_command_returns_report_stage_for_simulated_revision(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    intake_path = tmp_path / "intake.json"
    evidence_path = tmp_path / "evidence.json"
    assumptions_path = tmp_path / "assumptions.json"
    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "focus_entities": ["Japan", "China"],
                "current_development": "Naval transit through the Taiwan Strait",
                "current_stage": "trigger",
                "time_horizon": "30d",
            }
        ),
        encoding="utf-8",
    )
    evidence_path.write_text(
        json.dumps(
            {"revision_id": "r1", "items": [{"evidence_id": "r1-ev-1", "source_id": "doc-1", "source_title": "Doc 1", "reason": "Relevant context"}]},
        ),
        encoding="utf-8",
    )
    assumptions_path.write_text(json.dumps({"summary": ["Maintain limited signaling"]}), encoding="utf-8")

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-evidence-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(evidence_path)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["approve-revision", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(assumptions_path)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["simulate", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1"],
    ).exit_code == 0

    result = runner.invoke(
        app,
        ["draft-conversation-turn", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["stage"] == "report"
    assert payload["recommended_command"] == "forecast-harness begin-revision-update"
    assert payload["context"]["revision_id"] == "r1"


def test_draft_conversation_turn_command_embeds_native_adapter_payloads(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    corpus_db = tmp_path / "corpus.db"
    intake_path = tmp_path / "intake.json"
    source_dir = tmp_path / "incoming"
    source_dir.mkdir()
    (source_dir / "official-warning.md").write_text(
        "# Foreign Ministry\nOfficial statement and warning to the other state.\n",
        encoding="utf-8",
    )
    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "focus_entities": ["Japan", "China"],
                "current_development": "Naval transit through the Taiwan Strait",
                "current_stage": "trigger",
                "time_horizon": "30d",
            }
        ),
        encoding="utf-8",
    )

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0

    result = runner.invoke(
        app,
        [
            "draft-conversation-turn",
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
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["stage"] == "evidence"
    assert payload["recommended_command"] == "forecast-harness batch-ingest-recommended"
    assert payload["actions"][0]["command"] == "forecast-harness batch-ingest-recommended"
    assert payload["context"]["intake_guidance"]["domain_pack"] == "interstate-crisis"
    assert payload["context"]["ingestion_recommendations"][0]["source_role"] == "official communications"


def test_curate_evidence_draft_command_filters_existing_packet(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    evidence_path = tmp_path / "evidence.json"
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
                    },
                    {
                        "evidence_id": "r1-ev-2",
                        "source_id": "doc-2",
                        "source_title": "Doc 2",
                        "reason": "Follow-up context",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-evidence-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(evidence_path)],
    ).exit_code == 0

    result = runner.invoke(
        app,
        [
            "curate-evidence-draft",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--keep-evidence-id",
            "r1-ev-2",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert [item["evidence_id"] for item in payload["items"]] == ["r1-ev-2"]
    stored = RunRepository(root).load_revision_model("crisis-1", "evidence", "r1", EvidencePacket, approved=False)
    assert [item.evidence_id for item in stored.items] == ["r1-ev-2"]


def test_save_evidence_draft_command_accepts_inline_item_json(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0

    result = runner.invoke(
        app,
        [
            "save-evidence-draft",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--revision-id",
            "r1",
            "--item-json",
            json.dumps(
                {
                    "evidence_id": "r1-ev-1",
                    "source_id": "doc-1",
                    "source_title": "Doc 1",
                    "reason": "Relevant context",
                    "raw_passages": ["A directly supplied passage."],
                }
            ),
        ],
    )

    assert result.exit_code == 0
    stored = RunRepository(root).load_revision_model("crisis-1", "evidence", "r1", EvidencePacket, approved=False)
    assert stored.revision_id == "r1"
    assert [item.evidence_id for item in stored.items] == ["r1-ev-1"]
    assert stored.items[0].raw_passages == ["A directly supplied passage."]


def test_run_adapter_action_save_evidence_draft_accepts_inline_item_json(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"

    assert runner.invoke(
        app,
        ["run-adapter-action", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--action", "start-run", "--domain-pack", "interstate-crisis"],
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
            "Naval transit through the Taiwan Strait",
            "--current-stage",
            "trigger",
            "--time-horizon",
            "30d",
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
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["executed_action"] == "save-evidence-draft"
    assert payload["turn"]["stage"] == "approval"
    stored = RunRepository(root).load_revision_model("crisis-1", "evidence", "r1", EvidencePacket, approved=False)
    assert [item.evidence_id for item in stored.items] == ["r1-ev-1"]


def test_begin_revision_update_command_copies_parent_artifacts(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    intake_path = tmp_path / "intake.json"
    evidence_path = tmp_path / "evidence.json"
    assumptions_path = tmp_path / "assumptions.json"
    intake_path.write_text(
        json.dumps(
            {
                "event_framing": "Assess escalation",
                "focus_entities": ["Japan", "China"],
                "current_development": "Naval transit through the Taiwan Strait",
                "current_stage": "trigger",
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
    assumptions_path.write_text(json.dumps({"summary": ["Maintain limited signaling"]}), encoding="utf-8")

    assert runner.invoke(
        app,
        ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["save-evidence-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(evidence_path)],
    ).exit_code == 0
    assert runner.invoke(
        app,
        ["approve-revision", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(assumptions_path)],
    ).exit_code == 0

    result = runner.invoke(
        app,
        [
            "begin-revision-update",
            "--root",
            str(root),
            "--run-id",
            "crisis-1",
            "--parent-revision-id",
            "r1",
            "--revision-id",
            "r2",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["revision_id"] == "r2"
    assert payload["parent_revision_id"] == "r1"
    copied_intake = RunRepository(root).load_revision_model("crisis-1", "intake", "r2", IntakeDraft, approved=False)
    copied_evidence = RunRepository(root).load_revision_model("crisis-1", "evidence", "r2", EvidencePacket, approved=False)
    assert copied_intake.focus_entities == ["Japan", "China"]
    assert copied_evidence.revision_id == "r2"


def test_ingest_file_command_registers_a_searchable_source(tmp_path: Path) -> None:
    source = tmp_path / "signals.md"
    source.write_text("# Overview\nJapan issues a warning.\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "ingest-file",
            "--corpus-db",
            str(tmp_path / "corpus.db"),
            "--path",
            str(source),
            "--tag",
            "domain=interstate-crisis",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["source_type"] == "markdown"
    assert payload["chunk_count"] == 1

    hits = SearchEngine(CorpusRegistry(tmp_path / "corpus.db")).search(
        RetrievalQuery(text="Japan warning", filters={"domain": "interstate-crisis"})
    )
    assert [hit["source_id"] for hit in hits] == [payload["source_id"]]


def test_ingest_file_command_registers_xlsx_sources(tmp_path: Path) -> None:
    source = tmp_path / "signals.xlsx"
    _write_minimal_xlsx(source)

    result = CliRunner().invoke(
        app,
        [
            "ingest-file",
            "--corpus-db",
            str(tmp_path / "corpus.db"),
            "--path",
            str(source),
            "--tag",
            "domain=interstate-crisis",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["source_type"] == "spreadsheet"
    assert payload["chunk_count"] == 1

    hits = SearchEngine(CorpusRegistry(tmp_path / "corpus.db")).search(
        RetrievalQuery(text="Taiwan Strait warning", filters={"domain": "interstate-crisis"})
    )
    assert [hit["source_id"] for hit in hits] == [payload["source_id"]]


def test_ingest_directory_command_reports_ingested_and_skipped_files(tmp_path: Path) -> None:
    corpus_db = tmp_path / "corpus.db"
    source_dir = tmp_path / "corpus"
    source_dir.mkdir()
    (source_dir / "signals.md").write_text("# Overview\nWarning.\n", encoding="utf-8")
    (source_dir / "saved.html").write_text(
        "<html><head><title>Saved Page</title></head><body><h1>Overview</h1><p>Warning.</p></body></html>",
        encoding="utf-8",
    )
    _write_minimal_xlsx(source_dir / "signals.xlsx")
    (source_dir / "ignore.zip").write_text("not supported", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "ingest-directory",
            "--corpus-db",
            str(corpus_db),
            "--path",
            str(source_dir),
            "--tag",
            "domain=interstate-crisis",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ingested"] == 3
    assert payload["skipped"] == 1


def test_list_corpus_sources_command_lists_documents(tmp_path: Path) -> None:
    corpus_db = tmp_path / "corpus.db"
    registry = CorpusRegistry(corpus_db)
    registry.register_document(
        source_id="doc-1",
        title="Signals",
        source_type="markdown",
        path="/tmp/signals.md",
        published_at=None,
        tags={"domain": "interstate-crisis"},
        chunks=[{"chunk_id": "1", "location": "heading:Overview", "content": "Alpha"}],
    )

    result = CliRunner().invoke(
        app,
        [
            "list-corpus-sources",
            "--corpus-db",
            str(corpus_db),
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)[0]["source_id"] == "doc-1"
