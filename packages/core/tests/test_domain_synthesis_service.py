from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from forecasting_harness.evolution.models import (
    ActionTemplate,
    DomainBlueprint,
    FieldInferenceRule,
    FieldRuleTermDelta,
    FocusEntityRule,
)
from forecasting_harness.evolution.service import DomainEvolutionService
from forecasting_harness.evolution.storage import EvolutionStorage


def _blueprint() -> DomainBlueprint:
    return DomainBlueprint(
        slug="product-recall",
        class_name="ProductRecallPack",
        description="Product recall response",
        focus_entity_rule=FocusEntityRule(min_count=2),
        canonical_stages=["trigger", "response", "resolution"],
        suggested_related_actors=["Regulator", "Major Retailers"],
        follow_up_questions=["How severe is the safety issue?"],
        field_schema={"severity": "float", "recall_readiness": "float"},
        actor_categories=["company", "regulator", "customers"],
        evidence_categories=["safety reports", "regulator action"],
        evidence_category_terms={"safety reports": ["injuries", "defect report"]},
        semantic_alias_groups=[["recall", "withdrawal"]],
        starter_sources=[{"kind": "report", "description": "Incident reports"}],
        field_inference_rules={
            "severity": FieldInferenceRule(
                field_type="float",
                base=0.2,
                term_deltas=[FieldRuleTermDelta(terms=["injuries"], delta=0.35)],
            ),
            "recall_readiness": FieldInferenceRule(
                field_type="float",
                base=0.3,
                term_deltas=[FieldRuleTermDelta(terms=["contingency plan"], delta=0.2)],
            ),
        },
        action_templates=[
            ActionTemplate(
                stage="trigger",
                action_id="announce-recall",
                label="Announce recall",
                base_prior=0.12,
                field_weights={"severity": 0.3, "recall_readiness": 0.2},
                next_stage="response",
                field_updates={"recall_readiness": 0.1},
            )
        ],
        scoring_weights={
            "escalation": {"severity": 0.5},
            "negotiation": {"recall_readiness": 0.4},
            "economic_stress": {"severity": 0.3},
        },
    )


def test_synthesize_domain_generates_files(tmp_path: Path) -> None:
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
    manifest_root = tmp_path / "knowledge" / "domains"
    manifest_root.mkdir(parents=True)
    storage = EvolutionStorage(tmp_path / "knowledge" / "evolution")
    service = DomainEvolutionService(evolution_storage=storage, manifest_root=manifest_root)

    summary = service.synthesize_domain(_blueprint(), create_branch=False)

    assert summary["domain_slug"] == "product-recall"
    manifest_path = tmp_path / "knowledge" / "domains" / "product-recall.json"
    replay_path = tmp_path / "knowledge" / "replays" / "product-recall.json"
    pack_path = domain_dir / "product_recall.py"
    test_path = tmp_path / "packages" / "core" / "tests" / "test_product_recall_pack.py"

    assert manifest_path.exists()
    assert replay_path.exists()
    assert pack_path.exists()
    assert test_path.exists()

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_payload["slug"] == "product-recall"
    assert "recall" in manifest_payload["semantic_alias_groups"][0]
    assert "ProductRecallPack" in pack_path.read_text(encoding="utf-8")
    assert "product-recall" in (domain_dir / "registry.py").read_text(encoding="utf-8")

    spec = importlib.util.spec_from_file_location("generated_product_recall", pack_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pack = module.ProductRecallPack()
    assert pack.slug() == "product-recall"

