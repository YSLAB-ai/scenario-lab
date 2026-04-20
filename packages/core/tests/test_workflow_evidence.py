from __future__ import annotations

from datetime import datetime, timezone

import pytest

from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.workflow.compiler import compile_belief_state
from forecasting_harness.workflow.evidence import draft_evidence_packet
from forecasting_harness.workflow.models import AssumptionSummary, IntakeDraft


class _FrozenDateTime:
    @classmethod
    def now(cls, tz: timezone | None = None) -> datetime:
        assert tz == timezone.utc
        return datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc)


class StubPack(DomainPack):
    def slug(self) -> str:
        return "stub"

    def interaction_model(self) -> InteractionModel:
        return InteractionModel.EVENT_DRIVEN

    def extend_schema(self) -> dict[str, str]:
        return {}

    def suggest_questions(self) -> list[str]:
        return []

    def propose_actions(self, state: object) -> list[dict[str, object]]:
        return []

    def sample_transition(self, state: object, action_context: dict[str, object]) -> list[object]:
        return [state]

    def score_state(self, state: object) -> dict[str, float]:
        return {}

    def validate_state(self, state: object) -> list[str]:
        return []


def test_draft_evidence_packet_limits_entries_per_source_and_preserves_raw_passages() -> None:
    hits = [
        {"source_id": "s1", "title": "Doc 1", "content": "alpha", "published_at": "2026-04-20", "score": 1.0},
        {"source_id": "s1", "title": "Doc 1", "content": "beta", "published_at": "2026-04-20", "score": 0.9},
        {"source_id": "s1", "title": "Doc 1", "content": "gamma", "published_at": "2026-04-20", "score": 0.8},
        {"source_id": "s2", "title": "Doc 2", "content": "delta", "published_at": "2026-04-20", "score": 0.7},
    ]

    packet = draft_evidence_packet("r1", hits, max_per_source=2)

    assert [item.evidence_id for item in packet.items] == ["r1:s1:1", "r1:s1:2", "r1:s2:1"]
    assert [item.source_id for item in packet.items] == ["s1", "s1", "s2"]
    assert [item.raw_passages for item in packet.items] == [["alpha"], ["beta"], ["delta"]]
    assert len([item for item in packet.items if item.source_id == "s1"]) == 2


def test_draft_evidence_packet_is_deterministic_across_input_order() -> None:
    hits_a = [
        {"source_id": "s2", "title": "Doc 2", "content": "beta", "published_at": "2026-04-20", "score": 0.7},
        {"source_id": "s1", "title": "Doc 1", "content": "alpha", "published_at": "2026-04-20", "score": 1.0},
        {"source_id": "s1", "title": "Doc 1", "content": "gamma", "published_at": "2026-04-20", "score": 0.8},
        {"source_id": "s2", "title": "Doc 2", "content": "delta", "published_at": "2026-04-20", "score": 0.6},
    ]
    hits_b = [
        {"source_id": "s1", "title": "Doc 1", "content": "gamma", "published_at": "2026-04-20", "score": 0.8},
        {"source_id": "s2", "title": "Doc 2", "content": "delta", "published_at": "2026-04-20", "score": 0.6},
        {"source_id": "s1", "title": "Doc 1", "content": "alpha", "published_at": "2026-04-20", "score": 1.0},
        {"source_id": "s2", "title": "Doc 2", "content": "beta", "published_at": "2026-04-20", "score": 0.7},
    ]

    packet_a = draft_evidence_packet("r1", hits_a, max_per_source=2)
    packet_b = draft_evidence_packet("r1", hits_b, max_per_source=2)

    assert [item.evidence_id for item in packet_a.items] == [item.evidence_id for item in packet_b.items]
    assert [item.source_id for item in packet_a.items] == [item.source_id for item in packet_b.items]
    assert [item.raw_passages for item in packet_a.items] == [item.raw_passages for item in packet_b.items]


def test_draft_evidence_packet_enforces_a_total_cap() -> None:
    hits = [
        {"source_id": "s1", "title": "Doc 1", "content": "alpha", "published_at": "2026-04-20", "score": 1.0},
        {"source_id": "s1", "title": "Doc 1", "content": "beta", "published_at": "2026-04-20", "score": 0.9},
        {"source_id": "s2", "title": "Doc 2", "content": "gamma", "published_at": "2026-04-20", "score": 0.8},
        {"source_id": "s2", "title": "Doc 2", "content": "delta", "published_at": "2026-04-20", "score": 0.7},
    ]

    packet = draft_evidence_packet("r1", hits, max_per_source=2, max_total=3)

    assert len(packet.items) == 3
    assert [item.evidence_id for item in packet.items] == ["r1:s1:1", "r1:s1:2", "r1:s2:1"]


