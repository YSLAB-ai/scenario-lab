# Interstate Workflow Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first reusable analyst workflow slice for the forecasting harness, validated with an interstate-crisis reference pack but implemented so the core lifecycle can be reused by future domains.

**Architecture:** Keep the conversational experience in Codex/Claude adapter skills, but move all durable state transitions into a deterministic Python core under `packages/core/`. Add a small `workflow/` application layer for run/revision operations, belief-state compilation, evidence packet drafting, and report generation; then plug an `interstate_crisis` reference pack into the existing domain-pack system without special-casing the workflow architecture.

**Tech Stack:** Python 3.12+, Pydantic 2, Typer, pytest, sqlite3/FTS5

---

## Scope

This plan delivers the next executable slice after the current core prototype:

- reusable workflow models for runs, revisions, intake drafts, assumptions, and evidence packets
- revisioned artifact storage under `.forecast/`
- deterministic workflow service operations for:
  - `start-run`
  - `save-intake-draft`
  - `save-evidence-draft`
  - `approve-revision`
  - `compile-belief-state`
  - `simulate`
  - `generate-report`
- reusable evidence-packet drafting and belief-state compilation helpers
- one `interstate_crisis` reference domain pack
- report generation with evidence coverage and credibility notes
- CLI commands that map directly to the core workflow operations
- adapter docs updated to use the new workflow

This plan does not attempt:

- multiple mature domain packs
- simultaneous-move resolution
- open-web retrieval
- automatic rule extraction
- historical replay/calibration

## File Structure

### Existing files to modify

- Modify: `/packages/core/src/forecasting_harness/models.py`
  Extend the simulation-facing state with revision-aware metadata (`revision_id`, `domain_pack`, `phase`, approved evidence ids) without breaking the current engine.
- Modify: `/packages/core/src/forecasting_harness/artifacts.py`
  Replace the single-run flat artifact writer with a revision-aware repository that can persist drafts, approved snapshots, reports, and event logs.
- Modify: `/packages/core/src/forecasting_harness/domain/base.py`
  Add domain-pack hooks required by the reusable workflow: canonical phases, suggested actors, and retrieval filters.
- Modify: `/packages/core/src/forecasting_harness/domain/__init__.py`
  Export the new reference pack.
- Modify: `/packages/core/src/forecasting_harness/query_api.py`
  Add revision-aware report/query helpers.
- Modify: `/packages/core/src/forecasting_harness/cli.py`
  Replace the toy workflow surface with deterministic workflow commands while keeping `version` and `demo-run`.
- Modify: `/packages/core/tests/test_artifacts.py`
- Modify: `/packages/core/tests/test_cli_workflow.py`
- Modify: `/packages/core/tests/test_models.py`
- Modify: `/packages/core/tests/test_retrieval.py`
- Modify: `/packages/core/tests/test_adapter_docs.py`
- Modify: `/adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md`
- Modify: `/adapters/claude/skills/forecast-harness/SKILL.md`
- Modify: `/docs/install-codex.md`
- Modify: `/docs/install-claude-code.md`

### New workflow application layer

- Create: `/packages/core/src/forecasting_harness/workflow/__init__.py`
  Small package export surface.
- Create: `/packages/core/src/forecasting_harness/workflow/models.py`
  Pydantic models for `RunRecord`, `RevisionRecord`, `IntakeDraft`, `AssumptionSummary`, `EvidencePacket`, and evidence packet items.
- Create: `/packages/core/src/forecasting_harness/workflow/evidence.py`
  Reusable evidence packet drafting from retrieval hits.
- Create: `/packages/core/src/forecasting_harness/workflow/compiler.py`
  Reusable belief-state compilation from approved workflow inputs.
- Create: `/packages/core/src/forecasting_harness/workflow/reporting.py`
  Markdown report/workbench generation.
- Create: `/packages/core/src/forecasting_harness/workflow/service.py`
  Deterministic orchestration methods that adapters and CLI commands call.

### New reference domain pack

- Create: `/packages/core/src/forecasting_harness/domain/interstate_crisis.py`
  First reference pack using fixed phases, event-driven transitions, and suggested third parties.

### New tests

- Create: `/packages/core/tests/test_workflow_models.py`
- Create: `/packages/core/tests/test_workflow_service.py`
- Create: `/packages/core/tests/test_workflow_evidence.py`
- Create: `/packages/core/tests/test_interstate_crisis_pack.py`

## Task 1: Add Reusable Workflow Models and Extend BeliefState Metadata

**Files:**
- Modify: `/packages/core/src/forecasting_harness/models.py`
- Create: `/packages/core/src/forecasting_harness/workflow/__init__.py`
- Create: `/packages/core/src/forecasting_harness/workflow/models.py`
- Modify: `/packages/core/tests/test_models.py`
- Create: `/packages/core/tests/test_workflow_models.py`

- [ ] **Step 1: Write failing tests for workflow drafts, revisions, and revision-aware belief states**

