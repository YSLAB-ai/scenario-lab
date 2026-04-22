from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.domain.template_utils import (
    apply_manifest_action_biases,
    apply_manifest_state_overlays,
    bounded,
    compose_signal_text,
    numeric_field,
    state_signal_text,
    with_updates,
)
from forecasting_harness.evolution.models import (
    ActionTemplate,
    ActionTransitionOutcome,
    DomainBlueprint,
    FieldInferenceRule,
    FieldRuleTermDelta,
)


class GeneratedTemplatePack(DomainPack):
    BLUEPRINT: DomainBlueprint

    def slug(self) -> str:
        return self.BLUEPRINT.slug

    def interaction_model(self) -> InteractionModel:
        return InteractionModel.EVENT_DRIVEN

    def canonical_phases(self) -> list[str]:
        return list(self.BLUEPRINT.canonical_stages)

    def validate_intake(self, intake: Any) -> list[str]:
        issues: list[str] = []
        focus_entities = list(getattr(intake, "focus_entities", []))
        rule = self.BLUEPRINT.focus_entity_rule
        if len(focus_entities) < rule.min_count:
            issues.append(f"{self.slug()} requires at least {rule.min_count} focus entities")
        if rule.exact_count is not None and len(focus_entities) != rule.exact_count:
            issues.append(f"{self.slug()} requires exactly {rule.exact_count} focus entities")
        if getattr(intake, "current_stage", "") not in self.BLUEPRINT.canonical_stages:
            issues.append(f"unsupported phase: {getattr(intake, 'current_stage', '')}")
        return issues

    def suggest_related_actors(self, intake: Any) -> list[str]:
        return list(self.BLUEPRINT.suggested_related_actors)

    def retrieval_filters(self, intake: Any) -> dict[str, str]:
        return {"domain": self.slug()}

    def suggest_questions(self) -> list[str]:
        return list(self.BLUEPRINT.follow_up_questions)

    def extend_schema(self) -> dict[str, Any]:
        return dict(self.BLUEPRINT.field_schema)

    def infer_pack_fields(self, intake: Any, assumptions: Any, approved_evidence_items: list[Any]) -> dict[str, Any]:
        return self._infer_pack_fields_from_blueprint(intake, assumptions, approved_evidence_items)

    def _infer_pack_fields_from_blueprint(
        self,
        intake: Any,
        assumptions: Any,
        approved_evidence_items: list[Any],
    ) -> dict[str, Any]:
        evidence_passages = [passage for item in approved_evidence_items for passage in getattr(item, "raw_passages", [])]
        text = compose_signal_text(
            getattr(intake, "event_framing", ""),
            getattr(intake, "current_development", ""),
            getattr(intake, "known_constraints", []),
            getattr(intake, "known_unknowns", []),
            getattr(assumptions, "summary", []),
            evidence_passages,
        )

        inferred: dict[str, Any] = {}
        for field_name, rule in self.BLUEPRINT.field_inference_rules.items():
            inferred[field_name] = self._infer_field(rule, text)
        return apply_manifest_state_overlays(text=text, slug=self.slug(), field_values=inferred)

    def _infer_field(self, rule: FieldInferenceRule, text: str) -> Any:
        if rule.field_type == "str":
            value = str(rule.base)
            for term_rule in rule.term_deltas:
                if any(term in text.lower() for term in term_rule.terms) and term_rule.value is not None:
                    value = term_rule.value
            return value
        if rule.field_type == "bool":
            current = bool(rule.base)
            for term_rule in rule.term_deltas:
                if any(term in text.lower() for term in term_rule.terms):
                    current = bool(term_rule.value) if term_rule.value is not None else True
            return current

        numeric_value = float(rule.base)
        lowered = text.lower()
        for term_rule in rule.term_deltas:
            if any(term in lowered for term in term_rule.terms):
                numeric_value += term_rule.delta
        if rule.field_type == "int":
            return int(round(numeric_value))
        return round(bounded(numeric_value), 3)

    def is_terminal(self, state: Any, depth: int) -> bool:
        return getattr(state, "phase", None) == self.BLUEPRINT.canonical_stages[-1]

    def propose_actions(self, state: Any) -> list[dict[str, Any]]:
        return self._propose_actions_from_blueprint(state)

    def _propose_actions_from_blueprint(self, state: Any) -> list[dict[str, Any]]:
        stage = getattr(state, "phase", None) or self.BLUEPRINT.canonical_stages[0]
        actions: list[dict[str, Any]] = []
        for template in self.BLUEPRINT.action_templates:
            if template.stage != stage:
                continue
            prior = template.base_prior
            for field_name, weight in template.field_weights.items():
                prior += numeric_field(state, field_name, 0.0) * weight
            actions.append(
                {
                    "action_id": template.action_id,
                    "label": template.label,
                    "prior": bounded(prior),
                    "dependencies": {"fields": sorted(template.field_weights)},
                }
            )
        return apply_manifest_action_biases(text=state_signal_text(state), actions=actions, slug=self.slug())

    def sample_transition(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        return self._sample_transition_from_blueprint(state, action_context)

    def _sample_transition_from_blueprint(self, state: Any, action_context: dict[str, Any]) -> list[Any]:
        action_id = action_context.get("action_id") or action_context.get("branch_id")
        for template in self.BLUEPRINT.action_templates:
            if template.action_id != action_id:
                continue
            if template.outcomes:
                outcomes: list[dict[str, Any]] = []
                for outcome in template.outcomes:
                    if not self._outcome_matches(state, outcome):
                        continue
                    updates = self._merge_field_updates(state, outcome.field_updates)
                    outcomes.append(
                        {
                            "next_state": with_updates(state, phase=outcome.next_stage, field_updates=updates),
                            "weight": outcome.weight,
                            "outcome_id": outcome.outcome_id,
                        }
                    )
                if outcomes:
                    return outcomes
            updates: dict[str, Any] = {}
            for field_name, value in template.field_updates.items():
                current = getattr(state, "fields", {}).get(field_name)
                if isinstance(value, (int, float)) and current is not None and isinstance(current.normalized_value, (int, float)):
                    if isinstance(current.normalized_value, int):
                        updates[field_name] = int(current.normalized_value + value)
                    else:
                        updates[field_name] = bounded(float(current.normalized_value) + float(value))
                else:
                    updates[field_name] = value
            return [with_updates(state, phase=template.next_stage, field_updates=updates)]
        return [state]

    def _merge_field_updates(
        self,
        state: Any,
        field_updates: dict[str, float | int | str | bool],
    ) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        for field_name, value in field_updates.items():
            current = getattr(state, "fields", {}).get(field_name)
            if isinstance(value, (int, float)) and current is not None and isinstance(current.normalized_value, (int, float)):
                if isinstance(current.normalized_value, int):
                    updates[field_name] = int(current.normalized_value + value)
                else:
                    updates[field_name] = bounded(float(current.normalized_value) + float(value))
            else:
                updates[field_name] = value
        return updates

    def _outcome_matches(self, state: Any, outcome: ActionTransitionOutcome) -> bool:
        for field_name, minimum in outcome.field_minimums.items():
            if numeric_field(state, field_name, 0.0) < minimum:
                return False
        for field_name, maximum in outcome.field_maximums.items():
            if numeric_field(state, field_name, 0.0) > maximum:
                return False
        return True

    def score_state(self, state: Any) -> dict[str, float]:
        scores: dict[str, float] = {}
        for metric_name in ("escalation", "negotiation", "economic_stress"):
            weights = self.BLUEPRINT.scoring_weights.get(metric_name, {})
            total = 0.0
            for field_name, weight in weights.items():
                total += numeric_field(state, field_name, 0.0) * weight
            scores[metric_name] = bounded(total)
        return scores or {"escalation": 0.0, "negotiation": 0.0, "economic_stress": 0.0}

    def recommend_objective_profile(self, intake: Any, state: Any):
        return self._recommend_objective_profile_from_blueprint(intake, state)

    def _recommend_objective_profile_from_blueprint(self, intake: Any, state: Any):
        from forecasting_harness.objectives import objective_profile_by_name

        for rule in self.BLUEPRINT.objective_profile_rules:
            if self._objective_rule_matches(state, rule):
                return objective_profile_by_name(rule.profile_name)
        return super().recommend_objective_profile(intake, state)

    def _objective_rule_matches(self, state: Any, rule: Any) -> bool:
        for field_name, minimum in rule.field_minimums.items():
            if numeric_field(state, field_name, 0.0) < minimum:
                return False
        for field_name, maximum in rule.field_maximums.items():
            if numeric_field(state, field_name, 0.0) > maximum:
                return False
        return True

    def validate_state(self, state: Any) -> list[str]:
        phase = getattr(state, "phase", None) or ""
        return [] if phase in self.BLUEPRINT.canonical_stages else [f"unsupported phase: {phase}"]
