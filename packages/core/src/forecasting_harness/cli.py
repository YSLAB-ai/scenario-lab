from pathlib import Path

import typer
from typer import Typer

from forecasting_harness import __version__
from forecasting_harness.artifacts import RunRepository
from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.domain.generic_event import GenericEventPack
from forecasting_harness.models import BeliefState, ObjectiveProfile
from forecasting_harness.objectives import default_objective_profile
from forecasting_harness.simulation.engine import SimulationEngine


app = Typer(no_args_is_help=True)


@app.callback()
def main_command() -> None:
    return None


@app.command()
def version() -> None:
    print(__version__)


def _objective_profile_for_pack(pack: GenericEventPack) -> ObjectiveProfile:
    default_profile = getattr(pack, "default_objective_profile", None)
    if callable(default_profile):
        return default_profile()
    return default_objective_profile()


def _top_branch_label(result: dict[str, object]) -> str:
    branches = result.get("branches", [])
    if branches:
        top_branch = branches[0]
        if isinstance(top_branch, dict):
            label = top_branch.get("label")
            if isinstance(label, str) and label:
                return label
    return "No branches generated"


@app.command("demo-run")
def demo_run(root: Path = typer.Option(Path(".forecast"))) -> None:
    repo = RunRepository(root)
    state = BeliefState(
        run_id="demo-run",
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
    pack = GenericEventPack()
    objective_profile = _objective_profile_for_pack(pack)
    engine = SimulationEngine(pack, objective_profile)
    result = engine.run(state)
    repo.save_belief_state("demo-run", state)
    repo.write_json("demo-run", "tree-summary.json", result)
    repo.write_markdown(
        "demo-run",
        "report.md",
        f"# Scenario Report\n\n- Top branch: {_top_branch_label(result)}\n",
    )
    repo.write_markdown(
        "demo-run",
        "workbench.md",
        f"# Analyst Workbench\n\n- Objective profile: {objective_profile.name}\n",
    )
    print("demo-run complete")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
