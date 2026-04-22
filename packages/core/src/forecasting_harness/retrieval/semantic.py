from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import math
import os
import re
from typing import Callable, Iterable

BASELINE_EMBEDDING_VERSION = "local-semantic-v1"
DEFAULT_EMBEDDING_BACKEND = "baseline"
DEFAULT_NEURAL_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_BACKEND_ENV = "FORECAST_HARNESS_EMBEDDING_BACKEND"
EMBEDDING_MODEL_ENV = "FORECAST_HARNESS_EMBEDDING_MODEL"
VECTOR_DIMENSION = 256

_ALIAS_GROUPS = [
    ("ceo", "chief executive", "executive"),
    ("inventory shortage", "stockout", "supply shortage"),
    ("liquidity stress", "funding stress", "liquidity crunch"),
    ("rate pressure", "tightening pressure", "hike pressure"),
    ("turnout", "voter turnout", "base turnout"),
    ("regulator", "agency", "enforcer"),
]


@dataclass(frozen=True)
class EmbeddingBackend:
    requested_backend: str
    active_backend: str
    version: str
    model_name: str | None
    fallback_reason: str | None
    encoder: Callable[[str, Iterable[tuple[str, ...] | list[str]] | None], tuple[list[float], int]]


def _normalize_backend_name(name: str | None) -> str:
    normalized = (name or DEFAULT_EMBEDDING_BACKEND).strip().lower()
    if normalized not in {"auto", "baseline", "neural"}:
        return DEFAULT_EMBEDDING_BACKEND
    return normalized


def _normalize_model_name(name: str | None) -> str:
    normalized = (name or DEFAULT_NEURAL_MODEL).strip()
    return normalized or DEFAULT_NEURAL_MODEL


def _normalize_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _normalized_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _merge_alias_groups(
    alias_groups: Iterable[tuple[str, ...] | list[str]] | None,
) -> list[tuple[str, ...]]:
    merged: list[tuple[str, ...]] = list(_ALIAS_GROUPS)
    if alias_groups is None:
        return merged

    for group in alias_groups:
        normalized_group = tuple(term for term in group if term)
        if normalized_group and normalized_group not in merged:
            merged.append(normalized_group)
    return merged


def _expanded_terms(
    normalized_text: str,
    *,
    alias_groups: Iterable[tuple[str, ...] | list[str]] | None = None,
) -> list[str]:
    terms: list[str] = []
    for group in _merge_alias_groups(alias_groups):
        if any(term in normalized_text for term in group):
            terms.extend(group)
    return terms


def _expanded_text(
    text: str,
    *,
    alias_groups: Iterable[tuple[str, ...] | list[str]] | None = None,
) -> str:
    normalized = _normalize_text(text)
    aliases = _expanded_terms(normalized, alias_groups=alias_groups)
    if not aliases:
        return text
    return f"{text}\n{' '.join(aliases)}"


def _add_feature(vector: list[float], feature: str, weight: float) -> None:
    digest = hashlib.sha256(feature.encode("utf-8")).digest()
    index = int.from_bytes(digest[:4], "big") % VECTOR_DIMENSION
    sign = 1.0 if digest[4] % 2 == 0 else -1.0
    vector[index] += sign * weight


def _encode_with_baseline(
    text: str,
    alias_groups: Iterable[tuple[str, ...] | list[str]] | None = None,
) -> tuple[list[float], int]:
    normalized = _normalize_text(text)
    tokens = _normalized_tokens(text)
    if not tokens:
        return ([0.0] * VECTOR_DIMENSION, 0)

    vector = [0.0] * VECTOR_DIMENSION
    for token in tokens:
        _add_feature(vector, f"tok:{token}", 1.0)
        if len(token) >= 3:
            for index in range(len(token) - 2):
                _add_feature(vector, f"tri:{token[index:index + 3]}", 0.35)

    for left, right in zip(tokens, tokens[1:]):
        _add_feature(vector, f"bi:{left}_{right}", 0.7)

    for alias in _expanded_terms(normalized, alias_groups=alias_groups):
        _add_feature(vector, f"alias:{alias}", 0.9)

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return ([0.0] * VECTOR_DIMENSION, len(tokens))
    return ([value / norm for value in vector], len(tokens))


