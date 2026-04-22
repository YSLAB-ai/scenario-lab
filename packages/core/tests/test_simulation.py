from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from forecasting_harness.compatibility import compare_belief_states
from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.domain.generic_event import GenericEventPack
from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack
from forecasting_harness.models import Actor, BehaviorProfile, BeliefField, BeliefState
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


def test_objective_profile_can_aggregate_system_and_actor_metrics() -> None:
    profile = ObjectiveProfile(
        name="balanced-system",
        metric_weights={"escalation": -0.4, "negotiation": 0.3},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
        actor_metric_weights={"domestic_sensitivity": 0.5, "coercive_bias": -0.25},
        actor_weights={"alpha": 2.0},
        aggregation_mode="balanced-system",
        destabilization_penalty=0.2,
    )

    aggregate_score, breakdown = profile.aggregate(
        system_metrics={"escalation": 0.3, "negotiation": 0.8},
        actor_metrics={
            "alpha": {"domestic_sensitivity": 0.6, "coercive_bias": 0.2},
            "beta": {"domestic_sensitivity": 0.2, "coercive_bias": 0.4},
        },
    )

    assert aggregate_score == pytest.approx(0.2866666666666666)
    assert breakdown == {
        "system": pytest.approx(0.12),
        "actors": pytest.approx(1 / 6),
        "destabilization_penalty": pytest.approx(0.0),
    }


def test_objective_profile_uses_explicit_focal_weight_for_focal_actor_aggregation() -> None:
    profile = ObjectiveProfile(
        name="domestic-politics-first",
        metric_weights={"escalation": -0.4, "negotiation": 0.3},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
        actor_metric_weights={"domestic_sensitivity": 1.0},
        actor_weights={},
        aggregation_mode="focal-actor",
        focal_actor_id="alpha",
        focal_weight=3.0,
    )

    aggregate_score, breakdown = profile.aggregate(
        system_metrics={"escalation": 0.0, "negotiation": 0.0},
        actor_metrics={
            "alpha": {"domestic_sensitivity": 1.0},
            "beta": {"domestic_sensitivity": 0.0},
        },
    )

    assert aggregate_score == pytest.approx(0.75)
    assert breakdown == {
        "system": pytest.approx(0.0),
        "actors": pytest.approx(0.75),
        "destabilization_penalty": pytest.approx(0.0),
    }


def test_objective_profile_destabilization_penalty_tracks_worst_negative_actor_score() -> None:
    profile = ObjectiveProfile(
        name="balanced-system",
        metric_weights={"escalation": -0.4, "negotiation": 0.3},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
        actor_metric_weights={"domestic_sensitivity": 1.0, "coercive_bias": -2.0},
        actor_weights={},
        aggregation_mode="balanced-system",
        destabilization_penalty=0.2,
    )

    aggregate_score, breakdown = profile.aggregate(
        system_metrics={"escalation": 0.0, "negotiation": 0.0},
        actor_metrics={
            "alpha": {"domestic_sensitivity": 0.4, "coercive_bias": 0.7},
            "beta": {"domestic_sensitivity": 0.6, "coercive_bias": 0.1},
        },
    )

    assert aggregate_score == pytest.approx(-0.5)
    assert breakdown == {
        "system": pytest.approx(0.0),
        "actors": pytest.approx(-0.3),
        "destabilization_penalty": pytest.approx(-0.2),
    }


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


def test_should_reuse_node_allows_reusable_partial_reruns() -> None:
    node = {"node_id": "n1", "dependencies": {"fields": ["fuel_days"]}}
    compatibility = {"changed_fields": ["morale"], "compatible": False, "reusable": True}

    assert should_reuse_node(node, compatibility) is True


def test_compare_belief_states_blocks_reuse_when_actor_behavior_profile_changes() -> None:
    timestamp = datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc)
    previous = BeliefState(
        run_id="run-1",
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[
            Actor(
                actor_id="china",
                name="China",
                behavior_profile=BehaviorProfile(domestic_sensitivity=0.8, coercive_bias=0.4),
            )
        ],
        fields={
            "morale": BeliefField(
                value=0.8,
                normalized_value=0.8,
                status="observed",
                confidence=1.0,
                last_updated_at=timestamp,
            )
        },
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch="trigger",
        horizon="30d",
        phase="trigger",
        domain_pack="generic-event",
    )
    current = previous.model_copy(
        update={
            "actors": [
                previous.actors[0].model_copy(
                    update={"behavior_profile": BehaviorProfile(domestic_sensitivity=0.5, coercive_bias=0.4)}
                )
            ]
        }
    )

    result = compare_belief_states(previous, current, tolerances={"morale": 0.0})

    assert result["compatible"] is False
    assert result["reusable"] is False
    assert result["changed_fields"] == []
    assert "actor behavior_profile changed: china" in result["reasons"]


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


