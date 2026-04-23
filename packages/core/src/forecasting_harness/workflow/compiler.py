from __future__ import annotations

from datetime import datetime, timezone
import re

from forecasting_harness.domain.base import DomainPack
from forecasting_harness.models import Actor, BehaviorProfile, BeliefField, BeliefState
from forecasting_harness.workflow.models import AssumptionSummary, EvidencePacketItem, IntakeDraft


def _actor_id_from_name(name: str) -> str:
    actor_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return actor_id or name.lower()


def _dedupe_actor_names(values: list[str]) -> list[str]:
    seen_actor_families: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        actor_family = _canonical_actor_family(value)
        if actor_family in seen_actor_families:
            continue
        seen_actor_families.add(actor_family)
        unique_values.append(value)
    return unique_values


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def _normalized_tokens(text: str) -> tuple[str, ...]:
    normalized = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    if not normalized:
        return ()
    return tuple(token for token in normalized.split(" ") if token)


def _canonical_actor_family(name: str) -> str:
    actor_id = _actor_id_from_name(name)
    tokens = _normalized_tokens(name)
    if actor_id in {"us", "u-s", "united-states", "united-states-of-america"}:
        return "united-states"
    if tokens in {("us",), ("u", "s"), ("united", "states"), ("united", "states", "of", "america")}:
        return "united-states"
    return actor_id


def _actor_aliases(name: str) -> set[tuple[str, ...]]:
    actor_id = _actor_id_from_name(name)
    actor_family = _canonical_actor_family(name)
    aliases = {
        _normalized_tokens(name),
        _normalized_tokens(actor_id),
        _normalized_tokens(actor_id.replace("-", " ")),
    }
    if actor_family == "united-states":
        aliases.update(
            {
                _normalized_tokens("us"),
                _normalized_tokens("u.s."),
                _normalized_tokens("u s"),
                _normalized_tokens("united states"),
                _normalized_tokens("united states of america"),
            }
        )
    elif actor_id == "china":
        aliases.update(
            {
                _normalized_tokens("chinese"),
                _normalized_tokens("beijing"),
                _normalized_tokens("prc"),
                _normalized_tokens("pla"),
                _normalized_tokens("people's liberation army"),
                _normalized_tokens("peoples liberation army"),
            }
        )
    elif actor_id == "japan":
        aliases.update({_normalized_tokens("japanese"), _normalized_tokens("tokyo")})
    elif actor_id == "taiwan":
        aliases.update({_normalized_tokens("taiwanese"), _normalized_tokens("taipei")})
    return {alias for alias in aliases if alias}


def _contains_alias(text: str, aliases: set[tuple[str, ...]]) -> bool:
    text_tokens = _normalized_tokens(text)
    if not text_tokens:
        return False
    for alias in aliases:
        alias_length = len(alias)
        for index in range(len(text_tokens) - alias_length + 1):
            if text_tokens[index : index + alias_length] == alias:
                return True
    return False


def _count_term_matches(text: str, terms: tuple[str, ...]) -> int:
    lowered = text.lower()
    return sum(lowered.count(term) for term in terms)


def _behavior_segments(
    intake: IntakeDraft,
    assumptions: AssumptionSummary,
    approved_evidence_items: list[EvidencePacketItem],
) -> list[str]:
    return [
        intake.event_framing,
        intake.current_development,
        *intake.known_constraints,
        *intake.known_unknowns,
        *assumptions.summary,
        *(passage for item in approved_evidence_items for passage in item.raw_passages),
    ]


def _segment_clauses(segment: str) -> list[str]:
    parts = re.split(r"[;!?]\s+|\b(?:while|whereas|but|however)\b", segment)
    return [part.strip(" ,.;") for part in parts if part.strip(" ,.;")]


def _first_anchor_actor_family(
    clause: str,
    actor_aliases: dict[str, set[tuple[str, ...]]],
) -> str | None:
    tokens = _normalized_tokens(clause)
    if not tokens:
        return None

    best_match: tuple[int, int, str] | None = None
    for actor_family, aliases in actor_aliases.items():
        for alias in aliases:
            alias_length = len(alias)
            for index in range(len(tokens) - alias_length + 1):
                if tokens[index : index + alias_length] != alias:
                    continue
                candidate = (index, -alias_length, actor_family)
                if best_match is None or candidate < best_match:
                    best_match = candidate
                break
    return None if best_match is None else best_match[2]


