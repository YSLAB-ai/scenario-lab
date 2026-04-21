from __future__ import annotations

import json
from pathlib import Path

from forecasting_harness.replay import ReplayCase


def _replay_root() -> Path:
    return Path(__file__).resolve().parents[5] / "knowledge" / "replays"


def load_builtin_replay_cases() -> list[ReplayCase]:
    replay_path = _replay_root() / "builtin-cases.json"
    if not replay_path.exists():
        raise FileNotFoundError(replay_path)
    payload = json.loads(replay_path.read_text(encoding="utf-8"))
    return [ReplayCase.model_validate(item) for item in payload]
