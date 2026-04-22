from __future__ import annotations

from hashlib import sha1
import json
from typing import Literal

from pydantic import BaseModel, Field

from forecasting_harness.domain.base import DomainPack
from forecasting_harness.domain.template_utils import normalize_text, term_match_score, tokenize_text
from forecasting_harness.evolution.models import DomainSuggestion
from forecasting_harness.knowledge.manifests import DomainManifest
from forecasting_harness.models import BeliefState
from forecasting_harness.replay import ReplaySuiteResult
from forecasting_harness.workflow.models import EvidencePacket
from forecasting_harness.workflow.planning import classify_text

CompilerSourceKind = Literal["approved-evidence", "replay-miss"]

_STOPWORDS = {
    "about",
    "after",
    "against",
    "board",
    "candidate",
    "company",
    "crisis",
    "domain",
    "evidence",
    "forecast",
    "group",
    "issue",
    "item",
    "major",
    "message",
    "model",
    "note",
    "pack",
    "passage",
    "pressure",
    "response",
    "review",
    "root",
    "run",
    "scenario",
    "should",
    "signal",
    "source",
    "strategy",
    "suggest",
    "target",
    "term",
    "that",
    "their",
    "them",
    "this",
    "toward",
    "with",
}


class CompiledKnowledgeCandidate(BaseModel):
    category: Literal["state-field", "action-bias", "evidence-category", "semantic-alias"]
    target: str | None = None
    text: str
    terms: list[str] = Field(default_factory=list)
    source_kind: CompilerSourceKind
    source_refs: list[str] = Field(default_factory=list)


class KnowledgeCompilerResult(BaseModel):
    domain_slug: str
    source_kind: CompilerSourceKind
    candidates: list[CompiledKnowledgeCandidate] = Field(default_factory=list)

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)


def _known_terms(manifest: DomainManifest) -> set[str]:
    values: set[str] = set()
    for term_list in manifest.category_terms().values():
        values.update(normalize_text(term) for term in term_list if normalize_text(term))
    for alias_group in manifest.semantic_alias_groups:
        values.update(normalize_text(term) for term in alias_group if normalize_text(term))
    for field_rules in manifest.adaptive_state_terms.values():
        for rule in field_rules:
            values.update(normalize_text(term) for term in rule.terms if normalize_text(term))
    for bias in manifest.adaptive_action_biases:
        values.update(normalize_text(term) for term in bias.terms if normalize_text(term))
    return {value for value in values if value}


def _candidate_terms(text: str, *, known_terms: set[str], max_terms: int = 2) -> list[str]:
    tokens = [token for token in tokenize_text(text) if len(token) >= 4 and token not in _STOPWORDS]
    phrases: list[str] = []
    for size in (2, 1, 3):
        for index in range(len(tokens) - size + 1):
            phrase = " ".join(tokens[index : index + size])
            normalized = normalize_text(phrase)
            if not normalized or normalized in known_terms:
                continue
            if any(term_match_score(existing, phrase) > 0 for existing in phrases):
                continue
            phrases.append(phrase)
            if len(phrases) >= max_terms:
                return phrases
    return phrases


