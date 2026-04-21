# Domain Synthesis Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic pipeline that generates a brand-new template-backed domain pack, manifest, test, and review branch from a structured blueprint.

**Architecture:** Keep the shared algorithm untouched and introduce a reusable generated-pack runtime plus a synthesis service that renders domain files from blueprint data. Promotion remains branch-only.

**Tech Stack:** Python 3.11+, Pydantic, Typer, pytest, local git CLI, repo-owned JSON manifests.

---

### Task 1: Add blueprint models and generated-pack runtime

**Files:**
- Create: `packages/core/src/forecasting_harness/domain/generated_template.py`
- Modify: `packages/core/src/forecasting_harness/evolution/models.py`
- Create: `packages/core/tests/test_generated_template_pack.py`

- [ ] **Step 1: Write the failing tests**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement minimal blueprint and generated runtime**
- [ ] **Step 4: Run test to verify it passes**

### Task 2: Add synthesis service and file generation

**Files:**
- Modify: `packages/core/src/forecasting_harness/evolution/service.py`
- Create: `packages/core/tests/test_domain_synthesis_service.py`

- [ ] **Step 1: Write the failing tests**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement deterministic file generation from blueprint**
- [ ] **Step 4: Run test to verify it passes**

### Task 3: Add CLI synthesis command and branch promotion

**Files:**
- Modify: `packages/core/src/forecasting_harness/cli.py`
- Create: `packages/core/tests/test_domain_synthesis_cli.py`

- [ ] **Step 1: Write the failing tests**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement `forecast-harness synthesize-domain`**
- [ ] **Step 4: Run test to verify it passes**

### Task 4: Docs and verification

**Files:**
- Modify: `README.md`
- Modify: `docs/status/2026-04-20-project-status.md`
- Create: `docs/status/2026-04-21-domain-synthesis-pipeline.md`

- [ ] **Step 1: Update docs**
- [ ] **Step 2: Run targeted synthesis tests**
- [ ] **Step 3: Run full `packages/core` suite**
- [ ] **Step 4: Smoke-test synthesis in a temporary repo**