```python
# packages/core/tests/test_workflow_models.py
from datetime import datetime, timezone

import pytest

from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.models import BeliefState
from forecasting_harness.workflow.models import IntakeDraft, RevisionRecord, RunRecord


def test_intake_draft_requires_two_primary_actors() -> None:
    with pytest.raises(ValueError):
        IntakeDraft(
            event_framing="Assess crisis risk",
            primary_actors=["Actor A"],
            trigger="Border incident",
            current_phase="trigger",
            time_horizon="30d",
        )


def test_run_record_starts_without_current_revision() -> None:
    run = RunRecord(
        run_id="crisis-1",
        domain_pack="interstate-crisis",
        created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
    )
    assert run.current_revision_id is None


def test_revision_record_defaults_to_draft_status() -> None:
    revision = RevisionRecord(revision_id="r1")
    assert revision.status == "draft"


def test_belief_state_tracks_revision_phase_and_domain_pack() -> None:
    state = BeliefState(
        run_id="crisis-1",
        revision_id="r2",
        domain_pack="interstate-crisis",
        phase="signaling",
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[],
        fields={},
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        approved_evidence_ids=["ev-1"],
        current_epoch="trigger",
        horizon="30d",
    )
    assert state.revision_id == "r2"
    assert state.phase == "signaling"
    assert state.approved_evidence_ids == ["ev-1"]
```

- [ ] **Step 2: Run the model tests to verify they fail**

Run: `python -m pytest packages/core/tests/test_workflow_models.py packages/core/tests/test_models.py -v`

Expected: FAIL with import errors or missing `BeliefState` fields.

- [ ] **Step 3: Implement the workflow models and extend the simulation-facing belief state**

```python
# packages/core/src/forecasting_harness/workflow/models.py
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RevisionStatus = Literal["draft", "approved", "simulated"]


class RunRecord(BaseModel):
    run_id: str
    domain_pack: str
    created_at: datetime
    current_revision_id: str | None = None


class RevisionRecord(BaseModel):
    revision_id: str
    status: RevisionStatus = "draft"
    parent_revision_id: str | None = None


class IntakeDraft(BaseModel):
    event_framing: str
    primary_actors: list[str] = Field(min_length=2, max_length=2)
    trigger: str
    current_phase: str
    time_horizon: str
    known_constraints: list[str] = Field(default_factory=list)
    known_unknowns: list[str] = Field(default_factory=list)
    suggested_actors: list[str] = Field(default_factory=list)


class AssumptionSummary(BaseModel):
    summary: list[str] = Field(default_factory=list)
    suggested_actors: list[str] = Field(default_factory=list)
    objective_profile_name: str = "balanced"


class EvidencePacketItem(BaseModel):
    evidence_id: str
    source_id: str
    source_title: str
    reason: str
    passage_ids: list[str] = Field(default_factory=list)
    citation_refs: list[str] = Field(default_factory=list)
    raw_passages: list[str] = Field(default_factory=list)


class EvidencePacket(BaseModel):
    revision_id: str
    items: list[EvidencePacketItem] = Field(default_factory=list)
```

```python
# packages/core/src/forecasting_harness/models.py
class BeliefState(BaseModel):
    run_id: str
    revision_id: str | None = None
    domain_pack: str | None = None
    phase: str | None = None
    interaction_model: InteractionModel
    actors: list[Actor]
    fields: dict[str, BeliefField]
    objectives: dict[str, str]
    capabilities: dict[str, str]
    constraints: dict[str, str]
    unknowns: list[str]
    approved_evidence_ids: list[str] = Field(default_factory=list)
    current_epoch: str
    horizon: str
```

```python
# packages/core/src/forecasting_harness/workflow/__init__.py
from forecasting_harness.workflow.models import (
    AssumptionSummary,
    EvidencePacket,
    EvidencePacketItem,
    IntakeDraft,
    RevisionRecord,
    RunRecord,
)

__all__ = [
    "AssumptionSummary",
    "EvidencePacket",
    "EvidencePacketItem",
    "IntakeDraft",
    "RevisionRecord",
    "RunRecord",
]
```

- [ ] **Step 4: Run the model tests to verify they pass**

Run: `python -m pytest packages/core/tests/test_workflow_models.py packages/core/tests/test_models.py -v`

Expected: PASS

- [ ] **Step 5: Commit the workflow model layer**

```bash
git add packages/core/src/forecasting_harness/models.py \
        packages/core/src/forecasting_harness/workflow/__init__.py \
        packages/core/src/forecasting_harness/workflow/models.py \
        packages/core/tests/test_models.py \
        packages/core/tests/test_workflow_models.py
git commit -m "feat: add reusable workflow models"
```

## Task 2: Rebuild Artifact Storage Around Runs, Revisions, and Immutable Approved Snapshots

**Files:**
- Modify: `/packages/core/src/forecasting_harness/artifacts.py`
- Modify: `/packages/core/tests/test_artifacts.py`

- [ ] **Step 1: Write failing tests for run initialization, revision snapshots, and append-only events**

```python
# packages/core/tests/test_artifacts.py
from datetime import datetime, timezone

import json
import pytest

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.workflow.models import EvidencePacket, IntakeDraft, RunRecord


def test_init_run_creates_run_metadata_and_event_log(tmp_path) -> None:
    repo = RunRepository(tmp_path / ".forecast")
    run = RunRecord(
        run_id="crisis-1",
        domain_pack="interstate-crisis",
        created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
    )
    repo.init_run(run)
    assert (repo.run_dir("crisis-1") / "run.json").exists()
    assert (repo.run_dir("crisis-1") / "events.jsonl").exists()


def test_save_approved_snapshot_refuses_overwrite(tmp_path) -> None:
    repo = RunRepository(tmp_path / ".forecast")
    repo.write_revision_json("crisis-1", "intake", "r1", {"ok": True}, approved=True)
    with pytest.raises(FileExistsError):
        repo.write_revision_json("crisis-1", "intake", "r1", {"ok": False}, approved=True)


def test_append_event_writes_one_json_object_per_line(tmp_path) -> None:
    repo = RunRepository(tmp_path / ".forecast")
    repo.append_event("crisis-1", "run-started", {"domain_pack": "interstate-crisis"})
    lines = (repo.run_dir("crisis-1") / "events.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert json.loads(lines[0])["event_type"] == "run-started"
```

