# Forecasting Harness

Minimal core package for forecasting harness experiments.

## Quickstart

From the repository root, set `PYTHON` to any Python 3.12+ interpreter on your system:

```bash
PYTHON=/path/to/python3.12+-interpreter
"$PYTHON" -m venv .venv
source .venv/bin/activate
pip install -e 'packages/core[dev]'
forecast-harness demo-run
```

Requires Python 3.12+.

## Current Workflow Slice

The local CLI now supports the verified workflow commands:

- `forecast-harness version`
- `forecast-harness demo-run`
- `forecast-harness list-domain-packs`
- `forecast-harness ingest-file`
- `forecast-harness ingest-directory`
- `forecast-harness list-corpus-sources`
- `forecast-harness start-run`
- `forecast-harness save-intake-draft`
- `forecast-harness draft-intake-guidance`
- `forecast-harness draft-conversation-turn`
- `forecast-harness summarize-run`
- `forecast-harness summarize-revision`
- `forecast-harness save-evidence-draft`
- `forecast-harness draft-retrieval-plan`
- `forecast-harness draft-ingestion-plan`
- `forecast-harness recommend-ingestion-files`
- `forecast-harness batch-ingest-recommended`
- `forecast-harness draft-evidence-packet`
- `forecast-harness curate-evidence-draft`
- `forecast-harness draft-approval-packet`
- `forecast-harness approve-revision`
- `forecast-harness begin-revision-update`
- `forecast-harness simulate`
- `forecast-harness run-replay-suite`
- `forecast-harness record-domain-suggestion`
- `forecast-harness analyze-domain-weakness`
- `forecast-harness run-domain-evolution`
- `forecast-harness summarize-domain-evolution`
- `forecast-harness synthesize-domain`
- `forecast-harness generate-report`

Verified current progress:

- The reusable workflow core now supports registry-backed domain-pack discovery, local corpus ingestion, revisioned runs, direct structured intake/approval inputs, draft/approved artifacts, retrieval-backed evidence drafting, deterministic intake/approval guidance, conversation-stage turn drafting, in-place evidence curation, revision updates from approved parents, belief-state compilation, revisioned simulation outputs, and report generation.
- The repository now includes eight built-in domain packs:
  - `company-action`
  - `election-shock`
  - `generic-event`
  - `interstate-crisis`
  - `market-shock`
  - `pandemic-response`
  - `regulatory-enforcement`
  - `supply-chain-disruption`
- The latest full-suite verification in this worktree on 2026-04-21 ran `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core -q` and returned `246 passed in 2.69s`.
- The workflow slice persists artifacts locally under `.forecast/runs/<run-id>/`, including revision-specific files such as `belief-state/<revision>.approved.json`, `simulation/<revision>.approved.json`, `reports/<revision>.report.md`, and `revisions/<revision>.json`, while the summary and curation commands let adapters inspect and revise runs without loading or rewriting those full artifacts by default.
- The adapter-facing path can now call `forecast-harness draft-conversation-turn` after each workflow mutation to retrieve the verified current stage, next-step message, recommended command, and narrow context payload.
- The intake schema now accepts generic fields such as `focus_entities`, `current_development`, `current_stage`, and `pack_fields`, while still accepting the older interstate-oriented aliases.
- The local corpus can now ingest curated `Markdown`, `CSV`, `JSON`, and text-extractable `PDF` files into a searchable SQLite/FTS corpus with citation-friendly chunk locations.
- The local corpus now also persists local semantic vectors per chunk and uses hybrid lexical + semantic retrieval with no external API.
- The repo now includes source-manifest scaffolding under `knowledge/domains/` for:
  - `company-action`
  - `election-shock`
  - `interstate-crisis`
  - `market-shock`
  - `pandemic-response`
  - `regulatory-enforcement`
  - `supply-chain-disruption`
- The repo-owned domain manifests now affect retrieval directly by supplying:
  - domain-specific semantic alias groups for local semantic search
  - evidence-category term maps used to diversify drafted evidence packets
- The workflow core can now draft deterministic manifest-aware planning payloads for:
  - retrieval query expansion
  - corpus ingestion gaps
