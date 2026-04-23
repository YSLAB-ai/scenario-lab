# Scenario Lab CLI Rename And Slash Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the shipped user-facing command and adapter bundles from `forecast-harness` to `scenario-lab`, and add a real repo-owned `/scenario <prompt>` bootstrap that starts the existing workflow without inventing a parallel engine or writing invalid intake drafts.

**Architecture:** Keep the internal Python module path `forecasting_harness` stable, but rename the package entrypoint, adapter manifests, install targets, docs, and tests to `scenario-lab`. Implement the slash entry as a thin CLI command that validates `/scenario ...`, creates a run, drafts guidance from the existing workflow service, performs narrow actor extraction when the selected pack requires focus entities, saves a valid intake draft when possible, and otherwise returns an intake-stage turn with real guidance and validation errors.

**Tech Stack:** Python 3.12, Typer CLI, pytest, packaged Codex/Claude adapter bundles, existing workflow service and adapter runtime

---

## File Structure

### Package And CLI Surface

- Modify: `packages/core/pyproject.toml`
  - Change the installed console script from `forecast-harness` to `scenario-lab`.
- Modify: `packages/core/src/forecasting_harness/cli.py`
  - Add the slash bootstrap command and its parsing helpers.
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
  - Update runtime command string generation from `forecast-harness ...` to `scenario-lab ...`.

### Adapter Bundles

- Move: `adapters/codex/forecast-harness` -> `adapters/codex/scenario-lab`
  - Rename the Codex bundle root and update manifest/install/smoke references.
- Move: `adapters/claude/forecast-harness` -> `adapters/claude/scenario-lab`
  - Rename the Claude bundle root and update manifest/install/smoke references.
- Move: `adapters/codex/forecast-harness/skills/forecast-harness` -> `adapters/codex/scenario-lab/skills/scenario-lab`
  - Rename the installed Codex skill path and guidance text.
- Move: `adapters/claude/skills/forecast-harness` -> `adapters/claude/skills/scenario-lab`
  - Rename the legacy Claude skill path if it is still validated by tests/docs.

### Public And Install Docs

- Modify: `README.md`
  - Replace live `forecast-harness` command examples with `scenario-lab`.
- Modify: `docs/quickstart.md`
  - Replace live command examples.
- Modify: `docs/natural-language-workflow.md`
  - Describe the new `/scenario <prompt>` bootstrap.
- Modify: `docs/install-codex.md`
  - Point to `adapters/codex/scenario-lab`.
- Modify: `docs/install-claude-code.md`
  - Point to `adapters/claude/scenario-lab`.
- Modify: `adapters/codex/scenario-lab/README.md`
  - Update bundle instructions and smoke examples.
- Modify: `adapters/claude/scenario-lab/README.md`
  - Update bundle instructions and smoke examples.

### Tests

- Modify: `packages/core/tests/test_adapter_packages.py`
  - Validate renamed install targets and renamed smoke paths.
- Modify: `packages/core/tests/test_adapter_docs.py`
  - Validate renamed bundle paths and `scenario-lab` commands.
- Modify: `packages/core/tests/test_public_release_docs.py`
  - Validate `scenario-lab` examples instead of `forecast-harness`.
- Modify: `packages/core/tests/test_adapter_runtime_cli.py`
  - Add direct slash-bootstrap coverage.
- Modify: `packages/core/tests/test_cli_workflow.py`
  - Validate the new `scenario` command and changed command strings.

---

### Task 1: Add Failing Tests For The Renamed Surface And Slash Bootstrap

**Files:**
- Modify: `packages/core/tests/test_adapter_packages.py`
- Modify: `packages/core/tests/test_adapter_docs.py`
- Modify: `packages/core/tests/test_public_release_docs.py`
- Modify: `packages/core/tests/test_adapter_runtime_cli.py`
- Modify: `packages/core/tests/test_cli_workflow.py`
- Test: `packages/core/tests/test_adapter_packages.py`
- Test: `packages/core/tests/test_adapter_docs.py`
- Test: `packages/core/tests/test_public_release_docs.py`
- Test: `packages/core/tests/test_adapter_runtime_cli.py`
- Test: `packages/core/tests/test_cli_workflow.py`

- [ ] **Step 1: Rewrite adapter-package expectations to the renamed bundle paths**

Update the assertions in `packages/core/tests/test_adapter_packages.py` so they expect:

```python
assert (target_dir / "scenario-lab" / ".codex-plugin" / "plugin.json").exists()
assert (target_dir / "scenario-lab" / "skills" / "scenario-lab" / "SKILL.md").exists()
assert (target_dir / "skills" / "scenario-lab" / "SKILL.md").exists()
```

And update the install/smoke invocations to use:

```python
repo_root / "adapters" / "codex" / "scenario-lab" / "install.py"
repo_root / "adapters" / "codex" / "scenario-lab" / "smoke.py"
repo_root / "adapters" / "claude" / "scenario-lab" / "install.py"
repo_root / "adapters" / "claude" / "scenario-lab" / "smoke.py"
```

- [ ] **Step 2: Rewrite the doc-guard tests to require `scenario-lab` commands**

Update `packages/core/tests/test_adapter_docs.py` and `packages/core/tests/test_public_release_docs.py` so they assert:

```python
assert "scenario-lab demo-run --root .forecast" in readme
assert "scenario-lab demo-run --root .forecast" in quickstart
assert "adapters/codex/scenario-lab/install.py --target-dir /tmp/codex-plugins" in codex_doc
assert "adapters/claude/scenario-lab/install.py --target-dir /tmp/claude-root" in claude_doc
```

And replace old bundle-path reads with:

```python
root / "adapters" / "codex" / "scenario-lab" / "README.md"
root / "adapters" / "claude" / "scenario-lab" / "README.md"
```

- [ ] **Step 3: Add a failing slash-bootstrap test to the runtime CLI suite**

Append this test to `packages/core/tests/test_adapter_runtime_cli.py`:

```python
def test_scenario_command_bootstraps_a_real_workflow_turn(tmp_path: Path) -> None:
    runner = CliRunner()
    root = tmp_path / ".forecast"

    result = runner.invoke(
        app,
        [
            "scenario",
            "--root",
            str(root),
            "--run-id",
            "us-iran-1",
            "--revision-id",
            "r1",
            "--domain-pack",
            "interstate-crisis",
            "/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["command"] == "scenario"
    assert payload["prompt"].startswith("/scenario ")
    assert payload["intake"]["focus_entities"] == ["US", "Iran"]
    assert payload["turn"]["stage"] == "evidence"
    assert payload["turn"]["recommended_runtime_action"] in {
        "batch-ingest-recommended",
        "draft-evidence-packet",
    }
    assert payload["intake"]["current_stage"] == "trigger"
```

- [ ] **Step 4: Add a CLI-workflow test for renamed command strings in runtime payloads**

Append this assertion pattern to `packages/core/tests/test_cli_workflow.py` after loading a runtime payload:

```python
assert "scenario-lab save-intake-draft" in conversation_payload["recommended_command"]
assert "forecast-harness" not in conversation_payload["recommended_command"]
```

- [ ] **Step 5: Run the targeted test set and verify it fails**

Run:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest \
  packages/core/tests/test_adapter_packages.py \
  packages/core/tests/test_adapter_docs.py \
  packages/core/tests/test_public_release_docs.py \
  packages/core/tests/test_adapter_runtime_cli.py \
  packages/core/tests/test_cli_workflow.py -q
```

Expected:

- bundle tests fail because `adapters/.../scenario-lab` does not exist yet
- doc tests fail because the docs still say `forecast-harness`
- slash-bootstrap tests fail because no `scenario` command exists yet

- [ ] **Step 6: Commit the failing-test baseline**

```bash
git add \
  packages/core/tests/test_adapter_packages.py \
  packages/core/tests/test_adapter_docs.py \
  packages/core/tests/test_public_release_docs.py \
  packages/core/tests/test_adapter_runtime_cli.py \
  packages/core/tests/test_cli_workflow.py
