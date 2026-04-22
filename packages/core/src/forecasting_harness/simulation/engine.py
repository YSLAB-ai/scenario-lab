from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from math import sqrt
from typing import Any

from forecasting_harness.simulation.cache import should_reuse_node


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
    iterations: int = 10000
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
class _NodeStats:
    visits: int = 0
    value_sum: float = 0.0
    metric_sums: dict[str, float] = field(default_factory=dict)
    actor_metric_sums: dict[str, dict[str, float]] = field(default_factory=dict)
    aggregate_score_breakdown_sums: dict[str, float] = field(default_factory=dict)


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
    dependency_hash: str | None = None
    stats: _NodeStats = field(default_factory=_NodeStats)
    children: list["_SearchNode"] | None = None

    @property
    def mean_value(self) -> float:
        if self.stats.visits == 0:
            return 0.0
        return self.stats.value_sum / self.stats.visits

    @property
    def mean_metrics(self) -> dict[str, float]:
        if self.stats.visits == 0:
            return {}
        return {name: value / self.stats.visits for name, value in self.stats.metric_sums.items()}

    @property
    def visits(self) -> int:
        return self.stats.visits

    @property
    def value_sum(self) -> float:
        return self.stats.value_sum

    @property
    def metric_sums(self) -> dict[str, float]:
        return self.stats.metric_sums

    @property
    def actor_metric_sums(self) -> dict[str, dict[str, float]]:
        return self.stats.actor_metric_sums

    @property
    def aggregate_score_breakdown_sums(self) -> dict[str, float]:
        return self.stats.aggregate_score_breakdown_sums


@dataclass
class _ReuseTracker:
    enabled: bool = False
    source_revision_id: str | None = None
    compatibility: dict[str, Any] = field(default_factory=dict)
    cached_nodes_by_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    attempted_node_ids: set[str] = field(default_factory=set)
    reused_nodes: int = 0
    skipped_nodes: int = 0

    @classmethod
    def from_context(cls, reuse_context: dict[str, Any] | None) -> "_ReuseTracker":
        if not reuse_context:
            return cls()

        simulation = reuse_context.get("simulation", {})
        tree_nodes = simulation.get("tree_nodes", []) if isinstance(simulation, dict) else []
        cached_nodes_by_id = {
            node["node_id"]: node
            for node in tree_nodes
            if isinstance(node, dict) and isinstance(node.get("node_id"), str)
        }
        return cls(
            enabled=True,
            source_revision_id=reuse_context.get("source_revision_id"),
            compatibility=dict(reuse_context.get("compatibility", {})),
            cached_nodes_by_id=cached_nodes_by_id,
        )

    def maybe_seed(self, node: _SearchNode) -> None:
        if not self.enabled or node.node_id in self.attempted_node_ids:
            return

        cached = self.cached_nodes_by_id.get(node.node_id)
        if cached is None:
            return

        self.attempted_node_ids.add(node.node_id)
        if node.depth == 0 and self.compatibility.get("compatible") is False:
            self.skipped_nodes += 1
            return
        if cached.get("state_hash") != node.state_hash and cached.get("dependency_hash") != node.dependency_hash:
            self.skipped_nodes += 1
            return
        if not should_reuse_node(cached, self.compatibility):
            self.skipped_nodes += 1
            return
        if node.stats.visits > 0 or node.stats.value_sum != 0.0 or node.stats.metric_sums:
            return

        node.stats.visits = int(cached.get("visits", 0))
        node.stats.value_sum = float(cached.get("value_sum", 0.0))
        node.stats.metric_sums = {
            str(name): float(value) for name, value in dict(cached.get("metric_sums", {})).items()
        }
        node.stats.actor_metric_sums = {
            str(actor_id): {str(name): float(value) for name, value in dict(metrics).items()}
            for actor_id, metrics in dict(cached.get("actor_metric_sums", {})).items()
        }
        node.stats.aggregate_score_breakdown_sums = {
            str(name): float(value) for name, value in dict(cached.get("aggregate_score_breakdown_sums", {})).items()
        }
        self.reused_nodes += 1

    def summary(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "source_revision_id": self.source_revision_id,
            "reused_nodes": self.reused_nodes,
            "skipped_nodes": self.skipped_nodes,
            "compatibility": self.compatibility,
        }


