from __future__ import annotations

from typing import Any

from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.domain.template_utils import bounded, numeric_field, with_updates
from forecasting_harness.workflow.models import IntakeDraft


class ElectionShockPack(DomainPack):
    PHASES = ["trigger", "narrative-fight", "turnout-drive", "coalition-shaping", "resolution"]

    def slug(self) -> str:
        return "election-shock"

    def interaction_model(self) -> InteractionModel:
        return InteractionModel.EVENT_DRIVEN

    def canonical_phases(self) -> list[str]:
        return list(self.PHASES)

    def search_config(self) -> dict[str, int | float]:
        return {"iterations": 16, "max_depth": 4, "rollout_depth": 3, "c_puct": 1.1}

    def validate_intake(self, intake: IntakeDraft) -> list[str]:
        issues: list[str] = []
        if len(intake.focus_entities) != 2:
            issues.append("election-shock requires exactly two focus entities")
        if intake.current_stage not in self.PHASES:
            issues.append(f"unsupported phase: {intake.current_stage}")
        return issues

    def suggest_related_actors(self, intake: IntakeDraft) -> list[str]:
        return ["Major Donors", "Media", "Undecided Voters", "Party Leadership"]

    def retrieval_filters(self, intake: IntakeDraft) -> dict[str, str]:
        return {"domain": self.slug()}

    def suggest_questions(self) -> list[str]:
        return [
            "Does this shock mainly affect persuasion, turnout, or coalition discipline?",
            "Which voter bloc now matters most?",
        ]

    def extend_schema(self) -> dict[str, Any]:
        return {"poll_margin": "float", "turnout_energy": "float", "message_discipline": "float"}

    def is_terminal(self, state: Any, depth: int) -> bool:
        return getattr(state, "phase", None) == "resolution"

    def propose_actions(self, state: Any) -> list[dict[str, Any]]:
        phase = getattr(state, "phase", None) or "trigger"
        if phase == "trigger":
            return [
                {"action_id": "message-reset", "label": "Message reset", "prior": 0.4, "dependencies": {"fields": ["message_discipline"]}},
                {"action_id": "opposition-attack", "label": "Opposition attack", "prior": 0.35, "dependencies": {"fields": ["poll_margin"]}},
                {"action_id": "ground-game-surge", "label": "Ground game surge", "prior": 0.4, "dependencies": {"fields": ["turnout_energy"]}},
            ]
        if phase == "narrative-fight":
            return [
                {"action_id": "endorsement-push", "label": "Endorsement push", "prior": 0.5},
                {"action_id": "contrast-campaign", "label": "Contrast campaign", "prior": 0.45},
            ]
        if phase == "turnout-drive":
            return [
                {"action_id": "ballot-chase", "label": "Ballot chase", "prior": 0.55},
                {"action_id": "base-consolidation", "label": "Base consolidation", "prior": 0.45},
            ]
        if phase == "coalition-shaping":
            return [
                {"action_id": "targeted-deal", "label": "Targeted deal", "prior": 0.5},
                {"action_id": "discipline-message", "label": "Discipline message", "prior": 0.5},
            ]
        return []

    def sample_transition(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        action_id = action_context.get("action_id") or action_context.get("branch_id")
        margin = numeric_field(state, "poll_margin", 0.0)
        turnout = numeric_field(state, "turnout_energy", 0.5)
        discipline = numeric_field(state, "message_discipline", 0.5)
        phase = getattr(state, "phase", None) or "trigger"

        if phase == "trigger" and action_id == "message-reset":
            return [with_updates(state, phase="narrative-fight", field_updates={"message_discipline": discipline + 0.15, "poll_margin": margin + 0.3})]
        if phase == "trigger" and action_id == "opposition-attack":
            return [with_updates(state, phase="narrative-fight", field_updates={"message_discipline": max(0.0, discipline - 0.1), "poll_margin": margin - 0.4})]
        if phase == "trigger" and action_id == "ground-game-surge":
            return [with_updates(state, phase="turnout-drive", field_updates={"turnout_energy": turnout + 0.18, "poll_margin": margin + 0.1})]
        if phase == "narrative-fight" and action_id == "endorsement-push":
            return [with_updates(state, phase="coalition-shaping", field_updates={"poll_margin": margin + 0.4, "message_discipline": discipline + 0.05})]
        if phase == "narrative-fight" and action_id == "contrast-campaign":
            return [with_updates(state, phase="turnout-drive", field_updates={"turnout_energy": turnout + 0.08, "message_discipline": discipline - 0.02})]
        if phase == "turnout-drive" and action_id == "ballot-chase":
            return [with_updates(state, phase="resolution", field_updates={"turnout_energy": turnout + 0.1, "poll_margin": margin + 0.2})]
        if phase == "turnout-drive" and action_id == "base-consolidation":
            return [with_updates(state, phase="coalition-shaping", field_updates={"turnout_energy": turnout + 0.05, "message_discipline": discipline + 0.05})]
        if phase == "coalition-shaping" and action_id == "targeted-deal":
            return [with_updates(state, phase="resolution", field_updates={"poll_margin": margin + 0.25, "message_discipline": discipline + 0.03})]
        if phase == "coalition-shaping" and action_id == "discipline-message":
            return [with_updates(state, phase="resolution", field_updates={"message_discipline": discipline + 0.08, "turnout_energy": turnout + 0.02})]
        return [state]

    def score_state(self, state: Any) -> dict[str, float]:
        phase = getattr(state, "phase", None) or "trigger"
        margin = numeric_field(state, "poll_margin", 0.0)
        turnout = numeric_field(state, "turnout_energy", 0.5)
        discipline = numeric_field(state, "message_discipline", 0.5)
        volatility = {"trigger": 0.5, "narrative-fight": 0.55, "turnout-drive": 0.35, "coalition-shaping": 0.3, "resolution": 0.2}[phase]
        return {
            "escalation": bounded(volatility + max(0.0, -margin) * 0.08 + (0.5 - discipline) * 0.2),
            "negotiation": bounded(0.2 + discipline * 0.3 + turnout * 0.25 + max(margin, 0.0) * 0.05),
            "economic_stress": bounded(0.25 + volatility * 0.35 + max(0.0, 0.5 - turnout) * 0.2),
        }

    def validate_state(self, state: Any) -> list[str]:
        phase = getattr(state, "phase", None) or ""
        return [] if phase in self.PHASES else [f"unsupported phase: {phase}"]
