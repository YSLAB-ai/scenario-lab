# Scenario Lab

> Experimental preview: Monte Carlo simulation for real-world events you can run locally with Codex or Claude.

Scenario Lab is a Monte Carlo simulation engine for real-world events such as regional conflict, markets, politics, and company decision-making.

![Scenario Lab workflow](docs/assets/scenario-lab-workflow.png)

## What Is It

Scenario Lab turns a developing situation into a structured simulation run. You give it the actors, the current development, and the evidence you want to approve. It then explores many branching futures with Monte Carlo tree search and ranks the branches it finds.

At a high level, the engine works like this:

- A domain pack defines the actors, phases, and action space for a type of event such as an interstate crisis, a market shock, or a company decision.
- The approved evidence packet and the case framing are compiled into a belief state with actor behavior profiles and domain-specific fields.
- The simulation engine runs `mcts` over that state, proposing actions, sampling transitions, and scoring resulting branches.
- Reports turn the searched branches into readable outcomes, scenario families, and calibrated confidence labels.

The same runtime can be used for regional conflict, market stress, political bargaining, and company-response cases because the domain packs carry different rules and state fields.

## Quickstart

The full first-use flow is in [docs/quickstart.md](docs/quickstart.md). The shortest local setup is:

```bash
git clone git@github.com:YSLAB-ai/scenario-lab.git
cd scenario-lab
PYTHON=/path/to/python3.12
"$PYTHON" -m venv packages/core/.venv
source packages/core/.venv/bin/activate
pip install -e 'packages/core[dev]'
forecast-harness demo-run --root .forecast
```

You should see `demo-run complete`, then artifacts under `.forecast/runs/demo-run`.

Scenario Lab is packaged to run with:

- `Codex`: [docs/install-codex.md](docs/install-codex.md)
- `Claude Code`: [docs/install-claude-code.md](docs/install-claude-code.md)

If you want to use another coding agent, share this repo with that agent and tell it to follow [README.md](README.md), [docs/quickstart.md](docs/quickstart.md), and the linked docs for the natural-language workflow.

## Workflow And Demo

Scenario Lab is a natural-language-based interactive engine. A normal run moves through these actual runtime phases.

1. `intake`
   Runtime action: `save-intake-draft`
   What it does: captures the event framing, focus actors, current development, stage, and horizon. The repo’s guidance surface can also ask follow-up questions before the intake is locked.
2. `evidence`
   Runtime action: usually `draft-evidence-packet`
   Optional runtime action: `batch-ingest-recommended` when local candidate files exist and the workflow finds recommended ingestion targets
   What it does: shows suggested entities, follow-up questions, retrieval planning, and evidence-category coverage, then drafts or saves the evidence packet.
3. `approval`
   Runtime action: `approve-revision`
   What it does: freezes the intake, evidence, and assumptions for simulation and surfaces warnings before the revision is approved.
4. `simulation`
   Runtime action: `simulate`
   What it does: runs deterministic Monte Carlo tree search on the approved revision.
5. `report`
   Runtime action: `begin-revision-update`
   What it does: shows the top branches, scenario families, and the next step if you want to continue the run as a child revision.

The public `U.S.-Iran` example follows that exact repo workflow. A longer verified CLI transcript is in [docs/demo-us-iran.md](docs/demo-us-iran.md).

Verified `U.S.-Iran` example:

- broad question:
  - `How would a U.S.-Iran conflict at the Strait of Hormuz develop for the next 30 days?`
- intake guidance then asked exactly two follow-up questions:
  - `Which outside actor has the most leverage over the next phase?`
  - `What constraint most limits immediate escalation?`
- short user correction:
  - `Consider China. Go ahead.`
- saved intake then moved the run into `evidence`
- the evidence plan targeted:
  - `force posture`
  - `diplomatic signaling`
  - `alliance commitments`
  - `leader behavior`
  - `economic constraints`
- the approval packet carried:
  - `suggested external entity: China`
  - `no evidence drafted yet`
- approved revision counts:
  - evidence items: `0`
  - assumptions: `1`
- simulation facts:
  - search mode: `mcts`
  - iterations: `10000`
  - node count: `129`
  - top branch: `Open negotiation`
- report path from the rechecked run:
  - `/tmp/scenario-lab-us-iran-convo/run/runs/us-iran-convo/reports/r1.report.md`

The shorter phase-by-phase workflow notes are in [docs/natural-language-workflow.md](docs/natural-language-workflow.md).

## What Makes It Effective

Scenario Lab does not treat every branch as equally plausible. The branch search is shaped by domain rules, actor behavior profiles, and the evidence you approve for the case.

- Actor actions are constrained by domain packs. For example, the `company-action` pack tracks fields such as `cash_runway_months`, `brand_sentiment`, `operational_stability`, and `regulatory_pressure`.
- Those fields change the action priors and branch outcomes. In the company pack, weaker operations or higher regulatory pressure make moves like `operational-pivot`, `cost-program`, or `asset-sales` more competitive, while the state scoring also raises `economic_stress` and `escalation` when sentiment or operational stability deteriorate.
- Negative consequences are therefore punished in the ranking. A company branch that improves runway but damages brand sentiment or increases pressure can still rank worse because the downstream state becomes more fragile.
- The same pattern applies in other domains: stronger actor evidence and stronger domain knowledge produce better branch differentiation.

The repo ships with prebuilt domain knowledge, replay-backed calibration, and protected domain-evolution tools, but users should still add or modify evidence and domain assumptions for unusual scenarios.

## Current Limits

The current limitations are documented in [docs/limitations.md](docs/limitations.md).

- Output quality depends heavily on the approved evidence packet.
- Output quality depends heavily on the depth and quality of the domain pack.
- Community contribution is part of the design: replay coverage, evidence quality, and domain knowledge all improve the results over time.
- OCR-backed PDF ingestion is intentionally deferred in the current public preview.

## Others

Other useful entry points:

- public quickstart: [docs/quickstart.md](docs/quickstart.md)
- natural-language workflow notes: [docs/natural-language-workflow.md](docs/natural-language-workflow.md)
- verified `U.S.-Iran` demo: [docs/demo-us-iran.md](docs/demo-us-iran.md)
- current limitations: [docs/limitations.md](docs/limitations.md)
- preview summary: [docs/release-notes/public-preview.md](docs/release-notes/public-preview.md)

If you want the smallest runnable surface instead of the higher-level interactive workflow, use the built-in demo and inspect the generated files:

```bash
source packages/core/.venv/bin/activate
forecast-harness demo-run --root .forecast
ls .forecast/runs/demo-run
cat .forecast/runs/demo-run/report.md
cat .forecast/runs/demo-run/workbench.md
```
