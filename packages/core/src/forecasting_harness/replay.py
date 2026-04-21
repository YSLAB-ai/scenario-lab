from __future__ import annotations

import tempfile
from pathlib import Path

from pydantic import BaseModel, Field

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.domain.registry import build_default_registry
from forecasting_harness.models import BeliefState
from forecasting_harness.retrieval import CorpusRegistry
from forecasting_harness.workflow.models import AssumptionSummary, IntakeDraft
from forecasting_harness.workflow.service import WorkflowService


class ReplayCase(BaseModel):
    run_id: str
    domain_pack: str
    intake: IntakeDraft
    assumptions: AssumptionSummary
    documents: dict[str, str] = Field(default_factory=dict)
    expected_top_branch: str | None = None
    expected_root_strategy: str | None = None
    expected_evidence_sources: list[str] = Field(default_factory=list)
    expected_inferred_fields: list[str] = Field(default_factory=list)


class ReplayCaseResult(BaseModel):
    run_id: str
    domain_pack: str
    top_branch: str | None = None
    expected_top_branch: str | None = None
    top_branch_match: bool | None = None
    root_strategy: str | None = None
    expected_root_strategy: str | None = None
    root_strategy_match: bool | None = None
    evidence_sources: list[str] = Field(default_factory=list)
    expected_evidence_sources: list[str] = Field(default_factory=list)
    evidence_source_match: bool | None = None
    inferred_fields: list[str] = Field(default_factory=list)
    expected_inferred_fields: list[str] = Field(default_factory=list)
    inferred_field_coverage: float = 0.0
    node_count: int = 0
    transposition_hits: int = 0


class ReplaySuiteResult(BaseModel):
    case_count: int
    top_branch_accuracy: float
    root_strategy_accuracy: float
    evidence_source_accuracy: float
    average_inferred_field_coverage: float
    domain_breakdown: dict[str, dict[str, float | int]] = Field(default_factory=dict)
    results: list[ReplayCaseResult] = Field(default_factory=list)


def _safe_accuracy(values: list[bool | None]) -> float:
    observed = [value for value in values if value is not None]
    if not observed:
        return 0.0
    return round(sum(1 for value in observed if value) / len(observed), 3)


def _root_strategy_for_label(label: str | None) -> str | None:
    if not label:
        return None
    return label.split(" (", 1)[0].strip() or None


def _run_single_case(case: ReplayCase, workspace_root: Path) -> ReplayCaseResult:
    registry = build_default_registry()
    pack = registry.resolve(case.domain_pack)
    root = workspace_root / ".forecast"
    corpus_db = workspace_root / "corpus.db"
    docs_dir = workspace_root / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)

    service = WorkflowService(RunRepository(root), corpus_registry=CorpusRegistry(corpus_db), domain_registry=registry)
    service.start_run(case.run_id, case.domain_pack)
    service.save_intake_draft(case.run_id, "r1", case.intake)
    for filename, content in case.documents.items():
        (docs_dir / filename).write_text(content, encoding="utf-8")

    service.batch_ingest_recommended_files(case.run_id, "r1", pack=pack, path=docs_dir, max_files=max(1, len(case.documents)))
    packet = service.draft_evidence_packet(case.run_id, "r1", pack=pack)
    service.approve_revision(case.run_id, "r1", case.assumptions)
    simulation = service.simulate_revision(case.run_id, "r1", pack=pack)
    state = service.repository.load_revision_model(case.run_id, "belief-state", "r1", BeliefState, approved=True)

    top_branch = None
    branches = simulation.get("branches", [])
    if isinstance(branches, list) and branches and isinstance(branches[0], dict):
        top_branch = branches[0].get("label")
        if not isinstance(top_branch, str):
            top_branch = None
    root_strategy = _root_strategy_for_label(top_branch)

    evidence_sources = sorted(item.source_id for item in packet.items)
    inferred_fields = sorted(
        field_name for field_name, field in state.fields.items() if field.status == "inferred"
    )

    if case.expected_inferred_fields:
        covered = sum(1 for field_name in case.expected_inferred_fields if state.fields[field_name].status == "inferred")
        inferred_field_coverage = round(covered / len(case.expected_inferred_fields), 3)
    else:
        inferred_field_coverage = 0.0

    top_branch_match = None
    if case.expected_top_branch is not None:
        top_branch_match = top_branch == case.expected_top_branch

    root_strategy_match = None
    if case.expected_root_strategy is not None:
        root_strategy_match = root_strategy == case.expected_root_strategy

    evidence_source_match = None
    if case.expected_evidence_sources:
        evidence_source_match = sorted(case.expected_evidence_sources) == evidence_sources

    return ReplayCaseResult(
        run_id=case.run_id,
        domain_pack=case.domain_pack,
        top_branch=top_branch,
        expected_top_branch=case.expected_top_branch,
        top_branch_match=top_branch_match,
        root_strategy=root_strategy,
        expected_root_strategy=case.expected_root_strategy,
        root_strategy_match=root_strategy_match,
        evidence_sources=evidence_sources,
        expected_evidence_sources=sorted(case.expected_evidence_sources),
        evidence_source_match=evidence_source_match,
        inferred_fields=inferred_fields,
        expected_inferred_fields=sorted(case.expected_inferred_fields),
        inferred_field_coverage=inferred_field_coverage,
        node_count=int(simulation.get("node_count", 0)),
        transposition_hits=int(simulation.get("transposition_hits", 0)),
    )


def run_replay_suite(cases: list[ReplayCase], *, workspace_root: Path | None = None) -> ReplaySuiteResult:
    base_root = Path(workspace_root) if workspace_root is not None else Path(tempfile.mkdtemp(prefix="forecast-replay-"))
    base_root.mkdir(parents=True, exist_ok=True)
    results: list[ReplayCaseResult] = []
    for index, case in enumerate(cases, start=1):
        case_root = base_root / f"{index:02d}-{case.run_id}"
        case_root.mkdir(parents=True, exist_ok=True)
        results.append(_run_single_case(case, case_root))

    domain_breakdown: dict[str, dict[str, float | int]] = {}
    for domain_pack in sorted({result.domain_pack for result in results}):
        domain_results = [result for result in results if result.domain_pack == domain_pack]
        domain_breakdown[domain_pack] = {
            "count": len(domain_results),
            "top_branch_accuracy": _safe_accuracy([result.top_branch_match for result in domain_results]),
            "root_strategy_accuracy": _safe_accuracy([result.root_strategy_match for result in domain_results]),
            "evidence_source_accuracy": _safe_accuracy([result.evidence_source_match for result in domain_results]),
            "average_inferred_field_coverage": round(
                sum(result.inferred_field_coverage for result in domain_results) / len(domain_results),
                3,
            )
            if domain_results
            else 0.0,
        }

    return ReplaySuiteResult(
        case_count=len(results),
        top_branch_accuracy=_safe_accuracy([result.top_branch_match for result in results]),
        root_strategy_accuracy=_safe_accuracy([result.root_strategy_match for result in results]),
        evidence_source_accuracy=_safe_accuracy([result.evidence_source_match for result in results]),
        average_inferred_field_coverage=round(
            sum(result.inferred_field_coverage for result in results) / len(results), 3
        )
        if results
        else 0.0,
        domain_breakdown=domain_breakdown,
        results=results,
    )
