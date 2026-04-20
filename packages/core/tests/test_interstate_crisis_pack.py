from __future__ import annotations

from typing import get_type_hints

from forecasting_harness.domain import (
    DomainPack,
    GenericEventPack,
    InteractionModel,
    InterstateCrisisPack,
)
from forecasting_harness.workflow.models import IntakeDraft


def test_domain_package_exports_requested_pack_surface() -> None:
    assert issubclass(GenericEventPack, DomainPack)
    assert issubclass(InterstateCrisisPack, DomainPack)
    assert InteractionModel.EVENT_DRIVEN.value == "event_driven"


def test_pack_exposes_fixed_canonical_phases() -> None:
    pack = InterstateCrisisPack()

    assert pack.canonical_phases() == [
        "trigger",
        "signaling",
        "limited-response",
        "escalation",
        "negotiation-deescalation",
        "settlement-stalemate",
    ]


def test_pack_suggests_relevant_third_parties_for_us_iran_case() -> None:
    pack = InterstateCrisisPack()
    intake = IntakeDraft(
        event_framing="Assess escalation",
        primary_actors=["US", "Iran"],
        trigger="Exchange of strikes",
        current_phase="trigger",
        time_horizon="30d",
    )

    suggestions = pack.suggest_related_actors(intake)

    assert "China" in suggestions


def test_pack_exposes_domain_specific_retrieval_filters() -> None:
    pack = InterstateCrisisPack()
    intake = IntakeDraft(
        event_framing="Assess escalation",
        primary_actors=["US", "Iran"],
        trigger="Exchange of strikes",
        current_phase="trigger",
        time_horizon="30d",
    )

    assert pack.retrieval_filters(intake) == {"domain": "interstate-crisis"}


def test_pack_uses_workflow_intake_type_hints() -> None:
    assert get_type_hints(InterstateCrisisPack.suggest_related_actors)["intake"] is IntakeDraft
    assert get_type_hints(InterstateCrisisPack.retrieval_filters)["intake"] is IntakeDraft


def test_pack_suggests_crisis_questions_and_schema() -> None:
    pack = InterstateCrisisPack()

    assert pack.suggest_questions() == [
        "Which outside actor has the most leverage over the next phase?",
        "What constraint most limits immediate escalation?",
    ]
    assert pack.extend_schema() == {"military_posture": "str", "leader_style": "str"}


def test_pack_validates_phase_membership_and_state_phase() -> None:
    pack = InterstateCrisisPack()
    state = type("State", (), {"phase": "improvise"})()

    assert "unsupported phase" in pack.validate_phase("improvise")[0]
    assert "unsupported phase" in pack.validate_state(state)[0]


def test_pack_proposes_simple_event_driven_actions() -> None:
    pack = InterstateCrisisPack()

    assert pack.interaction_model() is InteractionModel.EVENT_DRIVEN
    assert [action["action_id"] for action in pack.propose_actions(None)] == [
        "signal",
        "limited-response",
        "open-negotiation",
    ]
