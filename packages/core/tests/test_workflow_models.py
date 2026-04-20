from datetime import datetime, timezone
from typing import get_args

import pytest
from pydantic import ValidationError

from forecasting_harness.workflow import (
    AssumptionSummary,
    EvidencePacket,
    EvidencePacketItem,
    IntakeDraft,
    RevisionRecord,
    RevisionStatus,
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
    record = RevisionRecord(revision_id="rev-1")

    assert record.status == "draft"
    assert record.parent_revision_id is None


def test_intake_draft_requires_two_primary_actors() -> None:
    with pytest.raises(ValidationError, match="primary_actors"):
        IntakeDraft(
            event_framing="A new policy shift is underway.",
            primary_actors=["actor-1"],
            trigger="policy change",
            current_phase="intake",
            time_horizon="2026-Q2",
        )


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
