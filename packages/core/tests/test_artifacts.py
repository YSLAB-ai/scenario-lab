from pathlib import Path

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
