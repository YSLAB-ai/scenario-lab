# Scenario Smoke Campaign

Date: 2026-04-21

## Verified Campaign

The current codebase was exercised through a 10-scenario end-to-end campaign using realistic local inputs across six domain packs:

- `us-iran-gulf`
- `japan-china-strait`
- `india-pakistan-crisis`
- `apple-ceo-transition`
- `boeing-post-reporting`
- `election-debate-collapse`
- `market-rate-shock`
- `regulator-adtech`
- `supply-rare-earth`
- `supplier-flooding`

Each run executed the same workflow:

1. `start-run`
2. `save-intake-draft`
3. `recommend-ingestion-files`
4. `batch-ingest-recommended`
5. `draft-evidence-packet`
6. `approve-revision`
7. `simulate`

Verified outcomes:

- All 10 runs produced non-empty deterministic MCTS output.
- All 10 runs produced scenario-local evidence packets from the files created for that run.
- All 10 runs inferred pack-specific state fields from approved evidence.
- The smoke campaign results are now locked into the automated suite through `packages/core/tests/test_smoke_campaign.py`.

## Bugs Found And Fixed

The campaign exposed several backend issues:

- Natural-language ingestion matching was too brittle for realistic wording.
- Different files with the same filename stem could collide on `source_id`.
- Same-domain runs could borrow stale evidence from earlier scenarios.
- Ingestion planning treated old same-domain coverage as sufficient for a new scenario.
- Belief-state compilation ignored approved evidence unless `pack_fields` were filled manually.
- Token matching allowed short fragments like `in` to match `India`, which created false-positive scenario relevance.

The current code now fixes those issues through:

- stronger text matching utilities in `domain/template_utils.py`
- path-aware `source_id` disambiguation in `retrieval/registry.py`
- run-scoped evidence drafting and ingestion planning in `workflow/service.py`
- evidence-driven pack-field inference in `workflow/compiler.py` plus pack-specific `infer_pack_fields(...)`
- regression coverage in:
  - `packages/core/tests/test_template_utils.py`
  - `packages/core/tests/test_retrieval.py`
  - `packages/core/tests/test_workflow_evidence.py`
  - `packages/core/tests/test_workflow_service.py`
  - `packages/core/tests/test_smoke_campaign.py`

## Final Verification

Verified on 2026-04-21:

- `packages/core/.venv/bin/python -m pytest packages/core -q`
- Result: `186 passed`