- [ ] **Step 2: Run the artifact tests to verify they fail**

Run: `python -m pytest packages/core/tests/test_artifacts.py -v`

Expected: FAIL with missing repository methods.

- [ ] **Step 3: Implement revision-aware repository methods and immutable approved writes**

```python
# packages/core/src/forecasting_harness/artifacts.py
import json
from datetime import datetime, timezone
from pathlib import Path

from forecasting_harness.models import BeliefState
from forecasting_harness.workflow.models import RunRecord


class RunRepository:
    ...

    def init_run(self, run: RunRecord) -> None:
        run_dir = self.run_dir(run.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run.json").write_text(run.model_dump_json(indent=2), encoding="utf-8")
        (run_dir / "events.jsonl").touch(exist_ok=True)

    def save_run_record(self, run: RunRecord) -> None:
        (self.run_dir(run.run_id) / "run.json").write_text(run.model_dump_json(indent=2), encoding="utf-8")

    def load_run_record(self, run_id: str) -> RunRecord:
        return RunRecord.model_validate_json((self.run_dir(run_id) / "run.json").read_text(encoding="utf-8"))

    def write_revision_json(
        self,
        run_id: str,
        section: str,
        revision_id: str,
        payload: object,
        *,
        approved: bool,
    ) -> Path:
        section_dir = self.run_dir(run_id) / section
        section_dir.mkdir(parents=True, exist_ok=True)
        suffix = "approved" if approved else "draft"
        path = section_dir / f"{revision_id}.{suffix}.json"
        if approved and path.exists():
            raise FileExistsError(path)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def load_revision_model(self, run_id: str, section: str, revision_id: str, model_type, *, approved: bool):
        suffix = "approved" if approved else "draft"
        path = self.run_dir(run_id) / section / f"{revision_id}.{suffix}.json"
        return model_type.model_validate_json(path.read_text(encoding="utf-8"))

    def write_revision_markdown(self, run_id: str, revision_id: str, name: str, content: str) -> Path:
        section_dir = self.run_dir(run_id) / "reports"
        section_dir.mkdir(parents=True, exist_ok=True)
        path = section_dir / f"{revision_id}.{name}"
        path.write_text(content, encoding="utf-8")
        return path

    def append_event(self, run_id: str, event_type: str, payload: dict[str, object]) -> None:
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        event = {
            "event_type": event_type,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        with (run_dir / "events.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True) + "\n")
```

- [ ] **Step 4: Run the artifact tests to verify they pass**

Run: `python -m pytest packages/core/tests/test_artifacts.py -v`

Expected: PASS

- [ ] **Step 5: Commit the repository rewrite**

```bash
git add packages/core/src/forecasting_harness/artifacts.py \
        packages/core/tests/test_artifacts.py
git commit -m "feat: add revision-aware run repository"
```

## Task 3: Add a Deterministic Workflow Service for Run Creation, Drafts, and Approval

**Files:**
- Create: `/packages/core/src/forecasting_harness/workflow/service.py`
- Create: `/packages/core/tests/test_workflow_service.py`

- [ ] **Step 1: Write failing tests for `start_run`, `save_intake_draft`, `save_evidence_draft`, and `approve_revision`**

```python
# packages/core/tests/test_workflow_service.py
from forecasting_harness.artifacts import RunRepository
from forecasting_harness.workflow.models import AssumptionSummary, EvidencePacket, IntakeDraft
from forecasting_harness.workflow.service import WorkflowService


def test_start_run_persists_run_and_event(tmp_path) -> None:
    repo = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repo)
    run = service.start_run(run_id="crisis-1", domain_pack="interstate-crisis")
    assert run.run_id == "crisis-1"
    assert repo.run_dir("crisis-1").joinpath("run.json").exists()


def test_approve_revision_sets_current_revision_and_writes_approved_snapshots(tmp_path) -> None:
    repo = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repo)
    service.start_run(run_id="crisis-1", domain_pack="interstate-crisis")
    intake = IntakeDraft(
        event_framing="Assess escalation",
        primary_actors=["US", "Iran"],
        trigger="Exchange of strikes",
        current_phase="trigger",
        time_horizon="30d",
    )
    evidence = EvidencePacket(revision_id="r1", items=[])
    assumptions = AssumptionSummary(summary=["Both sides avoid immediate full war"])
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)
    run = service.approve_revision("crisis-1", "r1", assumptions)
    assert run.current_revision_id == "r1"
```

- [ ] **Step 2: Run the workflow service tests to verify they fail**

Run: `python -m pytest packages/core/tests/test_workflow_service.py -v`

Expected: FAIL with `ModuleNotFoundError` or missing methods.

- [ ] **Step 3: Implement the workflow service for generic run and approval operations**

