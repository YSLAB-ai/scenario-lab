# Domain Evolution Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a domain-scoped self-improvement pipeline that records suggestions, analyzes replay weaknesses, compiles manifest-driven domain overlays, verifies the result, and promotes verified domain-only changes onto a review branch.

**Architecture:** Keep the MCTS/workflow/retrieval core protected and route evolution through repo-owned knowledge overlays plus branch-only promotion. Domain packs read adaptive manifest sections for additional inference terms and action priors, while the evolution service owns storage, replay comparison, and git promotion.

**Tech Stack:** Python 3.11+, Pydantic models, Typer CLI, pytest, local git CLI, repo-owned JSON/JSONL knowledge files.

---

### Task 1: Add evolution models and storage

**Files:**
- Create: `packages/core/src/forecasting_harness/evolution/models.py`
- Create: `packages/core/src/forecasting_harness/evolution/storage.py`
- Create: `packages/core/tests/test_evolution_storage.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_record_suggestion_round_trips(tmp_path: Path) -> None:
    storage = EvolutionStorage(tmp_path / "knowledge" / "evolution")
    record = storage.append_suggestion(
        DomainSuggestion(
            suggestion_id="s1",
            domain_slug="company-action",
            provenance="user",
            category="action-bias",
            target="contain-message",
            text="Board reassurance should favor containment messaging.",
            terms=["board reassurance"],
            status="pending",
        )
    )

    loaded = storage.load_suggestions("company-action")
    assert loaded == [record]


def test_write_baseline_snapshot(tmp_path: Path) -> None:
    storage = EvolutionStorage(tmp_path / "knowledge" / "evolution")
    storage.write_baseline("company-action", "baseline.json", {"top_branch_accuracy": 1.0})
    assert json.loads((tmp_path / "knowledge" / "evolution" / "baselines" / "company-action" / "baseline.json").read_text())["top_branch_accuracy"] == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_evolution_storage.py -q`
Expected: FAIL with missing `forecasting_harness.evolution` module

- [ ] **Step 3: Write minimal implementation**

Create Pydantic models for suggestion, weakness brief, baseline snapshot, and evolution summary. Implement JSONL append/load plus baseline/report writes in `storage.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_evolution_storage.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/forecasting_harness/evolution/models.py \
        packages/core/src/forecasting_harness/evolution/storage.py \
        packages/core/tests/test_evolution_storage.py
git commit -m "feat: add domain evolution storage"
```

### Task 2: Add adaptive manifest overlays and pack helpers

**Files:**
- Modify: `packages/core/src/forecasting_harness/knowledge/manifests.py`
- Modify: `packages/core/src/forecasting_harness/domain/template_utils.py`
- Modify: `packages/core/src/forecasting_harness/domain/company_action.py`
- Modify: `packages/core/src/forecasting_harness/domain/interstate_crisis.py`
- Modify: `packages/core/src/forecasting_harness/domain/pandemic_response.py`
- Test: `packages/core/tests/test_manifest_overlays.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_manifest_state_overlay_boosts_field_inference(tmp_path: Path) -> None:
    manifest = {
        "slug": "company-action",
        "description": "test",
        "adaptive_state_terms": {
            "board_cohesion": [{"terms": ["board reassurance"], "delta": 0.12}]
        },
    }
    path = tmp_path / "company-action.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    loaded = load_domain_manifest("company-action", root_override=tmp_path)
    assert loaded.adaptive_state_terms["board_cohesion"][0].delta == 0.12


def test_manifest_action_biases_adjust_prior() -> None:
    actions = [{"action_id": "contain-message", "label": "Contain message", "prior": 0.2}]
    biased = apply_manifest_action_biases(
        slug="company-action",
        text="board reassurance",
        actions=actions,
        manifest=DomainManifest(
            slug="company-action",
            description="x",
            adaptive_action_biases=[AdaptiveActionBias(target="contain-message", terms=["board reassurance"], delta=0.15)],
        ),
    )
    assert biased[0]["prior"] > 0.2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_manifest_overlays.py -q`
Expected: FAIL with missing adaptive manifest fields/helpers

- [ ] **Step 3: Write minimal implementation**

Add adaptive overlay models to `DomainManifest`. Add helper functions that:
- apply manifest-driven state-field deltas
- apply manifest-driven action-bias deltas

Use those helpers in representative packs so domain behavior can change through manifest updates without touching the engine.

