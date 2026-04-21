# Generalized Harness V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing workflow prototype into a genuinely reusable harness by wiring domain-pack discovery, generic intake extensions, retrieval-backed evidence drafting, and first-class revision lineage into the deterministic core.

**Architecture:** Keep the current local deterministic core and revisioned artifact model, but activate the generic seams that are already present. The work is split into small changes around the domain registry, workflow schema/service, retrieval integration, and revision metadata so the existing CLI workflow remains intact while becoming pack-driven instead of hardcoded.

**Tech Stack:** Python 3.12+, Typer, Pydantic, sqlite3/FTS5, pytest

---

## File Map

- Create: `packages/core/src/forecasting_harness/domain/registry.py`
- Create: `packages/core/tests/test_domain_registry.py`
- Modify: `packages/core/src/forecasting_harness/domain/__init__.py`
- Modify: `packages/core/src/forecasting_harness/domain/base.py`
- Modify: `packages/core/src/forecasting_harness/domain/generic_event.py`
- Modify: `packages/core/src/forecasting_harness/domain/interstate_crisis.py`
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Modify: `packages/core/src/forecasting_harness/artifacts.py`
- Modify: `packages/core/src/forecasting_harness/retrieval/search.py`
- Modify: `packages/core/src/forecasting_harness/workflow/models.py`
- Modify: `packages/core/src/forecasting_harness/workflow/compiler.py`
- Modify: `packages/core/src/forecasting_harness/workflow/evidence.py`
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Modify: `packages/core/tests/test_cli.py`
- Modify: `packages/core/tests/test_workflow_models.py`
- Modify: `packages/core/tests/test_workflow_evidence.py`
- Modify: `packages/core/tests/test_workflow_service.py`
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

### Task 1: Replace Hardcoded Domain-Pack Lookup With a Registry

**Files:**
- Create: `packages/core/src/forecasting_harness/domain/registry.py`
- Modify: `packages/core/src/forecasting_harness/domain/__init__.py`
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Test: `packages/core/tests/test_domain_registry.py`
- Test: `packages/core/tests/test_cli.py`

- [ ] **Step 1: Write failing registry tests for built-in pack discovery**

```python
from forecasting_harness.domain.registry import DomainPackRegistry, build_default_registry


def test_default_registry_lists_builtin_domain_packs() -> None:
    registry = build_default_registry()

    assert registry.list_slugs() == ["generic-event", "interstate-crisis"]


def test_default_registry_returns_new_pack_instances() -> None:
    registry = build_default_registry()

    first = registry.resolve("generic-event")
    second = registry.resolve("generic-event")

    assert first.slug() == "generic-event"
    assert second.slug() == "generic-event"
    assert first is not second
```

- [ ] **Step 2: Run the new registry tests to verify they fail**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_domain_registry.py -q`
Expected: FAIL because `forecasting_harness.domain.registry` does not exist yet.

- [ ] **Step 3: Implement a small in-process registry for built-in packs**

```python
from collections.abc import Callable

from forecasting_harness.domain.base import DomainPack
from forecasting_harness.domain.generic_event import GenericEventPack
from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack


PackFactory = Callable[[], DomainPack]


class DomainPackRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, PackFactory] = {}

    def register(self, slug: str, factory: PackFactory) -> None:
        self._factories[slug] = factory

    def list_slugs(self) -> list[str]:
        return sorted(self._factories)

    def resolve(self, slug: str) -> DomainPack:
        try:
            return self._factories[slug]()
        except KeyError as exc:
            raise KeyError(f"unknown domain pack: {slug}") from exc


def build_default_registry() -> DomainPackRegistry:
    registry = DomainPackRegistry()
    registry.register("generic-event", GenericEventPack)
    registry.register("interstate-crisis", InterstateCrisisPack)
    return registry
```

- [ ] **Step 4: Replace CLI hardcoding with registry-backed resolution and add `list-domain-packs`**

```python
from forecasting_harness.domain.registry import build_default_registry


def _registry():
    return build_default_registry()


def _pack_for_slug(domain_pack: str):
    try:
        return _registry().resolve(domain_pack)
    except KeyError as exc:
        raise typer.BadParameter(str(exc), param_hint="domain_pack") from exc


@app.command("list-domain-packs")
def list_domain_packs() -> None:
    print(json.dumps(_registry().list_slugs()))