def _normalize_for_hash(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "interaction_model") and hasattr(value, "fields") and hasattr(value, "current_epoch"):
        return {
            "interaction_model": _normalize_for_hash(value.interaction_model),
            "actors": _normalize_for_hash(getattr(value, "actors", [])),
            "fields": _normalize_for_hash(getattr(value, "fields", {})),
            "objectives": _normalize_for_hash(getattr(value, "objectives", {})),
            "capabilities": _normalize_for_hash(getattr(value, "capabilities", {})),
            "constraints": _normalize_for_hash(getattr(value, "constraints", {})),
            "unknowns": _normalize_for_hash(getattr(value, "unknowns", [])),
            "current_epoch": _normalize_for_hash(getattr(value, "current_epoch", None)),
            "horizon": _normalize_for_hash(getattr(value, "horizon", None)),
            "domain_pack": _normalize_for_hash(getattr(value, "domain_pack", None)),
            "phase": _normalize_for_hash(getattr(value, "phase", None)),
        }
    if hasattr(value, "normalized_value") and hasattr(value, "status") and hasattr(value, "confidence"):
        return {
            "normalized_value": _normalize_for_hash(getattr(value, "normalized_value", None)),
            "status": _normalize_for_hash(getattr(value, "status", None)),
            "confidence": _normalize_for_hash(getattr(value, "confidence", None)),
            "evidence_type": _normalize_for_hash(getattr(value, "evidence_type", None)),
            "time_scope": _normalize_for_hash(getattr(value, "time_scope", None)),
            "applicability_notes": _normalize_for_hash(getattr(value, "applicability_notes", None)),
        }
    if hasattr(value, "actor_id") and hasattr(value, "name"):
        return {
            "actor_id": _normalize_for_hash(getattr(value, "actor_id", None)),
            "name": _normalize_for_hash(getattr(value, "name", None)),
            "behavior_profile": _normalize_for_hash(getattr(value, "behavior_profile", None)),
        }
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


