from datetime import datetime, timezone

from forecasting_harness.compatibility import compare_belief_states, compare_state_slices
from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.models import Actor, BeliefField, BeliefState


def test_compatibility_uses_normalized_values_not_display_text() -> None:
    previous = {
        "morale": {"normalized_value": 0.8},
        "fuel_days": {"normalized_value": 12},
    }
    current = {
        "morale": {"normalized_value": 0.9},
        "fuel_days": {"normalized_value": 12},
    }

    result = compare_state_slices(
        previous,
        current,
        tolerances={"morale": 0.2, "fuel_days": 0.0},
    )

    assert result["compatible"] is True
    assert result["changed_fields"] == ["morale"]


def test_compatibility_treats_bool_changes_as_changes_not_numeric_drift() -> None:
    previous = {"enabled": {"normalized_value": False}}
    current = {"enabled": {"normalized_value": True}}

    result = compare_state_slices(
        previous,
        current,
        tolerances={"enabled": 10.0},
    )

    assert result["compatible"] is False
    assert result["changed_fields"] == ["enabled"]


def test_belief_state_compatibility_can_allow_reuse_with_changed_fields() -> None:
    timestamp = datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc)
    previous = BeliefState(
        run_id="run-1",
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[Actor(actor_id="a", name="A")],
        fields={
            "morale": BeliefField(
                value=0.8,
                normalized_value=0.8,
                status="observed",
                confidence=1.0,
                last_updated_at=timestamp,
            )
        },
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch="trigger",
        horizon="30d",
        phase="trigger",
        domain_pack="generic-event",
    )
    current = previous.model_copy(
        update={
            "fields": {
                "morale": BeliefField(
                    value=0.85,
                    normalized_value=0.85,
                    status="observed",
                    confidence=1.0,
                    last_updated_at=timestamp,
                )
            }
        }
    )

    result = compare_belief_states(previous, current, tolerances={"morale": 0.0})

    assert result["compatible"] is False
    assert result["reusable"] is True
    assert result["changed_fields"] == ["morale"]
    assert result["reasons"] == []


def test_belief_state_compatibility_blocks_reuse_when_structure_changes() -> None:
    timestamp = datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc)
    previous = BeliefState(
        run_id="run-1",
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[Actor(actor_id="a", name="A")],
        fields={
            "morale": BeliefField(
                value=0.8,
                normalized_value=0.8,
                status="observed",
                confidence=1.0,
                last_updated_at=timestamp,
            )
        },
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch="trigger",
        horizon="30d",
        phase="trigger",
        domain_pack="generic-event",
    )
    current = previous.model_copy(update={"phase": "signaling"})

    result = compare_belief_states(previous, current, tolerances={"morale": 0.0})

    assert result["compatible"] is False
    assert result["reusable"] is False
    assert "phase changed" in result["reasons"]
