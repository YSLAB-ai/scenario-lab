from __future__ import annotations

from typing import Any


def should_reuse_node(node: dict[str, Any], compatibility: dict[str, Any]) -> bool:
    if compatibility.get("compatible") is False:
        return False

    dependency_fields = set(node.get("dependencies", {}).get("fields", []))
    changed_fields = set(compatibility.get("changed_fields", []))
    return dependency_fields.isdisjoint(changed_fields)