def _dependency_hash(state: Any, dependencies: dict[str, Any]) -> str | None:
    dependency_fields = sorted(set(dependencies.get("fields", [])))
    if not dependency_fields:
        return None

    state_fields = getattr(state, "fields", {})
    payload = {
        "phase": _normalize_for_hash(getattr(state, "phase", None)),
        "current_epoch": _normalize_for_hash(getattr(state, "current_epoch", None)),
        "fields": {field_name: _normalize_for_hash(state_fields.get(field_name)) for field_name in dependency_fields},
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _search_config(domain_pack: Any, *, iterations_override: int | None = None) -> SearchConfig:
    raw_config = {}
    config_fn = getattr(domain_pack, "search_config", None)
    if callable(config_fn):
        raw_config = config_fn() or {}
    return SearchConfig(
        iterations=int(iterations_override if iterations_override is not None else raw_config.get("iterations", SearchConfig.iterations)),
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


def _merge_dependencies(*dependency_maps: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for dependency_map in dependency_maps:
        for key, value in dependency_map.items():
            if isinstance(value, list) and isinstance(merged.get(key), list):
                merged[key] = list(dict.fromkeys([*merged[key], *value]))
            elif isinstance(value, list):
                merged[key] = list(dict.fromkeys(value))
            else:
                merged[key] = value
    return merged


def _metric_sums(metrics: dict[str, float]) -> dict[str, float]:
    return {name: float(value) for name, value in metrics.items()}


def _mean_metrics(node: _SearchNode) -> dict[str, float]:
    return node.mean_metrics


def _actor_metric_sums(actor_metrics: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    return {
        actor_id: {metric_name: float(metric_value) for metric_name, metric_value in metrics.items()}
        for actor_id, metrics in actor_metrics.items()
    }


def _mean_actor_metrics(node: _SearchNode) -> dict[str, dict[str, float]]:
    if node.stats.visits == 0:
        return {}
    return {
        actor_id: {metric_name: value / node.stats.visits for metric_name, value in metrics.items()}
        for actor_id, metrics in node.stats.actor_metric_sums.items()
    }


def _mean_breakdown(node: _SearchNode) -> dict[str, float]:
    if node.stats.visits == 0:
        return {}
    return {
        metric_name: value / node.stats.visits for metric_name, value in node.stats.aggregate_score_breakdown_sums.items()
    }


def _serialize_tree_node(node: _SearchNode) -> dict[str, Any]:
    return {
        "node_id": node.node_id,
        "state_hash": node.state_hash,
        "depth": node.depth,
        "branch_id": node.branch_id,
        "label": node.label,
        "prior": node.prior,
        "dependencies": node.dependencies,
        "dependency_hash": node.dependency_hash,
        "visits": node.visits,
        "value_sum": node.value_sum,
        "metric_sums": node.metric_sums,
        "actor_metric_sums": node.actor_metric_sums,
        "aggregate_score_breakdown_sums": node.aggregate_score_breakdown_sums,
        "score": node.mean_value,
        "metrics": node.mean_metrics,
        "actor_metrics": _mean_actor_metrics(node),
        "aggregate_score_breakdown": _mean_breakdown(node),
        "child_ids": [child.node_id for child in node.children or []],
    }


class SimulationEngine:
    def __init__(self, domain_pack: Any, objective_profile: Any) -> None:
        self.domain_pack = domain_pack
        self.objective_profile = objective_profile
        self._all_nodes: dict[str, _SearchNode] = {}
        self._state_table: dict[str, _NodeStats] = {}
        self._seen_state_hashes: set[str] = set()
        self._transposition_hits = 0
        self._reuse_tracker = _ReuseTracker()

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

    def _register_node(self, node: _SearchNode) -> None:
        self._all_nodes.setdefault(node.node_id, node)
        self._seen_state_hashes.add(node.state_hash)
        self._reuse_tracker.maybe_seed(node)

    def _shared_stats_for(self, state_hash: str, depth: int) -> _NodeStats:
        if depth <= 1:
            return _NodeStats()
        stats = self._state_table.get(state_hash)
        if stats is not None:
            self._transposition_hits += 1
            return stats
        stats = _NodeStats()
        self._state_table[state_hash] = stats
        return stats

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
                child_dependencies = _merge_dependencies(
                    node.dependencies,
                    action.get("dependencies", {}),
                    outcome.dependencies,
                )
                child = _SearchNode(
                    node_id=f"{node.node_id}/{branch_id}",
                    state=outcome.next_state,
                    state_hash=child_state_hash,
                    depth=node.depth + 1,
                    prior=action["prior"] * outcome.weight,
                    branch_id=branch_id,
                    label=label,
                    dependencies=child_dependencies,
                    dependency_hash=_dependency_hash(outcome.next_state, child_dependencies),
                    stats=self._shared_stats_for(child_state_hash, node.depth + 1),
                )
                children.append(child)
                self._register_node(child)
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

    def _evaluate_leaf(
        self,
        node: _SearchNode,
        config: SearchConfig,
    ) -> tuple[float, dict[str, float], dict[str, dict[str, float]], dict[str, float], int]:
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
        actor_impact_fn = getattr(self.domain_pack, "score_actor_impacts", None)
        actor_metrics = actor_impact_fn(rollout_state) if callable(actor_impact_fn) else {}
        value, aggregate_score_breakdown = self.objective_profile.aggregate(metrics, actor_metrics)
        return value, metrics, actor_metrics, aggregate_score_breakdown, rollout_depth

    def _synthesize_branch(self, node: _SearchNode, config: SearchConfig, *, root_visits: int) -> dict[str, Any]:
        current_state = node.state
        current_depth = node.depth
        path = [
            {
                "label": node.label,
                "phase": getattr(current_state, "phase", None),
            }
        ]
        driver_fields = set(node.dependencies.get("fields", []))

        while not _is_terminal(self.domain_pack, current_state, current_depth) and current_depth < config.max_depth:
            actions = [_normalize_action(action) for action in self.domain_pack.propose_actions(current_state)]
            if not actions:
                break
            action = max(actions, key=lambda item: (item["prior"], item["branch_id"]))
            outcomes = _normalize_outcomes(self.domain_pack.sample_transition(current_state, action))
            if not outcomes:
                break
            outcome = max(
                outcomes,
                key=lambda item: (item.weight, item.outcome_id or "", item.outcome_label or ""),
            )
            driver_fields.update(action.get("dependencies", {}).get("fields", []))
            driver_fields.update(outcome.dependencies.get("fields", []))
            current_state = outcome.next_state
            current_depth += 1
            label = action["label"] if not outcome.outcome_label else f"{action['label']} ({outcome.outcome_label})"
            path.append(
                {
                    "label": label,
                    "phase": getattr(current_state, "phase", None),
                }
            )

        terminal_metrics = self.domain_pack.score_state(current_state)
        actor_impact_fn = getattr(self.domain_pack, "score_actor_impacts", None)
        actor_metrics = actor_impact_fn(current_state) if callable(actor_impact_fn) else {}
        _, aggregate_score_breakdown = self.objective_profile.aggregate(terminal_metrics, actor_metrics)
        key_drivers = sorted(driver_fields)
        if not key_drivers:
            key_drivers = [
                metric_name
                for metric_name, metric_value in sorted(
                    terminal_metrics.items(),
                    key=lambda item: (item[1], item[0]),
                    reverse=True,
                )
                if metric_value > 0
            ][:3]

        return {
            "path": path,
            "terminal_phase": getattr(current_state, "phase", None),
            "terminal_metrics": terminal_metrics,
            "terminal_actor_metrics": actor_metrics,
            "terminal_aggregate_score_breakdown": aggregate_score_breakdown,
            "key_drivers": key_drivers[:3],
            "confidence_signal": round(node.visits / max(root_visits, 1), 3),
        }

    def run(
        self,
        state: Any,
        reuse_context: dict[str, Any] | None = None,
        *,
        iterations: int | None = None,
    ) -> dict[str, Any]:
        self._validate_root_state(state)
        config = _search_config(self.domain_pack, iterations_override=iterations)
        self._all_nodes = {}
        self._state_table = {}
        self._seen_state_hashes = set()
        self._transposition_hits = 0
        self._reuse_tracker = _ReuseTracker.from_context(reuse_context)
        root = _SearchNode(
            node_id="root",
            state=state,
            state_hash=_state_hash(state),
            depth=0,
            prior=1.0,
        )
        self._register_node(root)
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
                unvisited_children = [child for child in children if child.visits == 0]
                if unvisited_children:
                    node = max(unvisited_children, key=lambda child: (child.prior, child.branch_id or child.node_id))
                    path.append(node)

            value, metrics, actor_metrics, aggregate_score_breakdown, reached_depth = self._evaluate_leaf(node, config)
            max_depth_reached = max(max_depth_reached, reached_depth)
            metric_updates = _metric_sums(metrics)
            actor_metric_updates = _actor_metric_sums(actor_metrics)
            aggregate_score_breakdown_updates = _metric_sums(aggregate_score_breakdown)
            for ancestor in path:
                ancestor.stats.visits += 1
                ancestor.stats.value_sum += value
                for name, metric_value in metric_updates.items():
                    ancestor.stats.metric_sums[name] = ancestor.stats.metric_sums.get(name, 0.0) + metric_value
                for actor_id, actor_metric_map in actor_metric_updates.items():
                    existing_actor_metrics = ancestor.stats.actor_metric_sums.setdefault(actor_id, {})
                    for metric_name, metric_value in actor_metric_map.items():
                        existing_actor_metrics[metric_name] = existing_actor_metrics.get(metric_name, 0.0) + metric_value
                for name, metric_value in aggregate_score_breakdown_updates.items():
                    ancestor.stats.aggregate_score_breakdown_sums[name] = (
                        ancestor.stats.aggregate_score_breakdown_sums.get(name, 0.0) + metric_value
                    )

        root_children = self._expand_node(root)
        branch_rows: list[dict[str, Any]] = []
        for child in root_children:
            branch = {
                "branch_id": child.branch_id,
                "label": child.label,
                "metrics": _mean_metrics(child),
                "actor_metrics": _mean_actor_metrics(child),
                "aggregate_score_breakdown": _mean_breakdown(child),
                "score": child.mean_value,
                "visits": child.visits,
                "prior": child.prior,
                "dependencies": child.dependencies,
                **self._synthesize_branch(child, config, root_visits=root.visits),
            }
            if child.visits == 0:
                branch["metrics"] = dict(branch["terminal_metrics"])
                branch["actor_metrics"] = dict(branch["terminal_actor_metrics"])
                branch["score"], branch["aggregate_score_breakdown"] = self.objective_profile.aggregate(
                    branch["terminal_metrics"],
                    branch["actor_metrics"],
                )
            branch_rows.append(branch)
        branches = sorted(
            branch_rows,
            key=lambda item: (item["visits"] > 0, item["score"], item["visits"], item["prior"], item["branch_id"]),
            reverse=True,
        )

        return {
            "search_mode": "mcts",
            "iterations": config.iterations,
            "node_count": len(self._all_nodes),
            "state_table_size": len(self._seen_state_hashes),
            "transposition_hits": self._transposition_hits,
            "max_depth_reached": max_depth_reached,
            "reuse_summary": self._reuse_tracker.summary(),
            "tree_nodes": [_serialize_tree_node(node) for _, node in sorted(self._all_nodes.items())],
            "branches": branches,
        }
