# Scenario Lab Demo: U.S.-Iran

Verified on April 23, 2026 in the isolated worktree at `/Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.worktrees/scenario-lab-public-release`.

## Verified environment note

Current worktree behavior, rechecked after the original run:

```bash
packages/core/.venv/bin/python -m forecasting_harness.cli --help
```

This command succeeds in this worktree. The transcript below documents the original verified run exactly as executed from `/tmp/scenario-lab-us-iran/transcript.txt`, which used the repo-root Python interpreter in each recorded command.

## Verified workflow

Setup used for the run:

```bash
WORKDIR=/tmp/scenario-lab-us-iran
ROOT="$WORKDIR/run"
CORPUS="$WORKDIR/corpus.db"
mkdir -p "$WORKDIR"
```

### 1. Start the run

```bash
PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.venv/bin/python -m forecasting_harness.cli run-adapter-action \
  --root '/tmp/scenario-lab-us-iran/run' \
  --run-id us-iran-public \
  --revision-id r1 \
  --action start-run \
  --domain-pack interstate-crisis
```

Exact observed output from `/tmp/scenario-lab-us-iran/transcript.txt`:

```json
{"run_id":"us-iran-public","revision_id":"r1","executed_action":"start-run","action_result":{"run_id":"us-iran-public","domain_pack":"interstate-crisis","created_at":"2026-04-23T16:30:41.226410Z","current_revision_id":null},"turn":{"run_id":"us-iran-public","revision_id":"r1","stage":"intake","headline":"Draft intake","recommended_command":"forecast-harness save-intake-draft","recommended_runtime_action":"save-intake-draft"}}
```

### 2. Save intake

```bash
PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.venv/bin/python -m forecasting_harness.cli run-adapter-action \
  --root '/tmp/scenario-lab-us-iran/run' \
  --corpus-db '/tmp/scenario-lab-us-iran/corpus.db' \
  --run-id us-iran-public \
  --revision-id r1 \
  --action save-intake-draft \
  --event-framing 'Assess 30-day crisis paths in a U.S.-Iran escalation scenario.' \
  --focus-entity 'United States' \
  --focus-entity 'Iran' \
  --current-development 'Shipping and retaliation threats intensify around the Gulf as allies urge restraint.' \
  --current-stage 'trigger' \
  --time-horizon '30d'
```

Exact observed output from `/tmp/scenario-lab-us-iran/transcript.txt`:

```json
{"run_id":"us-iran-public","revision_id":"r1","executed_action":"save-intake-draft","action_result":{"saved":true,"section":"intake","revision_id":"r1"},"turn":{"run_id":"us-iran-public","revision_id":"r1","stage":"evidence","headline":"Draft evidence packet","recommended_command":"forecast-harness draft-evidence-packet","recommended_runtime_action":"draft-evidence-packet","actions":[{"command":"forecast-harness draft-evidence-packet","runtime_action":"draft-evidence-packet","required_options":["corpus_db"]},{"command":"forecast-harness save-evidence-draft","runtime_action":"save-evidence-draft","required_options":[]}],"context":{"current_stage":"trigger","follow_up_questions":["Which outside actor has the most leverage over the next phase?","What constraint most limits immediate escalation?"],"ingestion_plan":{"corpus_source_count":0}}}}
```

This verified run did not surface `batch-ingest-recommended`. With no candidate path and no existing corpus sources, the accepted next runtime action was directly `draft-evidence-packet`.

### 3. Draft evidence through the packaged runtime

```bash
PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.venv/bin/python -m forecasting_harness.cli run-adapter-action \
  --root '/tmp/scenario-lab-us-iran/run' \
  --corpus-db '/tmp/scenario-lab-us-iran/corpus.db' \
  --run-id us-iran-public \
  --revision-id r1 \
  --action draft-evidence-packet
```

Exact observed output from `/tmp/scenario-lab-us-iran/transcript.txt`:

```json
{"run_id":"us-iran-public","revision_id":"r1","executed_action":"draft-evidence-packet","action_result":{"revision_id":"r1","items":[]},"turn":{"run_id":"us-iran-public","revision_id":"r1","stage":"approval","recommended_command":"forecast-harness approve-revision","recommended_runtime_action":"approve-revision","context":{"assumption_summary":["evidence gap: no cited evidence approved yet"],"evidence_summary":[],"warnings":["no evidence drafted yet","no suggested entities included yet"]}}}
```

For this run, `draft-evidence-packet` returned an empty packet. The verified fallback path is to save a hand-edited evidence packet with direct structured input instead of inventing evidence:

```bash
PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.venv/bin/python -m forecasting_harness.cli save-evidence-draft \
  --root '/tmp/scenario-lab-us-iran/run' \
  --run-id us-iran-public \
  --revision-id r1 \
  --item-json '<json-for-one-evidence-item>'
```

The same fallback is also exposed through the packaged runtime:

```bash
PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.venv/bin/python -m forecasting_harness.cli run-adapter-action \
  --root '/tmp/scenario-lab-us-iran/run' \
  --run-id us-iran-public \
  --revision-id r1 \
  --action save-evidence-draft \
  --item-json '<json-for-one-evidence-item>'
```

