from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pytest

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack
from forecasting_harness.workflow.models import (
    AssumptionSummary,
    EvidencePacket,
    EvidencePacketItem,
    IntakeDraft,
    RunRecord,
)
from forecasting_harness.workflow.service import WorkflowService


class _FrozenDateTime:
    @classmethod
    def now(cls, tz: timezone | None = None) -> datetime:
        assert tz == timezone.utc
        return datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc)


@dataclass
class _FakeRepository:
    initialized_runs: list[RunRecord] = field(default_factory=list)
    saved_runs: list[RunRecord] = field(default_factory=list)
    written_revision_json: list[tuple[str, str, str, object, bool]] = field(default_factory=list)
    loaded_revision_models: list[tuple[str, str, str, type, bool]] = field(default_factory=list)
    appended_events: list[tuple[str, str, dict[str, object]]] = field(default_factory=list)
    run_record: RunRecord | None = None
    revision_payloads: dict[tuple[str, str, str, bool], object] = field(default_factory=dict)

    def init_run(self, run: RunRecord) -> None:
        self.initialized_runs.append(run)

    def save_run_record(self, run: RunRecord) -> None:
        self.saved_runs.append(run)
        self.run_record = run

    def load_run_record(self, run_id: str) -> RunRecord:
        assert self.run_record is not None
        assert self.run_record.run_id == run_id
        return self.run_record

    def write_revision_json(
        self,
        run_id: str,
        section: str,
        revision_id: str,
        payload: object,
        *,
        approved: bool,
    ) -> None:
        self.written_revision_json.append((run_id, section, revision_id, payload, approved))

    def load_revision_model(
        self,
        run_id: str,
        section: str,
        revision_id: str,
        model_type: type,
        *,
        approved: bool,
    ):
        self.loaded_revision_models.append((run_id, section, revision_id, model_type, approved))
        payload = self.revision_payloads[(run_id, section, revision_id, approved)]
        return model_type.model_validate(payload)

    def append_event(self, run_id: str, event_type: str, payload: dict[str, object]) -> None:
        self.appended_events.append((run_id, event_type, payload))


def _make_run(run_id: str = "run-1") -> RunRecord:
    return RunRecord(
        run_id=run_id,
        domain_pack="interstate-crisis",
        created_at=datetime(2026, 4, 20, 11, 59, tzinfo=timezone.utc),
    )


def _make_intake() -> IntakeDraft:
    return IntakeDraft(
        event_framing="A policy shift is underway.",
        primary_actors=["country-a", "country-b"],
        trigger="policy change",
        current_phase="trigger",
        time_horizon="2026-Q2",
        known_constraints=["sanctions"],
        known_unknowns=["timing"],
        suggested_actors=["country-c"],
    )


def _make_evidence(revision_id: str = "rev-1") -> EvidencePacket:
    return EvidencePacket(revision_id=revision_id)


def _make_revision_inputs(revision_id: str, *, evidence_count: int = 1) -> tuple[IntakeDraft, EvidencePacket, AssumptionSummary]:
    intake = _make_intake()
    evidence = EvidencePacket(
        revision_id=revision_id,
        items=[
            EvidencePacketItem(
                evidence_id=f"{revision_id}-ev-{index}",
                source_id=f"source-{index}",
                source_title=f"Source {index}",
                reason="supports the forecast",
            )
            for index in range(evidence_count)
        ],
    )
    assumptions = AssumptionSummary(summary=["assumption-1"], suggested_actors=["country-c"])
    return intake, evidence, assumptions


def test_start_run_initializes_the_run_and_records_a_started_event(monkeypatch: pytest.MonkeyPatch) -> None:
    from forecasting_harness.workflow import service as workflow_service

    monkeypatch.setattr(workflow_service, "datetime", _FrozenDateTime)
    repository = _FakeRepository()
    service = WorkflowService(repository)

    run = service.start_run("run-1", "interstate-crisis")

    assert run == RunRecord(
        run_id="run-1",
        domain_pack="interstate-crisis",
        created_at=datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc),
    )
    assert repository.initialized_runs == [run]
    assert repository.appended_events == [("run-1", "run-started", {"run_id": "run-1"})]


def test_start_run_rejects_duplicate_run_ids_with_real_repository(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from forecasting_harness.workflow import service as workflow_service

    monkeypatch.setattr(workflow_service, "datetime", _FrozenDateTime)
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)

    first_run = service.start_run("run-1", "interstate-crisis")

    assert first_run.run_id == "run-1"

    with pytest.raises(FileExistsError):
        service.start_run("run-1", "interstate-crisis")

    loaded = repository.load_run_record("run-1")
    assert loaded == first_run


def test_save_intake_draft_writes_the_intake_snapshot_and_records_an_event() -> None:
    repository = _FakeRepository()
    service = WorkflowService(repository)
    intake = _make_intake()

    service.save_intake_draft("run-1", "rev-1", intake)

    assert repository.written_revision_json == [
        ("run-1", "intake", "rev-1", intake.model_dump(mode="json"), False)
    ]
    assert repository.appended_events == [("run-1", "intake-drafted", {"revision_id": "rev-1"})]