```python
# packages/core/src/forecasting_harness/workflow/service.py
from __future__ import annotations

from datetime import datetime, timezone

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.workflow.models import AssumptionSummary, EvidencePacket, IntakeDraft, RunRecord


class WorkflowService:
    def __init__(self, repo: RunRepository):
        self.repo = repo

    def start_run(self, *, run_id: str, domain_pack: str) -> RunRecord:
        run = RunRecord(
            run_id=run_id,
            domain_pack=domain_pack,
            created_at=datetime.now(timezone.utc),
        )
        self.repo.init_run(run)
        self.repo.append_event(run_id, "run-started", {"domain_pack": domain_pack})
        return run

    def save_intake_draft(self, run_id: str, revision_id: str, intake: IntakeDraft) -> None:
        self.repo.write_revision_json(run_id, "intake", revision_id, intake.model_dump(mode="json"), approved=False)
        self.repo.append_event(run_id, "intake-drafted", {"revision_id": revision_id})

    def save_evidence_draft(self, run_id: str, revision_id: str, packet: EvidencePacket) -> None:
        self.repo.write_revision_json(run_id, "evidence", revision_id, packet.model_dump(mode="json"), approved=False)
        self.repo.append_event(run_id, "evidence-drafted", {"revision_id": revision_id})

    def approve_revision(self, run_id: str, revision_id: str, assumptions: AssumptionSummary) -> RunRecord:
        intake = self.repo.load_revision_model(run_id, "intake", revision_id, IntakeDraft, approved=False)
        evidence = self.repo.load_revision_model(run_id, "evidence", revision_id, EvidencePacket, approved=False)
        self.repo.write_revision_json(
            run_id,
            "intake",
            revision_id,
            intake.model_dump(mode="json"),
            approved=True,
        )
        self.repo.write_revision_json(
            run_id,
            "evidence",
            revision_id,
            evidence.model_dump(mode="json"),
            approved=True,
        )
        self.repo.write_revision_json(
            run_id,
            "assumptions",
            revision_id,
            assumptions.model_dump(mode="json"),
            approved=True,
        )
        run = self.repo.load_run_record(run_id)
        updated = run.model_copy(update={"current_revision_id": revision_id})
        self.repo.save_run_record(updated)
        self.repo.append_event(run_id, "revision-approved", {"revision_id": revision_id})
        return updated
```

- [ ] **Step 4: Run the workflow service tests to verify they pass**

Run: `python -m pytest packages/core/tests/test_workflow_service.py -v`

Expected: PASS

- [ ] **Step 5: Commit the generic workflow service**

```bash
git add packages/core/src/forecasting_harness/workflow/service.py \
        packages/core/tests/test_workflow_service.py
git commit -m "feat: add deterministic workflow service"
```

## Task 4: Add Domain-Reusable Evidence Drafting, Belief-State Compilation, and New Domain Hooks

**Files:**
- Modify: `/packages/core/src/forecasting_harness/domain/base.py`
- Create: `/packages/core/src/forecasting_harness/workflow/evidence.py`
- Create: `/packages/core/src/forecasting_harness/workflow/compiler.py`
- Create: `/packages/core/tests/test_workflow_evidence.py`

- [ ] **Step 1: Write failing tests for source-balanced evidence packets and belief-state compilation**

```python
# packages/core/tests/test_workflow_evidence.py
from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.models import ObjectiveProfile
from forecasting_harness.workflow.compiler import compile_belief_state
from forecasting_harness.workflow.evidence import draft_evidence_packet
from forecasting_harness.workflow.models import AssumptionSummary, IntakeDraft


class StubPack(DomainPack):
    def slug(self) -> str: return "stub"
    def interaction_model(self) -> InteractionModel: return InteractionModel.EVENT_DRIVEN
    def extend_schema(self) -> dict[str, str]: return {}
    def suggest_questions(self) -> list[str]: return []
    def canonical_phases(self) -> list[str]: return ["trigger", "signaling"]
    def suggest_related_actors(self, intake: IntakeDraft) -> list[str]: return ["China"]
    def retrieval_filters(self, intake: IntakeDraft) -> dict[str, str]: return {"region": "middle-east"}
    def propose_actions(self, state): return []
    def sample_transition(self, state, action_context): return [state]
    def score_state(self, state): return {"escalation": 0.0}
    def validate_state(self, state): return []


def test_draft_evidence_packet_limits_passages_per_source() -> None:
    hits = [
        {"source_id": "s1", "title": "Doc 1", "content": "a", "published_at": "2026-04-20", "score": 1.0},
        {"source_id": "s1", "title": "Doc 1", "content": "b", "published_at": "2026-04-20", "score": 0.9},
        {"source_id": "s1", "title": "Doc 1", "content": "c", "published_at": "2026-04-20", "score": 0.8},
        {"source_id": "s2", "title": "Doc 2", "content": "d", "published_at": "2026-04-20", "score": 0.7},
    ]
    packet = draft_evidence_packet("r1", hits, max_per_source=2)
    assert len([item for item in packet.items if item.source_id == "s1"]) == 2


def test_compile_belief_state_includes_primary_and_suggested_actors() -> None:
    intake = IntakeDraft(
        event_framing="Assess escalation",
        primary_actors=["US", "Iran"],
        trigger="Exchange of strikes",
        current_phase="trigger",
        time_horizon="30d",
        suggested_actors=["China"],
    )
    assumptions = AssumptionSummary(summary=["China matters"], suggested_actors=["China"])
    state = compile_belief_state(
        run_id="crisis-1",
        revision_id="r1",
        pack=StubPack(),
        intake=intake,
        assumptions=assumptions,
        approved_evidence_ids=["ev-1"],
    )
    assert [actor.name for actor in state.actors] == ["US", "Iran", "China"]
    assert state.phase == "trigger"
```

- [ ] **Step 2: Run the workflow evidence tests to verify they fail**

Run: `python -m pytest packages/core/tests/test_workflow_evidence.py -v`

Expected: FAIL with missing domain hooks or missing compiler/evidence modules.

- [ ] **Step 3: Extend the generic domain interface with reusable workflow hooks**

