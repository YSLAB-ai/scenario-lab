from __future__ import annotations

from datetime import datetime, timezone
import re
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


def normalize_text(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _stem_token(token: str) -> str:
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("ing") and len(token) > 5:
        return token[:-3]
    if token.endswith("ed") and len(token) > 4:
        return token[:-2]
    if token.endswith("es") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and len(token) > 3 and not token.endswith("ss"):
        return token[:-1]
    return token


def tokenize_text(value: str) -> list[str]:
    return [_stem_token(token) for token in re.findall(r"[a-z0-9]+", value.lower())]


def _shared_prefix_length(left: str, right: str) -> int:
    length = 0
    for left_char, right_char in zip(left, right):
        if left_char != right_char:
            break
        length += 1
    return length


def _tokens_match(left: str, right: str) -> bool:
    if left == right:
        return True

    minimum_prefix_length = 4
    if min(len(left), len(right)) < minimum_prefix_length:
        return False

    if left.startswith(right) or right.startswith(left):
        return True

    return _shared_prefix_length(left, right) >= minimum_prefix_length


def term_match_score(text: str, term: str) -> int:
    normalized_text = normalize_text(text)
    normalized_term = normalize_text(term)
    if not normalized_term:
        return 0
    if normalized_term in normalized_text:
        return max(2, len(tokenize_text(term)))

    text_tokens = tokenize_text(text)
    term_tokens = tokenize_text(term)
    if not term_tokens or not text_tokens:
        return 0

    overlap = 0
    for term_token in term_tokens:
        if any(_tokens_match(text_token, term_token) for text_token in text_tokens):
            overlap += 1

    if overlap == len(term_tokens):
        return overlap
    return 0


def any_term_matches(text: str, terms: list[str]) -> bool:
    return any(term_match_score(text, term) > 0 for term in terms)


def count_term_matches(text: str, terms: list[str]) -> int:
    return sum(term_match_score(text, term) > 0 for term in terms)


def compose_signal_text(*parts: Any) -> str:
    values: list[str] = []
    for part in parts:
        if isinstance(part, str):
            if part.strip():
                values.append(part.strip())
            continue
        if isinstance(part, list):
            values.extend(str(item).strip() for item in part if str(item).strip())
            continue
    return " ".join(values)
