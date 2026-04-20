from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.objectives import default_objective_profile
from forecasting_harness.simulation.engine import SimulationEngine
from forecasting_harness.workflow.models import AssumptionSummary, EvidencePacket, IntakeDraft, RunRecord
from forecasting_harness.workflow.compiler import compile_belief_state
from forecasting_harness.workflow.reporting import render_report


class WorkflowService:
    def __init__(self, repository: RunRepository) -> None:
        self.repository = repository

    def start_run(self, run_id: str, domain_pack: str) -> RunRecord:
        run = RunRecord(run_id=run_id, domain_pack=domain_pack, created_at=datetime.now(timezone.utc))
        self.repository.init_run(run)
        self.repository.append_event(run_id, "run-started", {"run_id": run_id})
        return run

    def save_intake_draft(self, run_id: str, revision_id: str, intake: IntakeDraft) -> None:
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
