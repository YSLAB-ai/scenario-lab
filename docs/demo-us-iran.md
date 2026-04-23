# Scenario Lab Demo: U.S.-Iran

Verified on April 23, 2026 in an isolated worktree of this repository.

## Verified environment note

Current worktree behavior, rechecked after the original run:

```bash
packages/core/.venv/bin/python -m forecasting_harness.cli --help
```

This command succeeds in this worktree. The output blocks below are the exact observed results from the verified `/tmp/scenario-lab-us-iran` run. The command blocks use the repo-relative `packages/core/.venv/bin/python` form, and I rechecked that same `/tmp/scenario-lab-us-iran` workflow in this worktree with the same key facts: `evidence_items = 0`, `iterations = 10000`, `node_count = 129`, top branch `Open negotiation`, and a generated report under `/tmp/scenario-lab-us-iran/run/runs/us-iran-public/reports/r1.report.md`.

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
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli run-adapter-action \
  --root '/tmp/scenario-lab-us-iran/run' \
  --run-id us-iran-public \
  --revision-id r1 \
  --action start-run \
  --domain-pack interstate-crisis
```

Exact observed output from `/tmp/scenario-lab-us-iran/transcript.txt`:

```json
{
  "run_id": "us-iran-public",
  "revision_id": "r1",
  "executed_action": "start-run",
  "action_result": {
    "run_id": "us-iran-public",
    "domain_pack": "interstate-crisis",
    "created_at": "2026-04-23T16:30:41.226410Z",
    "current_revision_id": null
  },
  "turn": {
    "run_id": "us-iran-public",
    "revision_id": "r1",
    "stage": "intake",
    "headline": "Draft intake",
    "user_message": "Revision is ready for intake. Capture the event framing and core entities first.",
    "recommended_command": "scenario-lab save-intake-draft",
    "recommended_runtime_action": "save-intake-draft",
    "available_sections": [],
    "actions": [
      {
        "command": "scenario-lab save-intake-draft",
        "runtime_action": "save-intake-draft",
        "label": "Save intake draft",
        "description": "Capture the normalized intake fields for the revision.",
        "required_options": []
      }
    ],
    "context": {}
  }
}
```

### 2. Save intake

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli run-adapter-action \
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
{
  "run_id": "us-iran-public",
  "revision_id": "r1",
  "executed_action": "save-intake-draft",
  "action_result": {
    "saved": true,
    "section": "intake",
    "revision_id": "r1"
  },
  "turn": {
    "run_id": "us-iran-public",
    "revision_id": "r1",
    "stage": "evidence",
    "headline": "Draft evidence packet",
    "user_message": "Intake draft saved. Review suggested entities and follow-up questions, then draft evidence.",
    "recommended_command": "scenario-lab draft-evidence-packet",
    "recommended_runtime_action": "draft-evidence-packet",
    "available_sections": [
      "intake"
    ],
    "actions": [
      {
        "command": "scenario-lab draft-evidence-packet",
        "runtime_action": "draft-evidence-packet",
        "label": "Draft evidence packet",
        "description": "Draft a grouped evidence packet from the current corpus and manifest-driven retrieval plan.",
        "required_options": [
          "corpus_db"
        ]
      },
      {
        "command": "scenario-lab save-evidence-draft",
        "runtime_action": "save-evidence-draft",
        "label": "Save evidence draft",
        "description": "Persist a hand-edited evidence packet directly without going through a file-backed JSON handoff.",
        "required_options": []
      }
    ],
    "context": {
      "domain_pack": "interstate-crisis",
      "current_stage": "trigger",
      "canonical_stages": [
        "trigger",
        "signaling",
        "limited-response",
        "escalation",
        "negotiation-deescalation",
        "settlement-stalemate"
      ],
      "suggested_entities": [],
      "follow_up_questions": [
        "Which outside actor has the most leverage over the next phase?",
        "What constraint most limits immediate escalation?"
      ],
      "pack_field_schema": {
        "alliance_pressure": "float",
        "geographic_flashpoint": "float",
        "mediation_window": "float",
        "military_posture": "str",
        "leader_style": "str",
        "tension_index": "float",
        "diplomatic_channel": "float"
      },
      "default_objective_profile": {
        "name": "balanced-system",
        "metric_weights": {
          "escalation": -0.4,
          "negotiation": 0.3,
          "economic_stress": -0.3
        },
        "veto_thresholds": {},
        "risk_tolerance": 0.5,
        "asymmetry_penalties": {},
        "actor_metric_weights": {
          "domestic_sensitivity": 0.25,
          "economic_pain_tolerance": -0.2,
          "negotiation_openness": 0.2,
          "reputational_sensitivity": 0.15,
          "alliance_dependence": 0.1,
          "coercive_bias": -0.1
        },
        "actor_weights": {},
        "aggregation_mode": "balanced-system",
        "focal_actor_id": null,
        "focal_weight": 1.0,
        "destabilization_penalty": 0.1
      },
      "intake_guidance": {
        "domain_pack": "interstate-crisis",
        "current_stage": "trigger",
        "canonical_stages": [
          "trigger",
          "signaling",
          "limited-response",
          "escalation",
          "negotiation-deescalation",
          "settlement-stalemate"
        ],
        "suggested_entities": [],
        "follow_up_questions": [
          "Which outside actor has the most leverage over the next phase?",
          "What constraint most limits immediate escalation?"
        ],
        "pack_field_schema": {
          "alliance_pressure": "float",
          "geographic_flashpoint": "float",
          "mediation_window": "float",
          "military_posture": "str",
          "leader_style": "str",
          "tension_index": "float",
          "diplomatic_channel": "float"
        },
        "default_objective_profile": {
          "name": "balanced-system",
          "metric_weights": {
            "escalation": -0.4,
            "negotiation": 0.3,
            "economic_stress": -0.3
          },
          "veto_thresholds": {},
          "risk_tolerance": 0.5,
          "asymmetry_penalties": {},
          "actor_metric_weights": {
            "domestic_sensitivity": 0.25,
            "economic_pain_tolerance": -0.2,
            "negotiation_openness": 0.2,
            "reputational_sensitivity": 0.15,
            "alliance_dependence": 0.1,
            "coercive_bias": -0.1
          },
          "actor_weights": {},
          "aggregation_mode": "balanced-system",
          "focal_actor_id": null,
          "focal_weight": 1.0,
          "destabilization_penalty": 0.1
        }
      },
      "retrieval_plan": {
        "revision_id": "r1",
        "domain_pack": "interstate-crisis",
        "base_query": "United States Iran Shipping and retaliation threats intensify around the Gulf as allies urge restraint. trigger",
        "query_variants": [
          "United States Iran Shipping and retaliation threats intensify around the Gulf as allies urge restraint. trigger",
          "United States Iran Shipping and retaliation threats intensify around the Gulf as allies urge restraint. force posture",
          "United States Iran Shipping and retaliation threats intensify around the Gulf as allies urge restraint. diplomatic signaling",
          "United States Iran Shipping and retaliation threats intensify around the Gulf as allies urge restraint. alliance commitments",
          "United States Iran Shipping and retaliation threats intensify around the Gulf as allies urge restraint. leader behavior",
          "United States Iran Shipping and retaliation threats intensify around the Gulf as allies urge restraint. economic constraints"
        ],
        "filters": {
          "domain": "interstate-crisis"
        },
        "target_evidence_categories": [
          "force posture",
          "diplomatic signaling",
          "alliance commitments",
          "leader behavior",
          "economic constraints"
        ]
      },
      "ingestion_plan": {
        "revision_id": "r1",
        "domain_pack": "interstate-crisis",
        "corpus_source_count": 0,
        "current_sources": [],
        "covered_evidence_categories": [],
        "missing_evidence_categories": [
          "force posture",
          "diplomatic signaling",
          "alliance commitments",
          "leader behavior",
          "economic constraints"
        ],
        "recommended_source_types": [
          "government statements",
          "defense white papers",
          "treaties and alliance texts",
          "sanctions notices",
          "historical crisis timelines"
        ],
        "starter_sources": [
          {
            "kind": "official communications",
            "description": "foreign ministry, defense ministry, head-of-state, and alliance statements"
          },
          {
            "kind": "force and capability references",
            "description": "order-of-battle summaries, deployment statements, range and readiness references"
          },
          {
            "kind": "historical analogs",
            "description": "documented prior crises involving the same actors or theater"
          }
        ],
        "ingestion_priorities": [
          "fresh official statements and force-posture signals",
          "binding alliance and legal commitments",
          "historical analogs for leader and institutional response style"
        ],
        "ingest_tasks": [
          {
            "evidence_category": "force posture",
            "priority_rank": 1,
            "source_role": "force and capability references",
            "starter_source": {
              "kind": "force and capability references",
              "description": "order-of-battle summaries, deployment statements, range and readiness references"
            },
            "recommended_source_types": [
              "government statements",
              "defense white papers",
              "treaties and alliance texts",
              "sanctions notices",
              "historical crisis timelines"
            ]
          },
          {
            "evidence_category": "diplomatic signaling",
            "priority_rank": 2,
            "source_role": "official communications",
            "starter_source": {
              "kind": "official communications",
              "description": "foreign ministry, defense ministry, head-of-state, and alliance statements"
            },
            "recommended_source_types": [
              "government statements",
              "defense white papers",
              "treaties and alliance texts",
              "sanctions notices",
              "historical crisis timelines"
            ]
          },
          {
            "evidence_category": "alliance commitments",
            "priority_rank": 3,
            "source_role": "official communications",
            "starter_source": {
              "kind": "official communications",
              "description": "foreign ministry, defense ministry, head-of-state, and alliance statements"
            },
            "recommended_source_types": [
              "government statements",
              "defense white papers",
              "treaties and alliance texts",
              "sanctions notices",
              "historical crisis timelines"
            ]
          },
          {
            "evidence_category": "leader behavior",
            "priority_rank": 4,
            "source_role": "historical analogs",
            "starter_source": {
              "kind": "historical analogs",
              "description": "documented prior crises involving the same actors or theater"
            },
            "recommended_source_types": [
              "government statements",
              "defense white papers",
              "treaties and alliance texts",
              "sanctions notices",
              "historical crisis timelines"
            ]
          },
          {
            "evidence_category": "economic constraints",
            "priority_rank": 5,
            "source_role": "official communications",
            "starter_source": {
              "kind": "official communications",
              "description": "foreign ministry, defense ministry, head-of-state, and alliance statements"
            },
            "recommended_source_types": [
              "government statements",
              "defense white papers",
              "treaties and alliance texts",
              "sanctions notices",
              "historical crisis timelines"
            ]
          }
        ]
      }
    }
  }
}
```

This verified run did not surface `batch-ingest-recommended`. With no candidate path and no existing corpus sources, the accepted next runtime action was directly `draft-evidence-packet`.

### 3. Draft evidence through the packaged runtime

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli run-adapter-action \
  --root '/tmp/scenario-lab-us-iran/run' \
  --corpus-db '/tmp/scenario-lab-us-iran/corpus.db' \
  --run-id us-iran-public \
  --revision-id r1 \
  --action draft-evidence-packet
```

Exact observed output from `/tmp/scenario-lab-us-iran/transcript.txt`:

```json
{
  "run_id": "us-iran-public",
  "revision_id": "r1",
  "executed_action": "draft-evidence-packet",
  "action_result": {
    "revision_id": "r1",
    "items": []
  },
  "turn": {
    "run_id": "us-iran-public",
    "revision_id": "r1",
    "stage": "approval",
    "headline": "Review approval packet",
    "user_message": "Evidence draft is ready. Review warnings, assumptions, and evidence summary before approval.",
    "recommended_command": "scenario-lab approve-revision",
    "recommended_runtime_action": "approve-revision",
    "available_sections": [
      "intake",
      "evidence"
    ],
    "actions": [
      {
        "command": "scenario-lab approve-revision",
        "runtime_action": "approve-revision",
        "label": "Approve revision",
        "description": "Freeze the intake, evidence, and assumptions for simulation.",
        "required_options": []
      }
    ],
    "context": {
      "revision_id": "r1",
      "intake_summary": {
        "event_framing": "Assess 30-day crisis paths in a U.S.-Iran escalation scenario.",
        "focus_entities": [
          "United States",
          "Iran"
        ],
        "current_development": "Shipping and retaliation threats intensify around the Gulf as allies urge restraint.",
        "current_stage": "trigger",
        "time_horizon": "30d",
        "known_constraints": [],
        "known_unknowns": []
      },
      "assumption_summary": [
        "evidence gap: no cited evidence approved yet"
      ],
      "objective_profile": {
        "name": "balanced-system",
        "metric_weights": {
          "escalation": -0.4,
          "negotiation": 0.3,
          "economic_stress": -0.3
        },
        "veto_thresholds": {},
        "risk_tolerance": 0.5,
        "asymmetry_penalties": {},
        "actor_metric_weights": {
          "domestic_sensitivity": 0.25,
          "economic_pain_tolerance": -0.2,
          "negotiation_openness": 0.2,
          "reputational_sensitivity": 0.15,
          "alliance_dependence": 0.1,
          "coercive_bias": -0.1
        },
        "actor_weights": {},
        "aggregation_mode": "balanced-system",
        "focal_actor_id": null,
        "focal_weight": 1.0,
        "destabilization_penalty": 0.1
      },
      "actor_preferences": [],
      "recommended_run_lens": {
        "name": "balanced-system",
        "metric_weights": {
          "escalation": -0.4,
          "negotiation": 0.3,
          "economic_stress": -0.3
        },
        "veto_thresholds": {},
        "risk_tolerance": 0.5,
        "asymmetry_penalties": {},
        "actor_metric_weights": {
          "domestic_sensitivity": 0.25,
          "economic_pain_tolerance": -0.2,
          "negotiation_openness": 0.2,
          "reputational_sensitivity": 0.15,
          "alliance_dependence": 0.1,
          "coercive_bias": -0.1
        },
        "actor_weights": {},
        "aggregation_mode": "balanced-system",
        "focal_actor_id": null,
        "focal_weight": 1.0,
        "destabilization_penalty": 0.1
      },
      "evidence_summary": [],
      "warnings": [
        "no evidence drafted yet",
        "no suggested entities included yet"
      ],
      "approval_packet": {
        "revision_id": "r1",
        "intake_summary": {
          "event_framing": "Assess 30-day crisis paths in a U.S.-Iran escalation scenario.",
          "focus_entities": [
            "United States",
            "Iran"
          ],
          "current_development": "Shipping and retaliation threats intensify around the Gulf as allies urge restraint.",
          "current_stage": "trigger",
          "time_horizon": "30d",
          "known_constraints": [],
          "known_unknowns": []
        },
        "assumption_summary": [
          "evidence gap: no cited evidence approved yet"
        ],
        "objective_profile": {
          "name": "balanced-system",
          "metric_weights": {
            "escalation": -0.4,
            "negotiation": 0.3,
            "economic_stress": -0.3
          },
          "veto_thresholds": {},
          "risk_tolerance": 0.5,
          "asymmetry_penalties": {},
          "actor_metric_weights": {
            "domestic_sensitivity": 0.25,
            "economic_pain_tolerance": -0.2,
            "negotiation_openness": 0.2,
            "reputational_sensitivity": 0.15,
            "alliance_dependence": 0.1,
            "coercive_bias": -0.1
          },
          "actor_weights": {},
          "aggregation_mode": "balanced-system",
          "focal_actor_id": null,
          "focal_weight": 1.0,
          "destabilization_penalty": 0.1
        },
        "actor_preferences": [],
        "recommended_run_lens": {
          "name": "balanced-system",
          "metric_weights": {
            "escalation": -0.4,
            "negotiation": 0.3,
            "economic_stress": -0.3
          },
          "veto_thresholds": {},
          "risk_tolerance": 0.5,
          "asymmetry_penalties": {},
          "actor_metric_weights": {
            "domestic_sensitivity": 0.25,
            "economic_pain_tolerance": -0.2,
            "negotiation_openness": 0.2,
            "reputational_sensitivity": 0.15,
            "alliance_dependence": 0.1,
            "coercive_bias": -0.1
          },
          "actor_weights": {},
          "aggregation_mode": "balanced-system",
          "focal_actor_id": null,
          "focal_weight": 1.0,
          "destabilization_penalty": 0.1
        },
        "evidence_summary": [],
        "warnings": [
          "no evidence drafted yet",
          "no suggested entities included yet"
        ]
      }
    }
  }
}
```

For this run, `draft-evidence-packet` returned an empty packet. The repo also exposes a direct `save-evidence-draft` fallback for hand-edited structured evidence, but this specific public demo keeps the verified no-evidence path instead of inventing evidence.

### 4. Approve the revision

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli run-adapter-action \
  --root '/tmp/scenario-lab-us-iran/run' \
  --run-id us-iran-public \
  --revision-id r1 \
  --action approve-revision \
  --assumption 'Both sides seek to avoid immediate full-scale war while preserving deterrent signaling.'
```

