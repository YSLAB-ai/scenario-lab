from types import SimpleNamespace

from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack


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
    intake = SimpleNamespace(primary_actors=["US", "Iran"])

    assert "China" in pack.suggest_related_actors(intake)


def test_pack_exposes_domain_specific_retrieval_filters() -> None:
    pack = InterstateCrisisPack()
    intake = SimpleNamespace(primary_actors=["US", "Iran"])

    assert pack.retrieval_filters(intake) == {"domain": "interstate-crisis"}


def test_pack_suggests_crisis_questions_and_schema() -> None:
    pack = InterstateCrisisPack()

    assert pack.suggest_questions() == [
        "Which outside actor has the most leverage over the next phase?",
        "What constraint most limits immediate escalation?",
    ]
    assert pack.extend_schema() == {"military_posture": "str", "leader_style": "str"}


def test_pack_validates_phase_membership_and_state_phase() -> None:
    pack = InterstateCrisisPack()
    state = SimpleNamespace(phase="improvise")

    assert "unsupported phase" in pack.validate_phase("improvise")[0]
    assert "unsupported phase" in pack.validate_state(state)[0]


def test_pack_proposes_simple_event_driven_actions() -> None:
    pack = InterstateCrisisPack()

    assert pack.interaction_model().value == "event_driven"
    assert [action["action_id"] for action in pack.propose_actions(None)] == [
        "signal",
        "limited-response",
        "open-negotiation",
    ]
