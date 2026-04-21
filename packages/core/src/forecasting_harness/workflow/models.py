from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

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
    created_at: datetime
    approved_at: datetime | None = None
    simulated_at: datetime | None = None


class IntakeDraft(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_framing: str
    focus_entities: list[str] = Field(
        min_length=1,
        validation_alias=AliasChoices("focus_entities", "primary_actors"),
    )
    current_development: str = Field(
        validation_alias=AliasChoices("current_development", "trigger"),
    )
    current_stage: str = Field(
        validation_alias=AliasChoices("current_stage", "current_phase"),
    )
    time_horizon: str
    known_constraints: list[str] = Field(default_factory=list)
    known_unknowns: list[str] = Field(default_factory=list)
    suggested_entities: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("suggested_entities", "suggested_actors"),
    )
    pack_fields: dict[str, object] = Field(default_factory=dict)


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
