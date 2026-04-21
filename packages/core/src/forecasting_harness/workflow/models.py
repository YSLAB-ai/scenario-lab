from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

RevisionStatus = Literal["draft", "approved", "simulated"]
ConversationStage = Literal["intake", "evidence", "approval", "simulation", "report"]


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


class RetrievalPlan(BaseModel):
    revision_id: str
    domain_pack: str
    base_query: str
    query_variants: list[str] = Field(default_factory=list)
    filters: dict[str, str] = Field(default_factory=dict)
    target_evidence_categories: list[str] = Field(default_factory=list)


class IngestionPlan(BaseModel):
    revision_id: str
    domain_pack: str
    corpus_source_count: int = 0
    current_sources: list[dict[str, object]] = Field(default_factory=list)
    covered_evidence_categories: list[str] = Field(default_factory=list)
    missing_evidence_categories: list[str] = Field(default_factory=list)
    recommended_source_types: list[str] = Field(default_factory=list)
    starter_sources: list[dict[str, str]] = Field(default_factory=list)
    ingestion_priorities: list[str] = Field(default_factory=list)


class IntakeGuidance(BaseModel):
    domain_pack: str
    current_stage: str
    canonical_stages: list[str] = Field(default_factory=list)
    suggested_entities: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    pack_field_schema: dict[str, str] = Field(default_factory=dict)
    default_objective_profile: dict[str, object]


class ApprovalPacket(BaseModel):
    revision_id: str
    intake_summary: dict[str, object]
    assumption_summary: list[str] = Field(default_factory=list)
    objective_profile: dict[str, object]
    evidence_summary: list[dict[str, object]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RunSummary(BaseModel):
    run_id: str
    domain_pack: str
    current_revision_id: str | None = None
    revisions: list[dict[str, object]] = Field(default_factory=list)


class RevisionSummary(BaseModel):
    revision_id: str
    status: RevisionStatus
    parent_revision_id: str | None = None
    evidence_item_count: int = 0
    assumption_count: int = 0
    top_branches: list[dict[str, object]] = Field(default_factory=list)
    available_sections: list[str] = Field(default_factory=list)


class ConversationTurn(BaseModel):
    run_id: str
    revision_id: str
    stage: ConversationStage
    headline: str
    user_message: str
    recommended_command: str | None = None
    available_sections: list[str] = Field(default_factory=list)
    context: dict[str, object] = Field(default_factory=dict)
