# Conversation Adapter V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic conversation-turn state machine so Codex and Claude adapters can ask/show the right next thing in the forecasting workflow without inferring state from raw artifacts.

**Architecture:** Add a small `ConversationTurn` workflow payload, derive it from stored revision artifacts in the workflow service, expose it through a new CLI command, and then update the adapter docs to make `draft-conversation-turn` the standard “what next?” step after each mutation.

**Tech Stack:** Python 3.12+, Typer, Pydantic, pytest

---

## File Map

- Modify: `packages/core/src/forecasting_harness/workflow/models.py`
- Modify: `packages/core/src/forecasting_harness/workflow/__init__.py`
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Modify: `packages/core/tests/test_workflow_models.py`
- Modify: `packages/core/tests/test_workflow_service.py`
- Modify: `packages/core/tests/test_cli_workflow.py`
- Modify: `packages/core/tests/test_adapter_docs.py`
- Modify: `docs/install-codex.md`
- Modify: `docs/install-claude-code.md`
- Modify: `adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md`
- Modify: `adapters/claude/skills/forecast-harness/SKILL.md`
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

### Task 1: Add Conversation Turn Models

**Files:**
- Modify: `packages/core/src/forecasting_harness/workflow/models.py`
- Modify: `packages/core/src/forecasting_harness/workflow/__init__.py`
- Modify: `packages/core/tests/test_workflow_models.py`

- [ ] **Step 1: Write failing model tests**

Add a test like:

```python
def test_conversation_turn_captures_stage_and_context() -> None:
    turn = ConversationTurn(
        run_id="crisis-1",
        revision_id="r1",
        stage="approval",
        headline="Review approval packet",
        user_message="Evidence draft is ready.",
        recommended_command="forecast-harness approve-revision",
        available_sections=["intake", "evidence"],
        context={"revision_id": "r1"},
    )

    assert turn.stage == "approval"
    assert turn.context["revision_id"] == "r1"
```

- [ ] **Step 2: Run the model tests to verify they fail**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_workflow_models.py -q`

Expected: FAIL because `ConversationTurn` does not exist yet.

- [ ] **Step 3: Add the new model and export it**

Add:

```python
ConversationStage = Literal["intake", "evidence", "approval", "simulation", "report"]


class ConversationTurn(BaseModel):
    run_id: str
    revision_id: str
    stage: ConversationStage
    headline: str
    user_message: str
    recommended_command: str | None = None
    available_sections: list[str] = Field(default_factory=list)
    context: dict[str, object] = Field(default_factory=dict)
```

- [ ] **Step 4: Run the model tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_workflow_models.py -q`

Expected: PASS

- [ ] **Step 5: Commit the model changes**

```bash
git add packages/core/src/forecasting_harness/workflow/models.py \
        packages/core/src/forecasting_harness/workflow/__init__.py \
        packages/core/tests/test_workflow_models.py
git commit -m "feat: add conversation turn model"
```

### Task 2: Add Deterministic Conversation Turn Resolution

**Files:**
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Modify: `packages/core/tests/test_workflow_service.py`

- [ ] **Step 1: Write failing service tests for each stage**

Add tests for:

```python
def test_draft_conversation_turn_returns_intake_stage_when_revision_is_empty(...) -> None: ...
def test_draft_conversation_turn_returns_evidence_stage_from_intake_draft(...) -> None: ...
def test_draft_conversation_turn_returns_approval_stage_from_evidence_draft(...) -> None: ...
def test_draft_conversation_turn_returns_simulation_stage_from_approved_revision(...) -> None: ...
def test_draft_conversation_turn_returns_report_stage_from_simulated_revision(...) -> None: ...
```

Assertions should verify:

- `stage`
- `recommended_command`
- minimal deterministic `user_message`
- stage-specific `context`

- [ ] **Step 2: Run the targeted service tests to verify they fail**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_workflow_service.py -q`

Expected: FAIL because `draft_conversation_turn()` does not exist yet.

- [ ] **Step 3: Implement stage resolution helpers**

In `service.py`, add small helpers that:

- collect `available_sections`
- check for draft/approved/simulated artifacts
- reuse existing `draft_intake_guidance()`, `draft_approval_packet()`, and `summarize_revision()`

- [ ] **Step 4: Implement `draft_conversation_turn()`**

Add a method shaped like:

```python
def draft_conversation_turn(self, run_id: str, revision_id: str) -> ConversationTurn:
    run_dir = self.repository.run_dir(run_id)
    available_sections = ...

    if simulation_exists:
        summary = self.summarize_revision(run_id, revision_id)
        return ConversationTurn(...)
    if assumptions_approved_exists:
        ...
    if evidence_draft_exists:
        packet = self.draft_approval_packet(run_id, revision_id)
        return ConversationTurn(...)
    if intake_draft_exists:
        guidance = self.draft_intake_guidance(run_id, revision_id)
        return ConversationTurn(...)
    return ConversationTurn(...)
