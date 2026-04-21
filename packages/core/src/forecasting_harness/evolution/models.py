from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

SuggestionProvenance = Literal["user", "self-detected"]
SuggestionCategory = Literal["state-field", "action-bias", "evidence-category", "semantic-alias", "replay-gap"]
SuggestionStatus = Literal["pending", "accepted", "rejected", "promoted"]


class DomainSuggestion(BaseModel):
    suggestion_id: str
    timestamp: datetime
    domain_slug: str
    provenance: SuggestionProvenance
    category: SuggestionCategory
    target: str | None = None
    text: str
    terms: list[str] = Field(default_factory=list)
    status: SuggestionStatus = "pending"


class DomainWeaknessBrief(BaseModel):
    domain_slug: str
    reasons: list[str] = Field(default_factory=list)
    weak_cases: list[str] = Field(default_factory=list)
    suggested_targets: list[str] = Field(default_factory=list)


class DomainEvolutionCandidate(BaseModel):
    domain_slug: str
    updated_manifest: dict[str, Any]
    changed: bool
    applied_suggestion_ids: list[str] = Field(default_factory=list)
