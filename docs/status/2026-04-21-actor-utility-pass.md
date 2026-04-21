# Actor Utility Replay Pass

Date: 2026-04-21

## Changed Files

- `knowledge/replays/interstate-crisis.json`
- `packages/core/src/forecasting_harness/cli.py`
- `packages/core/src/forecasting_harness/compatibility.py`
- `packages/core/src/forecasting_harness/objectives.py`
- `packages/core/tests/test_replay.py`
- `packages/core/src/forecasting_harness/query_api.py`
- `packages/core/src/forecasting_harness/workflow/compiler.py`
- `packages/core/src/forecasting_harness/workflow/reporting.py`
- `packages/core/src/forecasting_harness/workflow/service.py`
- `packages/core/tests/test_cli_workflow.py`
- `packages/core/tests/test_retrieval.py`
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
- The final branch fixes also verified that:
  - actor `behavior_profile` changes now block warm-start reuse
  - the recommended run lens becomes the default when no explicit lens is selected
  - `US`, `U.S.`, and `United States` now persist as the same canonical actor id
  - report and query summaries keep the engine's explored-before-unexplored branch ordering

## Documentation

- Updated the top-level README to describe actor utility inference, grouped approval-packet surfaces, run-lens reporting, and the refreshed interstate replay coverage.
- Updated the project status note to record the verified actor-preference inference path, the approval/report surfaces, and the new shoal replay coverage.

## Verification

- Scoped replay verification passed:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core/tests/test_replay.py packages/core/tests/test_replay_library.py -q`
  - Result: `7 passed`
- Required full-suite verification passed:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `246 passed in 2.69s`

## Remaining Gaps

- The builtin replay corpus remains fixed at 12 total cases because the existing shared replay-library checks still pin that corpus size and the three-case interstate slice.
- The new shoal replay therefore replaced an older interstate replay rather than expanding the corpus size.
- The smoke-campaign fixtures outside this task’s ownership were not changed, so the new shoal case is pinned through the replay corpus and replay tests rather than the broader smoke suite.
