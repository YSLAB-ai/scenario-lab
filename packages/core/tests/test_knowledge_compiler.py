from __future__ import annotations

import json
from datetime import datetime, timezone

from forecasting_harness.domain.company_action import CompanyActionPack
from forecasting_harness.evolution.service import DomainEvolutionService
from forecasting_harness.evolution.storage import EvolutionStorage
from forecasting_harness.knowledge.compiler import (
    CompiledKnowledgeCandidate,
    compile_approved_evidence_knowledge,
    compile_replay_miss_knowledge,
)
from forecasting_harness.knowledge.manifests import DomainManifest
from forecasting_harness.replay import ReplayCaseResult, ReplaySuiteResult
from forecasting_harness.workflow.compiler import compile_belief_state
from forecasting_harness.workflow.models import AssumptionSummary, EvidencePacket, EvidencePacketItem, IntakeDraft


def _company_manifest() -> DomainManifest:
    return DomainManifest.model_validate(
        {
            "slug": "company-action",
            "description": "test manifest",
            "evidence_categories": ["financial resilience", "leadership behavior"],
            "evidence_category_terms": {
                "financial resilience": ["liquidity", "cash runway"],
                "leadership behavior": ["succession", "board response"],
            },
            "key_state_fields": ["board_cohesion", "cash_runway_months"],
            "semantic_alias_groups": [["leadership behavior", "succession"]],
        }
    )


def test_compile_approved_evidence_knowledge_emits_evidence_and_alias_candidates() -> None:
    pack = CompanyActionPack()
    evidence = EvidencePacket(
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
    )
    intake = IntakeDraft(
        event_framing="Assess company strategy after a CEO transition and liquidity stress.",
        focus_entities=["Acme"],
        current_development="A board-led leadership transition coincides with liquidity stress and customer concern.",
        current_stage="trigger",
        time_horizon="90d",
        suggested_entities=["Board"],
    )
    assumptions = AssumptionSummary(summary=["The board wants stability first"], suggested_actors=["Board"])
    state = compile_belief_state(
        run_id="run-1",
        revision_id="r1",
        pack=pack,
        intake=intake,
        assumptions=assumptions,
        approved_evidence_ids=[item.evidence_id for item in evidence.items],
        approved_evidence_items=evidence.items,
    )

    result = compile_approved_evidence_knowledge(
        domain_slug="company-action",
        manifest=_company_manifest(),
        evidence_packet=evidence,
        state=state,
        pack=pack,
    )

    assert result.source_kind == "approved-evidence"
    assert result.candidate_count >= 2
    categories = {candidate.category for candidate in result.candidates}
    assert "evidence-category" in categories
    assert "semantic-alias" in categories
    evidence_candidate = next(candidate for candidate in result.candidates if candidate.category == "evidence-category")
    assert evidence_candidate.target == "financial resilience"
    assert evidence_candidate.terms


def test_compile_replay_miss_knowledge_emits_action_and_state_candidates() -> None:
    replay_result = ReplaySuiteResult(
        case_count=1,
        top_branch_accuracy=0.0,
        root_strategy_accuracy=0.0,
        evidence_source_accuracy=1.0,
        average_inferred_field_coverage=0.0,
        domain_breakdown={},
        results=[
            ReplayCaseResult(
                run_id="openai-governance",
                domain_pack="company-action",
                case_title="OpenAI governance shock",
                top_branch="Stakeholder reset",
                expected_top_branch="Contain message (message lands)",
                top_branch_match=False,
                root_strategy="Stakeholder reset",
                expected_root_strategy="Contain message",
                root_strategy_match=False,
                evidence_sources=["board-reset"],
                expected_evidence_sources=["board-reset"],
                evidence_source_match=True,
                inferred_fields=[],
                expected_inferred_fields=["board_cohesion"],
                inferred_field_coverage=0.0,
                top_branch_confidence_signal=0.3,
            )
        ],
    )

    result = compile_replay_miss_knowledge(
        domain_slug="company-action",
        manifest=_company_manifest(),
        replay_result=replay_result,
    )

    assert result.source_kind == "replay-miss"
    assert {candidate.category for candidate in result.candidates} == {"action-bias", "state-field"}
    assert any(candidate.target == "contain-message" for candidate in result.candidates)
    assert any(candidate.target == "board_cohesion" for candidate in result.candidates)


def test_record_compiler_candidates_is_idempotent(tmp_path) -> None:
    manifest_root = tmp_path / "knowledge" / "domains"
    manifest_root.mkdir(parents=True)
    (manifest_root / "company-action.json").write_text(
        json.dumps(_company_manifest().model_dump(mode="json")),
        encoding="utf-8",
    )
    service = DomainEvolutionService(
        evolution_storage=EvolutionStorage(tmp_path / "knowledge" / "evolution"),
        manifest_root=manifest_root,
    )
    candidates = [
        CompiledKnowledgeCandidate(
            category="action-bias",
            target="contain-message",
            text="Replay miss suggests containment messaging.",
            terms=["contain message"],
            source_kind="replay-miss",
            source_refs=["openai-governance", "board-reset"],
        )
    ]

    first = service.record_compiler_candidates("company-action", candidates=candidates)
    second = service.record_compiler_candidates("company-action", candidates=candidates)

    assert first["recorded_count"] == 1
    assert second["recorded_count"] == 0
    stored = service.evolution_storage.load_suggestions("company-action")
    assert len(stored) == 1
    assert stored[0].provenance == "compiler"
    assert stored[0].suggestion_id.startswith("compiler-company-action-")
