import json
from pathlib import Path

import typer
from typer import Typer

from forecasting_harness import __version__
from forecasting_harness.artifacts import RunRepository
from forecasting_harness.domain.generic_event import GenericEventPack
from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack
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


def _pack_for_slug(domain_pack: str) -> GenericEventPack | InterstateCrisisPack:
    if domain_pack == "generic-event":
        return GenericEventPack()
    if domain_pack == "interstate-crisis":
        return InterstateCrisisPack()
    raise typer.BadParameter(
        f"unsupported domain pack: {domain_pack!r}",
        param_hint="domain_pack",
    )


def _initial_state(run_id: str, pack: GenericEventPack | InterstateCrisisPack) -> BeliefState:
    return BeliefState(
        run_id=run_id,
        interaction_model=pack.interaction_model(),
        actors=[],
        fields={},
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch="2026-W16",
        horizon="2026-W20",
    )


def _write_standard_outputs(repo: RunRepository, run_id: str, pack: GenericEventPack | InterstateCrisisPack, result: dict[str, object]) -> None:
    objective_profile = _objective_profile_for_pack(pack)
    repo.write_json(run_id, "tree-summary.json", result)
    repo.write_markdown(
        run_id,
        "report.md",
        f"# Scenario Report\n\n- Top branch: {_top_branch_label(result)}\n",
    )
    repo.write_markdown(
        run_id,
        "workbench.md",
        f"# Analyst Workbench\n\n- Objective profile: {objective_profile.name}\n",
    )


def _load_pack_for_run(repo: RunRepository, run_id: str) -> GenericEventPack | InterstateCrisisPack:
    run_file = repo.run_dir(run_id) / "run.json"
    if run_file.exists():
        metadata = json.loads(run_file.read_text(encoding="utf-8"))
        domain_pack = metadata.get("domain_pack")
        if isinstance(domain_pack, str):
            return _pack_for_slug(domain_pack)
    return GenericEventPack()


def _simulation_state(
    state: BeliefState,
    pack: GenericEventPack | InterstateCrisisPack,
) -> BeliefState:
    if isinstance(pack, InterstateCrisisPack):
        canonical_phases = pack.canonical_phases()
        if canonical_phases:
            object.__setattr__(state, "phase", canonical_phases[0])
    return state


@app.command("demo-run")
def demo_run(root: Path = typer.Option(Path(".forecast"))) -> None:
    repo = RunRepository(root)
    pack = GenericEventPack()
    state = _initial_state("demo-run", pack)
    objective_profile = _objective_profile_for_pack(pack)
    engine = SimulationEngine(pack, objective_profile)
    result = engine.run(state)
    repo.write_json("demo-run", "run.json", {"run_id": "demo-run", "domain_pack": pack.slug()})
    repo.save_belief_state("demo-run", state)
    _write_standard_outputs(repo, "demo-run", pack, result)
    print("demo-run complete")


@app.command("start-run")
def start_run(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    domain_pack: str = typer.Option(...),
) -> None:
    repo = RunRepository(root)
    pack = _pack_for_slug(domain_pack)
    state = _initial_state(run_id, pack)
    repo.write_json(run_id, "run.json", {"run_id": run_id, "domain_pack": pack.slug()})
    repo.save_belief_state(run_id, state)
    print(f"started {run_id}")


@app.command("simulate")
def simulate(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
) -> None:
    repo = RunRepository(root)
    pack = _load_pack_for_run(repo, run_id)
    state = _simulation_state(repo.load_belief_state(run_id), pack)
    objective_profile = _objective_profile_for_pack(pack)
    engine = SimulationEngine(pack, objective_profile)
    result = engine.run(state)
    _write_standard_outputs(repo, run_id, pack, result)
    print(json.dumps(result))


@app.command("generate-report")
def generate_report(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
) -> None:
    repo = RunRepository(root)
    pack = _load_pack_for_run(repo, run_id)
    result = json.loads((repo.run_dir(run_id) / "tree-summary.json").read_text(encoding="utf-8"))
    _write_standard_outputs(repo, run_id, pack, result)
    print(f"generated report for {run_id}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
