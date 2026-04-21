from __future__ import annotations

from typing import Any

from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.domain.template_utils import (
    any_term_matches,
    bounded,
    compose_signal_text,
    count_term_matches,
    integer_field,
    numeric_field,
    with_updates,
)
from forecasting_harness.workflow.models import IntakeDraft


class CompanyActionPack(DomainPack):
    PHASES = ["trigger", "board-response", "market-response", "restructuring", "resolution"]

    def slug(self) -> str:
        return "company-action"

    def interaction_model(self) -> InteractionModel:
        return InteractionModel.EVENT_DRIVEN

    def canonical_phases(self) -> list[str]:
        return list(self.PHASES)

    def search_config(self) -> dict[str, int | float]:
        return {"iterations": 16, "max_depth": 4, "rollout_depth": 3, "c_puct": 1.1}

    def validate_intake(self, intake: IntakeDraft) -> list[str]:
        issues: list[str] = []
        if len(intake.focus_entities) < 1:
            issues.append("company-action requires at least one focus entity")
        if intake.current_stage not in self.PHASES:
            issues.append(f"unsupported phase: {intake.current_stage}")
        return issues

    def suggest_related_actors(self, intake: IntakeDraft) -> list[str]:
        return ["Board", "Regulator", "Key Customers", "Lead Lenders"]

    def retrieval_filters(self, intake: IntakeDraft) -> dict[str, str]:
        return {"domain": self.slug()}

    def suggest_questions(self) -> list[str]:
        return [
            "Is the main pressure liquidity, reputation, or regulation?",
            "Which stakeholder can force the next company move?",
        ]

    def extend_schema(self) -> dict[str, Any]:
        return {"cash_runway_months": "int", "brand_sentiment": "float", "regulatory_pressure": "float"}

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

        cash_runway = 18
        cash_runway -= 4 * count_term_matches(
            text,
            ["weak quarter", "margin pressure", "funding pressure", "cash burn", "cash preservation"],
        )
        cash_runway -= 2 * count_term_matches(text, ["product delays", "delivery concerns", "supplier reassurance"])
        cash_runway += 3 * count_term_matches(text, ["balance sheet", "liquidity", "capital raise"])
        cash_runway = max(3, min(48, cash_runway))

        brand_sentiment = 0.58
        brand_sentiment -= 0.08 * count_term_matches(
            text,
            ["investor concern", "product delays", "delivery concerns", "customer backlash", "credibility pressure"],
        )
        brand_sentiment += 0.04 * count_term_matches(text, ["succession clarity", "supplier reassurance", "stabilize messaging"])
        brand_sentiment = bounded(brand_sentiment)

        regulatory_pressure = 0.25
        regulatory_pressure += 0.12 * count_term_matches(
            text,
            ["regulatory scrutiny", "safety scrutiny", "enforcement", "investigation", "agency pressure"],
        )
        regulatory_pressure = bounded(regulatory_pressure)

        return {
            "cash_runway_months": int(cash_runway),
            "brand_sentiment": round(brand_sentiment, 3),
            "regulatory_pressure": round(regulatory_pressure, 3),
        }

    def is_terminal(self, state: Any, depth: int) -> bool:
        return getattr(state, "phase", None) == "resolution"

    def propose_actions(self, state: Any) -> list[dict[str, Any]]:
        phase = getattr(state, "phase", None) or "trigger"
        if phase == "trigger":
            return [
                {"action_id": "contain-message", "label": "Contain message", "prior": 0.45, "dependencies": {"fields": ["brand_sentiment"]}},
                {"action_id": "strategic-review", "label": "Strategic review", "prior": 0.35, "dependencies": {"fields": ["cash_runway_months"]}},
                {"action_id": "operational-pivot", "label": "Operational pivot", "prior": 0.3, "dependencies": {"fields": ["cash_runway_months", "regulatory_pressure"]}},
            ]
        if phase == "board-response":
            return [
                {"action_id": "cost-program", "label": "Cost program", "prior": 0.55},
                {"action_id": "leadership-reset", "label": "Leadership reset", "prior": 0.4},
            ]
        if phase == "market-response":
            return [
                {"action_id": "capital-raise", "label": "Capital raise", "prior": 0.5},
                {"action_id": "customer-guarantees", "label": "Customer guarantees", "prior": 0.45},
            ]
        if phase == "restructuring":
            return [
                {"action_id": "asset-sales", "label": "Asset sales", "prior": 0.55},
                {"action_id": "stabilize-operations", "label": "Stabilize operations", "prior": 0.45},
            ]
        return []

    def sample_transition(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        action_id = action_context.get("action_id") or action_context.get("branch_id")
        runway = integer_field(state, "cash_runway_months", 9)
        sentiment = numeric_field(state, "brand_sentiment", 0.5)
        pressure = numeric_field(state, "regulatory_pressure", 0.35)
        phase = getattr(state, "phase", None) or "trigger"

        if phase == "trigger" and action_id == "contain-message":
            return [with_updates(state, phase="market-response", field_updates={"brand_sentiment": sentiment + 0.1, "cash_runway_months": runway})]
        if phase == "trigger" and action_id == "strategic-review":
            return [with_updates(state, phase="board-response", field_updates={"cash_runway_months": max(1, runway - 1), "regulatory_pressure": pressure})]
        if phase == "trigger" and action_id == "operational-pivot":
            return [with_updates(state, phase="restructuring", field_updates={"cash_runway_months": max(1, runway - 2), "brand_sentiment": sentiment - 0.05})]
        if phase == "board-response" and action_id == "cost-program":
            return [with_updates(state, phase="restructuring", field_updates={"cash_runway_months": runway + 2, "brand_sentiment": sentiment - 0.05})]
        if phase == "board-response" and action_id == "leadership-reset":
            return [with_updates(state, phase="market-response", field_updates={"brand_sentiment": sentiment + 0.12, "regulatory_pressure": max(0.0, pressure - 0.05)})]
        if phase == "market-response" and action_id == "capital-raise":
            return [with_updates(state, phase="resolution", field_updates={"cash_runway_months": runway + 4, "brand_sentiment": sentiment + 0.02})]
        if phase == "market-response" and action_id == "customer-guarantees":
            return [with_updates(state, phase="resolution", field_updates={"brand_sentiment": sentiment + 0.08, "cash_runway_months": max(1, runway - 1)})]
        if phase == "restructuring" and action_id == "asset-sales":
            return [with_updates(state, phase="resolution", field_updates={"cash_runway_months": runway + 3, "brand_sentiment": sentiment - 0.02})]
        if phase == "restructuring" and action_id == "stabilize-operations":
            return [with_updates(state, phase="resolution", field_updates={"brand_sentiment": sentiment + 0.06, "regulatory_pressure": max(0.0, pressure - 0.05)})]
        return [state]

    def score_state(self, state: Any) -> dict[str, float]:
        phase = getattr(state, "phase", None) or "trigger"
        runway = integer_field(state, "cash_runway_months", 9)
        sentiment = numeric_field(state, "brand_sentiment", 0.5)
        pressure = numeric_field(state, "regulatory_pressure", 0.35)
        phase_risk = {"trigger": 0.45, "board-response": 0.4, "market-response": 0.3, "restructuring": 0.5, "resolution": 0.2}[phase]
        return {
            "escalation": bounded(phase_risk + (0.5 - sentiment) * 0.3 + pressure * 0.15),
            "negotiation": bounded(0.25 + sentiment * 0.35 + max(0, runway - 6) * 0.03),
            "economic_stress": bounded(0.75 - min(runway, 12) / 16 + pressure * 0.2),
        }

    def validate_state(self, state: Any) -> list[str]:
        phase = getattr(state, "phase", None) or ""
        return [] if phase in self.PHASES else [f"unsupported phase: {phase}"]