git commit -m "test: add scenario lab rename guardrails"
```

---

### Task 2: Rename The Shipped Command And Runtime Command Strings

**Files:**
- Modify: `packages/core/pyproject.toml`
- Modify: `packages/core/src/forecasting_harness/workflow/service.py`
- Modify: `README.md`
- Modify: `docs/quickstart.md`
- Modify: `docs/natural-language-workflow.md`
- Modify: `docs/install-codex.md`
- Modify: `docs/install-claude-code.md`
- Test: `packages/core/tests/test_adapter_docs.py`
- Test: `packages/core/tests/test_public_release_docs.py`
- Test: `packages/core/tests/test_cli_workflow.py`

- [ ] **Step 1: Rename the installed console script in package metadata**

Change the script block in `packages/core/pyproject.toml` from:

```toml
[project.scripts]
forecast-harness = "forecasting_harness.cli:main"
```

to:

```toml
[project.scripts]
scenario-lab = "forecasting_harness.cli:main"
```

- [ ] **Step 2: Update runtime-generated command strings to `scenario-lab`**

In `packages/core/src/forecasting_harness/workflow/service.py`, replace:

```python
prefix = "forecast-harness "
```

with:

```python
prefix = "scenario-lab "
```

And update any hard-coded `recommended_command="forecast-harness ..."` values to `scenario-lab ...`.

- [ ] **Step 3: Update current public/install docs to the renamed command**

Replace live current-surface command examples such as:

```md
forecast-harness demo-run --root .forecast
forecast-harness run-adapter-action ...
forecast-harness summarize-revision ...
```

with:

```md
scenario-lab demo-run --root .forecast
scenario-lab run-adapter-action ...
scenario-lab summarize-revision ...
```

Do this only in the current public/install docs listed in the File Structure section, not in historical status/spec files.

- [ ] **Step 4: Run the doc/runtime test subset and verify it passes**

Run:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest \
  packages/core/tests/test_adapter_docs.py \
  packages/core/tests/test_public_release_docs.py \
  packages/core/tests/test_cli_workflow.py -q
```

Expected:

- all renamed-command assertions pass
- no live public doc still requires `forecast-harness`

- [ ] **Step 5: Commit the user-facing command rename**

```bash
git add \
  packages/core/pyproject.toml \
  packages/core/src/forecasting_harness/workflow/service.py \
  README.md \
  docs/quickstart.md \
  docs/natural-language-workflow.md \
  docs/install-codex.md \
  docs/install-claude-code.md
git commit -m "feat: rename user-facing cli to scenario-lab"
```

---

### Task 3: Rename The Adapter Bundles To `scenario-lab`

**Files:**
- Move: `adapters/codex/forecast-harness` -> `adapters/codex/scenario-lab`
- Move: `adapters/claude/forecast-harness` -> `adapters/claude/scenario-lab`
- Move: `adapters/codex/forecast-harness/skills/forecast-harness` -> `adapters/codex/scenario-lab/skills/scenario-lab`
- Move: `adapters/claude/skills/forecast-harness` -> `adapters/claude/skills/scenario-lab`
- Modify: `adapters/codex/scenario-lab/adapter.json`
- Modify: `adapters/codex/scenario-lab/.codex-plugin/plugin.json`
- Modify: `adapters/codex/scenario-lab/install.py`
- Modify: `adapters/codex/scenario-lab/smoke.py`
- Modify: `adapters/codex/scenario-lab/README.md`
- Modify: `adapters/codex/scenario-lab/skills/scenario-lab/SKILL.md`
- Modify: `adapters/claude/scenario-lab/adapter.json`
- Modify: `adapters/claude/scenario-lab/install.py`
- Modify: `adapters/claude/scenario-lab/smoke.py`
- Modify: `adapters/claude/scenario-lab/README.md`
- Modify: `adapters/claude/skills/scenario-lab/SKILL.md`
- Test: `packages/core/tests/test_adapter_packages.py`
- Test: `packages/core/tests/test_adapter_docs.py`

- [ ] **Step 1: Move the bundle and skill directories**

Run:

```bash
mv adapters/codex/forecast-harness adapters/codex/scenario-lab
mv adapters/claude/forecast-harness adapters/claude/scenario-lab
mv adapters/codex/scenario-lab/skills/forecast-harness adapters/codex/scenario-lab/skills/scenario-lab
mv adapters/claude/skills/forecast-harness adapters/claude/skills/scenario-lab
```

Expected:

- the live bundle roots become `scenario-lab`
- installed skill directory names also become `scenario-lab`

- [ ] **Step 2: Rewrite the bundle manifests and install targets**

Update `adapters/codex/scenario-lab/adapter.json` to:

```json
{
  "name": "scenario-lab",
  "adapter": "codex",
  "install_entries": [
    {
      "source": ".codex-plugin",
      "target": "scenario-lab/.codex-plugin"
    },
    {
      "source": "skills",
      "target": "scenario-lab/skills"
    },
    {
      "source": "README.md",
      "target": "scenario-lab/README.md"
    }
  ]
}
```

