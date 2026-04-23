# Scenario Lab Demo: U.S.-Iran Strait of Hormuz

Verified on April 23, 2026 in this repository on the current local `main`.

This demo uses the current public CLI and a deeper `U.S.-Iran` run than the short README summary. It keeps the same repo workflow, but it adds a richer evidence packet, explicit third-party assumptions, and a full `10000`-iteration search.

## Verified setup

```bash
WORKDIR=/tmp/scenario-lab-us-iran-deeper-main
ROOT="$WORKDIR/run"
CORPUS="$WORKDIR/corpus.db"
mkdir -p "$WORKDIR"
```

## 1. Start the run and save intake

```bash
packages/core/.venv/bin/scenario-lab run-adapter-action \
  --root "$ROOT" \
  --run-id us-iran-deeper \
  --revision-id r1 \
  --action start-run \
  --domain-pack interstate-crisis
```

Exact observed runtime facts:

```json
{
  "executed_action": "start-run",
  "turn": {
    "stage": "intake",
    "recommended_runtime_action": "save-intake-draft",
    "user_message": "Revision is ready for intake. Capture the event framing and core entities first."
  }
}
```

Then save the actual intake:

```bash
packages/core/.venv/bin/scenario-lab run-adapter-action \
  --root "$ROOT" \
  --corpus-db "$CORPUS" \
  --run-id us-iran-deeper \
  --revision-id r1 \
  --action save-intake-draft \
  --event-framing 'Assess the most likely 30-day paths for a U.S.-Iran Strait of Hormuz crisis with major third-party pressure.' \
  --focus-entity 'United States' \
  --focus-entity 'Iran' \
  --current-development 'Shipping attacks, retaliatory threats, and ceasefire instability are raising the risk of renewed confrontation around the Strait of Hormuz.' \
  --current-stage 'trigger' \
  --time-horizon '30d' \
  --suggested-entity 'China' \
  --suggested-entity 'Israel' \
  --suggested-entity 'Gulf States' \
  --suggested-entity 'United Kingdom' \
  --suggested-entity 'France'
```

Exact observed follow-up state:

```json
{
  "executed_action": "save-intake-draft",
  "turn": {
    "stage": "evidence",
    "recommended_runtime_action": "draft-evidence-packet",
    "follow_up_questions": [
      "Which outside actor has the most leverage over the next phase?",
      "What constraint most limits immediate escalation?"
    ],
    "target_evidence_categories": [
      "force posture",
      "diplomatic signaling",
      "alliance commitments",
      "leader behavior",
      "economic constraints"
    ]
  }
}
```

So the run was framed with:

- main actors: `United States`, `Iran`
- third-party actors carried into the case: `China`, `Israel`, `Gulf States`, `United Kingdom`, `France`
- time horizon: `30d`
- current stage: `trigger`

## 2. Save a richer evidence packet

For this deeper run, the evidence packet was saved directly instead of relying on an empty draft.

The exact packet contained `7` evidence items. These source titles were used:

1. `AP Apr. 23, 2026: U.S. threat posture around Hormuz shipping attacks`
2. `AP Apr. 17, 2026: UK-France maritime mission and wider diplomacy`
3. `AP Apr. 18, 2026: Iran says talks stall under maximalist U.S. demands`
4. `AP Mar. 18, 2026: China remains major buyer of Iranian oil`
5. `AP Mar. 19, 2026: Gulf export alternatives only partly offset Strait disruption`
6. `AP Apr. 21, 2026: market stress rises with ship attacks and retaliation threats`
7. `AP Apr. 23, 2026: Israel signals readiness to resume major strikes`

Each item was saved with the current public `EvidencePacket` shape: `evidence_id`, `source_id`, `source_title`, `reason`, `citation_refs`, and `raw_passages`.

```bash
packages/core/.venv/bin/scenario-lab run-adapter-action \
  --root "$ROOT" \
  --run-id us-iran-deeper \
  --revision-id r1 \
  --action save-evidence-draft \
  --input "$WORKDIR/evidence.json"
```

Exact observed runtime facts:

```json
{
  "executed_action": "save-evidence-draft",
  "turn": {
    "stage": "approval",
    "recommended_runtime_action": "approve-revision",
    "available_sections": [
      "intake",
      "evidence"
    ]
  }
}
```

## 3. Approve explicit third-party assumptions

The approved assumptions file for this run contained:

1. `China's leadership views prolonged Strait closure as a domestic and economic risk, and Chinese officials prefer negotiation, diplomacy, and backchannel pressure over coercive escalation.`
2. `Israel's leadership and public resolve are tied to deterrence credibility, and Israel is prepared to resume strikes if negotiations mainly buy time.`
3. `Gulf States prefer alliance coordination and security support for shipping, but they also want diplomacy and de-escalation to keep energy exports moving.`
4. `The United Kingdom supports alliance coordination, maritime security support, and diplomatic signaling through a defensive escort mission.`
5. `France supports alliance coordination, maritime security support, and diplomatic signaling through a defensive escort mission.`

The run kept the repo's default aggregation lens:

- objective profile: `balanced-system`
- aggregation mode: `balanced-system`

Approval command:

```bash
packages/core/.venv/bin/scenario-lab run-adapter-action \
  --root "$ROOT" \
  --run-id us-iran-deeper \
  --revision-id r1 \
  --action approve-revision \
  --input "$WORKDIR/assumptions.json"
```

Exact observed runtime facts:

```json
{
  "executed_action": "approve-revision",
  "turn": {
    "stage": "simulation",
    "recommended_runtime_action": "simulate",
    "context": {
      "evidence_item_count": 7,
      "assumption_count": 5
    }
  }
}
```

## 4. Simulate and generate the report

```bash
packages/core/.venv/bin/scenario-lab run-adapter-action \
  --root "$ROOT" \
  --run-id us-iran-deeper \
  --revision-id r1 \
  --action simulate \
  --iterations 10000

packages/core/.venv/bin/scenario-lab generate-report \
  --root "$ROOT" \
  --run-id us-iran-deeper \
  --revision-id r1
```

Exact observed report output:

```text
reported r1 /tmp/scenario-lab-us-iran-deeper-main/run/runs/us-iran-deeper/reports/r1.report.md
```

Exact observed search summary:

```json
{
  "search_mode": "mcts",
  "iterations": 10000,
  "node_count": 133,
  "transposition_hits": 111
}
```

## 5. Ranked scenarios from the verified run

Exact observed top-three branches:

1. `Coordinated consultation with allies` with score `0.2894457915831681`
   Engine label: `Alliance consultation (coordinated signaling)`
   What this means: the next phase is led by allied consultation and coordinated public signaling.
2. `A controlled show of resolve` with score `0.2887236102403397`
   Engine label: `Signal resolve (managed signal)`
   What this means: the next phase centers on a managed signal of firmness rather than a runaway escalation.
3. `Open negotiations` with score `0.28652269436203087`
   Engine label: `Open negotiation`
   What this means: the next phase is driven by open negotiation.

All three carried the same replay-backed calibration surface in this run:

- confidence bucket: `low`
- calibrated confidence: `0.875`
- replay cases: `6`
- fallback used: `false`

Exact observed scenario-family ranking:

1. `Allied consultation followed by a stalled settlement track`
   Engine label: `Alliance consultation -> settlement-stalemate`
   Plain-English reading: this family starts with coordinated allied consultation and then moves into a settlement effort that stalls.
2. `A controlled signal followed by a stalled settlement track`
   Engine label: `Signal resolve -> settlement-stalemate`
   Plain-English reading: this family starts with a managed signal of resolve and then moves into a settlement effort that stalls.
3. `Open negotiations followed by a stalled settlement track`
   Engine label: `Open negotiation -> settlement-stalemate`
   Plain-English reading: this family starts with open negotiation and then moves into a settlement effort that stalls.

That means the engine slightly favored coordinated consultation with allies over a controlled show of resolve or open negotiations, but the top of the ranking stayed tight rather than decisive.

## 6. What the engine inferred about third parties

Exact observed third-party actor preferences from the simulation payload:

- `China`: `domestic_sensitivity=0.62`, `negotiation_openness=0.75`
- `Israel`: `domestic_sensitivity=0.73`, `reputational_sensitivity=0.55`
- `Gulf States`: `alliance_dependence=0.86`
- `United Kingdom`: `alliance_dependence=0.97`
- `France`: `alliance_dependence=0.97`

The generated report summarized the same pressures like this:

```text
## Actor Utility Summary
- China: domestic_sensitivity=0.62, negotiation_openness=0.75
- Israel: domestic_sensitivity=0.73, reputational_sensitivity=0.55
- Gulf States: alliance_dependence=0.86
- United Kingdom: alliance_dependence=0.97
- France: alliance_dependence=0.97
```

## 7. Files produced by the run

- report:
  - `/tmp/scenario-lab-us-iran-deeper-main/run/runs/us-iran-deeper/reports/r1.report.md`
- summarize-revision JSON:
  - `/tmp/scenario-lab-us-iran-deeper-main/summary.json`
- simulation payload:
  - `/tmp/scenario-lab-us-iran-deeper-main/simulate.json`

This is the verified deeper `U.S.-Iran` example referenced from the public README.
