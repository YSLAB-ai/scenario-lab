from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def anchor_timestamp(state: Any) -> datetime:
    fields = getattr(state, "fields", {})
    if fields:
        return next(iter(fields.values())).last_updated_at
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def numeric_field(state: Any, field_name: str, default: float) -> float:
    field = getattr(state, "fields", {}).get(field_name)
    if field is None:
        return default
    try:
        return float(field.normalized_value)
    except (TypeError, ValueError):
        return default


def integer_field(state: Any, field_name: str, default: int) -> int:
    field = getattr(state, "fields", {}).get(field_name)
    if field is None:
        return default
    try:
        return int(field.normalized_value)
    except (TypeError, ValueError):
        return default


def string_field(state: Any, field_name: str, default: str) -> str:
    field = getattr(state, "fields", {}).get(field_name)
    if field is None:
        return default
    value = field.normalized_value
    return value if isinstance(value, str) else default


def with_updates(state: Any, *, phase: str, field_updates: dict[str, float | int | str]) -> Any:
    from forecasting_harness.models import BeliefField

    existing_fields = dict(getattr(state, "fields", {}))
    timestamp = anchor_timestamp(state)
    for field_name, value in field_updates.items():
        existing_fields[field_name] = BeliefField(
            value=value,
            normalized_value=value,
            status="inferred",
            confidence=0.65,
            last_updated_at=timestamp,
        )
    return state.model_copy(update={"phase": phase, "current_epoch": phase, "fields": existing_fields})


def bounded(value: float) -> float:
    return max(0.0, min(1.0, value))