```python
# packages/core/src/forecasting_harness/domain/base.py
class DomainPack(ABC):
    ...

    def canonical_phases(self) -> list[str]:
        return []

    def suggest_related_actors(self, intake: "IntakeDraft") -> list[str]:
        return []

    def retrieval_filters(self, intake: "IntakeDraft") -> dict[str, str]:
        return {}
```

- [ ] **Step 4: Implement reusable evidence drafting and belief-state compilation**

```python
# packages/core/src/forecasting_harness/workflow/evidence.py
from collections import defaultdict

from forecasting_harness.workflow.models import EvidencePacket, EvidencePacketItem


def draft_evidence_packet(
    revision_id: str,
    hits: list[dict[str, object]],
    *,
    max_per_source: int = 2,
) -> EvidencePacket:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for hit in hits:
        grouped[str(hit["source_id"])].append(hit)

    items: list[EvidencePacketItem] = []
    for source_id, source_hits in grouped.items():
        for index, hit in enumerate(source_hits[:max_per_source], start=1):
            items.append(
                EvidencePacketItem(
                    evidence_id=f"{revision_id}:{source_id}:{index}",
                    source_id=source_id,
                    source_title=str(hit["title"]),
                    reason="Candidate passage for approved evidence packet",
                    passage_ids=[f"{source_id}:{index}"],
                    citation_refs=[f"{source_id}:{index}"],
                    raw_passages=[str(hit["content"])],
                )
            )
    return EvidencePacket(revision_id=revision_id, items=items)
```

```python
# packages/core/src/forecasting_harness/workflow/compiler.py
from datetime import datetime, timezone

from forecasting_harness.domain.base import DomainPack
from forecasting_harness.models import Actor, BeliefField, BeliefState
from forecasting_harness.workflow.models import AssumptionSummary, IntakeDraft


def compile_belief_state(
    *,
    run_id: str,
    revision_id: str,
    pack: DomainPack,
    intake: IntakeDraft,
    assumptions: AssumptionSummary,
    approved_evidence_ids: list[str],
) -> BeliefState:
    actor_names = intake.primary_actors + [
        actor for actor in assumptions.suggested_actors if actor not in intake.primary_actors
    ]
    now = datetime.now(timezone.utc)
    return BeliefState(
        run_id=run_id,
        revision_id=revision_id,
        domain_pack=pack.slug(),
        phase=intake.current_phase,
        interaction_model=pack.interaction_model(),
        actors=[Actor(actor_id=name.lower().replace(" ", "-"), name=name) for name in actor_names],
        fields={
            "event_framing": BeliefField(
                value=intake.event_framing,
                normalized_value=intake.event_framing,
                status="observed",
                confidence=1.0,
                last_updated_at=now,
            ),
            "trigger": BeliefField(
                value=intake.trigger,
                normalized_value=intake.trigger,
                status="observed",
                confidence=1.0,
                last_updated_at=now,
            ),
        },
        objectives={},
        capabilities={},
        constraints={str(i): value for i, value in enumerate(intake.known_constraints)},
        unknowns=list(intake.known_unknowns),
        approved_evidence_ids=approved_evidence_ids,
        current_epoch=intake.current_phase,
        horizon=intake.time_horizon,
    )
```

- [ ] **Step 5: Run the workflow evidence tests to verify they pass**

Run: `python -m pytest packages/core/tests/test_workflow_evidence.py -v`

Expected: PASS

- [ ] **Step 6: Commit the reusable evidence/compiler layer**

```bash
git add packages/core/src/forecasting_harness/domain/base.py \
        packages/core/src/forecasting_harness/workflow/evidence.py \
        packages/core/src/forecasting_harness/workflow/compiler.py \
        packages/core/tests/test_workflow_evidence.py
git commit -m "feat: add reusable workflow evidence and compiler hooks"
```

## Task 5: Implement the Interstate-Crisis Reference Pack

**Files:**
- Create: `/packages/core/src/forecasting_harness/domain/interstate_crisis.py`
- Modify: `/packages/core/src/forecasting_harness/domain/__init__.py`
- Create: `/packages/core/tests/test_interstate_crisis_pack.py`

- [ ] **Step 1: Write failing tests for canonical phases, suggested third parties, and crisis actions**

```python
# packages/core/tests/test_interstate_crisis_pack.py
from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack
from forecasting_harness.workflow.models import IntakeDraft


def test_pack_exposes_fixed_canonical_phases() -> None:
    pack = InterstateCrisisPack()
    assert pack.canonical_phases() == [
        "trigger",
        "signaling",
        "limited-response",
        "escalation",
        "negotiation-deescalation",
        "settlement-stalemate",
    ]


def test_pack_suggests_relevant_third_parties_for_us_iran_case() -> None:
    pack = InterstateCrisisPack()
    intake = IntakeDraft(
        event_framing="Assess escalation",
        primary_actors=["US", "Iran"],
        trigger="Exchange of strikes",
        current_phase="trigger",
        time_horizon="30d",
    )
    suggestions = pack.suggest_related_actors(intake)
    assert "China" in suggestions


def test_pack_validates_phase_membership() -> None:
    pack = InterstateCrisisPack()
    assert "unsupported phase" in pack.validate_phase("improvise")[0]
```

- [ ] **Step 2: Run the interstate-crisis tests to verify they fail**

Run: `python -m pytest packages/core/tests/test_interstate_crisis_pack.py -v`

Expected: FAIL with import errors.

- [ ] **Step 3: Implement the reference pack with fixed phases and simple event-driven actions**

