# Domain Templates And Manifests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reusable domain template packs and repo-owned source manifests for the strongest non-geopolitical forecasting domains supported by the current harness.

**Architecture:** Extend the existing `DomainPack` registry with deterministic template packs, then add manifest files under a repo-owned knowledge directory so each domain has a structured ingestion blueprint without bundling source content. Keep the workflow and simulation interfaces unchanged.

**Tech Stack:** Python, Pydantic models already in repo, existing CLI/registry/tests, Markdown and JSON repo artifacts

---

### Task 1: Add Red Tests For New Domain Templates

**Files:**
- Modify: `packages/core/tests/test_domain_registry.py`
- Modify: `packages/core/tests/test_cli_workflow.py`
- Create or modify: `packages/core/tests/test_domain_templates.py`

- [ ] **Step 1: Write failing registry and CLI expectations**

Add expectations that `build_default_registry().list_slugs()` includes:

```python
[
    "company-action",
    "election-shock",
    "generic-event",
    "interstate-crisis",
    "market-shock",
    "regulatory-enforcement",
    "supply-chain-disruption",
]
```

- [ ] **Step 2: Run tests to verify failure**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_domain_registry.py packages/core/tests/test_cli_workflow.py -q`

Expected: failures showing the new packs are not registered yet.

- [ ] **Step 3: Add failing domain-template behavior tests**

Add focused tests that verify each new pack:

- returns the expected slug
- exposes non-empty canonical phases
- validates intake shape as expected
- returns non-empty actions from the starting phase
- transitions to a different phase after the first action

- [ ] **Step 4: Run the new template tests and verify failure**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_domain_templates.py -q`

Expected: import or registry failures because the new packs do not exist yet.

- [ ] **Step 5: Commit**

```bash
git add packages/core/tests/test_domain_registry.py packages/core/tests/test_cli_workflow.py packages/core/tests/test_domain_templates.py
git commit -m "test: define domain template behavior"
```

### Task 2: Implement New Domain Pack Templates

**Files:**
- Create: `packages/core/src/forecasting_harness/domain/company_action.py`
- Create: `packages/core/src/forecasting_harness/domain/election_shock.py`
- Create: `packages/core/src/forecasting_harness/domain/market_shock.py`
- Create: `packages/core/src/forecasting_harness/domain/supply_chain_disruption.py`
- Create: `packages/core/src/forecasting_harness/domain/regulatory_enforcement.py`
- Modify: `packages/core/src/forecasting_harness/domain/registry.py`

- [ ] **Step 1: Implement deterministic pack modules**

For each file, follow the existing `GenericEventPack`/`InterstateCrisisPack` pattern:

- helper field readers
- canonical phases
- intake validation
- retrieval filters
- pack schema
- deterministic actions
- deterministic transitions
- scoring

- [ ] **Step 2: Register packs in the default registry**

Update `build_default_registry()` so the new slugs resolve to fresh instances.

- [ ] **Step 3: Run focused domain tests**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core/tests/test_domain_registry.py packages/core/tests/test_domain_templates.py packages/core/tests/test_cli_workflow.py -q`

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add packages/core/src/forecasting_harness/domain/company_action.py \
        packages/core/src/forecasting_harness/domain/election_shock.py \
        packages/core/src/forecasting_harness/domain/market_shock.py \
        packages/core/src/forecasting_harness/domain/supply_chain_disruption.py \
        packages/core/src/forecasting_harness/domain/regulatory_enforcement.py \
        packages/core/src/forecasting_harness/domain/registry.py
git commit -m "feat: add reusable domain template packs"
```

### Task 3: Add Repo-Owned Domain Knowledge Manifests

**Files:**
- Create: `knowledge/domains/company-action.json`
- Create: `knowledge/domains/election-shock.json`
- Create: `knowledge/domains/interstate-crisis.json`
- Create: `knowledge/domains/market-shock.json`
- Create: `knowledge/domains/regulatory-enforcement.json`
- Create: `knowledge/domains/supply-chain-disruption.json`
- Create: `knowledge/README.md`

- [ ] **Step 1: Create domain manifest schema by convention**

Each manifest should contain concrete JSON fields:

- `slug`
- `description`
- `actor_categories`
- `evidence_categories`
- `key_state_fields`
- `canonical_stages`
- `recommended_source_types`
- `starter_sources`
- `ingestion_priorities`
- `freshness_notes`

- [ ] **Step 2: Populate manifests for all six domains**

Use source suggestions and evidence categories only. Do not embed copyrighted full-text content.

- [ ] **Step 3: Document how manifests fit the repo-owned knowledge system**

Explain that manifests are the local source-of-truth blueprint and the user populates the corpus with licensed, public-domain, or user-supplied materials later.

- [ ] **Step 4: Verify manifest files exist and are valid JSON**

Run:

```bash
python - <<'PY'
import json
from pathlib import Path
for path in sorted(Path("knowledge/domains").glob("*.json")):
    json.loads(path.read_text(encoding="utf-8"))
print("ok")
PY
```

Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add knowledge/domains knowledge/README.md
git commit -m "docs: add domain knowledge manifests"
```

### Task 4: Update Project Documentation And Verify End To End

**Files:**
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`

- [ ] **Step 1: Update README**

Add the new domain packs and knowledge-manifest directory to the verified project description.

- [ ] **Step 2: Update status note**

Record the new registry coverage, template-pack milestone, and manifest scaffold.

- [ ] **Step 3: Run full test suite**

Run: `"/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python" -m pytest packages/core -q`

Expected: full suite passes.

- [ ] **Step 4: Run CLI smoke check**

Run:

```bash
forecast-harness list-domain-packs
```

Expected: output includes all new domain slugs.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/status/2026-04-20-project-status.md
git commit -m "docs: record domain template milestone"
```
