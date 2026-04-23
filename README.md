# Scenario Lab

> Experimental preview: local-first scenario analysis you can run in natural language with Codex or Claude.

Scenario Lab helps you turn a developing situation into a structured scenario run, gather and approve evidence, simulate multiple branches, and generate readable reports.

## Quickstart

Run the built-in local demo:

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli demo-run --root .forecast
```

Expected:

- `demo-run complete`
- generated run artifacts under `.forecast/runs/demo-run`

## Natural-Language Workflow

- `Start a U.S.-Iran scenario run for the next 30 days`
- `Draft the evidence packet`
- `Approve and simulate`
- `Update the run with a new Strait of Hormuz development`

## What it does

Scenario Lab is a local-first scenario workflow built on the repo's verified forecasting harness CLI and packaged adapter runtime. It lets you create a run, save structured intake, curate evidence, approve a revision, simulate branches, and generate a report from local artifacts under `.forecast/`.

## Quickstart

The first-use setup and demo flow are documented in [docs/quickstart.md](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/scenario-lab-public-release/docs/quickstart.md).

## Natural-language workflow

The prompt-style workflow examples and runtime-action note are documented in [docs/natural-language-workflow.md](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/scenario-lab-public-release/docs/natural-language-workflow.md).

## U.S.-Iran demo

The public `U.S.-Iran` example starter page lives in [docs/demo-us-iran.md](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/scenario-lab-public-release/docs/demo-us-iran.md). Task 3 replaces that starter content with the exact verified workflow captured from the repo.

## Install with Codex / Claude

- Codex install notes: [docs/install-codex.md](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/scenario-lab-public-release/docs/install-codex.md)
- Claude install notes: [docs/install-claude-code.md](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/scenario-lab-public-release/docs/install-claude-code.md)

## What's included in this preview

The current preview surface is summarized in [docs/release-notes/public-preview.md](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/scenario-lab-public-release/docs/release-notes/public-preview.md):

- local-first scenario workflow
- replay-backed calibration
- packaged local Codex and Claude integrations
- spreadsheet and web-archive ingestion
- protected domain evolution and synthesis

## Current limits

The current limitations are documented in [docs/limitations.md](/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/scenario-lab-public-release/docs/limitations.md).

- Output quality depends heavily on the approved evidence packet.
- Output quality depends heavily on the depth and quality of the domain pack.
- OCR-backed PDF ingestion is intentionally deferred in the current public preview.

## Minimal builder section

If you want the lowest-level workflow surface instead of the built-in demo, use the verified CLI commands already present in the repo:

```bash
forecast-harness start-run --root .forecast --run-id crisis-1 --domain-pack interstate-crisis
forecast-harness save-intake-draft --root .forecast --run-id crisis-1 --revision-id r1
forecast-harness run-adapter-action --root .forecast --run-id crisis-1 --revision-id r1 --action draft-evidence-packet
forecast-harness approve-revision --root .forecast --run-id crisis-1 --revision-id r1 --assumption "Bounded escalation remains more likely than immediate full-scale war."
forecast-harness simulate --root .forecast --run-id crisis-1 --revision-id r1
forecast-harness generate-report --root .forecast --run-id crisis-1 --revision-id r1
```
