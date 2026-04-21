from __future__ import annotations

from typing import Any

from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.domain.template_utils import bounded, compose_signal_text, count_term_matches, integer_field, numeric_field, string_field, with_updates
from forecasting_harness.workflow.models import IntakeDraft


class SupplyChainDisruptionPack(DomainPack):
    PHASES = ["trigger", "triage", "rerouting", "capacity-rebuild", "resolution"]

    def slug(self) -> str:
        return "supply-chain-disruption"

    def interaction_model(self) -> InteractionModel:
        return InteractionModel.EVENT_DRIVEN

    def canonical_phases(self) -> list[str]:
        return list(self.PHASES)

    def search_config(self) -> dict[str, int | float]:
        return {"iterations": 16, "max_depth": 4, "rollout_depth": 3, "c_puct": 1.1}

    def validate_intake(self, intake: IntakeDraft) -> list[str]:
        issues: list[str] = []
        if len(intake.focus_entities) < 2:
            issues.append("supply-chain-disruption requires at least two focus entities")
        if intake.current_stage not in self.PHASES:
            issues.append(f"unsupported phase: {intake.current_stage}")
        return issues

    def suggest_related_actors(self, intake: IntakeDraft) -> list[str]:
        return ["Alternate Suppliers", "Logistics Partners", "Key Customers", "Port Authorities"]

    def retrieval_filters(self, intake: IntakeDraft) -> dict[str, str]:
        return {"domain": self.slug()}

    def suggest_questions(self) -> list[str]:
        return [
            "Is the binding constraint inventory, transport, or substitution?",
            "Which node in the chain is hardest to replace?",
        ]

    def extend_schema(self) -> dict[str, Any]:
        return {
            "customer_penalty_pressure": "float",
            "disruption_mode": "str",
            "inventory_cover_days": "int",
            "substitution_flexibility": "float",
            "supplier_concentration": "float",
            "transport_reliability": "float",
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

        inventory_cover_days = 18
        inventory_cover_days -= 4 * count_term_matches(
            text,
            ["single-source", "thin inventory", "launches committed", "port delays", "export restrictions"],
        )
        inventory_cover_days += 2 * count_term_matches(text, ["buffer", "allocation measures"])
        inventory_cover_days = max(3, min(30, inventory_cover_days))

        substitution_flexibility = 0.4
        substitution_flexibility -= 0.12 * count_term_matches(
            text,
            ["no easy substitute", "specialized", "rare-earth", "hardest to replace"],
        )
        substitution_flexibility += 0.08 * count_term_matches(text, ["alternate sources", "qualify alternate", "supplier onboard"])

        transport_reliability = 0.55
        transport_reliability -= 0.12 * count_term_matches(
            text,
            ["flooding", "port delays", "logistics disruption", "export restrictions", "congestion"],
        )
        transport_reliability += 0.05 * count_term_matches(text, ["reroute", "logistics partners"])

        supplier_concentration = 0.4
        supplier_concentration += 0.14 * count_term_matches(
            text,
            ["single-source", "single source", "rare-earth", "specialized", "hardest to replace"],
        )
        supplier_concentration -= 0.08 * count_term_matches(text, ["alternate sources", "supplier onboard", "qualify alternate"])

        customer_penalty_pressure = 0.25
        customer_penalty_pressure += 0.12 * count_term_matches(
            text,
            ["launches committed", "dealer inventories", "key customers", "highest-margin models", "delivery penalties"],
        )
        customer_penalty_pressure += 0.08 * count_term_matches(text, ["thin inventory", "priority customers"])

        transport_matches = count_term_matches(text, ["flooding", "port delays", "logistics disruption", "rerouting"])
        source_matches = count_term_matches(text, ["rare-earth", "specialized", "single-source", "export restrictions"])
        if source_matches >= 1 and source_matches >= transport_matches:
            disruption_mode = "source"
        elif transport_matches >= 1:
            disruption_mode = "transport"
        else:
            disruption_mode = "mixed"

        return {
            "customer_penalty_pressure": round(bounded(customer_penalty_pressure), 3),
            "disruption_mode": disruption_mode,
            "inventory_cover_days": int(inventory_cover_days),
            "substitution_flexibility": round(bounded(substitution_flexibility), 3),
            "supplier_concentration": round(bounded(supplier_concentration), 3),
            "transport_reliability": round(bounded(transport_reliability), 3),
        }

    def is_terminal(self, state: Any, depth: int) -> bool:
        return getattr(state, "phase", None) == "resolution"

    def propose_actions(self, state: Any) -> list[dict[str, Any]]:
        phase = getattr(state, "phase", None) or "trigger"
        customer_pressure = numeric_field(state, "customer_penalty_pressure", 0.25)
        disruption_mode = string_field(state, "disruption_mode", "mixed")
        inventory = integer_field(state, "inventory_cover_days", 18)
        concentration = numeric_field(state, "supplier_concentration", 0.4)
        transport = numeric_field(state, "transport_reliability", 0.55)
        substitution = numeric_field(state, "substitution_flexibility", 0.4)
        transport_bias = 0.24 if disruption_mode == "transport" else 0.0
        source_bias = 0.24 if disruption_mode == "source" else 0.0
        if phase == "trigger":
            return [
                {
                    "action_id": "allocate-inventory",
                    "label": "Allocate inventory",
                    "prior": bounded(0.1 + max(0, 14 - inventory) * 0.02 + customer_pressure * 0.16 + (0.08 if disruption_mode == "transport" else 0.0)),
                    "dependencies": {"fields": ["customer_penalty_pressure", "disruption_mode", "inventory_cover_days"]},
                },
                {
                    "action_id": "expedite-alternatives",
                    "label": "Expedite alternatives",
                    "prior": bounded(0.08 + max(0.0, 0.65 - substitution) * 0.14 + concentration * 0.18 + source_bias - transport_bias),
                    "dependencies": {"fields": ["disruption_mode", "substitution_flexibility", "supplier_concentration"]},
                },
                {
                    "action_id": "customer-prioritization",
                    "label": "Customer prioritization",
                    "prior": bounded(0.08 + customer_pressure * 0.22 + max(0, 12 - inventory) * 0.015 + max(0.0, 0.55 - transport) * 0.08 + transport_bias * 0.8),
                    "dependencies": {"fields": ["customer_penalty_pressure", "disruption_mode", "inventory_cover_days", "transport_reliability"]},
                },
                {
                    "action_id": "reserve-logistics",
                    "label": "Reserve logistics",
                    "prior": bounded(0.08 + max(0.0, 0.6 - transport) * 0.2 + concentration * 0.06 + transport_bias * 1.05),
                    "dependencies": {"fields": ["disruption_mode", "supplier_concentration", "transport_reliability"]},
                },
            ]
        if phase == "triage":
            return [
                {"action_id": "reroute-logistics", "label": "Reroute logistics", "prior": bounded(0.14 + max(0.0, 0.55 - transport) * 0.2)},
                {"action_id": "demand-shaping", "label": "Demand shaping", "prior": bounded(0.12 + customer_pressure * 0.18)},
            ]
        if phase == "rerouting":
            return [
                {"action_id": "buffer-build", "label": "Buffer build", "prior": bounded(0.12 + max(0, 12 - inventory) * 0.025)},
                {"action_id": "supplier-onboard", "label": "Supplier onboard", "prior": bounded(0.12 + concentration * 0.2 + max(0.0, 0.65 - substitution) * 0.12)},
            ]
        if phase == "capacity-rebuild":
            return [
                {"action_id": "stabilize-network", "label": "Stabilize network", "prior": bounded(0.16 + max(0.0, 0.55 - transport) * 0.14 + customer_pressure * 0.08)},
                {"action_id": "localize-node", "label": "Localize node", "prior": bounded(0.1 + concentration * 0.18)},
            ]
        return []

    def sample_transition(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        action_id = action_context.get("action_id") or action_context.get("branch_id")
        customer_pressure = numeric_field(state, "customer_penalty_pressure", 0.25)
        disruption_mode = string_field(state, "disruption_mode", "mixed")
        inventory = integer_field(state, "inventory_cover_days", 18)
        concentration = numeric_field(state, "supplier_concentration", 0.4)
        substitution = numeric_field(state, "substitution_flexibility", 0.4)
        transport = numeric_field(state, "transport_reliability", 0.55)
        phase = getattr(state, "phase", None) or "trigger"

        if phase == "trigger" and action_id == "allocate-inventory":
            return [
                with_updates(
                    state,
                    phase="triage",
                    field_updates={
                        "customer_penalty_pressure": min(1.0, customer_pressure + 0.03),
                        "disruption_mode": disruption_mode,
                        "inventory_cover_days": max(1, inventory - 4),
                        "transport_reliability": transport,
                    },
                )
            ]
        if phase == "trigger" and action_id == "expedite-alternatives":
            if disruption_mode == "transport":
                return [
                    with_updates(
                        state,
                        phase="triage",
                        field_updates={
                            "disruption_mode": disruption_mode,
                            "customer_penalty_pressure": min(1.0, customer_pressure + 0.02),
                            "inventory_cover_days": max(1, inventory - 4),
                            "substitution_flexibility": substitution + 0.05,
                            "supplier_concentration": max(0.0, concentration - 0.04),
                        },
                    )
                ]
            return [
                with_updates(
                    state,
                    phase="rerouting",
                    field_updates={
                        "disruption_mode": disruption_mode,
                        "inventory_cover_days": max(1, inventory - 2),
                        "substitution_flexibility": substitution + 0.15,
                        "supplier_concentration": max(0.0, concentration - 0.1),
                    },
                )
            ]
        if phase == "trigger" and action_id == "customer-prioritization":
            return [
                with_updates(
                    state,
                    phase="triage",
                    field_updates={
                        "customer_penalty_pressure": max(0.0, customer_pressure - 0.04),
                        "disruption_mode": disruption_mode,
                        "inventory_cover_days": max(1, inventory - 3),
                        "transport_reliability": transport + 0.03,
                    },
                )
            ]
        if phase == "trigger" and action_id == "reserve-logistics":
            if disruption_mode == "transport":
                return [
                    with_updates(
                        state,
                        phase="rerouting",
                        field_updates={
                            "customer_penalty_pressure": max(0.0, customer_pressure - 0.03),
                            "disruption_mode": disruption_mode,
                            "inventory_cover_days": max(1, inventory - 1),
                            "transport_reliability": transport + 0.2,
                        },
                    )
                ]
            return [
                with_updates(
                    state,
                    phase="rerouting",
                    field_updates={
                        "disruption_mode": disruption_mode,
                        "inventory_cover_days": max(1, inventory - 2),
                        "transport_reliability": transport + 0.12,
                    },
                )
            ]
        if phase == "triage" and action_id == "reroute-logistics":
            return [
                with_updates(
                    state,
                    phase="rerouting",
                    field_updates={
                        "inventory_cover_days": max(1, inventory - 1),
                        "transport_reliability": transport + 0.15,
                    },
                )
            ]
        if phase == "triage" and action_id == "demand-shaping":
            return [
                with_updates(
                    state,
                    phase="capacity-rebuild",
                    field_updates={
                        "customer_penalty_pressure": max(0.0, customer_pressure - 0.06),
                        "inventory_cover_days": inventory + 2,
                        "substitution_flexibility": substitution + 0.05,
                    },
                )
            ]
        if phase == "rerouting" and action_id == "buffer-build":
            return [
                with_updates(
                    state,
                    phase="capacity-rebuild",
                    field_updates={
                        "inventory_cover_days": inventory + 3,
                        "transport_reliability": transport + 0.05,
                    },
                )
            ]
        if phase == "rerouting" and action_id == "supplier-onboard":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "inventory_cover_days": inventory + 4,
                        "substitution_flexibility": substitution + 0.12,
                        "supplier_concentration": max(0.0, concentration - 0.16),
                    },
                )
            ]
        if phase == "capacity-rebuild" and action_id == "stabilize-network":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "customer_penalty_pressure": max(0.0, customer_pressure - 0.06),
                        "inventory_cover_days": inventory + 5,
                        "transport_reliability": transport + 0.08,
                    },
                )
            ]
        if phase == "capacity-rebuild" and action_id == "localize-node":
            return [
                with_updates(
                    state,
                    phase="resolution",
                    field_updates={
                        "substitution_flexibility": substitution + 0.08,
                        "supplier_concentration": max(0.0, concentration - 0.12),
                        "transport_reliability": transport + 0.04,
                    },
                )
            ]
        return [state]

    def score_state(self, state: Any) -> dict[str, float]:
        phase = getattr(state, "phase", None) or "trigger"
        customer_pressure = numeric_field(state, "customer_penalty_pressure", 0.25)
        inventory = integer_field(state, "inventory_cover_days", 18)
        concentration = numeric_field(state, "supplier_concentration", 0.4)
        substitution = numeric_field(state, "substitution_flexibility", 0.4)
        transport = numeric_field(state, "transport_reliability", 0.55)
        disruption = {"trigger": 0.55, "triage": 0.5, "rerouting": 0.4, "capacity-rebuild": 0.3, "resolution": 0.15}[phase]
        return {
            "escalation": bounded(disruption + max(0, 14 - inventory) / 30 + max(0.0, 0.55 - transport) * 0.16 + customer_pressure * 0.14),
            "negotiation": bounded(0.18 + substitution * 0.24 + transport * 0.18 + max(0.0, 0.6 - concentration) * 0.16),
            "economic_stress": bounded(0.26 + max(0, 20 - inventory) / 28 + max(0.0, 0.5 - substitution) * 0.16 + concentration * 0.14 + customer_pressure * 0.12),
        }

    def validate_state(self, state: Any) -> list[str]:
        phase = getattr(state, "phase", None) or ""
        return [] if phase in self.PHASES else [f"unsupported phase: {phase}"]
