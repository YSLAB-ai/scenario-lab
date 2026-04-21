from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.compatibility import compare_belief_states
from forecasting_harness.domain.base import DomainPack
from forecasting_harness.domain.registry import DomainPackRegistry, build_default_registry
from forecasting_harness.domain.template_utils import normalize_text, term_match_score
from forecasting_harness.knowledge.manifests import load_domain_manifest
from forecasting_harness.models import BeliefState
from forecasting_harness.objectives import default_objective_profile
from forecasting_harness.query_api import summarize_scenario_families, summarize_top_branches
from forecasting_harness.retrieval import CorpusRegistry, RetrievalQuery, SearchEngine, detect_source_type, ingest_file
from forecasting_harness.simulation.engine import SimulationEngine
from forecasting_harness.workflow.evidence import draft_evidence_packet as build_evidence_packet
from forecasting_harness.workflow.models import (
    AdapterAction,
    ApprovalPacket,
    AssumptionSummary,
    BatchIngestionResult,
    ConversationTurn,
    EvidencePacket,
    IngestionRecommendation,
    IngestionPlan,
    IntakeDraft,
    IntakeGuidance,
    RetrievalPlan,
    RevisionRecord,
    RevisionSummary,
    RunRecord,
    RunSummary,
)
from forecasting_harness.workflow.planning import build_ingest_tasks, build_query_variants, category_match_scores, classify_text, compact_query, select_source_role
from forecasting_harness.workflow.compiler import compile_belief_state
from forecasting_harness.workflow.reporting import render_report


def _validate_pack_fields(pack: DomainPack, intake: IntakeDraft) -> None:
    schema = pack.extend_schema()
    unknown_fields = sorted(set(intake.pack_fields) - set(schema))
    if unknown_fields:
        raise ValueError(f"unknown pack_fields: {', '.join(unknown_fields)}")

    expected_types = {"str": str, "int": int, "float": float, "bool": bool}
    for field_name, value in intake.pack_fields.items():
        expected_type_name = schema[field_name]
        expected_type = expected_types.get(expected_type_name)
        if expected_type is None:
            raise ValueError(f"unsupported pack field type: {expected_type_name}")
        if not isinstance(value, expected_type):
            raise ValueError(f"pack_fields.{field_name} must be {expected_type_name}")