Update `adapters/codex/scenario-lab/.codex-plugin/plugin.json` to:

```json
{
  "name": "scenario-lab",
  "version": "0.1.0",
  "description": "Codex adapter for Scenario Lab",
  "interface": {
    "displayName": "Scenario Lab"
  }
}
```

Update `adapters/claude/scenario-lab/adapter.json` to:

```json
{
  "name": "scenario-lab",
  "adapter": "claude",
  "install_entries": [
    {
      "source": "skills/scenario-lab",
      "target": "skills/scenario-lab"
    }
  ]
}
```

- [ ] **Step 3: Rewrite install/smoke/skill text to the renamed command**

In both bundle `install.py` files, change the parser descriptions from `forecasting-harness` to `Scenario Lab`.

In both bundle `smoke.py` files:

- update temp directory prefixes from `forecast-harness-...` to `scenario-lab-...`
- keep importing `forecasting_harness.cli` unchanged

In both skill files, replace live command examples like:

```md
forecast-harness run-adapter-action ...
forecast-harness start-run ...
forecast-harness summarize-run ...
```

with:

```md
scenario-lab run-adapter-action ...
scenario-lab start-run ...
scenario-lab summarize-run ...
```

- [ ] **Step 4: Run the adapter install/docs tests and the bundle smokes**

Run:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest \
  packages/core/tests/test_adapter_packages.py \
  packages/core/tests/test_adapter_docs.py -q
packages/core/.venv/bin/python adapters/codex/scenario-lab/smoke.py --work-dir /tmp/scenario-lab-codex-rename-smoke
packages/core/.venv/bin/python adapters/claude/scenario-lab/smoke.py --work-dir /tmp/scenario-lab-claude-rename-smoke
```

Expected:

- install/doc tests pass
- both smokes reach `report`

- [ ] **Step 5: Commit the bundle rename**

```bash
git add adapters/codex/scenario-lab adapters/claude/scenario-lab adapters/claude/skills/scenario-lab
git commit -m "feat: rename adapter bundles to scenario-lab"
```

---

### Task 4: Add The `/scenario <prompt>` Bootstrap Command

**Files:**
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Modify: `packages/core/tests/test_adapter_runtime_cli.py`
- Modify: `packages/core/tests/test_cli_workflow.py`
- Modify: `README.md`
- Modify: `docs/natural-language-workflow.md`
- Test: `packages/core/tests/test_adapter_runtime_cli.py`
- Test: `packages/core/tests/test_cli_workflow.py`
- Test: `packages/core/tests/test_public_release_docs.py`

- [ ] **Step 1: Add slash-prompt and actor-extraction helpers in `cli.py`**

Insert these helpers near the other CLI parsing helpers:

```python
def _parse_scenario_prompt(raw_prompt: str) -> str:
    prompt = raw_prompt.strip()
    if not prompt.startswith("/scenario"):
        raise typer.BadParameter("prompt must start with /scenario", param_hint="prompt")
    remainder = prompt[len("/scenario") :].strip()
    if not remainder:
        raise typer.BadParameter("prompt must include text after /scenario", param_hint="prompt")
    return remainder


def _extract_focus_entities_from_prompt(domain_pack: str, prompt: str) -> list[str]:
    normalized = prompt.lower()
    alias_map: dict[str, list[tuple[str, list[str]]]] = {
        "interstate-crisis": [
            ("US", ["u.s.", "us ", "united states", "america"]),
            ("Iran", ["iran", "iranian"]),
            ("China", ["china", "chinese", "prc", "beijing"]),
            ("Taiwan", ["taiwan", "taipei", "roc"]),
            ("Japan", ["japan", "japanese", "tokyo"]),
            ("Israel", ["israel", "israeli"]),
        ],
    }
    matches: list[str] = []
    for canonical, aliases in alias_map.get(domain_pack, []):
        if any(alias in normalized for alias in aliases):
            matches.append(canonical)
    return matches
