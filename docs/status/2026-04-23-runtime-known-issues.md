# Runtime Known Issues

Date: 2026-04-23

This note records the remaining verified runtime issues after the 2026-04-23 priority review-fix pass. These are intentionally tracked here instead of being mixed into the accepted behavior claims in [README.md](../../README.md).

## Verified Open Issues

- Replay "calibration" is still regression-derived rather than outcome-derived.
  - Verified in [packages/core/src/forecasting_harness/replay.py](../../packages/core/src/forecasting_harness/replay.py): domain confidence profiles are built from `top_branch_match` against replay-case expected branch labels, not from resolved historical outcome distributions.
  - Implication: replay confidence is a deterministic regression signal, not validated real-world forecast skill.

- `interstate-crisis` still encodes a narrow related-actor heuristic.
  - Verified in [packages/core/src/forecasting_harness/domain/interstate_crisis.py](../../packages/core/src/forecasting_harness/domain/interstate_crisis.py): `suggest_related_actors()` special-cases the U.S.-Iran frame, including common `US` / `United States` aliases, and otherwise returns an empty list.
  - Implication: many non-U.S.-Iran crisis runs still need manual suggested-entity enrichment.

- `interstate-crisis` still forces a bilateral focal frame.
  - Verified in [packages/core/src/forecasting_harness/domain/interstate_crisis.py](../../packages/core/src/forecasting_harness/domain/interstate_crisis.py): `validate_intake()` requires exactly two `focus_entities`.
  - Implication: triadic or coalition-heavy crises are still approximated through suggested entities rather than native multi-principal modeling.

- Recommended run lenses still lack an explicit rationale string.
  - Verified in [packages/core/src/forecasting_harness/workflow/service.py](../../packages/core/src/forecasting_harness/workflow/service.py) and [packages/core/src/forecasting_harness/workflow/reporting.py](../../packages/core/src/forecasting_harness/workflow/reporting.py): the workflow/report surfaces the selected and recommended lens payloads, but not a human-readable explanation for why the recommendation changed.
  - Implication: strong analytical commitments can still appear as silent lens swaps unless the user inspects the raw payloads closely.

- `interstate-crisis` search depth is still bounded by a compact pack configuration.
  - Verified in [packages/core/src/forecasting_harness/domain/interstate_crisis.py](../../packages/core/src/forecasting_harness/domain/interstate_crisis.py): `search_config()` returns `iterations=32`, `max_depth=4`, `rollout_depth=3`.
  - Implication: raising the runtime iteration count can improve visit stability, but it does not by itself create a deeper or broader causal tree for this pack.

## Explicitly Fixed In The Priority Pass

- Behavior-profile inference no longer attributes trait hits to any actor merely mentioned in the same passage.
- Fallback replay confidence no longer renders as a normal `low` / `medium` / `high` calibrated bucket in reports.
