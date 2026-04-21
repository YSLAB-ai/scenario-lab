# Guided Workflow V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic adapter-facing guidance and summary commands so Codex/Claude integrations can drive the forecasting workflow without hand-authoring JSON or loading raw run artifacts directly.

**Architecture:** Build thin, deterministic guidance methods on top of the existing saved run/revision artifacts. The workflow service will compute intake guidance, grouped approval packets, and narrow run/revision summaries on demand, and the CLI will expose them as JSON-returning commands. Adapter docs then switch to the new guided sequence rather than the current raw-artifact sequence.

**Tech Stack:** Python 3.12+, Typer, Pydantic, pytest

---

## File Map

- Modify: `packages/core/src/forecasting_harness/query_api.py`
- Modify: `packages/core/src/forecasting_harness/workflow/models.py`
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Modify: `packages/core/tests/test_workflow_models.py`
- Modify: `packages/core/tests/test_workflow_service.py`
- Modify: `packages/core/tests/test_cli_workflow.py`
- Modify: `packages/core/tests/test_adapter_docs.py`
- Modify: `docs/install-codex.md`
- Modify: `docs/install-claude-code.md`
- Modify: `adapters/claude/skills/forecast-harness/SKILL.md`
- Create: `adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md`
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

### Task 1: Add Guidance and Summary Models

**Files:**
- Modify: `packages/core/src/forecasting_harness/workflow/models.py`
- Modify: `packages/core/src/forecasting_harness/query_api.py`
- Modify: `packages/core/tests/test_workflow_models.py`

- [ ] **Step 1: Write failing model tests for the new adapter-facing payloads**

```python
from forecasting_harness.workflow.models import ApprovalPacket, IntakeGuidance, RevisionSummary, RunSummary


def test_intake_guidance_preserves_pack_assistance_fields() -> None:
    guidance = IntakeGuidance(
        domain_pack="interstate-crisis",
        current_stage="trigger",
        canonical_stages=["trigger", "signaling"],
        suggested_entities=["China"],
        follow_up_questions=["Which outside actor has leverage?"],
        pack_field_schema={"military_posture": "str"},
        default_objective_profile={"name": "balanced"},
    )

    assert guidance.domain_pack == "interstate-crisis"
    assert guidance.suggested_entities == ["China"]


def test_run_summary_preserves_revision_order() -> None:
    summary = RunSummary(
        run_id="crisis-1",
        domain_pack="interstate-crisis",
        current_revision_id="r2",
        revisions=[{"revision_id": "r1", "status": "approved"}, {"revision_id": "r2", "status": "simulated"}],
    )

    assert [item["revision_id"] for item in summary.revisions] == ["r1", "r2"]
```

- [ ] **Step 2: Run the new model tests to verify they fail**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_workflow_models.py -q`
Expected: FAIL because the new guidance/summary models do not exist yet.

- [ ] **Step 3: Add the new payload models**

```python
class IntakeGuidance(BaseModel):
    domain_pack: str
    current_stage: str
    canonical_stages: list[str] = Field(default_factory=list)
    suggested_entities: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    pack_field_schema: dict[str, str] = Field(default_factory=dict)
    default_objective_profile: dict[str, object]