```

- [ ] **Step 2: Add the real `scenario` CLI command with safe intake fallback**

Append this command to `packages/core/src/forecasting_harness/cli.py` below the runtime workflow commands:

```python
@app.command("scenario")
def scenario_command(
    prompt: str = typer.Argument(...),
    root: Path = typer.Option(Path(".forecast")),
    run_id: str = typer.Option(...),
    revision_id: str = typer.Option("r1"),
    domain_pack: str = typer.Option(...),
) -> None:
    parsed_prompt = _parse_scenario_prompt(prompt)
    service = _service(root)
    try:
        service.repository.load_run_record(run_id)
    except FileNotFoundError:
        service.start_run(run_id=run_id, domain_pack=domain_pack)

    guidance = service.draft_intake_guidance(run_id, revision_id)
    pack = _pack_for_slug(domain_pack)
    canonical_stages = pack.canonical_phases()
    focus_entities = _extract_focus_entities_from_prompt(domain_pack, parsed_prompt)
    intake = IntakeDraft(
        event_framing=parsed_prompt,
        focus_entities=focus_entities,
        current_development=parsed_prompt,
        current_stage=canonical_stages[0] if canonical_stages else guidance.current_stage,
        time_horizon="30d",
        known_constraints=[],
        known_unknowns=[],
        suggested_entities=[],
        pack_fields={},
    )
    validation_errors = pack.validate_intake(intake)
    if validation_errors:
        turn = ConversationTurn(
            run_id=run_id,
            revision_id=revision_id,
            stage="intake",
            headline="Need a little more setup before the run can start.",
            user_message="I could not extract enough valid focus actors from that prompt yet.",
            recommended_command="scenario-lab save-intake-draft",
            recommended_runtime_action="save-intake-draft",
            available_sections=[],
            actions=[],
            context={
                "intake_guidance": guidance.model_dump(mode="json"),
                "parsed_prompt": parsed_prompt,
                "validation_errors": validation_errors,
                "suggested_focus_entities": focus_entities,
            },
        )
        print(
            json.dumps(
                {
                    "command": "scenario",
                    "prompt": prompt,
                    "intake": intake.model_dump(mode="json"),
                    "turn": turn.model_dump(mode="json"),
                }
            )
        )
        return

    service.save_intake_draft(run_id, revision_id, intake)
    turn = service.draft_conversation_turn(run_id, revision_id)
    print(
        json.dumps(
            {
                "command": "scenario",
                "prompt": prompt,
                "intake": intake.model_dump(mode="json"),
                "turn": turn.model_dump(mode="json"),
            }
        )
    )
```

Keep this intentionally narrow in v1:

- no full semantic parser
- actor extraction only through a small explicit alias table for known current domains
- no fake evidence drafting
- no saving of invalid intake drafts

- [ ] **Step 3: Document the slash bootstrap in the current public docs**

Add one concrete line to `README.md` and `docs/natural-language-workflow.md` using the real command:

```md
scenario-lab scenario --root .forecast --run-id us-iran-1 --domain-pack interstate-crisis "/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days"
```

And explain that it returns the normal next workflow turn rather than running the full simulation immediately.

- [ ] **Step 4: Run the slash/runtime/doc verification**

Run:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest \
  packages/core/tests/test_adapter_runtime_cli.py \
  packages/core/tests/test_cli_workflow.py \
  packages/core/tests/test_public_release_docs.py -q
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli scenario \
  --root /tmp/scenario-lab-scenario-smoke \
  --run-id us-iran-1 \
  --domain-pack interstate-crisis \
  "/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days"
```

Expected:

- test suite passes
- the direct command prints JSON
- `turn.stage` is `evidence` for the verified U.S.-Iran case
- `turn.recommended_runtime_action` is the real next runtime action

- [ ] **Step 5: Run the full regression and final bundle smokes**

Run:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest packages/core -q
packages/core/.venv/bin/python adapters/codex/scenario-lab/smoke.py --work-dir /tmp/scenario-lab-codex-final
packages/core/.venv/bin/python adapters/claude/scenario-lab/smoke.py --work-dir /tmp/scenario-lab-claude-final
```

Expected:

- full suite passes
- both bundled smokes still reach `report`

- [ ] **Step 6: Commit the slash bootstrap and final docs**

```bash
git add \
  packages/core/src/forecasting_harness/cli.py \
  packages/core/tests/test_adapter_runtime_cli.py \
  packages/core/tests/test_cli_workflow.py \
  README.md \
  docs/natural-language-workflow.md
git commit -m "feat: add scenario slash bootstrap"
```

