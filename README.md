# Forecasting Harness

Local-first forecasting harness for scenario analysis. The repo contains a shared deterministic Python core, repo-owned domain manifests and replay cases, a packaged adapter runtime for Codex/Claude-style workflows, and local artifact storage under `.forecast/`.

## Repo State

- `main` is the accepted baseline branch.
- This README describes the accepted `main` state, including the actor-utility defaults, replay calibration improvements, and local neural embedding support.

Verified on `main` on 2026-04-22:

- Full suite:
  - `PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest packages/core -q`
  - `313 passed in 11.26s`
- Checked-in smoke campaign:
  - `PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest packages/core/tests/test_smoke_campaign.py -q`
  - `20 passed in 3.22s`

## Repository Layout

- [packages/core/src/forecasting_harness](packages/core/src/forecasting_harness)
  Shared core code: workflow, retrieval, simulation, replay, domain packs, and CLI.
- [packages/core/tests](packages/core/tests)
  Unit tests, replay coverage, adapter-doc checks, and the realistic smoke campaign.
- [knowledge/domains](knowledge/domains)
  Repo-owned manifests for built-in domains.
- [knowledge/replays](knowledge/replays)
  Built-in replay corpus used for regression and calibration checks.
- [adapters](adapters)
  Repo-owned local Codex and Claude bundles that install and smoke-test against the shared packaged adapter runtime.
- [docs/status](docs/status)
  Verified status notes and branch-specific pass summaries.
- `.forecast/`
  Local generated run artifacts. This is runtime data, not source code.
- `.worktrees/`
  Local git worktrees for development branches. These are workspace management, not product code.

## Current Capabilities

This repo state includes actor-utility and replay-calibration behavior on top of the existing workflow core:

- belief-state compilation now infers actor utility preference fields from approved evidence and case framing
- actor-aware scoring and run-lens recommendation now exist as shared `DomainPack` defaults, so new and existing domains inherit actor-aware behavior even without custom pack code
- approval packets now surface `actor_preferences` and `recommended_run_lens`
- simulation aggregation now includes actor impacts and aggregate-score breakdowns
- reports now expose actor-utility and aggregation-lens summaries
- focal-actor aggregation now uses an explicit `focal_weight` instead of a hidden multiplier
- `aggregation_mode` is now an extensible validated string rather than a closed literal, so future modes like `coalitional` or `adversarial` can be added without a schema break
- destabilization penalty now tracks the worst negative actor utility outcome instead of reusing a static actor trait
- domain-specific actor-utility hooks still exist where they add value, including `interstate-crisis`, `company-action`, and `pandemic-response`
- the shared actor-aware default now explicitly requires `score_state()` to provide `escalation`, `negotiation`, and `economic_stress` whenever actor preferences are present
- the CLI `simulate` command now defaults to a `10000`-iteration runtime search budget for serious analysis
- the interstate replay slice now includes `philippines-china-shoal`
- the built-in replay corpus now contains `40` cases, including `28` source-attributed historically anchored cases
- replay calibration summaries now expose structured per-case attention items and aggregated failure-type counts
- simulation payloads, revision summaries, and generated reports now expose replay-backed calibrated branch confidence buckets derived from the built-in replay corpus
- the repo now includes a deterministic knowledge compiler that can turn approved evidence or replay misses into candidate evidence categories, semantic aliases, manifest state terms, and action biases
- compiler proposals now flow into the existing protected domain-evolution suggestion store instead of mutating manifests or pack code directly
- the CLI now supports `compile-revision-knowledge` and `compile-replay-knowledge` so compiler candidates can be generated and inspected explicitly
- the CLI now supports `list-builtin-replay-cases` in addition to corpus and calibration summaries
- the CLI now supports `run-builtin-replay-retuning`, which runs the full built-in replay corpus one domain at a time through the protected retuning loop
- built-in replay retuning now prioritizes weaker domains first, rejects mixed-domain payloads, and treats inferred-field coverage as a first-class non-regression metric alongside top-branch, root-strategy, and evidence-source accuracy
- the accepted domain deepening pass expanded replay-justified election coalition-arithmetic and market-fragility modeling, and the checked-in smoke campaign now includes dedicated `election-hung-parliament` and `market-bank-rescue` scenarios
- synthesized domains now render explicit pack-local Python methods for field inference, action priors, transition logic, and objective recommendation hooks, and the generated pack tests pin those synthesized behaviors instead of stopping at import success
- the corpus now supports a persisted local semantic backend choice plus `rebuild-corpus-embeddings` for upgrading existing vector rows
- the retrieval layer now supports optional local neural embeddings through the `semantic-local` extra while preserving the deterministic hashed baseline as a fallback

