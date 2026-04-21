from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

SuggestionProvenance = Literal["user", "self-detected"]
SuggestionCategory = Literal["state-field", "action-bias", "evidence-category", "semantic-alias", "replay-gap"]
SuggestionStatus = Literal["pending", "accepted", "rejected", "promoted"]


class DomainSuggestion(BaseModel):
    suggestion_id: str
    timestamp: datetime
    domain_slug: str
    provenance: SuggestionProvenance
    category: SuggestionCategory
    target: str | None = None
    text: str
    terms: list[str] = Field(default_factory=list)
    status: SuggestionStatus = "pending"


class DomainWeaknessBrief(BaseModel):
    domain_slug: str
    reasons: list[str] = Field(default_factory=list)
    weak_cases: list[str] = Field(default_factory=list)
    suggested_targets: list[str] = Field(default_factory=list)


class DomainEvolutionCandidate(BaseModel):
    domain_slug: str
    updated_manifest: dict[str, Any]
    changed: bool
    applied_suggestion_ids: list[str] = Field(default_factory=list)


class FocusEntityRule(BaseModel):
    min_count: int = 1
    exact_count: int | None = None


class FieldRuleTermDelta(BaseModel):
    terms: list[str] = Field(default_factory=list)
    delta: float = 0.0
    value: str | None = None


class FieldInferenceRule(BaseModel):
    field_type: Literal["float", "int", "str", "bool"]
    base: float | int | str | bool
    term_deltas: list[FieldRuleTermDelta] = Field(default_factory=list)


class ActionTemplate(BaseModel):
    stage: str
    action_id: str
    label: str
    base_prior: float
    field_weights: dict[str, float] = Field(default_factory=dict)
    next_stage: str
    field_updates: dict[str, float | int | str | bool] = Field(default_factory=dict)


class DomainBlueprint(BaseModel):
    slug: str
    class_name: str
    description: str
    focus_entity_rule: FocusEntityRule
    canonical_stages: list[str]
    suggested_related_actors: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    field_schema: dict[str, str] = Field(default_factory=dict)
    actor_categories: list[str] = Field(default_factory=list)
    evidence_categories: list[str] = Field(default_factory=list)
    evidence_category_terms: dict[str, list[str]] = Field(default_factory=dict)
    semantic_alias_groups: list[list[str]] = Field(default_factory=list)
    starter_sources: list[dict[str, str]] = Field(default_factory=list)
    field_inference_rules: dict[str, FieldInferenceRule] = Field(default_factory=dict)
    action_templates: list[ActionTemplate] = Field(default_factory=list)
    scoring_weights: dict[str, dict[str, float]] = Field(default_factory=dict)
    replay_seed_cases: list[dict[str, Any]] = Field(default_factory=list)
