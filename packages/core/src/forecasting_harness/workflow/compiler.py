from __future__ import annotations

from datetime import datetime, timezone
import re

from forecasting_harness.domain.base import DomainPack
from forecasting_harness.models import Actor, BeliefField, BeliefState
from forecasting_harness.workflow.models import AssumptionSummary, EvidencePacketItem, IntakeDraft


def _actor_id_from_name(name: str) -> str:
    actor_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return actor_id or name.lower()


def _dedupe_actor_names(values: list[str]) -> list[str]:
    seen_actor_ids: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        actor_id = _actor_id_from_name(value)
        if actor_id in seen_actor_ids:
            continue
        seen_actor_ids.add(actor_id)
        unique_values.append(value)
    return unique_values


def compile_belief_state(
    *,
    run_id: str,
    revision_id: str,
    pack: DomainPack,
    intake: IntakeDraft,
    assumptions: AssumptionSummary,
    approved_evidence_ids: list[str],
    approved_evidence_items: list[EvidencePacketItem] | None = None,
) -> BeliefState:
    canonical_phases = pack.canonical_phases()
    if canonical_phases and intake.current_stage not in canonical_phases:
        raise ValueError(
            f"unsupported phase {intake.current_stage!r} for domain pack {pack.slug()!r}; "
            f"expected one of: {', '.join(canonical_phases)}"
        )
    actor_names = _dedupe_actor_names(
        [*intake.focus_entities, *intake.suggested_entities, *assumptions.suggested_actors]
    )
    now = datetime.now(timezone.utc)
    fields = {
        "event_framing": BeliefField(
            value=intake.event_framing,
            normalized_value=intake.event_framing,
            status="observed",
            confidence=1.0,
            last_updated_at=now,
        ),
        "current_development": BeliefField(
            value=intake.current_development,
            normalized_value=intake.current_development,
            status="observed",
            confidence=1.0,
            last_updated_at=now,
        ),
    }
    inferred_pack_fields = pack.infer_pack_fields(
        intake,
        assumptions,
        approved_evidence_items or [],
    )
    for field_name, value in intake.pack_fields.items():
        fields[field_name] = BeliefField(
            value=value,
            normalized_value=value,
            status="observed",
            confidence=1.0,
            last_updated_at=now,
        )
    for field_name, value in inferred_pack_fields.items():
        if field_name in fields:
            continue
        fields[field_name] = BeliefField(
            value=value,
            normalized_value=value,
            status="inferred",
            supporting_evidence_ids=list(approved_evidence_ids),
            confidence=0.65,
            last_updated_at=now,
        )
    return BeliefState(
        run_id=run_id,
        revision_id=revision_id,
        domain_pack=pack.slug(),
        phase=intake.current_stage,
        interaction_model=pack.interaction_model(),
        actors=[Actor(actor_id=_actor_id_from_name(name), name=name) for name in actor_names],
        fields=fields,
        objectives={},
        capabilities={},
        constraints={str(index): value for index, value in enumerate(intake.known_constraints)},
        unknowns=list(intake.known_unknowns),
        current_epoch=intake.current_stage,
        horizon=intake.time_horizon,
        approved_evidence_ids=list(approved_evidence_ids),
    )
