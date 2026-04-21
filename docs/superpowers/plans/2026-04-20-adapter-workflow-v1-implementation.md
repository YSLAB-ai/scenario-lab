# Adapter Workflow V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let Codex and Claude adapters drive the normal forecasting workflow without creating temporary JSON files for intake drafts, evidence curation, approvals, or revision updates.

**Architecture:** Extend the existing deterministic workflow service with two new adapter-facing operations: curate a draft evidence packet and fork a new draft revision from an approved parent. Then extend the CLI so the existing `save-intake-draft` and `approve-revision` commands support direct structured flags in addition to `--input`, and add dedicated commands for evidence curation and revision updates. Finally, refresh adapter docs to use the new direct-command path.

**Tech Stack:** Python 3.12+, Typer, Pydantic, pytest

---

## File Map

- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Modify: `packages/core/tests/test_workflow_service.py`
- Modify: `packages/core/tests/test_cli_workflow.py`
- Modify: `packages/core/tests/test_adapter_docs.py`
- Modify: `docs/install-codex.md`
- Modify: `docs/install-claude-code.md`
- Modify: `adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md`
- Modify: `adapters/claude/skills/forecast-harness/SKILL.md`
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

### Task 1: Add Adapter Workflow Service Operations

**Files:**
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Modify: `packages/core/tests/test_workflow_service.py`

- [ ] **Step 1: Write failing service tests for draft evidence curation**

Add tests that prove:

```python
def test_curate_evidence_draft_keeps_requested_ids_and_records_event() -> None:
    ...
    packet = service.curate_evidence_draft("crisis-1", "r1", ["r1-ev-2"])

    assert [item.evidence_id for item in packet.items] == ["r1-ev-2"]
    assert repository.appended_events[-1] == (
        "crisis-1",
        "evidence-curated",
        {"revision_id": "r1", "evidence_ids": ["r1-ev-2"]},
    )
```

```python
def test_curate_evidence_draft_rejects_unknown_ids() -> None:
    ...
    with pytest.raises(ValueError, match="unknown evidence ids"):
        service.curate_evidence_draft("crisis-1", "r1", ["missing-id"])
```

- [ ] **Step 2: Write failing service tests for revision update forking**

Add tests that prove:

```python
def test_begin_revision_update_copies_parent_artifacts_and_preserves_lineage() -> None:
    ...
    payload = service.begin_revision_update("crisis-1", "r2", parent_revision_id="r1")

    assert payload["revision_id"] == "r2"
    assert payload["parent_revision_id"] == "r1"
    assert payload["copied_sections"] == ["intake", "evidence"]
```

```python
def test_begin_revision_update_requires_approved_parent_sections() -> None:
    ...
    with pytest.raises(FileNotFoundError):
        service.begin_revision_update("crisis-1", "r2", parent_revision_id="r1")
```

- [ ] **Step 3: Run the targeted service tests to verify they fail**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_workflow_service.py -q`

Expected: FAIL because `curate_evidence_draft()` and `begin_revision_update()` do not exist yet.

- [ ] **Step 4: Implement `curate_evidence_draft()` in the workflow service**

Add a method that:

```python
def curate_evidence_draft(self, run_id: str, revision_id: str, evidence_ids: list[str]) -> EvidencePacket:
    packet = self.repository.load_revision_model(run_id, "evidence", revision_id, EvidencePacket, approved=False)
    items_by_id = {item.evidence_id: item for item in packet.items}
    unknown_ids = [evidence_id for evidence_id in evidence_ids if evidence_id not in items_by_id]
    if unknown_ids:
        raise ValueError(f"unknown evidence ids: {', '.join(unknown_ids)}")
    curated_items = [item for item in packet.items if item.evidence_id in evidence_ids]
    curated_packet = packet.model_copy(update={"items": curated_items})
    self.repository.write_revision_json(run_id, "evidence", revision_id, curated_packet.model_dump(mode="json"), approved=False)
    self.repository.append_event(run_id, "evidence-curated", {"revision_id": revision_id, "evidence_ids": evidence_ids})
    return curated_packet