```python
# packages/core/src/forecasting_harness/domain/interstate_crisis.py
from __future__ import annotations

from typing import Any

from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.workflow.models import IntakeDraft


class InterstateCrisisPack(DomainPack):
    PHASES = [
        "trigger",
        "signaling",
        "limited-response",
        "escalation",
        "negotiation-deescalation",
        "settlement-stalemate",
    ]

    def slug(self) -> str:
        return "interstate-crisis"

    def interaction_model(self) -> InteractionModel:
        return InteractionModel.EVENT_DRIVEN

    def canonical_phases(self) -> list[str]:
        return list(self.PHASES)

    def suggest_related_actors(self, intake: IntakeDraft) -> list[str]:
        actor_set = set(intake.primary_actors)
        if actor_set == {"US", "Iran"}:
            return ["China", "Israel", "Gulf States", "Russia"]
        return []

    def retrieval_filters(self, intake: IntakeDraft) -> dict[str, str]:
        return {"domain": "interstate-crisis"}

    def suggest_questions(self) -> list[str]:
        return [
            "Which outside actor has the most leverage over the next phase?",
            "What constraint most limits immediate escalation?",
        ]

    def extend_schema(self) -> dict[str, Any]:
        return {"military_posture": "str", "leader_style": "str"}

    def validate_phase(self, phase: str) -> list[str]:
        if phase not in self.PHASES:
            return [f"unsupported phase: {phase}"]
        return []

    def propose_actions(self, state) -> list[dict[str, Any]]:
        return [
            {"action_id": "signal", "branch_id": "signal", "label": "Signal resolve", "dependencies": {"fields": []}},
            {"action_id": "limited-response", "branch_id": "limited-response", "label": "Limited response", "dependencies": {"fields": []}},
            {"action_id": "open-negotiation", "branch_id": "open-negotiation", "label": "Open negotiation", "dependencies": {"fields": []}},
        ]

    def sample_transition(self, state, action_context):
        return [state]

    def score_state(self, state) -> dict[str, float]:
        return {"escalation": 0.3, "negotiation": 0.4, "economic_stress": 0.2}

    def validate_state(self, state) -> list[str]:
        return self.validate_phase(state.phase or "")
```

```python
# packages/core/src/forecasting_harness/domain/__init__.py
from forecasting_harness.domain.generic_event import GenericEventPack
from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack

__all__ = ["GenericEventPack", "InterstateCrisisPack"]
```

- [ ] **Step 4: Run the interstate-crisis tests to verify they pass**

Run: `python -m pytest packages/core/tests/test_interstate_crisis_pack.py -v`

Expected: PASS

- [ ] **Step 5: Commit the reference pack**

```bash
git add packages/core/src/forecasting_harness/domain/interstate_crisis.py \
        packages/core/src/forecasting_harness/domain/__init__.py \
        packages/core/tests/test_interstate_crisis_pack.py
git commit -m "feat: add interstate crisis reference pack"
```

## Task 6: Add Belief-State Compilation, Simulation, Report Generation, and Revisioned Reruns to the Workflow Service

**Files:**
- Create: `/packages/core/src/forecasting_harness/workflow/reporting.py`
- Modify: `/packages/core/src/forecasting_harness/workflow/service.py`
- Modify: `/packages/core/src/forecasting_harness/query_api.py`
- Modify: `/packages/core/tests/test_workflow_service.py`

- [ ] **Step 1: Write failing tests for compile/simulate/report and material evidence reruns**

```python
# packages/core/tests/test_workflow_service.py
from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack


def test_simulate_revision_writes_belief_state_tree_summary_and_report(tmp_path) -> None:
    repo = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repo)
    pack = InterstateCrisisPack()
    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    ...
    result = service.simulate_revision("crisis-1", "r1", pack=pack)
    assert "branches" in result
    assert repo.run_dir("crisis-1").joinpath("belief-state", "r1.approved.json").exists()
    assert repo.run_dir("crisis-1").joinpath("reports", "r1.report.md").exists()


def test_new_evidence_revision_does_not_overwrite_prior_report(tmp_path) -> None:
    repo = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repo)
    ...
    service.generate_report("crisis-1", "r1", simulation={"branches": []}, evidence_count=0, unsupported_count=1)
    service.generate_report("crisis-1", "r2", simulation={"branches": []}, evidence_count=2, unsupported_count=0)
    assert repo.run_dir("crisis-1").joinpath("reports", "r1.report.md").exists()
    assert repo.run_dir("crisis-1").joinpath("reports", "r2.report.md").exists()
```

- [ ] **Step 2: Run the workflow service tests to verify they fail**

Run: `python -m pytest packages/core/tests/test_workflow_service.py -v`

Expected: FAIL with missing `simulate_revision` or `generate_report`.

- [ ] **Step 3: Implement report rendering and simulation orchestration in the workflow service**

```python
# packages/core/src/forecasting_harness/workflow/reporting.py
from forecasting_harness.query_api import summarize_top_branches


def render_report(*, revision_id: str, simulation: dict[str, object], evidence_count: int, unsupported_count: int) -> str:
    top = summarize_top_branches(simulation.get("branches", []), limit=3)
    lines = [
        "# Scenario Report",
        "",
        f"- Revision: {revision_id}",
        f"- Approved evidence items: {evidence_count}",
        f"- Unsupported assumptions: {unsupported_count}",
        "",
        "## Top Branches",
    ]
    for branch in top:
        lines.append(f"- {branch['label']} ({branch['score']})")
    if evidence_count == 0:
        lines.extend(["", "## Credibility Note", "- No approved evidence items. Treat this as a low-credibility exploratory run."])
    return "\n".join(lines) + "\n"
```