def _relevant_actor_texts(
    actor_names: list[str],
    intake: IntakeDraft,
    assumptions: AssumptionSummary,
    approved_evidence_items: list[EvidencePacketItem],
) -> dict[str, str]:
    alias_map = {
        _canonical_actor_family(name): _actor_aliases(name)
        for name in actor_names
    }
    anchored_segments: dict[str, list[str]] = {actor_family: [] for actor_family in alias_map}
    for segment in _behavior_segments(intake, assumptions, approved_evidence_items):
        for clause in _segment_clauses(segment):
            actor_family = _first_anchor_actor_family(clause, alias_map)
            if actor_family is None:
                continue
            anchored_segments[actor_family].append(clause)
    return {
        actor_family: " ".join(segments).strip()
        for actor_family, segments in anchored_segments.items()
        if segments
    }


def _infer_behavior_profile_from_text(
    actor_text: str,
) -> BehaviorProfile | None:
    if not actor_text:
        return None

    domestic_hits = _count_term_matches(
        actor_text,
        ("domestic", "audience", "public", "party", "political", "leadership", "resolve", "meeting"),
    )
    alliance_hits = _count_term_matches(
        actor_text,
        ("alliance", "ally", "allies", "coordination", "backing", "security support", "security commitment", "support"),
    )
    negotiation_hits = _count_term_matches(
        actor_text,
        ("negotiat", "talk", "backchannel", "ceasefire", "de-escalat", "diplomac"),
    )
    reputational_hits = _count_term_matches(
        actor_text,
        ("credibility", "reputation", "prestige", "standing", "resolve", "signal"),
    )
    coercive_hits = _count_term_matches(
        actor_text,
        ("exercise", "drill", "strike", "missile", "intercept", "retaliat", "military", "blockade"),
    )

    profile = BehaviorProfile(
        domestic_sensitivity=round(_bounded(0.4 + 0.11 * domestic_hits), 3) if domestic_hits >= 2 else None,
        alliance_dependence=round(_bounded(0.42 + 0.11 * alliance_hits), 3) if alliance_hits >= 2 else None,
        negotiation_openness=round(_bounded(0.35 + 0.1 * negotiation_hits), 3) if negotiation_hits >= 2 else None,
        reputational_sensitivity=round(_bounded(0.35 + 0.1 * reputational_hits), 3) if reputational_hits >= 2 else None,
        coercive_bias=round(_bounded(0.3 + 0.09 * coercive_hits), 3) if coercive_hits >= 2 else None,
    )
    if profile.model_dump(exclude_none=True):
        return profile
    return None


def _infer_behavior_profiles(
    actor_names: list[str],
    intake: IntakeDraft,
    assumptions: AssumptionSummary,
    approved_evidence_items: list[EvidencePacketItem],
) -> dict[str, BehaviorProfile | None]:
    actor_texts = _relevant_actor_texts(actor_names, intake, assumptions, approved_evidence_items)
    return {
        _canonical_actor_family(name): _infer_behavior_profile_from_text(
            actor_texts.get(_canonical_actor_family(name), "")
        )
        for name in actor_names
    }


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
    behavior_profiles = _infer_behavior_profiles(actor_names, intake, assumptions, approved_evidence_items or [])
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
    actors = [
        Actor(
            actor_id=_canonical_actor_family(name),
            name=name,
            behavior_profile=behavior_profiles.get(_canonical_actor_family(name)),
        )
        for name in actor_names
    ]
    return BeliefState(
        run_id=run_id,
        revision_id=revision_id,
        domain_pack=pack.slug(),
        phase=intake.current_stage,
        interaction_model=pack.interaction_model(),
        actors=actors,
        fields=fields,
        objectives={},
        capabilities={},
        constraints={str(index): value for index, value in enumerate(intake.known_constraints)},
        unknowns=list(intake.known_unknowns),
        current_epoch=intake.current_stage,
        horizon=intake.time_horizon,
        approved_evidence_ids=list(approved_evidence_ids),
    )