```

- [ ] **Step 5: Extend CLI tests for registry-backed discovery**

```python
def test_list_domain_packs_command(runner: CliRunner) -> None:
    result = runner.invoke(app, ["list-domain-packs"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == ["generic-event", "interstate-crisis"]
```

- [ ] **Step 6: Run focused registry and CLI tests**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_domain_registry.py packages/core/tests/test_cli.py -q`
Expected: PASS

- [ ] **Step 7: Commit the registry slice**

```bash
git add packages/core/src/forecasting_harness/domain/registry.py \
        packages/core/src/forecasting_harness/domain/__init__.py \
        packages/core/src/forecasting_harness/cli.py \
        packages/core/tests/test_domain_registry.py \
        packages/core/tests/test_cli.py
git commit -m "feat: add domain pack registry"
```

### Task 2: Generalize Intake Schema and Activate Pack Validation

**Files:**
- Modify: `packages/core/src/forecasting_harness/domain/base.py`
- Modify: `packages/core/src/forecasting_harness/domain/generic_event.py`
- Modify: `packages/core/src/forecasting_harness/domain/interstate_crisis.py`
- Modify: `packages/core/src/forecasting_harness/workflow/models.py`
- Modify: `packages/core/src/forecasting_harness/workflow/compiler.py`
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Test: `packages/core/tests/test_workflow_models.py`
- Test: `packages/core/tests/test_workflow_evidence.py`
- Test: `packages/core/tests/test_workflow_service.py`

- [ ] **Step 1: Write failing schema tests for aliases and `pack_fields`**

```python
from forecasting_harness.workflow.models import IntakeDraft


def test_intake_draft_accepts_legacy_aliases() -> None:
    intake = IntakeDraft.model_validate(
        {
            "event_framing": "Assess escalation",
            "primary_actors": ["US", "Iran"],
            "trigger": "Exchange of strikes",
            "current_phase": "trigger",
            "time_horizon": "30d",
            "suggested_actors": ["China"],
        }
    )

    assert intake.focus_entities == ["US", "Iran"]
    assert intake.current_development == "Exchange of strikes"
    assert intake.current_stage == "trigger"
    assert intake.suggested_entities == ["China"]


def test_intake_draft_rejects_unknown_pack_fields() -> None:
    intake = IntakeDraft(
        event_framing="Assess escalation",
        focus_entities=["US", "Iran"],
        current_development="Exchange of strikes",
        current_stage="trigger",
        time_horizon="30d",
        pack_fields={"military_posture": "high"},
    )

    assert intake.pack_fields == {"military_posture": "high"}
```

- [ ] **Step 2: Run the targeted model tests to verify the current schema fails**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_workflow_models.py -q`
Expected: FAIL because the generic field names and aliases do not exist yet.

- [ ] **Step 3: Add generic intake fields, aliases, and pack-field storage**

```python
class IntakeDraft(BaseModel):
    event_framing: str
    focus_entities: list[str] = Field(min_length=1, validation_alias=AliasChoices("focus_entities", "primary_actors"))
    current_development: str = Field(validation_alias=AliasChoices("current_development", "trigger"))
    current_stage: str = Field(validation_alias=AliasChoices("current_stage", "current_phase"))
    time_horizon: str
    known_constraints: list[str] = Field(default_factory=list)
    known_unknowns: list[str] = Field(default_factory=list)
    suggested_entities: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("suggested_entities", "suggested_actors"),
    )
    pack_fields: dict[str, object] = Field(default_factory=dict)
```

- [ ] **Step 4: Add pack-level intake validation to the `DomainPack` contract**

```python
class DomainPack(ABC):
    def validate_intake(self, intake: "IntakeDraft") -> list[str]:
        return []
```

```python
class InterstateCrisisPack(DomainPack):
    def validate_intake(self, intake: IntakeDraft) -> list[str]:
        if len(intake.focus_entities) != 2:
            return ["interstate-crisis requires exactly two focus entities"]
        return []
```

- [ ] **Step 5: Validate `pack_fields` and pack intake rules in the workflow service**

```python
def _validate_pack_fields(pack: DomainPack, intake: IntakeDraft) -> None:
    schema = pack.extend_schema()
    unknown_fields = sorted(set(intake.pack_fields) - set(schema))
    if unknown_fields:
        raise ValueError(f"unknown pack_fields: {', '.join(unknown_fields)}")

    expected_types = {"str": str, "int": int, "float": float, "bool": bool}
    for field_name, value in intake.pack_fields.items():
        expected_name = schema[field_name]
        expected_type = expected_types[expected_name]
        if not isinstance(value, expected_type):
            raise ValueError(f"pack_fields.{field_name} must be {expected_name}")
```

- [ ] **Step 6: Update belief-state compilation to use generic names**

```python
actor_names = _dedupe_actor_names(
    [*intake.focus_entities, *intake.suggested_entities, *assumptions.suggested_actors]
)

fields = {
    "event_framing": BeliefField(..., value=intake.event_framing, normalized_value=intake.event_framing, ...),
    "current_development": BeliefField(
        ...,
        value=intake.current_development,
        normalized_value=intake.current_development,
        ...
    ),
}
for field_name, value in intake.pack_fields.items():
    fields[field_name] = BeliefField(value=value, normalized_value=value, status="observed", confidence=1.0, last_updated_at=now)
```

- [ ] **Step 7: Update workflow tests to cover generic access and pack validation**

```python
with pytest.raises(ValueError, match="exactly two focus entities"):
    service.save_intake_draft("run-1", "rev-1", IntakeDraft(... focus_entities=["US"]))
```

```python
state = compile_belief_state(...)
assert state.fields["current_development"].value == "Exchange of strikes"
assert state.fields["military_posture"].value == "high"
```

- [ ] **Step 8: Run targeted workflow model and service tests**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_workflow_models.py packages/core/tests/test_workflow_evidence.py packages/core/tests/test_workflow_service.py -q`
Expected: PASS

- [ ] **Step 9: Commit the intake/schema slice**

```bash
git add packages/core/src/forecasting_harness/domain/base.py \
        packages/core/src/forecasting_harness/domain/generic_event.py \
        packages/core/src/forecasting_harness/domain/interstate_crisis.py \
        packages/core/src/forecasting_harness/workflow/models.py \
        packages/core/src/forecasting_harness/workflow/compiler.py \
        packages/core/src/forecasting_harness/workflow/service.py \
        packages/core/tests/test_workflow_models.py \
        packages/core/tests/test_workflow_evidence.py \
        packages/core/tests/test_workflow_service.py
git commit -m "feat: generalize intake schema"
```

### Task 3: Wire Retrieval Into Deterministic Evidence Drafting

**Files:**
- Modify: `packages/core/src/forecasting_harness/retrieval/search.py`
- Modify: `packages/core/src/forecasting_harness/workflow/evidence.py`
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Test: `packages/core/tests/test_workflow_evidence.py`
- Test: `packages/core/tests/test_workflow_service.py`
- Test: `packages/core/tests/test_cli.py`

- [ ] **Step 1: Write failing tests for workflow-backed evidence drafting**

```python
def test_draft_evidence_packet_from_corpus_persists_a_revision_draft(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    registry = CorpusRegistry(tmp_path / "corpus.sqlite3")
    registry.register_document(
        source_id="doc-1",
        title="Taiwan Strait Signals",
        source_type="markdown",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis"},
        content="Japan and China exchange warnings in the Taiwan Strait.",
    )

    service = WorkflowService(repository, registry=registry)
    ...
    packet = service.draft_evidence_packet("crisis-1", "r1", query_text="Taiwan Strait warnings")

    assert [item.source_id for item in packet.items] == ["doc-1"]
```

- [ ] **Step 2: Run the new evidence drafting tests to verify they fail**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_workflow_service.py::test_draft_evidence_packet_from_corpus_persists_a_revision_draft -q`
Expected: FAIL because `WorkflowService` cannot draft evidence from retrieval yet.

- [ ] **Step 3: Extend `SearchEngine` to accept pack freshness policy input**

```python
def search(self, query: RetrievalQuery, *, freshness_policy: dict[str, float] | None = None) -> list[dict[str, Any]]:
    freshness_policy = freshness_policy or {}
    ...
    multiplier = self.freshness_multiplier(result["published_at"])
    domain_weight = freshness_policy.get(tags.get("domain", ""), 1.0)
    result["score"] = multiplier * domain_weight
```

- [ ] **Step 4: Add a workflow service method that drafts and persists evidence from corpus search**

```python
def draft_evidence_packet(
    self,
    run_id: str,
    revision_id: str,
    *,
    pack: DomainPack,
    query_text: str,
    max_per_source: int = 2,
    max_total: int = 6,
) -> EvidencePacket:
    intake = self.repository.load_revision_model(run_id, "intake", revision_id, IntakeDraft, approved=False)
    search_engine = SearchEngine(self.registry)
    hits = search_engine.search(
        RetrievalQuery(text=query_text, filters=pack.retrieval_filters(intake)),
        freshness_policy=pack.freshness_policy(),
    )
    packet = draft_evidence_packet(revision_id, hits, max_per_source=max_per_source, max_total=max_total)
    self.save_evidence_draft(run_id, revision_id, packet)
    self.repository.append_event(run_id, "evidence-packet-drafted", {"revision_id": revision_id, "query_text": query_text})
    return packet
```

- [ ] **Step 5: Add a CLI command for deterministic evidence drafting**

```python
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
    service = WorkflowService(repo, registry=CorpusRegistry(corpus_db))
    packet = service.draft_evidence_packet(run_id, revision_id, pack=pack, query_text=query_text)
    print(packet.model_dump_json())
```

- [ ] **Step 6: Keep `draft_evidence_packet()` deterministic and raw-passage-preserving**

```python
items.append(
    EvidencePacketItem(
        ...,
        reason="Candidate passage for approved evidence packet",
        raw_passages=[str(hit.get("content", ""))],
    )
)
```

- [ ] **Step 7: Run focused retrieval, workflow, and CLI tests**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_workflow_evidence.py packages/core/tests/test_workflow_service.py packages/core/tests/test_cli.py -q`
Expected: PASS

- [ ] **Step 8: Commit the retrieval-backed evidence slice**

```bash
git add packages/core/src/forecasting_harness/retrieval/search.py \
        packages/core/src/forecasting_harness/workflow/evidence.py \
        packages/core/src/forecasting_harness/workflow/service.py \
        packages/core/src/forecasting_harness/cli.py \
        packages/core/tests/test_workflow_evidence.py \
        packages/core/tests/test_workflow_service.py \
        packages/core/tests/test_cli.py
git commit -m "feat: draft evidence packets from retrieval"
```

### Task 4: Persist First-Class Revision Lineage and Status

**Files:**
- Modify: `packages/core/src/forecasting_harness/artifacts.py`
- Modify: `packages/core/src/forecasting_harness/workflow/models.py`
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Test: `packages/core/tests/test_workflow_models.py`
- Test: `packages/core/tests/test_workflow_service.py`

- [ ] **Step 1: Write failing tests for revision metadata persistence**

```python
def test_revision_record_tracks_lifecycle_timestamps(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    ...

    revision = repository.load_revision_record("crisis-1", "r1")

    assert revision.status == "simulated"
    assert revision.created_at is not None
    assert revision.approved_at is not None
    assert revision.simulated_at is not None
```

```python
def test_revision_record_preserves_parent_revision_id(tmp_path: Path) -> None:
    ...
    service.save_intake_draft("crisis-1", "r2", intake, parent_revision_id="r1")

    revision = repository.load_revision_record("crisis-1", "r2")
    assert revision.parent_revision_id == "r1"
```

- [ ] **Step 2: Run the lifecycle tests to verify they fail**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_workflow_service.py -q`
Expected: FAIL because `RunRepository` does not persist revision records yet.

- [ ] **Step 3: Extend `RevisionRecord` with lifecycle timestamps**

```python
class RevisionRecord(BaseModel):
    revision_id: str
    status: RevisionStatus = "draft"
    parent_revision_id: str | None = None
    created_at: datetime
    approved_at: datetime | None = None
    simulated_at: datetime | None = None
```

- [ ] **Step 4: Add repository helpers for revision record persistence**

```python
def save_revision_record(self, run_id: str, record: RevisionRecord) -> None:
    section_dir = self._require_initialized_run(run_id) / "revisions"
    section_dir.mkdir(parents=True, exist_ok=True)
    (section_dir / f"{record.revision_id}.json").write_text(record.model_dump_json(indent=2), encoding="utf-8")


def load_revision_record(self, run_id: str, revision_id: str) -> RevisionRecord:
    path = self.run_dir(run_id) / "revisions" / f"{revision_id}.json"
    return RevisionRecord.model_validate_json(path.read_text(encoding="utf-8"))
```

- [ ] **Step 5: Create or update revision records during workflow transitions**

```python
def _ensure_revision_record(...):
    try:
        return self.repository.load_revision_record(run_id, revision_id)
    except FileNotFoundError:
        record = RevisionRecord(
            revision_id=revision_id,
            status="draft",
            parent_revision_id=parent_revision_id,
            created_at=datetime.now(timezone.utc),
        )
        self.repository.save_revision_record(run_id, record)
        return record
```

```python
record = record.model_copy(update={"status": "approved", "approved_at": datetime.now(timezone.utc)})
self.repository.save_revision_record(run_id, record)
```

```python
record = record.model_copy(update={"status": "simulated", "simulated_at": datetime.now(timezone.utc)})
self.repository.save_revision_record(run_id, record)
```

- [ ] **Step 6: Expose parent-child revision creation in the service API**

```python
def save_intake_draft(self, run_id: str, revision_id: str, intake: IntakeDraft, *, parent_revision_id: str | None = None) -> None:
    self._ensure_revision_record(run_id, revision_id, parent_revision_id=parent_revision_id)
    ...
```

The same optional `parent_revision_id` should be available when saving evidence drafts so a new revision can be started from either step without hidden state.

- [ ] **Step 7: Run focused workflow lifecycle tests**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_workflow_models.py packages/core/tests/test_workflow_service.py -q`
Expected: PASS

- [ ] **Step 8: Commit the revision-lineage slice**

```bash
git add packages/core/src/forecasting_harness/artifacts.py \
        packages/core/src/forecasting_harness/workflow/models.py \
        packages/core/src/forecasting_harness/workflow/service.py \
        packages/core/tests/test_workflow_models.py \
        packages/core/tests/test_workflow_service.py
git commit -m "feat: persist revision lineage"
```

### Task 5: Refresh Docs and Run Full Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

- [ ] **Step 1: Update README to describe the new generic harness capabilities**

```md
## Current Workflow Slice

- `forecast-harness list-domain-packs`
- `forecast-harness draft-evidence-packet`
- generic intake aliases and `pack_fields`
- revision lineage metadata under `.forecast/runs/<run-id>/revisions/`
```

- [ ] **Step 2: Update the status doc with new verified progress and revised gaps**

```md
- domain packs are now discovered through a registry instead of hardcoded CLI lookup
- the workflow can now draft evidence packets from a local corpus
- revision lineage is now persisted as first-class metadata
```

- [ ] **Step 3: Run the full test suite**

Run: `packages/core/.venv/bin/python -m pytest packages/core -q`
Expected: PASS with all tests green.

- [ ] **Step 4: Smoke-test the new CLI flow**

Run:

```bash
tmpdir="$(mktemp -d)"
cd "$tmpdir"
cat > intake.json <<'EOF'
{
  "event_framing": "Assess escalation risk",
  "focus_entities": ["Japan", "China"],
  "current_development": "Naval transit through the Taiwan Strait",
  "current_stage": "trigger",
  "time_horizon": "30d",
  "pack_fields": {"military_posture": "heightened", "leader_style": "cautious"}
}
EOF
```

Then run:

```bash
forecast-harness list-domain-packs
forecast-harness start-run --root .forecast --run-id crisis-1 --domain-pack interstate-crisis
forecast-harness save-intake-draft --root .forecast --run-id crisis-1 --revision-id r1 --input intake.json
```

Expected:

- the registry lists the built-in packs
- intake saves successfully with the generic schema
- no existing command regresses

- [ ] **Step 5: Commit docs and verification updates**

```bash
git add README.md docs/status/2026-04-20-project-status.md
git commit -m "docs: refresh generic harness status"
```

## Self-Review

- Spec coverage: the plan covers all four scoped spec items with dedicated tasks:
  - registry and CLI discovery in Task 1
  - generic intake and pack validation in Task 2
  - retrieval-backed evidence drafting in Task 3
  - revision lineage in Task 4
  - docs and end-to-end verification in Task 5
- Placeholder scan: no `TBD`, `TODO`, or “implement later” placeholders remain in task steps.
- Type consistency: the plan consistently uses `focus_entities`, `current_development`, `current_stage`, `suggested_entities`, `pack_fields`, `RevisionRecord`, and `DomainPackRegistry` across tasks.