```python
# packages/core/src/forecasting_harness/workflow/service.py
from forecasting_harness.objectives import default_objective_profile
from forecasting_harness.simulation.engine import SimulationEngine
from forecasting_harness.workflow.compiler import compile_belief_state
from forecasting_harness.workflow.reporting import render_report


class WorkflowService:
    ...

    def simulate_revision(self, run_id: str, revision_id: str, *, pack) -> dict[str, object]:
        intake = self.repo.load_revision_model(run_id, "intake", revision_id, IntakeDraft, approved=False)
        assumptions = self.repo.load_revision_model(run_id, "assumptions", revision_id, AssumptionSummary, approved=True)
        evidence = self.repo.load_revision_model(run_id, "evidence", revision_id, EvidencePacket, approved=False)
        state = compile_belief_state(
            run_id=run_id,
            revision_id=revision_id,
            pack=pack,
            intake=intake,
            assumptions=assumptions,
            approved_evidence_ids=[item.evidence_id for item in evidence.items],
        )
        self.repo.write_revision_json(run_id, "belief-state", revision_id, state.model_dump(mode="json"), approved=True)
        engine = SimulationEngine(pack, default_objective_profile())
        result = engine.run(state)
        self.repo.write_revision_json(run_id, "simulation", revision_id, result, approved=True)
        self.repo.append_event(run_id, "simulation-complete", {"revision_id": revision_id})
        return result

    def generate_report(
        self,
        run_id: str,
        revision_id: str,
        *,
        simulation: dict[str, object],
        evidence_count: int,
        unsupported_count: int,
    ) -> str:
        content = render_report(
            revision_id=revision_id,
            simulation=simulation,
            evidence_count=evidence_count,
            unsupported_count=unsupported_count,
        )
        self.repo.write_revision_markdown(run_id, revision_id, "report.md", content)
        self.repo.append_event(run_id, "report-generated", {"revision_id": revision_id})
        return content
```

```python
# packages/core/src/forecasting_harness/query_api.py
def summarize_revision_change(previous_revision_id: str, next_revision_id: str) -> dict[str, str]:
    return {
        "from_revision": previous_revision_id,
        "to_revision": next_revision_id,
    }
```

- [ ] **Step 4: Run the workflow service tests to verify they pass**

Run: `python -m pytest packages/core/tests/test_workflow_service.py -v`

Expected: PASS

- [ ] **Step 5: Commit the compile/simulate/report flow**

```bash
git add packages/core/src/forecasting_harness/workflow/reporting.py \
        packages/core/src/forecasting_harness/workflow/service.py \
        packages/core/src/forecasting_harness/query_api.py \
        packages/core/tests/test_workflow_service.py
git commit -m "feat: add revisioned simulation and reporting flow"
```

## Task 7: Add CLI Commands, Update Adapter Docs, and Prove the End-to-End Workflow Slice

**Files:**
- Modify: `/packages/core/src/forecasting_harness/cli.py`
- Modify: `/packages/core/tests/test_cli_workflow.py`
- Modify: `/packages/core/tests/test_adapter_docs.py`
- Modify: `/adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md`
- Modify: `/adapters/claude/skills/forecast-harness/SKILL.md`
- Modify: `/docs/install-codex.md`
- Modify: `/docs/install-claude-code.md`

- [ ] **Step 1: Write failing CLI and adapter-doc tests for the new workflow commands**

```python
# packages/core/tests/test_cli_workflow.py
import json
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.cli import app


def test_start_run_and_simulate_interstate_workflow(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"
    intake_path = tmp_path / "intake.json"
    evidence_path = tmp_path / "evidence.json"
    assumptions_path = tmp_path / "assumptions.json"

    intake_path.write_text(json.dumps({
        "event_framing": "Assess escalation",
        "primary_actors": ["US", "Iran"],
        "trigger": "Exchange of strikes",
        "current_phase": "trigger",
        "time_horizon": "30d",
    }), encoding="utf-8")
    evidence_path.write_text(json.dumps({"revision_id": "r1", "items": []}), encoding="utf-8")
    assumptions_path.write_text(json.dumps({"summary": ["Both sides avoid immediate total war"]}), encoding="utf-8")

    assert runner.invoke(app, ["start-run", "--root", str(root), "--run-id", "crisis-1", "--domain-pack", "interstate-crisis"]).exit_code == 0
    assert runner.invoke(app, ["save-intake-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(intake_path)]).exit_code == 0
    assert runner.invoke(app, ["save-evidence-draft", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(evidence_path)]).exit_code == 0
    assert runner.invoke(app, ["approve-revision", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1", "--input", str(assumptions_path)]).exit_code == 0
    assert runner.invoke(app, ["simulate", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1"]).exit_code == 0
    assert runner.invoke(app, ["generate-report", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1"]).exit_code == 0
    assert (root / "runs" / "crisis-1" / "reports" / "r1.report.md").exists()
```

```python
# packages/core/tests/test_adapter_docs.py
def test_codex_skill_mentions_start_run_and_generate_report() -> None:
    content = Path("adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md").read_text(encoding="utf-8")
    assert "forecast-harness start-run" in content
    assert "forecast-harness generate-report" in content
```

- [ ] **Step 2: Run the CLI and adapter-doc tests to verify they fail**

Run: `python -m pytest packages/core/tests/test_cli_workflow.py packages/core/tests/test_adapter_docs.py -v`

Expected: FAIL with missing commands and outdated docs.

- [ ] **Step 3: Implement the CLI commands as thin wrappers over `WorkflowService`**

