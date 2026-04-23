from __future__ import annotations

from functools import lru_cache
import tempfile
from pathlib import Path

from pydantic import BaseModel, Field

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.domain.registry import build_default_registry
from forecasting_harness.models import BeliefState
from forecasting_harness.retrieval import CorpusRegistry
from forecasting_harness.workflow.models import AssumptionSummary, IntakeDraft


class ReplaySource(BaseModel):
    title: str
    publisher: str
    url: str


class ReplayCase(BaseModel):
    run_id: str
    domain_pack: str
    case_title: str | None = None
    time_anchor: str | None = None
    historical_outcome: str | None = None
    sources: list[ReplaySource] = Field(default_factory=list)
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
    case_title: str | None = None
    time_anchor: str | None = None
    historical_outcome: str | None = None
    source_count: int = 0
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
    top_branch_confidence_signal: float = 0.0
    node_count: int = 0
    transposition_hits: int = 0


class ConfidenceCalibrationBucket(BaseModel):
    bucket_id: str
    label: str
    lower_bound: float
    upper_bound: float
    case_count: int = 0
    observed_accuracy: float = 0.0
    calibrated_confidence: float = 0.0
    fallback_used: bool = False


class DomainConfidenceCalibration(BaseModel):
    domain_pack: str
    case_count: int = 0
    baseline_accuracy: float = 0.0
    buckets: list[ConfidenceCalibrationBucket] = Field(default_factory=list)


class CalibrationAttentionItem(BaseModel):
    run_id: str
    domain_pack: str
    case_title: str | None = None
    mismatch_types: list[str] = Field(default_factory=list)
    expected_top_branch: str | None = None
    actual_top_branch: str | None = None
    expected_root_strategy: str | None = None
    actual_root_strategy: str | None = None
    expected_evidence_sources: list[str] = Field(default_factory=list)
    actual_evidence_sources: list[str] = Field(default_factory=list)
    missing_inferred_fields: list[str] = Field(default_factory=list)
    inferred_field_coverage: float = 0.0


class ReplaySuiteResult(BaseModel):
    case_count: int
    top_branch_accuracy: float
    root_strategy_accuracy: float
    evidence_source_accuracy: float
    average_inferred_field_coverage: float
    domain_breakdown: dict[str, dict[str, float | int]] = Field(default_factory=dict)
    results: list[ReplayCaseResult] = Field(default_factory=list)


class CalibrationSummary(BaseModel):
    case_count: int
    historically_anchored_case_count: int = 0
    overall_top_branch_accuracy: float
    overall_root_strategy_accuracy: float
    overall_evidence_source_accuracy: float
    average_inferred_field_coverage: float
    failure_type_counts: dict[str, int] = Field(default_factory=dict)
    attention_items: list[CalibrationAttentionItem] = Field(default_factory=list)
    strongest_domains: list[str] = Field(default_factory=list)
    weakest_domains: list[str] = Field(default_factory=list)
    domains_needing_attention: list[str] = Field(default_factory=list)
    domain_breakdown: dict[str, dict[str, float | int]] = Field(default_factory=dict)
    domain_confidence_profiles: dict[str, DomainConfidenceCalibration] = Field(default_factory=dict)


_CONFIDENCE_BUCKET_SPECS: tuple[tuple[str, str, float, float], ...] = (
    ("low", "Low", 0.0, 0.34),
    ("medium", "Medium", 0.34, 0.67),
    ("high", "High", 0.67, 1.0),
)


def _safe_accuracy(values: list[bool | None]) -> float:
    observed = [value for value in values if value is not None]
    if not observed:
        return 0.0
    return round(sum(1 for value in observed if value) / len(observed), 3)


def _root_strategy_for_label(label: str | None) -> str | None:
    if not label:
        return None
    return label.split(" (", 1)[0].strip() or None


def _increment(mapping: dict[str, int], key: str) -> None:
    mapping[key] = mapping.get(key, 0) + 1


