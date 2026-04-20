from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

import pytest

from forecasting_harness.workflow.models import AssumptionSummary, EvidencePacket, IntakeDraft, RunRecord
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
        current_phase="intake",
        time_horizon="2026-Q2",
        known_constraints=["sanctions"],
        known_unknowns=["timing"],
        suggested_actors=["country-c"],
    )


def _make_evidence(revision_id: str = "rev-1") -> EvidencePacket:
    return EvidencePacket(revision_id=revision_id)


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
