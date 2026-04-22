# Repo Completion Final

Date: 2026-04-22

## Outcome

The fixed repo-completion program in [docs/superpowers/plans/2026-04-22-repo-completion-program.md](../superpowers/plans/2026-04-22-repo-completion-program.md) is complete on accepted `main` except for the explicitly deferred OCR note. The accepted docs now leave only that deferred OCR line in the open-gap section.

## Final Verification Baseline

- Local verification environment:
  - `packages/core/.venv`
  - `packages/core/.venv/bin/python --version`
  - output: `Python 3.12.13`
- Checked replay corpus:
  - `40` built-in replay cases
  - `28` historically anchored/source-attributed cases

## Exact Command Outputs

Full suite:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest packages/core -q
```

```text
313 passed in 11.75s
```

Checked-in smoke campaign:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest packages/core/tests/test_smoke_campaign.py -q
```

```text
20 passed in 3.35s
```

Built-in replay calibration:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli summarize-replay-calibration
```

```json
{"case_count":40,"historically_anchored_case_count":28,"overall_top_branch_accuracy":1.0,"overall_root_strategy_accuracy":1.0,"overall_evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"failure_type_counts":{},"attention_items":[],"strongest_domains":["company-action","election-shock","interstate-crisis","market-shock","pandemic-response","regulatory-enforcement","supply-chain-disruption"],"weakest_domains":["company-action","election-shock","interstate-crisis","market-shock","pandemic-response","regulatory-enforcement","supply-chain-disruption"],"domains_needing_attention":[],"domain_breakdown":{"company-action":{"count":7,"top_branch_accuracy":1.0,"root_strategy_accuracy":1.0,"evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"composite_score":1.0},"election-shock":{"count":5,"top_branch_accuracy":1.0,"root_strategy_accuracy":1.0,"evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"composite_score":1.0},"interstate-crisis":{"count":6,"top_branch_accuracy":1.0,"root_strategy_accuracy":1.0,"evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"composite_score":1.0},"market-shock":{"count":6,"top_branch_accuracy":1.0,"root_strategy_accuracy":1.0,"evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"composite_score":1.0},"pandemic-response":{"count":5,"top_branch_accuracy":1.0,"root_strategy_accuracy":1.0,"evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"composite_score":1.0},"regulatory-enforcement":{"count":5,"top_branch_accuracy":1.0,"root_strategy_accuracy":1.0,"evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"composite_score":1.0},"supply-chain-disruption":{"count":6,"top_branch_accuracy":1.0,"root_strategy_accuracy":1.0,"evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"composite_score":1.0}},"domain_confidence_profiles":{"company-action":{"domain_pack":"company-action","case_count":7,"baseline_accuracy":0.889,"buckets":[{"bucket_id":"low","label":"Low","lower_bound":0.0,"upper_bound":0.34,"case_count":4,"observed_accuracy":1.0,"calibrated_confidence":0.833,"fallback_used":false},{"bucket_id":"medium","label":"Medium","lower_bound":0.34,"upper_bound":0.67,"case_count":1,"observed_accuracy":1.0,"calibrated_confidence":0.667,"fallback_used":false},{"bucket_id":"high","label":"High","lower_bound":0.67,"upper_bound":1.0,"case_count":2,"observed_accuracy":1.0,"calibrated_confidence":0.75,"fallback_used":false}]},"election-shock":{"domain_pack":"election-shock","case_count":5,"baseline_accuracy":0.857,"buckets":[{"bucket_id":"low","label":"Low","lower_bound":0.0,"upper_bound":0.34,"case_count":4,"observed_accuracy":1.0,"calibrated_confidence":0.833,"fallback_used":false},{"bucket_id":"medium","label":"Medium","lower_bound":0.34,"upper_bound":0.67,"case_count":1,"observed_accuracy":1.0,"calibrated_confidence":0.667,"fallback_used":false},{"bucket_id":"high","label":"High","lower_bound":0.67,"upper_bound":1.0,"case_count":0,"observed_accuracy":0.0,"calibrated_confidence":0.857,"fallback_used":true}]},"interstate-crisis":{"domain_pack":"interstate-crisis","case_count":6,"baseline_accuracy":0.875,"buckets":[{"bucket_id":"low","label":"Low","lower_bound":0.0,"upper_bound":0.34,"case_count":6,"observed_accuracy":1.0,"calibrated_confidence":0.875,"fallback_used":false},{"bucket_id":"medium","label":"Medium","lower_bound":0.34,"upper_bound":0.67,"case_count":0,"observed_accuracy":0.0,"calibrated_confidence":0.875,"fallback_used":true},{"bucket_id":"high","label":"High","lower_bound":0.67,"upper_bound":1.0,"case_count":0,"observed_accuracy":0.0,"calibrated_confidence":0.875,"fallback_used":true}]},"market-shock":{"domain_pack":"market-shock","case_count":6,"baseline_accuracy":0.875,"buckets":[{"bucket_id":"low","label":"Low","lower_bound":0.0,"upper_bound":0.34,"case_count":1,"observed_accuracy":1.0,"calibrated_confidence":0.667,"fallback_used":false},{"bucket_id":"medium","label":"Medium","lower_bound":0.34,"upper_bound":0.67,"case_count":5,"observed_accuracy":1.0,"calibrated_confidence":0.857,"fallback_used":false},{"bucket_id":"high","label":"High","lower_bound":0.67,"upper_bound":1.0,"case_count":0,"observed_accuracy":0.0,"calibrated_confidence":0.875,"fallback_used":true}]},"pandemic-response":{"domain_pack":"pandemic-response","case_count":5,"baseline_accuracy":0.857,"buckets":[{"bucket_id":"low","label":"Low","lower_bound":0.0,"upper_bound":0.34,"case_count":3,"observed_accuracy":1.0,"calibrated_confidence":0.8,"fallback_used":false},{"bucket_id":"medium","label":"Medium","lower_bound":0.34,"upper_bound":0.67,"case_count":1,"observed_accuracy":1.0,"calibrated_confidence":0.667,"fallback_used":false},{"bucket_id":"high","label":"High","lower_bound":0.67,"upper_bound":1.0,"case_count":1,"observed_accuracy":1.0,"calibrated_confidence":0.667,"fallback_used":false}]},"regulatory-enforcement":{"domain_pack":"regulatory-enforcement","case_count":5,"baseline_accuracy":0.857,"buckets":[{"bucket_id":"low","label":"Low","lower_bound":0.0,"upper_bound":0.34,"case_count":5,"observed_accuracy":1.0,"calibrated_confidence":0.857,"fallback_used":false},{"bucket_id":"medium","label":"Medium","lower_bound":0.34,"upper_bound":0.67,"case_count":0,"observed_accuracy":0.0,"calibrated_confidence":0.857,"fallback_used":true},{"bucket_id":"high","label":"High","lower_bound":0.67,"upper_bound":1.0,"case_count":0,"observed_accuracy":0.0,"calibrated_confidence":0.857,"fallback_used":true}]},"supply-chain-disruption":{"domain_pack":"supply-chain-disruption","case_count":6,"baseline_accuracy":0.875,"buckets":[{"bucket_id":"low","label":"Low","lower_bound":0.0,"upper_bound":0.34,"case_count":1,"observed_accuracy":1.0,"calibrated_confidence":0.667,"fallback_used":false},{"bucket_id":"medium","label":"Medium","lower_bound":0.34,"upper_bound":0.67,"case_count":5,"observed_accuracy":1.0,"calibrated_confidence":0.857,"fallback_used":false},{"bucket_id":"high","label":"High","lower_bound":0.67,"upper_bound":1.0,"case_count":0,"observed_accuracy":0.0,"calibrated_confidence":0.875,"fallback_used":true}]}}}
```

Built-in replay retuning:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli run-builtin-replay-retuning --workspace-root /tmp/repo-completion-phase10-retuning --no-branch
```

