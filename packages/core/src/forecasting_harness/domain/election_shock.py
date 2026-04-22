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
        return {
            "coalition_fragility": "float",
            "donor_confidence": "float",
            "message_discipline": "float",
            "poll_margin": "float",
            "turnout_energy": "float",
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

        poll_margin = 0.0
        poll_margin -= 0.8 * count_term_matches(
            text,
            ["debate collapse", "campaign collapse", "donor confidence", "competency issue", "investor concern"],
        )
        poll_margin += 0.5 * count_term_matches(text, ["endorsement surge", "poll lead", "momentum gain"])

        turnout_energy = 0.5 + 0.08 * count_term_matches(
            text,
            ["ground game", "turnout organizers", "mobilization", "early vote", "base support"],
        )
        turnout_energy = bounded(turnout_energy)

        message_discipline = 0.5
        message_discipline -= 0.1 * count_term_matches(
            text,
            ["scrambles", "message reset", "debate collapse", "messaging", "narrative fight"],
        )
        message_discipline += 0.05 * count_term_matches(text, ["stabilize messaging", "discipline message"])
        message_discipline = bounded(message_discipline)

        donor_confidence = 0.48
        donor_confidence -= 0.12 * count_term_matches(
            text,
            ["donor confidence", "fundraising shock", "debate collapse", "party leadership scrambles", "elite panic"],
        )
        donor_confidence += 0.08 * count_term_matches(text, ["elite reassurance", "major donors regroup", "endorsement surge"])
        donor_confidence = bounded(donor_confidence)

        coalition_fragility = 0.34
        coalition_fragility += 0.12 * count_term_matches(
            text,
            ["party leadership", "elite defection", "coalition crack", "competency issue", "scrambles"],
        )
        coalition_fragility += 0.08 * count_term_matches(text, ["undecided voters", "swing voters"])
        coalition_fragility = bounded(coalition_fragility)

        return apply_manifest_state_overlays(
            text=text,
            slug=self.slug(),
            field_values={
            "coalition_fragility": round(coalition_fragility, 3),
            "donor_confidence": round(donor_confidence, 3),
            "poll_margin": round(poll_margin, 3),
            "turnout_energy": round(turnout_energy, 3),
            "message_discipline": round(message_discipline, 3),
            },
        )

    def is_terminal(self, state: Any, depth: int) -> bool:
        return getattr(state, "phase", None) == "resolution"

    def propose_actions(self, state: Any) -> list[dict[str, Any]]:
        phase = getattr(state, "phase", None) or "trigger"
        coalition = numeric_field(state, "coalition_fragility", 0.34)
        donors = numeric_field(state, "donor_confidence", 0.48)
        margin = numeric_field(state, "poll_margin", 0.0)
        turnout = numeric_field(state, "turnout_energy", 0.5)
        discipline = numeric_field(state, "message_discipline", 0.5)
        if phase == "trigger":
            actions = [
                {
                    "action_id": "message-reset",
                    "label": "Message reset",
                    "prior": bounded(0.18 + max(0.0, 0.55 - discipline) * 0.22 + max(0.0, 0.5 - donors) * 0.12),
                    "dependencies": {"fields": ["donor_confidence", "message_discipline"]},
                },
                {
                    "action_id": "opposition-attack",
                    "label": "Opposition attack",
                    "prior": bounded(0.14 + max(0.0, -margin) * 0.04 + coalition * 0.16),
                    "dependencies": {"fields": ["coalition_fragility", "poll_margin"]},
                },
                {
                    "action_id": "ground-game-surge",
                    "label": "Ground game surge",
                    "prior": bounded(0.16 + turnout * 0.18 + max(0.0, 0.45 - donors) * 0.08),
                    "dependencies": {"fields": ["donor_confidence", "turnout_energy"]},
                },
                {
                    "action_id": "elite-reassurance",
                    "label": "Elite reassurance",
                    "prior": bounded(0.12 + coalition * 0.2 + max(0.0, 0.45 - donors) * 0.22),
                    "dependencies": {"fields": ["coalition_fragility", "donor_confidence", "message_discipline"]},
                },
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "narrative-fight":
            actions = [
                {"action_id": "endorsement-push", "label": "Endorsement push", "prior": bounded(0.16 + max(0.0, 0.45 - donors) * 0.16 + coalition * 0.12)},
                {"action_id": "contrast-campaign", "label": "Contrast campaign", "prior": bounded(0.14 + max(0.0, -margin) * 0.03)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "turnout-drive":
            actions = [
                {"action_id": "ballot-chase", "label": "Ballot chase", "prior": bounded(0.18 + turnout * 0.16)},
                {"action_id": "base-consolidation", "label": "Base consolidation", "prior": bounded(0.16 + coalition * 0.12 + max(0.0, 0.45 - donors) * 0.08)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "coalition-shaping":
            actions = [
                {"action_id": "targeted-deal", "label": "Targeted deal", "prior": bounded(0.16 + coalition * 0.18 + max(0.0, 0.45 - donors) * 0.1)},
                {"action_id": "discipline-message", "label": "Discipline message", "prior": bounded(0.16 + discipline * 0.12)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        return []

    def sample_transition(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        action_id = action_context.get("action_id") or action_context.get("branch_id")
        coalition = numeric_field(state, "coalition_fragility", 0.34)
        donors = numeric_field(state, "donor_confidence", 0.48)
        margin = numeric_field(state, "poll_margin", 0.0)
        turnout = numeric_field(state, "turnout_energy", 0.5)
        discipline = numeric_field(state, "message_discipline", 0.5)
        phase = getattr(state, "phase", None) or "trigger"

        if phase == "trigger" and action_id == "message-reset":
            return [
                {
                    "next_state": with_updates(
                        state,
                        phase="narrative-fight",
                        field_updates={
                            "coalition_fragility": max(0.0, coalition - 0.04),
                            "donor_confidence": donors + 0.08,
                            "message_discipline": discipline + 0.15,
                            "poll_margin": margin + 0.3,
                        },
                    ),
                    "weight": 0.6,
                    "outcome_id": "reset-holds",
                    "outcome_label": "reset holds",
                },
                {
                    "next_state": with_updates(
                        state,
                        phase="turnout-drive",
                        field_updates={
                            "donor_confidence": donors + 0.03,
                            "message_discipline": discipline + 0.05,
                            "turnout_energy": turnout + 0.08,
                        },
                    ),
                    "weight": 0.4,
                    "outcome_id": "reset-to-turnout",
                    "outcome_label": "reset shifts to turnout",
                },
            ]
        if phase == "trigger" and action_id == "opposition-attack":
            return [
                with_updates(
                    state,
                    phase="narrative-fight",
                    field_updates={
                        "coalition_fragility": coalition + 0.08,
                        "donor_confidence": max(0.0, donors - 0.04),
                        "message_discipline": max(0.0, discipline - 0.1),
                        "poll_margin": margin - 0.4,
                    },
                )
            ]
        if phase == "trigger" and action_id == "ground-game-surge":
            return [
                with_updates(
                    state,
                    phase="turnout-drive",
                    field_updates={
                        "donor_confidence": donors + 0.02,
                        "turnout_energy": turnout + 0.18,
                        "poll_margin": margin + 0.1,
                    },
                )
            ]
        if phase == "trigger" and action_id == "elite-reassurance":
            return [
                with_updates(
                    state,
                    phase="coalition-shaping",
                    field_updates={
                        "coalition_fragility": max(0.0, coalition - 0.12),
                        "donor_confidence": donors + 0.12,
                        "message_discipline": discipline + 0.1,
                        "poll_margin": margin + 0.15,
                    },
                )
            ]
        if phase == "narrative-fight" and action_id == "endorsement-push":
            return [
                with_updates(
                    state,
                    phase="coalition-shaping",
                    field_updates={
                        "coalition_fragility": max(0.0, coalition - 0.08),
                        "donor_confidence": donors + 0.06,
                        "poll_margin": margin + 0.4,
                        "message_discipline": discipline + 0.05,
                    },
                )
            ]
        if phase == "narrative-fight" and action_id == "contrast-campaign":
            return [
                with_updates(
                    state,
                    phase="turnout-drive",
                    field_updates={
                        "coalition_fragility": coalition + 0.03,
                        "turnout_energy": turnout + 0.08,
                        "message_discipline": discipline - 0.02,
                    },
                )
            ]
        if phase == "turnout-drive" and action_id == "ballot-chase":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "turnout_energy": turnout + 0.1,
                        "poll_margin": margin + 0.2,
                        "donor_confidence": donors + 0.03,
                    },
                )
            ]
        if phase == "turnout-drive" and action_id == "base-consolidation":
            return [
                with_updates(
                    state,
                    phase="coalition-shaping",
                    field_updates={
                        "coalition_fragility": max(0.0, coalition - 0.06),
                        "turnout_energy": turnout + 0.05,
                        "message_discipline": discipline + 0.05,
                    },
                )
            ]
        if phase == "coalition-shaping" and action_id == "targeted-deal":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "coalition_fragility": max(0.0, coalition - 0.08),
                        "donor_confidence": donors + 0.04,
                        "poll_margin": margin + 0.25,
                        "message_discipline": discipline + 0.05,
                    },
                )
            ]
        if phase == "coalition-shaping" and action_id == "discipline-message":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "coalition_fragility": max(0.0, coalition - 0.04),
                        "message_discipline": discipline + 0.08,
                        "turnout_energy": turnout + 0.02,
                    },
                )
            ]
        return [state]

    def score_state(self, state: Any) -> dict[str, float]:
        phase = getattr(state, "phase", None) or "trigger"
        coalition = numeric_field(state, "coalition_fragility", 0.34)
        donors = numeric_field(state, "donor_confidence", 0.48)
        margin = numeric_field(state, "poll_margin", 0.0)
        turnout = numeric_field(state, "turnout_energy", 0.5)
        discipline = numeric_field(state, "message_discipline", 0.5)
        volatility = {"trigger": 0.5, "narrative-fight": 0.55, "turnout-drive": 0.35, "coalition-shaping": 0.3, "resolution": 0.2}[phase]
        return {
            "escalation": bounded(volatility + max(0.0, -margin) * 0.08 + (0.5 - discipline) * 0.18 + coalition * 0.14),
            "negotiation": bounded(0.16 + discipline * 0.24 + turnout * 0.22 + max(margin, 0.0) * 0.05 + donors * 0.12),
            "economic_stress": bounded(0.22 + volatility * 0.3 + max(0.0, 0.5 - turnout) * 0.16 + max(0.0, 0.5 - donors) * 0.16),
        }

    def validate_state(self, state: Any) -> list[str]:
        phase = getattr(state, "phase", None) or ""
        return [] if phase in self.PHASES else [f"unsupported phase: {phase}"]
