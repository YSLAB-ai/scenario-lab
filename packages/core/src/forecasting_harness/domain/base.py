from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from forecasting_harness.models import BeliefState, ObjectiveProfile
    from forecasting_harness.workflow.models import AssumptionSummary, EvidencePacketItem, IntakeDraft


class InteractionModel(StrEnum):
    EVENT_DRIVEN = "event_driven"
    SEQUENTIAL_TURN = "sequential_turn"
    SIMULTANEOUS_MOVE = "simultaneous_move"


class DomainPack(ABC):
    GENERIC_ACTOR_UTILITY_METRIC_KEYS = ("escalation", "negotiation", "economic_stress")

    @abstractmethod
    def slug(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def interaction_model(self) -> InteractionModel:
        raise NotImplementedError

    def canonical_phases(self) -> list[str]:
        return []

    def validate_intake(self, intake: "IntakeDraft") -> list[str]:
        return []

    def suggest_related_actors(self, intake: "IntakeDraft") -> list[str]:
        return []

    def retrieval_filters(self, intake: "IntakeDraft") -> dict[str, str]:
        return {}

    def search_config(self) -> dict[str, int | float]:
        return {}

    @abstractmethod
    def extend_schema(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def suggest_questions(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def propose_actions(self, state: "BeliefState") -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def sample_transition(self, state: "BeliefState", action_context: dict[str, Any]) -> list["BeliefState"]:
        raise NotImplementedError

    @abstractmethod
    def score_state(self, state: "BeliefState") -> dict[str, float]:
        """Return system metrics for a state.

        Packs that rely on the shared actor-aware defaults must include
        `escalation`, `negotiation`, and `economic_stress` in this mapping.
        """
        raise NotImplementedError

    def score_actor_impacts(self, state: "BeliefState") -> dict[str, dict[str, float]]:
        return self._generic_actor_impacts(state)

    @abstractmethod
    def validate_state(self, state: "BeliefState") -> list[str]:
        raise NotImplementedError

    def freshness_policy(self) -> dict[str, float]:
        return {}

    def is_terminal(self, state: "BeliefState", depth: int) -> bool:
        return False

    def infer_pack_fields(
        self,
        intake: "IntakeDraft",
        assumptions: "AssumptionSummary",
        approved_evidence_items: list["EvidencePacketItem"],
    ) -> dict[str, Any]:
        return {}

    def default_objective_profile(self) -> "ObjectiveProfile":
        from forecasting_harness.objectives import default_objective_profile as _default_objective_profile

        return _default_objective_profile()

    def recommend_objective_profile(
        self,
        intake: "IntakeDraft",
        state: "BeliefState",
    ) -> "ObjectiveProfile":
        return self._generic_recommended_objective_profile(state)

    def _generic_actor_impacts(self, state: "BeliefState") -> dict[str, dict[str, float]]:
        system_metrics = self._actor_utility_system_metrics(state)
        escalation = _bounded_metric(system_metrics.get("escalation", 0.0))
        negotiation = _bounded_metric(system_metrics.get("negotiation", 0.0))
        economic_stress = _bounded_metric(system_metrics.get("economic_stress", 0.0))
        pressure_signal = _bounded_metric(escalation * 0.45 + economic_stress * 0.35 + (1.0 - negotiation) * 0.2)
        stability_signal = _bounded_metric(negotiation * 0.45 + (1.0 - escalation) * 0.3 + (1.0 - economic_stress) * 0.25)

        actor_impacts: dict[str, dict[str, float]] = {}
        for actor in getattr(state, "actors", []):
            profile = getattr(actor, "behavior_profile", None)
            if profile is None:
                continue
            serialized = profile.model_dump(exclude_none=True)
            if not serialized:
                continue

            actor_impacts[actor.actor_id] = {
                "domestic_sensitivity": _bounded_metric(
                    (profile.domestic_sensitivity or 0.0) * (0.65 + pressure_signal * 0.45)
                ),
                "economic_pain_tolerance": _bounded_metric(
                    (profile.economic_pain_tolerance or 0.0)
                    * (0.65 + stability_signal * 0.2 - economic_stress * 0.25)
                ),
                "negotiation_openness": _bounded_metric(
                    (profile.negotiation_openness or 0.0) * (0.55 + negotiation * 0.35 - escalation * 0.15)
                ),
                "reputational_sensitivity": _bounded_metric(
                    (profile.reputational_sensitivity or 0.0) * (0.65 + pressure_signal * 0.35)
                ),
                "alliance_dependence": _bounded_metric(
                    (profile.alliance_dependence or 0.0) * (0.6 + negotiation * 0.15 + pressure_signal * 0.2)
                ),
                "coercive_bias": _bounded_metric(
                    (profile.coercive_bias or 0.0) * (0.5 + escalation * 0.35 - negotiation * 0.1)
                ),
            }
        return actor_impacts

    def _generic_recommended_objective_profile(self, state: "BeliefState") -> "ObjectiveProfile":
        from forecasting_harness.objectives import objective_profile_by_name

        system_metrics = self._actor_utility_system_metrics(state)
        escalation = _bounded_metric(system_metrics.get("escalation", 0.0))
        negotiation = _bounded_metric(system_metrics.get("negotiation", 0.0))
        economic_stress = _bounded_metric(system_metrics.get("economic_stress", 0.0))
        pressure_signal = _bounded_metric(escalation * 0.45 + economic_stress * 0.35 + (1.0 - negotiation) * 0.2)

        scored_actors: list[tuple[float, str]] = []
        for actor in getattr(state, "actors", []):
            profile = getattr(actor, "behavior_profile", None)
            if profile is None:
                continue
            domestic = profile.domestic_sensitivity or 0.0
            reputation = profile.reputational_sensitivity or 0.0
            alliance = profile.alliance_dependence or 0.0
            negotiation_openness = profile.negotiation_openness or 0.0
            actor_signal = (
                domestic * 0.5
                + reputation * 0.25
                + alliance * 0.15
                + max(0.0, 1.0 - negotiation_openness) * 0.1
            )
            if actor_signal > 0.0:
                scored_actors.append((actor_signal, actor.actor_id))

        if not scored_actors:
            return self.default_objective_profile()

        scored_actors.sort(reverse=True)
        top_signal, top_actor_id = scored_actors[0]
        second_signal = scored_actors[1][0] if len(scored_actors) > 1 else 0.0
        if pressure_signal >= 0.45 and top_signal >= 0.65 and (top_signal - second_signal >= 0.05 or top_signal >= 0.82):
            return objective_profile_by_name("domestic-politics-first").model_copy(
                update={"focal_actor_id": top_actor_id}
            )
        return self.default_objective_profile()

    def _actor_utility_system_metrics(self, state: "BeliefState") -> dict[str, float]:
        system_metrics = self.score_state(state)
        missing = [
            metric_name
            for metric_name in self.GENERIC_ACTOR_UTILITY_METRIC_KEYS
            if metric_name not in system_metrics
        ]
        if missing and self._state_has_actor_preferences(state):
            required = ", ".join(self.GENERIC_ACTOR_UTILITY_METRIC_KEYS)
            raise ValueError(f"score_state must include metrics: {required}")
        return system_metrics

    def _state_has_actor_preferences(self, state: "BeliefState") -> bool:
        for actor in getattr(state, "actors", []):
            profile = getattr(actor, "behavior_profile", None)
            if profile is not None and profile.model_dump(exclude_none=True):
                return True
        return False


def _bounded_metric(value: float | int | None) -> float:
    numeric_value = 0.0 if value is None else float(value)
    return max(0.0, min(1.0, numeric_value))
