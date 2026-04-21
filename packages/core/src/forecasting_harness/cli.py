import json
from datetime import datetime, timezone
from pathlib import Path

import typer
from typer import Typer

from forecasting_harness import __version__
from forecasting_harness.artifacts import RunRepository
from forecasting_harness.evolution.models import DomainBlueprint
from forecasting_harness.evolution.service import DomainEvolutionService
from forecasting_harness.evolution.storage import EvolutionStorage
from forecasting_harness.domain.generic_event import GenericEventPack
from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack
from forecasting_harness.domain.registry import build_default_registry
from forecasting_harness.knowledge import load_builtin_replay_cases, summarize_builtin_replay_corpus
from forecasting_harness.models import BeliefState, ObjectiveProfile
from forecasting_harness.objectives import default_objective_profile
from forecasting_harness.replay import ReplayCase, run_replay_suite, summarize_calibration
from forecasting_harness.retrieval import CorpusRegistry, detect_source_type, ingest_file
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


def _service(root: Path, *, corpus_db: Path | None = None) -> WorkflowService:
    corpus_registry = CorpusRegistry(corpus_db) if corpus_db is not None else None
    return WorkflowService(RunRepository(root), corpus_registry=corpus_registry)


def _evolution_service(workspace_root: Path) -> DomainEvolutionService:
    return DomainEvolutionService(
        evolution_storage=EvolutionStorage(workspace_root / "knowledge" / "evolution"),
        manifest_root=workspace_root / "knowledge" / "domains",
    )


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


def _parse_tags(values: list[str] | None) -> dict[str, str]:
    tags: dict[str, str] = {}
    for value in values or []:
        if "=" not in value:
            raise typer.BadParameter("tags must be key=value", param_hint="tag")
        key, raw_value = value.split("=", 1)
        if not key:
            raise typer.BadParameter("tag key cannot be empty", param_hint="tag")
        tags[key] = raw_value
    return tags


def _parse_scalar(raw_value: str) -> object:
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        return raw_value
    if isinstance(parsed, (str, int, float, bool)) or parsed is None:
        return parsed
    return raw_value


def _parse_pack_fields(values: list[str] | None) -> dict[str, object]:
    pack_fields: dict[str, object] = {}
    for value in values or []:
        if "=" not in value:
            raise typer.BadParameter("pack fields must be key=value", param_hint="pack_field")
        key, raw_value = value.split("=", 1)
        if not key:
            raise typer.BadParameter("pack field key cannot be empty", param_hint="pack_field")
        pack_fields[key] = _parse_scalar(raw_value)
    return pack_fields


def _require_flag(value: str | None, *, param_hint: str) -> str:
    if value is None or not value.strip():
        raise typer.BadParameter("required when --input is not provided", param_hint=param_hint)
    return value


def _intake_from_flags(
    *,
    event_framing: str | None,
    focus_entities: list[str] | None,
    current_development: str | None,
    current_stage: str | None,
    time_horizon: str | None,
    known_constraints: list[str] | None,
    known_unknowns: list[str] | None,
    suggested_entities: list[str] | None,
    pack_fields: list[str] | None,
) -> IntakeDraft:
    if not focus_entities:
        raise typer.BadParameter("required when --input is not provided", param_hint="focus_entity")
    return IntakeDraft(
        event_framing=_require_flag(event_framing, param_hint="event_framing"),
        focus_entities=focus_entities,
        current_development=_require_flag(current_development, param_hint="current_development"),
        current_stage=_require_flag(current_stage, param_hint="current_stage"),
        time_horizon=_require_flag(time_horizon, param_hint="time_horizon"),
        known_constraints=known_constraints or [],
        known_unknowns=known_unknowns or [],
        suggested_entities=suggested_entities or [],
        pack_fields=_parse_pack_fields(pack_fields),
    )


def _assumptions_from_flags(
    *,
    assumptions: list[str] | None,
    suggested_actors: list[str] | None,
    objective_profile_name: str | None,
) -> AssumptionSummary:
    return AssumptionSummary(
        summary=assumptions or [],
        suggested_actors=suggested_actors or [],
        objective_profile_name=objective_profile_name or "balanced",
    )