- The workflow core can now also turn ingestion gaps into:
  - concrete ingest tasks
  - ranked local file recommendations
  - prioritized batch ingestion into the corpus
- Belief-state compilation now also infers actor utility preference fields from approved evidence and case framing, including:
  - `domestic_sensitivity`
  - `economic_pain_tolerance`
  - `negotiation_openness`
  - `reputational_sensitivity`
  - `alliance_dependence`
  - `coercive_bias`
- Grouped approval packets now expose:
  - `actor_preferences`
  - `recommended_run_lens`
  - focal-actor lens metadata when the recommended run lens is actor-centered
- The simulation engine now runs deterministic multi-step MCTS over `BeliefState` and writes simulation payloads with:
  - `search_mode = "mcts"`
  - `iterations`
  - `node_count`
  - `state_table_size`
  - `transposition_hits`
  - `max_depth_reached`
  - `reuse_summary`
  - `tree_nodes`
  - root `branches` preserved for the workflow/report layer
- The workflow now also supports deterministic replay-suite execution through `forecast-harness run-replay-suite`, so curated scenario cases can be re-run and scored for top-branch accuracy, evidence-source accuracy, and inferred-field coverage.
- The replay coverage now spans multiple domains in the checked test suite:
  - `company-action`
  - `market-shock`
  - `regulatory-enforcement`
- Post-search reporting now synthesizes:
  - root-route-aware `scenario_families`
  - explicit top-branch path detail
  - search-summary metadata in the generated report
- The interstate-crisis pack now infers richer causal state fields from approved evidence:
  - `alliance_pressure`
  - `mediation_window`
  - `geographic_flashpoint`
- The company-action pack now infers richer causal state fields from approved evidence:
  - `board_cohesion`
  - `operational_stability`
- The market-shock pack now infers richer causal state fields from approved evidence:
  - `contagion_risk`
  - `policy_optionality`
- The regulatory-enforcement pack now infers richer causal state fields from approved evidence:
  - `remedy_severity`
  - `litigation_readiness`
- The supply-chain-disruption pack now infers richer causal state fields from approved evidence:
  - `supplier_concentration`
  - `customer_penalty_pressure`
- The checked-in 10-scenario smoke campaign now verifies differentiated first-move outcomes across the interstate, company, and supply templates instead of collapsing those scenarios into one repeated root strategy.
- The checked-in smoke and replay coverage now also includes a from-zero `pandemic-response` benchmark pack built inside the repo from the generic harness interfaces rather than extending an existing template.
- The latest verified smoke campaign on 2026-04-21 produced these top branches:
  - `US-Iran Gulf` -> `Alliance consultation (coordinated signaling)`
  - `Japan-China Strait` -> `Signal resolve (managed signal)`
  - `India-Pakistan crisis` -> `Signal resolve (backchannel opening)`
  - `Apple CEO transition` -> `Stakeholder reset`
  - `Boeing post-reporting` -> `Contain message (message lands)`
  - `Election debate collapse` -> `Message reset (reset holds)`
  - `Market rate shock` -> `Emergency liquidity`
  - `Regulator ad-tech` -> `Internal remediation`
  - `Supply rare-earth` -> `Expedite alternatives`
  - `Supplier flooding` -> `Reserve logistics`
- The replay suite now measures both exact top-branch matches and root-strategy matches per domain.
- Simulation outputs and generated reports now expose:
  - `actor_utility_summary`
  - selected and recommended aggregation-lens summaries
  - branch-level actor impact metrics
  - top-branch aggregate score breakdowns
- The repo now also includes a protected-surface domain evolution pipeline that can:
  - record explicit user suggestions per domain
  - derive self-detected suggestions from replay misses
  - compile manifest-driven adaptive state/action overlays
  - verify before/after replay metrics
  - promote verified domain-only changes onto a standalone review branch
- The repo now also includes a protected-surface domain synthesis pipeline that can:
  - accept a structured blueprint for a brand-new domain slug
  - generate a template-backed manifest, replay seed file, pack source file, and starter test
  - update the domain registry
  - create a standalone review branch and commit without touching `main`
