from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from forecasting_harness.models import BeliefState, ObjectiveProfile
    from forecasting_harness.workflow.models import IntakeDraft


class InteractionModel(StrEnum):
    EVENT_DRIVEN = "event_driven"
    SEQUENTIAL_TURN = "sequential_turn"
    SIMULTANEOUS_MOVE = "simultaneous_move"


class DomainPack(ABC):
    @abstractmethod
    def slug(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def interaction_model(self) -> InteractionModel:
        raise NotImplementedError

    def canonical_phases(self) -> list[str]:
        return []

    def suggest_related_actors(self, intake: "IntakeDraft") -> list[str]:
        return []

    def retrieval_filters(self, intake: "IntakeDraft") -> dict[str, str]:
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
        raise NotImplementedError

    @abstractmethod
    def validate_state(self, state: "BeliefState") -> list[str]:
        raise NotImplementedError

    def freshness_policy(self) -> dict[str, float]:
        return {}

    def default_objective_profile(self) -> "ObjectiveProfile":
        from forecasting_harness.objectives import default_objective_profile as _default_objective_profile

        return _default_objective_profile()
