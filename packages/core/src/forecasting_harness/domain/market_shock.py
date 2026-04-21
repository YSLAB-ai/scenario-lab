from __future__ import annotations

from typing import Any

from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.domain.template_utils import bounded, compose_signal_text, count_term_matches, numeric_field, with_updates
from forecasting_harness.workflow.models import IntakeDraft


class MarketShockPack(DomainPack):
    PHASES = ["trigger", "repricing", "policy-response", "liquidity-stabilization", "resolution"]

    def slug(self) -> str:
        return "market-shock"

    def interaction_model(self) -> InteractionModel:
        return InteractionModel.EVENT_DRIVEN

    def canonical_phases(self) -> list[str]:
        return list(self.PHASES)

    def search_config(self) -> dict[str, int | float]:
        return {"iterations": 18, "max_depth": 4, "rollout_depth": 3, "c_puct": 1.15}

    def validate_intake(self, intake: IntakeDraft) -> list[str]:
        issues: list[str] = []
        if len(intake.focus_entities) < 2:
            issues.append("market-shock requires at least two focus entities")
        if intake.current_stage not in self.PHASES:
            issues.append(f"unsupported phase: {intake.current_stage}")
        return issues

    def suggest_related_actors(self, intake: IntakeDraft) -> list[str]:
        return ["Treasury", "Money Market Funds", "Primary Dealers", "Foreign Central Banks"]

    def retrieval_filters(self, intake: IntakeDraft) -> dict[str, str]:
        return {"domain": self.slug()}

    def suggest_questions(self) -> list[str]:
        return [
            "Is the shock mainly a rates shock, liquidity shock, or credibility shock?",
            "Which policy actor can change expectations fastest?",
        ]

    def extend_schema(self) -> dict[str, Any]:
        return {"liquidity_stress": "float", "rate_pressure": "float", "policy_credibility": "float"}

    def infer_pack_fields(self, intake: IntakeDraft, assumptions: Any, approved_evidence_items: list[Any]) -> dict[str, Any]:
        evidence_passages = [passage for item in approved_evidence_items for passage in item.raw_passages]
        text = compose_signal_text(
            intake.event_framing,
            intake.current_development,
            intake.known_constraints,
            intake.known_unknowns,
            assumptions.summary,
            evidence_passages,
        )

        liquidity_stress = 0.45 + 0.1 * count_term_matches(
            text,
            ["liquidity", "funding market", "credit spreads", "market functioning", "deleveraging"],
        )
        rate_pressure = 0.5 + 0.1 * count_term_matches(
            text,
            ["rate hike", "hawkish", "repricing", "yield shock", "inflation credibility"],
        )
        rate_pressure -= 0.08 * count_term_matches(text, ["rate cut", "easing", "swap lines"])
        policy_credibility = 0.5 + 0.06 * count_term_matches(
            text,
            ["credibility restored", "clear guidance", "market functioning"],
        )
        policy_credibility -= 0.08 * count_term_matches(text, ["instability", "surprise decision", "wait and see"])

        return {
            "liquidity_stress": round(bounded(liquidity_stress), 3),
            "rate_pressure": round(bounded(rate_pressure), 3),
            "policy_credibility": round(bounded(policy_credibility), 3),
        }

    def is_terminal(self, state: Any, depth: int) -> bool:
        return getattr(state, "phase", None) == "resolution"

    def propose_actions(self, state: Any) -> list[dict[str, Any]]:
        phase = getattr(state, "phase", None) or "trigger"
        liquidity = numeric_field(state, "liquidity_stress", 0.45)
        rates = numeric_field(state, "rate_pressure", 0.55)
        credibility = numeric_field(state, "policy_credibility", 0.5)
        if phase == "trigger":
            return [
                {"action_id": "hawkish-guidance", "label": "Hawkish guidance", "prior": bounded(0.18 + rates * 0.25), "dependencies": {"fields": ["rate_pressure", "policy_credibility"]}},
                {"action_id": "emergency-liquidity", "label": "Emergency liquidity", "prior": bounded(0.22 + liquidity * 0.25), "dependencies": {"fields": ["liquidity_stress"]}},
                {"action_id": "wait-and-see", "label": "Wait and see", "prior": bounded(0.12 + max(0.0, credibility - 0.35) * 0.25), "dependencies": {"fields": ["policy_credibility"]}},
                {"action_id": "coordinated-backstop", "label": "Coordinated backstop", "prior": bounded(0.16 + liquidity * 0.15 + credibility * 0.1), "dependencies": {"fields": ["liquidity_stress", "policy_credibility"]}},
            ]
        if phase == "repricing":
            return [
                {"action_id": "verbal-backstop", "label": "Verbal backstop", "prior": 0.5},
                {"action_id": "forced-deleveraging", "label": "Forced deleveraging", "prior": 0.4},
            ]
        if phase == "policy-response":
            return [
                {"action_id": "swap-lines", "label": "Swap lines", "prior": 0.5},
                {"action_id": "rate-cut-path", "label": "Rate cut path", "prior": 0.45},
            ]
        if phase == "liquidity-stabilization":
            return [
                {"action_id": "restore-function", "label": "Restore function", "prior": 0.55},
                {"action_id": "moral-hazard-pushback", "label": "Moral hazard pushback", "prior": 0.35},
            ]
        return []

    def sample_transition(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        action_id = action_context.get("action_id") or action_context.get("branch_id")
        liquidity = numeric_field(state, "liquidity_stress", 0.45)
        rates = numeric_field(state, "rate_pressure", 0.55)
        credibility = numeric_field(state, "policy_credibility", 0.5)
        phase = getattr(state, "phase", None) or "trigger"

        if phase == "trigger" and action_id == "hawkish-guidance":
            return [with_updates(state, phase="repricing", field_updates={"rate_pressure": rates + 0.12, "policy_credibility": credibility + 0.05})]
        if phase == "trigger" and action_id == "emergency-liquidity":
            return [with_updates(state, phase="policy-response", field_updates={"liquidity_stress": max(0.0, liquidity - 0.18), "policy_credibility": credibility + 0.08})]
        if phase == "trigger" and action_id == "wait-and-see":
            return [with_updates(state, phase="repricing", field_updates={"liquidity_stress": liquidity + 0.1, "policy_credibility": credibility - 0.08})]
        if phase == "trigger" and action_id == "coordinated-backstop":
            return [
                with_updates(
                    state,
                    phase="policy-response",
                    field_updates={"liquidity_stress": max(0.0, liquidity - 0.12), "policy_credibility": credibility + 0.12},
                )
            ]
        if phase == "repricing" and action_id == "verbal-backstop":
            return [with_updates(state, phase="liquidity-stabilization", field_updates={"liquidity_stress": max(0.0, liquidity - 0.1), "policy_credibility": credibility + 0.08})]
        if phase == "repricing" and action_id == "forced-deleveraging":
            return [with_updates(state, phase="liquidity-stabilization", field_updates={"liquidity_stress": liquidity + 0.12, "rate_pressure": rates + 0.05})]
        if phase == "policy-response" and action_id == "swap-lines":
            return [with_updates(state, phase="resolution", field_updates={"liquidity_stress": max(0.0, liquidity - 0.2), "policy_credibility": credibility + 0.06})]
        if phase == "policy-response" and action_id == "rate-cut-path":
            return [with_updates(state, phase="liquidity-stabilization", field_updates={"rate_pressure": max(0.0, rates - 0.15), "policy_credibility": credibility + 0.04})]
        if phase == "liquidity-stabilization" and action_id == "restore-function":
            return [with_updates(state, phase="resolution", field_updates={"liquidity_stress": max(0.0, liquidity - 0.15), "rate_pressure": max(0.0, rates - 0.05)})]
        if phase == "liquidity-stabilization" and action_id == "moral-hazard-pushback":
            return [with_updates(state, phase="resolution", field_updates={"policy_credibility": credibility - 0.02, "liquidity_stress": max(0.0, liquidity - 0.05)})]
        return [state]

    def score_state(self, state: Any) -> dict[str, float]:
        phase = getattr(state, "phase", None) or "trigger"
        liquidity = numeric_field(state, "liquidity_stress", 0.45)
        rates = numeric_field(state, "rate_pressure", 0.55)
        credibility = numeric_field(state, "policy_credibility", 0.5)
        instability = {"trigger": 0.45, "repricing": 0.65, "policy-response": 0.4, "liquidity-stabilization": 0.3, "resolution": 0.15}[phase]
        return {
            "escalation": bounded(instability + liquidity * 0.25 + max(0.0, rates - 0.5) * 0.2),
            "negotiation": bounded(0.2 + credibility * 0.35 + max(0.0, 0.6 - liquidity) * 0.2),
            "economic_stress": bounded(0.25 + liquidity * 0.45 + rates * 0.2),
        }

    def validate_state(self, state: Any) -> list[str]:
        phase = getattr(state, "phase", None) or ""
        return [] if phase in self.PHASES else [f"unsupported phase: {phase}"]