def _dedupe_candidates(candidates: list[CompiledKnowledgeCandidate]) -> list[CompiledKnowledgeCandidate]:
    deduped: list[CompiledKnowledgeCandidate] = []
    seen: set[tuple[str, str, tuple[str, ...], tuple[str, ...]]] = set()
    for candidate in candidates:
        key = (
            candidate.category,
            candidate.target or "",
            tuple(candidate.terms),
            tuple(candidate.source_refs),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped


def _action_target(label: str) -> str:
    return normalize_text(label).replace(" ", "-")


def compile_approved_evidence_knowledge(
    *,
    domain_slug: str,
    manifest: DomainManifest,
    evidence_packet: EvidencePacket,
    state: BeliefState,
    pack: DomainPack,
) -> KnowledgeCompilerResult:
    known_terms = _known_terms(manifest)
    category_terms = manifest.category_terms()
    candidates: list[CompiledKnowledgeCandidate] = []

    # Evidence-category and semantic-alias proposals come from approved evidence language.
    for item in evidence_packet.items:
        item_text = " ".join([item.source_title, item.reason, *item.raw_passages])
        category = classify_text(item_text, category_terms=category_terms)
        if category is None:
            continue
        terms = _candidate_terms(item_text, known_terms=known_terms)
        if not terms:
            continue
        candidates.append(
            CompiledKnowledgeCandidate(
                category="evidence-category",
                target=category,
                text=f"Approved evidence introduces additional language for {category}.",
                terms=terms,
                source_kind="approved-evidence",
                source_refs=[item.evidence_id, item.source_id],
            )
        )
        alias_group = [category, *terms]
        normalized_aliases = [normalize_text(term) for term in alias_group]
        if len({term for term in normalized_aliases if term}) >= 2:
            candidates.append(
                CompiledKnowledgeCandidate(
                    category="semantic-alias",
                    text=f"Approved evidence uses related phrasing for {category}.",
                    terms=alias_group,
                    source_kind="approved-evidence",
                    source_refs=[item.evidence_id, item.source_id],
                )
            )
        known_terms.update(normalize_text(term) for term in terms if normalize_text(term))

    # Approved evidence can also justify a small action-bias proposal when the top action label
    # is already reflected directly in the evidence language.
    top_actions = sorted(
        pack.propose_actions(state),
        key=lambda action: (float(action.get("prior", 0.0) or 0.0), str(action.get("action_id") or action.get("branch_id") or "")),
        reverse=True,
    )
    if top_actions and evidence_packet.items:
        top_action = top_actions[0]
        action_label = str(top_action.get("label") or top_action.get("action_id") or top_action.get("branch_id") or "")
        flattened_evidence_text = " ".join(
            part for item in evidence_packet.items for part in [item.source_title, item.reason, *item.raw_passages]
        )
        if action_label and term_match_score(flattened_evidence_text, action_label) > 0:
            action_terms = _candidate_terms(f"{action_label} {flattened_evidence_text}", known_terms=known_terms, max_terms=2)
            if action_terms:
                candidates.append(
                    CompiledKnowledgeCandidate(
                        category="action-bias",
                        target=str(top_action.get("action_id") or top_action.get("branch_id") or _action_target(action_label)),
                        text=f"Approved evidence reinforces action prior for {action_label}.",
                        terms=action_terms,
                        source_kind="approved-evidence",
                        source_refs=sorted({item.source_id for item in evidence_packet.items}),
                    )
                )

    return KnowledgeCompilerResult(
        domain_slug=domain_slug,
        source_kind="approved-evidence",
        candidates=_dedupe_candidates(candidates),
    )


def compile_replay_miss_knowledge(
    *,
    domain_slug: str,
    manifest: DomainManifest,
    replay_result: ReplaySuiteResult,
) -> KnowledgeCompilerResult:
    known_terms = _known_terms(manifest)
    candidates: list[CompiledKnowledgeCandidate] = []

    for result in replay_result.results:
        if result.domain_pack != domain_slug:
            continue

        source_text = " ".join(
            [
                result.case_title or "",
                result.expected_root_strategy or "",
                " ".join(result.expected_evidence_sources),
                " ".join(result.expected_inferred_fields),
            ]
        )

        if result.root_strategy_match is False and result.expected_root_strategy:
            action_terms = _candidate_terms(source_text, known_terms=known_terms, max_terms=2)
            if action_terms:
                candidates.append(
                    CompiledKnowledgeCandidate(
                        category="action-bias",
                        target=_action_target(result.expected_root_strategy),
                        text=f"Replay miss suggests bias toward {result.expected_root_strategy}.",
                        terms=action_terms,
                        source_kind="replay-miss",
                        source_refs=[result.run_id, *result.expected_evidence_sources],
                    )
                )
                known_terms.update(normalize_text(term) for term in action_terms if normalize_text(term))

        missing_fields = sorted(set(result.expected_inferred_fields).difference(result.inferred_fields))
        for field_name in missing_fields:
            field_terms = _candidate_terms(
                f"{field_name.replace('_', ' ')} {' '.join(result.expected_evidence_sources)} {result.case_title or ''}",
                known_terms=known_terms,
                max_terms=2,
            )
            if not field_terms:
                field_terms = [field_name.replace("_", " ")]
            candidates.append(
                CompiledKnowledgeCandidate(
                    category="state-field",
                    target=field_name,
                    text=f"Replay miss suggests additional state terms for {field_name}.",
                    terms=field_terms,
                    source_kind="replay-miss",
                    source_refs=[result.run_id, *result.expected_evidence_sources],
                )
            )
            known_terms.update(normalize_text(term) for term in field_terms if normalize_text(term))

    return KnowledgeCompilerResult(
        domain_slug=domain_slug,
        source_kind="replay-miss",
        candidates=_dedupe_candidates(candidates),
    )


def suggestion_from_compiled_candidate(
    *,
    domain_slug: str,
    candidate: CompiledKnowledgeCandidate,
    timestamp,
) -> DomainSuggestion:
    identity_payload = {
        "domain_slug": domain_slug,
        "category": candidate.category,
        "target": candidate.target or "",
        "terms": candidate.terms,
        "source_kind": candidate.source_kind,
        "source_refs": candidate.source_refs,
        "text": candidate.text,
    }
    suggestion_hash = sha1(json.dumps(identity_payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return DomainSuggestion(
        suggestion_id=f"compiler-{domain_slug}-{suggestion_hash}",
        timestamp=timestamp,
        domain_slug=domain_slug,
        provenance="compiler",
        category=candidate.category,
        target=candidate.target,
        text=candidate.text,
        terms=list(candidate.terms),
        status="pending",
    )