### 4. Approve the revision

```bash
PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.venv/bin/python -m forecasting_harness.cli run-adapter-action \
  --root '/tmp/scenario-lab-us-iran/run' \
  --run-id us-iran-public \
  --revision-id r1 \
  --action approve-revision \
  --assumption 'Both sides seek to avoid immediate full-scale war while preserving deterrent signaling.'
```

Exact observed output from `/tmp/scenario-lab-us-iran/transcript.txt`:

```json
{"run_id":"us-iran-public","revision_id":"r1","executed_action":"approve-revision","turn":{"run_id":"us-iran-public","revision_id":"r1","stage":"simulation","recommended_command":"forecast-harness simulate","recommended_runtime_action":"simulate","context":{"evidence_item_count":0,"assumption_count":1}}}
```

### 5. Simulate

```bash
PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.venv/bin/python -m forecasting_harness.cli run-adapter-action \
  --root '/tmp/scenario-lab-us-iran/run' \
  --run-id us-iran-public \
  --revision-id r1 \
  --action simulate
```

Observed output from `/tmp/scenario-lab-us-iran/transcript.txt`, shortened only because the raw JSON includes the full search tree:

```json
{"run_id":"us-iran-public","revision_id":"r1","executed_action":"simulate","action_result":{"search_mode":"mcts","iterations":10000,"node_count":129,"state_table_size":87,"transposition_hits":46,"max_depth_reached":4},"turn":{"run_id":"us-iran-public","revision_id":"r1","stage":"report","recommended_command":"forecast-harness begin-revision-update","recommended_runtime_action":"begin-revision-update","context":{"top_branches":[{"branch_id":"open-negotiation","label":"Open negotiation","score":0.1388245462126309,"confidence_signal":0.72,"confidence_bucket":"fallback","calibrated_confidence":0.875,"calibration_case_count":0,"calibration_fallback_used":true},{"branch_id":"signal","label":"Signal resolve (managed signal)","score":0.12670715124816462,"confidence_signal":0.136,"confidence_bucket":"low","calibrated_confidence":0.875,"calibration_case_count":6,"calibration_fallback_used":false},{"branch_id":"signal-2","label":"Signal resolve (backchannel opening)","score":0.11504934959349547,"confidence_signal":0.049,"confidence_bucket":"low","calibrated_confidence":0.875,"calibration_case_count":6,"calibration_fallback_used":false}]}}}
```

The exact transcript line continues with the full `reuse_summary`, `tree_nodes`, `branches`, `confidence_calibration`, `aggregation_lens`, and `revision_summary` payloads before ending at the `turn` object shown above.

Verified defaults from this run:

- Search mode: `mcts`
- Iterations: `10000`
- Top branch: `Open negotiation`

### 6. Generate the report

```bash
PYTHONPATH=packages/core/src /Volumes/Yiwen'sDisk/codex/HeuristicSearchEngine/.venv/bin/python -m forecasting_harness.cli generate-report \
  --root '/tmp/scenario-lab-us-iran/run' \
  --run-id us-iran-public \
  --revision-id r1
```

Observed output:

```text
reported r1 /tmp/scenario-lab-us-iran/run/runs/us-iran-public/reports/r1.report.md
```

The verified report path pattern for this run is:

```text
/tmp/scenario-lab-us-iran/run/runs/<run-id>/reports/<revision-id>.report.md
```

## Verified report excerpt

From `/tmp/scenario-lab-us-iran/run/runs/us-iran-public/reports/r1.report.md`:

```md
# Scenario Report

- Revision: r1
- Approved evidence items: 0
- Unsupported assumptions: 1

## Top Branches
- Open negotiation (0.139); calibrated confidence: fallback baseline (0.875, 0 replay cases); breakdown: actors=0, destabilization_penalty=0, system=0.139
- Signal resolve (managed signal) (0.127); calibrated confidence: low (0.875 from 6 replay cases); breakdown: actors=0, destabilization_penalty=0, system=0.127
- Signal resolve (backchannel opening) (0.115); calibrated confidence: low (0.875 from 6 replay cases); breakdown: actors=0, destabilization_penalty=0, system=0.115

## Top Branch Detail
- Terminal phase: settlement-stalemate
- Confidence signal: 0.72
- Calibrated confidence: fallback baseline (0.875, 0 replay cases)
- Key drivers: diplomatic_channel, leader_style, mediation_window
- Path: Open negotiation -> Confidence measures

## Search Summary
- Search mode: mcts
- Node count: 129
- Transposition hits: 46

## Credibility Note
- No approved evidence items. Treat this as a low-credibility exploratory run.
```

## Verified artifacts

Artifacts written under `/tmp/scenario-lab-us-iran/run/runs/us-iran-public/`:

```text
assumptions/r1.approved.json
belief-state/r1.approved.json
evidence/r1.approved.json
evidence/r1.draft.json
intake/r1.approved.json
intake/r1.draft.json
reports/r1.report.md
revisions/r1.json
simulation/r1.approved.json
```
