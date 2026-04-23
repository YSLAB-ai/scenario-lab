# Scenario Lab Public Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repackage the repository as a user-first public `Scenario Lab` experimental preview with a verified `U.S.-Iran` demo, public-facing docs, visual assets, and a prepared GitHub metadata package.

**Architecture:** Treat the release as a documentation-and-presentation program around the already verified core runtime. Add regression tests for the public docs surface first, then rewrite the README and public docs, then verify and document one real `U.S.-Iran` workflow, then add branded visual assets, then prepare the GitHub metadata/rename package and only perform the live public-facing edits at the very end.

**Tech Stack:** Markdown docs, Python 3.12, Typer CLI, pytest, packaged local Codex/Claude bundles, image asset generation, GitHub repository metadata

---

## File Structure

### Public Landing Surface

- Modify: `README.md`
  - Replace the internal status-heavy homepage with the public `Scenario Lab` landing page.
- Create: `docs/quickstart.md`
  - Fastest first-use path for local users.
- Create: `docs/natural-language-workflow.md`
  - Copyable prompt-style usage for Codex and Claude users.
- Create: `docs/demo-us-iran.md`
  - Verified end-to-end public example using the `U.S.-Iran` scenario.
- Create: `docs/limitations.md`
  - Honest public limitation page, including evidence/domain dependence and community contribution framing.
- Create: `docs/release-notes/public-preview.md`
  - Snapshot of what the public preview includes.

### Adapter And Install Surface

- Modify: `docs/install-codex.md`
  - Align with `Scenario Lab` branding and public quickstart language.
- Modify: `docs/install-claude-code.md`
  - Align with `Scenario Lab` branding and public quickstart language.
- Modify: `adapters/codex/forecast-harness/README.md`
  - Rewrite to match the public product framing.
- Modify: `adapters/claude/forecast-harness/README.md`
  - Rewrite to match the public product framing.

### Visual And Metadata Surface

- Create: `docs/assets/scenario-lab-social-preview.png`
  - GitHub social preview asset.
- Create: `docs/assets/scenario-lab-workflow.png`
  - README visual that shows the product workflow honestly.
- Create: `docs/github-public-metadata.md`
  - Tracked source of truth for repo rename target, description, homepage, topics, and social-preview file path.

### Regression Tests

- Create: `packages/core/tests/test_public_release_docs.py`
  - Assert the public homepage/docs/assets exist and contain the new required product language.
- Modify: `packages/core/tests/test_adapter_docs.py`
  - Update install/bundle doc expectations to the new `Scenario Lab` public-release surface.

---

### Task 1: Add Public-Surface Regression Tests First

**Files:**
- Create: `packages/core/tests/test_public_release_docs.py`
- Modify: `packages/core/tests/test_adapter_docs.py`
- Test: `packages/core/tests/test_public_release_docs.py`
- Test: `packages/core/tests/test_adapter_docs.py`

- [ ] **Step 1: Write the failing public-doc regression test file**

```python
from pathlib import Path


def test_public_readme_is_scenario_lab_landing_page() -> None:
    root = Path(__file__).resolve().parents[3]
    readme = (root / "README.md").read_text(encoding="utf-8")

    assert readme.startswith("# Scenario Lab")
    assert "Experimental preview" in readme
    assert "U.S.-Iran" in readme
    assert "docs/quickstart.md" in readme
    assert "docs/natural-language-workflow.md" in readme
    assert "docs/demo-us-iran.md" in readme
    assert "docs/limitations.md" in readme


def test_public_docs_and_assets_exist() -> None:
    root = Path(__file__).resolve().parents[3]

    assert (root / "docs" / "quickstart.md").exists()
    assert (root / "docs" / "natural-language-workflow.md").exists()
    assert (root / "docs" / "demo-us-iran.md").exists()
    assert (root / "docs" / "limitations.md").exists()
    assert (root / "docs" / "release-notes" / "public-preview.md").exists()
    assert (root / "docs" / "assets" / "scenario-lab-social-preview.png").exists()
    assert (root / "docs" / "assets" / "scenario-lab-workflow.png").exists()
```

- [ ] **Step 2: Tighten the adapter-doc tests so they fail until the new branding lands**

