from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from forecasting_harness.domain.base import DomainPack, InteractionModel


def _anchor_timestamp(state: Any) -> datetime:
    fields = getattr(state, "fields", {})
    if fields:
        first_field = next(iter(fields.values()))
        return first_field.last_updated_at
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def _field_value(state: Any, field_name: str, default: float) -> float:
    field = getattr(state, "fields", {}).get(field_name)
    if field is None:
        return default
    try:
        return float(field.normalized_value)
    except (TypeError, ValueError):
        return default


def _with_updates(state: Any, *, phase: str, field_updates: dict[str, float]) -> Any:
    from forecasting_harness.models import BeliefField

    existing_fields = dict(getattr(state, "fields", {}))
    timestamp = _anchor_timestamp(state)
    for field_name, value in field_updates.items():
        existing_fields[field_name] = BeliefField(
            value=value,
            normalized_value=value,
            status="inferred",
            confidence=0.6,
            last_updated_at=timestamp,
        )
    return state.model_copy(update={"phase": phase, "current_epoch": phase, "fields": existing_fields})


class GenericEventPack(DomainPack):
    def slug(self) -> str:
        return "generic-event"

    def interaction_model(self) -> InteractionModel:
        return InteractionModel.EVENT_DRIVEN

    def search_config(self) -> dict[str, int | float]:
        return {"iterations": 12, "max_depth": 3, "rollout_depth": 2, "c_puct": 1.1}

    def extend_schema(self) -> dict[str, Any]:
        return {"morale": "float", "fuel_days": "int"}

    def suggest_questions(self) -> list[str]:
        return [
            "What changed most recently?",
            "Which actor has the most immediate leverage?",
        ]

    def is_terminal(self, state: Any, depth: int) -> bool:
        return getattr(state, "phase", None) == "resolved"

    def propose_actions(self, state: Any) -> list[dict[str, Any]]:
        phase = getattr(state, "phase", None) or "start"
        if phase == "start":
            return [
                {
                    "action_id": "maintain-course",
                    "branch_id": "maintain-course",
                    "label": "Maintain course",
                    "prior": 0.55,
                    "dependencies": {"fields": ["morale"]},
                },
                {
                    "action_id": "signal-negotiation",
                    "branch_id": "signal-negotiation",
                    "label": "Signal negotiation",
                    "prior": 0.45,
                    "dependencies": {"fields": ["morale", "fuel_days"]},
                },
            ]
        if phase == "stabilization":
            return [
                {"action_id": "seek-resupply", "label": "Seek resupply", "prior": 0.6},
                {"action_id": "prepare-pivot", "label": "Prepare pivot", "prior": 0.4},
            ]
        if phase == "negotiation":
            return [
                {"action_id": "formalize-terms", "label": "Formalize terms", "prior": 0.65},
                {"action_id": "stall-talks", "label": "Stall talks", "prior": 0.35},
            ]
        if phase == "pressure":
            return [
                {"action_id": "reassure", "label": "Reassure", "prior": 0.55},
                {"action_id": "double-down", "label": "Double down", "prior": 0.45},
            ]
        return []

    def sample_transition(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        action_id = action_context.get("action_id") or action_context.get("branch_id")
        phase = getattr(state, "phase", None) or "start"
        morale = _field_value(state, "morale", 0.5)
        fuel_days = _field_value(state, "fuel_days", 4.0)

        if phase == "start" and action_id == "maintain-course":
            return [_with_updates(state, phase="stabilization", field_updates={"morale": morale + 0.1, "fuel_days": fuel_days})]
        if phase == "start" and action_id == "signal-negotiation":
            return [_with_updates(state, phase="negotiation", field_updates={"morale": morale, "fuel_days": fuel_days - 1})]
        if phase == "stabilization" and action_id == "seek-resupply":
            return [_with_updates(state, phase="resolved", field_updates={"morale": morale + 0.1, "fuel_days": fuel_days + 2})]
        if phase == "stabilization" and action_id == "prepare-pivot":
            return [_with_updates(state, phase="pressure", field_updates={"morale": morale - 0.1, "fuel_days": fuel_days - 1})]
        if phase == "negotiation" and action_id == "formalize-terms":
            return [_with_updates(state, phase="resolved", field_updates={"morale": morale + 0.05, "fuel_days": fuel_days})]
        if phase == "negotiation" and action_id == "stall-talks":
            return [_with_updates(state, phase="stabilization", field_updates={"morale": morale - 0.05, "fuel_days": fuel_days - 1})]
        if phase == "pressure" and action_id == "reassure":
            return [_with_updates(state, phase="negotiation", field_updates={"morale": morale + 0.05, "fuel_days": fuel_days})]
        if phase == "pressure" and action_id == "double-down":
            return [_with_updates(state, phase="resolved", field_updates={"morale": morale - 0.2, "fuel_days": fuel_days - 1})]
        return [state]

    def score_state(self, state: Any) -> dict[str, float]:
        phase = getattr(state, "phase", None) or "start"
        morale = _field_value(state, "morale", 0.5)
        fuel_days = _field_value(state, "fuel_days", 4.0)
        fuel_pressure = max(0.0, 1.0 - min(fuel_days, 10.0) / 10.0)
        phase_escalation = {
            "start": 0.45,
            "stabilization": 0.3,
            "negotiation": 0.2,
            "pressure": 0.55,
            "resolved": 0.1,
        }.get(phase, 0.4)
        phase_negotiation = {
            "start": 0.35,
            "stabilization": 0.4,
            "negotiation": 0.7,
            "pressure": 0.25,
            "resolved": 0.8,
        }.get(phase, 0.3)
        return {
            "escalation": max(0.0, min(1.0, phase_escalation + (0.5 - morale) * 0.2)),
            "negotiation": max(0.0, min(1.0, phase_negotiation + (morale - 0.5) * 0.2)),
            "economic_stress": max(0.0, min(1.0, 0.2 + fuel_pressure * 0.5)),
        }

    def validate_state(self, state: Any) -> list[str]:
        return []
