from __future__ import annotations

from numbers import Real
from typing import Any


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

        previous_value = previous_slice.get("normalized_value")
        current_value = current_slice.get("normalized_value")

        if previous_value == current_value:
            continue

        changed_fields.append(field)

        tolerance = tolerances.get(field, 0.0)
        if isinstance(previous_value, Real) and isinstance(current_value, Real):
            if abs(float(previous_value) - float(current_value)) > tolerance:
                compatible = False
        else:
            compatible = False

    return {"compatible": compatible, "changed_fields": changed_fields}
