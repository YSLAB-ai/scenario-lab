# Pandemic Domain Benchmark

Date: 2026-04-21

## Scope

This pass tested a key workflow goal directly: whether the repo can support creating a new domain pack from zero, inside the existing harness, and then replay that new pack through the same deterministic workflow, search, and calibration surfaces.

The new domain added in this pass is:

- `pandemic-response`

Repo-owned artifacts added for the benchmark:

- domain pack:
  - `packages/core/src/forecasting_harness/domain/pandemic_response.py`
- domain manifest:
  - `knowledge/domains/pandemic-response.json`
- replay cases:
  - `knowledge/replays/pandemic-response.json`

## Verified Changes

- The domain registry now includes `pandemic-response`.
- `forecast-harness list-domain-packs` now includes `pandemic-response`.
- The built-in replay corpus now contains `12` cases across `7` replay files.
- The built-in replay corpus now contains `2` pandemic-response cases:
  - `pandemic-first-wave`
  - `pandemic-vaccine-wave`
- The new pack infers these causal state fields from approved evidence:
  - `hospital_strain`
  - `policy_alignment`
  - `public_compliance`
  - `testing_capacity`
  - `transmission_pressure`
  - `vaccine_readiness`

## Verified Outcomes

Replay verification:

- `pandemic-first-wave` -> `Containment push (coordination holds)`
- `pandemic-vaccine-wave` -> `Vaccine acceleration (uptake improves)`

Calibration verification:

- `pandemic-response.count = 2`
- `pandemic-response.top_branch_accuracy = 1.0`
- `pandemic-response.root_strategy_accuracy = 1.0`
- `pandemic-response.evidence_source_accuracy = 1.0`
- `pandemic-response.average_inferred_field_coverage = 1.0`

## Verification Commands

- `packages/core/.venv/bin/python -m pytest packages/core -q`
  - Result: `201 passed in 2.09s`
- `PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli summarize-builtin-replay-corpus`
  - Result:
    - `case_count = 12`
    - `files = 7`
    - includes domain `pandemic-response`
- `PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli summarize-replay-calibration`
  - Result:
    - `overall_top_branch_accuracy = 1.0`
    - `overall_root_strategy_accuracy = 1.0`
    - `domains_needing_attention = []`
    - includes `pandemic-response` domain metrics above

## Assessment

This benchmark does not prove real-world pandemic forecasting accuracy. It does verify something narrower and important:

- the existing harness can absorb a new domain from zero
- the new domain can be wired into manifests, replay cases, registry discovery, deterministic MCTS, and calibration reporting without bespoke framework changes
- the new domain can produce differentiated retrospective outcomes through the same core pipeline as the existing packs
