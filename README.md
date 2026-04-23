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
scenario-lab demo-run --root .forecast
```

You should see `demo-run complete`, then artifacts under `.forecast/runs/demo-run`.

For a repo-owned bootstrap that parses a literal scenario prompt and returns the normal next workflow turn instead of running the full simulation immediately, use:

```bash
scenario-lab scenario --root .forecast "/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days"
```

Scenario Lab is packaged to run with:

- `Codex`: [docs/install-codex.md](docs/install-codex.md)
- `Claude Code`: [docs/install-claude-code.md](docs/install-claude-code.md)

In Claude Code specifically, this repo now also ships a native project slash command at `.claude/commands/scenario.md`, so inside Claude you can start with:

```text
/scenario how would a U.S.-Iran conflict at the Strait of Hormuz develop over the next 30 days
```

If you want to use another coding agent, share this repo with that agent and tell it to follow [README.md](README.md), [docs/quickstart.md](docs/quickstart.md), and the linked docs for the natural-language workflow.

## Workflow And Demo

Scenario Lab is a natural-language-based interactive engine. A normal run moves through these actual runtime phases.

![Scenario Lab runtime workflow](docs/assets/scenario-lab-runtime-workflow.png)

1. `intake`
   Runtime action: `save-intake-draft`
   What it does: understand the problem, identify the main actors, and set the time horizon. The repo can also ask follow-up questions before this setup is locked.
2. `evidence`
   Runtime action: usually `draft-evidence-packet`
   Optional runtime action: `batch-ingest-recommended` when local candidate files exist and the workflow finds recommended ingestion targets
   What it does: review what outside actors matter, what evidence is missing, and what sources to pull in, then draft or save the evidence packet.
3. `approval`
   Runtime action: `approve-revision`
   What it does: lock the setup, assumptions, and evidence before search, while surfacing any warnings that still matter.
4. `simulation`
   Runtime action: `simulate`
   What it does: explore many possible paths with deterministic Monte Carlo tree search.
5. `report`
   Runtime action: `begin-revision-update`
   What it does: show the top outcomes, explain the main branches, and let you continue the run if the situation changes.

The public `U.S.-Iran` example follows that exact repo workflow. A longer verified CLI transcript is in [docs/demo-us-iran.md](docs/demo-us-iran.md).

Verified deeper `U.S.-Iran` example:

- broad question:
  - `How would a U.S.-Iran conflict at the Strait of Hormuz develop for the next 30 days?`
- intake then locked:
  - main actors: `United States`, `Iran`
  - third-party actors carried into the run: `China`, `Israel`, `Gulf States`, `United Kingdom`, `France`
  - time horizon: `30d`
  - stage: `trigger`
- the evidence packet approved `7` curated items covering:
  - U.S. force posture around shipping attacks
  - UK-France maritime security coordination
  - Iran's negotiating posture under pressure
  - China's oil dependence on the Strait staying open
  - Gulf export vulnerability if Hormuz closes
  - market stress from retaliation threats
  - Israel's readiness to resume strikes
- the retrieval/evidence plan still centered the same evidence categories:
  - `force posture`
  - `diplomatic signaling`
  - `alliance commitments`
  - `leader behavior`
  - `economic constraints`
- the approval step carried `5` explicit assumptions:
  - China prefers negotiation and backchannel pressure to prolonged closure
  - Israel's deterrence credibility can pull the crisis toward strikes
  - Gulf States want protected shipping but also de-escalation
  - the United Kingdom supports a defensive escort mission
  - France supports a defensive escort mission
- approved revision counts:
  - evidence items: `7`
  - assumptions: `5`
- simulation facts:
  - search mode: `mcts`
  - iterations: `10000`
  - node count: `133`
  - transposition hits: `111`
- top ranked scenarios:
  1. `Coordinated consultation with allies` with score `0.289`
     Engine label: `Alliance consultation (coordinated signaling)`
     What this means: the next phase is led by allied consultation and coordinated public signaling.
  2. `A controlled show of resolve` with score `0.289`
     Engine label: `Signal resolve (managed signal)`
     What this means: the next phase centers on a managed signal of firmness rather than a runaway escalation.
  3. `Open negotiations` with score `0.287`
     Engine label: `Open negotiation`
     What this means: the next phase is driven by open negotiation.
- leading scenario families:
  - `Allied consultation followed by a stalled settlement track`
    Engine label: `Alliance consultation -> settlement-stalemate`
    Plain-English reading: this family starts with coordinated allied consultation and then moves into a settlement effort that stalls.
  - `A controlled signal followed by a stalled settlement track`
    Engine label: `Signal resolve -> settlement-stalemate`
    Plain-English reading: this family starts with a managed signal of resolve and then moves into a settlement effort that stalls.
  - `Open negotiations followed by a stalled settlement track`
    Engine label: `Open negotiation -> settlement-stalemate`
    Plain-English reading: this family starts with open negotiation and then moves into a settlement effort that stalls.
- inferred third-party actor pressures from the approved evidence and assumptions:
  - `China`: `domestic_sensitivity=0.62`, `negotiation_openness=0.75`
  - `Israel`: `domestic_sensitivity=0.73`, `reputational_sensitivity=0.55`
  - `Gulf States`: `alliance_dependence=0.86`
  - `United Kingdom`: `alliance_dependence=0.97`
  - `France`: `alliance_dependence=0.97`
- report path from the rechecked run:
  - `/tmp/scenario-lab-us-iran-deeper-main/run/runs/us-iran-deeper/reports/r1.report.md`

In that verified `U.S.-Iran` run, **coordinated consultation with allies** ranked first, but the top three branches were very close together. The engine slightly favored that path over a controlled show of resolve or open negotiations; it did not find a runaway winner. Engine label: `Alliance consultation (coordinated signaling)`

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
scenario-lab demo-run --root .forecast
ls .forecast/runs/demo-run
cat .forecast/runs/demo-run/report.md
cat .forecast/runs/demo-run/workbench.md
```
