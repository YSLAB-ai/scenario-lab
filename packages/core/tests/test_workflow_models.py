from datetime import datetime, timezone
from typing import get_args

import pytest
from pydantic import ValidationError

from forecasting_harness.workflow import (
    ApprovalPacket,
    AssumptionSummary,
    ConversationTurn,
    EvidencePacket,
    EvidencePacketItem,
    IntakeGuidance,
    IntakeDraft,
    RevisionSummary,
    RevisionRecord,
    RevisionStatus,
    RunSummary,
    RunRecord,
)


def test_workflow_models_are_exported_from_package() -> None:
    assert get_args(RevisionStatus) == ("draft", "approved", "simulated")


def test_run_record_preserves_current_revision_id() -> None:
    record = RunRecord(
        run_id="run-1",
        domain_pack="generic-event",
        created_at=datetime(2026, 4, 19, tzinfo=timezone.utc),
    )

    assert record.current_revision_id is None
    assert record.domain_pack == "generic-event"


def test_revision_record_defaults_to_draft() -> None:
    record = RevisionRecord(
        revision_id="rev-1",
        created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
    )

    assert record.status == "draft"
    assert record.parent_revision_id is None
    assert record.approved_at is None
    assert record.simulated_at is None


def test_intake_draft_requires_at_least_one_focus_entity() -> None:
    with pytest.raises(ValidationError, match="primary_actors"):
        IntakeDraft(
            event_framing="A new policy shift is underway.",
            primary_actors=[],
            trigger="policy change",
            current_phase="intake",
            time_horizon="2026-Q2",
        )


def test_intake_draft_accepts_legacy_aliases() -> None:
    intake = IntakeDraft.model_validate(
        {
            "event_framing": "Assess escalation",
            "primary_actors": ["US", "Iran"],
            "trigger": "Exchange of strikes",
            "current_phase": "trigger",
            "time_horizon": "30d",
            "suggested_actors": ["China"],
        }
    )

    assert intake.focus_entities == ["US", "Iran"]
    assert intake.current_development == "Exchange of strikes"
    assert intake.current_stage == "trigger"
    assert intake.suggested_entities == ["China"]


def test_intake_draft_preserves_pack_fields() -> None:
    intake = IntakeDraft(
        event_framing="Assess escalation",
        focus_entities=["US", "Iran"],
        current_development="Exchange of strikes",
        current_stage="trigger",
        time_horizon="30d",
        pack_fields={"military_posture": "high"},
    )

    assert intake.pack_fields == {"military_posture": "high"}


def test_assumption_summary_defaults_to_balanced_profile() -> None:
    summary = AssumptionSummary()

    assert summary.summary == []
    assert summary.suggested_actors == []
    assert summary.objective_profile_name == "balanced"


def test_evidence_packet_defaults_to_empty_items() -> None:
    packet = EvidencePacket(revision_id="rev-1")

    assert packet.items == []


def test_evidence_packet_item_preserves_evidence_metadata() -> None:
    item = EvidencePacketItem(
        evidence_id="ev-1",
        source_id="src-1",
        source_title="Source Title",
        reason="Supports the revision",
    )

    assert item.passage_ids == []
    assert item.citation_refs == []
    assert item.raw_passages == []


def test_intake_guidance_preserves_pack_assistance_fields() -> None:
    guidance = IntakeGuidance(
        domain_pack="interstate-crisis",
        current_stage="trigger",
        canonical_stages=["trigger", "signaling"],
        suggested_entities=["China"],
        follow_up_questions=["Which outside actor has leverage?"],
        pack_field_schema={"military_posture": "str"},
        default_objective_profile={"name": "balanced"},
    )

    assert guidance.domain_pack == "interstate-crisis"
    assert guidance.suggested_entities == ["China"]


def test_run_summary_preserves_revision_order() -> None:
    summary = RunSummary(
        run_id="crisis-1",
        domain_pack="interstate-crisis",
        current_revision_id="r2",
        revisions=[{"revision_id": "r1", "status": "approved"}, {"revision_id": "r2", "status": "simulated"}],
    )

    assert [item["revision_id"] for item in summary.revisions] == ["r1", "r2"]


def test_approval_packet_and_revision_summary_capture_narrow_fields() -> None:
    packet = ApprovalPacket(
        revision_id="r1",
        intake_summary={"event_framing": "Assess escalation"},
        assumption_summary=["known unknown: timing"],
        objective_profile={"name": "balanced"},
        evidence_summary=[{"source_id": "src-1", "passage_count": 1}],
        warnings=["no evidence drafted yet"],
    )
    summary = RevisionSummary(
        revision_id="r1",
        status="draft",
        parent_revision_id=None,
        evidence_item_count=0,
        assumption_count=1,
        top_branches=[{"label": "Signal resolve", "score": -0.06}],
        available_sections=["intake", "evidence"],
    )

    assert packet.evidence_summary[0]["source_id"] == "src-1"
    assert summary.available_sections == ["intake", "evidence"]


def test_conversation_turn_captures_stage_and_context() -> None:
    turn = ConversationTurn(
        run_id="crisis-1",
        revision_id="r1",
        stage="approval",
        headline="Review approval packet",
        user_message="Evidence draft is ready.",
        recommended_command="forecast-harness approve-revision",
        available_sections=["intake", "evidence"],
        context={"revision_id": "r1"},
    )

    assert turn.stage == "approval"
    assert turn.context["revision_id"] == "r1"
