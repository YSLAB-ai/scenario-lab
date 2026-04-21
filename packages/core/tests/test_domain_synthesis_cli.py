from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.cli import app


def test_synthesize_domain_command(tmp_path: Path) -> None:
    domain_dir = tmp_path / "packages" / "core" / "src" / "forecasting_harness" / "domain"
    domain_dir.mkdir(parents=True)
    (domain_dir / "registry.py").write_text(
        "\n".join(
            [
                "from forecasting_harness.domain.base import DomainPack",
                "from forecasting_harness.domain.generic_event import GenericEventPack",
                "",
                "def build_default_registry():",
                "    registry = {}",
                "    registry['generic-event'] = GenericEventPack",
                "    return registry",
                "",
            ]
        ),
        encoding="utf-8",
    )
    blueprint = {
        "slug": "product-recall",
        "class_name": "ProductRecallPack",
        "description": "Product recall response",
        "focus_entity_rule": {"min_count": 2},
        "canonical_stages": ["trigger", "response", "resolution"],
        "field_schema": {"severity": "float", "recall_readiness": "float"},
        "actor_categories": ["company", "regulator", "customers"],
        "evidence_categories": ["safety reports"],
        "evidence_category_terms": {"safety reports": ["injuries"]},
        "semantic_alias_groups": [["recall", "withdrawal"]],
        "starter_sources": [{"kind": "report", "description": "Incident reports"}],
        "field_inference_rules": {
            "severity": {"field_type": "float", "base": 0.2, "term_deltas": [{"terms": ["injuries"], "delta": 0.35}]},
            "recall_readiness": {"field_type": "float", "base": 0.3, "term_deltas": [{"terms": ["contingency plan"], "delta": 0.2}]},
        },
        "action_templates": [
            {
                "stage": "trigger",
                "action_id": "announce-recall",
                "label": "Announce recall",
                "base_prior": 0.12,
                "field_weights": {"severity": 0.3, "recall_readiness": 0.2},
                "next_stage": "response",
                "field_updates": {"recall_readiness": 0.1},
            }
        ],
        "scoring_weights": {
            "escalation": {"severity": 0.5},
            "negotiation": {"recall_readiness": 0.4},
            "economic_stress": {"severity": 0.3},
        },
    }
    blueprint_path = tmp_path / "blueprint.json"
    blueprint_path.write_text(json.dumps(blueprint), encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "synthesize-domain",
            "--workspace-root",
            str(tmp_path),
            "--input",
            str(blueprint_path),
            "--no-branch",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["domain_slug"] == "product-recall"
    assert (tmp_path / "knowledge" / "domains" / "product-recall.json").exists()
    assert (domain_dir / "product_recall.py").exists()

