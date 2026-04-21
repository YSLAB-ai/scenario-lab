from __future__ import annotations

from typing import Any

from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.domain.template_utils import bounded, compose_signal_text, count_term_matches, integer_field, numeric_field, with_updates
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
        return {"inventory_cover_days": "int", "substitution_flexibility": "float", "transport_reliability": "float"}

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

        return {
            "inventory_cover_days": int(inventory_cover_days),
            "substitution_flexibility": round(bounded(substitution_flexibility), 3),
            "transport_reliability": round(bounded(transport_reliability), 3),
        }

    def is_terminal(self, state: Any, depth: int) -> bool:
        return getattr(state, "phase", None) == "resolution"

    def propose_actions(self, state: Any) -> list[dict[str, Any]]:
        phase = getattr(state, "phase", None) or "trigger"
        inventory = integer_field(state, "inventory_cover_days", 18)
        transport = numeric_field(state, "transport_reliability", 0.55)
        substitution = numeric_field(state, "substitution_flexibility", 0.4)
        if phase == "trigger":
            return [
                {"action_id": "allocate-inventory", "label": "Allocate inventory", "prior": bounded(0.18 + max(0, 14 - inventory) * 0.03), "dependencies": {"fields": ["inventory_cover_days"]}},
                {"action_id": "expedite-alternatives", "label": "Expedite alternatives", "prior": bounded(0.16 + max(0.0, 0.65 - substitution) * 0.18), "dependencies": {"fields": ["substitution_flexibility"]}},
                {"action_id": "customer-prioritization", "label": "Customer prioritization", "prior": bounded(0.14 + max(0, 12 - inventory) * 0.02 + max(0.0, 0.55 - transport) * 0.12), "dependencies": {"fields": ["inventory_cover_days", "transport_reliability"]}},
                {"action_id": "reserve-logistics", "label": "Reserve logistics", "prior": bounded(0.16 + max(0.0, 0.6 - transport) * 0.2), "dependencies": {"fields": ["transport_reliability"]}},
            ]
        if phase == "triage":
            return [
                {"action_id": "reroute-logistics", "label": "Reroute logistics", "prior": 0.5},
                {"action_id": "demand-shaping", "label": "Demand shaping", "prior": 0.4},
            ]
        if phase == "rerouting":
            return [
                {"action_id": "buffer-build", "label": "Buffer build", "prior": 0.5},
                {"action_id": "supplier-onboard", "label": "Supplier onboard", "prior": 0.45},
            ]
        if phase == "capacity-rebuild":
            return [
                {"action_id": "stabilize-network", "label": "Stabilize network", "prior": 0.55},
                {"action_id": "localize-node", "label": "Localize node", "prior": 0.35},
            ]
        return []

    def sample_transition(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        action_id = action_context.get("action_id") or action_context.get("branch_id")
        inventory = integer_field(state, "inventory_cover_days", 18)
        substitution = numeric_field(state, "substitution_flexibility", 0.4)
        transport = numeric_field(state, "transport_reliability", 0.55)
        phase = getattr(state, "phase", None) or "trigger"

        if phase == "trigger" and action_id == "allocate-inventory":
            return [with_updates(state, phase="triage", field_updates={"inventory_cover_days": max(1, inventory - 4), "transport_reliability": transport})]
        if phase == "trigger" and action_id == "expedite-alternatives":
            return [with_updates(state, phase="rerouting", field_updates={"substitution_flexibility": substitution + 0.15, "inventory_cover_days": max(1, inventory - 2)})]
        if phase == "trigger" and action_id == "customer-prioritization":
            return [with_updates(state, phase="triage", field_updates={"inventory_cover_days": max(1, inventory - 3), "transport_reliability": transport + 0.03})]
        if phase == "trigger" and action_id == "reserve-logistics":
            return [with_updates(state, phase="rerouting", field_updates={"transport_reliability": transport + 0.12, "inventory_cover_days": max(1, inventory - 2)})]
        if phase == "triage" and action_id == "reroute-logistics":
            return [with_updates(state, phase="rerouting", field_updates={"transport_reliability": transport + 0.15, "inventory_cover_days": max(1, inventory - 1)})]
        if phase == "triage" and action_id == "demand-shaping":
            return [with_updates(state, phase="capacity-rebuild", field_updates={"inventory_cover_days": inventory + 2, "substitution_flexibility": substitution + 0.05})]
        if phase == "rerouting" and action_id == "buffer-build":
            return [with_updates(state, phase="capacity-rebuild", field_updates={"inventory_cover_days": inventory + 3, "transport_reliability": transport + 0.05})]
        if phase == "rerouting" and action_id == "supplier-onboard":
            return [with_updates(state, phase="resolution", field_updates={"substitution_flexibility": substitution + 0.12, "inventory_cover_days": inventory + 4})]
        if phase == "capacity-rebuild" and action_id == "stabilize-network":
            return [with_updates(state, phase="resolution", field_updates={"inventory_cover_days": inventory + 5, "transport_reliability": transport + 0.08})]
        if phase == "capacity-rebuild" and action_id == "localize-node":
            return [with_updates(state, phase="resolution", field_updates={"substitution_flexibility": substitution + 0.08, "transport_reliability": transport + 0.04})]
        return [state]

    def score_state(self, state: Any) -> dict[str, float]:
        phase = getattr(state, "phase", None) or "trigger"
        inventory = integer_field(state, "inventory_cover_days", 18)
        substitution = numeric_field(state, "substitution_flexibility", 0.4)
        transport = numeric_field(state, "transport_reliability", 0.55)
        disruption = {"trigger": 0.55, "triage": 0.5, "rerouting": 0.4, "capacity-rebuild": 0.3, "resolution": 0.15}[phase]
        return {
            "escalation": bounded(disruption + max(0, 14 - inventory) / 28 + max(0.0, 0.55 - transport) * 0.2),
            "negotiation": bounded(0.2 + substitution * 0.3 + transport * 0.2),
            "economic_stress": bounded(0.3 + max(0, 20 - inventory) / 26 + max(0.0, 0.5 - substitution) * 0.2),
        }

    def validate_state(self, state: Any) -> list[str]:
        phase = getattr(state, "phase", None) or ""
        return [] if phase in self.PHASES else [f"unsupported phase: {phase}"]
