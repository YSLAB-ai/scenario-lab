from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.cli import app


def test_synthesize_domain_command_rejects_input_file() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("blueprint.json").write_text(
            json.dumps(
                {
                    "slug": "product-recall",
                    "class_name": "ProductRecallPack",
                    "description": "Product recall response",
                    "focus_entity_rule": {"min_count": 2},
                    "canonical_stages": ["trigger", "response", "resolution"],
                }
            ),
            encoding="utf-8",
        )
        result = runner.invoke(app, ["synthesize-domain", "--workspace-root", ".", "--input", "blueprint.json"])

    assert result.exit_code != 0


def test_synthesize_domain_command_accepts_direct_blueprint_flags(tmp_path: Path) -> None:
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

    result = CliRunner().invoke(
        app,
        [
            "synthesize-domain",
            "--workspace-root",
            str(tmp_path),
            "--slug",
            "product-recall",
            "--class-name",
            "ProductRecallPack",
            "--description",
            "Product recall response",
            "--focus-entity-rule-min-count",
            "2",
            "--canonical-stage",
            "trigger",
            "--canonical-stage",
            "response",
            "--canonical-stage",
            "resolution",
            "--field-schema",
            "severity=float",
            "--field-schema",
            "recall_readiness=float",
            "--actor-category",
            "company",
            "--actor-category",
            "regulator",
            "--actor-category",
            "customers",
            "--evidence-category",
            "safety reports",
            "--evidence-category-term-json",
            '{"safety reports": ["injuries"]}',
            "--semantic-alias-group-json",
            '["recall", "withdrawal"]',
            "--starter-source-json",
            '{"kind": "report", "description": "Incident reports"}',
            "--field-inference-rule-json",
            '{"severity": {"field_type": "float", "base": 0.2, "term_deltas": [{"terms": ["injuries"], "delta": 0.35}]}}',
            "--field-inference-rule-json",
            '{"recall_readiness": {"field_type": "float", "base": 0.3, "term_deltas": [{"terms": ["contingency plan"], "delta": 0.2}]}}',
            "--action-template-json",
            '{"stage": "trigger", "action_id": "announce-recall", "label": "Announce recall", "base_prior": 0.12, "field_weights": {"severity": 0.3, "recall_readiness": 0.2}, "next_stage": "response", "field_updates": {"recall_readiness": 0.1}, "outcomes": [{"outcome_id": "targeted-withdrawal", "next_stage": "response", "field_updates": {"recall_readiness": 0.1}}, {"outcome_id": "full-stop-sale", "next_stage": "response", "field_minimums": {"severity": 0.5}, "field_updates": {"recall_readiness": 0.2}}]}',
            "--scoring-weight-json",
            '{"escalation": {"severity": 0.5}, "negotiation": {"recall_readiness": 0.4}, "economic_stress": {"severity": 0.3}}',
            "--objective-profile-rule-json",
            '{"profile_name": "domestic-politics-first", "field_minimums": {"severity": 0.5}}',
            "--replay-seed-case-json",
            json.dumps(
                {
                    "run_id": "product-recall-replay",
                    "domain_pack": "product-recall",
                    "intake": {
                        "event_framing": "Assess recall",
                        "focus_entities": ["Acme"],
                        "current_development": "A recall begins",
                        "current_stage": "trigger",
                        "time_horizon": "30d",
                    },
                    "assumptions": {
                        "summary": ["The company will prioritize safety"],
                        "suggested_actors": ["Regulator"],
                    },
                }
            ),
            "--no-branch",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["domain_slug"] == "product-recall"
    assert (tmp_path / "knowledge" / "domains" / "product-recall.json").exists()
    generated = (domain_dir / "product_recall.py").read_text(encoding="utf-8")
    assert "def infer_pack_fields" in generated
    assert "def sample_transition" in generated
    assert "def recommend_objective_profile" in generated
