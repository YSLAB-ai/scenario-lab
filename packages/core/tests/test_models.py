from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.models import Actor, BehaviorProfile, BeliefField, BeliefState, ObjectiveProfile
from forecasting_harness.objectives import default_objective_profile, objective_profile_by_name


def test_belief_field_preserves_display_and_normalized_value() -> None:
    field = BeliefField(
        value="very high",
        normalized_value=0.9,
        status="inferred",
        supporting_evidence_ids=["ev-1"],
        confidence=0.7,
        last_updated_at=datetime(2026, 4, 19, tzinfo=timezone.utc),
    )

    assert field.value == "very high"
    assert field.normalized_value == 0.9
    assert field.last_updated_at == datetime(2026, 4, 19, tzinfo=timezone.utc)


def test_behavior_profile_accepts_actor_utility_fields() -> None:
    profile = BehaviorProfile(
        domestic_sensitivity=0.8,
        economic_pain_tolerance=0.2,
        negotiation_openness=0.6,
        reputational_sensitivity=0.7,
        alliance_dependence=0.4,
        coercive_bias=0.1,
    )

    assert profile.domestic_sensitivity == 0.8
    assert profile.economic_pain_tolerance == 0.2
    assert profile.negotiation_openness == 0.6
    assert profile.reputational_sensitivity == 0.7
    assert profile.alliance_dependence == 0.4
    assert profile.coercive_bias == 0.1


def test_objective_profile_scalarizes_metric_vector() -> None:
    profile = ObjectiveProfile(
        name="de-escalation",
        metric_weights={"escalation": -0.7, "negotiation": 0.3},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
    )

    score = profile.scalarize({"escalation": 0.8, "negotiation": 0.2})

    assert round(score, 3) == -0.5


def test_objective_profile_scalarize_rejects_unknown_metrics() -> None:
    profile = ObjectiveProfile(
        name="de-escalation",
        metric_weights={"escalation": -0.7},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
    )

    with pytest.raises(ValueError, match="unknown metric"):
        profile.scalarize({"escalation": 0.8, "negotiation": 0.2})


def test_objective_profile_registry_supports_aggregation_aliases() -> None:
    balanced = objective_profile_by_name("balanced")
    balanced_system = objective_profile_by_name("balanced-system")
    focal = objective_profile_by_name("domestic-politics-first")

    assert balanced.aggregation_mode == "balanced-system"
    assert balanced_system.aggregation_mode == "balanced-system"
    assert balanced_system.name == "balanced-system"
    assert focal.aggregation_mode == "focal-actor"
    assert balanced.focal_actor_id is None
    assert balanced_system.focal_actor_id is None
    assert focal.focal_actor_id is None
    assert set(balanced.actor_metric_weights) == {
        "domestic_sensitivity",
        "economic_pain_tolerance",
        "negotiation_openness",
        "reputational_sensitivity",
        "alliance_dependence",
        "coercive_bias",
    }
    assert focal.actor_metric_weights["domestic_sensitivity"] > balanced.actor_metric_weights["domestic_sensitivity"]


def test_default_objective_profile_remains_available() -> None:
    profile = default_objective_profile()

    assert profile.name == "balanced-system"
    assert profile.aggregation_mode == "balanced-system"


def test_belief_field_rejects_out_of_range_confidence() -> None:
    with pytest.raises(ValidationError, match="confidence"):
        BeliefField(
            value="high",
            normalized_value=0.9,
            status="observed",
            confidence=1.2,
            last_updated_at=datetime(2026, 4, 19, tzinfo=timezone.utc),
        )


def test_belief_field_rejects_invalid_timestamp() -> None:
    with pytest.raises(ValidationError, match="last_updated_at"):
        BeliefField(
            value="high",
            normalized_value=0.9,
            status="observed",
            confidence=0.7,
            last_updated_at="not-a-timestamp",
        )


def test_objective_profile_rejects_out_of_range_risk_tolerance() -> None:
    with pytest.raises(ValidationError, match="risk_tolerance"):
        ObjectiveProfile(
            name="de-escalation",
            metric_weights={"escalation": -0.7},
            veto_thresholds={},
            risk_tolerance=1.2,
            asymmetry_penalties={},
        )


def test_belief_state_tracks_interaction_model() -> None:
    state = BeliefState(
        run_id="run-1",
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[Actor(actor_id="a1", name="Actor 1")],
        fields={},
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch="2026-W16",
        horizon="2026-W20",
    )

    assert state.interaction_model is InteractionModel.EVENT_DRIVEN


def test_belief_state_tracks_revision_metadata() -> None:
    state = BeliefState(
        run_id="run-1",
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[Actor(actor_id="a1", name="Actor 1")],
        fields={},
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch="2026-W16",
        horizon="2026-W20",
        revision_id="rev-1",
        domain_pack="generic-event",
        phase="intake",
        approved_evidence_ids=["ev-1"],
    )

    assert state.revision_id == "rev-1"
    assert state.domain_pack == "generic-event"
    assert state.phase == "intake"
    assert state.approved_evidence_ids == ["ev-1"]