class WorkflowService:
    def __init__(
        self,
        repository: RunRepository,
        *,
        domain_registry: DomainPackRegistry | None = None,
        corpus_registry: CorpusRegistry | None = None,
    ) -> None:
        self.repository = repository
        self.domain_registry = domain_registry or build_default_registry()
        self.corpus_registry = corpus_registry

    def _pack_for_run(self, run_id: str) -> DomainPack:
        run = self.repository.load_run_record(run_id)
        return self.domain_registry.resolve(run.domain_pack)

    def _artifact_path(self, run_id: str, section: str, revision_id: str, *, approved: bool) -> str:
        suffix = "approved" if approved else "draft"
        return str(self.repository.run_dir(run_id) / section / f"{revision_id}.{suffix}.json")

    def _artifact_exists(self, run_id: str, section: str, revision_id: str, *, approved: bool) -> bool:
        suffix = "approved" if approved else "draft"
        return (self.repository.run_dir(run_id) / section / f"{revision_id}.{suffix}.json").exists()

    def _available_sections(self, run_id: str, revision_id: str) -> list[str]:
        run_dir = self.repository.run_dir(run_id)
        available_sections: list[str] = []
        for section in ("intake", "evidence", "assumptions", "belief-state", "simulation"):
            draft_path = run_dir / section / f"{revision_id}.draft.json"
            approved_path = run_dir / section / f"{revision_id}.approved.json"
            if draft_path.exists() or approved_path.exists():
                available_sections.append(section)
        return available_sections

    def _adapter_action(
        self,
        command: str,
        label: str,
        description: str,
        *,
        required_options: list[str] | None = None,
    ) -> AdapterAction:
        return AdapterAction(
            command=command,
            label=label,
            description=description,
            required_options=required_options or [],
        )

    def _hit_matches_entity_names(self, hit: dict[str, object], *, entity_names: list[str]) -> bool:
        tags = hit.get("tags") or {}

        search_text = " ".join(
            [
                str(hit.get("title", "")),
                str(hit.get("content", "")),
                " ".join(f"{key} {value}" for key, value in (tags.items() if isinstance(tags, dict) else [])),
            ]
        )
        normalized_text = normalize_text(search_text)
        return any(term_match_score(normalized_text, entity_name) > 0 for entity_name in entity_names if entity_name)

    def _hit_run_tag(self, hit: dict[str, object]) -> str | None:
        tags = hit.get("tags") or {}
        if not isinstance(tags, dict):
            return None
        value = tags.get("run_id")
        if value in (None, ""):
            return None
        return str(value)

    def _ensure_revision_record(
        self,
        run_id: str,
        revision_id: str,
        *,
        parent_revision_id: str | None = None,
    ) -> RevisionRecord:
        try:
            record = self.repository.load_revision_record(run_id, revision_id)
        except FileNotFoundError:
            record = RevisionRecord(
                revision_id=revision_id,
                parent_revision_id=parent_revision_id,
                created_at=datetime.now(timezone.utc),
            )
            self.repository.save_revision_record(run_id, record)
            return record

        if parent_revision_id is not None and record.parent_revision_id is None:
            record = record.model_copy(update={"parent_revision_id": parent_revision_id})
            self.repository.save_revision_record(run_id, record)
        return record

    def start_run(self, run_id: str, domain_pack: str) -> RunRecord:
        run = RunRecord(run_id=run_id, domain_pack=domain_pack, created_at=datetime.now(timezone.utc))
        self.repository.init_run(run)
        self.repository.append_event(run_id, "run-started", {"run_id": run_id})
        return run

    def save_intake_draft(
        self,
        run_id: str,
        revision_id: str,
        intake: IntakeDraft,
        *,
        parent_revision_id: str | None = None,
    ) -> None:
        pack = self._pack_for_run(run_id)
        _validate_pack_fields(pack, intake)
        validation_errors = pack.validate_intake(intake)
        if validation_errors:
            raise ValueError("; ".join(validation_errors))
        self._ensure_revision_record(run_id, revision_id, parent_revision_id=parent_revision_id)
        self.repository.write_revision_json(run_id, "intake", revision_id, intake.model_dump(mode="json"), approved=False)
        self.repository.append_event(run_id, "intake-drafted", {"revision_id": revision_id})

    def save_evidence_draft(
        self,
        run_id: str,
        revision_id: str,
        packet: EvidencePacket,
        *,
        parent_revision_id: str | None = None,
    ) -> None:
        if packet.revision_id != revision_id:
            raise ValueError(f"revision_id mismatch: expected {revision_id!r}, got {packet.revision_id!r}")
        self._ensure_revision_record(run_id, revision_id, parent_revision_id=parent_revision_id)
        self.repository.write_revision_json(
            run_id,
            "evidence",
            revision_id,
            packet.model_dump(mode="json"),
            approved=False,
        )
        self.repository.append_event(run_id, "evidence-drafted", {"revision_id": revision_id})

    def draft_intake_guidance(self, run_id: str, revision_id: str) -> IntakeGuidance:
        intake = self.repository.load_revision_model(run_id, "intake", revision_id, IntakeDraft, approved=False)
        pack = self._pack_for_run(run_id)
        profile = pack.default_objective_profile()
        return IntakeGuidance(
            domain_pack=pack.slug(),
            current_stage=intake.current_stage,
            canonical_stages=pack.canonical_phases(),
            suggested_entities=pack.suggest_related_actors(intake),
            follow_up_questions=pack.suggest_questions(),
            pack_field_schema=pack.extend_schema(),
            default_objective_profile=profile.model_dump(mode="json"),
        )

    def draft_approval_packet(self, run_id: str, revision_id: str) -> ApprovalPacket:
        intake = self.repository.load_revision_model(run_id, "intake", revision_id, IntakeDraft, approved=False)
        evidence = self.repository.load_revision_model(run_id, "evidence", revision_id, EvidencePacket, approved=False)
        pack = self._pack_for_run(run_id)
        profile = pack.default_objective_profile()

        warnings: list[str] = []
        if not evidence.items:
            warnings.append("no evidence drafted yet")
        if intake.known_unknowns:
            warnings.append("known unknowns remain unresolved")
        if not intake.suggested_entities:
            warnings.append("no suggested entities included yet")

        outside_entities = sorted(set(intake.suggested_entities) - set(intake.focus_entities))
        assumption_summary: list[str] = [f"known unknown: {value}" for value in intake.known_unknowns]
        if not evidence.items:
            assumption_summary.append("evidence gap: no cited evidence approved yet")
        for entity in outside_entities:
            assumption_summary.append(f"suggested external entity: {entity}")

        return ApprovalPacket(
            revision_id=revision_id,
            intake_summary={
                "event_framing": intake.event_framing,
                "focus_entities": intake.focus_entities,
                "current_development": intake.current_development,
                "current_stage": intake.current_stage,
                "time_horizon": intake.time_horizon,
                "known_constraints": intake.known_constraints,
                "known_unknowns": intake.known_unknowns,
            },
            assumption_summary=assumption_summary,
            objective_profile=profile.model_dump(mode="json"),
            evidence_summary=[
                {
                    "evidence_id": item.evidence_id,
                    "source_id": item.source_id,
                    "source_title": item.source_title,
                    "reason": item.reason,
                    "passage_count": len(item.raw_passages),
                }
                for item in evidence.items
            ],
            warnings=warnings,
        )

    def draft_evidence_packet(
        self,
        run_id: str,
        revision_id: str,
        *,
        pack: DomainPack,
        query_text: str | None = None,
        max_per_source: int = 2,
        max_total: int = 6,
    ) -> EvidencePacket:
        if self.corpus_registry is None:
            raise ValueError("corpus_registry is required for evidence drafting")

        intake = self.repository.load_revision_model(run_id, "intake", revision_id, IntakeDraft, approved=False)
        retrieval_plan = self.draft_retrieval_plan(run_id, revision_id, pack=pack, query_text=query_text)
        manifest = load_domain_manifest(pack.slug())
        search_engine = SearchEngine(self.corpus_registry)
        merged_hits: dict[tuple[str, str], dict[str, object]] = {}
        for variant in retrieval_plan.query_variants:
            hits = search_engine.search(
                RetrievalQuery(text=variant, filters=retrieval_plan.filters),
                freshness_policy=pack.freshness_policy(),
                alias_groups=manifest.alias_groups(),
            )
            for hit in hits:
                key = (str(hit["source_id"]), str(hit["chunk_id"]))
                result = dict(hit)
                if key not in merged_hits:
                    result["matched_queries"] = [variant]
                    merged_hits[key] = result
                    continue
                merged = merged_hits[key]
                merged["score"] = max(float(merged.get("score", 0.0)), float(result.get("score", 0.0)))
                merged["semantic_score"] = max(
                    float(merged.get("semantic_score", 0.0)), float(result.get("semantic_score", 0.0))
                )
                merged["lexical_score"] = max(
                    float(merged.get("lexical_score", 0.0)), float(result.get("lexical_score", 0.0))
                )
                matched_queries = list(merged.get("matched_queries", []))
                if variant not in matched_queries:
                    matched_queries.append(variant)
                merged["matched_queries"] = matched_queries

        hits = sorted(
            merged_hits.values(),
            key=lambda item: (-float(item.get("score", 0.0)), str(item.get("source_id", "")), str(item.get("chunk_id", ""))),
        )
        current_run_hits = [hit for hit in hits if self._hit_run_tag(hit) == run_id]
        focus_hits = [
            hit for hit in hits if self._hit_matches_entity_names(hit, entity_names=intake.focus_entities)
        ]
        fallback_hits = [hit for hit in hits if self._hit_run_tag(hit) in (None, run_id)]

        if current_run_hits:
            hits = current_run_hits
        elif focus_hits:
            hits = focus_hits
        else:
            hits = fallback_hits
        packet = build_evidence_packet(
            revision_id,
            hits,
            max_per_source=max_per_source,
            max_total=max_total,
            evidence_categories=manifest.evidence_categories,
            category_terms=manifest.category_terms(),
        )
        self.save_evidence_draft(run_id, revision_id, packet)
        self.repository.append_event(
            run_id,
            "evidence-packet-drafted",
            {"revision_id": revision_id, "query_text": retrieval_plan.base_query},
        )
        return packet

    def draft_retrieval_plan(
        self,
        run_id: str,
        revision_id: str,
        *,
        pack: DomainPack,
        query_text: str | None = None,
    ) -> RetrievalPlan:
        intake = self.repository.load_revision_model(run_id, "intake", revision_id, IntakeDraft, approved=False)
        manifest = load_domain_manifest(pack.slug())
        query_variants = build_query_variants(intake, manifest, query_text=query_text)
        base_query = query_variants[0] if query_variants else ""
        return RetrievalPlan(
            revision_id=revision_id,
            domain_pack=pack.slug(),
            base_query=base_query,
            query_variants=query_variants,
            filters=pack.retrieval_filters(intake),
            target_evidence_categories=list(manifest.evidence_categories),
        )

    def draft_ingestion_plan(
        self,
        run_id: str,
        revision_id: str,
        *,
        pack: DomainPack,
    ) -> IngestionPlan:
        if self.corpus_registry is None:
            raise ValueError("corpus_registry is required for ingestion planning")

        intake = self.repository.load_revision_model(run_id, "intake", revision_id, IntakeDraft, approved=False)
        manifest = load_domain_manifest(pack.slug())
        filters = pack.retrieval_filters(intake)
        retrieval_plan = self.draft_retrieval_plan(run_id, revision_id, pack=pack)
        search_engine = SearchEngine(self.corpus_registry)

        documents = [
            document
            for document in self.corpus_registry.list_documents()
            if all((document.get("tags") or {}).get(key) == value for key, value in filters.items())
        ]

        merged_hits: dict[tuple[str, str], dict[str, object]] = {}
        for variant in retrieval_plan.query_variants:
            hits = search_engine.search(
                RetrievalQuery(text=variant, filters=filters),
                freshness_policy=pack.freshness_policy(),
                alias_groups=manifest.alias_groups(),
            )
            for hit in hits:
                key = (str(hit["source_id"]), str(hit["chunk_id"]))
                result = dict(hit)
                if key not in merged_hits:
                    result["matched_queries"] = [variant]
                    merged_hits[key] = result
                    continue
                merged = merged_hits[key]
                merged["score"] = max(float(merged.get("score", 0.0)), float(result.get("score", 0.0)))
                matched_queries = list(merged.get("matched_queries", []))
                if variant not in matched_queries:
                    matched_queries.append(variant)
                merged["matched_queries"] = matched_queries

        chunks = sorted(
            merged_hits.values(),
            key=lambda item: (-float(item.get("score", 0.0)), str(item.get("source_id", "")), str(item.get("chunk_id", ""))),
        )

        current_run_chunks = [chunk for chunk in chunks if self._hit_run_tag(chunk) == run_id]
        focus_chunks = [
            chunk for chunk in chunks if self._hit_matches_entity_names(chunk, entity_names=intake.focus_entities)
        ]
        if current_run_chunks:
            relevant_chunks = current_run_chunks
        elif focus_chunks:
            relevant_chunks = focus_chunks
        else:
            relevant_chunks = []

        relevant_source_ids = {str(chunk.get("source_id", "")) for chunk in relevant_chunks}
        relevant_documents = [
            document
            for document in documents
            if str(document.get("source_id", "")) in relevant_source_ids
            or (document.get("tags") or {}).get("run_id") == run_id
        ]

        category_terms = manifest.category_terms()
        covered: set[str] = set()
        for chunk in relevant_chunks:
            matched = classify_text(
                " ".join(
                    [
                        str(chunk.get("title", "")),
                        str(chunk.get("content", "")),
                    ]
                ),
                category_terms=category_terms,
            )
            if matched:
                covered.add(matched)

        covered_categories = [category for category in manifest.evidence_categories if category in covered]
        missing_categories = [category for category in manifest.evidence_categories if category not in covered]
        return IngestionPlan(
            revision_id=revision_id,
            domain_pack=pack.slug(),
            corpus_source_count=len(relevant_documents),
            current_sources=[
                {
                    "source_id": str(document["source_id"]),
                    "title": str(document["title"]),
                    "source_type": str(document["source_type"]),
                    "published_at": document.get("published_at"),
                }
                for document in relevant_documents
            ],
            covered_evidence_categories=covered_categories,
            missing_evidence_categories=missing_categories,
            recommended_source_types=list(manifest.recommended_source_types),
            starter_sources=[source.model_dump(mode="json") for source in manifest.starter_sources],
            ingestion_priorities=list(manifest.ingestion_priorities),
            ingest_tasks=build_ingest_tasks(manifest, missing_categories=missing_categories),
        )

    def recommend_ingestion_files(
        self,
        run_id: str,
        revision_id: str,
        *,
        pack: DomainPack,
        path,
    ) -> list[IngestionRecommendation]:
        if self.corpus_registry is None:
            raise ValueError("corpus_registry is required for ingestion recommendations")

        manifest = load_domain_manifest(pack.slug())
        plan = self.draft_ingestion_plan(run_id, revision_id, pack=pack)
        candidate_categories = plan.missing_evidence_categories or manifest.evidence_categories
        category_terms = manifest.category_terms()

        recommendations: list[IngestionRecommendation] = []
        for candidate in sorted(path.iterdir()):
            if not candidate.is_file():
                continue
            try:
                detect_source_type(candidate)
            except ValueError:
                continue

            document = ingest_file(candidate)
            resolved_source_id = self.corpus_registry.resolve_source_id(document.source_id, document.path)
            content_text = compact_query([document.title, " ".join(chunk.content for chunk in document.chunks)])
            scores = category_match_scores(
                content_text,
                category_terms={category: category_terms.get(category, [category]) for category in candidate_categories},
            )
            matched_categories = [category for category in candidate_categories if category in scores]
            if not matched_categories:
                continue

            source = select_source_role(manifest, text=content_text, matched_categories=matched_categories)
            priority_score = 0.0
            for index, category in enumerate(candidate_categories):
                if category in scores:
                    priority_score += float((len(candidate_categories) - index) * scores[category])
            recommended_tags = {"domain": pack.slug(), "source_role": source.kind, "run_id": run_id}
            recommended_tags["evidence_category"] = matched_categories[0]
            recommendations.append(
                IngestionRecommendation(
                    path=str(candidate.resolve()),
                    source_id=resolved_source_id,
                    title=document.title,
                    source_type=document.source_type,
                    source_role=source.kind,
                    matched_evidence_categories=matched_categories,
                    priority_score=priority_score,
                    recommended_tags=recommended_tags,
                )
            )

        recommendations.sort(
            key=lambda item: (-item.priority_score, item.source_role, item.source_id)
        )
        return recommendations

    def batch_ingest_recommended_files(
        self,
        run_id: str,
        revision_id: str,
        *,
        pack: DomainPack,
        path,
        max_files: int = 5,
    ) -> BatchIngestionResult:
        if self.corpus_registry is None:
            raise ValueError("corpus_registry is required for batch ingestion")

        recommendations = self.recommend_ingestion_files(run_id, revision_id, pack=pack, path=path)
        selected = recommendations[:max_files]
        selected_paths = {item.path for item in selected}
        skipped_count = 0
        ingested_source_ids: list[str] = []

        for candidate in sorted(path.iterdir()):
            if not candidate.is_file():
                continue
            try:
                detect_source_type(candidate)
            except ValueError:
                skipped_count += 1
                continue
            if str(candidate.resolve()) not in selected_paths:
                skipped_count += 1
                continue

            recommendation = next(item for item in selected if item.path == str(candidate.resolve()))
            document = ingest_file(
                candidate,
                source_id=recommendation.source_id,
                title=recommendation.title,
                tags=recommendation.recommended_tags,
            )
            actual_source_id = self.corpus_registry.register_document(
                source_id=document.source_id,
                title=document.title,
                source_type=document.source_type,
                path=document.path,
                published_at=document.published_at,
                tags=document.tags,
                chunks=[
                    {
                        "chunk_id": chunk.chunk_id,
                        "location": chunk.location,
                        "content": chunk.content,
                    }
                    for chunk in document.chunks
                ],
            )
            ingested_source_ids.append(actual_source_id)

        return BatchIngestionResult(
            ingested_count=len(ingested_source_ids),
            skipped_count=skipped_count,
            ingested_source_ids=ingested_source_ids,
        )

    def curate_evidence_draft(self, run_id: str, revision_id: str, evidence_ids: list[str]) -> EvidencePacket:
        packet = self.repository.load_revision_model(run_id, "evidence", revision_id, EvidencePacket, approved=False)
        items_by_id = {item.evidence_id: item for item in packet.items}
        unknown_ids = [evidence_id for evidence_id in evidence_ids if evidence_id not in items_by_id]
        if unknown_ids:
            raise ValueError(f"unknown evidence ids: {', '.join(unknown_ids)}")

        curated_packet = packet.model_copy(
            update={"items": [item for item in packet.items if item.evidence_id in evidence_ids]}
        )
        self.repository.write_revision_json(
            run_id,
            "evidence",
            revision_id,
            curated_packet.model_dump(mode="json"),
            approved=False,
        )
        self.repository.append_event(
            run_id,
            "evidence-curated",
            {"revision_id": revision_id, "evidence_ids": evidence_ids},
        )
        return curated_packet

    def begin_revision_update(self, run_id: str, revision_id: str, *, parent_revision_id: str) -> dict[str, object]:
        intake = self.repository.load_revision_model(run_id, "intake", parent_revision_id, IntakeDraft, approved=True)
        evidence = self.repository.load_revision_model(run_id, "evidence", parent_revision_id, EvidencePacket, approved=True)
        self.save_intake_draft(run_id, revision_id, intake, parent_revision_id=parent_revision_id)
        self.save_evidence_draft(
            run_id,
            revision_id,
            evidence.model_copy(update={"revision_id": revision_id}),
            parent_revision_id=parent_revision_id,
        )
        self.repository.append_event(
            run_id,
            "revision-update-started",
            {"revision_id": revision_id, "parent_revision_id": parent_revision_id},
        )
        return {
            "revision_id": revision_id,
            "parent_revision_id": parent_revision_id,
            "copied_sections": ["intake", "evidence"],
        }

    def approve_revision(self, run_id: str, revision_id: str, assumptions: AssumptionSummary) -> RunRecord:
        intake = self.repository.load_revision_model(run_id, "intake", revision_id, IntakeDraft, approved=False)
        evidence = self.repository.load_revision_model(run_id, "evidence", revision_id, EvidencePacket, approved=False)

        self.repository.write_revision_json(run_id, "intake", revision_id, intake.model_dump(mode="json"), approved=True)
        self.repository.write_revision_json(
            run_id,
            "evidence",
            revision_id,
            evidence.model_dump(mode="json"),
            approved=True,
        )
        self.repository.write_revision_json(
            run_id,
            "assumptions",
            revision_id,
            assumptions.model_dump(mode="json"),
            approved=True,
        )

        run = self.repository.load_run_record(run_id)
        run.current_revision_id = revision_id
        self.repository.save_run_record(run)
        record = self._ensure_revision_record(run_id, revision_id).model_copy(
            update={"status": "approved", "approved_at": datetime.now(timezone.utc)}
        )
        self.repository.save_revision_record(run_id, record)
        self.repository.append_event(run_id, "revision-approved", {"revision_id": revision_id})
        return run

    def simulate_revision(self, run_id: str, revision_id: str, *, pack: Any) -> dict[str, object]:
        intake = self.repository.load_revision_model(run_id, "intake", revision_id, IntakeDraft, approved=True)
        assumptions = self.repository.load_revision_model(run_id, "assumptions", revision_id, AssumptionSummary, approved=True)
        evidence = self.repository.load_revision_model(run_id, "evidence", revision_id, EvidencePacket, approved=True)
        revision_record = self.repository.load_revision_record(run_id, revision_id)

        state = compile_belief_state(
            run_id=run_id,
            revision_id=revision_id,
            pack=pack,
            intake=intake,
            assumptions=assumptions,
            approved_evidence_ids=[item.evidence_id for item in evidence.items],
            approved_evidence_items=evidence.items,
        )
        self.repository.write_revision_json(run_id, "belief-state", revision_id, state.model_dump(mode="json"), approved=True)

        reuse_context: dict[str, object] | None = None
        parent_revision_id = revision_record.parent_revision_id
        if (
            parent_revision_id
            and self._artifact_exists(run_id, "belief-state", parent_revision_id, approved=True)
            and self._artifact_exists(run_id, "simulation", parent_revision_id, approved=True)
        ):
            parent_state = self.repository.load_revision_model(
                run_id,
                "belief-state",
                parent_revision_id,
                BeliefState,
                approved=True,
            )
            parent_simulation_path = self.repository.run_dir(run_id) / "simulation" / f"{parent_revision_id}.approved.json"
            parent_simulation = json.loads(parent_simulation_path.read_text(encoding="utf-8"))
            reuse_context = {
                "source_revision_id": parent_revision_id,
                "compatibility": compare_belief_states(parent_state, state, tolerances={}),
                "simulation": parent_simulation,
            }

        engine = SimulationEngine(pack, default_objective_profile())
        result = engine.run(state, reuse_context=reuse_context)
        self.repository.write_revision_json(run_id, "simulation", revision_id, result, approved=True)

        self.generate_report(
            run_id,
            revision_id,
            simulation=result,
            evidence_count=len(evidence.items),
            unsupported_count=len(assumptions.summary),
        )
        record = self._ensure_revision_record(run_id, revision_id).model_copy(
            update={"status": "simulated", "simulated_at": datetime.now(timezone.utc)}
        )
        self.repository.save_revision_record(run_id, record)
        self.repository.append_event(run_id, "simulation-complete", {"revision_id": revision_id})
        return result

    def generate_report(
        self,
        run_id: str,
        revision_id: str,
        *,
        simulation: dict[str, object],
        evidence_count: int,
        unsupported_count: int,
    ) -> str:
        content = render_report(
            revision_id=revision_id,
            simulation=simulation,
            evidence_count=evidence_count,
            unsupported_count=unsupported_count,
        )
        self.repository.write_revision_markdown(run_id, revision_id, "report.md", content)
        self.repository.append_event(run_id, "report-generated", {"revision_id": revision_id})
        return content

    def draft_conversation_turn(
        self,
        run_id: str,
        revision_id: str,
        *,
        candidate_path: Path | None = None,
    ) -> ConversationTurn:
        self.repository.load_run_record(run_id)
        available_sections = self._available_sections(run_id, revision_id)

        if self._artifact_exists(run_id, "simulation", revision_id, approved=True):
            summary = self.summarize_revision(run_id, revision_id)
            summary_payload = summary.model_dump(mode="json")
            return ConversationTurn(
                run_id=run_id,
                revision_id=revision_id,
                stage="report",
                headline="Review simulation report",
                user_message="Simulation is complete. Review the top branches and decide whether to update the revision.",
                recommended_command="forecast-harness begin-revision-update",
                available_sections=available_sections,
                actions=[
                    self._adapter_action(
                        "forecast-harness begin-revision-update",
                        "Start revision update",
                        "Create a child revision from the current approved revision and continue the conversation loop.",
                    )
                ],
                context={**summary_payload, "revision_summary": summary_payload},
            )

        if self._artifact_exists(run_id, "assumptions", revision_id, approved=True):
            evidence = self.repository.load_revision_model(run_id, "evidence", revision_id, EvidencePacket, approved=True)
            assumptions = self.repository.load_revision_model(
                run_id, "assumptions", revision_id, AssumptionSummary, approved=True
            )
            readiness_context = {
                "revision_id": revision_id,
                "evidence_item_count": len(evidence.items),
                "assumption_count": len(assumptions.summary),
            }
            return ConversationTurn(
                run_id=run_id,
                revision_id=revision_id,
                stage="simulation",
                headline="Ready to simulate",
                user_message="Revision is approved and ready to simulate.",
                recommended_command="forecast-harness simulate",
                available_sections=available_sections,
                actions=[
                    self._adapter_action(
                        "forecast-harness simulate",
                        "Run simulation",
                        "Execute deterministic search for the approved revision.",
                    )
                ],
                context={**readiness_context, "simulation_readiness": readiness_context},
            )

        if self._artifact_exists(run_id, "evidence", revision_id, approved=False):
            packet = self.draft_approval_packet(run_id, revision_id)
            packet_payload = packet.model_dump(mode="json")
            return ConversationTurn(
                run_id=run_id,
                revision_id=revision_id,
                stage="approval",
                headline="Review approval packet",
                user_message="Evidence draft is ready. Review warnings, assumptions, and evidence summary before approval.",
                recommended_command="forecast-harness approve-revision",
                available_sections=available_sections,
                actions=[
                    self._adapter_action(
                        "forecast-harness approve-revision",
                        "Approve revision",
                        "Freeze the intake, evidence, and assumptions for simulation.",
                    )
                ],
                context={**packet_payload, "approval_packet": packet_payload},
            )

        if self._artifact_exists(run_id, "intake", revision_id, approved=False):
            guidance = self.draft_intake_guidance(run_id, revision_id)
            guidance_payload = guidance.model_dump(mode="json")
            context: dict[str, object] = {**guidance_payload, "intake_guidance": guidance_payload}
            actions: list[AdapterAction] = []
            recommended_command = "forecast-harness draft-evidence-packet"

            if self.corpus_registry is not None:
                pack = self._pack_for_run(run_id)
                retrieval_plan = self.draft_retrieval_plan(run_id, revision_id, pack=pack)
                ingestion_plan = self.draft_ingestion_plan(run_id, revision_id, pack=pack)
                retrieval_payload = retrieval_plan.model_dump(mode="json")
                ingestion_payload = ingestion_plan.model_dump(mode="json")
                context["retrieval_plan"] = retrieval_payload
                context["ingestion_plan"] = ingestion_payload

                recommendations: list[IngestionRecommendation] = []
                if candidate_path is not None and candidate_path.exists() and candidate_path.is_dir():
                    recommendations = self.recommend_ingestion_files(
                        run_id,
                        revision_id,
                        pack=pack,
                        path=candidate_path,
                    )
                if recommendations:
                    context["ingestion_recommendations"] = [
                        item.model_dump(mode="json") for item in recommendations
                    ]
                    recommended_command = "forecast-harness batch-ingest-recommended"
                    actions.append(
                        self._adapter_action(
                            "forecast-harness batch-ingest-recommended",
                            "Batch ingest recommended files",
                            "Ingest the highest-priority local files that cover missing evidence categories.",
                            required_options=["corpus_db", "candidate_path"],
                        )
                    )

            actions.append(
                self._adapter_action(
                    "forecast-harness draft-evidence-packet",
                    "Draft evidence packet",
                    "Draft a grouped evidence packet from the current corpus and manifest-driven retrieval plan.",
                    required_options=["corpus_db"] if self.corpus_registry is not None else [],
                )
            )
            return ConversationTurn(
                run_id=run_id,
                revision_id=revision_id,
                stage="evidence",
                headline="Draft evidence packet",
                user_message="Intake draft saved. Review suggested entities and follow-up questions, then draft evidence.",
                recommended_command=recommended_command,
                available_sections=available_sections,
                actions=actions,
                context=context,
            )

        return ConversationTurn(
            run_id=run_id,
            revision_id=revision_id,
            stage="intake",
            headline="Draft intake",
            user_message="Revision is ready for intake. Capture the event framing and core entities first.",
            recommended_command="forecast-harness save-intake-draft",
            available_sections=available_sections,
            actions=[
                self._adapter_action(
                    "forecast-harness save-intake-draft",
                    "Save intake draft",
                    "Capture the normalized intake fields for the revision.",
                )
            ],
            context={},
        )

    def summarize_run(self, run_id: str) -> RunSummary:
        run = self.repository.load_run_record(run_id)
        revisions = self.repository.list_revision_records(run_id)
        return RunSummary(
            run_id=run.run_id,
            domain_pack=run.domain_pack,
            current_revision_id=run.current_revision_id,
            revisions=[record.model_dump(mode="json") for record in revisions],
        )

    def summarize_revision(self, run_id: str, revision_id: str) -> RevisionSummary:
        record = self.repository.load_revision_record(run_id, revision_id)
        run_dir = self.repository.run_dir(run_id)
        available_sections = self._available_sections(run_id, revision_id)
        evidence_item_count = 0
        assumption_count = 0
        top_branches: list[dict[str, object]] = []
        scenario_families: list[dict[str, object]] = []

        evidence_path = run_dir / "evidence" / f"{revision_id}.draft.json"
        if not evidence_path.exists():
            evidence_path = run_dir / "evidence" / f"{revision_id}.approved.json"
        if evidence_path.exists():
            evidence = EvidencePacket.model_validate_json(evidence_path.read_text(encoding="utf-8"))
            evidence_item_count = len(evidence.items)

        assumptions_path = run_dir / "assumptions" / f"{revision_id}.approved.json"
        if assumptions_path.exists():
            assumptions = AssumptionSummary.model_validate_json(assumptions_path.read_text(encoding="utf-8"))
            assumption_count = len(assumptions.summary)

        simulation_path = run_dir / "simulation" / f"{revision_id}.approved.json"
        if simulation_path.exists():
            simulation = json.loads(simulation_path.read_text(encoding="utf-8"))
            branches = simulation.get("branches", [])
            if isinstance(branches, list):
                top_branches = summarize_top_branches(branches)
                scenario_families = summarize_scenario_families(branches)

        return RevisionSummary(
            revision_id=record.revision_id,
            status=record.status,
            parent_revision_id=record.parent_revision_id,
            evidence_item_count=evidence_item_count,
            assumption_count=assumption_count,
            top_branches=top_branches,
            scenario_families=scenario_families,
            available_sections=available_sections,
        )