def test_save_evidence_draft_writes_the_evidence_snapshot_and_records_an_event() -> None:
    repository = _FakeRepository()
    service = WorkflowService(repository)
    packet = _make_evidence()

    service.save_evidence_draft("run-1", "rev-1", packet)

    assert repository.written_revision_json == [
        ("run-1", "evidence", "rev-1", packet.model_dump(mode="json"), False)
    ]
    assert repository.appended_events == [("run-1", "evidence-drafted", {"revision_id": "rev-1"})]


def test_save_evidence_draft_rejects_revision_id_mismatches() -> None:
    repository = _FakeRepository()
    service = WorkflowService(repository)
    packet = _make_evidence(revision_id="rev-2")

    with pytest.raises(ValueError, match="revision_id"):
        service.save_evidence_draft("run-1", "rev-1", packet)

    assert repository.written_revision_json == []
    assert repository.appended_events == []


def test_approve_revision_freezes_revision_artifacts_and_advances_the_run() -> None:
    repository = _FakeRepository(run_record=_make_run())
    intake = _make_intake()
    evidence = _make_evidence()
    assumptions = AssumptionSummary(summary=["assumption-1"], suggested_actors=["country-c"])
    repository.revision_payloads[("run-1", "intake", "rev-1", False)] = intake.model_dump(mode="json")
    repository.revision_payloads[("run-1", "evidence", "rev-1", False)] = evidence.model_dump(mode="json")
    service = WorkflowService(repository)

    run = service.approve_revision("run-1", "rev-1", assumptions)

    assert run.current_revision_id == "rev-1"
    assert repository.loaded_revision_models == [
        ("run-1", "intake", "rev-1", IntakeDraft, False),
        ("run-1", "evidence", "rev-1", EvidencePacket, False),
    ]
    assert repository.written_revision_json == [
        ("run-1", "intake", "rev-1", intake.model_dump(mode="json"), True),
        ("run-1", "evidence", "rev-1", evidence.model_dump(mode="json"), True),
        ("run-1", "assumptions", "rev-1", assumptions.model_dump(mode="json"), True),
    ]
    assert repository.saved_runs == [run]
    assert repository.appended_events == [("run-1", "revision-approved", {"revision_id": "rev-1"})]


def test_simulate_revision_writes_belief_state_summary_and_report(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake, evidence, assumptions = _make_revision_inputs("r1")

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)
    service.approve_revision("crisis-1", "r1", assumptions)

    result = service.simulate_revision("crisis-1", "r1", pack=pack)

    assert [branch["label"] for branch in result["branches"]] == [
        "Signal resolve",
        "Limited response",
        "Open negotiation",
    ]
    assert repository.run_dir("crisis-1").joinpath("belief-state", "r1.approved.json").exists()
    assert repository.run_dir("crisis-1").joinpath("simulation", "r1.approved.json").exists()
    report_path = repository.run_dir("crisis-1").joinpath("reports", "r1.report.md")
    assert report_path.exists()
    assert "# Scenario Report" in report_path.read_text(encoding="utf-8")
    assert "- Revision: r1" in report_path.read_text(encoding="utf-8")


def test_generate_report_writes_revision_specific_reports_and_credibility_note(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    service.start_run(run_id="crisis-1", domain_pack="interstate-crisis")

    first_report = service.generate_report(
        "crisis-1",
        "r1",
        simulation={
            "branches": [
                {"branch_id": "signal", "label": "Signal resolve", "score": 0.8},
                {"branch_id": "negotiation", "label": "Open negotiation", "score": 0.9},
            ]
        },
        evidence_count=0,
        unsupported_count=1,
    )
    second_report = service.generate_report(
        "crisis-1",
        "r2",
        simulation={"branches": []},
        evidence_count=2,
        unsupported_count=0,
    )

    report_dir = repository.run_dir("crisis-1") / "reports"
    assert report_dir.joinpath("r1.report.md").exists()
    assert report_dir.joinpath("r2.report.md").exists()
    assert first_report != second_report
    assert "low-credibility exploratory run" in first_report
    assert "low-credibility exploratory run" not in second_report


def test_revision_preserving_rerun_keeps_previous_report(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    intake_r1, evidence_r1, assumptions_r1 = _make_revision_inputs("r1")
    service.save_intake_draft("crisis-1", "r1", intake_r1)
    service.save_evidence_draft("crisis-1", "r1", evidence_r1)
    service.approve_revision("crisis-1", "r1", assumptions_r1)
    service.simulate_revision("crisis-1", "r1", pack=pack)

    intake_r2, evidence_r2, assumptions_r2 = _make_revision_inputs("r2", evidence_count=2)
    service.save_intake_draft("crisis-1", "r2", intake_r2)
    service.save_evidence_draft("crisis-1", "r2", evidence_r2)
    service.approve_revision("crisis-1", "r2", assumptions_r2)
    service.simulate_revision("crisis-1", "r2", pack=pack)

    report_dir = repository.run_dir("crisis-1") / "reports"
    assert report_dir.joinpath("r1.report.md").exists()
    assert report_dir.joinpath("r2.report.md").exists()
    assert repository.load_run_record("crisis-1").current_revision_id == "r2"
