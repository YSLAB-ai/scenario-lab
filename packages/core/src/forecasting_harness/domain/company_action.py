from __future__ import annotations

from typing import Any

from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.domain.template_utils import (
    apply_manifest_action_biases,
    apply_manifest_state_overlays,
    any_term_matches,
    bounded,
    compose_signal_text,
    count_term_matches,
    integer_field,
    numeric_field,
    state_signal_text,
    string_field,
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
        return {
            "board_cohesion": "float",
            "cash_runway_months": "int",
            "brand_sentiment": "float",
            "operational_stability": "float",
            "regulatory_pressure": "float",
        }

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

        board_cohesion = 0.5
        board_cohesion -= 0.09 * count_term_matches(
            text,
            ["sudden ceo transition", "board split", "activist pressure", "leadership uncertainty", "credibility pressure"],
        )
        board_cohesion += 0.1 * count_term_matches(
            text,
            ["succession clarity", "board wants stability", "board support", "internal successor", "stability"],
        )
        board_cohesion = bounded(board_cohesion)

        operational_stability = 0.56
        operational_stability -= 0.12 * count_term_matches(
            text,
            ["delivery concerns", "production recovery", "safety scrutiny", "supplier anxiety", "product delays", "quality systems"],
        )
        operational_stability += 0.06 * count_term_matches(text, ["roadmap credibility", "stabilize production", "supplier reassurance"])
        operational_stability = bounded(operational_stability)

        return apply_manifest_state_overlays(
            text=text,
            slug=self.slug(),
            field_values={
            "board_cohesion": round(board_cohesion, 3),
            "cash_runway_months": int(cash_runway),
            "brand_sentiment": round(brand_sentiment, 3),
            "operational_stability": round(operational_stability, 3),
            "regulatory_pressure": round(regulatory_pressure, 3),
            },
        )

    def is_terminal(self, state: Any, depth: int) -> bool:
        return getattr(state, "phase", None) == "resolution"

    def recommend_objective_profile(self, intake: IntakeDraft, state: Any):
        from forecasting_harness.objectives import objective_profile_by_name

        focal_actor = max(
            (
                actor
                for actor in getattr(state, "actors", [])
                if getattr(getattr(actor, "behavior_profile", None), "domestic_sensitivity", None) is not None
            ),
            key=lambda actor: (
                actor.behavior_profile.domestic_sensitivity or 0.0,
                actor.behavior_profile.reputational_sensitivity or 0.0,
                actor.actor_id,
            ),
            default=None,
        )
        if focal_actor is None:
            return self.default_objective_profile()

        board_cohesion = numeric_field(state, "board_cohesion", 0.5)
        brand_sentiment = numeric_field(state, "brand_sentiment", 0.5)
        regulatory_pressure = numeric_field(state, "regulatory_pressure", 0.35)
        text = compose_signal_text(
            intake.event_framing,
            intake.current_development,
            intake.known_constraints,
            intake.known_unknowns,
        )
        if (
            (focal_actor.behavior_profile.domestic_sensitivity or 0.0) >= 0.7
            and any_term_matches(
                text,
                [
                    "board confidence",
                    "leadership credibility",
                    "stakeholder confidence",
                    "ceo transition",
                    "governance crisis",
                    "board cohesion",
                ],
            )
            and (board_cohesion <= 0.45 or brand_sentiment <= 0.45 or regulatory_pressure >= 0.45)
        ):
            return objective_profile_by_name("domestic-politics-first").model_copy(
                update={"focal_actor_id": focal_actor.actor_id}
            )
        return self.default_objective_profile()

    def propose_actions(self, state: Any) -> list[dict[str, Any]]:
        phase = getattr(state, "phase", None) or "trigger"
        board_cohesion = numeric_field(state, "board_cohesion", 0.5)
        runway = integer_field(state, "cash_runway_months", 9)
        sentiment = numeric_field(state, "brand_sentiment", 0.5)
        operational_stability = numeric_field(state, "operational_stability", 0.5)
        pressure = numeric_field(state, "regulatory_pressure", 0.35)
        if phase == "trigger":
            actions = [
                {
                    "action_id": "contain-message",
                    "label": "Contain message",
                    "prior": bounded(0.14 + sentiment * 0.2 + board_cohesion * 0.16),
                    "dependencies": {"fields": ["board_cohesion", "brand_sentiment"]},
                },
                {
                    "action_id": "strategic-review",
                    "label": "Strategic review",
                    "prior": bounded(0.14 + max(0, 12 - runway) * 0.03 + max(0.0, 0.5 - board_cohesion) * 0.22),
                    "dependencies": {"fields": ["board_cohesion", "cash_runway_months"]},
                },
                {
                    "action_id": "operational-pivot",
                    "label": "Operational pivot",
                    "prior": bounded(
                        0.1
                        + pressure * 0.18
                        + max(0.0, 0.5 - operational_stability) * 0.35
                        + max(0, 10 - runway) * 0.02
                    ),
                    "dependencies": {"fields": ["cash_runway_months", "operational_stability", "regulatory_pressure"]},
                },
                {
                    "action_id": "stakeholder-reset",
                    "label": "Stakeholder reset",
                    "prior": bounded(0.08 + max(0.0, 0.6 - sentiment) * 0.18 + board_cohesion * 0.22 + pressure * 0.06),
                    "dependencies": {"fields": ["board_cohesion", "brand_sentiment", "regulatory_pressure"]},
                },
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "board-response":
            actions = [
                {"action_id": "cost-program", "label": "Cost program", "prior": bounded(0.18 + max(0, 8 - runway) * 0.03 + pressure * 0.08)},
                {"action_id": "leadership-reset", "label": "Leadership reset", "prior": bounded(0.12 + max(0.0, 0.5 - board_cohesion) * 0.22 + max(0.0, 0.55 - sentiment) * 0.16)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "market-response":
            actions = [
                {"action_id": "capital-raise", "label": "Capital raise", "prior": bounded(0.12 + max(0, 8 - runway) * 0.04 + pressure * 0.12)},
                {"action_id": "customer-guarantees", "label": "Customer guarantees", "prior": bounded(0.14 + sentiment * 0.14 + operational_stability * 0.2)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "restructuring":
            actions = [
                {"action_id": "asset-sales", "label": "Asset sales", "prior": bounded(0.22 + max(0, 8 - runway) * 0.03 + pressure * 0.12)},
                {"action_id": "stabilize-operations", "label": "Stabilize operations", "prior": bounded(0.18 + max(0.0, 0.5 - operational_stability) * 0.32 + pressure * 0.08)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        return []

    def sample_transition(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        action_id = action_context.get("action_id") or action_context.get("branch_id")
        board_cohesion = numeric_field(state, "board_cohesion", 0.5)
        runway = integer_field(state, "cash_runway_months", 9)
        sentiment = numeric_field(state, "brand_sentiment", 0.5)
        operational_stability = numeric_field(state, "operational_stability", 0.5)
        pressure = numeric_field(state, "regulatory_pressure", 0.35)
        phase = getattr(state, "phase", None) or "trigger"

        if phase == "trigger" and action_id == "contain-message":
            return [
                {
                    "next_state": with_updates(
                        state,
                        phase="market-response",
                        field_updates={
                            "board_cohesion": max(board_cohesion, 0.58),
                            "brand_sentiment": bounded(sentiment + 0.1),
                            "cash_runway_months": runway,
                            "operational_stability": operational_stability,
                        },
                    ),
                    "weight": 0.65,
                    "outcome_id": "message-lands",
                    "outcome_label": "message lands",
                },
                {
                    "next_state": with_updates(
                        state,
                        phase="board-response",
                        field_updates={
                            "board_cohesion": bounded(max(0.0, board_cohesion - 0.06)),
                            "brand_sentiment": max(0.0, sentiment - 0.02),
                            "cash_runway_months": runway - 1,
                            "operational_stability": operational_stability,
                        },
                    ),
                    "weight": 0.35,
                    "outcome_id": "skepticism-persists",
                    "outcome_label": "skepticism persists",
                },
            ]
        if phase == "trigger" and action_id == "strategic-review":
            return [
                with_updates(
                    state,
                    phase="board-response",
                    field_updates={
                        "board_cohesion": bounded(board_cohesion + 0.04),
                        "cash_runway_months": max(1, runway - 1),
                        "operational_stability": operational_stability,
                        "regulatory_pressure": pressure,
                    },
                )
            ]
        if phase == "trigger" and action_id == "operational-pivot":
            return [
                with_updates(
                    state,
                    phase="restructuring",
                    field_updates={
                        "cash_runway_months": max(1, runway - 1),
                        "brand_sentiment": bounded(sentiment - 0.03),
                        "operational_stability": bounded(operational_stability + 0.18),
                        "regulatory_pressure": pressure,
                    },
                )
            ]
        if phase == "trigger" and action_id == "stakeholder-reset":
            return [
                with_updates(
                    state,
                    phase="board-response",
                    field_updates={
                        "board_cohesion": max(board_cohesion, 0.65),
                        "brand_sentiment": bounded(sentiment + (0.08 if board_cohesion >= 0.55 else 0.03)),
                        "operational_stability": operational_stability,
                        "regulatory_pressure": max(0.0, pressure - (0.05 if board_cohesion >= 0.55 else 0.01)),
                    },
                )
            ]
        if phase == "board-response" and action_id == "cost-program":
            return [
                with_updates(
                    state,
                    phase="restructuring",
                    field_updates={
                        "board_cohesion": bounded(max(0.0, board_cohesion - 0.02)),
                        "cash_runway_months": runway + 2,
                        "brand_sentiment": bounded(sentiment - 0.05),
                        "operational_stability": bounded(operational_stability + 0.04),
                    },
                )
            ]
        if phase == "board-response" and action_id == "leadership-reset":
            return [
                with_updates(
                    state,
                    phase="market-response",
                    field_updates={
                        "board_cohesion": bounded(board_cohesion + 0.12),
                        "brand_sentiment": bounded(sentiment + 0.12),
                        "operational_stability": operational_stability,
                        "regulatory_pressure": max(0.0, pressure - 0.05),
                    },
                )
            ]
        if phase == "market-response" and action_id == "capital-raise":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "cash_runway_months": runway + 4,
                        "brand_sentiment": bounded(sentiment + 0.02),
                        "operational_stability": operational_stability,
                    },
                )
            ]
        if phase == "market-response" and action_id == "customer-guarantees":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "brand_sentiment": bounded(sentiment + 0.08),
                        "cash_runway_months": max(1, runway - 1),
                        "operational_stability": bounded(operational_stability + 0.08),
                    },
                )
            ]
        if phase == "restructuring" and action_id == "asset-sales":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "cash_runway_months": runway + 3,
                        "brand_sentiment": bounded(sentiment - 0.02),
                        "operational_stability": bounded(operational_stability + 0.02),
                    },
                )
            ]
        if phase == "restructuring" and action_id == "stabilize-operations":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "brand_sentiment": bounded(sentiment + 0.06),
                        "operational_stability": bounded(operational_stability + 0.16),
                        "regulatory_pressure": max(0.0, pressure - 0.05),
                    },
                )
            ]
        return [state]

    def score_state(self, state: Any) -> dict[str, float]:
        phase = getattr(state, "phase", None) or "trigger"
        board_cohesion = numeric_field(state, "board_cohesion", 0.5)
        runway = integer_field(state, "cash_runway_months", 9)
        sentiment = numeric_field(state, "brand_sentiment", 0.5)
        operational_stability = numeric_field(state, "operational_stability", 0.5)
        pressure = numeric_field(state, "regulatory_pressure", 0.35)
        phase_risk = {"trigger": 0.45, "board-response": 0.4, "market-response": 0.3, "restructuring": 0.5, "resolution": 0.2}[phase]
        return {
            "escalation": bounded(phase_risk + (0.5 - sentiment) * 0.24 + pressure * 0.12 + max(0.0, 0.5 - board_cohesion) * 0.1 + max(0.0, 0.5 - operational_stability) * 0.15),
            "negotiation": bounded(0.18 + sentiment * 0.28 + max(0, runway - 6) * 0.03 + board_cohesion * 0.12 + operational_stability * 0.1),
            "economic_stress": bounded(0.72 - min(runway, 12) / 16 + pressure * 0.18 + max(0.0, 0.5 - operational_stability) * 0.2),
        }

    def score_actor_impacts(self, state: Any) -> dict[str, dict[str, float]]:
        board_cohesion = numeric_field(state, "board_cohesion", 0.5)
        runway = integer_field(state, "cash_runway_months", 9)
        sentiment = numeric_field(state, "brand_sentiment", 0.5)
        operational_stability = numeric_field(state, "operational_stability", 0.5)
        pressure = numeric_field(state, "regulatory_pressure", 0.35)
        actor_impacts: dict[str, dict[str, float]] = {}

        for actor in getattr(state, "actors", []):
            profile = getattr(actor, "behavior_profile", None)
            if profile is None:
                continue

            actor_impacts[actor.actor_id] = {
                "domestic_sensitivity": bounded(
                    (profile.domestic_sensitivity or 0.0)
                    * (0.7 + max(0.0, 0.55 - board_cohesion) * 0.45 + max(0.0, 0.5 - sentiment) * 0.35)
                ),
                "economic_pain_tolerance": bounded(
                    (profile.economic_pain_tolerance or 0.0)
                    * (0.55 + min(runway, 12) / 18 - pressure * 0.15 + operational_stability * 0.05)
                ),
                "negotiation_openness": bounded(
                    (profile.negotiation_openness or 0.0)
                    * (0.7 + board_cohesion * 0.3 + max(0.0, 0.7 - pressure) * 0.2)
                ),
                "reputational_sensitivity": bounded(
                    (profile.reputational_sensitivity or 0.0)
                    * (0.7 + max(0.0, 0.55 - sentiment) * 0.45 + pressure * 0.15)
                ),
                "alliance_dependence": bounded((profile.alliance_dependence or 0.0) * (0.4 + pressure * 0.3)),
                "coercive_bias": bounded(
                    (profile.coercive_bias or 0.0)
                    * (0.45 + pressure * 0.25 + max(0.0, 0.5 - board_cohesion) * 0.2)
                ),
            }

        return actor_impacts

    def validate_state(self, state: Any) -> list[str]:
        phase = getattr(state, "phase", None) or ""
        return [] if phase in self.PHASES else [f"unsupported phase: {phase}"]