def _register_ingested_document(registry: CorpusRegistry, path: Path, *, source_id: str | None, title: str | None, published_at: str | None, tags: dict[str, str]) -> dict[str, object]:
    document = ingest_file(
        path,
        source_id=source_id,
        title=title,
        published_at=published_at,
        tags=tags,
    )
    actual_source_id = registry.register_document(
        source_id=document.source_id,
        title=document.title,
        source_type=document.source_type,
        path=document.path,
        published_at=document.published_at,
        tags=document.tags,
        chunks=[
            {
                "chunk_id": chunk.chunk_id,
                "location": chunk.location,
                "content": chunk.content,
            }
            for chunk in document.chunks
        ],
    )
    return {
        "source_id": actual_source_id,
        "title": document.title,
        "source_type": document.source_type,
        "path": document.path,
        "chunk_count": len(document.chunks),
    }


@app.command("list-domain-packs")
def list_domain_packs() -> None:
    print(json.dumps(_registry().list_slugs()))


@app.command("record-domain-suggestion")
def record_domain_suggestion_command(
    workspace_root: Path = typer.Option(Path(".")),
    domain_pack: str = typer.Option(...),
    text: str = typer.Option(...),
    category: str | None = typer.Option(None),
    target: str | None = typer.Option(None),
    term: list[str] | None = typer.Option(None),
) -> None:
    suggestion = _evolution_service(workspace_root).record_suggestion(
        domain_pack,
        text=text,
        category=category,
        target=target,
        terms=term,
    )
    print(suggestion.model_dump_json())


@app.command("analyze-domain-weakness")
def analyze_domain_weakness_command(
    workspace_root: Path = typer.Option(Path(".")),
    domain_pack: str = typer.Option(...),
) -> None:
    service = _evolution_service(workspace_root)
    cases = service._load_replay_cases(domain_pack)
    if cases:
        replay_result = run_replay_suite(cases)
    else:
        replay_result = run_replay_suite([])
    print(service.analyze_domain_weakness(domain_pack, replay_result=replay_result).model_dump_json())


@app.command("run-domain-evolution")
def run_domain_evolution_command(
    workspace_root: Path = typer.Option(Path(".")),
    domain_pack: str = typer.Option(...),
    no_branch: bool = typer.Option(False),
) -> None:
    summary = _evolution_service(workspace_root).run_domain_evolution(domain_pack, create_branch=not no_branch)
    print(json.dumps(summary))


@app.command("summarize-domain-evolution")
def summarize_domain_evolution_command(
    workspace_root: Path = typer.Option(Path(".")),
    domain_pack: str = typer.Option(...),
) -> None:
    print(json.dumps(_evolution_service(workspace_root).summarize_domain_evolution(domain_pack)))


@app.command("synthesize-domain")
def synthesize_domain_command(
    workspace_root: Path = typer.Option(Path(".")),
    input: Path = typer.Option(...),
    no_branch: bool = typer.Option(False),
) -> None:
    blueprint = DomainBlueprint.model_validate_json(input.read_text(encoding="utf-8"))
    print(json.dumps(_evolution_service(workspace_root).synthesize_domain(blueprint, create_branch=not no_branch)))


@app.command("ingest-file")
def ingest_file_command(
    corpus_db: Path = typer.Option(...),
    path: Path = typer.Option(...),
    source_id: str | None = typer.Option(None),
    title: str | None = typer.Option(None),
    published_at: str | None = typer.Option(None),
    tag: list[str] | None = typer.Option(None),
) -> None:
    registry = CorpusRegistry(corpus_db)
    payload = _register_ingested_document(
        registry,
        path,
        source_id=source_id,
        title=title,
        published_at=published_at,
        tags=_parse_tags(tag),
    )
    print(json.dumps(payload))


@app.command("ingest-directory")
def ingest_directory_command(
    corpus_db: Path = typer.Option(...),
    path: Path = typer.Option(...),
    published_at: str | None = typer.Option(None),
    tag: list[str] | None = typer.Option(None),
) -> None:
    registry = CorpusRegistry(corpus_db)
    tags = _parse_tags(tag)
    ingested = 0
    skipped = 0
    failed = 0
    for candidate in sorted(path.iterdir()):
        if not candidate.is_file():
            continue
        try:
            detect_source_type(candidate)
        except ValueError:
            skipped += 1
            continue
        try:
            _register_ingested_document(
                registry,
                candidate,
                source_id=None,
                title=None,
                published_at=published_at,
                tags=tags,
            )
            ingested += 1
        except Exception:
            failed += 1
    print(json.dumps({"ingested": ingested, "skipped": skipped, "failed": failed}))