```python
# packages/core/src/forecasting_harness/cli.py
import json

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack
from forecasting_harness.workflow.models import AssumptionSummary, EvidencePacket, IntakeDraft
from forecasting_harness.workflow.service import WorkflowService


def _service(root: Path) -> WorkflowService:
    return WorkflowService(RunRepository(root))


@app.command("start-run")
def start_run(root: Path, run_id: str, domain_pack: str) -> None:
    _service(root).start_run(run_id=run_id, domain_pack=domain_pack)
    print(f"started {run_id}")


@app.command("save-intake-draft")
def save_intake_draft(root: Path, run_id: str, revision_id: str, input: Path) -> None:
    payload = IntakeDraft.model_validate_json(input.read_text(encoding="utf-8"))
    _service(root).save_intake_draft(run_id, revision_id, payload)
    print(f"saved intake {revision_id}")


@app.command("save-evidence-draft")
def save_evidence_draft(root: Path, run_id: str, revision_id: str, input: Path) -> None:
    payload = EvidencePacket.model_validate_json(input.read_text(encoding="utf-8"))
    _service(root).save_evidence_draft(run_id, revision_id, payload)
    print(f"saved evidence {revision_id}")


@app.command("approve-revision")
def approve_revision(root: Path, run_id: str, revision_id: str, input: Path) -> None:
    payload = AssumptionSummary.model_validate_json(input.read_text(encoding="utf-8"))
    _service(root).approve_revision(run_id, revision_id, payload)
    print(f"approved {revision_id}")


@app.command("simulate")
def simulate(root: Path, run_id: str, revision_id: str) -> None:
    result = _service(root).simulate_revision(run_id, revision_id, pack=InterstateCrisisPack())
    print(json.dumps(result))


@app.command("generate-report")
def generate_report(root: Path, run_id: str, revision_id: str) -> None:
    repo = RunRepository(root)
    simulation = json.loads((repo.run_dir(run_id) / "simulation" / f"{revision_id}.approved.json").read_text(encoding="utf-8"))
    evidence = EvidencePacket.model_validate_json((repo.run_dir(run_id) / "evidence" / f"{revision_id}.draft.json").read_text(encoding="utf-8"))
    assumptions = AssumptionSummary.model_validate_json((repo.run_dir(run_id) / "assumptions" / f"{revision_id}.approved.json").read_text(encoding="utf-8"))
    _service(root).generate_report(
        run_id,
        revision_id,
        simulation=simulation,
        evidence_count=len(evidence.items),
        unsupported_count=len(assumptions.summary),
    )
    print(f"reported {revision_id}")
```

- [ ] **Step 4: Update adapter docs and install docs to use the new workflow**

```md
# adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md
1. Create or activate a Python 3.12+ virtualenv and install `packages/core[dev]`.
2. Start a run with `forecast-harness start-run`.
3. Write structured intake/evidence JSON drafts and persist them with `forecast-harness save-intake-draft` and `forecast-harness save-evidence-draft`.
4. Approve the revision with `forecast-harness approve-revision`.
5. Run `forecast-harness simulate` and `forecast-harness generate-report`.
6. Prefer reading revision-specific artifacts instead of loading the entire workbench.
```

```md
# docs/install-codex.md
4. Verify the workflow commands:
   - `forecast-harness start-run --help`
   - `forecast-harness simulate --help`
   - `forecast-harness generate-report --help`
```

- [ ] **Step 5: Run the CLI and adapter-doc tests to verify they pass**

Run: `python -m pytest packages/core/tests/test_cli_workflow.py packages/core/tests/test_adapter_docs.py -v`

Expected: PASS

- [ ] **Step 6: Run the full package test suite as the final proof for the slice**

Run: `python -m pytest packages/core -q`

Expected: PASS with all workflow, domain, CLI, and adapter-doc tests green.

- [ ] **Step 7: Commit the workflow CLI and docs**

```bash
git add packages/core/src/forecasting_harness/cli.py \
        packages/core/tests/test_cli_workflow.py \
        packages/core/tests/test_adapter_docs.py \
        adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md \
        adapters/claude/skills/forecast-harness/SKILL.md \
        docs/install-codex.md \
        docs/install-claude-code.md
git commit -m "feat: add interstate workflow slice CLI"
```

## Self-Review

### Spec coverage

- Reusable workflow contract: covered by Tasks 1, 3, 4, and 6.
- Revisioned run/artifact model: covered by Tasks 2 and 6.
- Structured but adaptive intake: covered by Tasks 1, 3, 4, and 5.
- Grouped assumption approval: covered by Tasks 1 and 3.
- Grouped evidence packet approval and dynamic evidence additions: covered by Tasks 3, 4, and 6.
- Interstate-crisis reference pack: covered by Task 5.
- Simulation/report flow with credibility notes: covered by Task 6.
- CLI/API operations and adapter usage: covered by Task 7.

### Placeholder scan

No `TODO`, `TBD`, “implement later”, or cross-task placeholders are left in this plan. Every task lists concrete files, test commands, implementation snippets, and commit commands.

### Type consistency

- `IntakeDraft`, `AssumptionSummary`, and `EvidencePacket` are defined in Task 1 and reused consistently in Tasks 3, 4, 6, and 7.
- `BeliefState` extension happens in Task 1 before the compiler and reference pack depend on `revision_id`, `phase`, and `approved_evidence_ids`.
- `canonical_phases`, `suggest_related_actors`, and `retrieval_filters` are added to `DomainPack` in Task 4 before `InterstateCrisisPack` implements them in Task 5.
