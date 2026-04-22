# Domain Synthesis Pipeline Pass

Date: 2026-04-21

## Summary

This pass extends the protected-surface domain-evolution system so the repo can now synthesize a brand-new domain from a structured blueprint without editing the shared algorithm. The new path generates a template-backed starter pack, a manifest, a replay seed file, a starter test, and a registry update, and it can promote those changes onto a standalone review branch.

## Verified Changes

- Added blueprint models in `packages/core/src/forecasting_harness/evolution/models.py`:
  - `FocusEntityRule`
  - `FieldRuleTermDelta`
  - `FieldInferenceRule`
  - `ActionTemplate`
  - `DomainBlueprint`
- Added generated-pack runtime in `packages/core/src/forecasting_harness/domain/generated_template.py`.
- Extended `DomainEvolutionService` in `packages/core/src/forecasting_harness/evolution/service.py` with:
  - `synthesize_domain(...)`
  - registry update support
  - generated pack rendering
  - generated starter test rendering
  - branch-promotion commit flow for new domains
- Added CLI entrypoint:
  - `forecast-harness synthesize-domain`
- Made manifest overlay helpers in `packages/core/src/forecasting_harness/domain/template_utils.py` tolerate a missing manifest safely so a generated pack can bootstrap cleanly.

## Verified Tests

- `packages/core/.venv/bin/python -m pytest packages/core/tests/test_generated_template_pack.py -q`
  - Result: `1 passed`
- `packages/core/.venv/bin/python -m pytest packages/core/tests/test_domain_synthesis_service.py -q`
  - Result: `1 passed`
- `packages/core/.venv/bin/python -m pytest packages/core/tests/test_domain_synthesis_cli.py -q`
  - Result: `1 passed`
- `packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `213 passed`

## Verified Smoke Checks

- Temporary workspace no-branch synthesis:
  - command: `forecast-harness synthesize-domain --workspace-root <tmp> --slug product-recall --class-name ProductRecallPack --description "Product recall response" --focus-entity-rule-min-count 2 --canonical-stage trigger --canonical-stage response --canonical-stage resolution --field-schema severity=float --field-schema recall_readiness=float --actor-category company --actor-category regulator --actor-category customers --evidence-category "safety reports" --evidence-category-term-json '{"safety reports":["injuries"]}' --semantic-alias-group-json '["recall","withdrawal"]' --starter-source-json '{"kind":"report","description":"Incident reports"}' --replay-seed-case-json '<case-json>' --no-branch`
  - result:
    - generated manifest file
    - generated replay file
    - generated domain pack file
    - generated starter test
    - updated registry file
  - dynamic import of the generated `product-recall` pack succeeded and returned slug `product-recall`
- Temporary git-repo branch-promotion synthesis:
  - command: `forecast-harness synthesize-domain --workspace-root <tmprepo> --slug product-recall --class-name ProductRecallPack --description "Product recall response" --focus-entity-rule-min-count 2 --canonical-stage trigger --canonical-stage response --canonical-stage resolution --field-schema severity=float --field-schema recall_readiness=float --actor-category company --actor-category regulator --actor-category customers --evidence-category "safety reports" --evidence-category-term-json '{"safety reports":["injuries"]}' --semantic-alias-group-json '["recall","withdrawal"]' --starter-source-json '{"kind":"report","description":"Incident reports"}' --replay-seed-case-json '<case-json>'`
  - result:
    - branch created: `codex/domain-synthesis-product-recall-20260421`
    - head commit message: `feat: synthesize product-recall domain`

## Current Boundary

- The synthesis path edits only domain-owned assets:
  - `knowledge/domains/<slug>.json`
  - `knowledge/replays/<slug>.json`
  - `packages/core/src/forecasting_harness/domain/<slug>.py`
  - starter test file
  - domain registry entry
- It does not edit:
  - the MCTS engine
  - generic workflow code
  - retrieval core
  - replay framework
- New domains currently start as generated template-backed packs rather than bespoke handwritten implementations.
