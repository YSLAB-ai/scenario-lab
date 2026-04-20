from __future__ import annotations

from typing import Any


def scalarize_node_value(metrics: dict[str, float], profile: Any) -> float:
    return profile.scalarize(metrics)


def _base_branch_id(action_context: dict[str, Any]) -> str:
    branch_id = action_context.get("branch_id") or action_context.get("action_id")
    if not isinstance(branch_id, str) or not branch_id:
        raise ValueError("action_context must include a usable branch_id or action_id")
    return branch_id


def _resolved_branch_id(action_context: dict[str, Any], transition_index: int) -> str:
    branch_id = _base_branch_id(action_context)
    if transition_index == 0:
        return branch_id
    return f"{branch_id}-{transition_index + 1}"


class SimulationEngine:
    def __init__(self, domain_pack: Any, objective_profile: Any) -> None:
        self.domain_pack = domain_pack
        self.objective_profile = objective_profile

    def run(self, state: Any) -> dict[str, list[dict[str, Any]]]:
        expected_interaction_model = self.domain_pack.interaction_model()
        if expected_interaction_model != state.interaction_model:
            raise ValueError(
                "interaction model mismatch: "
                f"domain_pack={expected_interaction_model!r}, state={state.interaction_model!r}"
            )

        validation_errors = self.domain_pack.validate_state(state)
        if validation_errors:
            raise ValueError(f"invalid state: {'; '.join(validation_errors)}")

        branches: list[dict[str, Any]] = []
        for action_context in self.domain_pack.propose_actions(state):
            for transition_index, next_state in enumerate(
                self.domain_pack.sample_transition(state, action_context)
            ):
                metrics = self.domain_pack.score_state(next_state)
                branches.append(
                    {
                        "branch_id": _resolved_branch_id(action_context, transition_index),
                        "label": action_context.get("label"),
                        "metrics": metrics,
                        "score": scalarize_node_value(metrics, self.objective_profile),
                        "dependencies": action_context.get("dependencies", {}),
                    }
                )

        return {"branches": sorted(branches, key=lambda item: item["score"], reverse=True)}