```python
def test_adapter_install_docs_reference_scenario_lab_branding() -> None:
    docs_root = Path(__file__).resolve().parents[3] / "docs"
    repo_root = Path(__file__).resolve().parents[3]

    codex_doc = (docs_root / "install-codex.md").read_text(encoding="utf-8")
    claude_doc = (docs_root / "install-claude-code.md").read_text(encoding="utf-8")
    codex_bundle = (repo_root / "adapters" / "codex" / "forecast-harness" / "README.md").read_text(encoding="utf-8")
    claude_bundle = (repo_root / "adapters" / "claude" / "forecast-harness" / "README.md").read_text(encoding="utf-8")

    assert "Scenario Lab" in codex_doc
    assert "Scenario Lab" in claude_doc
    assert "Scenario Lab" in codex_bundle
    assert "Scenario Lab" in claude_bundle
    assert "U.S.-Iran" in codex_doc
    assert "U.S.-Iran" in claude_doc
```

- [ ] **Step 3: Run the doc-focused tests to verify they fail**

Run:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest \
  packages/core/tests/test_public_release_docs.py \
  packages/core/tests/test_adapter_docs.py -q
```

Expected:

- `test_public_readme_is_scenario_lab_landing_page` fails because `README.md` still starts with `# Forecasting Harness`
- `test_public_docs_and_assets_exist` fails because the new public docs/assets do not exist yet
- the updated adapter-doc expectations fail because the current docs still say `Forecast Harness`

- [ ] **Step 4: Commit the failing-test baseline**

```bash
git add packages/core/tests/test_public_release_docs.py packages/core/tests/test_adapter_docs.py
git commit -m "test: add public release doc guardrails"
```

---

### Task 2: Rewrite The Homepage And Public Docs

**Files:**
- Modify: `README.md`
- Create: `docs/quickstart.md`
- Create: `docs/natural-language-workflow.md`
- Create: `docs/demo-us-iran.md`
- Create: `docs/limitations.md`
- Create: `docs/release-notes/public-preview.md`
- Test: `packages/core/tests/test_public_release_docs.py`

- [ ] **Step 1: Rewrite `README.md` into the public `Scenario Lab` landing page**

Use this exact top-of-file structure:

```md
# Scenario Lab

> Experimental preview: local-first scenario analysis you can run in natural language with Codex or Claude.

Scenario Lab helps you turn a developing situation into a structured scenario run, gather and approve evidence, simulate multiple branches, and generate readable reports.

## Quickstart

Run the built-in local demo:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli demo-run --root .forecast
```

Expected:

- `demo-run complete`
- generated run artifacts under `.forecast/runs/demo-run`

## Natural-Language Workflow

- `Start a U.S.-Iran scenario run for the next 30 days`
- `Draft the evidence packet`
- `Approve and simulate`
- `Update the run with a new Strait of Hormuz development`
```

Keep the rest of the README in this order:

1. What it does
2. Quickstart
3. Natural-language workflow
4. U.S.-Iran demo
5. Install with Codex / Claude
6. What’s included in this preview
7. Current limits
8. Minimal builder section

- [ ] **Step 2: Create `docs/quickstart.md`**

Create a concise first-use guide with these sections:

```md
# Scenario Lab Quickstart

## 1. Create the local environment

```bash
PYTHON=/path/to/python3.12
"$PYTHON" -m venv packages/core/.venv
source packages/core/.venv/bin/activate
pip install -e 'packages/core[dev]'
```

## 2. Run the built-in demo

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli demo-run --root .forecast
```

## 3. Generate a report

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli generate-report --root .forecast --run-id demo-run --revision-id r1
```
```

- [ ] **Step 3: Create `docs/natural-language-workflow.md`**

Use this exact structure:

```md
# Scenario Lab Natural-Language Workflow

## Example prompts

- `Start a U.S.-Iran scenario run for the next 30 days.`
- `Save the intake draft with U.S. and Iran as the focus actors.`
- `Draft the evidence packet.`
- `Approve the revision and simulate it.`
- `Generate the report.`

## Runtime actions

Scenario Lab exposes a packaged adapter runtime through `forecast-harness run-adapter-action`.
```

- [ ] **Step 4: Create `docs/limitations.md`**

Use these exact required bullets:

```md
# Scenario Lab Limitations

- Output quality depends heavily on the approved evidence packet.
- Output quality depends heavily on the depth and quality of the domain pack.
- Replay calibration is stronger in some domains than others.
- The system is designed to improve over time through community contributions and protected domain-evolution workflows.
- This is an experimental preview, not a production forecasting guarantee.
- OCR-backed PDF ingestion is intentionally deferred in the current public preview.
```

- [ ] **Step 5: Create `docs/release-notes/public-preview.md`**

Include:

```md
# Scenario Lab Public Preview