```

Use deterministic user messages and keep `context` narrow.

- [ ] **Step 5: Run the targeted service tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_workflow_service.py -q`

Expected: PASS

- [ ] **Step 6: Commit the service changes**

```bash
git add packages/core/src/forecasting_harness/workflow/service.py \
        packages/core/tests/test_workflow_service.py
git commit -m "feat: add conversation turn resolution"
```

### Task 3: Expose the Conversation Turn Through the CLI

**Files:**
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Modify: `packages/core/tests/test_cli_workflow.py`

- [ ] **Step 1: Write a failing CLI test**

Add a test like:

```python
def test_draft_conversation_turn_command_returns_report_stage_for_simulated_revision(tmp_path: Path) -> None:
    ...
    result = runner.invoke(
        app,
        ["draft-conversation-turn", "--root", str(root), "--run-id", "crisis-1", "--revision-id", "r1"],
    )

    payload = json.loads(result.stdout)
    assert payload["stage"] == "report"
    assert payload["recommended_command"] == "forecast-harness begin-revision-update"
```

Also add one test for the pre-evidence stage if needed.

- [ ] **Step 2: Run the CLI workflow tests to verify they fail**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_cli_workflow.py -q`

Expected: FAIL because the command does not exist yet.

- [ ] **Step 3: Add the new command**

Expose:

```python
@app.command("draft-conversation-turn")
def draft_conversation_turn(...):
    print(_service(root).draft_conversation_turn(run_id, revision_id).model_dump_json())
```

- [ ] **Step 4: Run the CLI workflow tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_cli_workflow.py -q`

Expected: PASS

- [ ] **Step 5: Commit the CLI changes**

```bash
git add packages/core/src/forecasting_harness/cli.py \
        packages/core/tests/test_cli_workflow.py
git commit -m "feat: add conversation turn command"
```

### Task 4: Refresh Adapter Docs Around the New State Machine

**Files:**
- Modify: `packages/core/tests/test_adapter_docs.py`
- Modify: `docs/install-codex.md`
- Modify: `docs/install-claude-code.md`
- Modify: `adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md`
- Modify: `adapters/claude/skills/forecast-harness/SKILL.md`
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

- [ ] **Step 1: Write failing adapter-doc assertions**

Update the doc test so it requires:

- `forecast-harness draft-conversation-turn`
- wording that the adapter should call it after each workflow mutation to determine the next conversation step

- [ ] **Step 2: Run the adapter doc test to verify it fails**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_adapter_docs.py -q`

Expected: FAIL because the docs do not mention the new command yet.

- [ ] **Step 3: Update install docs and skill docs**

Refresh them to describe the new loop:

1. mutate workflow state
2. call `forecast-harness draft-conversation-turn`
3. show the returned summary/context
4. ask the user for approval or the next input

- [ ] **Step 4: Update README and status note**

Refresh:

- current CLI list
- verified progress
- current gaps
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
git commit -m "docs: refresh conversation adapter guidance"
```

### Task 5: Full Verification and Fresh-Install Smoke Test

**Files:**
- No source changes expected

- [ ] **Step 1: Run the full test suite**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core -q`

Expected: PASS with a count above the current `125 passed`.

- [ ] **Step 2: Run a fresh Python 3.13 smoke test**

Verify a real flow that uses:

- `forecast-harness start-run`
- `forecast-harness save-intake-draft` with direct flags
- `forecast-harness draft-conversation-turn`
- `forecast-harness draft-evidence-packet`
- `forecast-harness curate-evidence-draft`
- `forecast-harness draft-conversation-turn`
- `forecast-harness approve-revision` with direct flags
- `forecast-harness draft-conversation-turn`
- `forecast-harness simulate`
- `forecast-harness draft-conversation-turn`
- `forecast-harness begin-revision-update`

Confirm the stage sequence progresses as:

- `evidence`
- `approval`
- `simulation`
- `report`

- [ ] **Step 3: Refresh status docs if final verification facts changed**

- [ ] **Step 4: Commit any verification-driven doc updates**

```bash
git add README.md docs/status/2026-04-20-project-status.md
git commit -m "docs: finalize conversation adapter status"
```
