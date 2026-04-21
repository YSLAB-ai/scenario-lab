from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.domain.base import DomainPack
from forecasting_harness.domain.registry import DomainPackRegistry, build_default_registry
from forecasting_harness.objectives import default_objective_profile
from forecasting_harness.retrieval import CorpusRegistry, RetrievalQuery, SearchEngine
from forecasting_harness.simulation.engine import SimulationEngine
from forecasting_harness.workflow.evidence import draft_evidence_packet as build_evidence_packet
from forecasting_harness.workflow.models import AssumptionSummary, EvidencePacket, IntakeDraft, RunRecord
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

    def start_run(self, run_id: str, domain_pack: str) -> RunRecord:
        run = RunRecord(run_id=run_id, domain_pack=domain_pack, created_at=datetime.now(timezone.utc))
        self.repository.init_run(run)
        self.repository.append_event(run_id, "run-started", {"run_id": run_id})
        return run

    def save_intake_draft(self, run_id: str, revision_id: str, intake: IntakeDraft) -> None:
        pack = self._pack_for_run(run_id)
        _validate_pack_fields(pack, intake)
        validation_errors = pack.validate_intake(intake)
        if validation_errors:
            raise ValueError("; ".join(validation_errors))
        self.repository.write_revision_json(run_id, "intake", revision_id, intake.model_dump(mode="json"), approved=False)
        self.repository.append_event(run_id, "intake-drafted", {"revision_id": revision_id})

    def save_evidence_draft(self, run_id: str, revision_id: str, packet: EvidencePacket) -> None:
        if packet.revision_id != revision_id:
            raise ValueError(f"revision_id mismatch: expected {revision_id!r}, got {packet.revision_id!r}")
        self.repository.write_revision_json(
            run_id,
            "evidence",
            revision_id,
            packet.model_dump(mode="json"),
            approved=False,
        )
        self.repository.append_event(run_id, "evidence-drafted", {"revision_id": revision_id})

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