This preview includes:

- local-first scenario workflow
- replay-backed calibration
- packaged local Codex and Claude integrations
- spreadsheet and web-archive ingestion
- protected domain evolution and synthesis
```

- [ ] **Step 6: Create `docs/demo-us-iran.md` with an explicit verification section that Task 3 will replace with the observed run details**

Use this starter content:

```md
# Scenario Lab Demo: U.S.-Iran

This page documents a verified end-to-end `U.S.-Iran` scenario run on accepted `main`.

## Commands

The commands in this page are replaced in Task 3 with the exact verified workflow captured from the repo.
```

- [ ] **Step 7: Run the public-doc regression tests and make them pass**

Run:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest \
  packages/core/tests/test_public_release_docs.py \
  packages/core/tests/test_adapter_docs.py -q
```

Expected:

- all tests in these two files pass

- [ ] **Step 8: Commit the homepage and public docs**

```bash
git add README.md \
  docs/quickstart.md \
  docs/natural-language-workflow.md \
  docs/demo-us-iran.md \
  docs/limitations.md \
  docs/release-notes/public-preview.md \
  packages/core/tests/test_public_release_docs.py \
  packages/core/tests/test_adapter_docs.py
git commit -m "docs: add scenario lab public release surface"
```

---

### Task 3: Verify And Document The Real U.S.-Iran Demo

**Files:**
- Modify: `docs/demo-us-iran.md`
- Modify: `README.md`
- Test: live CLI/runtime smoke under `/tmp`

- [ ] **Step 1: Run a real `U.S.-Iran` workflow and save the artifacts under `/tmp/scenario-lab-us-iran`**

Run:

```bash
WORKDIR=/tmp/scenario-lab-us-iran
ROOT="$WORKDIR/run"
CORPUS="$WORKDIR/corpus.db"
mkdir -p "$WORKDIR"

PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli start-run \
  --root "$ROOT" \
  --run-id us-iran-public \
  --domain-pack interstate-crisis

PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli save-intake-draft \
  --root "$ROOT" \
  --run-id us-iran-public \
  --revision-id r1 \
  --event-framing "Assess 30-day crisis paths in a U.S.-Iran escalation scenario." \
  --focus-entity "United States" \
  --focus-entity Iran \
  --current-development "Shipping and retaliation threats intensify around the Gulf as allies urge restraint." \
  --current-stage trigger \
  --time-horizon 30d
```

Expected:

- `started us-iran-public`
- `saved intake r1`

- [ ] **Step 2: Use the packaged runtime path, not an undocumented shortcut**

Run:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli run-adapter-action \
  --root "$ROOT" \
  --corpus-db "$CORPUS" \
  --run-id us-iran-public \
  --revision-id r1 \
  --action draft-evidence-packet
```

Expected:

- JSON output with `executed_action` = `draft-evidence-packet`

If the draft is empty, explicitly document the verified fallback path using `save-evidence-draft --item-json ...` rather than hiding the behavior.

- [ ] **Step 3: Approve, simulate, and generate the report**

Run:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli approve-revision \
  --root "$ROOT" \
  --run-id us-iran-public \
  --revision-id r1 \
  --assumption "Both sides prefer bounded retaliation to immediate total war."

PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli simulate \
  --root "$ROOT" \
  --run-id us-iran-public \
  --revision-id r1

PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli generate-report \
  --root "$ROOT" \
  --run-id us-iran-public \
  --revision-id r1
```

Expected:

- `simulate` succeeds
- `generate-report` prints an absolute report path
- a real report exists under `"$ROOT"/runs/us-iran-public/reports/`

- [ ] **Step 4: Rewrite `docs/demo-us-iran.md` with the verified commands and exact observed outputs**

Use the real values you observed. The doc must include:

- commands actually run
- actual top branch
- actual iteration count
- actual report path pattern

- [ ] **Step 5: Add a short `U.S.-Iran` demo excerpt to `README.md`**

Embed a short block like:

```md
## Demo: U.S.-Iran

Verified on accepted `main`:

- top branch: `...`
- iterations: `...`
- report: `...`
```

Fill the values with the real verified run results from Step 4.

- [ ] **Step 6: Commit the verified demo docs**

```bash
git add README.md docs/demo-us-iran.md
git commit -m "docs: add verified us-iran public demo"
```

---

### Task 4: Rebrand Install And Bundle Docs For Public First Use