- [ ] **Step 4: Run test to verify it passes**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_manifest_overlays.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/forecasting_harness/knowledge/manifests.py \
        packages/core/src/forecasting_harness/domain/template_utils.py \
        packages/core/src/forecasting_harness/domain/company_action.py \
        packages/core/src/forecasting_harness/domain/interstate_crisis.py \
        packages/core/src/forecasting_harness/domain/pandemic_response.py \
        packages/core/tests/test_manifest_overlays.py
git commit -m "feat: add manifest-driven domain overlays"
```

### Task 3: Add weakness analysis and candidate synthesis

**Files:**
- Create: `packages/core/src/forecasting_harness/evolution/service.py`
- Modify: `packages/core/src/forecasting_harness/replay.py`
- Test: `packages/core/tests/test_domain_evolution_service.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_analyze_domain_weakness_returns_brief_for_missed_cases(tmp_path: Path) -> None:
    service = DomainEvolutionService(...)
    brief = service.analyze_domain_weakness("company-action", replay_result=ReplaySuiteResult(...))
    assert brief.domain_slug == "company-action"
    assert brief.reasons


def test_synthesize_candidate_updates_manifest_terms(tmp_path: Path) -> None:
    service = DomainEvolutionService(...)
    result = service.synthesize_candidate("company-action", suggestions=[...], weakness_brief=None)
    assert "adaptive_action_biases" in result.updated_manifest
```

- [ ] **Step 2: Run test to verify it fails**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_domain_evolution_service.py -q`
Expected: FAIL with missing domain evolution service

- [ ] **Step 3: Write minimal implementation**

Implement:
- suggestion normalization/classification
- weakness analysis from replay misses
- candidate manifest synthesis from pending suggestions plus misses
- protected-surface checks

- [ ] **Step 4: Run test to verify it passes**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_domain_evolution_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/forecasting_harness/evolution/service.py \
        packages/core/src/forecasting_harness/replay.py \
        packages/core/tests/test_domain_evolution_service.py
git commit -m "feat: add domain evolution analysis"
```

### Task 4: Add CLI commands and branch promotion

**Files:**
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Modify: `packages/core/src/forecasting_harness/evolution/service.py`
- Test: `packages/core/tests/test_domain_evolution_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_record_domain_suggestion_command(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["record-domain-suggestion", "--root", str(tmp_path), "--domain-pack", "company-action", "--text", "Board reassurance should favor containment messaging."])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "pending"


def test_run_domain_evolution_writes_branch_summary(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["run-domain-evolution", "--root", str(tmp_path), "--domain-pack", "company-action", "--no-branch"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["promotion_decision"] in {"promoted", "rejected"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_domain_evolution_cli.py -q`
Expected: FAIL with unknown CLI commands

- [ ] **Step 3: Write minimal implementation**

Add commands:
- `record-domain-suggestion`
- `analyze-domain-weakness`
- `run-domain-evolution`
- `summarize-domain-evolution`

Branch promotion should default to review-branch creation, but tests may use `--no-branch` to avoid git mutations in temp dirs.

- [ ] **Step 4: Run test to verify it passes**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_domain_evolution_cli.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/core/src/forecasting_harness/cli.py \
        packages/core/src/forecasting_harness/evolution/service.py \
        packages/core/tests/test_domain_evolution_cli.py
git commit -m "feat: add domain evolution commands"
```

### Task 5: Docs, full verification, and merge readiness

**Files:**
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`
- Create: `docs/status/2026-04-21-domain-evolution-pipeline.md`

- [ ] **Step 1: Update docs**

Document:
- new evolution storage
- manifest overlay behavior
- CLI commands
- branch-only promotion model

- [ ] **Step 2: Run targeted verification**

Run: `packages/core/.venv/bin/python -m pytest packages/core/tests/test_evolution_storage.py packages/core/tests/test_manifest_overlays.py packages/core/tests/test_domain_evolution_service.py packages/core/tests/test_domain_evolution_cli.py -q`
Expected: PASS

- [ ] **Step 3: Run full verification**

Run: `packages/core/.venv/bin/python -m pytest packages/core -q`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add README.md \
        docs/status/2026-04-20-project-status.md \
        docs/status/2026-04-21-domain-evolution-pipeline.md
git commit -m "docs: add domain evolution pipeline notes"
```

- [ ] **Step 5: Request code review**

Compare the feature branch against `main` and request review before merge.

## Self-Review

- Spec coverage: this plan covers storage, overlays, analysis, CLI, git promotion, docs, and verification.
- Placeholder scan: all tasks include explicit files and test commands.
- Type consistency: models and commands use consistent `domain_slug` / `domain-pack` naming across tasks.
