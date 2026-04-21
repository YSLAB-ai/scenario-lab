from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from forecasting_harness.replay import ReplayCase


def _replay_root() -> Path:
    return Path(__file__).resolve().parents[5] / "knowledge" / "replays"


class ReplayCorpusSummary(BaseModel):
    case_count: int
    domains: list[str] = Field(default_factory=list)
    domain_counts: dict[str, int] = Field(default_factory=dict)
    files: dict[str, int] = Field(default_factory=dict)


def load_builtin_replay_cases() -> list[ReplayCase]:
    replay_root = _replay_root()
    if not replay_root.exists():
        raise FileNotFoundError(replay_root)

    cases: list[ReplayCase] = []
    for replay_path in sorted(replay_root.glob("*.json")):
        payload = json.loads(replay_path.read_text(encoding="utf-8"))
        cases.extend(ReplayCase.model_validate(item) for item in payload)
    return cases


def summarize_builtin_replay_corpus() -> ReplayCorpusSummary:
    replay_root = _replay_root()
    if not replay_root.exists():
        raise FileNotFoundError(replay_root)

    domain_counts: dict[str, int] = {}
    file_counts: dict[str, int] = {}
    case_count = 0
    for replay_path in sorted(replay_root.glob("*.json")):
        payload = json.loads(replay_path.read_text(encoding="utf-8"))
        file_counts[replay_path.name] = len(payload)
        case_count += len(payload)
        for item in payload:
            domain_pack = ReplayCase.model_validate(item).domain_pack
            domain_counts[domain_pack] = domain_counts.get(domain_pack, 0) + 1

    return ReplayCorpusSummary(
        case_count=case_count,
        domains=sorted(domain_counts),
        domain_counts=domain_counts,
        files=file_counts,
    )