```

Keep ordering stable from the existing packet rather than from the input list.

- [ ] **Step 5: Implement `begin_revision_update()` in the workflow service**

Add a method that:

```python
def begin_revision_update(self, run_id: str, revision_id: str, *, parent_revision_id: str) -> dict[str, object]:
    intake = self.repository.load_revision_model(run_id, "intake", parent_revision_id, IntakeDraft, approved=True)
    evidence = self.repository.load_revision_model(run_id, "evidence", parent_revision_id, EvidencePacket, approved=True)
    self.save_intake_draft(run_id, revision_id, intake, parent_revision_id=parent_revision_id)
    self.save_evidence_draft(run_id, revision_id, evidence.model_copy(update={"revision_id": revision_id}), parent_revision_id=parent_revision_id)
    self.repository.append_event(
        run_id,
        "revision-update-started",
        {"revision_id": revision_id, "parent_revision_id": parent_revision_id},
    )
    return {
        "revision_id": revision_id,
        "parent_revision_id": parent_revision_id,
        "copied_sections": ["intake", "evidence"],
    }
```

Do not copy assumptions, belief state, simulation, or reports.

- [ ] **Step 6: Run the targeted service tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_workflow_service.py -q`

Expected: PASS

- [ ] **Step 7: Commit the service changes**

```bash
git add packages/core/src/forecasting_harness/workflow/service.py \
        packages/core/tests/test_workflow_service.py
git commit -m "feat: add adapter workflow service operations"
```

### Task 2: Add Direct Adapter CLI Commands and Flag Modes

**Files:**
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Modify: `packages/core/tests/test_cli_workflow.py`

- [ ] **Step 1: Write failing CLI tests for direct intake flags**

Add a test that invokes:

```python
result = runner.invoke(
    app,
    [
        "save-intake-draft",
        "--root", str(root),
        "--run-id", "crisis-1",
        "--revision-id", "r1",
        "--event-framing", "Assess escalation risk",
        "--focus-entity", "Japan",
        "--focus-entity", "China",
        "--current-development", "Naval transit through the Taiwan Strait",
        "--current-stage", "trigger",
        "--time-horizon", "30d",
        "--known-unknown", "US response posture",
        "--suggested-entity", "United States",
        "--pack-field", "leader_style=hawkish",
    ],
)
```

and proves the draft file was written without an input file.

- [ ] **Step 2: Write failing CLI tests for direct approval flags**

Add a test that invokes:

```python
result = runner.invoke(
    app,
    [
        "approve-revision",
        "--root", str(root),
        "--run-id", "crisis-1",
        "--revision-id", "r1",
        "--assumption", "Both sides prefer limited signaling",
        "--suggested-actor", "United States",
        "--objective-profile-name", "balanced",
    ],
)
```

and proves the approved assumptions snapshot is created.

- [ ] **Step 3: Write failing CLI tests for evidence curation and revision updates**

Add tests that prove:

```python
result = runner.invoke(
    app,
    [
        "curate-evidence-draft",
        "--root", str(root),
        "--run-id", "crisis-1",
        "--revision-id", "r1",
        "--keep-evidence-id", "r1:doc-1:1",
    ],
)
```

returns a single selected evidence item.

And:

```python
result = runner.invoke(
    app,
    [
        "begin-revision-update",
        "--root", str(root),
        "--run-id", "crisis-1",
        "--parent-revision-id", "r1",
        "--revision-id", "r2",
    ],
)
```

returns the copied section summary and creates draft artifacts for `r2`.

- [ ] **Step 4: Run the targeted CLI workflow tests to verify they fail**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_cli_workflow.py -q`

Expected: FAIL because the CLI does not yet support these modes/commands.

- [ ] **Step 5: Add CLI helpers for structured intake and approval parsing**

In `cli.py`, add small deterministic helpers:

```python
def _parse_pack_fields(values: list[str] | None) -> dict[str, object]:
    ...

def _intake_from_flags(...) -> IntakeDraft:
    ...

def _assumptions_from_flags(...) -> AssumptionSummary:
    ...
