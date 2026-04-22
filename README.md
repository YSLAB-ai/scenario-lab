# Forecasting Harness

Local-first forecasting harness for scenario analysis. The repo contains a shared deterministic Python core, repo-owned domain manifests and replay cases, thin Codex/Claude adapter scaffolding, and local artifact storage under `.forecast/`.

## Repo State

- `main` is the accepted baseline branch.
- `codex/actor-utility-run-lens` is a review branch. It is pushed to `origin/codex/actor-utility-run-lens` and is not merged into `main`.
- This README describes the current state of `codex/actor-utility-run-lens`.

Verified on this branch on 2026-04-21:

- Full suite:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core -q`
  - `252 passed in 2.58s`
- Checked-in smoke campaign:
  - `PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core/tests/test_smoke_campaign.py -q`
  - `16 passed in 0.67s`

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
  Thin Codex and Claude scaffolding.
- [docs/status](docs/status)
  Verified status notes and branch-specific pass summaries.
- `.forecast/`
  Local generated run artifacts. This is runtime data, not source code.
- `.worktrees/`
  Local git worktrees for development branches. These are workspace management, not product code.

## What This Branch Adds

This review branch adds actor-utility and run-lens behavior on top of the existing workflow core:

- belief-state compilation now infers actor utility preference fields from approved evidence and case framing
- approval packets now surface `actor_preferences` and `recommended_run_lens`
- simulation aggregation now includes actor impacts and aggregate-score breakdowns
- reports now expose actor-utility and aggregation-lens summaries
- focal-actor aggregation now uses an explicit `focal_weight` instead of a hidden multiplier
- destabilization penalty now tracks the worst negative actor utility outcome instead of reusing a static actor trait
- actor-utility hooks now extend beyond `interstate-crisis`, including `company-action` and `pandemic-response`
- `interstate-crisis` now uses a modestly higher default search budget (`32` iterations) so actor-centered replay cases do not collapse onto one visited root branch
- the interstate replay slice now includes `philippines-china-shoal`

This branch also includes correctness fixes that matter for review:

- the recommended run lens becomes the default when no explicit lens is selected
- `US`, `U.S.`, and `United States` now persist as the same canonical actor id
- behavior-profile changes now block unsafe warm-start reuse
- report and query summaries preserve the engine’s explored-before-unexplored branch ordering

Detailed branch note:
- [2026-04-21-actor-utility-pass.md](docs/status/2026-04-21-actor-utility-pass.md)

## Install

From the repo root, use any Python 3.12+ interpreter:

```bash
PYTHON=/path/to/python3.12
"$PYTHON" -m venv .venv
source .venv/bin/activate
pip install -e 'packages/core[dev]'
```

## How To Use

### 1. Discover available domains

```bash
forecast-harness list-domain-packs
```

### 2. Start a run

```bash
RUN_ROOT=.forecast
forecast-harness start-run --root "$RUN_ROOT" --run-id china-taiwan-1 --domain-pack interstate-crisis
```

### 3. Save intake directly from structured flags

```bash
forecast-harness save-intake-draft \
  --root "$RUN_ROOT" \
  --run-id china-taiwan-1 \
  --revision-id r1 \
  --event-framing "Assess 30-day crisis paths in a China-Taiwan escalation scenario." \
  --focus-entity China \
  --focus-entity Taiwan \
  --current-development "Cross-strait signaling intensifies around the Taiwan Strait after a political trigger." \
  --current-stage trigger \
  --time-horizon 30d
```

### 4. Let the core drive the next step

This is the adapter-facing loop surface:

```bash
CORPUS_DB=.forecast/corpus.db
forecast-harness draft-conversation-turn \
  --root "$RUN_ROOT" \
  --corpus-db "$CORPUS_DB" \
  --run-id china-taiwan-1 \
  --revision-id r1
```

Use the returned:

- `headline`
- `user_message`
- `recommended_command`
- `actions`
- `context`

for the next step instead of inferring workflow state yourself.

### 5. Ingest local evidence if recommended

If the conversation turn includes ingestion recommendations:

```bash
forecast-harness batch-ingest-recommended \
  --root "$RUN_ROOT" \
  --corpus-db "$CORPUS_DB" \
  --path /path/to/local/docs \
  --run-id china-taiwan-1 \
  --revision-id r1
```

### 6. Draft and curate evidence

```bash
forecast-harness draft-evidence-packet \
  --root "$RUN_ROOT" \
  --corpus-db "$CORPUS_DB" \
  --run-id china-taiwan-1 \
  --revision-id r1
```

Then keep only the evidence ids you want:

```bash
forecast-harness curate-evidence-draft \
  --root "$RUN_ROOT" \
  --run-id china-taiwan-1 \
  --revision-id r1 \
  --keep-evidence-id ev-1 \
  --keep-evidence-id ev-2
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
forecast-harness approve-revision \
  --root "$RUN_ROOT" \
  --run-id china-taiwan-1 \
  --revision-id r1 \
  --assumption "Both sides prefer bounded signaling to immediate total war."

forecast-harness simulate --root "$RUN_ROOT" --run-id china-taiwan-1 --revision-id r1
forecast-harness summarize-revision --root "$RUN_ROOT" --run-id china-taiwan-1 --revision-id r1
forecast-harness generate-report --root "$RUN_ROOT" --run-id china-taiwan-1 --revision-id r1
```

### 9. Create a child revision when the situation changes

```bash
forecast-harness begin-revision-update \
  --root "$RUN_ROOT" \
  --run-id china-taiwan-1 \
  --parent-revision-id r1 \
  --revision-id r2
```

## Verification Commands

Full suite:

```bash
PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core -q
```

Checked-in smoke campaign:

```bash
PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/packages/core/.venv/bin/python -m pytest packages/core/tests/test_smoke_campaign.py -q
```

Built-in replay and calibration checks:

```bash
forecast-harness summarize-builtin-replay-corpus
forecast-harness run-builtin-replay-suite
forecast-harness summarize-replay-calibration
```

## Adapters

Verified adapter-facing pieces:

- Codex install guide: [docs/install-codex.md](docs/install-codex.md)
- Claude install guide: [docs/install-claude-code.md](docs/install-claude-code.md)
- Codex skill: [adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md](adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md)
- Claude skill: [adapters/claude/skills/forecast-harness/SKILL.md](adapters/claude/skills/forecast-harness/SKILL.md)

Current boundary:

- the deterministic core has a native conversational adapter loop through `draft-conversation-turn`
- Codex and Claude are still skill/doc-driven integrations
- there is not yet a fully packaged runtime that executes the loop automatically

## Detailed Status Notes

- Branch-specific actor-utility pass:
  - [2026-04-21-actor-utility-pass.md](docs/status/2026-04-21-actor-utility-pass.md)
- Broader repo status on this branch:
  - [2026-04-20-project-status.md](docs/status/2026-04-20-project-status.md)

## Current Gaps

- The Codex and Claude integrations are still scaffolding, not a packaged runtime.
- The built-in domain packs are templates, not mature validated forecasting models.
- The replay corpus is still small.
- Some evidence replacement and bulk-edit paths remain file-backed.
