from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from forecasting_harness.domain.base import InteractionModel

FieldStatus = Literal["observed", "inferred", "unknown"]


class BehaviorProfile(BaseModel):
    risk_tolerance: float | None = None
    escalation_tolerance: float | None = None
    notes: str | None = None


class Actor(BaseModel):
    actor_id: str
    name: str
    behavior_profile: BehaviorProfile | None = None


class BeliefField(BaseModel):
    value: Any
    normalized_value: Any
    status: FieldStatus
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    confidence: float
    last_updated_at: str
    evidence_type: str | None = None
    time_scope: str | None = None
    applicability_notes: str | None = None


class ObjectiveProfile(BaseModel):
    name: str
    metric_weights: dict[str, float]
    veto_thresholds: dict[str, float]
    risk_tolerance: float
    asymmetry_penalties: dict[str, float]

    def scalarize(self, metrics: dict[str, float]) -> float:
        return sum(self.metric_weights.get(metric, 0.0) * value for metric, value in metrics.items())


class BeliefState(BaseModel):
    run_id: str
    interaction_model: InteractionModel
    actors: list[Actor]
    fields: dict[str, BeliefField]
    objectives: dict[str, str]
    capabilities: dict[str, str]
    constraints: dict[str, str]
    unknowns: list[str]
    current_epoch: str
    horizon: str
