from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from math import sqrt
from typing import Any


def scalarize_node_value(metrics: dict[str, float], profile: Any) -> float:
    return profile.scalarize(metrics)


def _base_branch_id(action_context: dict[str, Any]) -> str:
    branch_id = action_context.get("branch_id") or action_context.get("action_id")
    if not isinstance(branch_id, str) or not branch_id:
        raise ValueError("action_context must include a usable branch_id or action_id")
    return branch_id


def _resolved_branch_id(branch_id: str, seen_branch_ids: dict[str, int]) -> str:
    occurrence = seen_branch_ids.get(branch_id, 0) + 1
    seen_branch_ids[branch_id] = occurrence
    if occurrence == 1:
        return branch_id
    return f"{branch_id}-{occurrence}"


@dataclass(frozen=True)
class SearchConfig:
    iterations: int = 24
    max_depth: int = 3
    rollout_depth: int = 3
    c_puct: float = 1.2


@dataclass(frozen=True)
class _NormalizedOutcome:
    next_state: Any
    weight: float
    outcome_id: str | None = None
    outcome_label: str | None = None
    dependencies: dict[str, Any] = field(default_factory=dict)


@dataclass
class _SearchNode:
    node_id: str
    state: Any
    state_hash: str
    depth: int
    prior: float
    branch_id: str | None = None
    label: str | None = None
    dependencies: dict[str, Any] = field(default_factory=dict)
    visits: int = 0
    value_sum: float = 0.0
    metric_sums: dict[str, float] = field(default_factory=dict)
    children: list["_SearchNode"] | None = None

    @property
    def mean_value(self) -> float:
        if self.visits == 0:
            return 0.0
        return self.value_sum / self.visits

    @property
    def mean_metrics(self) -> dict[str, float]:
        if self.visits == 0:
            return {}
        return {name: value / self.visits for name, value in self.metric_sums.items()}


