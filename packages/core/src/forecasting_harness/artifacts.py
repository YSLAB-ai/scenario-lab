from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from forecasting_harness.models import BeliefState
from forecasting_harness.workflow.models import RevisionRecord, RunRecord

RESERVED_ARTIFACT_NAMES = {"belief-state.json"}


class RunRepository:
    def __init__(self, root: Path) -> None:
        self.root = root

    def run_dir(self, run_id: str) -> Path:
        self._validate_path_segment(run_id, "run_id")
        return self.root / "runs" / run_id

    def init_run(self, run: RunRecord) -> None:
        run_dir = self.run_dir(run.run_id)
        if run_dir.exists():
            raise FileExistsError(run_dir)
        run_dir.mkdir(parents=True, exist_ok=False)
        (run_dir / "run.json").write_text(run.model_dump_json(indent=2), encoding="utf-8")
        (run_dir / "events.jsonl").touch(exist_ok=True)

    def save_run_record(self, run: RunRecord) -> None:
        run_dir = self.run_dir(run.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run.json").write_text(run.model_dump_json(indent=2), encoding="utf-8")

    def load_run_record(self, run_id: str) -> RunRecord:
        run = RunRecord.model_validate_json((self.run_dir(run_id) / "run.json").read_text(encoding="utf-8"))
        if run.run_id != run_id:
            raise ValueError(f"run_id mismatch: expected {run_id!r}, got {run.run_id!r}")
        return run

    def save_revision_record(self, run_id: str, record: RevisionRecord) -> None:
        self._validate_path_segment(record.revision_id, "revision_id")
        revision_dir = self._require_initialized_run(run_id) / "revisions"
        revision_dir.mkdir(parents=True, exist_ok=True)
        (revision_dir / f"{record.revision_id}.json").write_text(record.model_dump_json(indent=2), encoding="utf-8")

    def load_revision_record(self, run_id: str, revision_id: str) -> RevisionRecord:
        self._validate_path_segment(revision_id, "revision_id")
        path = self.run_dir(run_id) / "revisions" / f"{revision_id}.json"
        return RevisionRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def list_revision_records(self, run_id: str) -> list[RevisionRecord]:
        revision_dir = self.run_dir(run_id) / "revisions"
        if not revision_dir.exists():
            return []
        return [
            RevisionRecord.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(revision_dir.glob("*.json"))
        ]

    def save_belief_state(self, run_id: str, state: BeliefState) -> None:
        if state.run_id != run_id:
            raise ValueError(f"run_id mismatch: expected {run_id!r}, got {state.run_id!r}")
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "belief-state.json").write_text(state.model_dump_json(indent=2), encoding="utf-8")

    def load_belief_state(self, run_id: str) -> BeliefState:
        state = BeliefState.model_validate_json((self.run_dir(run_id) / "belief-state.json").read_text(encoding="utf-8"))
        if state.run_id != run_id:
            raise ValueError(f"run_id mismatch: expected {run_id!r}, got {state.run_id!r}")
        return state

    def write_markdown(self, run_id: str, name: str, content: str) -> None:
        run_dir = self.run_dir(run_id)
        self._validate_artifact_name(name)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / name).write_text(content, encoding="utf-8")

    def write_json(self, run_id: str, name: str, payload: object) -> None:
        run_dir = self.run_dir(run_id)
        self._validate_artifact_name(name)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / name).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def write_revision_json(
        self,
        run_id: str,
        section: str,
        revision_id: str,
        payload: object,
        *,
        approved: bool,
        overwrite: bool = False,
    ) -> Path:
        self._validate_path_segment(section, "section")
        self._validate_path_segment(revision_id, "revision_id")
        run_dir = self._require_initialized_run(run_id)
        section_dir = run_dir / section
        section_dir.mkdir(parents=True, exist_ok=True)
        suffix = "approved" if approved else "draft"
        path = section_dir / f"{revision_id}.{suffix}.json"
        if approved and path.exists() and not overwrite:
            raise FileExistsError(path)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def load_revision_model(
        self,
        run_id: str,
        section: str,
        revision_id: str,
        model_type: type,
        *,
        approved: bool,
    ):
        suffix = "approved" if approved else "draft"
        self._validate_path_segment(section, "section")
        self._validate_path_segment(revision_id, "revision_id")
        path = self.run_dir(run_id) / section / f"{revision_id}.{suffix}.json"
        return model_type.model_validate_json(path.read_text(encoding="utf-8"))

    def write_revision_markdown(self, run_id: str, revision_id: str, name: str, content: str) -> Path:
        self._validate_path_segment(revision_id, "revision_id")
        self._validate_artifact_name(name)
        run_dir = self._require_initialized_run(run_id)
        section_dir = run_dir / "reports"
        section_dir.mkdir(parents=True, exist_ok=True)
        path = section_dir / f"{revision_id}.{name}"
        path.write_text(content, encoding="utf-8")
        return path

    def append_event(self, run_id: str, event_type: str, payload: dict[str, object]) -> None:
        run_dir = self._require_initialized_run(run_id)
        event = {
            "event_type": event_type,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        with (run_dir / "events.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True) + "\n")

    @staticmethod
    def _validate_path_segment(value: str, label: str) -> None:
        path = Path(value)
        if path.is_absolute() or len(path.parts) != 1 or path.parts[0] in {".", ".."}:
            raise ValueError(f"{label} path traversal is not allowed: {value!r}")

    @staticmethod
    def _validate_artifact_name(value: str) -> None:
        RunRepository._validate_path_segment(value, "artifact name")
        if value in RESERVED_ARTIFACT_NAMES:
            raise ValueError(f"artifact name is reserved: {value!r}")

    def _require_initialized_run(self, run_id: str) -> Path:
        run_dir = self.run_dir(run_id)
        if not (run_dir / "run.json").exists():
            raise FileNotFoundError(run_dir / "run.json")
        return run_dir