Exact observed output from `/tmp/scenario-lab-us-iran/transcript.txt`:

```json
{
  "run_id": "us-iran-public",
  "revision_id": "r1",
  "executed_action": "approve-revision",
  "action_result": {
    "run_id": "us-iran-public",
    "domain_pack": "interstate-crisis",
    "created_at": "2026-04-23T16:30:41.226410Z",
    "current_revision_id": "r1"
  },
  "turn": {
    "run_id": "us-iran-public",
    "revision_id": "r1",
    "stage": "simulation",
    "headline": "Ready to simulate",
    "user_message": "Revision is approved and ready to simulate.",
    "recommended_command": "scenario-lab simulate",
    "recommended_runtime_action": "simulate",
    "available_sections": [
      "intake",
      "evidence",
      "assumptions"
    ],
    "actions": [
      {
        "command": "scenario-lab simulate",
        "runtime_action": "simulate",
        "label": "Run simulation",
        "description": "Execute deterministic search for the approved revision.",
        "required_options": []
      }
    ],
    "context": {
      "revision_id": "r1",
      "evidence_item_count": 0,
      "assumption_count": 1,
      "simulation_readiness": {
        "revision_id": "r1",
        "evidence_item_count": 0,
        "assumption_count": 1
      }
    }
  }
}
```

### 5. Simulate

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli run-adapter-action \
  --root '/tmp/scenario-lab-us-iran/run' \
  --run-id us-iran-public \
  --revision-id r1 \
  --action simulate
