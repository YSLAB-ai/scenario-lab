import json
from pathlib import Path
from datetime import datetime, timezone

import pytest
from pydantic import BaseModel

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.models import BeliefState
from forecasting_harness.workflow.models import RunRecord


class RevisionPayload(BaseModel):
    value: int


def test_run_repository_persists_belief_state(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    state = BeliefState(
        run_id="run-1",
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[],
        fields={},
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch="2026-W16",
        horizon="2026-W20",
    )

    repository.save_belief_state("run-1", state)
    loaded = repository.load_belief_state("run-1")

    assert loaded.run_id == "run-1"


def test_run_repository_rejects_mismatched_belief_state_run_id(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    state = BeliefState(
        run_id="run-2",
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[],
        fields={},
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch="2026-W16",
        horizon="2026-W20",
    )

    with pytest.raises(ValueError, match="run_id"):
        repository.save_belief_state("run-1", state)


def test_run_repository_rejects_path_traversal_in_run_id(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")

    with pytest.raises(ValueError, match="path traversal"):
        repository.run_dir("../escape")


def test_run_repository_rejects_path_traversal_in_artifact_name(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")

    with pytest.raises(ValueError, match="path traversal"):
        repository.write_markdown("run-1", "../escape.md", "content")


def test_run_repository_rejects_reserved_canonical_artifact_name(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")

    with pytest.raises(ValueError, match="reserved"):
        repository.write_json("run-1", "belief-state.json", {"ok": True})


def test_run_repository_initializes_runs_and_persists_run_records(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    run = RunRecord(
        run_id="run-1",
        domain_pack="interstate-crisis",
        created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
    )

    repository.init_run(run)
    repository.save_run_record(run)

    run_dir = repository.run_dir("run-1")
    assert (run_dir / "run.json").exists()
    assert (run_dir / "events.jsonl").exists()
    assert repository.load_run_record("run-1") == run


def test_run_repository_writes_revision_snapshots_and_loads_models(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    repository.init_run(
        RunRecord(
            run_id="run-1",
            domain_pack="interstate-crisis",
            created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
        )
    )

    path = repository.write_revision_json(
        "run-1",
        "intake",
        "r1",
        RevisionPayload(value=1).model_dump(mode="json"),
        approved=True,
    )

    assert path.name == "r1.approved.json"
    assert repository.load_revision_model("run-1", "intake", "r1", RevisionPayload, approved=True) == RevisionPayload(
        value=1
    )

    with pytest.raises(FileExistsError):
        repository.write_revision_json(
            "run-1",
            "intake",
            "r1",
            RevisionPayload(value=2).model_dump(mode="json"),
            approved=True,
        )


def test_run_repository_writes_revision_markdown_and_appends_events(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    repository.init_run(
        RunRecord(
            run_id="run-1",
            domain_pack="interstate-crisis",
            created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
        )
    )

    report_path = repository.write_revision_markdown("run-1", "r1", "report.md", "# Report\n")
    repository.append_event("run-1", "run-started", {"revision_id": "r1"})
    repository.append_event("run-1", "run-updated", {"revision_id": "r2"})

    event_lines = (repository.run_dir("run-1") / "events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    events = [json.loads(line) for line in event_lines]

    assert report_path.name == "r1.report.md"
    assert [event["event_type"] for event in events] == ["run-started", "run-updated"]
    assert [event["payload"]["revision_id"] for event in events] == ["r1", "r2"]


@pytest.mark.parametrize(
    ("operation", "args", "kwargs"),
    [
        ("write_revision_json", ("run-1", "intake", "r1", {"value": 1}), {"approved": True}),
        ("write_revision_markdown", ("run-1", "r1", "report.md", "# Report\n"), {}),
        ("append_event", ("run-1", "run-started", {"revision_id": "r1"}), {}),
    ],
)
def test_run_repository_rejects_writes_for_uninitialized_runs(
    tmp_path: Path,
    operation: str,
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> None:
    repository = RunRepository(tmp_path / ".forecast")

    with pytest.raises(FileNotFoundError, match="run.json"):
        getattr(repository, operation)(*args, **kwargs)

    assert not repository.run_dir("run-1").exists()


def test_run_repository_rejects_path_traversal_in_revision_inputs(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    run = RunRecord(
        run_id="run-1",
        domain_pack="interstate-crisis",
        created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
    )
    repository.init_run(run)

    with pytest.raises(ValueError, match="path traversal"):
        repository.write_revision_json("../escape", "intake", "r1", {"value": 1}, approved=True)

    with pytest.raises(ValueError, match="path traversal"):
        repository.write_revision_json("run-1", "../escape", "r1", {"value": 1}, approved=True)

    with pytest.raises(ValueError, match="path traversal"):
        repository.write_revision_json("run-1", "intake", "../escape", {"value": 1}, approved=True)

    with pytest.raises(ValueError, match="path traversal"):
        repository.write_revision_markdown("run-1", "../escape", "report.md", "# Report\n")