def _baseline_backend(*, requested_backend: str, fallback_reason: str | None = None) -> EmbeddingBackend:
    return EmbeddingBackend(
        requested_backend=requested_backend,
        active_backend="baseline",
        version=BASELINE_EMBEDDING_VERSION,
        model_name=None,
        fallback_reason=fallback_reason,
        encoder=_encode_with_baseline,
    )


def _neural_model_version(model_name: str) -> str:
    sanitized = re.sub(r"[^a-z0-9]+", "-", model_name.lower()).strip("-")
    return f"local-neural-{sanitized}"


def _build_neural_backend(
    *,
    requested_backend: str,
    model_name: str,
) -> EmbeddingBackend | None:
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        return None

    try:
        model = SentenceTransformer(model_name)
        dimension = int(model.get_sentence_embedding_dimension() or 0)
    except Exception:
        return None

    def _encode_with_neural(
        text: str,
        alias_groups: Iterable[tuple[str, ...] | list[str]] | None = None,
    ) -> tuple[list[float], int]:
        expanded = _expanded_text(text, alias_groups=alias_groups)
        tokens = _normalized_tokens(expanded)
        if not tokens:
            return ([0.0] * max(dimension, 1), 0)

        vector = model.encode(expanded, normalize_embeddings=True, convert_to_numpy=True)
        return ([float(value) for value in vector.tolist()], len(tokens))

    return EmbeddingBackend(
        requested_backend=requested_backend,
        active_backend="neural",
        version=_neural_model_version(model_name),
        model_name=model_name,
        fallback_reason=None,
        encoder=_encode_with_neural,
    )


@lru_cache(maxsize=16)
def _resolve_backend(requested_backend: str | None, model_name: str | None) -> EmbeddingBackend:
    normalized_backend = _normalize_backend_name(
        requested_backend or os.getenv(EMBEDDING_BACKEND_ENV, DEFAULT_EMBEDDING_BACKEND)
    )
    normalized_model = _normalize_model_name(model_name or os.getenv(EMBEDDING_MODEL_ENV, DEFAULT_NEURAL_MODEL))

    if normalized_backend == "baseline":
        return _baseline_backend(requested_backend=normalized_backend)

    neural_backend = _build_neural_backend(
        requested_backend=normalized_backend,
        model_name=normalized_model,
    )
    if neural_backend is not None:
        return neural_backend

    fallback_reason = (
        "sentence-transformers unavailable or model could not be loaded"
        if normalized_backend in {"auto", "neural"}
        else None
    )
    return _baseline_backend(requested_backend=normalized_backend, fallback_reason=fallback_reason)


def clear_embedding_backend_cache() -> None:
    _resolve_backend.cache_clear()


def embedding_backend_summary(
    *,
    requested_backend: str | None = None,
    model_name: str | None = None,
) -> dict[str, str | bool | None]:
    backend = _resolve_backend(requested_backend, model_name)
    return {
        "requested_backend": backend.requested_backend,
        "active_backend": backend.active_backend,
        "embedding_version": backend.version,
        "model_name": backend.model_name,
        "is_neural": backend.active_backend == "neural",
        "fallback_reason": backend.fallback_reason,
    }


def current_embedding_version(
    *,
    requested_backend: str | None = None,
    model_name: str | None = None,
) -> str:
    return _resolve_backend(requested_backend, model_name).version


def encode_text(
    text: str,
    *,
    alias_groups: Iterable[tuple[str, ...] | list[str]] | None = None,
    requested_backend: str | None = None,
    model_name: str | None = None,
) -> tuple[list[float], int]:
    backend = _resolve_backend(requested_backend, model_name)
    return backend.encoder(text, alias_groups)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def serialize_vector(vector: list[float]) -> str:
    return json.dumps(vector, separators=(",", ":"))


def deserialize_vector(value: str) -> list[float]:
    return [float(item) for item in json.loads(value)]


EMBEDDING_VERSION = current_embedding_version()
