# Domain Evolution Pipeline

Date: 2026-04-21

## Scope

This pass adds a repo-owned self-improvement pipeline for domain knowledge.

The new pipeline is intentionally bounded:

- one domain at a time
- protected shared algorithm
- domain-only promotion branch
- no automatic merge to `main`

The first implementation compiles improvements into manifest-owned overlays rather than rewriting the shared MCTS or workflow code.

## Files Added or Changed

- new package:
  - `packages/core/src/forecasting_harness/evolution/`
- new spec:
  - `docs/superpowers/specs/2026-04-21-domain-evolution-pipeline-design.md`
- new plan:
  - `docs/superpowers/plans/2026-04-21-domain-evolution-pipeline-implementation.md`
- updated manifest loader and domain helpers:
  - `packages/core/src/forecasting_harness/knowledge/manifests.py`
  - `packages/core/src/forecasting_harness/domain/template_utils.py`
- updated packs to consume adaptive overlays:
  - `company-action`
  - `election-shock`
  - `interstate-crisis`
  - `market-shock`
  - `pandemic-response`
  - `regulatory-enforcement`
  - `supply-chain-disruption`
- new tests:
  - `packages/core/tests/test_evolution_storage.py`
  - `packages/core/tests/test_manifest_overlays.py`
  - `packages/core/tests/test_domain_evolution_service.py`
  - `packages/core/tests/test_domain_evolution_cli.py`

## New CLI Commands

- `forecast-harness record-domain-suggestion`
- `forecast-harness analyze-domain-weakness`
- `forecast-harness run-domain-evolution`
- `forecast-harness summarize-domain-evolution`

## Verified Behavior

The pipeline can now:

- store explicit user suggestions under `knowledge/evolution/suggestions/<slug>.jsonl`
- derive self-detected `action-bias` suggestions from replay misses
- synthesize adaptive manifest changes for:
  - `adaptive_state_terms`
  - `adaptive_action_biases`
  - `semantic_alias_groups`
  - `evidence_category_terms`
- compare before/after replay metrics for a domain
- promote successful domain-only changes onto a standalone branch

## Verification

### Full test suite

- `packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `210 passed in 2.25s`

### No-branch CLI smoke

Verified in a temporary workspace with a minimal `company-action` manifest:

- `record-domain-suggestion`
  - stored pending suggestion for `contain-message`
- `run-domain-evolution --no-branch`
  - returned `promotion_decision = promoted`
- `summarize-domain-evolution`
  - returned `pending_suggestions = 0`
  - returned the latest report payload

### Branch-promotion smoke

Verified in a temporary git repo:

- `run-domain-evolution`
  - created branch `codex/domain-evolution-company-action-20260421`
  - committed domain knowledge changes
  - head commit message: `feat: evolve company-action domain knowledge`

## Current Limitation

The first implementation improves built-in packs through manifest-owned overlays. It does not yet synthesize direct Python edits to domain pack source files or new replay cases automatically.
