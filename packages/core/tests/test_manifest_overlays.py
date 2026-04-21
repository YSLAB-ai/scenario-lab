from __future__ import annotations

import json
from pathlib import Path

from forecasting_harness.domain.template_utils import apply_manifest_action_biases, manifest_state_delta
from forecasting_harness.knowledge.manifests import AdaptiveActionBias, DomainManifest, load_domain_manifest


def test_manifest_state_overlay_boosts_field_inference(tmp_path: Path) -> None:
    manifest = {
        "slug": "company-action",
        "description": "test manifest",
        "adaptive_state_terms": {
            "board_cohesion": [{"terms": ["board reassurance"], "delta": 0.12}],
        },
    }
    path = tmp_path / "company-action.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    loaded = load_domain_manifest("company-action", root_override=tmp_path)

    assert loaded.adaptive_state_terms["board_cohesion"][0].delta == 0.12
    assert manifest_state_delta("board reassurance", "board_cohesion", manifest=loaded) == 0.12


def test_manifest_action_biases_adjust_prior() -> None:
    actions = [{"action_id": "contain-message", "label": "Contain message", "prior": 0.2}]
    biased = apply_manifest_action_biases(
        text="board reassurance",
        actions=actions,
        manifest=DomainManifest(
            slug="company-action",
            description="test",
            adaptive_action_biases=[
                AdaptiveActionBias(target="contain-message", terms=["board reassurance"], delta=0.15)
            ],
        ),
    )

    assert biased[0]["prior"] > 0.2