- The domain evolution pipeline is limited to domain-owned assets and does not edit the shared MCTS/workflow/retrieval core.
- The domain synthesis pipeline is also limited to domain-owned assets and does not edit the shared MCTS/workflow/retrieval core.
- Built-in packs now read manifest-driven adaptive overlays for:
  - state-field inference boosts
  - action-prior biases
- The repo now includes a built-in 12-case replay library under `knowledge/replays/` so replay and calibration checks can run without ad hoc JSON input.
- The built-in replay library is now split into domain-scoped files under `knowledge/replays/` instead of one monolithic JSON blob.
- The CLI now exposes:
  - `forecast-harness run-builtin-replay-suite`
  - `forecast-harness summarize-builtin-replay-corpus`
  - `forecast-harness summarize-replay-calibration`
- The calibration summary now reports:
  - overall top-branch accuracy
  - overall root-strategy accuracy
  - per-domain breakdown metrics
  - domains needing attention when accuracy or inferred-field coverage drops below threshold
- The from-zero `pandemic-response` benchmark now verifies two retrospective cases through that same replay path:
  - `pandemic-first-wave` -> `Containment push (coordination holds)`
  - `pandemic-vaccine-wave` -> `Vaccine acceleration (uptake improves)`
- A direct CLI verification on 2026-04-21 now confirms:
  - `forecast-harness summarize-builtin-replay-corpus` -> `case_count = 12`
  - `forecast-harness summarize-builtin-replay-corpus` includes domain `pandemic-response`
  - `forecast-harness summarize-replay-calibration` reports `pandemic-response` with `top_branch_accuracy = 1.0`
  - `forecast-harness summarize-replay-calibration` reports `pandemic-response` with `root_strategy_accuracy = 1.0`
- A direct CLI verification on 2026-04-21 now also confirms the domain evolution no-branch path:
  - `record-domain-suggestion` stored a pending `company-action` suggestion
  - `run-domain-evolution --no-branch` returned `promotion_decision = promoted`
  - `summarize-domain-evolution` reported `pending_suggestions = 0` and the latest evolution report
- A temporary git-repo smoke check on 2026-04-21 also confirmed the branch-promotion path:
  - `run-domain-evolution` created branch `codex/domain-evolution-company-action-20260421`
  - the branch head commit message was `feat: evolve company-action domain knowledge`
- A temporary git-repo smoke check on 2026-04-21 also confirmed the new-domain synthesis path:
  - `synthesize-domain` created branch `codex/domain-synthesis-product-recall-20260421`
  - the branch head commit message was `feat: synthesize product-recall domain`
  - the generated `product-recall` pack imported successfully after synthesis
- The built-in replay corpus still contains 12 cases, and the interstate replay slice now includes `philippines-china-shoal` to pin a preference-differentiated case where approval and report surfaces expose actor preferences plus a `domestic-politics-first` recommended run lens.
- Compatible child revisions can now warm-start from an approved parent simulation. The deterministic simulation payload persists enough node metadata for dependency-aware subtree reuse on rerun.
- The reference domain packs now perform deterministic phase-changing transitions instead of replaying the input state unchanged.
- A fresh Python 3.13 install now verifies the deterministic stage progression used by the adapter path:
  - `evidence` after `save-intake-draft`
  - `approval` after `draft-evidence-packet` and curation
  - `simulation` after `approve-revision`
  - `report` after `simulate`
  - `approval` again for a child revision created with `begin-revision-update`
- A fresh Python 3.13 install also verifies the new simulation facts:
  - `simulation/r1.approved.json` contains `search_mode = "mcts"`
  - `simulation/r1.approved.json` contains `iterations = 18` for the `interstate-crisis` pack
  - the top branch remains `Signal resolve`
  - `reports/r1.report.md` exists after simulation
- A fresh Python 3.13 child-revision smoke test now also verifies:
  - `simulation/r2.approved.json` reports `reuse_summary.enabled = true`
  - `simulation/r2.approved.json` reports `source_revision_id = "r1"`
  - the rerun reused cached nodes (`reused_nodes = 7`) and skipped invalidated ones (`skipped_nodes = 9`)
  - the rerun reported transposition metadata (`transposition_hits = 37`, `state_table_size = 14`, `node_count = 40`)
