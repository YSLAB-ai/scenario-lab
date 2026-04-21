from __future__ import annotations

import hashlib
import json
import math
import re

EMBEDDING_VERSION = "local-semantic-v1"
VECTOR_DIMENSION = 256

_ALIAS_GROUPS = [
    ("ceo", "chief executive", "executive"),
    ("inventory shortage", "stockout", "supply shortage"),
    ("liquidity stress", "funding stress", "liquidity crunch"),
    ("rate pressure", "tightening pressure", "hike pressure"),
    ("turnout", "voter turnout", "base turnout"),
    ("regulator", "agency", "enforcer"),
]


def _normalize_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _normalized_tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _expanded_terms(normalized_text: str) -> list[str]:
    terms: list[str] = []
    for group in _ALIAS_GROUPS:
        if any(term in normalized_text for term in group):
            terms.extend(group)
    return terms


def _add_feature(vector: list[float], feature: str, weight: float) -> None:
    digest = hashlib.sha256(feature.encode("utf-8")).digest()
    index = int.from_bytes(digest[:4], "big") % VECTOR_DIMENSION
    sign = 1.0 if digest[4] % 2 == 0 else -1.0
    vector[index] += sign * weight


def encode_text(text: str) -> tuple[list[float], int]:
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

    for alias in _expanded_terms(normalized):
        _add_feature(vector, f"alias:{alias}", 0.9)

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return ([0.0] * VECTOR_DIMENSION, len(tokens))
    return ([value / norm for value in vector], len(tokens))


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def serialize_vector(vector: list[float]) -> str:
    return json.dumps(vector, separators=(",", ":"))


def deserialize_vector(value: str) -> list[float]:
    return [float(item) for item in json.loads(value)]