def test_simulation_engine_reports_actor_metrics_and_aggregate_breakdown() -> None:
    class DomainPackStub:
        def interaction_model(self) -> InteractionModel:
            return InteractionModel.EVENT_DRIVEN

        def validate_state(self, state: object) -> list[str]:
            return []

        def search_config(self) -> dict[str, float]:
            return {"iterations": 8, "max_depth": 2, "rollout_depth": 1, "c_puct": 1.0}

        def is_terminal(self, state: object, depth: int) -> bool:
            return depth > 0

        def propose_actions(self, state: object) -> list[dict[str, object]]:
            return [{"branch_id": "pressure-test", "label": "Pressure test", "prior": 1.0}]

        def sample_transition(self, state: object, action_context: dict[str, object]) -> list[object]:
            return [
                SimpleNamespace(
                    interaction_model=InteractionModel.EVENT_DRIVEN,
                    score_metrics={"escalation": 0.2, "negotiation": 0.7},
                    actor_impact_metrics={
                        "alpha": {"domestic_sensitivity": 0.9, "coercive_bias": 0.1},
                        "beta": {"domestic_sensitivity": 0.2, "coercive_bias": 0.8},
                    },
                )
            ]

        def score_state(self, state: object) -> dict[str, float]:
            return state.score_metrics

        def score_actor_impacts(self, state: object) -> dict[str, dict[str, float]]:
            return state.actor_impact_metrics

    profile = ObjectiveProfile(
        name="balanced-system",
        metric_weights={"escalation": -0.4, "negotiation": 0.3},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
        actor_metric_weights={"domestic_sensitivity": 0.5, "coercive_bias": -0.25},
        actor_weights={"alpha": 2.0},
        aggregation_mode="balanced-system",
        destabilization_penalty=0.2,
    )
    engine = SimulationEngine(DomainPackStub(), profile)

    result = engine.run(SimpleNamespace(interaction_model=InteractionModel.EVENT_DRIVEN))

    branch = result["branches"][0]
    assert branch["actor_metrics"] == {
        "alpha": {"domestic_sensitivity": pytest.approx(0.9), "coercive_bias": pytest.approx(0.1)},
        "beta": {"domestic_sensitivity": pytest.approx(0.2), "coercive_bias": pytest.approx(0.8)},
    }
    assert branch["aggregate_score_breakdown"] == {
        "system": pytest.approx(0.13),
        "actors": pytest.approx(0.25),
        "destabilization_penalty": pytest.approx(-0.02),
    }
    assert branch["score"] == pytest.approx(0.36)


def test_simulation_engine_allows_system_only_profile_when_actor_metrics_exist() -> None:
    class DomainPackStub:
        def interaction_model(self) -> InteractionModel:
            return InteractionModel.EVENT_DRIVEN

        def validate_state(self, state: object) -> list[str]:
            return []

        def search_config(self) -> dict[str, float]:
            return {"iterations": 4, "max_depth": 1, "rollout_depth": 1, "c_puct": 1.0}

        def is_terminal(self, state: object, depth: int) -> bool:
            return depth > 0

        def propose_actions(self, state: object) -> list[dict[str, object]]:
            return [{"branch_id": "system-only", "label": "System only", "prior": 1.0}]

        def sample_transition(self, state: object, action_context: dict[str, object]) -> list[object]:
            return [
                SimpleNamespace(
                    interaction_model=InteractionModel.EVENT_DRIVEN,
                    score_metrics={"escalation": 0.2, "negotiation": 0.7},
                    actor_impact_metrics={"alpha": {"domestic_sensitivity": 0.9, "coercive_bias": 0.1}},
                )
            ]

        def score_state(self, state: object) -> dict[str, float]:
            return state.score_metrics

        def score_actor_impacts(self, state: object) -> dict[str, dict[str, float]]:
            return state.actor_impact_metrics

    profile = ObjectiveProfile(
        name="system-only",
        metric_weights={"escalation": -0.4, "negotiation": 0.3},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
    )
    engine = SimulationEngine(DomainPackStub(), profile)

    result = engine.run(SimpleNamespace(interaction_model=InteractionModel.EVENT_DRIVEN))

    branch = result["branches"][0]
    assert branch["actor_metrics"] == {
        "alpha": {"domestic_sensitivity": pytest.approx(0.9), "coercive_bias": pytest.approx(0.1)}
    }
    assert branch["aggregate_score_breakdown"] == {
        "system": pytest.approx(0.13),
        "actors": pytest.approx(0.0),
        "destabilization_penalty": pytest.approx(0.0),
    }
    assert branch["score"] == pytest.approx(0.13)


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


