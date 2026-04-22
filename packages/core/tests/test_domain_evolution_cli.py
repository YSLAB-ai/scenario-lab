from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.cli import app
from forecasting_harness.domain.company_action import CompanyActionPack
from forecasting_harness.replay import ReplayCase
from forecasting_harness.artifacts import RunRepository
from forecasting_harness.workflow.service import WorkflowService
from forecasting_harness.workflow.models import EvidencePacket, EvidencePacketItem
from forecasting_harness.workflow.models import AssumptionSummary, IntakeDraft


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
    case = ReplayCase(
        run_id="openai-governance-retune",
        domain_pack="company-action",
        intake=IntakeDraft(
            event_framing="Assess OpenAI strategy after a board-driven leadership crisis.",
            focus_entities=["OpenAI"],
            current_development="OpenAI faces leadership turnover, governance questions, and partner pressure.",
            current_stage="trigger",
            time_horizon="120d",
            suggested_entities=["Board", "Enterprise Customers"],
        ),
        assumptions=AssumptionSummary(
            summary=["The company will prioritize stakeholder reassurance."],
            suggested_actors=["Board", "Enterprise Customers"],
        ),
        documents={
            "leadership-transition.md": "OpenAI leadership turnover created partner pressure and governance concern.",
            "board-reset.md": "Board reset and stakeholder reassurance dominate the next strategic move.",
        },
        expected_top_branch="Nonexistent branch",
        expected_root_strategy="Nonexistent strategy",
    )

    result = CliRunner().invoke(
        app,
        [
            "run-replay-retuning",
            "--workspace-root",
            str(tmp_path),
            "--domain-pack",
            "company-action",
            "--replay-case-json",
            case.model_dump_json(),
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


def test_run_replay_retuning_command_rejects_input_file() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("retune-cases.json").write_text(
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
                            "board-reset.md": "Board reset and stakeholder reassurance dominate the next strategic move.",
                        },
                        "expected_top_branch": "Nonexistent branch",
                        "expected_root_strategy": "Nonexistent strategy",
                    }
                ]
            ),
            encoding="utf-8",
        )
        result = runner.invoke(
            app,
            [
                "run-replay-retuning",
                "--workspace-root",
                ".",
                "--domain-pack",
                "company-action",
                "--input",
                "retune-cases.json",
            ],
        )

    assert result.exit_code != 0


