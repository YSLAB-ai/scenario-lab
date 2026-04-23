# Scenario Lab Natural-Language Workflow

## 5-minute conversational path

These prompts map to the verified `U.S.-Iran` public demo in [docs/demo-us-iran.md](docs/demo-us-iran.md), but the point is to keep the user messages short and let the assistant do the structuring work.

1. `How would a U.S.-Iran conflict at the Strait of Hormuz develop for the next 30 days?`
   What to expect: the assistant frames it as an `interstate-crisis`, proposes the stage and horizon, and asks follow-up questions instead of forcing you to write structured fields.
2. `Consider China. Go ahead.`
   What to expect: the intake is saved with `United States` and `Iran` as focus actors, the run moves to `evidence`, and the evidence plan targets `force posture`, `diplomatic signaling`, `alliance commitments`, `leader behavior`, and `economic constraints`.
3. `Draft the evidence. If it stays exploratory, continue anyway.`
   What to expect: Scenario Lab drafts evidence if it finds it. In the verified public demo, this returned an empty packet and moved the run to `approval` with a no-evidence warning instead of inventing sources.
4. `Approve.`
   What to expect: the assistant freezes the revision for simulation. In the verified public demo, the approved revision carried one explicit assumption and `0` approved evidence items.
5. `Go ahead.`
   What to expect: the run simulates, reaches `report`, and writes a real report file. In the verified U.S.-Iran demo, the top branch was `Open negotiation`.

## Example prompts

- `How would a U.S.-Iran conflict at the Strait of Hormuz develop for the next 30 days?`
- `Consider China. Go ahead.`
- `Draft the evidence. If it stays exploratory, continue anyway.`
- `Approve.`
- `Go ahead.`

## Runtime actions

Scenario Lab exposes a packaged adapter runtime through `forecast-harness run-adapter-action`.

The packaged adapter smokes in this repo reached the stage sequence `intake -> evidence -> approval -> simulation -> report`.
