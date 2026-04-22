# Actor Utility Replay Pass

Date: 2026-04-21

## Review Handoff

- Branch under review: `codex/actor-utility-run-lens`
- This branch is pushed and not merged into `main`.
- Start with [README.md](../../README.md) for repo layout, workflow usage, and branch scope.
- Then review these files first:
  - `packages/core/src/forecasting_harness/models.py`
  - `packages/core/src/forecasting_harness/objectives.py`
  - `packages/core/src/forecasting_harness/domain/base.py`
  - `packages/core/src/forecasting_harness/domain/interstate_crisis.py`
  - `packages/core/src/forecasting_harness/workflow/compiler.py`
  - `packages/core/src/forecasting_harness/workflow/models.py`
  - `packages/core/src/forecasting_harness/workflow/service.py`
  - `packages/core/src/forecasting_harness/compatibility.py`
  - `packages/core/src/forecasting_harness/simulation/engine.py`
  - `packages/core/src/forecasting_harness/query_api.py`
  - `packages/core/src/forecasting_harness/workflow/reporting.py`

## Review Focus

- Confirm actor preference inference is deterministic and auditable.
- Confirm recommended-vs-selected run-lens behavior is coherent.
- Confirm actor alias normalization preserves reuse and focal-actor continuity.
- Confirm report and query summaries match the engine's explored-first branch ordering.
- Confirm the replay and smoke outputs still match the checked-in expectations after the branch-only changes.
- Confirm the review-fix pass:
  - makes focal weighting explicit
  - bases destabilization on branch downside instead of a static actor trait
  - extends actor-utility hooks to at least two additional packs

## Changed Files

- `knowledge/replays/interstate-crisis.json`
- `packages/core/src/forecasting_harness/cli.py`
- `packages/core/src/forecasting_harness/compatibility.py`
- `packages/core/src/forecasting_harness/domain/base.py`
- `packages/core/src/forecasting_harness/domain/company_action.py`
- `packages/core/src/forecasting_harness/domain/interstate_crisis.py`
- `packages/core/src/forecasting_harness/domain/pandemic_response.py`
- `packages/core/src/forecasting_harness/models.py`
- `packages/core/src/forecasting_harness/objectives.py`
- `packages/core/tests/test_replay.py`
- `packages/core/src/forecasting_harness/query_api.py`
- `packages/core/src/forecasting_harness/simulation/engine.py`
- `packages/core/src/forecasting_harness/workflow/compiler.py`
- `packages/core/src/forecasting_harness/workflow/models.py`
- `packages/core/src/forecasting_harness/workflow/reporting.py`
- `packages/core/src/forecasting_harness/workflow/service.py`
- `packages/core/tests/test_cli_workflow.py`
- `packages/core/tests/test_interstate_crisis_pack.py`
- `packages/core/tests/test_models.py`
- `packages/core/tests/test_retrieval.py`
- `packages/core/tests/test_reporting.py`
- `packages/core/tests/test_simulation.py`
- `packages/core/tests/test_workflow_evidence.py`
- `packages/core/tests/test_workflow_models.py`
- `packages/core/tests/test_workflow_service.py`
- `README.md`
- `docs/status/2026-04-20-project-status.md`
- `docs/status/2026-04-21-actor-utility-pass.md`

## Replay Coverage

- Refreshed the interstate replay slice with a new `philippines-china-shoal` builtin case.
- The new case is framed around the Second Thomas Shoal water-cannon crisis.
- The case now pins:
  - deterministic evidence ingestion for `shoal-water-cannon` and `beijing-hotline`
  - inferred interstate state fields
  - approval-packet `actor_preferences`
  - approval-packet `recommended_run_lens`
  - replayed top-branch and root-strategy expectations
- The strengthened replay test verifies the shoal case reaches a `domestic-politics-first` recommended run lens with `focal_actor_id = "united-states"` while the searched top branch remains `Signal resolve (managed signal)`.
- The follow-up review-fix pass preserved that replay behavior after changing actor aggregation by:
  - making focal weighting explicit through `focal_weight`
  - redefining destabilization as the worst negative actor utility score
  - raising the default `interstate-crisis` search budget from `18` to `32` iterations so the shoal replay no longer collapses onto a single visited root branch
- The latest generalization pass moved actor-aware defaults into the shared `DomainPack` base layer, so untouched packs like `market-shock` and `regulatory-enforcement` now inherit actor-impact scoring and run-lens recommendation without custom pack code.
- The final branch fixes also verified that:
  - actor `behavior_profile` changes now block warm-start reuse
  - the recommended run lens becomes the default when no explicit lens is selected
  - `US`, `U.S.`, and `United States` now persist as the same canonical actor id
  - report and query summaries keep the engine's explored-before-unexplored branch ordering
  - `company-action` and `pandemic-response` now implement `recommend_objective_profile()` and `score_actor_impacts()`

## Documentation

- Updated the top-level README to describe actor utility inference, grouped approval-packet surfaces, run-lens reporting, and the refreshed interstate replay coverage.
- Updated the project status note to record the verified actor-preference inference path, the approval/report surfaces, and the new shoal replay coverage.

## Verification

- Scoped replay verification passed:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core/tests/test_replay.py packages/core/tests/test_replay_library.py -q`
  - Result: `7 passed in 0.26s`
- Checked-in smoke campaign verification passed:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core/tests/test_smoke_campaign.py -q`
  - Result: `16 passed in 0.67s`
- Direct end-to-end smoke rerun on the same branch verified these top branches across the checked-in 12 scenarios:
  - `US-Iran Gulf` -> `Alliance consultation (coordinated signaling)`
  - `Japan-China Strait` -> `Signal resolve (managed signal)`
  - `India-Pakistan crisis` -> `Signal resolve (backchannel opening)`
  - `Apple CEO transition` -> `Stakeholder reset`
  - `Boeing post-reporting` -> `Contain message (message lands)`
  - `Election debate collapse` -> `Message reset (reset holds)`
  - `Market rate shock` -> `Emergency liquidity`
  - `Pandemic first wave` -> `Containment push (coordination holds)`
  - `Pandemic vaccine wave` -> `Vaccine acceleration (uptake improves)`
  - `Regulator ad-tech` -> `Internal remediation`
  - `Supply rare-earth` -> `Expedite alternatives`
  - `Supplier flooding` -> `Reserve logistics`
- Required full-suite verification passed:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `254 passed in 2.61s`

## Remaining Gaps

- The builtin replay corpus remains fixed at 12 total cases because the existing shared replay-library checks still pin that corpus size and the three-case interstate slice.
- The new shoal replay therefore replaced an older interstate replay rather than expanding the corpus size.
- The smoke-campaign fixtures outside this task’s ownership were not changed, so the new shoal case is pinned through the replay corpus and replay tests rather than the broader smoke suite.