def _bucket_id_for_signal(confidence_signal: float) -> str:
    bounded_signal = max(0.0, min(1.0, float(confidence_signal)))
    for bucket_id, _, lower_bound, upper_bound in _CONFIDENCE_BUCKET_SPECS:
        if bucket_id == "high":
            if lower_bound <= bounded_signal <= upper_bound:
                return bucket_id
            continue
        if lower_bound <= bounded_signal < upper_bound:
            return bucket_id
    return "high"


def _smoothed_confidence(match_count: int, case_count: int) -> float:
    return round((match_count + 1) / (case_count + 2), 3) if case_count >= 0 else 0.0


def _build_domain_confidence_profile(
    domain_pack: str,
    domain_results: list[ReplayCaseResult],
) -> DomainConfidenceCalibration:
    scored_results = [result for result in domain_results if result.top_branch_match is not None]
    match_count = sum(1 for result in scored_results if result.top_branch_match)
    baseline_accuracy = _smoothed_confidence(match_count, len(scored_results))
    buckets: list[ConfidenceCalibrationBucket] = []

    for bucket_id, label, lower_bound, upper_bound in _CONFIDENCE_BUCKET_SPECS:
        bucket_results = [
            result for result in scored_results if _bucket_id_for_signal(result.top_branch_confidence_signal) == bucket_id
        ]
        bucket_match_count = sum(1 for result in bucket_results if result.top_branch_match)
        observed_accuracy = _safe_accuracy([result.top_branch_match for result in bucket_results])
        fallback_used = len(bucket_results) == 0
        calibrated_confidence = (
            baseline_accuracy if fallback_used else _smoothed_confidence(bucket_match_count, len(bucket_results))
        )
        buckets.append(
            ConfidenceCalibrationBucket(
                bucket_id=bucket_id,
                label=label,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                case_count=len(bucket_results),
                observed_accuracy=observed_accuracy,
                calibrated_confidence=calibrated_confidence,
                fallback_used=fallback_used,
            )
        )

    return DomainConfidenceCalibration(
        domain_pack=domain_pack,
        case_count=len(scored_results),
        baseline_accuracy=baseline_accuracy,
        buckets=buckets,
    )


def calibrate_confidence_signal(
    confidence_signal: float,
    profile: DomainConfidenceCalibration | None,
) -> dict[str, object]:
    bounded_signal = round(max(0.0, min(1.0, float(confidence_signal))), 3)
    bucket_id = _bucket_id_for_signal(bounded_signal)
    default_bucket_id, default_label, default_lower_bound, default_upper_bound = next(
        spec for spec in _CONFIDENCE_BUCKET_SPECS if spec[0] == bucket_id
    )
    if profile is None:
        return {
            "confidence_bucket": "fallback",
            "confidence_bucket_label": "Fallback baseline",
            "calibrated_confidence": bounded_signal,
            "calibration_case_count": 0,
            "calibration_observed_accuracy": 0.0,
            "calibration_fallback_used": True,
        }

    bucket = next((item for item in profile.buckets if item.bucket_id == bucket_id), None)
    if bucket is None:
        return {
            "confidence_bucket": "fallback",
            "confidence_bucket_label": "Fallback baseline",
            "calibrated_confidence": profile.baseline_accuracy,
            "calibration_case_count": 0,
            "calibration_observed_accuracy": 0.0,
            "calibration_fallback_used": True,
        }

    if bucket.fallback_used:
        return {
            "confidence_bucket": "fallback",
            "confidence_bucket_label": "Fallback baseline",
            "calibrated_confidence": profile.baseline_accuracy,
            "calibration_case_count": 0,
            "calibration_observed_accuracy": 0.0,
            "calibration_fallback_used": True,
        }

    return {
        "confidence_bucket": bucket.bucket_id,
        "confidence_bucket_label": bucket.label,
        "calibrated_confidence": bucket.calibrated_confidence,
        "calibration_case_count": bucket.case_count,
        "calibration_observed_accuracy": bucket.observed_accuracy,
        "calibration_fallback_used": bucket.fallback_used,
    }


