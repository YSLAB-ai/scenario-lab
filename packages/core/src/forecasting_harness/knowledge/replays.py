from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from forecasting_harness.replay import ReplayCase


def _replay_root() -> Path:
    return Path(__file__).resolve().parents[5] / "knowledge" / "replays"


class ReplayCorpusSummary(BaseModel):
    case_count: int
    anchored_case_count: int = 0
    domains: list[str] = Field(default_factory=list)
    domain_counts: dict[str, int] = Field(default_factory=dict)
    files: dict[str, int] = Field(default_factory=dict)


class ReplayCatalogEntry(BaseModel):
    run_id: str
    domain_pack: str
    case_title: str | None = None
    time_anchor: str | None = None
    expected_top_branch: str | None = None
    expected_root_strategy: str | None = None
    source_count: int = 0


def load_builtin_replay_cases(*, domain_packs: list[str] | None = None) -> list[ReplayCase]:
    replay_root = _replay_root()
    if not replay_root.exists():
        raise FileNotFoundError(replay_root)

    allowed = set(domain_packs or [])
    cases: list[ReplayCase] = []
    for replay_path in sorted(replay_root.glob("*.json")):
        payload = json.loads(replay_path.read_text(encoding="utf-8"))
        for item in payload:
            case = ReplayCase.model_validate(item)
            if allowed and case.domain_pack not in allowed:
                continue
            cases.append(case)
    return cases


def summarize_builtin_replay_corpus() -> ReplayCorpusSummary:
    replay_root = _replay_root()
    if not replay_root.exists():
        raise FileNotFoundError(replay_root)

    domain_counts: dict[str, int] = {}
    file_counts: dict[str, int] = {}
    case_count = 0
    anchored_case_count = 0
    for replay_path in sorted(replay_root.glob("*.json")):
        payload = json.loads(replay_path.read_text(encoding="utf-8"))
        file_counts[replay_path.name] = len(payload)
        case_count += len(payload)
        for item in payload:
            case = ReplayCase.model_validate(item)
            domain_pack = case.domain_pack
            domain_counts[domain_pack] = domain_counts.get(domain_pack, 0) + 1
            if case.sources:
                anchored_case_count += 1

    return ReplayCorpusSummary(
        case_count=case_count,
        anchored_case_count=anchored_case_count,
        domains=sorted(domain_counts),
        domain_counts=domain_counts,
        files=file_counts,
    )


def list_builtin_replay_cases() -> list[ReplayCatalogEntry]:
    return [
        ReplayCatalogEntry(
            run_id=case.run_id,
            domain_pack=case.domain_pack,
            case_title=case.case_title,
            time_anchor=case.time_anchor,
            expected_top_branch=case.expected_top_branch,
            expected_root_strategy=case.expected_root_strategy,
            source_count=len(case.sources),
        )
        for case in load_builtin_replay_cases()
    ]
