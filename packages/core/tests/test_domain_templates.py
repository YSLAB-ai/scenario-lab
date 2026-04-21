from datetime import datetime, timezone

import pytest

from forecasting_harness.knowledge.manifests import AdaptiveActionBias, DomainManifest
from forecasting_harness.models import BeliefField, BeliefState
from forecasting_harness.workflow.models import IntakeDraft


def _field(value: object) -> BeliefField:
    return BeliefField(
        value=value,
        normalized_value=value,
        status="observed",
        confidence=1.0,
        last_updated_at=datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc),
    )


def _state(pack_slug: str, phase: str, fields: dict[str, BeliefField]) -> BeliefState:
    from forecasting_harness.domain.base import InteractionModel

    return BeliefState(
        run_id="run-1",
        revision_id="r1",
        domain_pack=pack_slug,
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[],
        fields=fields,
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch=phase,
        horizon="30d",
        phase=phase,
    )


@pytest.mark.parametrize(
    ("module_name", "class_name", "slug", "focus_entities", "pack_fields"),
    [
        (
            "forecasting_harness.domain.company_action",
            "CompanyActionPack",
            "company-action",
            ["Acme Corp"],
            {"cash_runway_months": 9, "brand_sentiment": 0.55},
        ),
        (
            "forecasting_harness.domain.election_shock",
            "ElectionShockPack",
            "election-shock",
            ["Candidate A", "Candidate B"],
            {"poll_margin": 1.5, "turnout_energy": 0.6},
        ),
        (
            "forecasting_harness.domain.market_shock",
            "MarketShockPack",
            "market-shock",
            ["Federal Reserve", "Bond Market"],
            {"liquidity_stress": 0.45, "rate_pressure": 0.6},
        ),
        (
            "forecasting_harness.domain.pandemic_response",
            "PandemicResponsePack",
            "pandemic-response",
            ["National Government", "Public Health System"],
            {"transmission_pressure": 0.7, "hospital_strain": 0.6},
        ),
        (
            "forecasting_harness.domain.regulatory_enforcement",
            "RegulatoryEnforcementPack",
            "regulatory-enforcement",
            ["Agency", "Target Company"],
            {"enforcement_momentum": 0.5, "compliance_posture": "mixed"},
        ),
        (
            "forecasting_harness.domain.supply_chain_disruption",
            "SupplyChainDisruptionPack",
            "supply-chain-disruption",
            ["Manufacturer", "Critical Supplier"],
            {"inventory_cover_days": 18, "substitution_flexibility": 0.4},
        ),
    ],
)
def test_domain_template_pack_exposes_stages_actions_and_transitions(
    module_name: str,
    class_name: str,
    slug: str,
    focus_entities: list[str],
    pack_fields: dict[str, object],
) -> None:
    module = __import__(module_name, fromlist=[class_name])
    pack = getattr(module, class_name)()
    intake = IntakeDraft(
        event_framing="Assess scenario evolution",
        focus_entities=focus_entities,
        current_development="A material development occurred",
        current_stage=pack.canonical_phases()[0],
        time_horizon="30d",
        pack_fields=pack_fields,
    )

    assert pack.slug() == slug
    assert pack.canonical_phases()
    assert pack.validate_intake(intake) == []
    assert pack.extend_schema()

    state = _state(
        slug,
        pack.canonical_phases()[0],
        {"event_framing": _field(intake.event_framing), **{name: _field(value) for name, value in pack_fields.items()}},
    )
    actions = pack.propose_actions(state)

    assert actions
    transition = pack.sample_transition(state, actions[0])[0]
    next_state = transition["next_state"] if isinstance(transition, dict) else transition
    assert next_state.phase != state.phase
    assert pack.score_state(next_state)


def test_company_action_pack_uses_manifest_action_bias(monkeypatch: pytest.MonkeyPatch) -> None:
    from forecasting_harness.domain.company_action import CompanyActionPack
    import forecasting_harness.domain.template_utils as template_utils

    monkeypatch.setattr(
        template_utils,
        "load_domain_manifest",
        lambda slug: DomainManifest(
            slug=slug,
            description="test",
            adaptive_action_biases=[
                AdaptiveActionBias(target="contain-message", terms=["board reassurance"], delta=0.2)
            ],
        ),
    )

    pack = CompanyActionPack()
    state = _state(
        "company-action",
        "trigger",
        {
            "event_framing": _field("board reassurance needed"),
            "board_cohesion": _field(0.4),
            "cash_runway_months": _field(9),
            "brand_sentiment": _field(0.5),
            "operational_stability": _field(0.5),
            "regulatory_pressure": _field(0.2),
        },
    )

    contain_before = next(action for action in pack.propose_actions(state) if action["action_id"] == "contain-message")

    monkeypatch.setattr(
        template_utils,
        "load_domain_manifest",
        lambda slug: DomainManifest(slug=slug, description="test"),
    )
    contain_after = next(action for action in pack.propose_actions(state) if action["action_id"] == "contain-message")

    assert contain_before["prior"] > contain_after["prior"]
