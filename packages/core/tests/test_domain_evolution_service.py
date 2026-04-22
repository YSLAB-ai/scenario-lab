from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from forecasting_harness.evolution.models import DomainSuggestion
from forecasting_harness.evolution.service import DomainEvolutionService
from forecasting_harness.evolution.storage import EvolutionStorage
from forecasting_harness.evolution.models import DomainEvolutionCandidate
from forecasting_harness.replay import ReplayCaseResult, ReplaySuiteResult


def test_analyze_domain_weakness_returns_brief_for_missed_cases(tmp_path: Path) -> None:
    storage = EvolutionStorage(tmp_path / "knowledge" / "evolution")
    service = DomainEvolutionService(
        evolution_storage=storage,
        manifest_root=tmp_path / "knowledge" / "domains",
    )
    replay_result = ReplaySuiteResult(
        case_count=1,
        top_branch_accuracy=0.0,
        root_strategy_accuracy=0.0,
        evidence_source_accuracy=1.0,
        average_inferred_field_coverage=1.0,
        domain_breakdown={
            "company-action": {
                "count": 1,
                "top_branch_accuracy": 0.0,
                "root_strategy_accuracy": 0.0,
                "evidence_source_accuracy": 1.0,
                "average_inferred_field_coverage": 1.0,
            }
        },
        results=[
            ReplayCaseResult(
                run_id="boeing-post-reporting",
                domain_pack="company-action",
                top_branch="Stakeholder reset",
                expected_top_branch="Contain message (message lands)",
                top_branch_match=False,
                root_strategy="Stakeholder reset",
                expected_root_strategy="Contain message",
                root_strategy_match=False,
                evidence_sources=["boeing-reporting"],
                expected_evidence_sources=["boeing-reporting"],
                evidence_source_match=True,
                inferred_fields=["board_cohesion"],
                expected_inferred_fields=["board_cohesion"],
                inferred_field_coverage=1.0,
                node_count=12,
                transposition_hits=2,
            )
        ],
    )

    brief = service.analyze_domain_weakness("company-action", replay_result=replay_result)

    assert brief.domain_slug == "company-action"
    assert brief.reasons
    stored = storage.load_suggestions("company-action")
    assert stored == []


def test_analyze_domain_weakness_includes_evidence_and_field_gaps(tmp_path: Path) -> None:
    storage = EvolutionStorage(tmp_path / "knowledge" / "evolution")
    service = DomainEvolutionService(
        evolution_storage=storage,
        manifest_root=tmp_path / "knowledge" / "domains",
    )
    replay_result = ReplaySuiteResult(
        case_count=1,
        top_branch_accuracy=1.0,
        root_strategy_accuracy=1.0,
        evidence_source_accuracy=0.0,
        average_inferred_field_coverage=0.5,
        domain_breakdown={
            "company-action": {
                "count": 1,
                "top_branch_accuracy": 1.0,
                "root_strategy_accuracy": 1.0,
                "evidence_source_accuracy": 0.0,
                "average_inferred_field_coverage": 0.5,
            }
        },
        results=[
            ReplayCaseResult(
                run_id="openai-governance-gap",
                domain_pack="company-action",
                top_branch="Contain message",
                expected_top_branch="Contain message",
                top_branch_match=True,
                root_strategy="Contain message",
                expected_root_strategy="Contain message",
                root_strategy_match=True,
                evidence_sources=["wrong-source"],
                expected_evidence_sources=["board-reset"],
                evidence_source_match=False,
                inferred_fields=["board_cohesion"],
                expected_inferred_fields=["board_cohesion", "brand_sentiment"],
                inferred_field_coverage=0.5,
                node_count=10,
                transposition_hits=1,
            )
        ],
    )

    brief = service.analyze_domain_weakness("company-action", replay_result=replay_result)

    assert brief.domain_slug == "company-action"
    assert brief.weak_cases == ["openai-governance-gap"]
    assert any("evidence" in reason for reason in brief.reasons)
    assert any("inferred" in reason for reason in brief.reasons)


def test_compile_replay_knowledge_is_idempotent_for_compiler_replay_suggestions(tmp_path: Path) -> None:
    manifest_root = tmp_path / "knowledge" / "domains"
    manifest_root.mkdir(parents=True)
    (manifest_root / "company-action.json").write_text(
        json.dumps({"slug": "company-action", "description": "test manifest", "key_state_fields": ["board_cohesion"]}),
        encoding="utf-8",
    )
    storage = EvolutionStorage(tmp_path / "knowledge" / "evolution")
    service = DomainEvolutionService(
        evolution_storage=storage,
        manifest_root=manifest_root,
    )
    replay_result = ReplaySuiteResult(
        case_count=1,
        top_branch_accuracy=0.0,
        root_strategy_accuracy=0.0,
        evidence_source_accuracy=1.0,
        average_inferred_field_coverage=1.0,
        domain_breakdown={
            "company-action": {
                "count": 1,
                "top_branch_accuracy": 0.0,
                "root_strategy_accuracy": 0.0,
                "evidence_source_accuracy": 1.0,
                "average_inferred_field_coverage": 1.0,
            }
        },
        results=[
            ReplayCaseResult(
                run_id="boeing-post-reporting",
                domain_pack="company-action",
                top_branch="Stakeholder reset",
                expected_top_branch="Contain message (message lands)",
                top_branch_match=False,
                root_strategy="Stakeholder reset",
                expected_root_strategy="Contain message",
                root_strategy_match=False,
                evidence_sources=["boeing-reporting"],
                expected_evidence_sources=["boeing-reporting"],
                evidence_source_match=True,
                inferred_fields=["board_cohesion"],
                expected_inferred_fields=["board_cohesion"],
                inferred_field_coverage=1.0,
                node_count=12,
                transposition_hits=2,
            )
        ],
    )

    service.compile_replay_knowledge("company-action", replay_result=replay_result)
    service.compile_replay_knowledge("company-action", replay_result=replay_result)

    stored = storage.load_suggestions("company-action")
    assert len(stored) >= 1
    assert len({item.suggestion_id for item in stored}) == len(stored)
    assert all(item.provenance == "compiler" for item in stored)


