from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.models import BeliefField
from forecasting_harness.workflow.models import IntakeDraft

if TYPE_CHECKING:
    from forecasting_harness.models import BeliefState


def _anchor_timestamp(state: Any) -> datetime:
    fields = getattr(state, "fields", {})
    if fields:
        return next(iter(fields.values())).last_updated_at
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def _numeric_field(state: Any, field_name: str, default: float) -> float:
    field = getattr(state, "fields", {}).get(field_name)
    if field is None:
        return default
    try:
        return float(field.normalized_value)
    except (TypeError, ValueError):
        return default


def _string_field(state: Any, field_name: str, default: str) -> str:
    field = getattr(state, "fields", {}).get(field_name)
    if field is None:
        return default
    value = field.normalized_value
    return default if not isinstance(value, str) else value


def _with_updates(state: Any, *, phase: str, field_updates: dict[str, float | str]) -> Any:
    existing_fields = dict(getattr(state, "fields", {}))
    timestamp = _anchor_timestamp(state)
    for field_name, value in field_updates.items():
        existing_fields[field_name] = BeliefField(
            value=value,
            normalized_value=value,
            status="inferred",
            confidence=0.65,
            last_updated_at=timestamp,
        )
    return state.model_copy(update={"phase": phase, "current_epoch": phase, "fields": existing_fields})