- A direct CLI check now verifies `forecast-harness list-domain-packs` returns all eight built-in domain templates.
- The retrieval layer now supports semantic-only local matches where exact FTS terms would miss, for example `ceo response` retrieving a chunk about a `chief executive`.
- The workflow can now use manifest-specific semantic aliases, for example matching `military buildup` to a chunk about `force posture` inside the `interstate-crisis` domain without exact lexical overlap.
- Evidence drafting can now label and diversify packets using manifest evidence categories such as `force posture` and `diplomatic signaling`.
- Evidence drafting can now also run with no explicit `query_text`; the core generates deterministic manifest-aware query variants from the intake.
- The CLI now exposes `draft-retrieval-plan` and `draft-ingestion-plan` so adapters can ask the core what to search for and what the local corpus is still missing.
- The CLI now exposes `recommend-ingestion-files` and `batch-ingest-recommended` so the core can map local files to domain/source roles and ingest the highest-priority candidates directly.
- Batch ingestion now stores recommended tags such as `domain`, `source_role`, and top `evidence_category` on the ingested document rows.
- A checked-in 10-scenario smoke campaign now verifies realistic runs across:
  - `interstate-crisis`
  - `company-action`
  - `election-shock`
  - `market-shock`
  - `regulatory-enforcement`
  - `supply-chain-disruption`
- That campaign exposed and the current code now fixes:
  - brittle natural-language ingestion matching
  - source-id collisions when different files shared the same stem
  - cross-run evidence contamination inside the same domain
  - ingestion planning that treated old same-domain coverage as sufficient for a new scenario
  - missing pack-field inference from approved evidence
  - over-convergent interstate root strategies driven by coarse alliance modeling
  - over-convergent company root strategies driven by shallow board and operations modeling
- A direct CLI smoke check now verifies:
  - `draft-retrieval-plan` returns deterministic `query_variants` for the current intake
  - `draft-ingestion-plan` reports covered and missing manifest evidence categories from the local corpus
  - `draft-evidence-packet` succeeds without `--query-text`
- A direct CLI smoke check now also verifies the native conversational adapter loop:
  - `draft-conversation-turn --corpus-db ... --candidate-path ...` returns `stage = evidence`
  - the same payload returns `recommended_command = forecast-harness batch-ingest-recommended`
  - the payload embeds ordered `actions` for `batch-ingest-recommended` and `draft-evidence-packet`
  - the payload embeds `intake_guidance`, `retrieval_plan`, `ingestion_plan`, and `ingestion_recommendations`

## Remaining Gaps

- The broader analyst workflow is still a local filesystem slice, not the full product described in the design spec.
- The deterministic core now supports a native conversational adapter loop through `draft-conversation-turn`, but the Codex and Claude integrations are still skill/doc-driven rather than a packaged plugin runtime that executes the loop automatically.
- Manual file-backed paths still exist for evidence replacement and bulk edits.
- The repository still relies on curated local inputs rather than open-web retrieval.
- The semantic retrieval layer is a deterministic local baseline, not a neural embedding model.
- The built-in domain packs are templates, not mature validated forecasting models.
- The source manifests define what to ingest, but they do not yet populate the local corpus automatically.
- The source manifests now guide retrieval planning and ingestion-gap reporting, but they do not yet trigger automatic ingestion or open-web acquisition.
- The source manifests now guide ingestion orchestration, but they do not yet schedule ingestion work automatically or acquire files from outside the local workspace.
- Corpus ingestion does not yet support OCR PDFs, spreadsheets, or web archives.
- The replay suite infrastructure now exists, but the repo still does not contain a large curated historical replay library or calibration loop that tunes model behavior against real outcomes.
- The repo now has a small curated replay library and a deterministic calibration summary, but it still does not contain a large historical replay corpus or a tuning loop against real outcomes.
- Domain evolution currently compiles improvements into manifest-owned overlays only. It does not yet synthesize direct edits to existing domain pack Python files or replay files.
- New-domain synthesis currently generates template-backed starter packs. It does not yet synthesize richer bespoke Python logic for a new domain beyond that generated template runtime.
