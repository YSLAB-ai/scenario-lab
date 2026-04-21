from __future__ import annotations

from typing import Any

from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.domain.template_utils import bounded, numeric_field, string_field, with_updates
from forecasting_harness.workflow.models import IntakeDraft


class RegulatoryEnforcementPack(DomainPack):
    PHASES = ["trigger", "inquiry", "negotiation", "remedy", "resolution"]

    def slug(self) -> str:
        return "regulatory-enforcement"

    def interaction_model(self) -> InteractionModel:
        return InteractionModel.EVENT_DRIVEN

    def canonical_phases(self) -> list[str]:
        return list(self.PHASES)

    def search_config(self) -> dict[str, int | float]:
        return {"iterations": 16, "max_depth": 4, "rollout_depth": 3, "c_puct": 1.1}

    def validate_intake(self, intake: IntakeDraft) -> list[str]:
        issues: list[str] = []
        if len(intake.focus_entities) < 2:
            issues.append("regulatory-enforcement requires at least two focus entities")
        if intake.current_stage not in self.PHASES:
            issues.append(f"unsupported phase: {intake.current_stage}")
        return issues

    def suggest_related_actors(self, intake: IntakeDraft) -> list[str]:
        return ["External Counsel", "Independent Monitor", "State Attorneys General", "Industry Peers"]

    def retrieval_filters(self, intake: IntakeDraft) -> dict[str, str]:
        return {"domain": self.slug()}

    def suggest_questions(self) -> list[str]:
        return [
            "Is the likely path settlement, litigation, or remediation?",
            "What internal control weakness matters most?",
        ]

    def extend_schema(self) -> dict[str, Any]:
        return {"enforcement_momentum": "float", "compliance_posture": "str", "public_attention": "float"}

    def is_terminal(self, state: Any, depth: int) -> bool:
        return getattr(state, "phase", None) == "resolution"

    def propose_actions(self, state: Any) -> list[dict[str, Any]]:
        phase = getattr(state, "phase", None) or "trigger"
        posture = string_field(state, "compliance_posture", "mixed")
        litigate_prior = 0.4 if posture == "adversarial" else 0.25
        if phase == "trigger":
            return [
                {"action_id": "cooperate-early", "label": "Cooperate early", "prior": 0.45, "dependencies": {"fields": ["compliance_posture"]}},
                {"action_id": "litigate", "label": "Litigate", "prior": litigate_prior, "dependencies": {"fields": ["compliance_posture", "enforcement_momentum"]}},
                {"action_id": "internal-remediation", "label": "Internal remediation", "prior": 0.35, "dependencies": {"fields": ["public_attention"]}},
            ]
        if phase == "inquiry":
            return [
                {"action_id": "narrow-scope", "label": "Narrow scope", "prior": 0.45},
                {"action_id": "expand-record", "label": "Expand record", "prior": 0.4},
            ]
        if phase == "negotiation":
            return [
                {"action_id": "settlement-framework", "label": "Settlement framework", "prior": 0.55},
                {"action_id": "contest-findings", "label": "Contest findings", "prior": 0.35},
            ]
        if phase == "remedy":
            return [
                {"action_id": "consent-order", "label": "Consent order", "prior": 0.5},
                {"action_id": "monitor-plan", "label": "Monitor plan", "prior": 0.45},
            ]
        return []

    def sample_transition(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        action_id = action_context.get("action_id") or action_context.get("branch_id")
        momentum = numeric_field(state, "enforcement_momentum", 0.5)
        attention = numeric_field(state, "public_attention", 0.45)
        phase = getattr(state, "phase", None) or "trigger"

        if phase == "trigger" and action_id == "cooperate-early":
            return [with_updates(state, phase="inquiry", field_updates={"enforcement_momentum": max(0.0, momentum - 0.05), "public_attention": attention - 0.02})]
        if phase == "trigger" and action_id == "litigate":
            return [with_updates(state, phase="inquiry", field_updates={"enforcement_momentum": momentum + 0.1, "public_attention": attention + 0.08})]
        if phase == "trigger" and action_id == "internal-remediation":
            return [with_updates(state, phase="negotiation", field_updates={"enforcement_momentum": max(0.0, momentum - 0.08), "public_attention": attention})]
        if phase == "inquiry" and action_id == "narrow-scope":
            return [with_updates(state, phase="negotiation", field_updates={"enforcement_momentum": max(0.0, momentum - 0.05), "public_attention": attention - 0.03})]
        if phase == "inquiry" and action_id == "expand-record":
            return [with_updates(state, phase="remedy", field_updates={"enforcement_momentum": momentum + 0.08, "public_attention": attention + 0.05})]
        if phase == "negotiation" and action_id == "settlement-framework":
            return [with_updates(state, phase="resolution", field_updates={"enforcement_momentum": max(0.0, momentum - 0.12), "public_attention": attention - 0.05})]
        if phase == "negotiation" and action_id == "contest-findings":
            return [with_updates(state, phase="remedy", field_updates={"enforcement_momentum": momentum + 0.05, "public_attention": attention + 0.04})]
        if phase == "remedy" and action_id == "consent-order":
            return [with_updates(state, phase="resolution", field_updates={"enforcement_momentum": max(0.0, momentum - 0.15), "public_attention": attention - 0.05})]
        if phase == "remedy" and action_id == "monitor-plan":
            return [with_updates(state, phase="resolution", field_updates={"enforcement_momentum": max(0.0, momentum - 0.1), "public_attention": attention})]
        return [state]

    def score_state(self, state: Any) -> dict[str, float]:
        phase = getattr(state, "phase", None) or "trigger"
        momentum = numeric_field(state, "enforcement_momentum", 0.5)
        attention = numeric_field(state, "public_attention", 0.45)
        phase_pressure = {"trigger": 0.45, "inquiry": 0.5, "negotiation": 0.35, "remedy": 0.55, "resolution": 0.2}[phase]
        return {
            "escalation": bounded(phase_pressure + momentum * 0.2 + attention * 0.1),
            "negotiation": bounded(0.2 + max(0.0, 0.65 - momentum) * 0.35 + max(0.0, 0.55 - attention) * 0.15),
            "economic_stress": bounded(0.25 + momentum * 0.35 + attention * 0.15),
        }

    def validate_state(self, state: Any) -> list[str]:
        phase = getattr(state, "phase", None) or ""
        return [] if phase in self.PHASES else [f"unsupported phase: {phase}"]