Recent correctness fixes included in `main`:

- the recommended run lens becomes the default when no explicit lens is selected
- `US`, `U.S.`, and `United States` now persist as the same canonical actor id
- behavior-profile changes now block unsafe warm-start reuse
- report and query summaries preserve the engine’s explored-before-unexplored branch ordering

### Phase 2 ingestion additions

This branch extends corpus ingestion with a bounded set of saved-document formats:

- `ingest-file` and `ingest-directory` now accept `.xlsx` spreadsheets, plain `.html`/`.htm` pages, and archived saved pages in `.webarchive`, `.mhtml`, `.mht`, and `.eml` containers.
- Spreadsheet ingestion keeps stable row-level anchors using sheet and cell ranges, for example `sheet:Signals!A1:B1`.
- HTML and archive ingestion preserves parsed page metadata when available, including title and a normalized `YYYY-MM-DD` published date.
- HTML chunking is intentionally limited to text-bearing block content such as headings, paragraphs, lists, and similar block elements.
- Archive support is bounded to files that expose a main HTML body or web-archive main resource; OCR and image-only page extraction remain out of scope.

Detailed recent notes:
- [2026-04-21-actor-utility-pass.md](docs/status/2026-04-21-actor-utility-pass.md)
- [2026-04-21-replay-calibration-v2.md](docs/status/2026-04-21-replay-calibration-v2.md)
- [2026-04-21-replay-retuning-v2.md](docs/status/2026-04-21-replay-retuning-v2.md)
- [2026-04-22-local-neural-embeddings-v1.md](docs/status/2026-04-22-local-neural-embeddings-v1.md)
- [2026-04-22-probability-calibration-v1.md](docs/status/2026-04-22-probability-calibration-v1.md)
- [2026-04-22-knowledge-compiler-v1.md](docs/status/2026-04-22-knowledge-compiler-v1.md)
- [2026-04-22-domain-retuning-v1.md](docs/status/2026-04-22-domain-retuning-v1.md)
- [2026-04-22-domain-synthesis-v2.md](docs/status/2026-04-22-domain-synthesis-v2.md)

## Install

From the repo root, use any Python 3.12+ interpreter to build the checked-in local verification environment under `packages/core/.venv`:

```bash
PYTHON=/path/to/python3.12
"$PYTHON" -m venv packages/core/.venv
source packages/core/.venv/bin/activate
pip install -e 'packages/core[dev]'
```

To enable the local neural embedding backend as well:

```bash
pip install -e 'packages/core[dev,semantic-local]'
```

## How To Use

### 1. Discover available domains

```bash
forecast-harness list-domain-packs
```

### 2. Start a run through the packaged adapter runtime

```bash
RUN_ROOT=.forecast
forecast-harness run-adapter-action \
  --root "$RUN_ROOT" \
  --run-id china-taiwan-1 \
  --revision-id r1 \
  --action start-run \
  --domain-pack interstate-crisis
```

### 3. Save intake through the same runtime surface

