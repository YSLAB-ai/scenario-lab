from types import SimpleNamespace

import pytest

from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.domain.generic_event import GenericEventPack
from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack
from forecasting_harness.models import BeliefState
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


def test_simulation_engine_returns_mcts_metadata_and_multi_step_backed_up_scores() -> None:
    class DomainPackStub:
        def interaction_model(self) -> InteractionModel:
            return InteractionModel.EVENT_DRIVEN

        def validate_state(self, state: object) -> list[str]:
            return []

        def search_config(self) -> dict[str, float]:
            return {"iterations": 18, "max_depth": 3, "rollout_depth": 3, "c_puct": 1.2}

        def is_terminal(self, state: object, depth: int) -> bool:
            return getattr(state, "name", "").startswith("terminal")

        def propose_actions(self, state: object) -> list[dict[str, object]]:
            if state.name == "root":
                return [
                    {
                        "branch_id": "low-path",
                        "label": "Low path",
                        "prior": 0.6,
                        "dependencies": {"fields": ["fuel_days"]},
                    },
                    {
                        "branch_id": "setup-path",
                        "label": "Setup path",
                        "prior": 0.4,
                        "dependencies": {"fields": ["morale"]},
                    },
                ]
            if state.name == "low-1":
                return [{"action_id": "coast", "label": "Coast", "prior": 1.0}]
            if state.name == "setup-1":
                return [{"action_id": "close-deal", "label": "Close deal", "prior": 1.0}]
            return []

        def sample_transition(self, state: object, action_context: dict[str, object]) -> list[object]:
            if state.name == "root" and action_context.get("branch_id") == "low-path":
                return [
                    SimpleNamespace(
                        name="low-1",
                        score_metrics={"escalation": 0.1, "negotiation": 0.4},
                        interaction_model=InteractionModel.EVENT_DRIVEN,
                    )
                ]
            if state.name == "root" and action_context.get("branch_id") == "setup-path":
                return [
                    SimpleNamespace(
                        name="setup-1",
                        score_metrics={"escalation": 0.4, "negotiation": 0.2},
                        interaction_model=InteractionModel.EVENT_DRIVEN,
                    )
                ]
            if state.name == "low-1":
                return [
                    SimpleNamespace(
                        name="terminal-low",
                        score_metrics={"escalation": 0.7, "negotiation": 0.1},
                        interaction_model=InteractionModel.EVENT_DRIVEN,
                    )
                ]
            if state.name == "setup-1":
                return [
                    SimpleNamespace(
                        name="terminal-win",
                        score_metrics={"escalation": 0.1, "negotiation": 0.9},
                        interaction_model=InteractionModel.EVENT_DRIVEN,
                    )
                ]
            return []

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
    state = SimpleNamespace(name="root", interaction_model=InteractionModel.EVENT_DRIVEN)

    result = engine.run(state)

    assert result["search_mode"] == "mcts"
    assert result["iterations"] == 18
    assert result["node_count"] >= 5
    assert result["max_depth_reached"] >= 2
    assert [branch["branch_id"] for branch in result["branches"]] == ["setup-path", "low-path"]
    assert result["branches"][0]["visits"] > 0
    assert result["branches"][0]["prior"] == pytest.approx(0.4)
    assert result["branches"][0]["metrics"]["negotiation"] == pytest.approx(0.9)
    assert result["branches"][0]["score"] > result["branches"][1]["score"]


def test_simulation_engine_rejects_interaction_model_mismatch() -> None:
    class DomainPackStub:
        def interaction_model(self) -> InteractionModel:
            return InteractionModel.EVENT_DRIVEN

        def validate_state(self, state: object) -> list[str]:
            return []

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


def test_simulation_engine_rejects_invalid_state_before_generating_branches() -> None:
    class DomainPackStub:
        def interaction_model(self) -> InteractionModel:
            return InteractionModel.EVENT_DRIVEN

        def validate_state(self, state: object) -> list[str]:
            return ["fuel_days must be non-negative"]

        def propose_actions(self, state: object) -> list[dict[str, object]]:
            raise AssertionError("propose_actions should not run for invalid state")

        def sample_transition(self, state: object, action_context: dict[str, object]) -> list[object]:
            raise AssertionError("sample_transition should not run for invalid state")

        def score_state(self, state: object) -> dict[str, float]:
            raise AssertionError("score_state should not run for invalid state")

    profile = ObjectiveProfile(
        name="avoid-escalation",
        metric_weights={"escalation": -1.0, "negotiation": 0.5},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
    )
    engine = SimulationEngine(DomainPackStub(), profile)
    state = SimpleNamespace(interaction_model=InteractionModel.EVENT_DRIVEN)

    with pytest.raises(ValueError, match="invalid state"):
        engine.run(state)