```

Exact observed output from `/tmp/scenario-lab-us-iran/transcript.txt`:

```json
{
  "run_id": "us-iran-public",
  "revision_id": "r1",
  "executed_action": "simulate",
  "action_result": {
    "search_mode": "mcts",
    "iterations": 10000,
    "node_count": 129,
    "state_table_size": 87,
    "transposition_hits": 46,
    "max_depth_reached": 4,
    "reuse_summary": {
      "enabled": false,
      "source_revision_id": null,
      "reused_nodes": 0,
      "skipped_nodes": 0,
      "compatibility": {}
    },
    "tree_nodes": [
      {
        "node_id": "rollout-1/confidence-measures",
        "state_hash": "241d0ff8840299af",
        "depth": 2,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5859000000000001,
        "dependencies": {},
        "dependency_hash": null,
        "visits": 488,
        "value_sum": 13.078399999999911,
        "metric_sums": {
          "escalation": 145.9120000000017,
          "negotiation": 403.28319999999763,
          "economic_stress": 165.13919999999945
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 13.078399999999911,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.026799999999999817,
        "metrics": {
          "escalation": 0.2990000000000035,
          "negotiation": 0.8263999999999951,
          "economic_stress": 0.33839999999999887
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.026799999999999817,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "rollout-1/stalemate-return",
        "state_hash": "8c76aca2b882449f",
        "depth": 2,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.07919999999999999,
        "dependencies": {},
        "dependency_hash": null,
        "visits": 7182,
        "value_sum": 1024.5554099998749,
        "metric_sums": {
          "escalation": 1003.5899999999998,
          "negotiation": 7022.074000000552,
          "economic_stress": 2268.7693000002546
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 1024.5554099998749,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.14265600250624824,
        "metrics": {
          "escalation": 0.13973684210526313,
          "negotiation": 0.9777323865219371,
          "economic_stress": 0.31589658869399256
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.14265600250624824,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "rollout-2/allied-pressure",
        "state_hash": "a2eac07db07e149a",
        "depth": 3,
        "branch_id": "allied-pressure",
        "label": "Allied pressure",
        "prior": 0.19720000000000001,
        "dependencies": {},
        "dependency_hash": null,
        "visits": 119,
        "value_sum": -0.18480000000000102,
        "metric_sums": {
          "escalation": 39.86099999999998,
          "negotiation": 94.25359999999984,
          "economic_stress": 41.7216
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.18480000000000102,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.0015529411764705968,
        "metrics": {
          "escalation": 0.3349663865546217,
          "negotiation": 0.792047058823528,
          "economic_stress": 0.35060168067226893
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.0015529411764705968,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "rollout-2/crisis-talks",
        "state_hash": "ba7950a999876aa4",
        "depth": 3,
        "branch_id": "crisis-talks",
        "label": "Crisis talks",
        "prior": 0.3806,
        "dependencies": {},
        "dependency_hash": null,
        "visits": 477,
        "value_sum": 38.84480000000015,
        "metric_sums": {
          "escalation": 103.13500000000008,
          "negotiation": 430.50280000000174,
          "economic_stress": 163.50680000000105
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 38.84480000000015,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.08143563941299821,
        "metrics": {
          "escalation": 0.21621593291404628,
          "negotiation": 0.9025215932914082,
          "economic_stress": 0.3427815513626856
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.08143563941299821,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "rollout-2/intercept",
        "state_hash": "c43eee67cc1625c4",
        "depth": 3,
        "branch_id": "intercept",
        "label": "Intercept",
        "prior": 0.14359999999999998,
        "dependencies": {},
        "dependency_hash": null,
        "visits": 45,
        "value_sum": -6.706610000000009,
        "metric_sums": {
          "escalation": 25.180999999999994,
          "negotiation": 32.1848,
          "economic_stress": 20.96550000000002
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -6.706610000000009,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.149035777777778,
        "metrics": {
          "escalation": 0.5595777777777776,
          "negotiation": 0.7152177777777778,
          "economic_stress": 0.4659000000000004
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.149035777777778,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "rollout-2/signal-resolve",
        "state_hash": "45b464eeb9d1da33",
        "depth": 3,
        "branch_id": "signal-resolve",
        "label": "Signal resolve",
        "prior": 0.38880000000000003,
        "dependencies": {},
        "dependency_hash": null,
        "visits": 6898,
        "value_sum": 1062.705879999896,
        "metric_sums": {
          "escalation": 862.25,
          "negotiation": 6840.0568000005005,
          "economic_stress": 2148.037200000247
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 1062.705879999896,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.15405999999998493,
        "metrics": {
          "escalation": 0.125,
          "negotiation": 0.9916000000000725,
          "economic_stress": 0.3114000000000358
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.15405999999998493,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "rollout-3/allied-pressure",
        "state_hash": "888ee3d9508a56d6",
        "depth": 4,
        "branch_id": "allied-pressure",
        "label": "Allied pressure",
        "prior": 0.19720000000000001,
        "dependencies": {},
        "dependency_hash": null,
        "visits": 15,
        "value_sum": -2.1762799999999998,
        "metric_sums": {
          "escalation": 8.309,
          "negotiation": 10.252399999999996,
          "economic_stress": 6.428000000000001
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -2.1762799999999998,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.14508533333333332,
        "metrics": {
          "escalation": 0.5539333333333333,
          "negotiation": 0.6834933333333331,
          "economic_stress": 0.4285333333333334
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.14508533333333332,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "rollout-3/confidence-measures",
        "state_hash": "79913979c85da0b7",
        "depth": 4,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5509999999999999,
        "dependencies": {},
        "dependency_hash": null,
        "visits": 175,
        "value_sum": 3.738000000000004,
        "metric_sums": {
          "escalation": 53.02499999999987,
          "negotiation": 142.3799999999997,
          "economic_stress": 59.22
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 3.738000000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.02136000000000002,
        "metrics": {
          "escalation": 0.30299999999999927,
          "negotiation": 0.8135999999999983,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.02136000000000002,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "rollout-3/crisis-talks",
        "state_hash": "ba7950a999876aa4",
        "depth": 4,
        "branch_id": "crisis-talks",
        "label": "Crisis talks",
        "prior": 0.3518,
        "dependencies": {},
        "dependency_hash": null,
        "visits": 477,
        "value_sum": 38.84480000000015,
        "metric_sums": {
          "escalation": 103.13500000000008,
          "negotiation": 430.50280000000174,
          "economic_stress": 163.50680000000105
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 38.84480000000015,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.08143563941299821,
        "metrics": {
          "escalation": 0.21621593291404628,
          "negotiation": 0.9025215932914082,
          "economic_stress": 0.3427815513626856
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.08143563941299821,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "rollout-3/intercept",
        "state_hash": "831a1408abb2b8dc",
        "depth": 4,
        "branch_id": "intercept",
        "label": "Intercept",
        "prior": 0.15,
        "dependencies": {},
        "dependency_hash": null,
        "visits": 4,
        "value_sum": -2.2957199999999998,
        "metric_sums": {
          "escalation": 3.6959999999999997,
          "negotiation": 1.1712,
          "economic_stress": 3.8956
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -2.2957199999999998,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.5739299999999999,
        "metrics": {
          "escalation": 0.9239999999999999,
          "negotiation": 0.2928,
          "economic_stress": 0.9739
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.5739299999999999,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "rollout-3/signal-resolve",
        "state_hash": "462d4558a9edf2fa",
        "depth": 4,
        "branch_id": "signal-resolve",
        "label": "Signal resolve",
        "prior": 0.3744,
        "dependencies": {},
        "dependency_hash": null,
        "visits": 415,
        "value_sum": 61.6773000000003,
        "metric_sums": {
          "escalation": 53.534999999999755,
          "negotiation": 406.201999999998,
          "economic_stress": 129.2310000000011
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 61.6773000000003,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.14862000000000072,
        "metrics": {
          "escalation": 0.12899999999999942,
          "negotiation": 0.9787999999999952,
          "economic_stress": 0.3114000000000027
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.14862000000000072,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "rollout-3/stalemate-return",
        "state_hash": "7b5c068c2f250473",
        "depth": 4,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.09359999999999999,
        "dependencies": {},
        "dependency_hash": null,
        "visits": 439,
        "value_sum": 55.59064000000027,
        "metric_sums": {
          "escalation": 68.75299999999979,
          "negotiation": 419.0943999999977,
          "economic_stress": 142.12160000000074
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 55.59064000000027,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.12663015945330358,
        "metrics": {
          "escalation": 0.15661275626423643,
          "negotiation": 0.9546569476081952,
          "economic_stress": 0.3237394077448764
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.12663015945330358,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root",
        "state_hash": "1ae2f626e14a2dff",
        "depth": 0,
        "branch_id": null,
        "label": null,
        "prior": 1.0,
        "dependencies": {},
        "dependency_hash": null,
        "visits": 10000,
        "value_sum": 1301.9533099999967,
        "metric_sums": {
          "escalation": 1555.2369999999771,
          "negotiation": 9589.965199999979,
          "economic_stress": 3176.471500000397
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 1301.9533099999967,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.13019533099999966,
        "metrics": {
          "escalation": 0.1555236999999977,
          "negotiation": 0.9589965199999979,
          "economic_stress": 0.31764715000003974
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.13019533099999966,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/signal",
          "root/signal-2",
          "root/limited-response",
          "root/limited-response-2",
          "root/alliance-consultation",
          "root/alliance-consultation-2",
          "root/alliance-consultation-3",
          "root/open-negotiation"
        ]
      },
      {
        "node_id": "root/alliance-consultation",
        "state_hash": "6ca2fc9a78a0fc31",
        "depth": 1,
        "branch_id": "alliance-consultation",
        "label": "Alliance consultation (coordinated restraint)",
        "prior": 0.0762614039470397,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "c99a4e139e95964d",
        "visits": 83,
        "value_sum": 2.752629999999999,
        "metric_sums": {
          "escalation": 23.833999999999985,
          "negotiation": 68.93880000000004,
          "economic_stress": 27.984699999999993
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 2.752629999999999,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.03316421686746987,
        "metrics": {
          "escalation": 0.2871566265060239,
          "negotiation": 0.8305879518072294,
          "economic_stress": 0.33716506024096377
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.03316421686746987,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation/confidence-measures",
          "root/alliance-consultation/stalemate-return"
        ]
      },
      {
        "node_id": "root/alliance-consultation-2",
        "state_hash": "8017e87c2773f20d",
        "depth": 1,
        "branch_id": "alliance-consultation-2",
        "label": "Alliance consultation (coordinated signaling)",
        "prior": 0.08457886585061204,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "f980d81c63f7c914",
        "visits": 148,
        "value_sum": 11.375149999999996,
        "metric_sums": {
          "escalation": 31.866999999999983,
          "negotiation": 128.91920000000033,
          "economic_stress": 48.51269999999994
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 11.375149999999996,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.07685912162162159,
        "metrics": {
          "escalation": 0.21531756756756745,
          "negotiation": 0.8710756756756779,
          "economic_stress": 0.3277885135135131
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.07685912162162159,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation-2/signal-resolve",
          "root/alliance-consultation-2/intercept",
          "root/alliance-consultation-2/allied-pressure",
          "root/alliance-consultation-2/crisis-talks"
        ]
      },
      {
        "node_id": "root/alliance-consultation-2/allied-pressure",
        "state_hash": "5915954cf3173463",
        "depth": 2,
        "branch_id": "allied-pressure",
        "label": "Allied pressure",
        "prior": 0.2504,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "66421ffc6a39f4a7",
        "visits": 20,
        "value_sum": 0.03492999999999978,
        "metric_sums": {
          "escalation": 6.419,
          "negotiation": 16.083599999999993,
          "economic_stress": 7.4085
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.03492999999999978,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.001746499999999989,
        "metrics": {
          "escalation": 0.32094999999999996,
          "negotiation": 0.8041799999999997,
          "economic_stress": 0.370425
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.001746499999999989,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation-2/allied-pressure/confidence-measures",
          "root/alliance-consultation-2/allied-pressure/stalemate-return"
        ]
      },
      {
        "node_id": "root/alliance-consultation-2/allied-pressure/confidence-measures",
        "state_hash": "0cd66c5f9a2aeecf",
        "depth": 3,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5012,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "233019e0d118fc7e",
        "visits": 21,
        "value_sum": 0.4485599999999997,
        "metric_sums": {
          "escalation": 6.3629999999999995,
          "negotiation": 17.085599999999992,
          "economic_stress": 7.1064
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.4485599999999997,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.021359999999999983,
        "metrics": {
          "escalation": 0.303,
          "negotiation": 0.8135999999999997,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.021359999999999983,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-2/allied-pressure/stalemate-return",
        "state_hash": "bb7f837f82de5e68",
        "depth": 3,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.1496,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "ed57f7b9384081a2",
        "visits": 5,
        "value_sum": -0.28547,
        "metric_sums": {
          "escalation": 1.874,
          "negotiation": 3.8796,
          "economic_stress": 2.3325
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.28547,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.057094,
        "metrics": {
          "escalation": 0.3748,
          "negotiation": 0.7759199999999999,
          "economic_stress": 0.4665
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.057094,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation-2/allied-pressure/stalemate-return/signal-resolve",
          "root/alliance-consultation-2/allied-pressure/stalemate-return/intercept",
          "root/alliance-consultation-2/allied-pressure/stalemate-return/allied-pressure",
          "root/alliance-consultation-2/allied-pressure/stalemate-return/crisis-talks"
        ]
      },
      {
        "node_id": "root/alliance-consultation-2/allied-pressure/stalemate-return/allied-pressure",
        "state_hash": "1b469e3b5656a8d7",
        "depth": 4,
        "branch_id": "allied-pressure",
        "label": "Allied pressure",
        "prior": 0.24480000000000002,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "75e107645fbd1ef8",
        "visits": 1,
        "value_sum": -0.13564000000000004,
        "metric_sums": {
          "escalation": 0.547,
          "negotiation": 0.7015999999999999,
          "economic_stress": 0.4244
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.13564000000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.13564000000000004,
        "metrics": {
          "escalation": 0.547,
          "negotiation": 0.7015999999999999,
          "economic_stress": 0.4244
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.13564000000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-2/allied-pressure/stalemate-return/crisis-talks",
        "state_hash": "fc3ccfaecf2aee9a",
        "depth": 4,
        "branch_id": "crisis-talks",
        "label": "Crisis talks",
        "prior": 0.323,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "d72c008f00832cee",
        "visits": 23,
        "value_sum": 0.7111999999999996,
        "metric_sums": {
          "escalation": 6.775000000000003,
          "negotiation": 19.219199999999994,
          "economic_stress": 7.8152
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.7111999999999996,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.030921739130434767,
        "metrics": {
          "escalation": 0.2945652173913045,
          "negotiation": 0.8356173913043475,
          "economic_stress": 0.33979130434782606
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.030921739130434767,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-2/allied-pressure/stalemate-return/intercept",
        "state_hash": "b1bdd189b2c5e8f0",
        "depth": 4,
        "branch_id": "intercept",
        "label": "Intercept",
        "prior": 0.15639999999999998,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "ecfd33eb43533204",
        "visits": 1,
        "value_sum": -0.5793699999999999,
        "metric_sums": {
          "escalation": 0.9279999999999999,
          "negotiation": 0.28,
          "economic_stress": 0.9739
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.5793699999999999,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.5793699999999999,
        "metrics": {
          "escalation": 0.9279999999999999,
          "negotiation": 0.28,
          "economic_stress": 0.9739
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.5793699999999999,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-2/allied-pressure/stalemate-return/signal-resolve",
        "state_hash": "d45745300e8e249f",
        "depth": 4,
        "branch_id": "signal-resolve",
        "label": "Signal resolve",
        "prior": 0.36,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "3e70b47f3ae8ba28",
        "visits": 3,
        "value_sum": 0.42954000000000003,
        "metric_sums": {
          "escalation": 0.399,
          "negotiation": 2.8979999999999997,
          "economic_stress": 0.9342
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.42954000000000003,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.14318,
        "metrics": {
          "escalation": 0.133,
          "negotiation": 0.9659999999999999,
          "economic_stress": 0.3114
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.14318,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-2/crisis-talks",
        "state_hash": "fc3ccfaecf2aee9a",
        "depth": 2,
        "branch_id": "crisis-talks",
        "label": "Crisis talks",
        "prior": 0.2276,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "d72c008f00832cee",
        "visits": 23,
        "value_sum": 0.7111999999999996,
        "metric_sums": {
          "escalation": 6.775000000000003,
          "negotiation": 19.219199999999994,
          "economic_stress": 7.8152
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.7111999999999996,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.030921739130434767,
        "metrics": {
          "escalation": 0.2945652173913045,
          "negotiation": 0.8356173913043475,
          "economic_stress": 0.33979130434782606
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.030921739130434767,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation-2/crisis-talks/confidence-measures",
          "root/alliance-consultation-2/crisis-talks/stalemate-return"
        ]
      },
      {
        "node_id": "root/alliance-consultation-2/crisis-talks/confidence-measures",
        "state_hash": "82ae35739e59a51b",
        "depth": 3,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5859000000000001,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "c4dfafe553141ea2",
        "visits": 20,
        "value_sum": 0.5359999999999998,
        "metric_sums": {
          "escalation": 5.980000000000002,
          "negotiation": 16.527999999999995,
          "economic_stress": 6.768
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.5359999999999998,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.02679999999999999,
        "metrics": {
          "escalation": 0.2990000000000001,
          "negotiation": 0.8263999999999998,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.02679999999999999,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-2/crisis-talks/stalemate-return",
        "state_hash": "a342fc160b7bea72",
        "depth": 3,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.07919999999999999,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "ceda9cde541853af",
        "visits": 3,
        "value_sum": 0.17520000000000002,
        "metric_sums": {
          "escalation": 0.795,
          "negotiation": 2.6912000000000003,
          "economic_stress": 1.0472000000000001
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.17520000000000002,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.05840000000000001,
        "metrics": {
          "escalation": 0.265,
          "negotiation": 0.8970666666666668,
          "economic_stress": 0.3490666666666667
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.05840000000000001,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation-2/crisis-talks/stalemate-return/signal-resolve",
          "root/alliance-consultation-2/crisis-talks/stalemate-return/intercept",
          "root/alliance-consultation-2/crisis-talks/stalemate-return/allied-pressure",
          "root/alliance-consultation-2/crisis-talks/stalemate-return/crisis-talks"
        ]
      },
      {
        "node_id": "root/alliance-consultation-2/crisis-talks/stalemate-return/allied-pressure",
        "state_hash": "0ff44d10d7c59e64",
        "depth": 4,
        "branch_id": "allied-pressure",
        "label": "Allied pressure",
        "prior": 0.24480000000000002,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "c238f75f4d5378dc",
        "visits": 1,
        "value_sum": -0.13292000000000004,
        "metric_sums": {
          "escalation": 0.545,
          "negotiation": 0.708,
          "economic_stress": 0.4244
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.13292000000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.13292000000000004,
        "metrics": {
          "escalation": 0.545,
          "negotiation": 0.708,
          "economic_stress": 0.4244
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.13292000000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-2/crisis-talks/stalemate-return/crisis-talks",
        "state_hash": "fc3ccfaecf2aee9a",
        "depth": 4,
        "branch_id": "crisis-talks",
        "label": "Crisis talks",
        "prior": 0.3806,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "d72c008f00832cee",
        "visits": 23,
        "value_sum": 0.7111999999999996,
        "metric_sums": {
          "escalation": 6.775000000000003,
          "negotiation": 19.219199999999994,
          "economic_stress": 7.8152
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.7111999999999996,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.030921739130434767,
        "metrics": {
          "escalation": 0.2945652173913045,
          "negotiation": 0.8356173913043475,
          "economic_stress": 0.33979130434782606
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.030921739130434767,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-2/crisis-talks/stalemate-return/intercept",
        "state_hash": "b66ffe65e76852d3",
        "depth": 4,
        "branch_id": "intercept",
        "label": "Intercept",
        "prior": 0.14359999999999998,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "3a05499593f40731",
        "visits": 0,
        "value_sum": 0.0,
        "metric_sums": {},
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {},
        "score": 0.0,
        "metrics": {},
        "actor_metrics": {},
        "aggregate_score_breakdown": {},
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-2/crisis-talks/stalemate-return/signal-resolve",
        "state_hash": "473933e74a95edd1",
        "depth": 4,
        "branch_id": "signal-resolve",
        "label": "Signal resolve",
        "prior": 0.38880000000000003,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "f65f6caefd672380",
        "visits": 2,
        "value_sum": 0.30812000000000006,
        "metric_sums": {
          "escalation": 0.25,
          "negotiation": 1.9832,
          "economic_stress": 0.6228
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.30812000000000006,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.15406000000000003,
        "metrics": {
          "escalation": 0.125,
          "negotiation": 0.9916,
          "economic_stress": 0.3114
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.15406000000000003,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-2/intercept",
        "state_hash": "d86b3a5c8cea5371",
        "depth": 2,
        "branch_id": "intercept",
        "label": "Intercept",
        "prior": 0.19480000000000003,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "e81d5d7bbe439216",
        "visits": 9,
        "value_sum": -1.1578600000000003,
        "metric_sums": {
          "escalation": 4.465,
          "negotiation": 5.4884,
          "economic_stress": 3.3945999999999996
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -1.1578600000000003,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.12865111111111116,
        "metrics": {
          "escalation": 0.4961111111111111,
          "negotiation": 0.6098222222222223,
          "economic_stress": 0.3771777777777777
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.12865111111111116,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation-2/intercept/force-projection",
          "root/alliance-consultation-2/intercept/emergency-backchannel"
        ]
      },
      {
        "node_id": "root/alliance-consultation-2/intercept/emergency-backchannel",
        "state_hash": "bd2e28cb58a30147",
        "depth": 3,
        "branch_id": "emergency-backchannel",
        "label": "Emergency backchannel",
        "prior": 0.208,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "9f915e9b6ffd2956",
        "visits": 7,
        "value_sum": -0.14372000000000001,
        "metric_sums": {
          "escalation": 2.465,
          "negotiation": 5.3244,
          "economic_stress": 2.5168
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.14372000000000001,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.020531428571428572,
        "metrics": {
          "escalation": 0.35214285714285715,
          "negotiation": 0.7606285714285714,
          "economic_stress": 0.3595428571428571
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.020531428571428572,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation-2/intercept/emergency-backchannel/confidence-measures",
          "root/alliance-consultation-2/intercept/emergency-backchannel/stalemate-return"
        ]
      },
      {
        "node_id": "root/alliance-consultation-2/intercept/emergency-backchannel/confidence-measures",
        "state_hash": "0cd66c5f9a2aeecf",
        "depth": 4,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5509999999999999,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "233019e0d118fc7e",
        "visits": 21,
        "value_sum": 0.4485599999999997,
        "metric_sums": {
          "escalation": 6.3629999999999995,
          "negotiation": 17.085599999999992,
          "economic_stress": 7.1064
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.4485599999999997,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.021359999999999983,
        "metrics": {
          "escalation": 0.303,
          "negotiation": 0.8135999999999997,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.021359999999999983,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-2/intercept/emergency-backchannel/stalemate-return",
        "state_hash": "9b78e310eff92ce7",
        "depth": 4,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.09359999999999999,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "082c5e27ae1dd828",
        "visits": 1,
        "value_sum": -0.27187999999999996,
        "metric_sums": {
          "escalation": 0.6469999999999999,
          "negotiation": 0.44279999999999997,
          "economic_stress": 0.48639999999999994
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.27187999999999996,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.27187999999999996,
        "metrics": {
          "escalation": 0.6469999999999999,
          "negotiation": 0.44279999999999997,
          "economic_stress": 0.48639999999999994
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.27187999999999996,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-2/intercept/force-projection",
        "state_hash": "e923a3817dfe8602",
        "depth": 3,
        "branch_id": "force-projection",
        "label": "Force projection",
        "prior": 0.3744,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "03398846d52d9ef0",
        "visits": 2,
        "value_sum": -1.01414,
        "metric_sums": {
          "escalation": 2.0,
          "negotiation": 0.164,
          "economic_stress": 0.8777999999999999
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -1.01414,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.50707,
        "metrics": {
          "escalation": 1.0,
          "negotiation": 0.082,
          "economic_stress": 0.43889999999999996
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.50707,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-2/signal-resolve",
        "state_hash": "518878d85ca3fabc",
        "depth": 2,
        "branch_id": "signal-resolve",
        "label": "Signal resolve",
        "prior": 0.319,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "7ad38be3a28014bc",
        "visits": 96,
        "value_sum": 11.786880000000007,
        "metric_sums": {
          "escalation": 14.20799999999998,
          "negotiation": 88.12800000000013,
          "economic_stress": 29.894399999999976
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 11.786880000000007,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.12278000000000007,
        "metrics": {
          "escalation": 0.1479999999999998,
          "negotiation": 0.9180000000000014,
          "economic_stress": 0.31139999999999973
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.12278000000000007,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-3",
        "state_hash": "1d4d4d7ad9e445b2",
        "depth": 1,
        "branch_id": "alliance-consultation-3",
        "label": "Alliance consultation (harder deterrence)",
        "prior": 0.05535973020234822,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "a04bbc094eca8708",
        "visits": 36,
        "value_sum": -1.0821900000000004,
        "metric_sums": {
          "escalation": 12.957000000000006,
          "negotiation": 26.3196,
          "economic_stress": 12.6509
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -1.0821900000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.030060833333333346,
        "metrics": {
          "escalation": 0.35991666666666683,
          "negotiation": 0.7311000000000001,
          "economic_stress": 0.3514138888888889
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.030060833333333346,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation-3/contain-response",
          "root/alliance-consultation-3/retaliate",
          "root/alliance-consultation-3/ceasefire-channel"
        ]
      },
      {
        "node_id": "root/alliance-consultation-3/ceasefire-channel",
        "state_hash": "20efca2683bbbfd5",
        "depth": 2,
        "branch_id": "ceasefire-channel",
        "label": "Ceasefire channel",
        "prior": 0.2166,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "bef99d6df2f1bf43",
        "visits": 23,
        "value_sum": 0.6544500000000001,
        "metric_sums": {
          "escalation": 6.866999999999999,
          "negotiation": 19.2132,
          "economic_stress": 7.8757
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.6544500000000001,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.02845434782608696,
        "metrics": {
          "escalation": 0.2985652173913043,
          "negotiation": 0.8353565217391304,
          "economic_stress": 0.3424217391304348
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.02845434782608696,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation-3/ceasefire-channel/confidence-measures",
          "root/alliance-consultation-3/ceasefire-channel/stalemate-return"
        ]
      },
      {
        "node_id": "root/alliance-consultation-3/ceasefire-channel/confidence-measures",
        "state_hash": "162282d6a06222a0",
        "depth": 3,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5928,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "45770cbbce0cd561",
        "visits": 19,
        "value_sum": 0.4833600000000003,
        "metric_sums": {
          "escalation": 5.699999999999998,
          "negotiation": 15.6408,
          "economic_stress": 6.4296
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.4833600000000003,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.025440000000000015,
        "metrics": {
          "escalation": 0.29999999999999993,
          "negotiation": 0.8232,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.025440000000000015,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-3/ceasefire-channel/stalemate-return",
        "state_hash": "28d2f8b84a8dc08c",
        "depth": 3,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.08279999999999998,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "33cbf3430f6362d9",
        "visits": 4,
        "value_sum": 0.17108999999999994,
        "metric_sums": {
          "escalation": 1.167,
          "negotiation": 3.5724,
          "economic_stress": 1.4461
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.17108999999999994,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.042772499999999984,
        "metrics": {
          "escalation": 0.29175,
          "negotiation": 0.8931,
          "economic_stress": 0.361525
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.042772499999999984,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation-3/ceasefire-channel/stalemate-return/signal-resolve",
          "root/alliance-consultation-3/ceasefire-channel/stalemate-return/intercept",
          "root/alliance-consultation-3/ceasefire-channel/stalemate-return/allied-pressure",
          "root/alliance-consultation-3/ceasefire-channel/stalemate-return/crisis-talks"
        ]
      },
      {
        "node_id": "root/alliance-consultation-3/ceasefire-channel/stalemate-return/allied-pressure",
        "state_hash": "827ee0a2232f7365",
        "depth": 4,
        "branch_id": "allied-pressure",
        "label": "Allied pressure",
        "prior": 0.23800000000000002,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "325a3eb186794cec",
        "visits": 1,
        "value_sum": -0.13428000000000004,
        "metric_sums": {
          "escalation": 0.546,
          "negotiation": 0.7048,
          "economic_stress": 0.4244
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.13428000000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.13428000000000004,
        "metrics": {
          "escalation": 0.546,
          "negotiation": 0.7048,
          "economic_stress": 0.4244
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.13428000000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-3/ceasefire-channel/stalemate-return/crisis-talks",
        "state_hash": "cf1fa4019543be6a",
        "depth": 4,
        "branch_id": "crisis-talks",
        "label": "Crisis talks",
        "prior": 0.3734,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "78a032fe873feb9e",
        "visits": 1,
        "value_sum": -3.0000000000016125e-05,
        "metric_sums": {
          "escalation": 0.369,
          "negotiation": 0.8908,
          "economic_stress": 0.3989
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -3.0000000000016125e-05,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -3.0000000000016125e-05,
        "metrics": {
          "escalation": 0.369,
          "negotiation": 0.8908,
          "economic_stress": 0.3989
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -3.0000000000016125e-05,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-3/ceasefire-channel/stalemate-return/intercept",
        "state_hash": "f6c431d6f3d096bd",
        "depth": 4,
        "branch_id": "intercept",
        "label": "Intercept",
        "prior": 0.1452,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "b29b5346e7817d4c",
        "visits": 0,
        "value_sum": 0.0,
        "metric_sums": {},
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {},
        "score": 0.0,
        "metrics": {},
        "actor_metrics": {},
        "aggregate_score_breakdown": {},
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-3/ceasefire-channel/stalemate-return/signal-resolve",
        "state_hash": "5c8bf8cc79f2a1fc",
        "depth": 4,
        "branch_id": "signal-resolve",
        "label": "Signal resolve",
        "prior": 0.3852,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "46933d20a888291c",
        "visits": 2,
        "value_sum": 0.3054,
        "metric_sums": {
          "escalation": 0.252,
          "negotiation": 1.9768000000000001,
          "economic_stress": 0.6228
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.3054,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.1527,
        "metrics": {
          "escalation": 0.126,
          "negotiation": 0.9884000000000001,
          "economic_stress": 0.3114
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.1527,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-3/contain-response",
        "state_hash": "8d087b6d33b7435a",
        "depth": 2,
        "branch_id": "contain-response",
        "label": "Contain response",
        "prior": 0.269,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "735e9a6c6c5ffc67",
        "visits": 5,
        "value_sum": -1.0858500000000002,
        "metric_sums": {
          "escalation": 2.625,
          "negotiation": 1.6999999999999997,
          "economic_stress": 1.8195000000000001
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -1.0858500000000002,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.21717000000000003,
        "metrics": {
          "escalation": 0.525,
          "negotiation": 0.33999999999999997,
          "economic_stress": 0.3639
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.21717000000000003,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-3/retaliate",
        "state_hash": "6d4c6d45dca3cbae",
        "depth": 2,
        "branch_id": "retaliate",
        "label": "Retaliate",
        "prior": 0.21639999999999998,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "28f94df713dadd4d",
        "visits": 8,
        "value_sum": -0.65079,
        "metric_sums": {
          "escalation": 3.4649999999999994,
          "negotiation": 5.4064000000000005,
          "economic_stress": 2.9557
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.65079,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.08134875,
        "metrics": {
          "escalation": 0.4331249999999999,
          "negotiation": 0.6758000000000001,
          "economic_stress": 0.3694625
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.08134875,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation-3/retaliate/force-projection",
          "root/alliance-consultation-3/retaliate/emergency-backchannel"
        ]
      },
      {
        "node_id": "root/alliance-consultation-3/retaliate/emergency-backchannel",
        "state_hash": "bbf881330810562e",
        "depth": 3,
        "branch_id": "emergency-backchannel",
        "label": "Emergency backchannel",
        "prior": 0.192,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "ac2649a6d91750ab",
        "visits": 7,
        "value_sum": -0.1437200000000001,
        "metric_sums": {
          "escalation": 2.465,
          "negotiation": 5.3244,
          "economic_stress": 2.5168
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.1437200000000001,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.020531428571428586,
        "metrics": {
          "escalation": 0.35214285714285715,
          "negotiation": 0.7606285714285714,
          "economic_stress": 0.3595428571428571
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.020531428571428586,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation-3/retaliate/emergency-backchannel/confidence-measures",
          "root/alliance-consultation-3/retaliate/emergency-backchannel/stalemate-return"
        ]
      },
      {
        "node_id": "root/alliance-consultation-3/retaliate/emergency-backchannel/confidence-measures",
        "state_hash": "7a16c5d6daa76c9f",
        "depth": 4,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5509999999999999,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "06c19ef6c5165524",
        "visits": 6,
        "value_sum": 0.12815999999999986,
        "metric_sums": {
          "escalation": 1.818,
          "negotiation": 4.8816,
          "economic_stress": 2.0303999999999998
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.12815999999999986,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.021359999999999976,
        "metrics": {
          "escalation": 0.303,
          "negotiation": 0.8136,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.021359999999999976,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-3/retaliate/emergency-backchannel/stalemate-return",
        "state_hash": "2b45f35ee5014d5e",
        "depth": 4,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.09359999999999999,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "94ea189688f6c757",
        "visits": 1,
        "value_sum": -0.27187999999999996,
        "metric_sums": {
          "escalation": 0.6469999999999999,
          "negotiation": 0.44279999999999997,
          "economic_stress": 0.48639999999999994
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.27187999999999996,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.27187999999999996,
        "metrics": {
          "escalation": 0.6469999999999999,
          "negotiation": 0.44279999999999997,
          "economic_stress": 0.48639999999999994
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.27187999999999996,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation-3/retaliate/force-projection",
        "state_hash": "a94957366ee37c37",
        "depth": 3,
        "branch_id": "force-projection",
        "label": "Force projection",
        "prior": 0.3884,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "9f925a5b3af5d9c8",
        "visits": 1,
        "value_sum": -0.50707,
        "metric_sums": {
          "escalation": 1.0,
          "negotiation": 0.082,
          "economic_stress": 0.43889999999999996
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.50707,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.50707,
        "metrics": {
          "escalation": 1.0,
          "negotiation": 0.082,
          "economic_stress": 0.43889999999999996
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.50707,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation/confidence-measures",
        "state_hash": "cebdf52ed5fd50aa",
        "depth": 2,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5492,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "9098d62c567f47ef",
        "visits": 57,
        "value_sum": 1.2950399999999993,
        "metric_sums": {
          "escalation": 17.213999999999984,
          "negotiation": 46.55760000000003,
          "economic_stress": 19.2888
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 1.2950399999999993,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.022719999999999987,
        "metrics": {
          "escalation": 0.3019999999999997,
          "negotiation": 0.8168000000000005,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.022719999999999987,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation/stalemate-return",
        "state_hash": "d981cb6a2b00cb53",
        "depth": 2,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.1316,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "2c42fddc5d749b9a",
        "visits": 26,
        "value_sum": 1.4575899999999997,
        "metric_sums": {
          "escalation": 6.620000000000002,
          "negotiation": 22.381199999999993,
          "economic_stress": 8.695899999999998
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 1.4575899999999997,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.05606115384615384,
        "metrics": {
          "escalation": 0.2546153846153847,
          "negotiation": 0.8608153846153843,
          "economic_stress": 0.33445769230769223
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.05606115384615384,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation/stalemate-return/signal-resolve",
          "root/alliance-consultation/stalemate-return/intercept",
          "root/alliance-consultation/stalemate-return/allied-pressure",
          "root/alliance-consultation/stalemate-return/crisis-talks"
        ]
      },
      {
        "node_id": "root/alliance-consultation/stalemate-return/allied-pressure",
        "state_hash": "9e8575e6dda70dbe",
        "depth": 3,
        "branch_id": "allied-pressure",
        "label": "Allied pressure",
        "prior": 0.255,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "90c8b845cbd1b409",
        "visits": 5,
        "value_sum": -0.19188,
        "metric_sums": {
          "escalation": 1.863,
          "negotiation": 3.6844,
          "economic_stress": 1.8399999999999999
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.19188,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.038376,
        "metrics": {
          "escalation": 0.3726,
          "negotiation": 0.73688,
          "economic_stress": 0.368
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.038376,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation/stalemate-return/allied-pressure/confidence-measures",
          "root/alliance-consultation/stalemate-return/allied-pressure/stalemate-return"
        ]
      },
      {
        "node_id": "root/alliance-consultation/stalemate-return/allied-pressure/confidence-measures",
        "state_hash": "1547d03a7c4a55b6",
        "depth": 4,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5035999999999999,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "5436a06b384f58aa",
        "visits": 4,
        "value_sum": 0.0854399999999999,
        "metric_sums": {
          "escalation": 1.2120000000000002,
          "negotiation": 3.2544,
          "economic_stress": 1.3536
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.0854399999999999,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.021359999999999976,
        "metrics": {
          "escalation": 0.30300000000000005,
          "negotiation": 0.8136,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.021359999999999976,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation/stalemate-return/allied-pressure/stalemate-return",
        "state_hash": "778f9e79febeecff",
        "depth": 4,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.13040000000000002,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "8fd051017dfa129c",
        "visits": 1,
        "value_sum": -0.2773199999999999,
        "metric_sums": {
          "escalation": 0.6509999999999999,
          "negotiation": 0.43,
          "economic_stress": 0.48639999999999994
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.2773199999999999,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.2773199999999999,
        "metrics": {
          "escalation": 0.6509999999999999,
          "negotiation": 0.43,
          "economic_stress": 0.48639999999999994
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.2773199999999999,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation/stalemate-return/crisis-talks",
        "state_hash": "62a34a7df2d5f105",
        "depth": 3,
        "branch_id": "crisis-talks",
        "label": "Crisis talks",
        "prior": 0.359,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "93bd54027a571112",
        "visits": 7,
        "value_sum": 0.18759999999999993,
        "metric_sums": {
          "escalation": 2.093,
          "negotiation": 5.784799999999999,
          "economic_stress": 2.3688
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.18759999999999993,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.02679999999999999,
        "metrics": {
          "escalation": 0.299,
          "negotiation": 0.8263999999999998,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.02679999999999999,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation/stalemate-return/crisis-talks/confidence-measures",
          "root/alliance-consultation/stalemate-return/crisis-talks/stalemate-return"
        ]
      },
      {
        "node_id": "root/alliance-consultation/stalemate-return/crisis-talks/confidence-measures",
        "state_hash": "261d1c955c3f548c",
        "depth": 4,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5859000000000001,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "be6b6ee2ab6b3f65",
        "visits": 7,
        "value_sum": 0.18759999999999993,
        "metric_sums": {
          "escalation": 2.093,
          "negotiation": 5.784799999999999,
          "economic_stress": 2.3688
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 0.18759999999999993,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.02679999999999999,
        "metrics": {
          "escalation": 0.299,
          "negotiation": 0.8263999999999998,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.02679999999999999,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation/stalemate-return/crisis-talks/stalemate-return",
        "state_hash": "4e5b150a2a1be3bf",
        "depth": 4,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.07919999999999999,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "279ba1ede334e537",
        "visits": 0,
        "value_sum": 0.0,
        "metric_sums": {},
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {},
        "score": 0.0,
        "metrics": {},
        "actor_metrics": {},
        "aggregate_score_breakdown": {},
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation/stalemate-return/intercept",
        "state_hash": "82f9d17bba1207bb",
        "depth": 3,
        "branch_id": "intercept",
        "label": "Intercept",
        "prior": 0.14839999999999998,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "c048e90392bcf274",
        "visits": 1,
        "value_sum": -0.48787,
        "metric_sums": {
          "escalation": 1.0,
          "negotiation": 0.14600000000000002,
          "economic_stress": 0.43889999999999996
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.48787,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.48787,
        "metrics": {
          "escalation": 1.0,
          "negotiation": 0.14600000000000002,
          "economic_stress": 0.43889999999999996
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.48787,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/alliance-consultation/stalemate-return/intercept/force-projection",
          "root/alliance-consultation/stalemate-return/intercept/emergency-backchannel"
        ]
      },
      {
        "node_id": "root/alliance-consultation/stalemate-return/intercept/emergency-backchannel",
        "state_hash": "1d36d0e1e52e30a4",
        "depth": 4,
        "branch_id": "emergency-backchannel",
        "label": "Emergency backchannel",
        "prior": 0.32000000000000006,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "091caf7c40dc76d2",
        "visits": 0,
        "value_sum": 0.0,
        "metric_sums": {},
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {},
        "score": 0.0,
        "metrics": {},
        "actor_metrics": {},
        "aggregate_score_breakdown": {},
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation/stalemate-return/intercept/force-projection",
        "state_hash": "6ede23a148cc94aa",
        "depth": 4,
        "branch_id": "force-projection",
        "label": "Force projection",
        "prior": 0.3744,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "1f2b708696b11ad0",
        "visits": 1,
        "value_sum": -0.48787,
        "metric_sums": {
          "escalation": 1.0,
          "negotiation": 0.14600000000000002,
          "economic_stress": 0.43889999999999996
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.48787,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.48787,
        "metrics": {
          "escalation": 1.0,
          "negotiation": 0.14600000000000002,
          "economic_stress": 0.43889999999999996
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.48787,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/alliance-consultation/stalemate-return/signal-resolve",
        "state_hash": "dd5797a6f3ad677b",
        "depth": 3,
        "branch_id": "signal-resolve",
        "label": "Signal resolve",
        "prior": 0.378,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "dependency_hash": "17068ca23dce4072",
        "visits": 13,
        "value_sum": 1.9497399999999998,
        "metric_sums": {
          "escalation": 1.6640000000000006,
          "negotiation": 12.765999999999998,
          "economic_stress": 4.0482
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 1.9497399999999998,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.14997999999999997,
        "metrics": {
          "escalation": 0.12800000000000006,
          "negotiation": 0.9819999999999999,
          "economic_stress": 0.31139999999999995
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.14997999999999997,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response",
        "state_hash": "bb12debe16955e0c",
        "depth": 1,
        "branch_id": "limited-response",
        "label": "Limited response (contained response)",
        "prior": 0.18984,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "3816f99820d37bd5",
        "visits": 222,
        "value_sum": 9.83382,
        "metric_sums": {
          "escalation": 58.81799999999973,
          "negotiation": 186.85320000000075,
          "economic_stress": 75.64979999999997
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 9.83382,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.044296486486486486,
        "metrics": {
          "escalation": 0.2649459459459447,
          "negotiation": 0.8416810810810845,
          "economic_stress": 0.34076486486486474
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.044296486486486486,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/limited-response/contain-response",
          "root/limited-response/retaliate",
          "root/limited-response/ceasefire-channel"
        ]
      },
      {
        "node_id": "root/limited-response-2",
        "state_hash": "b95f69a1fa2902e2",
        "depth": 1,
        "branch_id": "limited-response-2",
        "label": "Limited response (escalatory response)",
        "prior": 0.12656,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "1324c8f27479c221",
        "visits": 462,
        "value_sum": 51.05187000000026,
        "metric_sums": {
          "escalation": 82.73700000000026,
          "negotiation": 430.42119999999755,
          "economic_stress": 149.9323000000005
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 51.05187000000026,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.11050188311688368,
        "metrics": {
          "escalation": 0.17908441558441615,
          "negotiation": 0.9316476190476137,
          "economic_stress": 0.32452878787878897
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.11050188311688368,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/limited-response-2/force-projection",
          "root/limited-response-2/emergency-backchannel"
        ]
      },
      {
        "node_id": "root/limited-response-2/emergency-backchannel",
        "state_hash": "b52b19b7920612af",
        "depth": 2,
        "branch_id": "emergency-backchannel",
        "label": "Emergency backchannel",
        "prior": 0.1908,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "6527215a3636cf53",
        "visits": 529,
        "value_sum": 53.520190000000305,
        "metric_sums": {
          "escalation": 103.67300000000064,
          "negotiation": 492.606399999996,
          "economic_stress": 175.97509999999997
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 53.520190000000305,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.10117238185255256,
        "metrics": {
          "escalation": 0.19597920604915056,
          "negotiation": 0.9312030245746615,
          "economic_stress": 0.33265614366729673
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.10117238185255256,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/limited-response-2/emergency-backchannel/confidence-measures",
          "root/limited-response-2/emergency-backchannel/stalemate-return"
        ]
      },
      {
        "node_id": "root/limited-response-2/emergency-backchannel/confidence-measures",
        "state_hash": "79913979c85da0b7",
        "depth": 3,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5509999999999999,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "0a16820d7320907d",
        "visits": 175,
        "value_sum": 3.738000000000004,
        "metric_sums": {
          "escalation": 53.02499999999987,
          "negotiation": 142.3799999999997,
          "economic_stress": 59.22
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 3.738000000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.02136000000000002,
        "metrics": {
          "escalation": 0.30299999999999927,
          "negotiation": 0.8135999999999983,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.02136000000000002,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response-2/emergency-backchannel/stalemate-return",
        "state_hash": "7b5c068c2f250473",
        "depth": 3,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.09359999999999999,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "639c702a1d98507d",
        "visits": 439,
        "value_sum": 55.59064000000027,
        "metric_sums": {
          "escalation": 68.75299999999979,
          "negotiation": 419.0943999999977,
          "economic_stress": 142.12160000000074
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 55.59064000000027,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.12663015945330358,
        "metrics": {
          "escalation": 0.15661275626423643,
          "negotiation": 0.9546569476081952,
          "economic_stress": 0.3237394077448764
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.12663015945330358,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/limited-response-2/emergency-backchannel/stalemate-return/signal-resolve",
          "root/limited-response-2/emergency-backchannel/stalemate-return/intercept",
          "root/limited-response-2/emergency-backchannel/stalemate-return/allied-pressure",
          "root/limited-response-2/emergency-backchannel/stalemate-return/crisis-talks"
        ]
      },
      {
        "node_id": "root/limited-response-2/emergency-backchannel/stalemate-return/allied-pressure",
        "state_hash": "888ee3d9508a56d6",
        "depth": 4,
        "branch_id": "allied-pressure",
        "label": "Allied pressure",
        "prior": 0.19720000000000001,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "7b3fd586af43f72f",
        "visits": 15,
        "value_sum": -2.1762799999999998,
        "metric_sums": {
          "escalation": 8.309,
          "negotiation": 10.252399999999996,
          "economic_stress": 6.428000000000001
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -2.1762799999999998,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.14508533333333332,
        "metrics": {
          "escalation": 0.5539333333333333,
          "negotiation": 0.6834933333333331,
          "economic_stress": 0.4285333333333334
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.14508533333333332,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response-2/emergency-backchannel/stalemate-return/crisis-talks",
        "state_hash": "ba7950a999876aa4",
        "depth": 4,
        "branch_id": "crisis-talks",
        "label": "Crisis talks",
        "prior": 0.3518,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "d05f6192776e4ea3",
        "visits": 477,
        "value_sum": 38.84480000000015,
        "metric_sums": {
          "escalation": 103.13500000000008,
          "negotiation": 430.50280000000174,
          "economic_stress": 163.50680000000105
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 38.84480000000015,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.08143563941299821,
        "metrics": {
          "escalation": 0.21621593291404628,
          "negotiation": 0.9025215932914082,
          "economic_stress": 0.3427815513626856
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.08143563941299821,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response-2/emergency-backchannel/stalemate-return/intercept",
        "state_hash": "831a1408abb2b8dc",
        "depth": 4,
        "branch_id": "intercept",
        "label": "Intercept",
        "prior": 0.15,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "4cbc3aeedbf61585",
        "visits": 4,
        "value_sum": -2.2957199999999998,
        "metric_sums": {
          "escalation": 3.6959999999999997,
          "negotiation": 1.1712,
          "economic_stress": 3.8956
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -2.2957199999999998,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.5739299999999999,
        "metrics": {
          "escalation": 0.9239999999999999,
          "negotiation": 0.2928,
          "economic_stress": 0.9739
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.5739299999999999,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response-2/emergency-backchannel/stalemate-return/signal-resolve",
        "state_hash": "462d4558a9edf2fa",
        "depth": 4,
        "branch_id": "signal-resolve",
        "label": "Signal resolve",
        "prior": 0.3744,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "457e931ef0baecb3",
        "visits": 415,
        "value_sum": 61.6773000000003,
        "metric_sums": {
          "escalation": 53.534999999999755,
          "negotiation": 406.201999999998,
          "economic_stress": 129.2310000000011
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 61.6773000000003,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.14862000000000072,
        "metrics": {
          "escalation": 0.12899999999999942,
          "negotiation": 0.9787999999999952,
          "economic_stress": 0.3114000000000027
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.14862000000000072,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response-2/force-projection",
        "state_hash": "7e7df5757e951804",
        "depth": 2,
        "branch_id": "force-projection",
        "label": "Force projection",
        "prior": 0.3804,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "dfc9e81a6458cd9f",
        "visits": 15,
        "value_sum": -7.642050000000002,
        "metric_sums": {
          "escalation": 15.0,
          "negotiation": 1.1100000000000005,
          "economic_stress": 6.583500000000001
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -7.642050000000002,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.5094700000000001,
        "metrics": {
          "escalation": 1.0,
          "negotiation": 0.07400000000000004,
          "economic_stress": 0.43890000000000007
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.5094700000000001,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response/ceasefire-channel",
        "state_hash": "c48ca1dcb20c72dc",
        "depth": 2,
        "branch_id": "ceasefire-channel",
        "label": "Ceasefire channel",
        "prior": 0.21299999999999997,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "1054e1fb0b4f7a4d",
        "visits": 194,
        "value_sum": 15.098219999999966,
        "metric_sums": {
          "escalation": 44.111999999999945,
          "negotiation": 174.02000000000058,
          "economic_stress": 64.8765999999999
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 15.098219999999966,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.07782587628865961,
        "metrics": {
          "escalation": 0.22738144329896878,
          "negotiation": 0.8970103092783535,
          "economic_stress": 0.33441546391752525
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.07782587628865961,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/limited-response/ceasefire-channel/confidence-measures",
          "root/limited-response/ceasefire-channel/stalemate-return"
        ]
      },
      {
        "node_id": "root/limited-response/ceasefire-channel/confidence-measures",
        "state_hash": "95b4f430bcca6c5f",
        "depth": 3,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5928,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "abc340e9d0cf4a16",
        "visits": 87,
        "value_sum": 2.213279999999998,
        "metric_sums": {
          "escalation": 26.10000000000004,
          "negotiation": 71.61840000000001,
          "economic_stress": 29.4408
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 2.213279999999998,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.025439999999999977,
        "metrics": {
          "escalation": 0.3000000000000005,
          "negotiation": 0.8232,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.025439999999999977,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response/ceasefire-channel/stalemate-return",
        "state_hash": "207cb87062cc9b70",
        "depth": 3,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.08279999999999998,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "6d460338e155ffb2",
        "visits": 107,
        "value_sum": 12.88493999999998,
        "metric_sums": {
          "escalation": 18.011999999999993,
          "negotiation": 102.4015999999999,
          "economic_stress": 35.43579999999996
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 12.88493999999998,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.12041999999999982,
        "metrics": {
          "escalation": 0.16833644859813077,
          "negotiation": 0.9570242990654196,
          "economic_stress": 0.33117570093457904
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.12041999999999982,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/limited-response/ceasefire-channel/stalemate-return/signal-resolve",
          "root/limited-response/ceasefire-channel/stalemate-return/intercept",
          "root/limited-response/ceasefire-channel/stalemate-return/allied-pressure",
          "root/limited-response/ceasefire-channel/stalemate-return/crisis-talks"
        ]
      },
      {
        "node_id": "root/limited-response/ceasefire-channel/stalemate-return/allied-pressure",
        "state_hash": "257bb4398e8ef790",
        "depth": 4,
        "branch_id": "allied-pressure",
        "label": "Allied pressure",
        "prior": 0.19720000000000001,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "5b4f66cf7ebd6ea9",
        "visits": 7,
        "value_sum": -0.9399600000000004,
        "metric_sums": {
          "escalation": 3.822000000000001,
          "negotiation": 4.933599999999999,
          "economic_stress": 2.9707999999999997
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.9399600000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.13428000000000004,
        "metrics": {
          "escalation": 0.5460000000000002,
          "negotiation": 0.7047999999999999,
          "economic_stress": 0.42439999999999994
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.13428000000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response/ceasefire-channel/stalemate-return/crisis-talks",
        "state_hash": "ba7950a999876aa4",
        "depth": 4,
        "branch_id": "crisis-talks",
        "label": "Crisis talks",
        "prior": 0.3734,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "d05f6192776e4ea3",
        "visits": 477,
        "value_sum": 38.84480000000015,
        "metric_sums": {
          "escalation": 103.13500000000008,
          "negotiation": 430.50280000000174,
          "economic_stress": 163.50680000000105
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 38.84480000000015,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.08143563941299821,
        "metrics": {
          "escalation": 0.21621593291404628,
          "negotiation": 0.9025215932914082,
          "economic_stress": 0.3427815513626856
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.08143563941299821,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response/ceasefire-channel/stalemate-return/intercept",
        "state_hash": "933932881ef02517",
        "depth": 4,
        "branch_id": "intercept",
        "label": "Intercept",
        "prior": 0.1452,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "61d1288260fae738",
        "visits": 2,
        "value_sum": -1.1397,
        "metric_sums": {
          "escalation": 1.8419999999999999,
          "negotiation": 0.6048,
          "economic_stress": 1.9478
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -1.1397,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.56985,
        "metrics": {
          "escalation": 0.9209999999999999,
          "negotiation": 0.3024,
          "economic_stress": 0.9739
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.56985,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response/ceasefire-channel/stalemate-return/signal-resolve",
        "state_hash": "70673d3243e743ad",
        "depth": 4,
        "branch_id": "signal-resolve",
        "label": "Signal resolve",
        "prior": 0.3852,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "9f418775a46240ef",
        "visits": 98,
        "value_sum": 14.964599999999978,
        "metric_sums": {
          "escalation": 12.347999999999988,
          "negotiation": 96.86319999999989,
          "economic_stress": 30.517199999999974
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 14.964599999999978,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.15269999999999978,
        "metrics": {
          "escalation": 0.1259999999999999,
          "negotiation": 0.988399999999999,
          "economic_stress": 0.31139999999999973
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.15269999999999978,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response/contain-response",
        "state_hash": "3cb339280a72ac61",
        "depth": 2,
        "branch_id": "contain-response",
        "label": "Contain response",
        "prior": 0.267,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "a26ad0c3d9aaba60",
        "visits": 14,
        "value_sum": -3.04038,
        "metric_sums": {
          "escalation": 7.350000000000002,
          "negotiation": 4.759999999999999,
          "economic_stress": 5.094600000000001
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -3.04038,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.21717,
        "metrics": {
          "escalation": 0.5250000000000001,
          "negotiation": 0.3399999999999999,
          "economic_stress": 0.36390000000000006
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.21717,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response/retaliate",
        "state_hash": "19a9c5edbd83ccd1",
        "depth": 2,
        "branch_id": "retaliate",
        "label": "Retaliate",
        "prior": 0.2142,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "146dfe2bcce6d7ee",
        "visits": 14,
        "value_sum": -2.22402,
        "metric_sums": {
          "escalation": 7.356000000000001,
          "negotiation": 8.0732,
          "economic_stress": 5.6785999999999985
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -2.22402,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.15885857142857143,
        "metrics": {
          "escalation": 0.5254285714285715,
          "negotiation": 0.5766571428571429,
          "economic_stress": 0.4056142857142856
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.15885857142857143,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/limited-response/retaliate/force-projection",
          "root/limited-response/retaliate/emergency-backchannel"
        ]
      },
      {
        "node_id": "root/limited-response/retaliate/emergency-backchannel",
        "state_hash": "b52b19b7920612af",
        "depth": 3,
        "branch_id": "emergency-backchannel",
        "label": "Emergency backchannel",
        "prior": 0.192,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "6527215a3636cf53",
        "visits": 529,
        "value_sum": 53.520190000000305,
        "metric_sums": {
          "escalation": 103.67300000000064,
          "negotiation": 492.606399999996,
          "economic_stress": 175.97509999999997
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 53.520190000000305,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.10117238185255256,
        "metrics": {
          "escalation": 0.19597920604915056,
          "negotiation": 0.9312030245746615,
          "economic_stress": 0.33265614366729673
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.10117238185255256,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/limited-response/retaliate/emergency-backchannel/confidence-measures",
          "root/limited-response/retaliate/emergency-backchannel/stalemate-return"
        ]
      },
      {
        "node_id": "root/limited-response/retaliate/emergency-backchannel/confidence-measures",
        "state_hash": "79913979c85da0b7",
        "depth": 4,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5509999999999999,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "0a16820d7320907d",
        "visits": 175,
        "value_sum": 3.738000000000004,
        "metric_sums": {
          "escalation": 53.02499999999987,
          "negotiation": 142.3799999999997,
          "economic_stress": 59.22
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 3.738000000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.02136000000000002,
        "metrics": {
          "escalation": 0.30299999999999927,
          "negotiation": 0.8135999999999983,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.02136000000000002,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response/retaliate/emergency-backchannel/stalemate-return",
        "state_hash": "7b5c068c2f250473",
        "depth": 4,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.09359999999999999,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "639c702a1d98507d",
        "visits": 439,
        "value_sum": 55.59064000000027,
        "metric_sums": {
          "escalation": 68.75299999999979,
          "negotiation": 419.0943999999977,
          "economic_stress": 142.12160000000074
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 55.59064000000027,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.12663015945330358,
        "metrics": {
          "escalation": 0.15661275626423643,
          "negotiation": 0.9546569476081952,
          "economic_stress": 0.3237394077448764
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.12663015945330358,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/limited-response/retaliate/force-projection",
        "state_hash": "85a0b3cae29cdb44",
        "depth": 3,
        "branch_id": "force-projection",
        "label": "Force projection",
        "prior": 0.3884,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "300391608fe2fd25",
        "visits": 2,
        "value_sum": -1.01414,
        "metric_sums": {
          "escalation": 2.0,
          "negotiation": 0.164,
          "economic_stress": 0.8777999999999999
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -1.01414,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.50707,
        "metrics": {
          "escalation": 1.0,
          "negotiation": 0.082,
          "economic_stress": 0.43889999999999996
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.50707,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/open-negotiation",
        "state_hash": "57c609deb3182765",
        "depth": 1,
        "branch_id": "open-negotiation",
        "label": "Open negotiation",
        "prior": 0.22340000000000002,
        "dependencies": {
          "fields": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "1402bcd4ee3ca447",
        "visits": 7195,
        "value_sum": 998.8426099998794,
        "metric_sums": {
          "escalation": 1046.964999999995,
          "negotiation": 6996.50720000051,
          "economic_stress": 2271.0785000002584
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 998.8426099998794,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.1388245462126309,
        "metrics": {
          "escalation": 0.14551285615010354,
          "negotiation": 0.9724123974983336,
          "economic_stress": 0.31564676858933405
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.1388245462126309,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/open-negotiation/confidence-measures",
          "root/open-negotiation/stalemate-return"
        ]
      },
      {
        "node_id": "root/open-negotiation/confidence-measures",
        "state_hash": "241d0ff8840299af",
        "depth": 2,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5859000000000001,
        "dependencies": {
          "fields": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "db9aff5e2198a36c",
        "visits": 488,
        "value_sum": 13.078399999999911,
        "metric_sums": {
          "escalation": 145.9120000000017,
          "negotiation": 403.28319999999763,
          "economic_stress": 165.13919999999945
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 13.078399999999911,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.026799999999999817,
        "metrics": {
          "escalation": 0.2990000000000035,
          "negotiation": 0.8263999999999951,
          "economic_stress": 0.33839999999999887
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.026799999999999817,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/open-negotiation/stalemate-return",
        "state_hash": "8c76aca2b882449f",
        "depth": 2,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.07919999999999999,
        "dependencies": {
          "fields": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "3819062e30299cd7",
        "visits": 7182,
        "value_sum": 1024.5554099998749,
        "metric_sums": {
          "escalation": 1003.5899999999998,
          "negotiation": 7022.074000000552,
          "economic_stress": 2268.7693000002546
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 1024.5554099998749,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.14265600250624824,
        "metrics": {
          "escalation": 0.13973684210526313,
          "negotiation": 0.9777323865219371,
          "economic_stress": 0.31589658869399256
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.14265600250624824,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/open-negotiation/stalemate-return/signal-resolve",
          "root/open-negotiation/stalemate-return/intercept",
          "root/open-negotiation/stalemate-return/allied-pressure",
          "root/open-negotiation/stalemate-return/crisis-talks"
        ]
      },
      {
        "node_id": "root/open-negotiation/stalemate-return/allied-pressure",
        "state_hash": "a2eac07db07e149a",
        "depth": 3,
        "branch_id": "allied-pressure",
        "label": "Allied pressure",
        "prior": 0.19720000000000001,
        "dependencies": {
          "fields": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "c7b5ea67e936da29",
        "visits": 119,
        "value_sum": -0.18480000000000102,
        "metric_sums": {
          "escalation": 39.86099999999998,
          "negotiation": 94.25359999999984,
          "economic_stress": 41.7216
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.18480000000000102,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.0015529411764705968,
        "metrics": {
          "escalation": 0.3349663865546217,
          "negotiation": 0.792047058823528,
          "economic_stress": 0.35060168067226893
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.0015529411764705968,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/open-negotiation/stalemate-return/allied-pressure/confidence-measures",
          "root/open-negotiation/stalemate-return/allied-pressure/stalemate-return"
        ]
      },
      {
        "node_id": "root/open-negotiation/stalemate-return/allied-pressure/confidence-measures",
        "state_hash": "79913979c85da0b7",
        "depth": 4,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5147999999999999,
        "dependencies": {
          "fields": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "3f7263e2678962c9",
        "visits": 175,
        "value_sum": 3.738000000000004,
        "metric_sums": {
          "escalation": 53.02499999999987,
          "negotiation": 142.3799999999997,
          "economic_stress": 59.22
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 3.738000000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.02136000000000002,
        "metrics": {
          "escalation": 0.30299999999999927,
          "negotiation": 0.8135999999999983,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.02136000000000002,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/open-negotiation/stalemate-return/allied-pressure/stalemate-return",
        "state_hash": "c08c226708ea76ec",
        "depth": 4,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.12319999999999999,
        "dependencies": {
          "fields": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "51c1d4be162cb6e2",
        "visits": 4,
        "value_sum": -1.0983999999999998,
        "metric_sums": {
          "escalation": 2.5959999999999996,
          "negotiation": 1.7456,
          "economic_stress": 1.9455999999999998
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -1.0983999999999998,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.27459999999999996,
        "metrics": {
          "escalation": 0.6489999999999999,
          "negotiation": 0.4364,
          "economic_stress": 0.48639999999999994
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.27459999999999996,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/open-negotiation/stalemate-return/crisis-talks",
        "state_hash": "ba7950a999876aa4",
        "depth": 3,
        "branch_id": "crisis-talks",
        "label": "Crisis talks",
        "prior": 0.3806,
        "dependencies": {
          "fields": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "09c73d782ff49beb",
        "visits": 477,
        "value_sum": 38.84480000000015,
        "metric_sums": {
          "escalation": 103.13500000000008,
          "negotiation": 430.50280000000174,
          "economic_stress": 163.50680000000105
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 38.84480000000015,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.08143563941299821,
        "metrics": {
          "escalation": 0.21621593291404628,
          "negotiation": 0.9025215932914082,
          "economic_stress": 0.3427815513626856
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.08143563941299821,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/open-negotiation/stalemate-return/crisis-talks/confidence-measures",
          "root/open-negotiation/stalemate-return/crisis-talks/stalemate-return"
        ]
      },
      {
        "node_id": "root/open-negotiation/stalemate-return/crisis-talks/confidence-measures",
        "state_hash": "241d0ff8840299af",
        "depth": 4,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5859000000000001,
        "dependencies": {
          "fields": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "db9aff5e2198a36c",
        "visits": 488,
        "value_sum": 13.078399999999911,
        "metric_sums": {
          "escalation": 145.9120000000017,
          "negotiation": 403.28319999999763,
          "economic_stress": 165.13919999999945
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 13.078399999999911,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.026799999999999817,
        "metrics": {
          "escalation": 0.2990000000000035,
          "negotiation": 0.8263999999999951,
          "economic_stress": 0.33839999999999887
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.026799999999999817,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/open-negotiation/stalemate-return/crisis-talks/stalemate-return",
        "state_hash": "8c76aca2b882449f",
        "depth": 4,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.07919999999999999,
        "dependencies": {
          "fields": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "3819062e30299cd7",
        "visits": 7182,
        "value_sum": 1024.5554099998749,
        "metric_sums": {
          "escalation": 1003.5899999999998,
          "negotiation": 7022.074000000552,
          "economic_stress": 2268.7693000002546
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 1024.5554099998749,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.14265600250624824,
        "metrics": {
          "escalation": 0.13973684210526313,
          "negotiation": 0.9777323865219371,
          "economic_stress": 0.31589658869399256
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.14265600250624824,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/open-negotiation/stalemate-return/intercept",
        "state_hash": "c43eee67cc1625c4",
        "depth": 3,
        "branch_id": "intercept",
        "label": "Intercept",
        "prior": 0.14359999999999998,
        "dependencies": {
          "fields": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "b2c541e7bc4a0f8c",
        "visits": 45,
        "value_sum": -6.706610000000009,
        "metric_sums": {
          "escalation": 25.180999999999994,
          "negotiation": 32.1848,
          "economic_stress": 20.96550000000002
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -6.706610000000009,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.149035777777778,
        "metrics": {
          "escalation": 0.5595777777777776,
          "negotiation": 0.7152177777777778,
          "economic_stress": 0.4659000000000004
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.149035777777778,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/open-negotiation/stalemate-return/intercept/force-projection",
          "root/open-negotiation/stalemate-return/intercept/emergency-backchannel"
        ]
      },
      {
        "node_id": "root/open-negotiation/stalemate-return/intercept/emergency-backchannel",
        "state_hash": "b52b19b7920612af",
        "depth": 4,
        "branch_id": "emergency-backchannel",
        "label": "Emergency backchannel",
        "prior": 0.3368,
        "dependencies": {
          "fields": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "d2600cc9360c87db",
        "visits": 529,
        "value_sum": 53.520190000000305,
        "metric_sums": {
          "escalation": 103.67300000000064,
          "negotiation": 492.606399999996,
          "economic_stress": 175.97509999999997
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 53.520190000000305,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.10117238185255256,
        "metrics": {
          "escalation": 0.19597920604915056,
          "negotiation": 0.9312030245746615,
          "economic_stress": 0.33265614366729673
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.10117238185255256,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/open-negotiation/stalemate-return/intercept/force-projection",
        "state_hash": "0dff861f1dcb1f3c",
        "depth": 4,
        "branch_id": "force-projection",
        "label": "Force projection",
        "prior": 0.3744,
        "dependencies": {
          "fields": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "b628380dc7a7d9bf",
        "visits": 4,
        "value_sum": -1.93996,
        "metric_sums": {
          "escalation": 4.0,
          "negotiation": 0.6224000000000001,
          "economic_stress": 1.7555999999999998
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -1.93996,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.48499,
        "metrics": {
          "escalation": 1.0,
          "negotiation": 0.15560000000000002,
          "economic_stress": 0.43889999999999996
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.48499,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/open-negotiation/stalemate-return/signal-resolve",
        "state_hash": "45b464eeb9d1da33",
        "depth": 3,
        "branch_id": "signal-resolve",
        "label": "Signal resolve",
        "prior": 0.38880000000000003,
        "dependencies": {
          "fields": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "27f86318104c9ada",
        "visits": 6898,
        "value_sum": 1062.705879999896,
        "metric_sums": {
          "escalation": 862.25,
          "negotiation": 6840.0568000005005,
          "economic_stress": 2148.037200000247
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 1062.705879999896,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.15405999999998493,
        "metrics": {
          "escalation": 0.125,
          "negotiation": 0.9916000000000725,
          "economic_stress": 0.3114000000000358
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.15405999999998493,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal",
        "state_hash": "9a6772b110468f57",
        "depth": 1,
        "branch_id": "signal",
        "label": "Signal resolve (managed signal)",
        "prior": 0.15172045266353848,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "157c59a43d2e5ad0",
        "visits": 1362,
        "value_sum": 172.5751400000002,
        "metric_sums": {
          "escalation": 211.26400000000058,
          "negotiation": 1290.2235999999825,
          "economic_stress": 433.287799999993
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 172.5751400000002,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.12670715124816462,
        "metrics": {
          "escalation": 0.15511306901615315,
          "negotiation": 0.9473007342143778,
          "economic_stress": 0.3181261380323003
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.12670715124816462,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/signal/signal-resolve",
          "root/signal/intercept",
          "root/signal/allied-pressure",
          "root/signal/crisis-talks"
        ]
      },
      {
        "node_id": "root/signal-2",
        "state_hash": "f12a9ab9c6cd23f0",
        "depth": 1,
        "branch_id": "signal-2",
        "label": "Signal resolve (backchannel opening)",
        "prior": 0.1166795473364615,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "e4768c1f9c3848bf",
        "visits": 492,
        "value_sum": 56.60427999999977,
        "metric_sums": {
          "escalation": 86.79500000000013,
          "negotiation": 461.782400000005,
          "economic_stress": 157.3748000000001
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 56.60427999999977,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.11504934959349547,
        "metrics": {
          "escalation": 0.17641260162601652,
          "negotiation": 0.9385821138211484,
          "economic_stress": 0.31986747967479695
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.11504934959349547,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/signal-2/confidence-measures",
          "root/signal-2/stalemate-return"
        ]
      },
      {
        "node_id": "root/signal-2/confidence-measures",
        "state_hash": "b33497068a604546",
        "depth": 2,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5366,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "3903c2cf46b58130",
        "visits": 108,
        "value_sum": 2.453760000000003,
        "metric_sums": {
          "escalation": 32.615999999999964,
          "negotiation": 88.21440000000005,
          "economic_stress": 36.5472
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 2.453760000000003,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.02272000000000003,
        "metrics": {
          "escalation": 0.30199999999999966,
          "negotiation": 0.8168000000000005,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.02272000000000003,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal-2/stalemate-return",
        "state_hash": "02ca22904e333399",
        "depth": 2,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.11880000000000002,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "d1d02347470ee6a9",
        "visits": 384,
        "value_sum": 54.150519999999794,
        "metric_sums": {
          "escalation": 54.17900000000004,
          "negotiation": 373.56800000000305,
          "economic_stress": 120.82760000000097
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 54.150519999999794,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.14101697916666614,
        "metrics": {
          "escalation": 0.14109114583333343,
          "negotiation": 0.9728333333333413,
          "economic_stress": 0.3146552083333359
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.14101697916666614,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/signal-2/stalemate-return/signal-resolve",
          "root/signal-2/stalemate-return/intercept",
          "root/signal-2/stalemate-return/allied-pressure",
          "root/signal-2/stalemate-return/crisis-talks"
        ]
      },
      {
        "node_id": "root/signal-2/stalemate-return/allied-pressure",
        "state_hash": "888ee3d9508a56d6",
        "depth": 3,
        "branch_id": "allied-pressure",
        "label": "Allied pressure",
        "prior": 0.19720000000000001,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "ca697a36925272ff",
        "visits": 15,
        "value_sum": -2.1762799999999998,
        "metric_sums": {
          "escalation": 8.309,
          "negotiation": 10.252399999999996,
          "economic_stress": 6.428000000000001
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -2.1762799999999998,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.14508533333333332,
        "metrics": {
          "escalation": 0.5539333333333333,
          "negotiation": 0.6834933333333331,
          "economic_stress": 0.4285333333333334
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.14508533333333332,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/signal-2/stalemate-return/allied-pressure/confidence-measures",
          "root/signal-2/stalemate-return/allied-pressure/stalemate-return"
        ]
      },
      {
        "node_id": "root/signal-2/stalemate-return/allied-pressure/confidence-measures",
        "state_hash": "79913979c85da0b7",
        "depth": 4,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5035999999999999,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "3f7263e2678962c9",
        "visits": 175,
        "value_sum": 3.738000000000004,
        "metric_sums": {
          "escalation": 53.02499999999987,
          "negotiation": 142.3799999999997,
          "economic_stress": 59.22
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 3.738000000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.02136000000000002,
        "metrics": {
          "escalation": 0.30299999999999927,
          "negotiation": 0.8135999999999983,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.02136000000000002,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal-2/stalemate-return/allied-pressure/stalemate-return",
        "state_hash": "9fce5f2ae7ad19c0",
        "depth": 4,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.13040000000000002,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "285dbb0546c6c0d8",
        "visits": 142,
        "value_sum": 17.071859999999962,
        "metric_sums": {
          "escalation": 23.063999999999925,
          "negotiation": 133.94199999999972,
          "economic_stress": 46.28379999999993
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 17.071859999999962,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.12022436619718282,
        "metrics": {
          "escalation": 0.1624225352112671,
          "negotiation": 0.9432535211267586,
          "economic_stress": 0.32594225352112627
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.12022436619718282,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal-2/stalemate-return/crisis-talks",
        "state_hash": "ba7950a999876aa4",
        "depth": 3,
        "branch_id": "crisis-talks",
        "label": "Crisis talks",
        "prior": 0.359,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "09c73d782ff49beb",
        "visits": 477,
        "value_sum": 38.84480000000015,
        "metric_sums": {
          "escalation": 103.13500000000008,
          "negotiation": 430.50280000000174,
          "economic_stress": 163.50680000000105
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 38.84480000000015,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.08143563941299821,
        "metrics": {
          "escalation": 0.21621593291404628,
          "negotiation": 0.9025215932914082,
          "economic_stress": 0.3427815513626856
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.08143563941299821,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal-2/stalemate-return/intercept",
        "state_hash": "425559ebc1d5ac1d",
        "depth": 3,
        "branch_id": "intercept",
        "label": "Intercept",
        "prior": 0.14839999999999998,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "d488489783eb7585",
        "visits": 10,
        "value_sum": -1.5147000000000006,
        "metric_sums": {
          "escalation": 5.784,
          "negotiation": 6.852,
          "economic_stress": 4.189
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -1.5147000000000006,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.15147000000000005,
        "metrics": {
          "escalation": 0.5784,
          "negotiation": 0.6852,
          "economic_stress": 0.4189
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.15147000000000005,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/signal-2/stalemate-return/intercept/force-projection",
          "root/signal-2/stalemate-return/intercept/emergency-backchannel"
        ]
      },
      {
        "node_id": "root/signal-2/stalemate-return/intercept/emergency-backchannel",
        "state_hash": "b52b19b7920612af",
        "depth": 4,
        "branch_id": "emergency-backchannel",
        "label": "Emergency backchannel",
        "prior": 0.32000000000000006,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "d2600cc9360c87db",
        "visits": 529,
        "value_sum": 53.520190000000305,
        "metric_sums": {
          "escalation": 103.67300000000064,
          "negotiation": 492.606399999996,
          "economic_stress": 175.97509999999997
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 53.520190000000305,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.10117238185255256,
        "metrics": {
          "escalation": 0.19597920604915056,
          "negotiation": 0.9312030245746615,
          "economic_stress": 0.33265614366729673
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.10117238185255256,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal-2/stalemate-return/intercept/force-projection",
        "state_hash": "74f177901f8c3d55",
        "depth": 4,
        "branch_id": "force-projection",
        "label": "Force projection",
        "prior": 0.3744,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "76644d41d077d0ae",
        "visits": 2,
        "value_sum": -0.97574,
        "metric_sums": {
          "escalation": 2.0,
          "negotiation": 0.29200000000000004,
          "economic_stress": 0.8777999999999999
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.97574,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.48787,
        "metrics": {
          "escalation": 1.0,
          "negotiation": 0.14600000000000002,
          "economic_stress": 0.43889999999999996
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.48787,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal-2/stalemate-return/signal-resolve",
        "state_hash": "ebd507e7498c9d32",
        "depth": 3,
        "branch_id": "signal-resolve",
        "label": "Signal resolve",
        "prior": 0.378,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "b18c2ba2b7a011f2",
        "visits": 373,
        "value_sum": 55.942539999999795,
        "metric_sums": {
          "escalation": 47.744000000000035,
          "negotiation": 366.28600000000296,
          "economic_stress": 116.15220000000089
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 55.942539999999795,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.14997999999999945,
        "metrics": {
          "escalation": 0.12800000000000009,
          "negotiation": 0.982000000000008,
          "economic_stress": 0.3114000000000024
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.14997999999999945,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal/allied-pressure",
        "state_hash": "571d4269a9c16e11",
        "depth": 2,
        "branch_id": "allied-pressure",
        "label": "Allied pressure",
        "prior": 0.20520000000000002,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "add6ab6dd459fd19",
        "visits": 168,
        "value_sum": 17.925899999999967,
        "metric_sums": {
          "escalation": 30.59399999999989,
          "negotiation": 155.4791999999999,
          "economic_stress": 54.93419999999989
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 17.925899999999967,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.10670178571428551,
        "metrics": {
          "escalation": 0.18210714285714222,
          "negotiation": 0.9254714285714281,
          "economic_stress": 0.32698928571428504
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.10670178571428551,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/signal/allied-pressure/confidence-measures",
          "root/signal/allied-pressure/stalemate-return"
        ]
      },
      {
        "node_id": "root/signal/allied-pressure/confidence-measures",
        "state_hash": "79913979c85da0b7",
        "depth": 3,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5012,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "3f7263e2678962c9",
        "visits": 175,
        "value_sum": 3.738000000000004,
        "metric_sums": {
          "escalation": 53.02499999999987,
          "negotiation": 142.3799999999997,
          "economic_stress": 59.22
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 3.738000000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.02136000000000002,
        "metrics": {
          "escalation": 0.30299999999999927,
          "negotiation": 0.8135999999999983,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.02136000000000002,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal/allied-pressure/stalemate-return",
        "state_hash": "9fce5f2ae7ad19c0",
        "depth": 3,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.1496,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "285dbb0546c6c0d8",
        "visits": 142,
        "value_sum": 17.071859999999962,
        "metric_sums": {
          "escalation": 23.063999999999925,
          "negotiation": 133.94199999999972,
          "economic_stress": 46.28379999999993
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 17.071859999999962,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.12022436619718282,
        "metrics": {
          "escalation": 0.1624225352112671,
          "negotiation": 0.9432535211267586,
          "economic_stress": 0.32594225352112627
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.12022436619718282,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/signal/allied-pressure/stalemate-return/signal-resolve",
          "root/signal/allied-pressure/stalemate-return/intercept",
          "root/signal/allied-pressure/stalemate-return/allied-pressure",
          "root/signal/allied-pressure/stalemate-return/crisis-talks"
        ]
      },
      {
        "node_id": "root/signal/allied-pressure/stalemate-return/allied-pressure",
        "state_hash": "888ee3d9508a56d6",
        "depth": 4,
        "branch_id": "allied-pressure",
        "label": "Allied pressure",
        "prior": 0.19720000000000001,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "ca697a36925272ff",
        "visits": 15,
        "value_sum": -2.1762799999999998,
        "metric_sums": {
          "escalation": 8.309,
          "negotiation": 10.252399999999996,
          "economic_stress": 6.428000000000001
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -2.1762799999999998,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.14508533333333332,
        "metrics": {
          "escalation": 0.5539333333333333,
          "negotiation": 0.6834933333333331,
          "economic_stress": 0.4285333333333334
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.14508533333333332,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal/allied-pressure/stalemate-return/crisis-talks",
        "state_hash": "ba7950a999876aa4",
        "depth": 4,
        "branch_id": "crisis-talks",
        "label": "Crisis talks",
        "prior": 0.323,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "09c73d782ff49beb",
        "visits": 477,
        "value_sum": 38.84480000000015,
        "metric_sums": {
          "escalation": 103.13500000000008,
          "negotiation": 430.50280000000174,
          "economic_stress": 163.50680000000105
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 38.84480000000015,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.08143563941299821,
        "metrics": {
          "escalation": 0.21621593291404628,
          "negotiation": 0.9025215932914082,
          "economic_stress": 0.3427815513626856
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.08143563941299821,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal/allied-pressure/stalemate-return/intercept",
        "state_hash": "b96b2c3b683695fa",
        "depth": 4,
        "branch_id": "intercept",
        "label": "Intercept",
        "prior": 0.15639999999999998,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "5b4d0f65f8867675",
        "visits": 2,
        "value_sum": -1.1587399999999999,
        "metric_sums": {
          "escalation": 1.8559999999999999,
          "negotiation": 0.56,
          "economic_stress": 1.9478
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -1.1587399999999999,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.5793699999999999,
        "metrics": {
          "escalation": 0.9279999999999999,
          "negotiation": 0.28,
          "economic_stress": 0.9739
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.5793699999999999,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal/allied-pressure/stalemate-return/signal-resolve",
        "state_hash": "7cf63f71cded384e",
        "depth": 4,
        "branch_id": "signal-resolve",
        "label": "Signal resolve",
        "prior": 0.36,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "325d0316e3ca0f17",
        "visits": 134,
        "value_sum": 19.18611999999998,
        "metric_sums": {
          "escalation": 17.821999999999935,
          "negotiation": 129.44399999999968,
          "economic_stress": 41.72759999999994
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 19.18611999999998,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.14317999999999986,
        "metrics": {
          "escalation": 0.1329999999999995,
          "negotiation": 0.9659999999999975,
          "economic_stress": 0.31139999999999957
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.14317999999999986,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal/crisis-talks",
        "state_hash": "ba7950a999876aa4",
        "depth": 2,
        "branch_id": "crisis-talks",
        "label": "Crisis talks",
        "prior": 0.31220000000000003,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "09c73d782ff49beb",
        "visits": 477,
        "value_sum": 38.84480000000015,
        "metric_sums": {
          "escalation": 103.13500000000008,
          "negotiation": 430.50280000000174,
          "economic_stress": 163.50680000000105
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 38.84480000000015,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.08143563941299821,
        "metrics": {
          "escalation": 0.21621593291404628,
          "negotiation": 0.9025215932914082,
          "economic_stress": 0.3427815513626856
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.08143563941299821,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/signal/crisis-talks/confidence-measures",
          "root/signal/crisis-talks/stalemate-return"
        ]
      },
      {
        "node_id": "root/signal/crisis-talks/confidence-measures",
        "state_hash": "241d0ff8840299af",
        "depth": 3,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5859000000000001,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "db9aff5e2198a36c",
        "visits": 488,
        "value_sum": 13.078399999999911,
        "metric_sums": {
          "escalation": 145.9120000000017,
          "negotiation": 403.28319999999763,
          "economic_stress": 165.13919999999945
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 13.078399999999911,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.026799999999999817,
        "metrics": {
          "escalation": 0.2990000000000035,
          "negotiation": 0.8263999999999951,
          "economic_stress": 0.33839999999999887
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.026799999999999817,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal/crisis-talks/stalemate-return",
        "state_hash": "8c76aca2b882449f",
        "depth": 3,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.07919999999999999,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "3819062e30299cd7",
        "visits": 7182,
        "value_sum": 1024.5554099998749,
        "metric_sums": {
          "escalation": 1003.5899999999998,
          "negotiation": 7022.074000000552,
          "economic_stress": 2268.7693000002546
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 1024.5554099998749,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.14265600250624824,
        "metrics": {
          "escalation": 0.13973684210526313,
          "negotiation": 0.9777323865219371,
          "economic_stress": 0.31589658869399256
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.14265600250624824,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/signal/crisis-talks/stalemate-return/signal-resolve",
          "root/signal/crisis-talks/stalemate-return/intercept",
          "root/signal/crisis-talks/stalemate-return/allied-pressure",
          "root/signal/crisis-talks/stalemate-return/crisis-talks"
        ]
      },
      {
        "node_id": "root/signal/crisis-talks/stalemate-return/allied-pressure",
        "state_hash": "a2eac07db07e149a",
        "depth": 4,
        "branch_id": "allied-pressure",
        "label": "Allied pressure",
        "prior": 0.19720000000000001,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "c7b5ea67e936da29",
        "visits": 119,
        "value_sum": -0.18480000000000102,
        "metric_sums": {
          "escalation": 39.86099999999998,
          "negotiation": 94.25359999999984,
          "economic_stress": 41.7216
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -0.18480000000000102,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.0015529411764705968,
        "metrics": {
          "escalation": 0.3349663865546217,
          "negotiation": 0.792047058823528,
          "economic_stress": 0.35060168067226893
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.0015529411764705968,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal/crisis-talks/stalemate-return/crisis-talks",
        "state_hash": "ba7950a999876aa4",
        "depth": 4,
        "branch_id": "crisis-talks",
        "label": "Crisis talks",
        "prior": 0.3806,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "09c73d782ff49beb",
        "visits": 477,
        "value_sum": 38.84480000000015,
        "metric_sums": {
          "escalation": 103.13500000000008,
          "negotiation": 430.50280000000174,
          "economic_stress": 163.50680000000105
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 38.84480000000015,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.08143563941299821,
        "metrics": {
          "escalation": 0.21621593291404628,
          "negotiation": 0.9025215932914082,
          "economic_stress": 0.3427815513626856
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.08143563941299821,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal/crisis-talks/stalemate-return/intercept",
        "state_hash": "c43eee67cc1625c4",
        "depth": 4,
        "branch_id": "intercept",
        "label": "Intercept",
        "prior": 0.14359999999999998,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "b2c541e7bc4a0f8c",
        "visits": 45,
        "value_sum": -6.706610000000009,
        "metric_sums": {
          "escalation": 25.180999999999994,
          "negotiation": 32.1848,
          "economic_stress": 20.96550000000002
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -6.706610000000009,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.149035777777778,
        "metrics": {
          "escalation": 0.5595777777777776,
          "negotiation": 0.7152177777777778,
          "economic_stress": 0.4659000000000004
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.149035777777778,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal/crisis-talks/stalemate-return/signal-resolve",
        "state_hash": "45b464eeb9d1da33",
        "depth": 4,
        "branch_id": "signal-resolve",
        "label": "Signal resolve",
        "prior": 0.38880000000000003,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "27f86318104c9ada",
        "visits": 6898,
        "value_sum": 1062.705879999896,
        "metric_sums": {
          "escalation": 862.25,
          "negotiation": 6840.0568000005005,
          "economic_stress": 2148.037200000247
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 1062.705879999896,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.15405999999998493,
        "metrics": {
          "escalation": 0.125,
          "negotiation": 0.9916000000000725,
          "economic_stress": 0.3114000000000358
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.15405999999998493,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal/intercept",
        "state_hash": "e469bbfc7897b81f",
        "depth": 2,
        "branch_id": "intercept",
        "label": "Intercept",
        "prior": 0.17720000000000002,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "dedad1f3c73a2139",
        "visits": 29,
        "value_sum": -2.918239999999999,
        "metric_sums": {
          "escalation": 13.295000000000009,
          "negotiation": 18.9548,
          "economic_stress": 10.9556
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -2.918239999999999,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.10062896551724135,
        "metrics": {
          "escalation": 0.45844827586206927,
          "negotiation": 0.6536137931034482,
          "economic_stress": 0.3777793103448276
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.10062896551724135,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/signal/intercept/force-projection",
          "root/signal/intercept/emergency-backchannel"
        ]
      },
      {
        "node_id": "root/signal/intercept/emergency-backchannel",
        "state_hash": "b52b19b7920612af",
        "depth": 3,
        "branch_id": "emergency-backchannel",
        "label": "Emergency backchannel",
        "prior": 0.2696,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "d2600cc9360c87db",
        "visits": 529,
        "value_sum": 53.520190000000305,
        "metric_sums": {
          "escalation": 103.67300000000064,
          "negotiation": 492.606399999996,
          "economic_stress": 175.97509999999997
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 53.520190000000305,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.10117238185255256,
        "metrics": {
          "escalation": 0.19597920604915056,
          "negotiation": 0.9312030245746615,
          "economic_stress": 0.33265614366729673
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.10117238185255256,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": [
          "root/signal/intercept/emergency-backchannel/confidence-measures",
          "root/signal/intercept/emergency-backchannel/stalemate-return"
        ]
      },
      {
        "node_id": "root/signal/intercept/emergency-backchannel/confidence-measures",
        "state_hash": "79913979c85da0b7",
        "depth": 4,
        "branch_id": "confidence-measures",
        "label": "Confidence measures",
        "prior": 0.5509999999999999,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "3f7263e2678962c9",
        "visits": 175,
        "value_sum": 3.738000000000004,
        "metric_sums": {
          "escalation": 53.02499999999987,
          "negotiation": 142.3799999999997,
          "economic_stress": 59.22
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 3.738000000000004,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.02136000000000002,
        "metrics": {
          "escalation": 0.30299999999999927,
          "negotiation": 0.8135999999999983,
          "economic_stress": 0.3384
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.02136000000000002,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal/intercept/emergency-backchannel/stalemate-return",
        "state_hash": "7b5c068c2f250473",
        "depth": 4,
        "branch_id": "stalemate-return",
        "label": "Stalemate return",
        "prior": 0.09359999999999999,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "efc038bffb41d338",
        "visits": 439,
        "value_sum": 55.59064000000027,
        "metric_sums": {
          "escalation": 68.75299999999979,
          "negotiation": 419.0943999999977,
          "economic_stress": 142.12160000000074
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 55.59064000000027,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.12663015945330358,
        "metrics": {
          "escalation": 0.15661275626423643,
          "negotiation": 0.9546569476081952,
          "economic_stress": 0.3237394077448764
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.12663015945330358,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal/intercept/force-projection",
        "state_hash": "270452afe26f54f7",
        "depth": 3,
        "branch_id": "force-projection",
        "label": "Force projection",
        "prior": 0.3744,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "f0fc51ed2c4631d8",
        "visits": 4,
        "value_sum": -1.98604,
        "metric_sums": {
          "escalation": 4.0,
          "negotiation": 0.4688,
          "economic_stress": 1.7555999999999998
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": -1.98604,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.49651,
        "metrics": {
          "escalation": 1.0,
          "negotiation": 0.1172,
          "economic_stress": 0.43889999999999996
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.49651,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      },
      {
        "node_id": "root/signal/signal-resolve",
        "state_hash": "7e0afc1b67a51e90",
        "depth": 2,
        "branch_id": "signal-resolve",
        "label": "Signal resolve",
        "prior": 0.36460000000000004,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "dependency_hash": "5f618fed1431200d",
        "visits": 748,
        "value_sum": 103.02951999999857,
        "metric_sums": {
          "escalation": 102.47600000000033,
          "negotiation": 712.993600000004,
          "economic_stress": 232.9271999999984
        },
        "actor_metric_sums": {},
        "aggregate_score_breakdown_sums": {
          "system": 103.02951999999857,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.1377399999999981,
        "metrics": {
          "escalation": 0.13700000000000043,
          "negotiation": 0.9532000000000054,
          "economic_stress": 0.31139999999999785
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.1377399999999981,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "child_ids": []
      }
    ],
    "branches": [
      {
        "branch_id": "open-negotiation",
        "label": "Open negotiation",
        "metrics": {
          "escalation": 0.14551285615010354,
          "negotiation": 0.9724123974983336,
          "economic_stress": 0.31564676858933405
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.1388245462126309,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.1388245462126309,
        "visits": 7195,
        "prior": 0.22340000000000002,
        "dependencies": {
          "fields": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window",
            "tension_index"
          ]
        },
        "path": [
          {
            "label": "Open negotiation",
            "phase": "negotiation-deescalation"
          },
          {
            "label": "Confidence measures",
            "phase": "settlement-stalemate"
          }
        ],
        "terminal_phase": "settlement-stalemate",
        "terminal_metrics": {
          "escalation": 0.29900000000000004,
          "negotiation": 0.8264,
          "economic_stress": 0.3384
        },
        "terminal_actor_metrics": {},
        "terminal_aggregate_score_breakdown": {
          "system": 0.02679999999999999,
          "actors": 0.0,
          "destabilization_penalty": -0.0
        },
        "key_drivers": [
          "diplomatic_channel",
          "leader_style",
          "mediation_window"
        ],
        "confidence_signal": 0.72,
        "raw_confidence_signal": 0.72,
        "confidence_bucket": "fallback",
        "confidence_bucket_label": "Fallback baseline",
        "calibrated_confidence": 0.875,
        "calibration_case_count": 0,
        "calibration_observed_accuracy": 0.0,
        "calibration_fallback_used": true
      },
      {
        "branch_id": "signal",
        "label": "Signal resolve (managed signal)",
        "metrics": {
          "escalation": 0.15511306901615315,
          "negotiation": 0.9473007342143778,
          "economic_stress": 0.3181261380323003
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.12670715124816462,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.12670715124816462,
        "visits": 1362,
        "prior": 0.15172045266353848,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "path": [
          {
            "label": "Signal resolve (managed signal)",
            "phase": "signaling"
          },
          {
            "label": "Signal resolve",
            "phase": "settlement-stalemate"
          }
        ],
        "terminal_phase": "settlement-stalemate",
        "terminal_metrics": {
          "escalation": 0.137,
          "negotiation": 0.9532,
          "economic_stress": 0.3114
        },
        "terminal_actor_metrics": {},
        "terminal_aggregate_score_breakdown": {
          "system": 0.13773999999999997,
          "actors": 0.0,
          "destabilization_penalty": -0.0
        },
        "key_drivers": [
          "diplomatic_channel",
          "leader_style",
          "mediation_window"
        ],
        "confidence_signal": 0.136,
        "raw_confidence_signal": 0.136,
        "confidence_bucket": "low",
        "confidence_bucket_label": "Low",
        "calibrated_confidence": 0.875,
        "calibration_case_count": 6,
        "calibration_observed_accuracy": 1.0,
        "calibration_fallback_used": false
      },
      {
        "branch_id": "signal-2",
        "label": "Signal resolve (backchannel opening)",
        "metrics": {
          "escalation": 0.17641260162601652,
          "negotiation": 0.9385821138211484,
          "economic_stress": 0.31986747967479695
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.11504934959349547,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.11504934959349547,
        "visits": 492,
        "prior": 0.1166795473364615,
        "dependencies": {
          "fields": [
            "leader_style",
            "diplomatic_channel",
            "mediation_window",
            "tension_index"
          ]
        },
        "path": [
          {
            "label": "Signal resolve (backchannel opening)",
            "phase": "negotiation-deescalation"
          },
          {
            "label": "Confidence measures",
            "phase": "settlement-stalemate"
          }
        ],
        "terminal_phase": "settlement-stalemate",
        "terminal_metrics": {
          "escalation": 0.30200000000000005,
          "negotiation": 0.8168,
          "economic_stress": 0.3384
        },
        "terminal_actor_metrics": {},
        "terminal_aggregate_score_breakdown": {
          "system": 0.022719999999999976,
          "actors": 0.0,
          "destabilization_penalty": -0.0
        },
        "key_drivers": [
          "diplomatic_channel",
          "leader_style",
          "mediation_window"
        ],
        "confidence_signal": 0.049,
        "raw_confidence_signal": 0.049,
        "confidence_bucket": "low",
        "confidence_bucket_label": "Low",
        "calibrated_confidence": 0.875,
        "calibration_case_count": 6,
        "calibration_observed_accuracy": 1.0,
        "calibration_fallback_used": false
      },
      {
        "branch_id": "limited-response-2",
        "label": "Limited response (escalatory response)",
        "metrics": {
          "escalation": 0.17908441558441615,
          "negotiation": 0.9316476190476137,
          "economic_stress": 0.32452878787878897
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.11050188311688368,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.11050188311688368,
        "visits": 462,
        "prior": 0.12656,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "path": [
          {
            "label": "Limited response (escalatory response)",
            "phase": "escalation"
          },
          {
            "label": "Force projection",
            "phase": "settlement-stalemate"
          }
        ],
        "terminal_phase": "settlement-stalemate",
        "terminal_metrics": {
          "escalation": 1.0,
          "negotiation": 0.07400000000000001,
          "economic_stress": 0.43889999999999996
        },
        "terminal_actor_metrics": {},
        "terminal_aggregate_score_breakdown": {
          "system": -0.50947,
          "actors": 0.0,
          "destabilization_penalty": -0.0
        },
        "key_drivers": [
          "geographic_flashpoint",
          "leader_style",
          "mediation_window"
        ],
        "confidence_signal": 0.046,
        "raw_confidence_signal": 0.046,
        "confidence_bucket": "low",
        "confidence_bucket_label": "Low",
        "calibrated_confidence": 0.875,
        "calibration_case_count": 6,
        "calibration_observed_accuracy": 1.0,
        "calibration_fallback_used": false
      },
      {
        "branch_id": "alliance-consultation-2",
        "label": "Alliance consultation (coordinated signaling)",
        "metrics": {
          "escalation": 0.21531756756756745,
          "negotiation": 0.8710756756756779,
          "economic_stress": 0.3277885135135131
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.07685912162162159,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.07685912162162159,
        "visits": 148,
        "prior": 0.08457886585061204,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "path": [
          {
            "label": "Alliance consultation (coordinated signaling)",
            "phase": "signaling"
          },
          {
            "label": "Signal resolve",
            "phase": "settlement-stalemate"
          }
        ],
        "terminal_phase": "settlement-stalemate",
        "terminal_metrics": {
          "escalation": 0.148,
          "negotiation": 0.918,
          "economic_stress": 0.3114
        },
        "terminal_actor_metrics": {},
        "terminal_aggregate_score_breakdown": {
          "system": 0.12277999999999997,
          "actors": 0.0,
          "destabilization_penalty": -0.0
        },
        "key_drivers": [
          "alliance_pressure",
          "diplomatic_channel",
          "mediation_window"
        ],
        "confidence_signal": 0.015,
        "raw_confidence_signal": 0.015,
        "confidence_bucket": "low",
        "confidence_bucket_label": "Low",
        "calibrated_confidence": 0.875,
        "calibration_case_count": 6,
        "calibration_observed_accuracy": 1.0,
        "calibration_fallback_used": false
      },
      {
        "branch_id": "limited-response",
        "label": "Limited response (contained response)",
        "metrics": {
          "escalation": 0.2649459459459447,
          "negotiation": 0.8416810810810845,
          "economic_stress": 0.34076486486486474
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.044296486486486486,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.044296486486486486,
        "visits": 222,
        "prior": 0.18984,
        "dependencies": {
          "fields": [
            "geographic_flashpoint",
            "leader_style",
            "military_posture",
            "mediation_window",
            "tension_index"
          ]
        },
        "path": [
          {
            "label": "Limited response (contained response)",
            "phase": "limited-response"
          },
          {
            "label": "Contain response",
            "phase": "settlement-stalemate"
          }
        ],
        "terminal_phase": "settlement-stalemate",
        "terminal_metrics": {
          "escalation": 0.525,
          "negotiation": 0.33999999999999997,
          "economic_stress": 0.3639
        },
        "terminal_actor_metrics": {},
        "terminal_aggregate_score_breakdown": {
          "system": -0.21717000000000003,
          "actors": 0.0,
          "destabilization_penalty": -0.0
        },
        "key_drivers": [
          "geographic_flashpoint",
          "leader_style",
          "mediation_window"
        ],
        "confidence_signal": 0.022,
        "raw_confidence_signal": 0.022,
        "confidence_bucket": "low",
        "confidence_bucket_label": "Low",
        "calibrated_confidence": 0.875,
        "calibration_case_count": 6,
        "calibration_observed_accuracy": 1.0,
        "calibration_fallback_used": false
      },
      {
        "branch_id": "alliance-consultation",
        "label": "Alliance consultation (coordinated restraint)",
        "metrics": {
          "escalation": 0.2871566265060239,
          "negotiation": 0.8305879518072294,
          "economic_stress": 0.33716506024096377
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": 0.03316421686746987,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": 0.03316421686746987,
        "visits": 83,
        "prior": 0.0762614039470397,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "path": [
          {
            "label": "Alliance consultation (coordinated restraint)",
            "phase": "negotiation-deescalation"
          },
          {
            "label": "Confidence measures",
            "phase": "settlement-stalemate"
          }
        ],
        "terminal_phase": "settlement-stalemate",
        "terminal_metrics": {
          "escalation": 0.30200000000000005,
          "negotiation": 0.8168,
          "economic_stress": 0.3384
        },
        "terminal_actor_metrics": {},
        "terminal_aggregate_score_breakdown": {
          "system": 0.022719999999999976,
          "actors": 0.0,
          "destabilization_penalty": -0.0
        },
        "key_drivers": [
          "alliance_pressure",
          "diplomatic_channel",
          "mediation_window"
        ],
        "confidence_signal": 0.008,
        "raw_confidence_signal": 0.008,
        "confidence_bucket": "low",
        "confidence_bucket_label": "Low",
        "calibrated_confidence": 0.875,
        "calibration_case_count": 6,
        "calibration_observed_accuracy": 1.0,
        "calibration_fallback_used": false
      },
      {
        "branch_id": "alliance-consultation-3",
        "label": "Alliance consultation (harder deterrence)",
        "metrics": {
          "escalation": 0.35991666666666683,
          "negotiation": 0.7311000000000001,
          "economic_stress": 0.3514138888888889
        },
        "actor_metrics": {},
        "aggregate_score_breakdown": {
          "system": -0.030060833333333346,
          "actors": 0.0,
          "destabilization_penalty": 0.0
        },
        "score": -0.030060833333333346,
        "visits": 36,
        "prior": 0.05535973020234822,
        "dependencies": {
          "fields": [
            "alliance_pressure",
            "diplomatic_channel",
            "mediation_window",
            "military_posture",
            "tension_index"
          ]
        },
        "path": [
          {
            "label": "Alliance consultation (harder deterrence)",
            "phase": "limited-response"
          },
          {
            "label": "Contain response",
            "phase": "settlement-stalemate"
          }
        ],
        "terminal_phase": "settlement-stalemate",
        "terminal_metrics": {
          "escalation": 0.525,
          "negotiation": 0.33999999999999997,
          "economic_stress": 0.3639
        },
        "terminal_actor_metrics": {},
        "terminal_aggregate_score_breakdown": {
          "system": -0.21717000000000003,
          "actors": 0.0,
          "destabilization_penalty": -0.0
        },
        "key_drivers": [
          "alliance_pressure",
          "diplomatic_channel",
          "mediation_window"
        ],
        "confidence_signal": 0.004,
        "raw_confidence_signal": 0.004,
        "confidence_bucket": "low",
        "confidence_bucket_label": "Low",
        "calibrated_confidence": 0.875,
        "calibration_case_count": 6,
        "calibration_observed_accuracy": 1.0,
        "calibration_fallback_used": false
      }
    ],
    "confidence_calibration": {
      "domain_pack": "interstate-crisis",
      "profile": {
        "domain_pack": "interstate-crisis",
        "case_count": 6,
        "baseline_accuracy": 0.875,
        "buckets": [
          {
            "bucket_id": "low",
            "label": "Low",
            "lower_bound": 0.0,
            "upper_bound": 0.34,
            "case_count": 6,
            "observed_accuracy": 1.0,
            "calibrated_confidence": 0.875,
            "fallback_used": false
          },
          {
            "bucket_id": "medium",
            "label": "Medium",
            "lower_bound": 0.34,
            "upper_bound": 0.67,
            "case_count": 0,
            "observed_accuracy": 0.0,
            "calibrated_confidence": 0.875,
            "fallback_used": true
          },
          {
            "bucket_id": "high",
            "label": "High",
            "lower_bound": 0.67,
            "upper_bound": 1.0,
            "case_count": 0,
            "observed_accuracy": 0.0,
            "calibrated_confidence": 0.875,
            "fallback_used": true
          }
        ]
      }
    },
    "actor_utility_summary": [],
    "aggregation_lens": {
      "name": "balanced-system",
      "metric_weights": {
        "escalation": -0.4,
        "negotiation": 0.3,
        "economic_stress": -0.3
      },
      "veto_thresholds": {},
      "risk_tolerance": 0.5,
      "asymmetry_penalties": {},
      "actor_metric_weights": {
        "domestic_sensitivity": 0.25,
        "economic_pain_tolerance": -0.2,
        "negotiation_openness": 0.2,
        "reputational_sensitivity": 0.15,
        "alliance_dependence": 0.1,
        "coercive_bias": -0.1
      },
      "actor_weights": {},
      "aggregation_mode": "balanced-system",
      "focal_actor_id": null,
      "focal_weight": 1.0,
      "destabilization_penalty": 0.1
    },
    "recommended_run_lens": {
      "name": "balanced-system",
      "metric_weights": {
        "escalation": -0.4,
        "negotiation": 0.3,
        "economic_stress": -0.3
      },
      "veto_thresholds": {},
      "risk_tolerance": 0.5,
      "asymmetry_penalties": {},
      "actor_metric_weights": {
        "domestic_sensitivity": 0.25,
        "economic_pain_tolerance": -0.2,
        "negotiation_openness": 0.2,
        "reputational_sensitivity": 0.15,
        "alliance_dependence": 0.1,
        "coercive_bias": -0.1
      },
      "actor_weights": {},
      "aggregation_mode": "balanced-system",
      "focal_actor_id": null,
      "focal_weight": 1.0,
      "destabilization_penalty": 0.1
    }
  },
  "turn": {
    "run_id": "us-iran-public",
    "revision_id": "r1",
    "stage": "report",
    "headline": "Review simulation report",
    "user_message": "Simulation is complete. Review the top branches and decide whether to update the revision.",
    "recommended_command": "scenario-lab begin-revision-update",
    "recommended_runtime_action": "begin-revision-update",
    "available_sections": [
      "intake",
      "evidence",
      "assumptions",
      "belief-state",
      "simulation"
    ],
    "actions": [
      {
        "command": "scenario-lab begin-revision-update",
        "runtime_action": "begin-revision-update",
        "label": "Start revision update",
        "description": "Create a child revision from the current approved revision and continue the conversation loop.",
        "required_options": []
      }
    ],
    "context": {
      "revision_id": "r1",
      "status": "simulated",
      "parent_revision_id": null,
      "evidence_item_count": 0,
      "assumption_count": 1,
      "top_branches": [
        {
          "branch_id": "open-negotiation",
          "label": "Open negotiation",
          "score": 0.1388245462126309,
          "confidence_signal": 0.72,
          "confidence_bucket": "fallback",
          "calibrated_confidence": 0.875,
          "calibration_case_count": 0,
          "calibration_fallback_used": true
        },
        {
          "branch_id": "signal",
          "label": "Signal resolve (managed signal)",
          "score": 0.12670715124816462,
          "confidence_signal": 0.136,
          "confidence_bucket": "low",
          "calibrated_confidence": 0.875,
          "calibration_case_count": 6,
          "calibration_fallback_used": false
        },
        {
          "branch_id": "signal-2",
          "label": "Signal resolve (backchannel opening)",
          "score": 0.11504934959349547,
          "confidence_signal": 0.049,
          "confidence_bucket": "low",
          "calibrated_confidence": 0.875,
          "calibration_case_count": 6,
          "calibration_fallback_used": false
        }
      ],
      "scenario_families": [
        {
          "family_id": "open-negotiation-settlement-stalemate-diplomatic-channel-leader-style",
          "root_route": "Open negotiation",
          "terminal_phase": "settlement-stalemate",
          "branch_count": 1,
          "best_score": 0.1388245462126309,
          "representative_label": "Open negotiation",
          "key_drivers": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window"
          ],
          "confidence_signal": 0.72,
          "confidence_bucket": "fallback",
          "calibrated_confidence": 0.875,
          "calibration_case_count": 0,
          "calibration_fallback_used": true
        },
        {
          "family_id": "signal-resolve-settlement-stalemate-diplomatic-channel-leader-style",
          "root_route": "Signal resolve",
          "terminal_phase": "settlement-stalemate",
          "branch_count": 2,
          "best_score": 0.12670715124816462,
          "representative_label": "Signal resolve (managed signal)",
          "key_drivers": [
            "diplomatic_channel",
            "leader_style",
            "mediation_window"
          ],
          "confidence_signal": 0.136,
          "confidence_bucket": "low",
          "calibrated_confidence": 0.875,
          "calibration_case_count": 6,
          "calibration_fallback_used": false
        },
        {
          "family_id": "limited-response-settlement-stalemate-geographic-flashpoint-leader-style",
          "root_route": "Limited response",
          "terminal_phase": "settlement-stalemate",
          "branch_count": 2,
          "best_score": 0.11050188311688368,
          "representative_label": "Limited response (escalatory response)",
          "key_drivers": [
            "geographic_flashpoint",
            "leader_style",
            "mediation_window"
          ],
          "confidence_signal": 0.046,
          "confidence_bucket": "low",
          "calibrated_confidence": 0.875,
          "calibration_case_count": 6,
          "calibration_fallback_used": false
        }
      ],
      "available_sections": [
        "intake",
        "evidence",
        "assumptions",
        "belief-state",
        "simulation"
      ],
      "revision_summary": {
        "revision_id": "r1",
        "status": "simulated",
        "parent_revision_id": null,
        "evidence_item_count": 0,
        "assumption_count": 1,
        "top_branches": [
          {
            "branch_id": "open-negotiation",
            "label": "Open negotiation",
            "score": 0.1388245462126309,
            "confidence_signal": 0.72,
            "confidence_bucket": "fallback",
            "calibrated_confidence": 0.875,
            "calibration_case_count": 0,
            "calibration_fallback_used": true
          },
          {
            "branch_id": "signal",
            "label": "Signal resolve (managed signal)",
            "score": 0.12670715124816462,
            "confidence_signal": 0.136,
            "confidence_bucket": "low",
            "calibrated_confidence": 0.875,
            "calibration_case_count": 6,
            "calibration_fallback_used": false
          },
          {
            "branch_id": "signal-2",
            "label": "Signal resolve (backchannel opening)",
            "score": 0.11504934959349547,
            "confidence_signal": 0.049,
            "confidence_bucket": "low",
            "calibrated_confidence": 0.875,
            "calibration_case_count": 6,
            "calibration_fallback_used": false
          }
        ],
        "scenario_families": [
          {
            "family_id": "open-negotiation-settlement-stalemate-diplomatic-channel-leader-style",
            "root_route": "Open negotiation",
            "terminal_phase": "settlement-stalemate",
            "branch_count": 1,
            "best_score": 0.1388245462126309,
            "representative_label": "Open negotiation",
            "key_drivers": [
              "diplomatic_channel",
              "leader_style",
              "mediation_window"
            ],
            "confidence_signal": 0.72,
            "confidence_bucket": "fallback",
            "calibrated_confidence": 0.875,
            "calibration_case_count": 0,
            "calibration_fallback_used": true
          },
          {
            "family_id": "signal-resolve-settlement-stalemate-diplomatic-channel-leader-style",
            "root_route": "Signal resolve",
            "terminal_phase": "settlement-stalemate",
            "branch_count": 2,
            "best_score": 0.12670715124816462,
            "representative_label": "Signal resolve (managed signal)",
            "key_drivers": [
              "diplomatic_channel",
              "leader_style",
              "mediation_window"
            ],
            "confidence_signal": 0.136,
            "confidence_bucket": "low",
            "calibrated_confidence": 0.875,
            "calibration_case_count": 6,
            "calibration_fallback_used": false
          },
          {
            "family_id": "limited-response-settlement-stalemate-geographic-flashpoint-leader-style",
            "root_route": "Limited response",
            "terminal_phase": "settlement-stalemate",
            "branch_count": 2,
            "best_score": 0.11050188311688368,
            "representative_label": "Limited response (escalatory response)",
            "key_drivers": [
              "geographic_flashpoint",
              "leader_style",
              "mediation_window"
            ],
            "confidence_signal": 0.046,
            "confidence_bucket": "low",
            "calibrated_confidence": 0.875,
            "calibration_case_count": 6,
            "calibration_fallback_used": false
          }
        ],
        "available_sections": [
          "intake",
          "evidence",
          "assumptions",
          "belief-state",
          "simulation"
        ]
      }
    }
  }
}
```

Verified defaults from this run:

- Search mode: `mcts`
- Iterations: `10000`
- Top branch: `Open negotiation`

### 6. Generate the report

```bash
PYTHONPATH=packages/core/src packages/core/.venv/bin/python -m forecasting_harness.cli generate-report \
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
