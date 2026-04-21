from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.domain.template_utils import (
    any_term_matches,
    apply_manifest_action_biases,
    apply_manifest_state_overlays,
    bounded,
    compose_signal_text,
    count_term_matches,
    state_signal_text,
)
from forecasting_harness.workflow.models import IntakeDraft

if TYPE_CHECKING:
    from forecasting_harness.models import BeliefState


def _anchor_timestamp(state: Any) -> datetime:
    fields = getattr(state, "fields", {})
    if fields:
        timestamp = getattr(next(iter(fields.values())), "last_updated_at", None)
        if isinstance(timestamp, datetime):
            return timestamp
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
    from forecasting_harness.models import BeliefField

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


def _normalized_weights(*values: float) -> list[float]:
    safe_values = [max(0.01, value) for value in values]
    total = sum(safe_values)
    return [value / total for value in safe_values]


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
        return {
            "alliance_pressure": "float",
            "geographic_flashpoint": "float",
            "mediation_window": "float",
            "military_posture": "str",
            "leader_style": "str",
            "tension_index": "float",
            "diplomatic_channel": "float",
        }

    def infer_pack_fields(self, intake: IntakeDraft, assumptions: Any, approved_evidence_items: list[Any]) -> dict[str, Any]:
        evidence_passages = [passage for item in approved_evidence_items for passage in item.raw_passages]
        text = compose_signal_text(
            intake.event_framing,
            intake.current_development,
            intake.focus_entities,
            intake.known_constraints,
            intake.known_unknowns,
            intake.suggested_entities,
            assumptions.summary,
            evidence_passages,
        )

        if any_term_matches(text, ["backchannel", "restraint", "talks", "ceasefire", "de-escalation"]):
            leader_style = "cautious"
        elif any_term_matches(text, ["retaliation", "mobilization", "threat", "intercept", "airstrike"]):
            leader_style = "hawkish"
        else:
            leader_style = "cautious"

        if any_term_matches(text, ["naval transit", "taiwan strait", "intercept", "contested"]):
            military_posture = "contested"
        elif any_term_matches(text, ["mobilization", "deployment", "high alert", "readiness"]):
            military_posture = "high-alert"
        elif any_term_matches(text, ["carrier", "forward", "naval deployments"]):
            military_posture = "forward-deployed"
        else:
            military_posture = "reserve"

        tension_index = 0.42 + 0.1 * count_term_matches(
            text,
            ["retaliation", "mobilization", "threat", "strike", "missile", "intercept", "high alert", "border attack", "shipping strike"],
        )
        tension_index -= 0.06 * count_term_matches(text, ["backchannel", "restraint", "talks", "ceasefire"])

        diplomatic_channel = 0.32 + 0.1 * count_term_matches(
            text,
            ["backchannel", "restraint", "talks", "ceasefire", "diplomacy", "mediators", "emergency diplomacy", "partially open"],
        )
        diplomatic_channel -= 0.05 * count_term_matches(text, ["threat", "retaliation", "intercept"])

        alliance_pressure = 0.08
        alliance_pressure += 0.14 * count_term_matches(
            text,
            ["allies", "alliance commitments", "security commitments", "treaty", "coalition", "joint statement"],
        )
        alliance_pressure += 0.08 * count_term_matches(text, ["united states", "israel", "gulf states", "taiwan"])
        alliance_pressure -= 0.04 * count_term_matches(text, ["independent", "unilateral"])

        mediation_window = 0.18
        mediation_window += 0.14 * count_term_matches(
            text,
            ["backchannel", "mediators", "restraint", "emergency diplomacy", "talks", "diplomatic channels", "partially open"],
        )
        mediation_window -= 0.06 * count_term_matches(text, ["retaliation", "intercept threats", "mobilization", "high alert"])

        geographic_flashpoint = 0.22
        geographic_flashpoint += 0.12 * count_term_matches(
            text,
            ["taiwan strait", "gulf shipping", "border attack", "intercept", "naval transit", "shipping", "border", "missile readiness"],
        )
        geographic_flashpoint += 0.08 * count_term_matches(text, ["militant attack", "proxy militias", "carrier", "strait"])

        return apply_manifest_state_overlays(
            text=text,
            slug=self.slug(),
            field_values={
                "alliance_pressure": round(bounded(alliance_pressure), 3),
                "leader_style": leader_style,
                "geographic_flashpoint": round(bounded(geographic_flashpoint), 3),
                "mediation_window": round(bounded(mediation_window), 3),
                "military_posture": military_posture,
                "tension_index": round(bounded(tension_index), 3),
                "diplomatic_channel": round(bounded(diplomatic_channel), 3),
            },
        )

    def validate_phase(self, phase: str) -> list[str]:
        if phase not in self.PHASES:
            return [f"unsupported phase: {phase}"]
        return []

    def recommend_objective_profile(self, intake: IntakeDraft, state: "BeliefState"):
        from forecasting_harness.objectives import objective_profile_by_name

        domestic_focus_actor = max(
            (
                actor
                for actor in getattr(state, "actors", [])
                if getattr(getattr(actor, "behavior_profile", None), "domestic_sensitivity", None) is not None
            ),
            key=lambda actor: actor.behavior_profile.domestic_sensitivity or 0.0,
            default=None,
        )
        alliance_salient = any(
            (getattr(actor.behavior_profile, "alliance_dependence", 0.0) or 0.0) >= 0.7
            for actor in getattr(state, "actors", [])
            if getattr(actor, "behavior_profile", None) is not None
        )
        text = " ".join([intake.event_framing, intake.current_development]).lower()
        if (
            domestic_focus_actor is not None
            and (domestic_focus_actor.behavior_profile.domestic_sensitivity or 0.0) >= 0.7
            and alliance_salient
            and any_term_matches(text, ["domestic", "resolve", "alliance", "security"])
        ):
            return objective_profile_by_name("domestic-politics-first").model_copy(
                update={"focal_actor_id": domestic_focus_actor.actor_id}
            )
        return self.default_objective_profile()

    def is_terminal(self, state: "BeliefState", depth: int) -> bool:
        return getattr(state, "phase", None) == "settlement-stalemate"

    def propose_actions(self, state: "BeliefState") -> list[dict[str, Any]]:
        phase = getattr(state, "phase", None) or "trigger"
        leader_style = _string_field(state, "leader_style", "cautious") if state is not None else "cautious"
        alliance = _numeric_field(state, "alliance_pressure", 0.15)
        flashpoint = _numeric_field(state, "geographic_flashpoint", 0.25)
        mediation = _numeric_field(state, "mediation_window", 0.25)
        military_posture = _string_field(state, "military_posture", "reserve")
        tension = _numeric_field(state, "tension_index", 0.4)
        diplomacy = _numeric_field(state, "diplomatic_channel", 0.3)
        hawkish_adjustment = 0.1 if leader_style == "hawkish" else 0.0
        posture_adjustment = 0.08 if military_posture in {"high-alert", "forward-deployed", "contested"} else 0.0

        if phase == "trigger":
            actions = [
                {
                    "action_id": "signal",
                    "branch_id": "signal",
                    "label": "Signal resolve",
                    "prior": bounded(0.22 + diplomacy * 0.22 + mediation * 0.16 - max(0.0, tension - 0.55) * 0.18 - flashpoint * 0.04),
                    "dependencies": {"fields": ["leader_style", "diplomatic_channel", "mediation_window", "tension_index"]},
                },
                {
                    "action_id": "limited-response",
                    "branch_id": "limited-response",
                    "label": "Limited response",
                    "prior": bounded(
                        0.12
                        + hawkish_adjustment
                        + posture_adjustment
                        + max(0.0, tension - 0.48) * 0.22
                        + flashpoint * 0.16
                        - mediation * 0.08
                    ),
                    "dependencies": {"fields": ["geographic_flashpoint", "leader_style", "military_posture", "mediation_window", "tension_index"]},
                },
                {
                    "action_id": "alliance-consultation",
                    "branch_id": "alliance-consultation",
                    "label": "Alliance consultation",
                    "prior": bounded(0.03 + alliance * 0.45 + posture_adjustment * 0.1 + max(0.0, tension - 0.5) * 0.06 - mediation * 0.05),
                    "dependencies": {"fields": ["alliance_pressure", "diplomatic_channel", "mediation_window", "military_posture", "tension_index"]},
                },
                {
                    "action_id": "open-negotiation",
                    "branch_id": "open-negotiation",
                    "label": "Open negotiation",
                    "prior": bounded(0.1 + diplomacy * 0.22 + mediation * 0.32 - hawkish_adjustment * 0.35 - max(0.0, tension - 0.7) * 0.1),
                    "dependencies": {"fields": ["diplomatic_channel", "leader_style", "mediation_window", "tension_index"]},
                },
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "signaling":
            actions = [
                {"action_id": "signal-resolve", "label": "Signal resolve", "prior": bounded(0.2 + diplomacy * 0.2 + mediation * 0.18 - max(0.0, tension - 0.65) * 0.1)},
                {"action_id": "intercept", "label": "Intercept", "prior": bounded(0.08 + hawkish_adjustment + flashpoint * 0.18 + max(0.0, tension - 0.55) * 0.24 - mediation * 0.08)},
                {"action_id": "allied-pressure", "label": "Allied pressure", "prior": bounded(0.04 + alliance * 0.34 + diplomacy * 0.08)},
                {"action_id": "crisis-talks", "label": "Crisis talks", "prior": bounded(0.08 + mediation * 0.36 + diplomacy * 0.18 - max(0.0, tension - 0.75) * 0.08)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "limited-response":
            actions = [
                {"action_id": "contain-response", "label": "Contain response", "prior": bounded(0.2 + diplomacy * 0.14 + mediation * 0.16 - max(0.0, tension - 0.75) * 0.08)},
                {"action_id": "retaliate", "label": "Retaliate", "prior": bounded(0.12 + hawkish_adjustment + flashpoint * 0.14 + max(0.0, tension - 0.6) * 0.22 - mediation * 0.1)},
                {"action_id": "ceasefire-channel", "label": "Ceasefire channel", "prior": bounded(0.12 + mediation * 0.24 + diplomacy * 0.18)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "escalation":
            actions = [
                {"action_id": "force-projection", "label": "Force projection", "prior": bounded(0.24 + hawkish_adjustment + flashpoint * 0.18 + max(0.0, tension - 0.7) * 0.2)},
                {"action_id": "emergency-backchannel", "label": "Emergency backchannel", "prior": bounded(0.12 + mediation * 0.28 + diplomacy * 0.16)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "negotiation-deescalation":
            actions = [
                {"action_id": "confidence-measures", "label": "Confidence measures", "prior": bounded(0.18 + diplomacy * 0.25 + mediation * 0.28 - max(0.0, tension - 0.55) * 0.08)},
                {"action_id": "stalemate-return", "label": "Stalemate return", "prior": bounded(0.15 + max(0.0, tension - 0.45) * 0.32 + flashpoint * 0.12 - mediation * 0.18)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        return []

    def sample_transition(
        self, state: "BeliefState", action_context: dict[str, Any]
    ) -> list["BeliefState"] | list[dict[str, Any]]:
        action_id = action_context.get("action_id") or action_context.get("branch_id")
        phase = state.phase or "trigger"
        alliance = _numeric_field(state, "alliance_pressure", 0.15)
        flashpoint = _numeric_field(state, "geographic_flashpoint", 0.25)
        mediation = _numeric_field(state, "mediation_window", 0.25)
        tension = _numeric_field(state, "tension_index", 0.4)
        diplomacy = _numeric_field(state, "diplomatic_channel", 0.3)

        if phase == "trigger" and action_id == "signal":
            managed_weight, backchannel_weight = _normalized_weights(
                0.28 + flashpoint * 0.18 + max(0.0, tension - 0.45) * 0.12,
                0.22 + mediation * 0.34 + diplomacy * 0.1,
            )
            return [
                {
                    "next_state": _with_updates(
                        state,
                        phase="signaling",
                        field_updates={
                            "tension_index": max(tension, 0.45),
                            "diplomatic_channel": max(diplomacy, 0.45),
                            "mediation_window": max(mediation, 0.42),
                        },
                    ),
                    "weight": managed_weight,
                    "outcome_id": "managed-signal",
                    "outcome_label": "managed signal",
                },
                {
                    "next_state": _with_updates(
                        state,
                        phase="negotiation-deescalation",
                        field_updates={
                            "tension_index": max(0.18, tension - 0.12),
                            "diplomatic_channel": max(diplomacy, 0.62),
                            "mediation_window": max(mediation, 0.72),
                        },
                    ),
                    "weight": backchannel_weight,
                    "outcome_id": "backchannel-open",
                    "outcome_label": "backchannel opening",
                },
            ]
        if phase == "trigger" and action_id == "limited-response":
            return [
                {
                    "next_state": _with_updates(
                        state,
                        phase="limited-response",
                        field_updates={
                            "tension_index": max(0.75, tension),
                            "diplomatic_channel": min(0.25, diplomacy),
                            "mediation_window": min(0.22, mediation),
                        },
                    ),
                    "weight": 0.6,
                    "outcome_id": "contained-response",
                    "outcome_label": "contained response",
                },
                {
                    "next_state": _with_updates(
                        state,
                        phase="escalation",
                        field_updates={
                            "tension_index": 0.88,
                            "diplomatic_channel": min(0.18, diplomacy),
                            "mediation_window": min(0.15, mediation),
                        },
                    ),
                    "weight": 0.4,
                    "outcome_id": "escalatory-response",
                    "outcome_label": "escalatory response",
                },
            ]
        if phase == "trigger" and action_id == "alliance-consultation":
            restraint_weight, signaling_weight, deterrence_weight = _normalized_weights(
                0.18 + mediation * 0.35 + diplomacy * 0.12,
                0.16 + alliance * 0.22 + flashpoint * 0.12,
                0.12 + max(0.0, tension - 0.55) * 0.18 + flashpoint * 0.14 - mediation * 0.08,
            )
            return [
                {
                    "next_state": _with_updates(
                        state,
                        phase="negotiation-deescalation",
                        field_updates={
                            "tension_index": max(0.34, tension - 0.08),
                            "diplomatic_channel": max(0.68, diplomacy),
                            "mediation_window": max(0.72, mediation),
                            "alliance_pressure": max(0.55, alliance),
                        },
                    ),
                    "weight": restraint_weight,
                    "outcome_id": "coordinated-restraint",
                    "outcome_label": "coordinated restraint",
                },
                {
                    "next_state": _with_updates(
                        state,
                        phase="signaling",
                        field_updates={
                            "tension_index": max(0.58, tension),
                            "diplomatic_channel": max(0.42, diplomacy),
                            "alliance_pressure": max(0.52, alliance),
                        },
                    ),
                    "weight": signaling_weight,
                    "outcome_id": "coordinated-signaling",
                    "outcome_label": "coordinated signaling",
                },
                {
                    "next_state": _with_updates(
                        state,
                        phase="limited-response",
                        field_updates={
                            "tension_index": max(0.76, tension + 0.04),
                            "diplomatic_channel": max(0.22, diplomacy),
                            "mediation_window": min(0.24, mediation),
                            "alliance_pressure": max(0.5, alliance),
                        },
                    ),
                    "weight": deterrence_weight,
                    "outcome_id": "harder-deterrence",
                    "outcome_label": "harder deterrence",
                },
            ]
        if phase == "trigger" and action_id == "open-negotiation":
            return [
                _with_updates(
                    state,
                    phase="negotiation-deescalation",
                    field_updates={
                        "tension_index": 0.3,
                        "diplomatic_channel": 0.75,
                        "mediation_window": max(0.78, mediation),
                    },
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
        if phase == "signaling" and action_id == "allied-pressure":
            return [
                _with_updates(
                    state,
                    phase="negotiation-deescalation",
                    field_updates={
                        "tension_index": max(0.22, tension - 0.08),
                        "diplomatic_channel": max(0.6, diplomacy),
                        "mediation_window": max(0.62, mediation),
                    },
                )
            ]
        if phase == "signaling" and action_id == "crisis-talks":
            return [
                _with_updates(
                    state,
                    phase="negotiation-deescalation",
                    field_updates={
                        "tension_index": 0.35,
                        "diplomatic_channel": 0.75,
                        "mediation_window": max(0.78, mediation),
                    },
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
                    field_updates={
                        "tension_index": 0.35,
                        "diplomatic_channel": 0.8,
                        "mediation_window": max(0.76, mediation),
                    },
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
                    field_updates={
                        "tension_index": 0.45,
                        "diplomatic_channel": 0.7,
                        "mediation_window": max(0.7, mediation),
                    },
                )
            ]
        if phase == "negotiation-deescalation" and action_id == "confidence-measures":
            return [
                _with_updates(
                    state,
                    phase="settlement-stalemate",
                    field_updates={"tension_index": 0.28, "diplomatic_channel": 0.68, "mediation_window": max(0.7, mediation)},
                )
            ]
        if phase == "negotiation-deescalation" and action_id == "stalemate-return":
            return [
                _with_updates(
                    state,
                    phase="signaling",
                    field_updates={"tension_index": 0.6, "diplomatic_channel": 0.35, "mediation_window": max(0.36, mediation - 0.12)},
                )
            ]
        return [state]

    def score_state(self, state: "BeliefState") -> dict[str, float]:
        flashpoint = _numeric_field(state, "geographic_flashpoint", 0.25)
        mediation = _numeric_field(state, "mediation_window", 0.25)
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
            "escalation": bounded(tension + flashpoint * 0.1 + max(0.0, 0.45 - diplomacy) * 0.18 - mediation * 0.05),
            "negotiation": bounded(diplomacy + mediation * 0.16 + max(0.0, 0.55 - tension) * 0.08),
            "economic_stress": bounded(phase_stress + tension * 0.15 + flashpoint * 0.08),
        }

    def validate_state(self, state: "BeliefState") -> list[str]:
        return self.validate_phase(state.phase or "")
