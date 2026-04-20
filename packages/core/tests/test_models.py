from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.models import Actor, BeliefField, BeliefState, ObjectiveProfile


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
