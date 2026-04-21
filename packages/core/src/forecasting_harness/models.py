from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from forecasting_harness.domain.base import InteractionModel

FieldStatus = Literal["observed", "inferred", "unknown"]


class BehaviorProfile(BaseModel):
    risk_tolerance: float | None = None
    escalation_tolerance: float | None = None
    domestic_sensitivity: float | None = Field(default=None, ge=0.0, le=1.0)
    economic_pain_tolerance: float | None = Field(default=None, ge=0.0, le=1.0)
    negotiation_openness: float | None = Field(default=None, ge=0.0, le=1.0)
    reputational_sensitivity: float | None = Field(default=None, ge=0.0, le=1.0)
    alliance_dependence: float | None = Field(default=None, ge=0.0, le=1.0)
    coercive_bias: float | None = Field(default=None, ge=0.0, le=1.0)
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
    confidence: float = Field(ge=0.0, le=1.0)
    last_updated_at: datetime
    evidence_type: str | None = None
    time_scope: str | None = None
    applicability_notes: str | None = None


class ObjectiveProfile(BaseModel):
    name: str
    metric_weights: dict[str, float]
    veto_thresholds: dict[str, float]
    risk_tolerance: float = Field(ge=0.0, le=1.0)
    asymmetry_penalties: dict[str, float]
    actor_metric_weights: dict[str, float] = Field(default_factory=dict)
    actor_weights: dict[str, float] = Field(default_factory=dict)
    aggregation_mode: Literal["balanced-system", "focal-actor"] = "balanced-system"
    focal_actor_id: str | None = None
    destabilization_penalty: float = 0.0

    def scalarize(self, metrics: dict[str, float]) -> float:
        unknown_metrics = sorted(metric for metric in metrics if metric not in self.metric_weights)
        if unknown_metrics:
            raise ValueError(f"unknown metric names: {', '.join(unknown_metrics)}")
        return sum(self.metric_weights[metric] * value for metric, value in metrics.items())

    def aggregate(
        self,
        system_metrics: dict[str, float],
        actor_metrics: dict[str, dict[str, float]],
    ) -> tuple[float, dict[str, float]]:
        system_score = self.scalarize(system_metrics)
        if not self.actor_metric_weights:
            breakdown = {
                "system": system_score,
                "actors": 0.0,
                "destabilization_penalty": 0.0,
            }
            return sum(breakdown.values()), breakdown
        actor_score = self._aggregate_actor_metrics(actor_metrics)
        destabilization_signal = max(
            (metrics.get("domestic_sensitivity", 0.0) for metrics in actor_metrics.values()),
            default=0.0,
        )
        destabilization_component = -self.destabilization_penalty * destabilization_signal
        breakdown = {
            "system": system_score,
            "actors": actor_score,
            "destabilization_penalty": destabilization_component,
        }
        return sum(breakdown.values()), breakdown

    def _aggregate_actor_metrics(self, actor_metrics: dict[str, dict[str, float]]) -> float:
        if not actor_metrics or not self.actor_metric_weights:
            return 0.0

        weighted_scores: list[tuple[float, float]] = []
        for actor_id, metrics in actor_metrics.items():
            unknown_metrics = sorted(metric for metric in metrics if metric not in self.actor_metric_weights)
            if unknown_metrics:
                raise ValueError(f"unknown actor metric names: {', '.join(unknown_metrics)}")
            actor_score = sum(self.actor_metric_weights[metric] * value for metric, value in metrics.items())
            actor_weight = self.actor_weights.get(actor_id, 1.0)
            if self.aggregation_mode == "focal-actor" and actor_id == self.focal_actor_id:
                actor_weight *= 2.0
            weighted_scores.append((actor_score, actor_weight))

        total_weight = sum(weight for _, weight in weighted_scores)
        if total_weight <= 0.0:
            return 0.0
        return sum(score * weight for score, weight in weighted_scores) / total_weight


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
    revision_id: str | None = None
    domain_pack: str | None = None
    phase: str | None = None
    approved_evidence_ids: list[str] = Field(default_factory=list)