def apply_confidence_calibration(
    simulation: dict[str, object],
    *,
    domain_pack: str,
    profile: DomainConfidenceCalibration | None,
) -> dict[str, object]:
    branches = simulation.get("branches", [])
    if not isinstance(branches, list):
        return simulation

    calibrated_branches: list[dict[str, object]] = []
    for branch in branches:
        if not isinstance(branch, dict):
            calibrated_branches.append(branch)
            continue
        calibrated_branch = dict(branch)
        confidence_signal = float(calibrated_branch.get("confidence_signal", 0.0) or 0.0)
        calibrated_branch.update(calibrate_confidence_signal(confidence_signal, profile))
        calibrated_branches.append(calibrated_branch)

    updated = dict(simulation)
    updated["branches"] = calibrated_branches
    updated["confidence_calibration"] = {
        "domain_pack": domain_pack,
        "profile": profile.model_dump(mode="json") if profile is not None else None,
    }
    return updated


@lru_cache(maxsize=32)
def load_builtin_domain_confidence_profile(domain_pack: str) -> DomainConfidenceCalibration | None:
    from forecasting_harness.knowledge.replays import load_builtin_replay_cases

    cases = load_builtin_replay_cases(domain_packs=[domain_pack])
    if not cases:
        return None

    summary = summarize_calibration(run_replay_suite(cases))
    return summary.domain_confidence_profiles.get(domain_pack)


def _run_single_case(
    case: ReplayCase,
    workspace_root: Path,
    *,
    attach_calibration: bool = False,
) -> ReplayCaseResult:
    from forecasting_harness.workflow.service import WorkflowService

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
    simulation = service.simulate_revision(case.run_id, "r1", pack=pack, attach_calibration=attach_calibration)
    state = service.repository.load_revision_model(case.run_id, "belief-state", "r1", BeliefState, approved=True)

    top_branch = None
    top_branch_confidence_signal = 0.0
    branches = simulation.get("branches", [])
    if isinstance(branches, list) and branches and isinstance(branches[0], dict):
        top_branch = branches[0].get("label")
        top_branch_confidence_signal = float(branches[0].get("confidence_signal", 0.0) or 0.0)
        if not isinstance(top_branch, str):
            top_branch = None
    root_strategy = _root_strategy_for_label(top_branch)

    evidence_sources = sorted(item.source_id for item in packet.items)
    inferred_fields = sorted(
        field_name for field_name, field in state.fields.items() if field.status == "inferred"
    )

    if case.expected_inferred_fields:
        covered = sum(
            1
            for field_name in case.expected_inferred_fields
            if field_name in state.fields and state.fields[field_name].status == "inferred"
        )
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
        case_title=case.case_title,
        time_anchor=case.time_anchor,
        historical_outcome=case.historical_outcome,
        source_count=len(case.sources),
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
        top_branch_confidence_signal=top_branch_confidence_signal,
        node_count=int(simulation.get("node_count", 0)),
        transposition_hits=int(simulation.get("transposition_hits", 0)),
    )


def run_replay_suite(
    cases: list[ReplayCase],
    *,
    workspace_root: Path | None = None,
    attach_calibration: bool = False,
) -> ReplaySuiteResult:
    base_root = Path(workspace_root) if workspace_root is not None else Path(tempfile.mkdtemp(prefix="forecast-replay-"))
    base_root.mkdir(parents=True, exist_ok=True)
    results: list[ReplayCaseResult] = []
    for index, case in enumerate(cases, start=1):
        case_root = base_root / f"{index:02d}-{case.run_id}"
        case_root.mkdir(parents=True, exist_ok=True)
        results.append(_run_single_case(case, case_root, attach_calibration=attach_calibration))

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


def _domain_composite_score(metrics: dict[str, float | int]) -> float:
    return round(
        float(metrics.get("top_branch_accuracy", 0.0)) * 0.35
        + float(metrics.get("root_strategy_accuracy", 0.0)) * 0.4
        + float(metrics.get("evidence_source_accuracy", 0.0)) * 0.1
        + float(metrics.get("average_inferred_field_coverage", 0.0)) * 0.15,
        3,
    )