def test_simulation_engine_reports_transposition_hits_for_equivalent_non_root_states() -> None:
    class DomainPackStub:
        def interaction_model(self) -> InteractionModel:
            return InteractionModel.EVENT_DRIVEN

        def validate_state(self, state: object) -> list[str]:
            return []

        def search_config(self) -> dict[str, float]:
            return {"iterations": 16, "max_depth": 4, "rollout_depth": 2, "c_puct": 1.1}

        def is_terminal(self, state: object, depth: int) -> bool:
            return getattr(state, "name", "").startswith("terminal")

        def propose_actions(self, state: object) -> list[dict[str, object]]:
            if state.name == "root":
                return [
                    {"branch_id": "path-a", "label": "Path A", "prior": 0.5},
                    {"branch_id": "path-b", "label": "Path B", "prior": 0.5},
                ]
            if state.name in {"a-1", "b-1"}:
                return [{"action_id": "advance", "label": "Advance", "prior": 1.0}]
            return []

        def sample_transition(self, state: object, action_context: dict[str, object]) -> list[object]:
            if state.name == "root" and action_context.get("branch_id") == "path-a":
                return [SimpleNamespace(name="a-1", score_metrics={"escalation": 0.4, "negotiation": 0.3}, interaction_model=InteractionModel.EVENT_DRIVEN)]
            if state.name == "root" and action_context.get("branch_id") == "path-b":
                return [SimpleNamespace(name="b-1", score_metrics={"escalation": 0.4, "negotiation": 0.3}, interaction_model=InteractionModel.EVENT_DRIVEN)]
            return [SimpleNamespace(name="terminal-shared", score_metrics={"escalation": 0.2, "negotiation": 0.7}, interaction_model=InteractionModel.EVENT_DRIVEN)]

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
    result = engine.run(SimpleNamespace(name="root", interaction_model=InteractionModel.EVENT_DRIVEN))

    assert result["transposition_hits"] > 0
    assert result["state_table_size"] < result["node_count"]


def test_simulation_engine_reuses_compatible_cached_nodes_from_prior_tree() -> None:
    class DomainPackStub:
        def interaction_model(self) -> InteractionModel:
            return InteractionModel.EVENT_DRIVEN

        def validate_state(self, state: object) -> list[str]:
            return []

        def search_config(self) -> dict[str, float]:
            return {"iterations": 6, "max_depth": 3, "rollout_depth": 2, "c_puct": 1.0}

        def is_terminal(self, state: object, depth: int) -> bool:
            return getattr(state, "name", "").startswith("terminal")

        def propose_actions(self, state: object) -> list[dict[str, object]]:
            if state.name == "root":
                return [
                    {"branch_id": "stable-path", "label": "Stable path", "prior": 0.55, "dependencies": {"fields": ["fuel_days"]}},
                    {"branch_id": "changed-path", "label": "Changed path", "prior": 0.45, "dependencies": {"fields": ["morale"]}},
                ]
            if state.name in {"stable-1", "changed-1"}:
                return [{"action_id": "close", "label": "Close", "prior": 1.0}]
            return []

        def sample_transition(self, state: object, action_context: dict[str, object]) -> list[object]:
            if state.name == "root" and action_context.get("branch_id") == "stable-path":
                return [SimpleNamespace(name="stable-1", score_metrics={"escalation": 0.2, "negotiation": 0.5}, interaction_model=InteractionModel.EVENT_DRIVEN)]
            if state.name == "root" and action_context.get("branch_id") == "changed-path":
                return [SimpleNamespace(name="changed-1", score_metrics={"escalation": 0.5, "negotiation": 0.2}, interaction_model=InteractionModel.EVENT_DRIVEN)]
            if state.name == "stable-1":
                return [SimpleNamespace(name="terminal-stable", score_metrics={"escalation": 0.1, "negotiation": 0.8}, interaction_model=InteractionModel.EVENT_DRIVEN)]
            return [SimpleNamespace(name="terminal-changed", score_metrics={"escalation": 0.8, "negotiation": 0.1}, interaction_model=InteractionModel.EVENT_DRIVEN)]

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
    root = SimpleNamespace(name="root", interaction_model=InteractionModel.EVENT_DRIVEN)
    first = engine.run(root)
    second = engine.run(
        root,
        reuse_context={
            "source_revision_id": "r1",
            "compatibility": {"compatible": False, "reusable": True, "changed_fields": ["morale"]},
            "simulation": first,
        },
    )

    assert second["reuse_summary"]["enabled"] is True
    assert second["reuse_summary"]["source_revision_id"] == "r1"
    assert second["reuse_summary"]["reused_nodes"] > 0
    assert second["reuse_summary"]["skipped_nodes"] > 0
    assert second["tree_nodes"]