**Files:**
- Modify: `docs/install-codex.md`
- Modify: `docs/install-claude-code.md`
- Modify: `adapters/codex/forecast-harness/README.md`
- Modify: `adapters/claude/forecast-harness/README.md`
- Modify: `packages/core/tests/test_adapter_docs.py`
- Test: `packages/core/tests/test_adapter_docs.py`
- Test: bundle smoke scripts

- [ ] **Step 1: Rewrite the install docs to lead with `Scenario Lab`, not `Forecasting Harness`**

Ensure each install doc includes:

```md
# Scenario Lab for Codex
```

or:

```md
# Scenario Lab for Claude
```

Each doc must also include:

- the Python 3.12 environment setup
- the local bundle install command
- the smoke command
- a pointer to the `U.S.-Iran` demo and natural-language workflow docs

- [ ] **Step 2: Rewrite the bundle READMEs**

Use this shape:

```md
# Scenario Lab Codex Bundle

This packaged local bundle installs Scenario Lab into a local Codex plugin root and verifies the end-to-end runtime path.
```

and:

```md
# Scenario Lab Claude Bundle

This packaged local bundle installs Scenario Lab into a local Claude root and verifies the end-to-end runtime path.
```

- [ ] **Step 3: Extend the adapter-doc test file so it asserts the new docs link back to the public pages**

Add checks for:

```python
assert "docs/quickstart.md" in codex_doc
assert "docs/natural-language-workflow.md" in codex_doc
assert "docs/demo-us-iran.md" in codex_doc
assert "docs/quickstart.md" in claude_doc
assert "docs/natural-language-workflow.md" in claude_doc
assert "docs/demo-us-iran.md" in claude_doc
```

- [ ] **Step 4: Run the adapter-doc tests**

Run:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest \
  packages/core/tests/test_adapter_docs.py -q
```

Expected:

- all adapter-doc tests pass

- [ ] **Step 5: Run the packaged bundle smokes again**

Run:

```bash
packages/core/.venv/bin/python adapters/codex/forecast-harness/smoke.py --work-dir /tmp/scenario-lab-codex-smoke
packages/core/.venv/bin/python adapters/claude/forecast-harness/smoke.py --work-dir /tmp/scenario-lab-claude-smoke
```

Expected:

- both smokes reach `report`

- [ ] **Step 6: Commit the public install/bundle rewrite**

```bash
git add docs/install-codex.md \
  docs/install-claude-code.md \
  adapters/codex/forecast-harness/README.md \
  adapters/claude/forecast-harness/README.md \
  packages/core/tests/test_adapter_docs.py
git commit -m "docs: rebrand adapter docs for scenario lab"
```

---

### Task 5: Add Visual Assets And Wire Them Into The Public Docs

**Files:**
- Create: `docs/assets/scenario-lab-social-preview.png`
- Create: `docs/assets/scenario-lab-workflow.png`
- Modify: `README.md`
- Modify: `docs/release-notes/public-preview.md`
- Test: `packages/core/tests/test_public_release_docs.py`

- [ ] **Step 1: Generate the social-preview image**

Create a 1280x640 asset with these verified content constraints:

- title: `Scenario Lab`
- subtitle: `Experimental preview`
- visible workflow words:
  - `Intake`
  - `Evidence`
  - `Simulation`
  - `Report`
- one visible example card labeled `U.S.-Iran`

Do not add any capability claims not already supported by the repo.

- [ ] **Step 2: Generate the README workflow visual**

Create a landscape asset that visually shows:

- natural-language prompt
- evidence approval
- branch simulation
- report output

Keep the look product-like but restrained.

- [ ] **Step 3: Reference the assets in `README.md` and `docs/release-notes/public-preview.md`**

Add image references like:

```md
![Scenario Lab workflow](docs/assets/scenario-lab-workflow.png)
```

and mention the social-preview asset location in the release notes.

- [ ] **Step 4: Update the public-doc test so it asserts the README references the workflow image**

Add:

```python
assert "docs/assets/scenario-lab-workflow.png" in readme
```

- [ ] **Step 5: Run the public-doc tests again**

Run:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest \
  packages/core/tests/test_public_release_docs.py -q
```

Expected:

- all tests in `test_public_release_docs.py` pass

- [ ] **Step 6: Commit the visual-assets pass**

```bash
git add docs/assets/scenario-lab-social-preview.png \
  docs/assets/scenario-lab-workflow.png \
  README.md \
  docs/release-notes/public-preview.md \
  packages/core/tests/test_public_release_docs.py
git commit -m "docs: add scenario lab public visuals"
```

---