def summarize_calibration(result: ReplaySuiteResult, *, attention_threshold: float = 0.85) -> CalibrationSummary:
    enriched_breakdown: dict[str, dict[str, float | int]] = {}
    domain_confidence_profiles: dict[str, DomainConfidenceCalibration] = {}
    weakest_domains: list[tuple[float, str]] = []
    strongest_domains: list[tuple[float, str]] = []
    domains_needing_attention: list[str] = []
    failure_type_counts: dict[str, int] = {}
    attention_items: list[CalibrationAttentionItem] = []

    for domain_pack, metrics in sorted(result.domain_breakdown.items()):
        enriched_metrics = dict(metrics)
        composite_score = _domain_composite_score(enriched_metrics)
        enriched_metrics["composite_score"] = composite_score
        enriched_breakdown[domain_pack] = enriched_metrics
        domain_confidence_profiles[domain_pack] = _build_domain_confidence_profile(
            domain_pack,
            [replay_result for replay_result in result.results if replay_result.domain_pack == domain_pack],
        )
        weakest_domains.append((composite_score, domain_pack))
        strongest_domains.append((composite_score, domain_pack))

        if (
            float(metrics.get("top_branch_accuracy", 0.0)) < attention_threshold
            or float(metrics.get("root_strategy_accuracy", 0.0)) < attention_threshold
            or float(metrics.get("average_inferred_field_coverage", 0.0)) < attention_threshold
        ):
            domains_needing_attention.append(domain_pack)

    for replay_result in result.results:
        mismatch_types: list[str] = []
        if replay_result.top_branch_match is False:
            mismatch_types.append("top_branch_mismatch")
        if replay_result.root_strategy_match is False:
            mismatch_types.append("root_strategy_mismatch")
        if replay_result.evidence_source_match is False:
            mismatch_types.append("evidence_source_mismatch")
        missing_inferred_fields = sorted(
            set(replay_result.expected_inferred_fields).difference(replay_result.inferred_fields)
        )
        if missing_inferred_fields:
            mismatch_types.append("inferred_field_gap")
        if not mismatch_types:
            continue

        for mismatch in mismatch_types:
            _increment(failure_type_counts, mismatch)

        attention_items.append(
            CalibrationAttentionItem(
                run_id=replay_result.run_id,
                domain_pack=replay_result.domain_pack,
                case_title=replay_result.case_title,
                mismatch_types=mismatch_types,
                expected_top_branch=replay_result.expected_top_branch,
                actual_top_branch=replay_result.top_branch,
                expected_root_strategy=replay_result.expected_root_strategy,
                actual_root_strategy=replay_result.root_strategy,
                expected_evidence_sources=replay_result.expected_evidence_sources,
                actual_evidence_sources=replay_result.evidence_sources,
                missing_inferred_fields=missing_inferred_fields,
                inferred_field_coverage=replay_result.inferred_field_coverage,
            )
        )

    strongest = [domain for _, domain in sorted(strongest_domains, key=lambda item: (-item[0], item[1]))]
    weakest = [domain for _, domain in sorted(weakest_domains, key=lambda item: (item[0], item[1]))]

    return CalibrationSummary(
        case_count=result.case_count,
        historically_anchored_case_count=sum(1 for case in result.results if case.source_count > 0),
        overall_top_branch_accuracy=result.top_branch_accuracy,
        overall_root_strategy_accuracy=result.root_strategy_accuracy,
        overall_evidence_source_accuracy=result.evidence_source_accuracy,
        average_inferred_field_coverage=result.average_inferred_field_coverage,
        failure_type_counts=failure_type_counts,
        attention_items=attention_items,
        strongest_domains=strongest,
        weakest_domains=weakest,
        domains_needing_attention=sorted(domains_needing_attention),
        domain_breakdown=enriched_breakdown,
        domain_confidence_profiles=domain_confidence_profiles,
    )
