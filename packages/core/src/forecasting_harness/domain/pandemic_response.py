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


class PandemicResponsePack(DomainPack):
    PHASES = ["trigger", "containment", "surge-response", "vaccination", "stabilization", "resolution"]

    def slug(self) -> str:
        return "pandemic-response"

    def interaction_model(self) -> InteractionModel:
        return InteractionModel.EVENT_DRIVEN

    def canonical_phases(self) -> list[str]:
        return list(self.PHASES)

    def search_config(self) -> dict[str, int | float]:
        return {"iterations": 18, "max_depth": 4, "rollout_depth": 3, "c_puct": 1.15}

    def validate_intake(self, intake: IntakeDraft) -> list[str]:
        issues: list[str] = []
        if len(intake.focus_entities) < 2:
            issues.append("pandemic-response requires at least two focus entities")
        if intake.current_stage not in self.PHASES:
            issues.append(f"unsupported phase: {intake.current_stage}")
        return issues

    def suggest_related_actors(self, intake: IntakeDraft) -> list[str]:
        return ["Hospitals", "Regional Governments", "Schools", "Pharmacies"]

    def retrieval_filters(self, intake: IntakeDraft) -> dict[str, str]:
        return {"domain": self.slug()}

    def suggest_questions(self) -> list[str]:
        return [
            "Is the binding constraint transmission, hospital capacity, or vaccine/booster uptake?",
            "Can officials still coordinate broad measures, or is the response shifting to targeted mitigation?",
        ]

    def extend_schema(self) -> dict[str, Any]:
        return {
            "hospital_strain": "float",
            "policy_alignment": "float",
            "public_compliance": "float",
            "testing_capacity": "float",
            "transmission_pressure": "float",
            "vaccine_readiness": "float",
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

        transmission_pressure = 0.42 + 0.1 * count_term_matches(
            text,
            [
                "community transmission",
                "spread accelerates",
                "winter wave",
                "outbreak",
                "surge",
                "case growth",
                "variant wave",
            ],
        )
        hospital_strain = 0.32 + 0.12 * count_term_matches(
            text,
            [
                "hospital admissions",
                "hospital strain",
                "intensive care",
                "capacity tightens",
                "overload",
                "staffing strain",
            ],
        )
        testing_capacity = 0.48
        testing_capacity -= 0.12 * count_term_matches(
            text,
            ["testing shortages", "limited testing", "slow turnaround", "surveillance gaps"],
        )
        testing_capacity += 0.08 * count_term_matches(text, ["testing expansion", "surveillance", "screening program"])

        public_compliance = 0.54
        public_compliance -= 0.12 * count_term_matches(
            text,
            ["fatigue", "compliance weakens", "resistance", "public fatigue", "lockdown fatigue"],
        )
        public_compliance += 0.08 * count_term_matches(text, ["distancing guidance", "mask uptake", "public support", "behavior change"])

        policy_alignment = 0.46
        policy_alignment += 0.1 * count_term_matches(
            text,
            ["health agencies", "coordinated", "regional governments", "coordination", "acceleration plans"],
        )
        policy_alignment -= 0.12 * count_term_matches(
            text,
            ["mixed messaging", "debate", "fragmented", "political split", "officials debate"],
        )

        vaccine_readiness = 0.08
        vaccine_readiness += 0.16 * count_term_matches(
            text,
            ["vaccine supply", "booster", "rollout", "cold-chain", "pharmacies", "acceleration plans"],
        )
        vaccine_readiness -= 0.08 * count_term_matches(text, ["no vaccine", "early outbreak", "novel virus"])

        return apply_manifest_state_overlays(
            text=text,
            slug=self.slug(),
            field_values={
            "hospital_strain": round(bounded(hospital_strain), 3),
            "policy_alignment": round(bounded(policy_alignment), 3),
            "public_compliance": round(bounded(public_compliance), 3),
            "testing_capacity": round(bounded(testing_capacity), 3),
            "transmission_pressure": round(bounded(transmission_pressure), 3),
            "vaccine_readiness": round(bounded(vaccine_readiness), 3),
            },
        )

    def is_terminal(self, state: Any, depth: int) -> bool:
        return getattr(state, "phase", None) == "resolution"

    def propose_actions(self, state: Any) -> list[dict[str, Any]]:
        phase = getattr(state, "phase", None) or "trigger"
        hospital = numeric_field(state, "hospital_strain", 0.35)
        alignment = numeric_field(state, "policy_alignment", 0.45)
        compliance = numeric_field(state, "public_compliance", 0.5)
        testing = numeric_field(state, "testing_capacity", 0.45)
        transmission = numeric_field(state, "transmission_pressure", 0.45)
        vaccine = numeric_field(state, "vaccine_readiness", 0.1)

        if phase == "trigger":
            actions = [
                {
                    "action_id": "containment-push",
                    "label": "Containment push",
                    "prior": bounded(0.1 + transmission * 0.24 + hospital * 0.12 + alignment * 0.16 + compliance * 0.08 - vaccine * 0.1),
                    "dependencies": {"fields": ["hospital_strain", "policy_alignment", "transmission_pressure", "vaccine_readiness"]},
                },
                {
                    "action_id": "hospital-surge",
                    "label": "Hospital surge",
                    "prior": bounded(0.1 + hospital * 0.24 + max(0.0, 0.55 - testing) * 0.14),
                    "dependencies": {"fields": ["hospital_strain", "testing_capacity"]},
                },
                {
                    "action_id": "vaccine-acceleration",
                    "label": "Vaccine acceleration",
                    "prior": bounded(0.04 + vaccine * 0.34 + hospital * 0.08 + max(0.0, 0.55 - compliance) * 0.1),
                    "dependencies": {"fields": ["hospital_strain", "public_compliance", "vaccine_readiness"]},
                },
                {
                    "action_id": "targeted-guidance",
                    "label": "Targeted guidance",
                    "prior": bounded(0.08 + alignment * 0.12 + max(0.0, 0.55 - compliance) * 0.16 + transmission * 0.08),
                    "dependencies": {"fields": ["policy_alignment", "public_compliance", "transmission_pressure"]},
                },
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "containment":
            actions = [
                {"action_id": "testing-expansion", "label": "Testing expansion", "prior": bounded(0.16 + max(0.0, 0.55 - testing) * 0.26)},
                {"action_id": "community-support", "label": "Community support", "prior": bounded(0.14 + max(0.0, 0.55 - compliance) * 0.22 + alignment * 0.08)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "surge-response":
            actions = [
                {"action_id": "care-capacity", "label": "Care capacity", "prior": bounded(0.18 + hospital * 0.22 + max(0.0, 0.55 - testing) * 0.08)},
                {"action_id": "emergency-support", "label": "Emergency support", "prior": bounded(0.14 + alignment * 0.12 + hospital * 0.12)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "vaccination":
            actions = [
                {"action_id": "booster-campaign", "label": "Booster campaign", "prior": bounded(0.18 + vaccine * 0.24 + max(0.0, 0.55 - compliance) * 0.08)},
                {"action_id": "targeted-mandates", "label": "Targeted mandates", "prior": bounded(0.12 + alignment * 0.16 + max(0.0, 0.5 - compliance) * 0.16)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        if phase == "stabilization":
            actions = [
                {"action_id": "phased-reopening", "label": "Phased reopening", "prior": bounded(0.16 + compliance * 0.12 + max(0.0, 0.55 - transmission) * 0.16)},
                {"action_id": "surveillance-pivot", "label": "Surveillance pivot", "prior": bounded(0.14 + testing * 0.18 + vaccine * 0.1)},
            ]
            return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())
        return []

    def sample_transition(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        action_id = action_context.get("action_id") or action_context.get("branch_id")
        hospital = numeric_field(state, "hospital_strain", 0.35)
        alignment = numeric_field(state, "policy_alignment", 0.45)
        compliance = numeric_field(state, "public_compliance", 0.5)
        testing = numeric_field(state, "testing_capacity", 0.45)
        transmission = numeric_field(state, "transmission_pressure", 0.45)
        vaccine = numeric_field(state, "vaccine_readiness", 0.1)
        phase = getattr(state, "phase", None) or "trigger"

        if phase == "trigger" and action_id == "containment-push":
            transmission_delta = 0.16 if alignment + compliance >= 0.8 else 0.08
            hospital_delta = 0.03 if alignment + compliance >= 0.8 else 0.08
            return [
                {
                    "next_state": with_updates(
                        state,
                        phase="containment",
                        field_updates={
                            "hospital_strain": bounded(hospital + hospital_delta),
                            "policy_alignment": bounded(alignment + 0.08),
                            "public_compliance": bounded(compliance + 0.06),
                            "transmission_pressure": max(0.0, transmission - transmission_delta),
                        },
                    ),
                    "weight": 0.7 if alignment + compliance >= 0.8 else 0.45,
                    "outcome_id": "coordination-holds",
                    "outcome_label": "coordination holds",
                },
                {
                    "next_state": with_updates(
                        state,
                        phase="surge-response",
                        field_updates={
                            "hospital_strain": bounded(hospital + 0.08),
                            "policy_alignment": bounded(alignment - 0.02),
                            "public_compliance": max(0.0, compliance - 0.03),
                            "transmission_pressure": max(0.0, transmission - 0.05),
                        },
                    ),
                    "weight": 0.3 if alignment + compliance >= 0.8 else 0.55,
                    "outcome_id": "late-containment",
                    "outcome_label": "late containment",
                },
            ]
        if phase == "trigger" and action_id == "hospital-surge":
            return [
                with_updates(
                    state,
                    phase="surge-response",
                    field_updates={
                        "hospital_strain": max(0.0, hospital - 0.08),
                        "testing_capacity": bounded(testing + 0.08),
                        "policy_alignment": bounded(alignment + 0.05),
                        "transmission_pressure": transmission,
                    },
                )
            ]
        if phase == "trigger" and action_id == "vaccine-acceleration":
            if vaccine < 0.25:
                return [
                    with_updates(
                        state,
                        phase="surge-response",
                        field_updates={
                            "hospital_strain": bounded(hospital + 0.04),
                            "public_compliance": max(0.0, compliance - 0.02),
                            "transmission_pressure": max(0.0, transmission - 0.01),
                            "vaccine_readiness": bounded(vaccine + 0.05),
                        },
                    )
                ]
            return [
                {
                    "next_state": with_updates(
                        state,
                        phase="vaccination",
                        field_updates={
                            "hospital_strain": max(0.0, hospital - 0.08),
                            "public_compliance": bounded(compliance + 0.04),
                            "transmission_pressure": max(0.0, transmission - 0.09),
                            "vaccine_readiness": bounded(vaccine + 0.22),
                        },
                    ),
                    "weight": 0.72,
                    "outcome_id": "uptake-improves",
                    "outcome_label": "uptake improves",
                },
                {
                    "next_state": with_updates(
                        state,
                        phase="vaccination",
                        field_updates={
                            "hospital_strain": max(0.0, hospital - 0.02),
                            "public_compliance": max(0.0, compliance - 0.04),
                            "transmission_pressure": max(0.0, transmission - 0.03),
                            "vaccine_readiness": bounded(vaccine + 0.12),
                        },
                    ),
                    "weight": 0.28,
                    "outcome_id": "uptake-lags",
                    "outcome_label": "uptake lags",
                },
            ]
        if phase == "trigger" and action_id == "targeted-guidance":
            return [
                with_updates(
                    state,
                    phase="containment",
                    field_updates={
                        "policy_alignment": bounded(alignment + 0.05),
                        "public_compliance": bounded(compliance + 0.02),
                        "transmission_pressure": max(0.0, transmission - 0.08),
                        "testing_capacity": bounded(testing + 0.05),
                    },
                )
            ]
        if phase == "containment" and action_id == "testing-expansion":
            return [
                with_updates(
                    state,
                    phase="stabilization",
                    field_updates={
                        "hospital_strain": max(0.0, hospital - 0.06),
                        "testing_capacity": bounded(testing + 0.18),
                        "transmission_pressure": max(0.0, transmission - 0.08),
                    },
                )
            ]
        if phase == "containment" and action_id == "community-support":
            return [
                with_updates(
                    state,
                    phase="stabilization",
                    field_updates={
                        "policy_alignment": bounded(alignment + 0.06),
                        "public_compliance": bounded(compliance + 0.12),
                        "transmission_pressure": max(0.0, transmission - 0.06),
                    },
                )
            ]
        if phase == "surge-response" and action_id == "care-capacity":
            return [
                with_updates(
                    state,
                    phase="stabilization",
                    field_updates={
                        "hospital_strain": max(0.0, hospital - 0.16),
                        "testing_capacity": bounded(testing + 0.06),
                        "policy_alignment": bounded(alignment + 0.04),
                    },
                )
            ]
        if phase == "surge-response" and action_id == "emergency-support":
            return [
                with_updates(
                    state,
                    phase="stabilization",
                    field_updates={
                        "hospital_strain": max(0.0, hospital - 0.1),
                        "policy_alignment": bounded(alignment + 0.08),
                        "public_compliance": bounded(compliance + 0.04),
                    },
                )
            ]
        if phase == "vaccination" and action_id == "booster-campaign":
            return [
                with_updates(
                    state,
                    phase="stabilization",
                    field_updates={
                        "hospital_strain": max(0.0, hospital - 0.08),
                        "public_compliance": bounded(compliance + 0.06),
                        "transmission_pressure": max(0.0, transmission - 0.08),
                        "vaccine_readiness": bounded(vaccine + 0.12),
                    },
                )
            ]
        if phase == "vaccination" and action_id == "targeted-mandates":
            return [
                with_updates(
                    state,
                    phase="stabilization",
                    field_updates={
                        "policy_alignment": bounded(alignment + 0.08),
                        "public_compliance": bounded(compliance + 0.04),
                        "transmission_pressure": max(0.0, transmission - 0.06),
                        "vaccine_readiness": bounded(vaccine + 0.08),
                    },
                )
            ]
        if phase == "stabilization" and action_id == "phased-reopening":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "hospital_strain": max(0.0, hospital - 0.06),
                        "public_compliance": max(0.0, compliance - 0.02),
                        "transmission_pressure": max(0.0, transmission - 0.04),
                    },
                )
            ]
        if phase == "stabilization" and action_id == "surveillance-pivot":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "testing_capacity": bounded(testing + 0.08),
                        "transmission_pressure": max(0.0, transmission - 0.05),
                        "vaccine_readiness": bounded(vaccine + 0.04),
                    },
                )
            ]
        return [state]

    def score_state(self, state: Any) -> dict[str, float]:
        phase = getattr(state, "phase", None) or "trigger"
        hospital = numeric_field(state, "hospital_strain", 0.35)
        alignment = numeric_field(state, "policy_alignment", 0.45)
        compliance = numeric_field(state, "public_compliance", 0.5)
        testing = numeric_field(state, "testing_capacity", 0.45)
        transmission = numeric_field(state, "transmission_pressure", 0.45)
        vaccine = numeric_field(state, "vaccine_readiness", 0.1)
        phase_severity = {
            "trigger": 0.62,
            "containment": 0.5,
            "surge-response": 0.56,
            "vaccination": 0.38,
            "stabilization": 0.28,
            "resolution": 0.16,
        }[phase]
        return {
            "escalation": bounded(phase_severity + hospital * 0.22 + transmission * 0.24 + max(0.0, 0.45 - testing) * 0.08),
            "negotiation": bounded(0.18 + alignment * 0.26 + compliance * 0.18 + vaccine * 0.16),
            "economic_stress": bounded(0.22 + transmission * 0.16 + max(0.0, 0.5 - compliance) * 0.18 + (0.12 if phase in {"containment", "surge-response"} else 0.04)),
        }

    def validate_state(self, state: Any) -> list[str]:
        phase = getattr(state, "phase", None) or ""
        return [] if phase in self.PHASES else [f"unsupported phase: {phase}"]
