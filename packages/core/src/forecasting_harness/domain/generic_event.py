from __future__ import annotations

from typing import Any

from forecasting_harness.domain.base import DomainPack, InteractionModel


class GenericEventPack(DomainPack):
    def slug(self) -> str:
        return "generic-event"

    def interaction_model(self) -> InteractionModel:
        return InteractionModel.EVENT_DRIVEN

    def extend_schema(self) -> dict[str, Any]:
        return {"morale": "float", "fuel_days": "int"}

    def suggest_questions(self) -> list[str]:
        return [
            "What changed most recently?",
            "Which actor has the most immediate leverage?",
        ]

    def propose_actions(self, state: Any) -> list[dict[str, Any]]:
        return [
            {
                "action_id": "maintain-course",
                "branch_id": "maintain-course",
                "label": "Maintain course",
                "dependencies": {"fields": ["morale"]},
            },
            {
                "action_id": "signal-negotiation",
                "branch_id": "signal-negotiation",
                "label": "Signal negotiation",
                "dependencies": {"fields": ["morale", "fuel_days"]},
            },
        ]

    def sample_transition(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        return [state]

    def score_state(self, state: Any) -> dict[str, float]:
        return {"escalation": 0.2, "negotiation": 0.4, "economic_stress": 0.3}

    def validate_state(self, state: Any) -> list[str]:
        return []
