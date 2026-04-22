from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

from forecasting_harness.evolution.models import (
    ActionTemplate,
    ActionTransitionOutcome,
    DomainBlueprint,
    FieldInferenceRule,
    FieldRuleTermDelta,
    FocusEntityRule,
    ObjectiveRecommendationRule,
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
                outcomes=[
                    ActionTransitionOutcome(
                        outcome_id="targeted-withdrawal",
                        next_stage="response",
                        field_updates={"recall_readiness": 0.1},
                    ),
                    ActionTransitionOutcome(
                        outcome_id="full-stop-sale",
                        next_stage="response",
                        field_minimums={"severity": 0.5},
                        field_updates={"recall_readiness": 0.2},
                    ),
                ],
            )
        ],
        scoring_weights={
            "escalation": {"severity": 0.5},
            "negotiation": {"recall_readiness": 0.4},
            "economic_stress": {"severity": 0.3},
        },
        objective_profile_rules=[
            ObjectiveRecommendationRule(
                profile_name="domestic-politics-first",
                field_minimums={"severity": 0.5},
            )
        ],
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
    pack_text = pack_path.read_text(encoding="utf-8")
    assert "ProductRecallPack" in pack_text
    assert "def infer_pack_fields" in pack_text
    assert "def propose_actions" in pack_text
    assert "def sample_transition" in pack_text
    assert "def recommend_objective_profile" in pack_text
    assert "product-recall" in (domain_dir / "registry.py").read_text(encoding="utf-8")

    spec = importlib.util.spec_from_file_location("generated_product_recall", pack_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pack = module.ProductRecallPack()
    assert pack.slug() == "product-recall"


def test_synthesize_domain_branch_mode_preserves_review_gate(tmp_path: Path) -> None:
    domain_dir = tmp_path / "packages" / "core" / "src" / "forecasting_harness" / "domain"
    domain_dir.mkdir(parents=True)
    registry_path = domain_dir / "registry.py"
    registry_path.write_text(
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

    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", str(registry_path)], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)

    storage = EvolutionStorage(tmp_path / "knowledge" / "evolution")
    service = DomainEvolutionService(evolution_storage=storage, manifest_root=manifest_root)

    summary = service.synthesize_domain(_blueprint(), create_branch=True)

    branch_name = summary["branch_name"]
    assert isinstance(branch_name, str)
    assert branch_name.startswith("codex/domain-synthesis-product-recall-")
    current_branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=tmp_path, text=True).strip()
    assert current_branch == branch_name
    head_subject = subprocess.check_output(["git", "log", "-1", "--pretty=%s"], cwd=tmp_path, text=True).strip()
    assert head_subject == "feat: synthesize product-recall domain"
