from __future__ import annotations

from typing import get_type_hints

import pytest

from forecasting_harness.domain import (
    DomainPack,
    GenericEventPack,
    InteractionModel,
    InterstateCrisisPack,
)
from forecasting_harness.models import Actor, BehaviorProfile, ObjectiveProfile
from forecasting_harness.workflow.models import IntakeDraft


class _StubPack(DomainPack):
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
        return []

    def score_state(self, state: object) -> dict[str, float]:
        return {}

    def validate_state(self, state: object) -> list[str]:
        return []


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
    assert pack.extend_schema() == {
        "alliance_pressure": "float",
        "geographic_flashpoint": "float",
        "mediation_window": "float",
        "military_posture": "str",
        "leader_style": "str",
        "tension_index": "float",
        "diplomatic_channel": "float",
    }


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
        "alliance-consultation",
        "open-negotiation",
    ]


def test_pack_limited_response_can_branch_into_multiple_outcomes() -> None:
    pack = InterstateCrisisPack()
    state = type(
        "State",
        (),
        {
            "phase": "trigger",
            "fields": {
                "tension_index": type("Field", (), {"normalized_value": 0.8})(),
                "diplomatic_channel": type("Field", (), {"normalized_value": 0.2})(),
                "military_posture": type("Field", (), {"normalized_value": "high-alert"})(),
                "leader_style": type("Field", (), {"normalized_value": "hawkish"})(),
            },
            "model_copy": lambda self, update: type("NextState", (), {**self.__dict__, **update})(),
        },
    )()

    outcomes = pack.sample_transition(
        state,
        {"action_id": "limited-response", "branch_id": "limited-response", "label": "Limited response", "prior": 0.5},
    )

    assert isinstance(outcomes, list)
    assert len(outcomes) >= 2


def test_domain_pack_recommend_objective_profile_defaults_to_balanced_system() -> None:
    pack = _StubPack()
    intake = IntakeDraft(
        event_framing="Assess escalation",
        focus_entities=["A", "B"],
        current_development="A trigger event occurred.",
        current_stage="trigger",
        time_horizon="30d",
    )
    state = type("State", (), {"actors": []})()

    profile = pack.recommend_objective_profile(intake, state)

    assert isinstance(profile, ObjectiveProfile)
    assert profile.name == "balanced-system"
    assert profile.aggregation_mode == "balanced-system"


def test_interstate_pack_can_recommend_domestic_politics_first_profile() -> None:
    pack = InterstateCrisisPack()
    intake = IntakeDraft(
        event_framing="Domestic resolve and alliance signaling are central to the next crisis move.",
        focus_entities=["China", "Taiwan"],
        current_development="Both sides are publicly framing resolve and alliance commitments.",
        current_stage="signaling",
        time_horizon="30d",
    )
    state = type(
        "State",
        (),
        {
            "actors": [
                Actor(
                    actor_id="china",
                    name="China",
                    behavior_profile=BehaviorProfile(domestic_sensitivity=0.82, reputational_sensitivity=0.71),
                ),
                Actor(
                    actor_id="taiwan",
                    name="Taiwan",
                    behavior_profile=BehaviorProfile(alliance_dependence=0.86, negotiation_openness=0.44),
                ),
            ]
        },
    )()

    profile = pack.recommend_objective_profile(intake, state)

    assert profile.name == "domestic-politics-first"
    assert profile.aggregation_mode == "focal-actor"
    assert profile.focal_actor_id == "china"


def test_interstate_pack_scores_actor_impacts_from_behavior_profiles_and_state_fields() -> None:
    pack = InterstateCrisisPack()
    state = type(
        "State",
        (),
        {
            "actors": [
                Actor(
                    actor_id="china",
                    name="China",
                    behavior_profile=BehaviorProfile(
                        domestic_sensitivity=0.8,
                        economic_pain_tolerance=0.6,
                        negotiation_openness=0.3,
                        reputational_sensitivity=0.7,
                        alliance_dependence=0.2,
                        coercive_bias=0.9,
                    ),
                ),
                Actor(
                    actor_id="taiwan",
                    name="Taiwan",
                    behavior_profile=BehaviorProfile(
                        domestic_sensitivity=0.6,
                        economic_pain_tolerance=0.4,
                        negotiation_openness=0.8,
                        reputational_sensitivity=0.5,
                        alliance_dependence=0.9,
                        coercive_bias=0.2,
                    ),
                ),
            ],
            "fields": {
                "tension_index": type("Field", (), {"normalized_value": 0.7})(),
                "diplomatic_channel": type("Field", (), {"normalized_value": 0.4})(),
                "alliance_pressure": type("Field", (), {"normalized_value": 0.8})(),
                "mediation_window": type("Field", (), {"normalized_value": 0.3})(),
            },
        },
    )()

    actor_impacts = pack.score_actor_impacts(state)

    assert actor_impacts == {
        "china": {
            "domestic_sensitivity": pytest.approx(0.8),
            "economic_pain_tolerance": pytest.approx(0.474),
            "negotiation_openness": pytest.approx(0.258),
            "reputational_sensitivity": pytest.approx(0.7),
            "alliance_dependence": pytest.approx(0.16),
            "coercive_bias": pytest.approx(0.666),
        },
        "taiwan": {
            "domestic_sensitivity": pytest.approx(0.6),
            "economic_pain_tolerance": pytest.approx(0.316),
            "negotiation_openness": pytest.approx(0.688),
            "reputational_sensitivity": pytest.approx(0.5),
            "alliance_dependence": pytest.approx(0.72),
            "coercive_bias": pytest.approx(0.148),
        },
    }
