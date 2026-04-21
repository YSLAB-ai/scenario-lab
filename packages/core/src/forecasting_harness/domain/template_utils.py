from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from forecasting_harness.knowledge.manifests import DomainManifest, load_domain_manifest


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


def state_signal_text(state: Any) -> str:
    field_parts: list[str] = []
    for field in getattr(state, "fields", {}).values():
        value = getattr(field, "value", None)
        normalized = getattr(field, "normalized_value", None)
        if value not in (None, ""):
            field_parts.append(str(value))
        if normalized not in (None, "", value):
            field_parts.append(str(normalized))
    return compose_signal_text(field_parts)


def manifest_state_delta(text: str, field_name: str, *, manifest: DomainManifest | None = None, slug: str | None = None) -> float:
    active_manifest = manifest
    if active_manifest is None and slug is not None:
        active_manifest = load_domain_manifest(slug)
    if active_manifest is None:
        return 0.0

    total = 0.0
    for rule in active_manifest.adaptive_state_terms.get(field_name, []):
        if any_term_matches(text, rule.terms):
            total += rule.delta
    return total


def apply_manifest_state_overlays(
    *,
    text: str,
    field_values: dict[str, Any],
    manifest: DomainManifest | None = None,
    slug: str | None = None,
) -> dict[str, Any]:
    active_manifest = manifest
    if active_manifest is None and slug is not None:
        active_manifest = load_domain_manifest(slug)
    if active_manifest is None:
        return field_values

    updated = dict(field_values)
    for field_name, value in field_values.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        delta = manifest_state_delta(text, field_name, manifest=active_manifest)
        if delta == 0.0:
            continue
        next_value = float(value) + delta
        if isinstance(value, int):
            updated[field_name] = int(round(next_value))
        elif 0.0 <= float(value) <= 1.0:
            updated[field_name] = round(bounded(next_value), 3)
        else:
            updated[field_name] = round(next_value, 3)
    return updated


def apply_manifest_action_biases(
    *,
    text: str,
    actions: list[dict[str, Any]],
    manifest: DomainManifest | None = None,
    slug: str | None = None,
) -> list[dict[str, Any]]:
    active_manifest = manifest
    if active_manifest is None and slug is not None:
        active_manifest = load_domain_manifest(slug)
    if active_manifest is None:
        return actions

    biased_actions: list[dict[str, Any]] = []
    for action in actions:
        updated = dict(action)
        prior = float(updated.get("prior", 0.0))
        action_id = str(updated.get("action_id", ""))
        label = normalize_text(str(updated.get("label", "")))
        for rule in active_manifest.adaptive_action_biases:
            target = normalize_text(rule.target)
            if target not in {normalize_text(action_id), label}:
                continue
            if any_term_matches(text, rule.terms):
                prior += rule.delta
        updated["prior"] = bounded(prior)
        biased_actions.append(updated)
    return biased_actions
