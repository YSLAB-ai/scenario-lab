from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

RevisionStatus = Literal["draft", "approved", "simulated"]


class RunRecord(BaseModel):
    run_id: str
    domain_pack: str
    created_at: datetime
    current_revision_id: str | None = None


class RevisionRecord(BaseModel):
    revision_id: str
    status: RevisionStatus = "draft"
    parent_revision_id: str | None = None


class IntakeDraft(BaseModel):
    event_framing: str
    primary_actors: list[str] = Field(min_length=2, max_length=2)
    trigger: str
    current_phase: str
    time_horizon: str
    known_constraints: list[str] = Field(default_factory=list)
    known_unknowns: list[str] = Field(default_factory=list)
    suggested_actors: list[str] = Field(default_factory=list)


class AssumptionSummary(BaseModel):
    summary: list[str] = Field(default_factory=list)
    suggested_actors: list[str] = Field(default_factory=list)
    objective_profile_name: str = "balanced"


class EvidencePacketItem(BaseModel):
    evidence_id: str
    source_id: str
    source_title: str
    reason: str
    passage_ids: list[str] = Field(default_factory=list)
    citation_refs: list[str] = Field(default_factory=list)
    raw_passages: list[str] = Field(default_factory=list)


class EvidencePacket(BaseModel):
    revision_id: str
    items: list[EvidencePacketItem] = Field(default_factory=list)