```

Rules:
- if `--input` is present, use existing file behavior
- if `--input` is absent, require the flag-based required fields
- parse `pack-field` values with JSON scalar fallback, then string fallback

- [ ] **Step 6: Extend `save-intake-draft` and `approve-revision`**

Update the commands so they support both file and direct-flag mode without breaking existing invocations.

- [ ] **Step 7: Add `curate-evidence-draft` and `begin-revision-update` commands**

Expose the new workflow service methods as JSON-returning CLI commands.

- [ ] **Step 8: Run the targeted CLI workflow tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_cli_workflow.py -q`

Expected: PASS

- [ ] **Step 9: Commit the CLI changes**

```bash
git add packages/core/src/forecasting_harness/cli.py \
        packages/core/tests/test_cli_workflow.py
git commit -m "feat: add adapter workflow cli commands"
```

### Task 3: Refresh Adapter Docs and Status Notes

**Files:**
- Modify: `packages/core/tests/test_adapter_docs.py`
- Modify: `docs/install-codex.md`
- Modify: `docs/install-claude-code.md`
- Modify: `adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md`
- Modify: `adapters/claude/skills/forecast-harness/SKILL.md`
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

- [ ] **Step 1: Write failing adapter doc assertions for the new direct workflow**

Update `test_adapter_docs.py` so it requires the new commands:

- `forecast-harness curate-evidence-draft`
- `forecast-harness begin-revision-update`

And so it requires the docs to mention direct structured input rather than only file-backed input for routine adapter flow.

- [ ] **Step 2: Run the adapter doc test to verify it fails**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_adapter_docs.py -q`

Expected: FAIL because the docs do not mention the new commands yet.

- [ ] **Step 3: Update the install docs and skill docs**

Refresh both adapter paths to describe the new normal flow:

- start run
- save intake draft directly from structured adapter inputs
- draft intake guidance
- draft evidence packet
- curate evidence draft if needed
- approve revision directly from structured adapter inputs
- simulate
- summarize revision / summarize run
- begin revision update for reruns

Do not claim the flow is fully conversational yet.

- [ ] **Step 4: Update README and status note**

Refresh:
- current CLI command list
- verified current progress
- remaining gaps
- latest test count after final verification

- [ ] **Step 5: Run the adapter doc test**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_adapter_docs.py -q`

Expected: PASS

- [ ] **Step 6: Commit the doc refresh**

```bash
git add packages/core/tests/test_adapter_docs.py \
        docs/install-codex.md \
        docs/install-claude-code.md \
        adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md \
        adapters/claude/skills/forecast-harness/SKILL.md \
        README.md \
        docs/status/2026-04-20-project-status.md
git commit -m "docs: refresh adapter workflow guidance"
```

### Task 4: Full Verification and Fresh-Install Smoke Test

**Files:**
- No source changes expected

- [ ] **Step 1: Run the full test suite**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core -q`

Expected: PASS with an increased count above the current `117 passed`.

- [ ] **Step 2: Run a fresh Python 3.13 install smoke test using the direct adapter flow**

Run a clean smoke flow in a temporary directory that verifies:

- `pip install -e 'packages/core[dev]'`
- `forecast-harness ingest-file`
- `forecast-harness start-run`
- `forecast-harness save-intake-draft` using direct flags
- `forecast-harness draft-intake-guidance`
- `forecast-harness draft-evidence-packet`
- `forecast-harness curate-evidence-draft`
- `forecast-harness approve-revision` using direct flags
- `forecast-harness simulate`
- `forecast-harness summarize-revision`
- `forecast-harness summarize-run`
- `forecast-harness begin-revision-update`

Confirm the smoke run creates the expected revision artifacts for both the original and updated revision.

- [ ] **Step 3: Update the status note if the final verification output differs**

If the final passing test count or smoke-test facts differ from the current docs, refresh them before claiming completion.

- [ ] **Step 4: Commit any final verification-driven doc updates**

```bash
git add README.md docs/status/2026-04-20-project-status.md
git commit -m "docs: finalize adapter workflow status"
```