@app.command("list-corpus-sources")
def list_corpus_sources(corpus_db: Path = typer.Option(...)) -> None:
    print(json.dumps(CorpusRegistry(corpus_db).list_documents()))


@app.command("run-replay-suite")
def run_replay_suite_command(
    input: Path = typer.Option(...),
) -> None:
    cases = [ReplayCase.model_validate(item) for item in json.loads(input.read_text(encoding="utf-8"))]
    print(run_replay_suite(cases).model_dump_json())


@app.command("run-builtin-replay-suite")
def run_builtin_replay_suite_command() -> None:
    print(run_replay_suite(load_builtin_replay_cases()).model_dump_json())


@app.command("summarize-builtin-replay-corpus")
def summarize_builtin_replay_corpus_command() -> None:
    print(summarize_builtin_replay_corpus().model_dump_json())


@app.command("summarize-replay-calibration")
def summarize_replay_calibration_command(
    input: Path | None = typer.Option(None),
) -> None:
    cases = load_builtin_replay_cases() if input is None else [ReplayCase.model_validate(item) for item in json.loads(input.read_text(encoding="utf-8"))]
    summary = summarize_calibration(run_replay_suite(cases))
    print(summary.model_dump_json())


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
    input: Path | None = typer.Option(None),
    parent_revision_id: str | None = typer.Option(None),
    event_framing: str | None = typer.Option(None),
    focus_entity: list[str] | None = typer.Option(None),
    current_development: str | None = typer.Option(None),
    current_stage: str | None = typer.Option(None),
    time_horizon: str | None = typer.Option(None),
    known_constraint: list[str] | None = typer.Option(None),
    known_unknown: list[str] | None = typer.Option(None),
    suggested_entity: list[str] | None = typer.Option(None),
    pack_field: list[str] | None = typer.Option(None),
) -> None:
    if input is not None:
        payload = IntakeDraft.model_validate_json(input.read_text(encoding="utf-8"))
    else:
        payload = _intake_from_flags(
            event_framing=event_framing,
            focus_entities=focus_entity,
            current_development=current_development,
            current_stage=current_stage,
            time_horizon=time_horizon,
            known_constraints=known_constraint,
            known_unknowns=known_unknown,
            suggested_entities=suggested_entity,
            pack_fields=pack_field,
        )
    _service(root).save_intake_draft(
        run_id=run_id,
        revision_id=revision_id,
        intake=payload,
        parent_revision_id=parent_revision_id,
    )
    print(f"saved intake {revision_id}")


@app.command("save-evidence-draft")
def save_evidence_draft(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
    input: Path = typer.Option(...),
    parent_revision_id: str | None = typer.Option(None),
) -> None:
    payload = EvidencePacket.model_validate_json(input.read_text(encoding="utf-8"))
    _service(root).save_evidence_draft(
        run_id=run_id,
        revision_id=revision_id,
        packet=payload,
        parent_revision_id=parent_revision_id,
    )
    print(f"saved evidence {revision_id}")


@app.command("draft-intake-guidance")
def draft_intake_guidance(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
) -> None:
    print(_service(root).draft_intake_guidance(run_id, revision_id).model_dump_json())


@app.command("draft-evidence-packet")
def draft_evidence_packet_command(
    root: Path = typer.Option(Path(".forecast")),
    corpus_db: Path = typer.Option(...),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
    query_text: str | None = typer.Option(None),
) -> None:
    repo = RunRepository(root)
    pack = _load_pack_for_run(repo, run_id)
    service = WorkflowService(repo, corpus_registry=CorpusRegistry(corpus_db))
    packet = service.draft_evidence_packet(run_id, revision_id, pack=pack, query_text=query_text)
    print(packet.model_dump_json())