def test_run_replay_retuning_command_accepts_replay_case_json(tmp_path: Path) -> None:
    manifest_root = tmp_path / "knowledge" / "domains"
    manifest_root.mkdir(parents=True)
    (manifest_root / "company-action.json").write_text(
        json.dumps({"slug": "company-action", "description": "test manifest"}),
        encoding="utf-8",
    )

    case = ReplayCase(
        run_id="openai-governance-retune",
        domain_pack="company-action",
        intake=IntakeDraft(
            event_framing="Assess OpenAI strategy after a board-driven leadership crisis.",
            focus_entities=["OpenAI"],
            current_development="OpenAI faces leadership turnover, governance questions, and partner pressure.",
            current_stage="trigger",
            time_horizon="120d",
            suggested_entities=["Board", "Enterprise Customers"],
        ),
        assumptions=AssumptionSummary(
            summary=["The company will prioritize stakeholder reassurance."],
            suggested_actors=["Board", "Enterprise Customers"],
        ),
        documents={
            "leadership-transition.md": "OpenAI leadership turnover created partner pressure and governance concern.",
            "board-reset.md": "Board reset and stakeholder reassurance dominate the next strategic move.",
        },
        expected_top_branch="Nonexistent branch",
        expected_root_strategy="Nonexistent strategy",
    )

    result = CliRunner().invoke(
        app,
        [
            "run-replay-retuning",
            "--workspace-root",
            str(tmp_path),
            "--domain-pack",
            "company-action",
            "--replay-case-json",
            case.model_dump_json(),
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


def test_compile_revision_knowledge_command_records_idempotent_compiler_candidates(tmp_path: Path) -> None:
    root = tmp_path / ".forecast"
    pack = CompanyActionPack()
    service = WorkflowService(RunRepository(root))
    service.start_run("company-case", pack.slug())
    service.save_intake_draft(
        "company-case",
        "r1",
        IntakeDraft(
            event_framing="Assess company strategy after a CEO transition and liquidity stress.",
            focus_entities=["Acme"],
            current_development="A board-led leadership transition coincides with liquidity stress and customer concern.",
            current_stage="trigger",
            time_horizon="90d",
            suggested_entities=["Board"],
        ),
    )
    service.save_evidence_draft(
        "company-case",
        "r1",
        EvidencePacket(
            revision_id="r1",
            items=[
                EvidencePacketItem(
                    evidence_id="r1:liquidity:1",
                    source_id="liquidity",
                    source_title="Liquidity buffer plan",
                    reason="Candidate passage for approved evidence packet: financial resilience",
                    raw_passages=[
                        "Management outlines a liquidity buffer and cash preservation plan while the board stabilizes the transition."
                    ],
                )
            ],
        ),
    )
    service.approve_revision(
        "company-case",
        "r1",
        AssumptionSummary(summary=["The board wants stability first"], suggested_actors=["Board"]),
    )

    runner = CliRunner()
    first = runner.invoke(
        app,
        [
            "compile-revision-knowledge",
            "--workspace-root",
            str(tmp_path),
            "--root",
            str(root),
            "--run-id",
            "company-case",
            "--revision-id",
            "r1",
        ],
    )
    second = runner.invoke(
        app,
        [
            "compile-revision-knowledge",
            "--workspace-root",
            str(tmp_path),
            "--root",
            str(root),
            "--run-id",
            "company-case",
            "--revision-id",
            "r1",
        ],
    )

    assert first.exit_code == 0
    assert second.exit_code == 0
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert first_payload["domain_slug"] == "company-action"
    assert first_payload["candidate_count"] >= 1
    assert first_payload["recorded_count"] >= 1
    assert second_payload["candidate_count"] == first_payload["candidate_count"]
    assert second_payload["recorded_count"] == 0


def test_compile_replay_knowledge_command_records_structured_candidates(tmp_path: Path) -> None:
    manifest_root = tmp_path / "knowledge" / "domains"
    manifest_root.mkdir(parents=True)
    (manifest_root / "company-action.json").write_text(
        json.dumps({"slug": "company-action", "description": "test manifest", "key_state_fields": ["board_cohesion"]}),
        encoding="utf-8",
    )
    case = ReplayCase(
        run_id="openai-governance-retune",
        domain_pack="company-action",
        case_title="OpenAI governance shock",
        intake=IntakeDraft(
            event_framing="Assess OpenAI strategy after a board-driven leadership crisis.",
            focus_entities=["OpenAI"],
            current_development="OpenAI faces leadership turnover, governance questions, and partner pressure.",
            current_stage="trigger",
            time_horizon="120d",
            suggested_entities=["Board", "Enterprise Customers"],
        ),
        assumptions=AssumptionSummary(
            summary=["The company will prioritize stakeholder reassurance."],
            suggested_actors=["Board", "Enterprise Customers"],
        ),
        documents={
            "leadership-transition.md": "OpenAI leadership turnover created partner pressure and governance concern.",
            "board-reset.md": "Board reset and stakeholder reassurance dominate the next strategic move.",
        },
        expected_top_branch="Nonexistent branch",
        expected_root_strategy="Contain message",
        expected_inferred_fields=["board_cohesion"],
    )

    runner = CliRunner()
    first = runner.invoke(
        app,
        [
            "compile-replay-knowledge",
            "--workspace-root",
            str(tmp_path),
            "--domain-pack",
            "company-action",
            "--replay-case-json",
            case.model_dump_json(),
        ],
    )
    second = runner.invoke(
        app,
        [
            "compile-replay-knowledge",
            "--workspace-root",
            str(tmp_path),
            "--domain-pack",
            "company-action",
            "--replay-case-json",
            case.model_dump_json(),
        ],
    )

    assert first.exit_code == 0
    assert second.exit_code == 0
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert first_payload["source_kind"] == "replay-miss"
    assert first_payload["candidate_count"] >= 1
    assert first_payload["recorded_count"] >= 1
    assert second_payload["recorded_count"] == 0


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
    assert payload["case_count"] == 11
    assert payload["weak_domain_count"] == 0
    assert payload["domains"] == ["market-shock", "regulatory-enforcement"]
    assert payload["generated_suggestion_count"] == 0
    assert set(payload["per_domain"]) == {"market-shock", "regulatory-enforcement"}