```bash
forecast-harness run-adapter-action \
  --root "$RUN_ROOT" \
  --run-id china-taiwan-1 \
  --revision-id r1 \
  --action save-intake-draft \
  --event-framing "Assess 30-day crisis paths in a China-Taiwan escalation scenario." \
  --focus-entity China \
  --focus-entity Taiwan \
  --current-development "Cross-strait signaling intensifies around the Taiwan Strait after a political trigger." \
  --current-stage trigger \
  --time-horizon 30d
```

### 4. Let the runtime drive the next step

This is the adapter-facing execution surface. Each call applies one action and returns the next turn:

```bash
CORPUS_DB=.forecast/corpus.db
forecast-harness run-adapter-action \
  --root "$RUN_ROOT" \
  --corpus-db "$CORPUS_DB" \
  --candidate-path /path/to/local/docs \
  --run-id china-taiwan-1 \
  --revision-id r1 \
  --action batch-ingest-recommended
```

Use the returned:

- `executed_action`
- `action_result`
- `headline`
- `user_message`
- `recommended_runtime_action`
- `actions`
- `context`

for the next step instead of inferring workflow state yourself.

### 5. Inspect or recover the current stage when needed

If you need to query the current stage without executing a mutation:

```bash
forecast-harness draft-conversation-turn \
  --root "$RUN_ROOT" \
  --corpus-db "$CORPUS_DB" \
  --run-id china-taiwan-1 \
  --revision-id r1
```

### 6. Draft and curate evidence

```bash
forecast-harness run-adapter-action \
  --root "$RUN_ROOT" \
  --corpus-db "$CORPUS_DB" \
  --run-id china-taiwan-1 \
  --revision-id r1 \
  --action draft-evidence-packet
```

Then keep only the evidence ids you want:

```bash
forecast-harness run-adapter-action \
  --root "$RUN_ROOT" \
  --run-id china-taiwan-1 \
  --revision-id r1 \
  --action curate-evidence-draft \
  --keep-evidence-id ev-1 \
  --keep-evidence-id ev-2
```

If you need to replace the evidence packet directly instead of curating the drafted ids in place:

```bash
forecast-harness run-adapter-action \
  --root "$RUN_ROOT" \
  --run-id china-taiwan-1 \
  --revision-id r1 \
  --action save-evidence-draft \
  --item-json '{"evidence_id":"r1-ev-1","source_id":"doc-1","source_title":"Doc 1","reason":"Analyst-selected evidence"}'
```

### 7. Inspect the approval packet

This branch’s main review surface appears here:

```bash
forecast-harness draft-approval-packet \
  --root "$RUN_ROOT" \
  --run-id china-taiwan-1 \
  --revision-id r1
```

Inspect the returned:

- `actor_preferences`
- `recommended_run_lens`

before approval.

### 8. Approve, simulate, and inspect the result

```bash
forecast-harness run-adapter-action \
  --root "$RUN_ROOT" \
  --run-id china-taiwan-1 \
  --revision-id r1 \
  --action approve-revision \
  --assumption "Both sides prefer bounded signaling to immediate total war."

forecast-harness run-adapter-action \
  --root "$RUN_ROOT" \
  --run-id china-taiwan-1 \
  --revision-id r1 \
  --action simulate
forecast-harness summarize-revision --root "$RUN_ROOT" --run-id china-taiwan-1 --revision-id r1
forecast-harness generate-report --root "$RUN_ROOT" --run-id china-taiwan-1 --revision-id r1
```

The default simulation budget is `10000` MCTS iterations. To change it for a specific run:

```bash
forecast-harness simulate \
  --root "$RUN_ROOT" \
  --run-id china-taiwan-1 \
  --revision-id r1 \
  --iterations 3000
```

### 9. Create a child revision when the situation changes

```bash
forecast-harness begin-revision-update \
  --root "$RUN_ROOT" \
  --run-id china-taiwan-1 \
  --parent-revision-id r1 \
  --revision-id r2
```

### 10. Upgrade a corpus to local neural embeddings

After installing the `semantic-local` extra, rebuild the stored vectors once and persist the new backend choice in the corpus DB:

```bash
forecast-harness rebuild-corpus-embeddings \
  --corpus-db "$CORPUS_DB" \
  --semantic-backend neural
```

Future ingests into that same corpus will reuse the stored backend preference automatically.

## Verification Commands

Full suite:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest packages/core -q
```

Checked-in smoke campaign:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m pytest packages/core/tests/test_smoke_campaign.py -q
```

Built-in replay and calibration checks:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli summarize-builtin-replay-corpus
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli list-builtin-replay-cases
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli run-builtin-replay-suite
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli summarize-replay-calibration
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli run-replay-retuning --domain-pack company-action --no-branch
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli run-builtin-replay-retuning --workspace-root /tmp/replay-retuning --no-branch
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli rebuild-corpus-embeddings --corpus-db .forecast/corpus.db --semantic-backend neural
```

## Adapters

Verified adapter-facing pieces:

- Codex install guide: [docs/install-codex.md](docs/install-codex.md)
- Claude install guide: [docs/install-claude-code.md](docs/install-claude-code.md)
- Codex skill: [adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md](adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md)
- Claude skill: [adapters/claude/forecast-harness/skills/forecast-harness/SKILL.md](adapters/claude/forecast-harness/skills/forecast-harness/SKILL.md)
- Codex bundle installer: [adapters/codex/forecast-harness/install.py](adapters/codex/forecast-harness/install.py)
- Claude bundle installer: [adapters/claude/forecast-harness/install.py](adapters/claude/forecast-harness/install.py)
- Codex bundle smoke: [adapters/codex/forecast-harness/smoke.py](adapters/codex/forecast-harness/smoke.py)
- Claude bundle smoke: [adapters/claude/forecast-harness/smoke.py](adapters/claude/forecast-harness/smoke.py)

Current boundary:

- the deterministic core now includes a packaged adapter runtime through `run-adapter-action`
- `draft-conversation-turn` remains available as a query-only inspection and recovery surface
- Codex and Claude now also ship repo-owned local installer and smoke bundles; marketplace distribution remains out of scope

## Detailed Status Notes

- Actor-utility pass:
  - [2026-04-21-actor-utility-pass.md](docs/status/2026-04-21-actor-utility-pass.md)
- Replay calibration expansion:
  - [2026-04-21-replay-calibration-v2.md](docs/status/2026-04-21-replay-calibration-v2.md)
- High default iterations:
  - [2026-04-21-high-default-iterations.md](docs/status/2026-04-21-high-default-iterations.md)
- Adapter runtime packaging:
  - [2026-04-21-adapter-runtime-v1.md](docs/status/2026-04-21-adapter-runtime-v1.md)
- Replay retuning:
  - [2026-04-21-replay-retuning-v1.md](docs/status/2026-04-21-replay-retuning-v1.md)
- Broader replay history plus retuning:
  - [2026-04-21-replay-retuning-v2.md](docs/status/2026-04-21-replay-retuning-v2.md)
- Local neural embeddings:
  - [2026-04-22-local-neural-embeddings-v1.md](docs/status/2026-04-22-local-neural-embeddings-v1.md)
- Replay expansion to the frozen 40-case target:
  - [2026-04-22-replay-expansion-v3.md](docs/status/2026-04-22-replay-expansion-v3.md)
- Direct evidence runtime editing:
  - [2026-04-21-evidence-runtime-v1.md](docs/status/2026-04-21-evidence-runtime-v1.md)
- Local adapter packaging:
  - [2026-04-22-adapter-packaging-v2.md](docs/status/2026-04-22-adapter-packaging-v2.md)
- Final repo-completion closeout:
  - [2026-04-22-repo-completion-final.md](docs/status/2026-04-22-repo-completion-final.md)
- Broader repo status:
  - [2026-04-20-project-status.md](docs/status/2026-04-20-project-status.md)

## Current Gaps

- OCR-backed PDF ingestion is deferred rather than open-ended; text-extractable PDFs already work, and adapter-side PDF handling covers image-heavy cases for now.