### Task 6: Prepare The GitHub Metadata And Rename Package

**Files:**
- Create: `docs/github-public-metadata.md`
- Modify: `docs/release-notes/public-preview.md`
- Test: manual review of file contents

- [ ] **Step 1: Create `docs/github-public-metadata.md` as the tracked source of truth**

Use this exact structure:

```md
# Scenario Lab GitHub Public Metadata

- Repository rename target: `scenario-lab`
- Product name: `Scenario Lab`
- Description: `Experimental local-first scenario analysis for natural-language forecasting with Codex or Claude`
- Homepage: `https://github.com/YSLAB-ai/scenario-lab`
- Topics:
  - `scenario-analysis`
  - `forecasting`
  - `decision-support`
  - `local-first`
  - `codex`
  - `claude`
  - `mcts`
  - `agent-tools`
- Social preview asset: `docs/assets/scenario-lab-social-preview.png`
```

- [ ] **Step 2: Note the action-time boundary clearly in the file**

Add this exact note:

```md
The live GitHub rename and metadata edits are public-facing changes and must be performed only after the repo content is verified and immediately before release.
```

- [ ] **Step 3: Link this file from `docs/release-notes/public-preview.md`**

Add a short line:

```md
The tracked GitHub metadata package for this release lives in `docs/github-public-metadata.md`.
```

- [ ] **Step 4: Review the metadata file manually for consistency with the public docs**

Check:

- repo name target matches `scenario-lab`
- description matches the README hero language
- social preview path matches the actual committed asset
- topics are all relevant

- [ ] **Step 5: Commit the metadata package**

```bash
git add docs/github-public-metadata.md docs/release-notes/public-preview.md
git commit -m "docs: add scenario lab github metadata package"
```

---

### Task 7: Final Verification And Live GitHub Release Actions

**Files:**
- No source changes required unless verification finds a real defect.
- Execute the live GitHub rename/metadata step only after the user confirms immediately before the public-facing change.

- [ ] **Step 1: Run the full verification sweep**

Run:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest packages/core -q
packages/core/.venv/bin/python adapters/codex/forecast-harness/smoke.py --work-dir /tmp/scenario-lab-codex-final
packages/core/.venv/bin/python adapters/claude/forecast-harness/smoke.py --work-dir /tmp/scenario-lab-claude-final
```

Expected:

- full suite passes
- both adapter smokes reach `report`

- [ ] **Step 2: Review the public docs as a first-time visitor**

Check manually:

- `README.md` reads like a product page, not an internal status note
- the quickstart is visible above builder detail
- `U.S.-Iran` is the primary public example
- limitations include evidence/domain dependence and community contribution

- [ ] **Step 3: Ask for action-time confirmation before the live public-facing GitHub changes**

Use this exact question:

```text
The repo content is ready. Do you want me to perform the live GitHub rename to `scenario-lab` and update the public repo metadata now?
```

This step is required because the live rename, description, homepage, topics, and social preview are public-facing edits.

- [ ] **Step 4: After confirmation, perform the live GitHub edits**

Apply:

- repo rename to `scenario-lab`
- description from `docs/github-public-metadata.md`
- homepage from `docs/github-public-metadata.md`
- topics from `docs/github-public-metadata.md`
- social preview image from `docs/assets/scenario-lab-social-preview.png`

- [ ] **Step 5: Record the final public-release status**

Append or create a note in:

```md
docs/status/2026-04-23-public-release-pass.md
```

Include:

- final repo name
- final metadata values
- verification commands and outputs
- any deferred items, which should only include OCR unless a verified new blocker appeared

- [ ] **Step 6: Commit any last repo-side release-note change**

```bash
git add docs/status/2026-04-23-public-release-pass.md
git commit -m "docs: record scenario lab public release pass"
```

---

## Self-Review

### Spec Coverage

- Public product naming and repo rename: Task 6 and Task 7
- User-first README: Task 2
- Public docs map: Task 2
- `U.S.-Iran` demo: Task 3
- Visual assets: Task 5
- Codex/Claude public docs: Task 4
- Honest limitations and community contribution framing: Task 2
- GitHub-facing metadata package: Task 6

### Placeholder Scan

No `TBD`, `TODO`, or unresolved execution placeholders remain in the plan. The tracked homepage target is explicitly set to the renamed repository URL.

### Type And Path Consistency

All referenced paths are repo-absolute and match the current repository layout:

- `README.md`
- `docs/...`
- `adapters/...`
- `packages/core/tests/...`