def test_run_replay_retuning_returns_structured_summary_for_missed_case(tmp_path: Path) -> None:
    manifest_root = tmp_path / "knowledge" / "domains"
    manifest_root.mkdir(parents=True)
    (manifest_root / "company-action.json").write_text(
        json.dumps({"slug": "company-action", "description": "test manifest"}),
        encoding="utf-8",
    )
    storage = EvolutionStorage(tmp_path / "knowledge" / "evolution")
    service = DomainEvolutionService(
        evolution_storage=storage,
        manifest_root=manifest_root,
    )
    replay_cases = [
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

    summary = service.run_replay_retuning(
        "company-action",
        replay_cases=replay_cases,
        create_branch=False,
    )

    assert summary["domain_slug"] == "company-action"
    assert summary["case_count"] == 1
    assert summary["weak_case_count"] == 1
    assert summary["generated_suggestion_count"] >= 1
    assert summary["evolution_summary"]["promotion_decision"] == "promoted"


def test_run_replay_retuning_rejects_mixed_domain_payload(tmp_path: Path) -> None:
    manifest_root = tmp_path / "knowledge" / "domains"
    manifest_root.mkdir(parents=True)
    (manifest_root / "company-action.json").write_text(
        json.dumps({"slug": "company-action", "description": "test manifest"}),
        encoding="utf-8",
    )
    storage = EvolutionStorage(tmp_path / "knowledge" / "evolution")
    service = DomainEvolutionService(
        evolution_storage=storage,
        manifest_root=manifest_root,
    )

    replay_cases = [
        {
            "run_id": "openai-governance-retune",
            "domain_pack": "company-action",
            "intake": {
                "event_framing": "Assess OpenAI strategy after a board-driven leadership crisis.",
                "focus_entities": ["OpenAI"],
                "current_development": "OpenAI faces leadership turnover, governance questions, and partner pressure.",
                "current_stage": "trigger",
                "time_horizon": "120d",
            },
            "assumptions": {"summary": ["The company will prioritize stakeholder reassurance."]},
            "documents": {"case.md": "Leadership turnover creates board pressure."},
        },
        {
            "run_id": "wrong-domain-case",
            "domain_pack": "market-shock",
            "intake": {
                "event_framing": "Assess market stress after a bank failure.",
                "focus_entities": ["Federal Reserve", "Banking System"],
                "current_development": "A failed bank triggers funding stress and emergency support debate.",
                "current_stage": "trigger",
                "time_horizon": "21d",
            },
            "assumptions": {"summary": ["Authorities will act quickly."]},
            "documents": {"case.md": "Support measures are debated after the failure."},
        },
    ]

    with pytest.raises(ValueError, match="mixed-domain replay payload"):
        service.run_replay_retuning(
            "company-action",
            replay_cases=replay_cases,
            create_branch=False,
        )


def test_synthesize_candidate_updates_manifest_terms(tmp_path: Path) -> None:
    manifest_root = tmp_path / "knowledge" / "domains"
    manifest_root.mkdir(parents=True)
    (manifest_root / "company-action.json").write_text(
        json.dumps({"slug": "company-action", "description": "test manifest"}),
        encoding="utf-8",
    )
    storage = EvolutionStorage(tmp_path / "knowledge" / "evolution")
    service = DomainEvolutionService(
        evolution_storage=storage,
        manifest_root=manifest_root,
    )
    suggestion = DomainSuggestion(
        suggestion_id="s1",
        timestamp=datetime(2026, 4, 21, tzinfo=timezone.utc),
        domain_slug="company-action",
        provenance="user",
        category="action-bias",
        target="contain-message",
        text="Board reassurance should favor containment messaging.",
        terms=["board reassurance"],
        status="pending",
    )

    candidate = service.synthesize_candidate("company-action", suggestions=[suggestion], weakness_brief=None)

    assert candidate.domain_slug == "company-action"
    assert candidate.updated_manifest["adaptive_action_biases"][0]["target"] == "contain-message"
    assert candidate.changed


def test_promotion_decision_rejects_inferred_field_coverage_regression(tmp_path: Path) -> None:
    storage = EvolutionStorage(tmp_path / "knowledge" / "evolution")
    service = DomainEvolutionService(
        evolution_storage=storage,
        manifest_root=tmp_path / "knowledge" / "domains",
    )
    decision = service._promotion_decision(
        pre_metrics={
            "top_branch_accuracy": 1.0,
            "root_strategy_accuracy": 1.0,
            "evidence_source_accuracy": 1.0,
            "average_inferred_field_coverage": 1.0,
        },
        post_metrics={
            "top_branch_accuracy": 1.0,
            "root_strategy_accuracy": 1.0,
            "evidence_source_accuracy": 1.0,
            "average_inferred_field_coverage": 0.8,
        },
        candidate=DomainEvolutionCandidate(
            domain_slug="company-action",
            updated_manifest={"slug": "company-action"},
            changed=True,
            applied_suggestion_ids=["s1"],
        ),
    )

    assert decision == "rejected"
