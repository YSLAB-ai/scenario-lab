from __future__ import annotations

import json
from pathlib import Path

from forecasting_harness.models import BeliefState


class RunRepository:
    def __init__(self, root: Path) -> None:
        self.root = root

    def run_dir(self, run_id: str) -> Path:
        return self.root / "runs" / run_id

    def save_belief_state(self, run_id: str, state: BeliefState) -> None:
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "belief-state.json").write_text(state.model_dump_json(indent=2), encoding="utf-8")

    def load_belief_state(self, run_id: str) -> BeliefState:
        return BeliefState.model_validate_json((self.run_dir(run_id) / "belief-state.json").read_text(encoding="utf-8"))

    def write_markdown(self, run_id: str, name: str, content: str) -> None:
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / name).write_text(content, encoding="utf-8")

    def write_json(self, run_id: str, name: str, payload: object) -> None:
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / name).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