def test_simulation_engine_rehydrates_task3_accumulators_when_reusing_nodes() -> None:
    class DomainPackStub:
        def interaction_model(self) -> InteractionModel:
            return InteractionModel.EVENT_DRIVEN

        def validate_state(self, state: object) -> list[str]:
            return []

        def search_config(self) -> dict[str, float]:
            return {"iterations": 1, "max_depth": 2, "rollout_depth": 1, "c_puct": 1.0}

        def is_terminal(self, state: object, depth: int) -> bool:
            return getattr(state, "name", "").startswith("terminal")

        def propose_actions(self, state: object) -> list[dict[str, object]]:
            if state.name == "root":
                return [
                    {"branch_id": "stable-path", "label": "Stable path", "prior": 1.0, "dependencies": {"fields": ["fuel_days"]}}
                ]
            if state.name == "stable-1":
                return [{"action_id": "close", "label": "Close", "prior": 1.0}]
            return []

        def sample_transition(self, state: object, action_context: dict[str, object]) -> list[object]:
            if state.name == "root":
                return [
                    SimpleNamespace(
                        name="stable-1",
                        score_metrics={"escalation": 0.2, "negotiation": 0.5},
                        interaction_model=InteractionModel.EVENT_DRIVEN,
                    )
                ]
            return [
                SimpleNamespace(
                    name="terminal-stable",
                    score_metrics={"escalation": 0.1, "negotiation": 0.8},
                    actor_impact_metrics={"alpha": {"domestic_sensitivity": 0.9, "coercive_bias": 0.1}},
                    interaction_model=InteractionModel.EVENT_DRIVEN,
                )
            ]

        def score_state(self, state: object) -> dict[str, float]:
            return state.score_metrics

        def score_actor_impacts(self, state: object) -> dict[str, dict[str, float]]:
            return getattr(state, "actor_impact_metrics", {})

    profile = ObjectiveProfile(
        name="balanced-system",
        metric_weights={"escalation": -0.4, "negotiation": 0.3},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
        actor_metric_weights={"domestic_sensitivity": 0.5, "coercive_bias": -0.25},
        actor_weights={},
        aggregation_mode="balanced-system",
        destabilization_penalty=0.2,
    )
    engine = SimulationEngine(DomainPackStub(), profile)
    root = SimpleNamespace(name="root", interaction_model=InteractionModel.EVENT_DRIVEN)
    first = engine.run(root)
    second = engine.run(
        root,
        reuse_context={
            "source_revision_id": "r1",
            "compatibility": {"compatible": True, "changed_fields": []},
            "simulation": first,
        },
    )

    reused_node = next(node for node in second["tree_nodes"] if node["node_id"] == "root/stable-path")

    assert reused_node["visits"] == 1
    assert reused_node["value_sum"] == pytest.approx(0.625)
    assert reused_node["actor_metric_sums"] == {
        "alpha": {"domestic_sensitivity": pytest.approx(0.9), "coercive_bias": pytest.approx(0.1)}
    }
    assert reused_node["aggregate_score_breakdown_sums"] == {
        "system": pytest.approx(0.2),
        "actors": pytest.approx(0.425),
        "destabilization_penalty": pytest.approx(0.0),
    }


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
    transition = pack.sample_transition(root_state, pack.propose_actions(root_state)[0])[0]
    signaling_state = transition["next_state"] if isinstance(transition, dict) else transition
    signaling_actions = [
        action.get("branch_id") or action.get("action_id") for action in pack.propose_actions(signaling_state)
    ]

    assert root_actions == ["signal", "limited-response", "alliance-consultation", "open-negotiation"]
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