def _normalize_for_hash(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return _normalize_for_hash(value.model_dump(mode="json"))
    if hasattr(value, "__dict__"):
        return _normalize_for_hash(vars(value))
    if isinstance(value, dict):
        return {str(key): _normalize_for_hash(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_normalize_for_hash(item) for item in value]
    if isinstance(value, set):
        return sorted(_normalize_for_hash(item) for item in value)
    return str(value)


def _state_hash(state: Any) -> str:
    payload = json.dumps(_normalize_for_hash(state), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _search_config(domain_pack: Any) -> SearchConfig:
    raw_config = {}
    config_fn = getattr(domain_pack, "search_config", None)
    if callable(config_fn):
        raw_config = config_fn() or {}
    return SearchConfig(
        iterations=int(raw_config.get("iterations", SearchConfig.iterations)),
        max_depth=int(raw_config.get("max_depth", SearchConfig.max_depth)),
        rollout_depth=int(raw_config.get("rollout_depth", SearchConfig.rollout_depth)),
        c_puct=float(raw_config.get("c_puct", SearchConfig.c_puct)),
    )


def _normalize_action(action_context: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(action_context)
    normalized["branch_id"] = _base_branch_id(action_context)
    normalized["label"] = action_context.get("label") or normalized["branch_id"]
    normalized["prior"] = float(action_context.get("prior", 1.0))
    normalized["dependencies"] = dict(action_context.get("dependencies", {}))
    return normalized


def _normalize_outcomes(raw_outcomes: list[Any]) -> list[_NormalizedOutcome]:
    normalized: list[_NormalizedOutcome] = []
    for index, raw_outcome in enumerate(raw_outcomes, start=1):
        if isinstance(raw_outcome, dict) and "next_state" in raw_outcome:
            normalized.append(
                _NormalizedOutcome(
                    next_state=raw_outcome["next_state"],
                    weight=float(raw_outcome.get("weight", 1.0)),
                    outcome_id=raw_outcome.get("outcome_id"),
                    outcome_label=raw_outcome.get("outcome_label"),
                    dependencies=dict(raw_outcome.get("dependencies", {})),
                )
            )
            continue
        normalized.append(
            _NormalizedOutcome(
                next_state=raw_outcome,
                weight=1.0,
                outcome_id=f"outcome-{index}",
            )
        )
    return normalized


def _is_terminal(domain_pack: Any, state: Any, depth: int) -> bool:
    terminal_fn = getattr(domain_pack, "is_terminal", None)
    if callable(terminal_fn):
        return bool(terminal_fn(state, depth))
    return False


def _merge_dependencies(action_context: dict[str, Any], outcome: _NormalizedOutcome) -> dict[str, Any]:
    merged = dict(action_context.get("dependencies", {}))
    for key, value in outcome.dependencies.items():
        merged[key] = value
    return merged


def _metric_sums(metrics: dict[str, float]) -> dict[str, float]:
    return {name: float(value) for name, value in metrics.items()}


def _mean_metrics(node: _SearchNode) -> dict[str, float]:
    return node.mean_metrics


class SimulationEngine:
    def __init__(self, domain_pack: Any, objective_profile: Any) -> None:
        self.domain_pack = domain_pack
        self.objective_profile = objective_profile

    def _validate_root_state(self, state: Any) -> None:
        expected_interaction_model = self.domain_pack.interaction_model()
        if expected_interaction_model != state.interaction_model:
            raise ValueError(
                "interaction model mismatch: "
                f"domain_pack={expected_interaction_model!r}, state={state.interaction_model!r}"
            )

        validation_errors = self.domain_pack.validate_state(state)
        if validation_errors:
            raise ValueError(f"invalid state: {'; '.join(validation_errors)}")

    def _expand_node(self, node: _SearchNode) -> list[_SearchNode]:
        if node.children is not None:
            return node.children

        children: list[_SearchNode] = []
        seen_branch_ids: dict[str, int] = {}
        for raw_action in self.domain_pack.propose_actions(node.state):
            action = _normalize_action(raw_action)
            outcomes = _normalize_outcomes(self.domain_pack.sample_transition(node.state, action))
            for outcome in outcomes:
                branch_id = _resolved_branch_id(action["branch_id"], seen_branch_ids)
                child_state_hash = _state_hash(outcome.next_state)
                outcome_label = outcome.outcome_label
                label = action["label"] if not outcome_label else f"{action['label']} ({outcome_label})"
                child = _SearchNode(
                    node_id=f"{node.node_id}/{branch_id}",
                    state=outcome.next_state,
                    state_hash=child_state_hash,
                    depth=node.depth + 1,
                    prior=action["prior"] * outcome.weight,
                    branch_id=branch_id,
                    label=label,
                    dependencies=_merge_dependencies(action, outcome),
                )
                children.append(child)
        node.children = children
        return children

    def _select_child(self, node: _SearchNode, config: SearchConfig) -> _SearchNode:
        assert node.children
        parent_visits = max(node.visits, 1)

        def puct_score(child: _SearchNode) -> tuple[float, float, str]:
            exploration = config.c_puct * child.prior * sqrt(parent_visits) / (1 + child.visits)
            return (child.mean_value + exploration, child.prior, child.branch_id or child.node_id)

        return max(node.children, key=puct_score)

    def _best_rollout_child(self, node: _SearchNode) -> _SearchNode | None:
        children = self._expand_node(node)
        if not children:
            return None
        return max(children, key=lambda child: (child.prior, child.branch_id or child.node_id))

    def _evaluate_leaf(self, node: _SearchNode, config: SearchConfig) -> tuple[float, dict[str, float], int]:
        rollout_state = node.state
        rollout_depth = node.depth
        steps = 0

        while (
            not _is_terminal(self.domain_pack, rollout_state, rollout_depth)
            and rollout_depth < config.max_depth
            and steps < config.rollout_depth
        ):
            rollout_node = _SearchNode(
                node_id=f"rollout-{rollout_depth}",
                state=rollout_state,
                state_hash=_state_hash(rollout_state),
                depth=rollout_depth,
                prior=1.0,
            )
            best_child = self._best_rollout_child(rollout_node)
            if best_child is None:
                break
            rollout_state = best_child.state
            rollout_depth = best_child.depth
            steps += 1

        metrics = self.domain_pack.score_state(rollout_state)
        value = scalarize_node_value(metrics, self.objective_profile)
        return value, metrics, rollout_depth

    def run(self, state: Any) -> dict[str, Any]:
        self._validate_root_state(state)
        config = _search_config(self.domain_pack)
        root = _SearchNode(
            node_id="root",
            state=state,
            state_hash=_state_hash(state),
            depth=0,
            prior=1.0,
        )
        all_nodes: dict[str, _SearchNode] = {root.node_id: root}
        max_depth_reached = 0

        for _ in range(config.iterations):
            path = [root]
            node = root

            while (
                node.children
                and not _is_terminal(self.domain_pack, node.state, node.depth)
                and node.depth < config.max_depth
            ):
                node = self._select_child(node, config)
                path.append(node)

            if not _is_terminal(self.domain_pack, node.state, node.depth) and node.depth < config.max_depth:
                children = self._expand_node(node)
                for child in children:
                    all_nodes.setdefault(child.node_id, child)
                unvisited_children = [child for child in children if child.visits == 0]
                if unvisited_children:
                    node = max(unvisited_children, key=lambda child: (child.prior, child.branch_id or child.node_id))
                    path.append(node)

            value, metrics, reached_depth = self._evaluate_leaf(node, config)
            max_depth_reached = max(max_depth_reached, reached_depth)
            metric_updates = _metric_sums(metrics)
            for ancestor in path:
                ancestor.visits += 1
                ancestor.value_sum += value
                for name, metric_value in metric_updates.items():
                    ancestor.metric_sums[name] = ancestor.metric_sums.get(name, 0.0) + metric_value

        root_children = self._expand_node(root)
        branches = sorted(
            [
                {
                    "branch_id": child.branch_id,
                    "label": child.label,
                    "metrics": _mean_metrics(child),
                    "score": child.mean_value,
                    "visits": child.visits,
                    "prior": child.prior,
                    "dependencies": child.dependencies,
                }
                for child in root_children
            ],
            key=lambda item: (item["score"], item["prior"], item["branch_id"]),
            reverse=True,
        )

        return {
            "search_mode": "mcts",
            "iterations": config.iterations,
            "node_count": len(all_nodes),
            "max_depth_reached": max_depth_reached,
            "branches": branches,
        }
