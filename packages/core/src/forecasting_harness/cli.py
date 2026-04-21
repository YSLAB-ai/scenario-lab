import json
from datetime import datetime, timezone
from pathlib import Path

import typer
from typer import Typer

from forecasting_harness import __version__
from forecasting_harness.artifacts import RunRepository
from forecasting_harness.domain.generic_event import GenericEventPack
from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack
from forecasting_harness.domain.registry import build_default_registry
from forecasting_harness.models import BeliefState, ObjectiveProfile
from forecasting_harness.objectives import default_objective_profile
from forecasting_harness.retrieval import CorpusRegistry
from forecasting_harness.simulation.engine import SimulationEngine
from forecasting_harness.workflow.models import AssumptionSummary, EvidencePacket, IntakeDraft, RunRecord
from forecasting_harness.workflow.service import WorkflowService


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


def _registry():
    return build_default_registry()


def _pack_for_slug(domain_pack: str) -> GenericEventPack | InterstateCrisisPack:
    try:
        return _registry().resolve(domain_pack)
    except KeyError as exc:
        raise typer.BadParameter(str(exc), param_hint="domain_pack") from exc


def _service(root: Path) -> WorkflowService:
    return WorkflowService(RunRepository(root))


def _repair_run_record(repo: RunRepository, run_id: str, domain_pack: str) -> None:
    run_dir = repo.run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "events.jsonl").touch(exist_ok=True)
    repo.save_run_record(
        RunRecord(
            run_id=run_id,
            domain_pack=domain_pack,
            created_at=datetime.now(timezone.utc),
        )
    )
    repo.append_event(run_id, "run-started", {"run_id": run_id})


def _ensure_demo_run_record(root: Path, repo: RunRepository, domain_pack: str) -> None:
    run_id = "demo-run"
    try:
        existing_run = repo.load_run_record(run_id)
    except FileNotFoundError:
        if repo.run_dir(run_id).exists():
            _repair_run_record(repo, run_id=run_id, domain_pack=domain_pack)
        else:
            _service(root).start_run(run_id=run_id, domain_pack=domain_pack)
        return

    (repo.run_dir(run_id) / "events.jsonl").touch(exist_ok=True)
    if existing_run.domain_pack != domain_pack:
        repo.save_run_record(existing_run.model_copy(update={"domain_pack": domain_pack}))


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


def _write_standard_outputs(
    repo: RunRepository,
    run_id: str,
    pack: GenericEventPack | InterstateCrisisPack,
    result: dict[str, object],
) -> None:
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
    return _pack_for_slug(repo.load_run_record(run_id).domain_pack)


@app.command("list-domain-packs")
def list_domain_packs() -> None:
    print(json.dumps(_registry().list_slugs()))


@app.command("demo-run")
def demo_run(root: Path = typer.Option(Path(".forecast"))) -> None:
    repo = RunRepository(root)
    pack = GenericEventPack()
    state = _initial_state("demo-run", pack)
    objective_profile = _objective_profile_for_pack(pack)
    engine = SimulationEngine(pack, objective_profile)
    result = engine.run(state)
    _ensure_demo_run_record(root, repo, pack.slug())
    repo.save_belief_state("demo-run", state)
    _write_standard_outputs(repo, "demo-run", pack, result)
    print("demo-run complete")


@app.command("start-run")
def start_run(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    domain_pack: str = typer.Option(...),
) -> None:
    pack = _pack_for_slug(domain_pack)
    _service(root).start_run(run_id=run_id, domain_pack=pack.slug())
    print(f"started {run_id}")


@app.command("save-intake-draft")
def save_intake_draft(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
    input: Path = typer.Option(...),
) -> None:
    payload = IntakeDraft.model_validate_json(input.read_text(encoding="utf-8"))
    _service(root).save_intake_draft(run_id=run_id, revision_id=revision_id, intake=payload)
    print(f"saved intake {revision_id}")


@app.command("save-evidence-draft")
def save_evidence_draft(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
    input: Path = typer.Option(...),
) -> None:
    payload = EvidencePacket.model_validate_json(input.read_text(encoding="utf-8"))
    _service(root).save_evidence_draft(run_id=run_id, revision_id=revision_id, packet=payload)
    print(f"saved evidence {revision_id}")


@app.command("draft-evidence-packet")
def draft_evidence_packet_command(
    root: Path = typer.Option(Path(".forecast")),
    corpus_db: Path = typer.Option(...),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
    query_text: str = typer.Option(...),
) -> None:
    repo = RunRepository(root)
    pack = _load_pack_for_run(repo, run_id)
    service = WorkflowService(repo, corpus_registry=CorpusRegistry(corpus_db))
    packet = service.draft_evidence_packet(run_id, revision_id, pack=pack, query_text=query_text)
    print(packet.model_dump_json())


@app.command("approve-revision")
def approve_revision(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
    input: Path = typer.Option(...),
) -> None:
    payload = AssumptionSummary.model_validate_json(input.read_text(encoding="utf-8"))
    _service(root).approve_revision(run_id=run_id, revision_id=revision_id, assumptions=payload)
    print(f"approved {revision_id}")


@app.command("simulate")
def simulate(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
) -> None:
    repo = RunRepository(root)
    pack = _load_pack_for_run(repo, run_id)
    result = _service(root).simulate_revision(run_id=run_id, revision_id=revision_id, pack=pack)
    print(json.dumps(result))


@app.command("generate-report")
def generate_report(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
) -> None:
    repo = RunRepository(root)
    simulation = json.loads(
        (repo.run_dir(run_id) / "simulation" / f"{revision_id}.approved.json").read_text(encoding="utf-8")
    )
    evidence = repo.load_revision_model(run_id, "evidence", revision_id, EvidencePacket, approved=True)
    assumptions = repo.load_revision_model(run_id, "assumptions", revision_id, AssumptionSummary, approved=True)
    _service(root).generate_report(
        run_id=run_id,
        revision_id=revision_id,
        simulation=simulation,
        evidence_count=len(evidence.items),
        unsupported_count=len(assumptions.summary),
    )
    print(f"reported {revision_id}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