def test_draft_evidence_packet_total_cap_prefers_higher_ranked_hits_across_sources() -> None:
    hits = [
        {"source_id": "s1", "title": "Doc 1", "content": "alpha", "published_at": "2026-04-20", "score": 0.91},
        {"source_id": "s1", "title": "Doc 1", "content": "beta", "published_at": "2026-04-20", "score": 0.52},
        {"source_id": "s2", "title": "Doc 2", "content": "gamma", "published_at": "2026-04-20", "score": 0.83},
        {"source_id": "s3", "title": "Doc 3", "content": "delta", "published_at": "2026-04-20", "score": 0.74},
    ]

    packet = draft_evidence_packet("r1", hits, max_per_source=2, max_total=2)

    assert [item.evidence_id for item in packet.items] == ["r1:s1:1", "r1:s2:1"]
    assert [item.raw_passages for item in packet.items] == [["alpha"], ["gamma"]]


def test_compile_belief_state_includes_primary_and_suggested_actors(monkeypatch) -> None:
    from forecasting_harness.workflow import compiler as workflow_compiler

    monkeypatch.setattr(workflow_compiler, "datetime", _FrozenDateTime)

    intake = IntakeDraft(
        event_framing="Assess escalation",
        primary_actors=["US", "Iran"],
        trigger="Exchange of strikes",
        current_phase="trigger",
        time_horizon="30d",
        known_constraints=["sanctions"],
        known_unknowns=["timing"],
        suggested_actors=["China", "Russia"],
    )
    assumptions = AssumptionSummary(summary=["China matters"], suggested_actors=["China", "EU", "US"])

    state = compile_belief_state(
        run_id="crisis-1",
        revision_id="r1",
        pack=StubPack(),
        intake=intake,
        assumptions=assumptions,
        approved_evidence_ids=["ev-1"],
    )

    assert state.run_id == "crisis-1"
    assert state.revision_id == "r1"
    assert state.domain_pack == "stub"
    assert state.phase == "trigger"
    assert state.current_epoch == "trigger"
    assert state.horizon == "30d"
    assert state.interaction_model is InteractionModel.EVENT_DRIVEN
    assert [actor.name for actor in state.actors] == ["US", "Iran", "China", "Russia", "EU"]
    assert state.fields["event_framing"].status == "observed"
    assert state.fields["event_framing"].value == "Assess escalation"
    assert state.fields["event_framing"].normalized_value == "Assess escalation"
    assert state.fields["event_framing"].last_updated_at == datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc)
    assert state.fields["trigger"].status == "observed"
    assert state.fields["trigger"].value == "Exchange of strikes"
    assert state.fields["trigger"].normalized_value == "Exchange of strikes"
    assert state.fields["trigger"].last_updated_at == datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc)
    assert list(state.constraints.values()) == ["sanctions"]
    assert state.unknowns == ["timing"]
    assert state.approved_evidence_ids == ["ev-1"]


def test_compile_belief_state_rejects_unsupported_phases() -> None:
    class PhasePack(StubPack):
        def canonical_phases(self) -> list[str]:
            return ["trigger", "signaling"]

    intake = IntakeDraft(
        event_framing="Assess escalation",
        primary_actors=["US", "Iran"],
        trigger="Exchange of strikes",
        current_phase="improvise",
        time_horizon="30d",
    )

    with pytest.raises(ValueError, match="unsupported phase"):
        compile_belief_state(
            run_id="crisis-1",
            revision_id="r1",
            pack=PhasePack(),
            intake=intake,
            assumptions=AssumptionSummary(),
            approved_evidence_ids=[],
        )


def test_domain_pack_workflow_hooks_default_to_empty_collections() -> None:
    pack = StubPack()
    intake = IntakeDraft(
        event_framing="Assess escalation",
        primary_actors=["US", "Iran"],
        trigger="Exchange of strikes",
        current_phase="trigger",
        time_horizon="30d",
    )

    assert pack.canonical_phases() == []
    assert pack.suggest_related_actors(intake) == []
    assert pack.retrieval_filters(intake) == {}