```

```python
class ApprovalPacket(BaseModel):
    revision_id: str
    intake_summary: dict[str, object]
    assumption_summary: list[str] = Field(default_factory=list)
    objective_profile: dict[str, object]
    evidence_summary: list[dict[str, object]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
```

```python
class RunSummary(BaseModel):
    run_id: str
    domain_pack: str
    current_revision_id: str | None = None
    revisions: list[dict[str, object]] = Field(default_factory=list)


class RevisionSummary(BaseModel):
    revision_id: str
    status: RevisionStatus
    parent_revision_id: str | None = None
    evidence_item_count: int = 0
    assumption_count: int = 0
    top_branches: list[dict[str, object]] = Field(default_factory=list)
    available_sections: list[str] = Field(default_factory=list)
```

- [ ] **Step 4: Add query helpers for narrow summary composition**

```python
def summarize_revision_change(previous_revision_id: str, next_revision_id: str) -> dict[str, str]:
    return {"from_revision": previous_revision_id, "to_revision": next_revision_id}
```

Keep `query_api.py` focused on narrow JSON-friendly helpers; do not move workflow logic there.

- [ ] **Step 5: Run focused model tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_workflow_models.py -q`
Expected: PASS

- [ ] **Step 6: Commit the new payload models**

```bash
git add packages/core/src/forecasting_harness/workflow/models.py \
        packages/core/src/forecasting_harness/query_api.py \
        packages/core/tests/test_workflow_models.py
git commit -m "feat: add guided workflow models"
```

### Task 2: Add Workflow Service Methods for Guidance and Narrow Summaries

**Files:**
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Modify: `packages/core/tests/test_workflow_service.py`

- [ ] **Step 1: Write failing service tests for intake guidance and approval packets**

```python
def test_draft_intake_guidance_uses_domain_pack_hooks(tmp_path: Path) -> None:
    ...
    guidance = service.draft_intake_guidance("crisis-1", "r1")

    assert guidance.domain_pack == "interstate-crisis"
    assert guidance.current_stage == "trigger"
    assert "China" in guidance.suggested_entities
    assert "military_posture" in guidance.pack_field_schema
```

```python
def test_draft_approval_packet_summarizes_evidence_and_warnings(tmp_path: Path) -> None:
    ...
    packet = service.draft_approval_packet("crisis-1", "r1")

    assert packet.revision_id == "r1"
    assert packet.evidence_summary[0]["source_id"] == "source-0"
    assert "known unknowns remain unresolved" in packet.warnings
```

- [ ] **Step 2: Write failing service tests for run and revision summaries**

```python
def test_summarize_run_returns_revision_statuses(tmp_path: Path) -> None:
    ...
    summary = service.summarize_run("crisis-1")

    assert summary.current_revision_id == "r2"
    assert [item["status"] for item in summary.revisions] == ["simulated", "approved"]
```

```python
def test_summarize_revision_returns_available_sections_and_top_branches(tmp_path: Path) -> None:
    ...
    summary = service.summarize_revision("crisis-1", "r1")

    assert "intake" in summary.available_sections
    assert summary.top_branches[0]["label"] == "Signal resolve"
```

- [ ] **Step 3: Run the targeted workflow service tests to verify they fail**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_workflow_service.py -q`
Expected: FAIL because these service methods do not exist yet.

- [ ] **Step 4: Implement `draft_intake_guidance()`**

```python
def draft_intake_guidance(self, run_id: str, revision_id: str) -> IntakeGuidance:
    intake = self.repository.load_revision_model(run_id, "intake", revision_id, IntakeDraft, approved=False)
    pack = self._pack_for_run(run_id)
    profile = pack.default_objective_profile()
    return IntakeGuidance(
        domain_pack=pack.slug(),
        current_stage=intake.current_stage,
        canonical_stages=pack.canonical_phases(),
        suggested_entities=pack.suggest_related_actors(intake),
        follow_up_questions=pack.suggest_questions(),
        pack_field_schema=pack.extend_schema(),
        default_objective_profile=profile.model_dump(mode="json"),
    )
```

- [ ] **Step 5: Implement `draft_approval_packet()`**

```python
def draft_approval_packet(self, run_id: str, revision_id: str) -> ApprovalPacket:
    intake = self.repository.load_revision_model(run_id, "intake", revision_id, IntakeDraft, approved=False)
    evidence = self.repository.load_revision_model(run_id, "evidence", revision_id, EvidencePacket, approved=False)
    pack = self._pack_for_run(run_id)
    profile = pack.default_objective_profile()
    warnings = []
    if not evidence.items:
        warnings.append("no evidence drafted yet")
    if intake.known_unknowns:
        warnings.append("known unknowns remain unresolved")
    if not intake.suggested_entities:
        warnings.append("no suggested entities included yet")
    return ApprovalPacket(
        revision_id=revision_id,
        intake_summary={...},
        assumption_summary=[...],
        objective_profile=profile.model_dump(mode="json"),
        evidence_summary=[...],
        warnings=warnings,
    )
```

Keep the assumption summary deterministic and explicitly derived from:
- `known_unknowns`
- zero-evidence state
- suggested entities outside the current focus set

- [ ] **Step 6: Implement `summarize_run()` and `summarize_revision()`**

```python
def summarize_run(self, run_id: str) -> RunSummary:
    run = self.repository.load_run_record(run_id)
    revisions = self.repository.list_revision_records(run_id)
    return RunSummary(
        run_id=run.run_id,
        domain_pack=run.domain_pack,
        current_revision_id=run.current_revision_id,
        revisions=[record.model_dump(mode="json") for record in revisions],
    )
```

```python
def summarize_revision(self, run_id: str, revision_id: str) -> RevisionSummary:
    record = self.repository.load_revision_record(run_id, revision_id)
    available_sections = [...]
    top_branches = summarize_top_branches(simulation["branches"]) if simulation exists else []
    return RevisionSummary(...)
```

Use the existing repository structure and `query_api.summarize_top_branches()` rather than reimplementing branch ranking in the service.

- [ ] **Step 7: Run focused service tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_workflow_service.py -q`
Expected: PASS

- [ ] **Step 8: Commit the workflow guidance slice**

```bash
git add packages/core/src/forecasting_harness/workflow/service.py \
        packages/core/tests/test_workflow_service.py
git commit -m "feat: add guided workflow summaries"
```

### Task 3: Expose the Guidance Surface Through the CLI

**Files:**
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Modify: `packages/core/tests/test_cli_workflow.py`

- [ ] **Step 1: Write failing CLI tests for the new commands**

```python
def test_draft_intake_guidance_command_returns_pack_guidance(tmp_path: Path) -> None:
    ...
    result = runner.invoke(app, ["draft-intake-guidance", ...])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["domain_pack"] == "interstate-crisis"
```

```python
def test_draft_approval_packet_command_returns_grouped_summary(tmp_path: Path) -> None:
    ...
    assert payload["revision_id"] == "r1"
    assert "warnings" in payload
```

```python
def test_summarize_run_and_revision_commands_return_narrow_json(tmp_path: Path) -> None:
    ...
    assert run_payload["current_revision_id"] == "r1"
    assert revision_payload["revision_id"] == "r1"
```

- [ ] **Step 2: Run the CLI tests to verify they fail**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_cli_workflow.py -q`
Expected: FAIL because the commands do not exist yet.

- [ ] **Step 3: Add the new commands**

```python
@app.command("draft-intake-guidance")
def draft_intake_guidance(...):
    payload = _service(root).draft_intake_guidance(run_id, revision_id)
    print(payload.model_dump_json())
```

```python
@app.command("draft-approval-packet")
def draft_approval_packet(...):
    payload = _service(root).draft_approval_packet(run_id, revision_id)
    print(payload.model_dump_json())
```

```python
@app.command("summarize-run")
def summarize_run(...):
    payload = _service(root).summarize_run(run_id)
    print(payload.model_dump_json())
```

```python
@app.command("summarize-revision")
def summarize_revision(...):
    payload = _service(root).summarize_revision(run_id, revision_id)
    print(payload.model_dump_json())
```

- [ ] **Step 4: Run focused CLI tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_cli_workflow.py -q`
Expected: PASS

- [ ] **Step 5: Commit the CLI guidance slice**

```bash
git add packages/core/src/forecasting_harness/cli.py \
        packages/core/tests/test_cli_workflow.py
git commit -m "feat: add guided workflow commands"
```

### Task 4: Refresh Adapter Docs and Verify Guided Sequence

**Files:**
- Modify: `docs/install-codex.md`
- Modify: `docs/install-claude-code.md`
- Modify: `adapters/claude/skills/forecast-harness/SKILL.md`
- Create: `adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md`
- Modify: `packages/core/tests/test_adapter_docs.py`
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

- [ ] **Step 1: Write failing adapter-doc tests for the guided command sequence**

```python
assert "forecast-harness draft-intake-guidance" in codex_doc
assert "forecast-harness draft-approval-packet" in codex_doc
assert "forecast-harness summarize-run" in codex_doc
assert "forecast-harness summarize-revision" in codex_doc
```

Apply the same expectations to:
- Claude install docs
- Codex skill
- Claude skill

- [ ] **Step 2: Run the adapter-doc tests to verify they fail**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_adapter_docs.py -q`
Expected: FAIL because the docs do not mention the new sequence yet.

- [ ] **Step 3: Update install docs and skill stubs to the guided sequence**

The new recommended sequence should be:

```text
forecast-harness start-run
forecast-harness save-intake-draft
forecast-harness draft-intake-guidance
forecast-harness draft-evidence-packet
forecast-harness draft-approval-packet
forecast-harness approve-revision
forecast-harness simulate
forecast-harness summarize-run
forecast-harness summarize-revision
```

- [ ] **Step 4: Update README and the status note**

README should now describe the repo as supporting:
- guided workflow commands for adapters
- local corpus ingestion
- deterministic summaries for progressive disclosure

The status note should reflect:
- new guided workflow commands
- updated test count
- remaining gaps now shifting toward a real thread-native adapter and search realism

- [ ] **Step 5: Run the adapter-doc tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_adapter_docs.py -q`
Expected: PASS

- [ ] **Step 6: Commit the docs slice**

```bash
git add docs/install-codex.md \
        docs/install-claude-code.md \
        adapters/claude/skills/forecast-harness/SKILL.md \
        adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md \
        packages/core/tests/test_adapter_docs.py \
        README.md \
        docs/status/2026-04-20-project-status.md
git commit -m "docs: add guided adapter workflow docs"
```

### Task 5: Final Verification and Smoke Flow

**Files:**
- Modify: none expected

- [ ] **Step 1: Run the full test suite**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core -q`
Expected: PASS

- [ ] **Step 2: Smoke-test the guided workflow commands**

Run:

```bash
tmpdir="$(mktemp -d)"
cd "$tmpdir"
cat > intake.json <<'EOF'
{
  "event_framing": "Assess escalation risk",
  "focus_entities": ["US", "Iran"],
  "current_development": "Exchange of strikes",
  "current_stage": "trigger",
  "time_horizon": "30d"
}
EOF
PYTHONPATH="/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/guided-workflow-v1/packages/core/src" \
"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m forecasting_harness.cli start-run \
  --root .forecast \
  --run-id crisis-1 \
  --domain-pack interstate-crisis
PYTHONPATH="/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/guided-workflow-v1/packages/core/src" \
"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m forecasting_harness.cli save-intake-draft \
  --root .forecast \
  --run-id crisis-1 \
  --revision-id r1 \
  --input intake.json
PYTHONPATH="/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/guided-workflow-v1/packages/core/src" \
"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m forecasting_harness.cli draft-intake-guidance \
  --root .forecast \
  --run-id crisis-1 \
  --revision-id r1
PYTHONPATH="/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/guided-workflow-v1/packages/core/src" \
"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m forecasting_harness.cli summarize-run \
  --root .forecast \
  --run-id crisis-1
```

Expected:

- `draft-intake-guidance` returns suggested entities and follow-up questions
- `summarize-run` returns run and revision metadata without loading raw artifacts

- [ ] **Step 3: Commit only if the smoke flow exposes a fixable issue**

If smoke test stays green, no additional code commit is needed here.

## Self-Review

- Spec coverage: the plan covers every scoped part of the spec:
  - intake guidance
  - grouped approval packet
  - run/revision summaries
  - adapter docs and guided command sequence
- Placeholder scan: no `TBD`, `TODO`, or deferred “implement later” placeholders remain in task steps.
- Type consistency: the plan consistently uses `IntakeGuidance`, `ApprovalPacket`, `RunSummary`, `RevisionSummary`, `draft-intake-guidance`, `draft-approval-packet`, `summarize-run`, and `summarize-revision` across models, service methods, tests, and CLI commands.
