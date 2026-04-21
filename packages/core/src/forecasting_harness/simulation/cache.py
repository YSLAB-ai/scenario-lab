from __future__ import annotations

from typing import Any


_SUPPORTED_DEPENDENCY_KEYS = {"fields"}


def should_reuse_node(node: dict[str, Any], compatibility: dict[str, Any]) -> bool:
    dependencies = node.get("dependencies", {})
    unsupported_keys = set(dependencies) - _SUPPORTED_DEPENDENCY_KEYS
    if unsupported_keys:
        raise ValueError(
            "unsupported dependency keys for field-based reuse: " + ", ".join(sorted(unsupported_keys))
        )

    if compatibility.get("reusable", compatibility.get("compatible")) is False:
        return False

    dependency_fields = set(dependencies.get("fields", []))
    changed_fields = set(compatibility.get("changed_fields", []))
    return dependency_fields.isdisjoint(changed_fields)
