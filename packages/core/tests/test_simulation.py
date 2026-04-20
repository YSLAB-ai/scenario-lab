from types import SimpleNamespace

import pytest

from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.models import ObjectiveProfile
from forecasting_harness.simulation import SimulationEngine, scalarize_node_value
from forecasting_harness.simulation.cache import should_reuse_node


def test_scalarize_node_value_uses_objective_profile_weights() -> None:
    profile = ObjectiveProfile(
        name="avoid-escalation",
        metric_weights={"escalation": -1.0, "negotiation": 0.5},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
    )

    assert scalarize_node_value({"escalation": 0.6, "negotiation": 0.2}, profile) == -0.5


def test_should_reuse_node_rejects_unsupported_dependency_keys() -> None:
    node = {"node_id": "n1", "dependencies": {"fields": ["fuel_days"], "metrics": ["economic_stress"]}}
    compatibility = {"changed_fields": ["morale"], "compatible": True}

    with pytest.raises(ValueError, match="unsupported dependency keys"):
        should_reuse_node(node, compatibility)


def test_should_reuse_node_rejects_unsupported_dependency_keys_when_incompatible() -> None:
    node = {"node_id": "n1", "dependencies": {"fields": ["fuel_days"], "metrics": ["economic_stress"]}}
    compatibility = {"changed_fields": [], "compatible": False}

    with pytest.raises(ValueError, match="unsupported dependency keys"):
        should_reuse_node(node, compatibility)


def test_should_reuse_node_allows_disjoint_field_dependencies() -> None:
    node = {"node_id": "n1", "dependencies": {"fields": ["fuel_days"]}}
    compatibility = {"changed_fields": ["morale"], "compatible": True}

    assert should_reuse_node(node, compatibility) is True


def test_should_reuse_node_rejects_incompatible_result() -> None:
    node = {"node_id": "n1", "dependencies": {"fields": ["fuel_days"]}}
    compatibility = {"changed_fields": [], "compatible": False}

    assert should_reuse_node(node, compatibility) is False


def test_should_reuse_node_rejects_overlapping_changed_fields() -> None:
    node = {"node_id": "n1", "dependencies": {"fields": ["fuel_days", "morale"]}}
    compatibility = {"changed_fields": ["morale"], "compatible": True}

    assert should_reuse_node(node, compatibility) is False


def test_simulation_engine_sorts_branches_by_score() -> None:
    class DomainPackStub:
        def interaction_model(self) -> InteractionModel:
            return InteractionModel.EVENT_DRIVEN

        def propose_actions(self, state: object) -> list[dict[str, object]]:
            return [
                {"branch_id": "b-1", "label": "low", "dependencies": {"fields": ["fuel_days"]}},
                {"branch_id": "b-2", "label": "high", "dependencies": {"fields": ["morale"]}},
            ]

        def sample_transition(self, state: object, action_context: dict[str, object]) -> list[object]:
            if action_context["branch_id"] == "b-1":
                return [SimpleNamespace(score_metrics={"escalation": 0.8, "negotiation": 0.0})]
            return [SimpleNamespace(score_metrics={"escalation": 0.1, "negotiation": 0.8})]

        def score_state(self, state: object) -> dict[str, float]:
            return state.score_metrics

    profile = ObjectiveProfile(
        name="avoid-escalation",
        metric_weights={"escalation": -1.0, "negotiation": 0.5},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
    )
    engine = SimulationEngine(DomainPackStub(), profile)
    state = SimpleNamespace(interaction_model=InteractionModel.EVENT_DRIVEN)

    result = engine.run(state)

    assert [branch["branch_id"] for branch in result["branches"]] == ["b-2", "b-1"]


def test_simulation_engine_rejects_interaction_model_mismatch() -> None:
    class DomainPackStub:
        def interaction_model(self) -> InteractionModel:
            return InteractionModel.EVENT_DRIVEN

        def propose_actions(self, state: object) -> list[dict[str, object]]:
            return []

        def sample_transition(self, state: object, action_context: dict[str, object]) -> list[object]:
            return []

        def score_state(self, state: object) -> dict[str, float]:
            return {}

    profile = ObjectiveProfile(
        name="avoid-escalation",
        metric_weights={"escalation": -1.0, "negotiation": 0.5},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
    )
    engine = SimulationEngine(DomainPackStub(), profile)
    state = SimpleNamespace(interaction_model=InteractionModel.SEQUENTIAL_TURN)

    with pytest.raises(ValueError, match="interaction model mismatch"):
        engine.run(state)
