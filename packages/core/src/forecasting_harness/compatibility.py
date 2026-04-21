from __future__ import annotations

from numbers import Real
from typing import Any


def _slice_get(slice_value: Any, key: str) -> Any:
    if isinstance(slice_value, dict):
        return slice_value.get(key)
    return getattr(slice_value, key, None)


def _actor_ids(state: Any) -> list[str]:
    return sorted(getattr(actor, "actor_id", getattr(actor, "name", "")) for actor in getattr(state, "actors", []))


def compare_state_slices(
    previous: dict[str, dict[str, Any]],
    current: dict[str, dict[str, Any]],
    tolerances: dict[str, float],
) -> dict[str, Any]:
    changed_fields: list[str] = []
    compatible = True

    for field in sorted(set(previous) | set(current)):
        previous_slice = previous.get(field)
        current_slice = current.get(field)

        if previous_slice is None or current_slice is None:
            changed_fields.append(field)
            compatible = False
            continue

        previous_value = _slice_get(previous_slice, "normalized_value")
        current_value = _slice_get(current_slice, "normalized_value")

        if previous_value == current_value:
            continue

        if isinstance(previous_value, bool) or isinstance(current_value, bool):
            changed_fields.append(field)
            compatible = False
            continue

        changed_fields.append(field)

        tolerance = tolerances.get(field, 0.0)
        if isinstance(previous_value, Real) and isinstance(current_value, Real):
            if abs(float(previous_value) - float(current_value)) > tolerance:
                compatible = False
        else:
            compatible = False

    return {"compatible": compatible, "changed_fields": changed_fields}


def compare_belief_states(previous: Any, current: Any, tolerances: dict[str, float]) -> dict[str, Any]:
    reasons: list[str] = []

    if previous.interaction_model != current.interaction_model:
        reasons.append("interaction_model changed")
    if getattr(previous, "domain_pack", None) != getattr(current, "domain_pack", None):
        reasons.append("domain_pack changed")
    if getattr(previous, "phase", None) != getattr(current, "phase", None):
        reasons.append("phase changed")
    if previous.current_epoch != current.current_epoch:
        reasons.append("current_epoch changed")
    if previous.horizon != current.horizon:
        reasons.append("horizon changed")
    if _actor_ids(previous) != _actor_ids(current):
        reasons.append("actors changed")
    if previous.objectives != current.objectives:
        reasons.append("objectives changed")
    if previous.capabilities != current.capabilities:
        reasons.append("capabilities changed")
    if previous.constraints != current.constraints:
        reasons.append("constraints changed")
    if sorted(previous.unknowns) != sorted(current.unknowns):
        reasons.append("unknowns changed")

    field_result = compare_state_slices(previous.fields, current.fields, tolerances=tolerances)
    reusable = not reasons
    compatible = reusable and field_result["compatible"]

    return {
        "compatible": compatible,
        "reusable": reusable,
        "changed_fields": field_result["changed_fields"],
        "reasons": reasons,
    }
