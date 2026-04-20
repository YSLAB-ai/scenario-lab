from pathlib import Path

import pytest

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.models import BeliefState


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