```json
{"domains":["company-action","election-shock","interstate-crisis","market-shock","pandemic-response","regulatory-enforcement","supply-chain-disruption"],"prioritized_domains":["election-shock","pandemic-response","regulatory-enforcement","interstate-crisis","market-shock","supply-chain-disruption","company-action"],"domain_count":7,"case_count":40,"weak_domain_count":0,"generated_suggestion_count":0,"per_domain":{"company-action":{"domain_slug":"company-action","case_count":7,"weak_case_count":0,"generated_suggestion_count":0,"calibration_summary":{"case_count":7,"top_branch_accuracy":1.0,"root_strategy_accuracy":1.0,"evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"domains_needing_attention":[]},"compiler_summary":{"domain_slug":"company-action","source_kind":"replay-miss","candidate_count":0,"recorded_count":0,"recorded_suggestion_ids":[],"candidates":[]},"weakness_brief":{"domain_slug":"company-action","reasons":[],"weak_cases":[],"suggested_targets":[]},"evolution_summary":null},"election-shock":{"domain_slug":"election-shock","case_count":5,"weak_case_count":0,"generated_suggestion_count":0,"calibration_summary":{"case_count":5,"top_branch_accuracy":1.0,"root_strategy_accuracy":1.0,"evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"domains_needing_attention":[]},"compiler_summary":{"domain_slug":"election-shock","source_kind":"replay-miss","candidate_count":0,"recorded_count":0,"recorded_suggestion_ids":[],"candidates":[]},"weakness_brief":{"domain_slug":"election-shock","reasons":[],"weak_cases":[],"suggested_targets":[]},"evolution_summary":null},"interstate-crisis":{"domain_slug":"interstate-crisis","case_count":6,"weak_case_count":0,"generated_suggestion_count":0,"calibration_summary":{"case_count":6,"top_branch_accuracy":1.0,"root_strategy_accuracy":1.0,"evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"domains_needing_attention":[]},"compiler_summary":{"domain_slug":"interstate-crisis","source_kind":"replay-miss","candidate_count":0,"recorded_count":0,"recorded_suggestion_ids":[],"candidates":[]},"weakness_brief":{"domain_slug":"interstate-crisis","reasons":[],"weak_cases":[],"suggested_targets":[]},"evolution_summary":null},"market-shock":{"domain_slug":"market-shock","case_count":6,"weak_case_count":0,"generated_suggestion_count":0,"calibration_summary":{"case_count":6,"top_branch_accuracy":1.0,"root_strategy_accuracy":1.0,"evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"domains_needing_attention":[]},"compiler_summary":{"domain_slug":"market-shock","source_kind":"replay-miss","candidate_count":0,"recorded_count":0,"recorded_suggestion_ids":[],"candidates":[]},"weakness_brief":{"domain_slug":"market-shock","reasons":[],"weak_cases":[],"suggested_targets":[]},"evolution_summary":null},"pandemic-response":{"domain_slug":"pandemic-response","case_count":5,"weak_case_count":0,"generated_suggestion_count":0,"calibration_summary":{"case_count":5,"top_branch_accuracy":1.0,"root_strategy_accuracy":1.0,"evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"domains_needing_attention":[]},"compiler_summary":{"domain_slug":"pandemic-response","source_kind":"replay-miss","candidate_count":0,"recorded_count":0,"recorded_suggestion_ids":[],"candidates":[]},"weakness_brief":{"domain_slug":"pandemic-response","reasons":[],"weak_cases":[],"suggested_targets":[]},"evolution_summary":null},"regulatory-enforcement":{"domain_slug":"regulatory-enforcement","case_count":5,"weak_case_count":0,"generated_suggestion_count":0,"calibration_summary":{"case_count":5,"top_branch_accuracy":1.0,"root_strategy_accuracy":1.0,"evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"domains_needing_attention":[]},"compiler_summary":{"domain_slug":"regulatory-enforcement","source_kind":"replay-miss","candidate_count":0,"recorded_count":0,"recorded_suggestion_ids":[],"candidates":[]},"weakness_brief":{"domain_slug":"regulatory-enforcement","reasons":[],"weak_cases":[],"suggested_targets":[]},"evolution_summary":null},"supply-chain-disruption":{"domain_slug":"supply-chain-disruption","case_count":6,"weak_case_count":0,"generated_suggestion_count":0,"calibration_summary":{"case_count":6,"top_branch_accuracy":1.0,"root_strategy_accuracy":1.0,"evidence_source_accuracy":1.0,"average_inferred_field_coverage":1.0,"domains_needing_attention":[]},"compiler_summary":{"domain_slug":"supply-chain-disruption","source_kind":"replay-miss","candidate_count":0,"recorded_count":0,"recorded_suggestion_ids":[],"candidates":[]},"weakness_brief":{"domain_slug":"supply-chain-disruption","reasons":[],"weak_cases":[],"suggested_targets":[]},"evolution_summary":null}}}
```

## Final Boundary

- OCR-backed PDF ingestion remains explicitly deferred.
- Public marketplace publication remains deferred; the accepted repo state only targets repo-owned local Codex and Claude bundles with installer and smoke coverage.