class InterstateCrisisPack(DomainPack):
    PHASES = [
        "trigger",
        "signaling",
        "limited-response",
        "escalation",
        "negotiation-deescalation",
        "settlement-stalemate",
    ]

    def slug(self) -> str:
        return "interstate-crisis"

    def interaction_model(self) -> InteractionModel:
        return InteractionModel.EVENT_DRIVEN

    def search_config(self) -> dict[str, int | float]:
        return {"iterations": 18, "max_depth": 4, "rollout_depth": 3, "c_puct": 1.15}

    def canonical_phases(self) -> list[str]:
        return list(self.PHASES)

    def validate_intake(self, intake: IntakeDraft) -> list[str]:
        issues: list[str] = []
        if len(intake.focus_entities) != 2:
            issues.append("interstate-crisis requires exactly two focus entities")
        issues.extend(self.validate_phase(intake.current_stage))
        return issues

    def suggest_related_actors(self, intake: IntakeDraft) -> list[str]:
        if set(intake.focus_entities) == {"US", "Iran"}:
            return ["China", "Israel", "Gulf States", "Russia"]
        return []

    def retrieval_filters(self, intake: IntakeDraft) -> dict[str, str]:
        return {"domain": "interstate-crisis"}

    def suggest_questions(self) -> list[str]:
        return [
            "Which outside actor has the most leverage over the next phase?",
            "What constraint most limits immediate escalation?",
        ]

    def extend_schema(self) -> dict[str, Any]:
        return {"military_posture": "str", "leader_style": "str"}

    def validate_phase(self, phase: str) -> list[str]:
        if phase not in self.PHASES:
            return [f"unsupported phase: {phase}"]
        return []

    def is_terminal(self, state: "BeliefState", depth: int) -> bool:
        return getattr(state, "phase", None) == "settlement-stalemate"

    def propose_actions(self, state: "BeliefState") -> list[dict[str, Any]]:
        phase = state.phase or "trigger"
        leader_style = _string_field(state, "leader_style", "cautious")
        hawkish_adjustment = 0.1 if leader_style == "hawkish" else 0.0

        if phase == "trigger":
            return [
                {
                    "action_id": "signal",
                    "branch_id": "signal",
                    "label": "Signal resolve",
                    "prior": 0.5,
                    "dependencies": {"fields": ["leader_style"]},
                },
                {
                    "action_id": "limited-response",
                    "branch_id": "limited-response",
                    "label": "Limited response",
                    "prior": 0.3 + hawkish_adjustment,
                    "dependencies": {"fields": ["leader_style", "military_posture"]},
                },
                {
                    "action_id": "open-negotiation",
                    "branch_id": "open-negotiation",
                    "label": "Open negotiation",
                    "prior": 0.25,
                    "dependencies": {"fields": ["leader_style"]},
                },
            ]
        if phase == "signaling":
            return [
                {"action_id": "signal-resolve", "label": "Signal resolve", "prior": 0.6},
                {"action_id": "intercept", "label": "Intercept", "prior": 0.25 + hawkish_adjustment},
                {"action_id": "crisis-talks", "label": "Crisis talks", "prior": 0.4},
            ]
        if phase == "limited-response":
            return [
                {"action_id": "contain-response", "label": "Contain response", "prior": 0.6},
                {"action_id": "retaliate", "label": "Retaliate", "prior": 0.35 + hawkish_adjustment},
                {"action_id": "ceasefire-channel", "label": "Ceasefire channel", "prior": 0.4},
            ]
        if phase == "escalation":
            return [
                {"action_id": "force-projection", "label": "Force projection", "prior": 0.55 + hawkish_adjustment},
                {"action_id": "emergency-backchannel", "label": "Emergency backchannel", "prior": 0.45},
            ]
        if phase == "negotiation-deescalation":
            return [
                {"action_id": "confidence-measures", "label": "Confidence measures", "prior": 0.4},
                {"action_id": "stalemate-return", "label": "Stalemate return", "prior": 0.6},
            ]
        return []

    def sample_transition(
        self, state: "BeliefState", action_context: dict[str, Any]
    ) -> list["BeliefState"] | list[dict[str, Any]]:
        action_id = action_context.get("action_id") or action_context.get("branch_id")
        phase = state.phase or "trigger"
        tension = _numeric_field(state, "tension_index", 0.4)
        diplomacy = _numeric_field(state, "diplomatic_channel", 0.3)

        if phase == "trigger" and action_id == "signal":
            return [
                _with_updates(
                    state,
                    phase="signaling",
                    field_updates={"tension_index": max(tension, 0.45), "diplomatic_channel": max(diplomacy, 0.45)},
                )
            ]
        if phase == "trigger" and action_id == "limited-response":
            return [
                _with_updates(
                    state,
                    phase="limited-response",
                    field_updates={"tension_index": 0.75, "diplomatic_channel": 0.2},
                )
            ]
        if phase == "trigger" and action_id == "open-negotiation":
            return [
                _with_updates(
                    state,
                    phase="negotiation-deescalation",
                    field_updates={"tension_index": 0.3, "diplomatic_channel": 0.75},
                )
            ]
        if phase == "signaling" and action_id == "signal-resolve":
            return [
                _with_updates(
                    state,
                    phase="settlement-stalemate",
                    field_updates={"tension_index": 0.1, "diplomatic_channel": 0.85},
                )
            ]
        if phase == "signaling" and action_id == "intercept":
            return [
                _with_updates(
                    state,
                    phase="escalation",
                    field_updates={"tension_index": 0.85, "diplomatic_channel": 0.2},
                )
            ]
        if phase == "signaling" and action_id == "crisis-talks":
            return [
                _with_updates(
                    state,
                    phase="negotiation-deescalation",
                    field_updates={"tension_index": 0.35, "diplomatic_channel": 0.75},
                )
            ]
        if phase == "limited-response" and action_id == "contain-response":
            return [
                _with_updates(
                    state,
                    phase="settlement-stalemate",
                    field_updates={"tension_index": 0.45, "diplomatic_channel": 0.3},
                )
            ]
        if phase == "limited-response" and action_id == "retaliate":
            return [
                _with_updates(
                    state,
                    phase="escalation",
                    field_updates={"tension_index": 0.92, "diplomatic_channel": 0.1},
                )
            ]
        if phase == "limited-response" and action_id == "ceasefire-channel":
            return [
                _with_updates(
                    state,
                    phase="negotiation-deescalation",
                    field_updates={"tension_index": 0.35, "diplomatic_channel": 0.8},
                )
            ]
        if phase == "escalation" and action_id == "force-projection":
            return [
                _with_updates(
                    state,
                    phase="settlement-stalemate",
                    field_updates={"tension_index": 0.95, "diplomatic_channel": 0.05},
                )
            ]
        if phase == "escalation" and action_id == "emergency-backchannel":
            return [
                _with_updates(
                    state,
                    phase="negotiation-deescalation",
                    field_updates={"tension_index": 0.45, "diplomatic_channel": 0.7},
                )
            ]
        if phase == "negotiation-deescalation" and action_id == "confidence-measures":
            return [
                _with_updates(
                    state,
                    phase="settlement-stalemate",
                    field_updates={"tension_index": 0.3, "diplomatic_channel": 0.6},
                )
            ]
        if phase == "negotiation-deescalation" and action_id == "stalemate-return":
            return [
                _with_updates(
                    state,
                    phase="signaling",
                    field_updates={"tension_index": 0.6, "diplomatic_channel": 0.35},
                )
            ]
        return [state]

    def score_state(self, state: "BeliefState") -> dict[str, float]:
        tension = _numeric_field(state, "tension_index", 0.5)
        diplomacy = _numeric_field(state, "diplomatic_channel", 0.3)
        phase = state.phase or "trigger"
        phase_stress = {
            "trigger": 0.3,
            "signaling": 0.35,
            "limited-response": 0.55,
            "escalation": 0.8,
            "negotiation-deescalation": 0.3,
            "settlement-stalemate": 0.25,
        }.get(phase, 0.4)
        return {
            "escalation": max(0.0, min(1.0, tension)),
            "negotiation": max(0.0, min(1.0, diplomacy)),
            "economic_stress": max(0.0, min(1.0, phase_stress + tension * 0.15)),
        }

    def validate_state(self, state: "BeliefState") -> list[str]:
        return self.validate_phase(state.phase or "")