def test_simulation_engine_assigns_deterministic_fallback_branch_ids() -> None:
    class DomainPackStub:
        def interaction_model(self) -> InteractionModel:
            return InteractionModel.EVENT_DRIVEN

        def validate_state(self, state: object) -> list[str]:
            return []

        def is_terminal(self, state: object, depth: int) -> bool:
            return depth > 0

        def propose_actions(self, state: object) -> list[dict[str, object]]:
            return [
                {"action_id": "signal-negotiation", "label": "Signal negotiation"},
                {"action_id": "stabilize-front", "label": "Stabilize front"},
            ]

        def sample_transition(self, state: object, action_context: dict[str, object]) -> list[object]:
            if action_context["action_id"] == "signal-negotiation":
                return [
                    SimpleNamespace(score_metrics={"escalation": 0.2, "negotiation": 0.6}),
                    SimpleNamespace(score_metrics={"escalation": 0.4, "negotiation": 0.4}),
                ]
            return [SimpleNamespace(score_metrics={"escalation": 0.3, "negotiation": 0.5})]

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

    assert [branch["branch_id"] for branch in result["branches"]] == [
        "signal-negotiation",
        "stabilize-front",
        "signal-negotiation-2",
    ]


def test_simulation_engine_makes_shared_fallback_branch_ids_globally_unique() -> None:
    class DomainPackStub:
        def interaction_model(self) -> InteractionModel:
            return InteractionModel.EVENT_DRIVEN

        def validate_state(self, state: object) -> list[str]:
            return []

        def is_terminal(self, state: object, depth: int) -> bool:
            return depth > 0

        def propose_actions(self, state: object) -> list[dict[str, object]]:
            return [
                {"action_id": "signal-negotiation", "label": "Signal negotiation A"},
                {"action_id": "signal-negotiation", "label": "Signal negotiation B"},
            ]

        def sample_transition(self, state: object, action_context: dict[str, object]) -> list[object]:
            if action_context["label"] == "Signal negotiation A":
                return [SimpleNamespace(score_metrics={"escalation": 0.2, "negotiation": 0.8})]
            return [SimpleNamespace(score_metrics={"escalation": 0.1, "negotiation": 0.4})]

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

    assert sorted(branch["branch_id"] for branch in result["branches"]) == [
        "signal-negotiation",
        "signal-negotiation-2",
    ]


def test_simulation_engine_supports_weighted_transition_outcomes() -> None:
    class DomainPackStub:
        def interaction_model(self) -> InteractionModel:
            return InteractionModel.EVENT_DRIVEN

        def validate_state(self, state: object) -> list[str]:
            return []

        def is_terminal(self, state: object, depth: int) -> bool:
            return depth > 0

        def propose_actions(self, state: object) -> list[dict[str, object]]:
            return [{"branch_id": "signal", "label": "Signal", "prior": 0.5}]

        def sample_transition(self, state: object, action_context: dict[str, object]) -> list[object]:
            return [
                {
                    "outcome_id": "warning",
                    "weight": 0.7,
                    "next_state": SimpleNamespace(
                        score_metrics={"escalation": 0.2, "negotiation": 0.5},
                        interaction_model=InteractionModel.EVENT_DRIVEN,
                    ),
                },
                {
                    "outcome_id": "misread",
                    "weight": 0.3,
                    "next_state": SimpleNamespace(
                        score_metrics={"escalation": 0.8, "negotiation": 0.1},
                        interaction_model=InteractionModel.EVENT_DRIVEN,
                    ),
                },
            ]

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

    assert [branch["branch_id"] for branch in result["branches"]] == ["signal", "signal-2"]
    assert result["branches"][0]["prior"] == pytest.approx(0.35)
    assert result["branches"][1]["prior"] == pytest.approx(0.15)


def test_interstate_crisis_pack_transitions_change_follow_on_actions() -> None:
    pack = InterstateCrisisPack()
    root_state = BeliefState(
        run_id="run-1",
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[],
        fields={},
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch="trigger",
        horizon="30d",
        phase="trigger",
    )

    root_actions = [action.get("branch_id") or action.get("action_id") for action in pack.propose_actions(root_state)]
    signaling_state = pack.sample_transition(root_state, pack.propose_actions(root_state)[0])[0]
    signaling_actions = [
        action.get("branch_id") or action.get("action_id") for action in pack.propose_actions(signaling_state)
    ]

    assert root_actions == ["signal", "limited-response", "open-negotiation"]
    assert signaling_state.phase == "signaling"
    assert signaling_actions != root_actions
    assert "intercept" in signaling_actions


def test_generic_event_pack_transitions_change_follow_on_actions() -> None:
    pack = GenericEventPack()
    root_state = BeliefState(
        run_id="run-1",
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[],
        fields={},
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch="start",
        horizon="30d",
        phase=None,
    )

    root_actions = [action.get("branch_id") or action.get("action_id") for action in pack.propose_actions(root_state)]
    next_state = pack.sample_transition(root_state, pack.propose_actions(root_state)[0])[0]
    next_actions = [action.get("branch_id") or action.get("action_id") for action in pack.propose_actions(next_state)]

    assert root_actions == ["maintain-course", "signal-negotiation"]
    assert next_state.phase == "stabilization"
    assert next_actions != root_actions
