from __future__ import annotations

from typing import Any

from forecasting_harness.domain.base import DomainPack, InteractionModel


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

    def canonical_phases(self) -> list[str]:
        return list(self.PHASES)

    def suggest_related_actors(self, intake: Any) -> list[str]:
        if set(getattr(intake, "primary_actors", [])) == {"US", "Iran"}:
            return ["China", "Israel", "Gulf States", "Russia"]
        return []

    def retrieval_filters(self, intake: Any) -> dict[str, str]:
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

    def propose_actions(self, state: Any) -> list[dict[str, Any]]:
        return [
            {
                "action_id": "signal",
                "branch_id": "signal",
                "label": "Signal resolve",
                "dependencies": {"fields": []},
            },
            {
                "action_id": "limited-response",
                "branch_id": "limited-response",
                "label": "Limited response",
                "dependencies": {"fields": []},
            },
            {
                "action_id": "open-negotiation",
                "branch_id": "open-negotiation",
                "label": "Open negotiation",
                "dependencies": {"fields": []},
            },
        ]

    def sample_transition(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        return [state]

    def score_state(self, state: Any) -> dict[str, float]:
        return {"escalation": 0.3, "negotiation": 0.4, "economic_stress": 0.2}

    def validate_state(self, state: Any) -> list[str]:
        return self.validate_phase(getattr(state, "phase", ""))