@app.command("draft-retrieval-plan")
def draft_retrieval_plan_command(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
    query_text: str | None = typer.Option(None),
) -> None:
    repo = RunRepository(root)
    pack = _load_pack_for_run(repo, run_id)
    service = WorkflowService(repo)
    print(service.draft_retrieval_plan(run_id, revision_id, pack=pack, query_text=query_text).model_dump_json())


@app.command("draft-ingestion-plan")
def draft_ingestion_plan_command(
    root: Path = typer.Option(Path(".forecast")),
    corpus_db: Path = typer.Option(...),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
) -> None:
    repo = RunRepository(root)
    pack = _load_pack_for_run(repo, run_id)
    service = WorkflowService(repo, corpus_registry=CorpusRegistry(corpus_db))
    print(service.draft_ingestion_plan(run_id, revision_id, pack=pack).model_dump_json())


@app.command("recommend-ingestion-files")
def recommend_ingestion_files_command(
    root: Path = typer.Option(Path(".forecast")),
    corpus_db: Path = typer.Option(...),
    path: Path = typer.Option(...),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
) -> None:
    repo = RunRepository(root)
    pack = _load_pack_for_run(repo, run_id)
    service = WorkflowService(repo, corpus_registry=CorpusRegistry(corpus_db))
    recommendations = service.recommend_ingestion_files(run_id, revision_id, pack=pack, path=path)
    print(json.dumps([item.model_dump(mode="json") for item in recommendations]))


@app.command("batch-ingest-recommended")
def batch_ingest_recommended_command(
    root: Path = typer.Option(Path(".forecast")),
    corpus_db: Path = typer.Option(...),
    path: Path = typer.Option(...),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
    max_files: int = typer.Option(5),
) -> None:
    repo = RunRepository(root)
    pack = _load_pack_for_run(repo, run_id)
    service = WorkflowService(repo, corpus_registry=CorpusRegistry(corpus_db))
    result = service.batch_ingest_recommended_files(
        run_id,
        revision_id,
        pack=pack,
        path=path,
        max_files=max_files,
    )
    print(result.model_dump_json())


@app.command("draft-approval-packet")
def draft_approval_packet(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
) -> None:
    print(_service(root).draft_approval_packet(run_id, revision_id).model_dump_json())


@app.command("draft-conversation-turn")
def draft_conversation_turn(
    root: Path = typer.Option(Path(".forecast")),
    corpus_db: Path | None = typer.Option(None),
    candidate_path: Path | None = typer.Option(None),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
) -> None:
    print(
        _service(root, corpus_db=corpus_db)
        .draft_conversation_turn(run_id, revision_id, candidate_path=candidate_path)
        .model_dump_json()
    )


@app.command("curate-evidence-draft")
def curate_evidence_draft(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
    keep_evidence_id: list[str] | None = typer.Option(None),
) -> None:
    if not keep_evidence_id:
        raise typer.BadParameter("at least one evidence id is required", param_hint="keep_evidence_id")
    print(_service(root).curate_evidence_draft(run_id, revision_id, keep_evidence_id).model_dump_json())


@app.command("approve-revision")
def approve_revision(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
    input: Path | None = typer.Option(None),
    assumption: list[str] | None = typer.Option(None),
    suggested_actor: list[str] | None = typer.Option(None),
    objective_profile_name: str | None = typer.Option(None),
) -> None:
    if input is not None:
        payload = AssumptionSummary.model_validate_json(input.read_text(encoding="utf-8"))
    else:
        payload = _assumptions_from_flags(
            assumptions=assumption,
            suggested_actors=suggested_actor,
            objective_profile_name=objective_profile_name,
        )
    _service(root).approve_revision(run_id=run_id, revision_id=revision_id, assumptions=payload)
    print(f"approved {revision_id}")


@app.command("begin-revision-update")
def begin_revision_update(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    parent_revision_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
) -> None:
    print(
        json.dumps(
            _service(root).begin_revision_update(
                run_id=run_id,
                revision_id=revision_id,
                parent_revision_id=parent_revision_id,
            )
        )
    )


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


@app.command("summarize-run")
def summarize_run(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
) -> None:
    print(_service(root).summarize_run(run_id).model_dump_json())


@app.command("summarize-revision")
def summarize_revision(
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option(...),
) -> None:
    print(_service(root).summarize_revision(run_id, revision_id).model_dump_json())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
