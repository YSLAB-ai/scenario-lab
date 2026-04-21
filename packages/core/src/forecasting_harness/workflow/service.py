from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.domain.base import DomainPack
from forecasting_harness.domain.registry import DomainPackRegistry, build_default_registry
from forecasting_harness.objectives import default_objective_profile
from forecasting_harness.query_api import summarize_top_branches
from forecasting_harness.retrieval import CorpusRegistry, RetrievalQuery, SearchEngine
from forecasting_harness.simulation.engine import SimulationEngine
from forecasting_harness.workflow.evidence import draft_evidence_packet as build_evidence_packet
from forecasting_harness.workflow.models import (
    ApprovalPacket,
    AssumptionSummary,
    EvidencePacket,
    IntakeDraft,
    IntakeGuidance,
    RevisionRecord,
    RevisionSummary,
    RunRecord,
    RunSummary,
)
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
        query_text: str,
        max_per_source: int = 2,
        max_total: int = 6,
    ) -> EvidencePacket:
        if self.corpus_registry is None:
            raise ValueError("corpus_registry is required for evidence drafting")

        intake = self.repository.load_revision_model(run_id, "intake", revision_id, IntakeDraft, approved=False)
        search_engine = SearchEngine(self.corpus_registry)
        hits = search_engine.search(
            RetrievalQuery(text=query_text, filters=pack.retrieval_filters(intake)),
            freshness_policy=pack.freshness_policy(),
        )
        packet = build_evidence_packet(revision_id, hits, max_per_source=max_per_source, max_total=max_total)
        self.save_evidence_draft(run_id, revision_id, packet)
        self.repository.append_event(
            run_id,
            "evidence-packet-drafted",
            {"revision_id": revision_id, "query_text": query_text},
        )
        return packet

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

        state = compile_belief_state(
            run_id=run_id,
            revision_id=revision_id,
            pack=pack,
            intake=intake,
            assumptions=assumptions,
            approved_evidence_ids=[item.evidence_id for item in evidence.items],
        )
        self.repository.write_revision_json(run_id, "belief-state", revision_id, state.model_dump(mode="json"), approved=True)

        engine = SimulationEngine(pack, default_objective_profile())
        result = engine.run(state)
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
        available_sections: list[str] = []
        evidence_item_count = 0
        assumption_count = 0
        top_branches: list[dict[str, object]] = []

        for section in ("intake", "evidence", "assumptions", "belief-state", "simulation"):
            draft_path = run_dir / section / f"{revision_id}.draft.json"
            approved_path = run_dir / section / f"{revision_id}.approved.json"
            if draft_path.exists() or approved_path.exists():
                available_sections.append(section)

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

        return RevisionSummary(
            revision_id=record.revision_id,
            status=record.status,
            parent_revision_id=record.parent_revision_id,
            evidence_item_count=evidence_item_count,
            assumption_count=assumption_count,
            top_branches=top_branches,
            available_sections=available_sections,
        )
