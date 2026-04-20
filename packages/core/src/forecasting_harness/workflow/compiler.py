from __future__ import annotations

from datetime import datetime, timezone
import re

from forecasting_harness.domain.base import DomainPack
from forecasting_harness.models import Actor, BeliefField, BeliefState
from forecasting_harness.workflow.models import AssumptionSummary, IntakeDraft


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values


def _actor_id_from_name(name: str) -> str:
    actor_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return actor_id or name.lower()


def compile_belief_state(
    *,
    run_id: str,
    revision_id: str,
    pack: DomainPack,
    intake: IntakeDraft,
    assumptions: AssumptionSummary,
    approved_evidence_ids: list[str],
) -> BeliefState:
    canonical_phases = pack.canonical_phases()
    if canonical_phases and intake.current_phase not in canonical_phases:
        raise ValueError(
            f"unsupported phase {intake.current_phase!r} for domain pack {pack.slug()!r}; "
            f"expected one of: {', '.join(canonical_phases)}"
        )
    actor_names = _dedupe_preserving_order([*intake.primary_actors, *assumptions.suggested_actors])
    now = datetime.now(timezone.utc)
    return BeliefState(
        run_id=run_id,
        revision_id=revision_id,
        domain_pack=pack.slug(),
        phase=intake.current_phase,
        interaction_model=pack.interaction_model(),
        actors=[Actor(actor_id=_actor_id_from_name(name), name=name) for name in actor_names],
        fields={
            "event_framing": BeliefField(
                value=intake.event_framing,
                normalized_value=intake.event_framing,
                status="observed",
                confidence=1.0,
                last_updated_at=now,
            ),
            "trigger": BeliefField(
                value=intake.trigger,
                normalized_value=intake.trigger,
                status="observed",
                confidence=1.0,
                last_updated_at=now,
            ),
        },
        objectives={},
        capabilities={},
        constraints={str(index): value for index, value in enumerate(intake.known_constraints)},
        unknowns=list(intake.known_unknowns),
        current_epoch=intake.current_phase,
        horizon=intake.time_horizon,
        approved_evidence_ids=list(approved_evidence_ids),
    )
