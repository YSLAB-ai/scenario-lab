from __future__ import annotations

from typing import Any

from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.domain.template_utils import (
    apply_manifest_action_biases,
    apply_manifest_state_overlays,
    bounded,
    compose_signal_text,
    count_term_matches,
    numeric_field,
    state_signal_text,
    with_updates,
)
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
        return {
            "contagion_risk": "float",
            "liquidity_stress": "float",
            "policy_credibility": "float",
            "policy_optionality": "float",
            "rate_pressure": "float",
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

        contagion_risk = 0.35 + 0.12 * count_term_matches(
            text,
            ["credit spreads", "cross-asset", "spillover", "funding market", "dealers", "global equities"],
        )
        contagion_risk += 0.08 * count_term_matches(text, ["money market", "treasury market", "banks"])
        contagion_risk += 0.06 * count_term_matches(text, ["confidence crisis", "depositor confidence", "bank failures"])

        policy_optionality = 0.3
        policy_optionality += 0.12 * count_term_matches(
            text,
            ["swap lines", "market functioning", "facility", "liquidity tools", "backstop", "authorities will prioritize"],
        )
        policy_optionality += 0.12 * count_term_matches(
            text,
            [
                "forced takeover",
                "takeover",
                "merger",
                "receivership",
                "transfer",
                "guarantees",
                "support measures",
                "protect depositors",
            ],
        )
        policy_optionality -= 0.08 * count_term_matches(text, ["credibility at stake", "emergency rate hike", "surprise decision"])

        return apply_manifest_state_overlays(
            text=text,
            slug=self.slug(),
            field_values={
            "contagion_risk": round(bounded(contagion_risk), 3),
            "liquidity_stress": round(bounded(liquidity_stress), 3),
            "rate_pressure": round(bounded(rate_pressure), 3),
            "policy_credibility": round(bounded(policy_credibility), 3),
            "policy_optionality": round(bounded(policy_optionality), 3),
            },
        )

    def is_terminal(self, state: Any, depth: int) -> bool:
        return getattr(state, "phase", None) == "resolution"

    def propose_actions(self, state: Any) -> list[dict[str, Any]]:
        phase = getattr(state, "phase", None) or "trigger"
        contagion = numeric_field(state, "contagion_risk", 0.35)
        liquidity = numeric_field(state, "liquidity_stress", 0.45)
        rates = numeric_field(state, "rate_pressure", 0.55)
        credibility = numeric_field(state, "policy_credibility", 0.5)
        optionality = numeric_field(state, "policy_optionality", 0.3)
        backstop_signal = count_term_matches(
            state_signal_text(state),
            [
                "forced takeover",
                "takeover",
                "merger",
                "receivership",
                "transfer",
                "guarantees",
                "support measures",
                "protect depositors",
            ],
        )
        if phase == "trigger":
            actions = [
                {
                    "action_id": "hawkish-guidance",
                    "label": "Hawkish guidance",
                    "prior": bounded(0.1 + rates * 0.22 + credibility * 0.1 - optionality * 0.08),
                    "dependencies": {"fields": ["policy_credibility", "policy_optionality", "rate_pressure"]},
                },
                {
                    "action_id": "emergency-liquidity",
                    "label": "Emergency liquidity",
                    "prior": bounded(0.14 + liquidity * 0.18 + contagion * 0.18 + optionality * 0.14 - backstop_signal * 0.04),
                    "dependencies": {"fields": ["contagion_risk", "liquidity_stress", "policy_optionality"]},
                },
                {
                    "action_id": "wait-and-see",
                    "label": "Wait and see",
                    "prior": bounded(0.08 + max(0.0, credibility - 0.4) * 0.18 - contagion * 0.12),
                    "dependencies": {"fields": ["contagion_risk", "policy_credibility"]},
                },
                {
                    "action_id": "coordinated-backstop",
                    "label": "Coordinated backstop",
                    "prior": bounded(
                        0.1
                        + liquidity * 0.12
                        + contagion * 0.16
                        + credibility * 0.08
                        + optionality * 0.16
                        + backstop_signal * 0.14
                    ),
                    "dependencies": {"fields": ["contagion_risk", "liquidity_stress", "policy_credibility", "policy_optionality"]},
                },
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "repricing":
            actions = [
                {"action_id": "verbal-backstop", "label": "Verbal backstop", "prior": bounded(0.15 + credibility * 0.18 + optionality * 0.16)},
                {"action_id": "forced-deleveraging", "label": "Forced deleveraging", "prior": bounded(0.12 + liquidity * 0.14 + contagion * 0.18)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "policy-response":
            actions = [
                {"action_id": "swap-lines", "label": "Swap lines", "prior": bounded(0.16 + optionality * 0.22 + contagion * 0.14)},
                {"action_id": "rate-cut-path", "label": "Rate cut path", "prior": bounded(0.14 + optionality * 0.16 + max(0.0, rates - 0.55) * 0.18)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "liquidity-stabilization":
            actions = [
                {"action_id": "restore-function", "label": "Restore function", "prior": bounded(0.18 + liquidity * 0.08 + optionality * 0.18)},
                {"action_id": "moral-hazard-pushback", "label": "Moral hazard pushback", "prior": bounded(0.1 + credibility * 0.12 + max(0.0, 0.5 - optionality) * 0.14)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        return []

    def sample_transition(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        action_id = action_context.get("action_id") or action_context.get("branch_id")
        contagion = numeric_field(state, "contagion_risk", 0.35)
        liquidity = numeric_field(state, "liquidity_stress", 0.45)
        rates = numeric_field(state, "rate_pressure", 0.55)
        credibility = numeric_field(state, "policy_credibility", 0.5)
        optionality = numeric_field(state, "policy_optionality", 0.3)
        backstop_signal = count_term_matches(
            state_signal_text(state),
            [
                "forced takeover",
                "takeover",
                "merger",
                "receivership",
                "transfer",
                "guarantees",
                "support measures",
                "protect depositors",
            ],
        )
        phase = getattr(state, "phase", None) or "trigger"

        if phase == "trigger" and action_id == "hawkish-guidance":
            return [
                with_updates(
                    state,
                    phase="repricing",
                    field_updates={
                        "contagion_risk": bounded(contagion + 0.06),
                        "rate_pressure": rates + 0.12,
                        "policy_credibility": credibility + 0.05,
                        "policy_optionality": max(0.0, optionality - 0.06),
                    },
                )
            ]
        if phase == "trigger" and action_id == "emergency-liquidity":
            return [
                with_updates(
                    state,
                    phase="policy-response",
                    field_updates={
                        "contagion_risk": max(0.0, contagion - 0.08),
                        "liquidity_stress": max(0.0, liquidity - 0.18),
                        "policy_credibility": credibility + 0.08,
                        "policy_optionality": optionality + 0.04,
                    },
                )
            ]
        if phase == "trigger" and action_id == "wait-and-see":
            return [
                with_updates(
                    state,
                    phase="repricing",
                    field_updates={
                        "contagion_risk": bounded(contagion + 0.1),
                        "liquidity_stress": liquidity + 0.1,
                        "policy_credibility": credibility - 0.08,
                        "policy_optionality": max(0.0, optionality - 0.04),
                    },
                )
            ]
        if phase == "trigger" and action_id == "coordinated-backstop":
            return [
                with_updates(
                    state,
                    phase="policy-response",
                    field_updates={
                        "contagion_risk": max(0.0, contagion - (0.14 if backstop_signal >= 2 else 0.1)),
                        "liquidity_stress": max(0.0, liquidity - (0.15 if backstop_signal >= 2 else 0.12)),
                        "policy_credibility": credibility + (0.14 if backstop_signal >= 2 else 0.12),
                        "policy_optionality": optionality + 0.08,
                    },
                )
            ]
        if phase == "repricing" and action_id == "verbal-backstop":
            return [
                with_updates(
                    state,
                    phase="liquidity-stabilization",
                    field_updates={
                        "contagion_risk": max(0.0, contagion - 0.06),
                        "liquidity_stress": max(0.0, liquidity - 0.1),
                        "policy_credibility": credibility + 0.08,
                        "policy_optionality": optionality + 0.04,
                    },
                )
            ]
        if phase == "repricing" and action_id == "forced-deleveraging":
            return [
                with_updates(
                    state,
                    phase="liquidity-stabilization",
                    field_updates={
                        "contagion_risk": bounded(contagion + 0.08),
                        "liquidity_stress": liquidity + 0.12,
                        "rate_pressure": rates + 0.05,
                    },
                )
            ]
        if phase == "policy-response" and action_id == "swap-lines":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "contagion_risk": max(0.0, contagion - 0.12),
                        "liquidity_stress": max(0.0, liquidity - 0.2),
                        "policy_credibility": credibility + 0.06,
                        "policy_optionality": optionality + 0.05,
                    },
                )
            ]
        if phase == "policy-response" and action_id == "rate-cut-path":
            return [
                with_updates(
                    state,
                    phase="liquidity-stabilization",
                    field_updates={
                        "liquidity_stress": max(0.0, liquidity - 0.08),
                        "rate_pressure": max(0.0, rates - 0.15),
                        "policy_credibility": credibility + 0.04,
                    },
                )
            ]
        if phase == "liquidity-stabilization" and action_id == "restore-function":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "contagion_risk": max(0.0, contagion - 0.08),
                        "liquidity_stress": max(0.0, liquidity - 0.15),
                        "rate_pressure": max(0.0, rates - 0.05),
                    },
                )
            ]
        if phase == "liquidity-stabilization" and action_id == "moral-hazard-pushback":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "policy_credibility": credibility - 0.02,
                        "liquidity_stress": max(0.0, liquidity - 0.05),
                        "policy_optionality": max(0.0, optionality - 0.06),
                    },
                )
            ]
        return [state]

    def score_state(self, state: Any) -> dict[str, float]:
        phase = getattr(state, "phase", None) or "trigger"
        contagion = numeric_field(state, "contagion_risk", 0.35)
        liquidity = numeric_field(state, "liquidity_stress", 0.45)
        rates = numeric_field(state, "rate_pressure", 0.55)
        credibility = numeric_field(state, "policy_credibility", 0.5)
        optionality = numeric_field(state, "policy_optionality", 0.3)
        instability = {"trigger": 0.45, "repricing": 0.65, "policy-response": 0.4, "liquidity-stabilization": 0.3, "resolution": 0.15}[phase]
        return {
            "escalation": bounded(instability + liquidity * 0.22 + contagion * 0.2 + max(0.0, rates - 0.5) * 0.18),
            "negotiation": bounded(0.16 + credibility * 0.28 + optionality * 0.18 + max(0.0, 0.6 - liquidity) * 0.18),
            "economic_stress": bounded(0.22 + liquidity * 0.4 + rates * 0.18 + contagion * 0.14),
        }

    def validate_state(self, state: Any) -> list[str]:
        phase = getattr(state, "phase", None) or ""
        return [] if phase in self.PHASES else [f"unsupported phase: {phase}"]
