from datetime import datetime, timezone

import pytest

from forecasting_harness.knowledge.manifests import AdaptiveActionBias, DomainManifest
from forecasting_harness.models import Actor, BehaviorProfile, BeliefField, BeliefState
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


def test_company_action_pack_recommends_focal_run_lens_for_board_crisis() -> None:
    from forecasting_harness.domain.company_action import CompanyActionPack

    pack = CompanyActionPack()
    intake = IntakeDraft(
        event_framing="Assess whether board confidence and leadership credibility can stabilize Acme Corp.",
        focus_entities=["Acme Corp"],
        current_development="Board cohesion is weakening and stakeholder confidence is under pressure after the CEO transition.",
        current_stage="trigger",
        time_horizon="30d",
    )
    state = _state(
        "company-action",
        "trigger",
        {
            "board_cohesion": _field(0.32),
            "cash_runway_months": _field(10),
            "brand_sentiment": _field(0.38),
            "operational_stability": _field(0.46),
            "regulatory_pressure": _field(0.28),
        },
    ).model_copy(
        update={
            "actors": [
                Actor(
                    actor_id="acme-corp",
                    name="Acme Corp",
                    behavior_profile=BehaviorProfile(
                        domestic_sensitivity=0.86,
                        reputational_sensitivity=0.8,
                        negotiation_openness=0.42,
                    ),
                ),
                Actor(
                    actor_id="regulator",
                    name="Regulator",
                    behavior_profile=BehaviorProfile(
                        domestic_sensitivity=0.3,
                        negotiation_openness=0.55,
                    ),
                ),
            ]
        }
    )

    profile = pack.recommend_objective_profile(intake, state)

    assert profile.name == "domestic-politics-first"
    assert profile.aggregation_mode == "focal-actor"
    assert profile.focal_actor_id == "acme-corp"


def test_company_action_pack_scores_actor_impacts_from_company_state() -> None:
    from forecasting_harness.domain.company_action import CompanyActionPack

    pack = CompanyActionPack()
    state = _state(
        "company-action",
        "market-response",
        {
            "board_cohesion": _field(0.38),
            "cash_runway_months": _field(6),
            "brand_sentiment": _field(0.34),
            "operational_stability": _field(0.42),
            "regulatory_pressure": _field(0.62),
        },
    ).model_copy(
        update={
            "actors": [
                Actor(
                    actor_id="acme-corp",
                    name="Acme Corp",
                    behavior_profile=BehaviorProfile(
                        domestic_sensitivity=0.8,
                        economic_pain_tolerance=0.35,
                        negotiation_openness=0.45,
                        reputational_sensitivity=0.82,
                        coercive_bias=0.15,
                    ),
                ),
                Actor(
                    actor_id="regulator",
                    name="Regulator",
                    behavior_profile=BehaviorProfile(
                        domestic_sensitivity=0.4,
                        negotiation_openness=0.65,
                        reputational_sensitivity=0.35,
                        coercive_bias=0.05,
                    ),
                ),
            ]
        }
    )

    actor_impacts = pack.score_actor_impacts(state)

    assert actor_impacts["acme-corp"]["domestic_sensitivity"] > actor_impacts["regulator"]["domestic_sensitivity"]
    assert actor_impacts["acme-corp"]["reputational_sensitivity"] > 0.7
    assert actor_impacts["acme-corp"]["economic_pain_tolerance"] < 0.35
    assert actor_impacts["regulator"]["negotiation_openness"] > 0.5


def test_pandemic_response_pack_recommends_focal_run_lens_for_compliance_crisis() -> None:
    from forecasting_harness.domain.pandemic_response import PandemicResponsePack

    pack = PandemicResponsePack()
    intake = IntakeDraft(
        event_framing="Assess whether government credibility and public compliance can contain the next pandemic wave.",
        focus_entities=["National Government", "Public Health System"],
        current_development="Officials face domestic pressure as hospital strain rises and public compliance weakens.",
        current_stage="trigger",
        time_horizon="30d",
    )
    state = _state(
        "pandemic-response",
        "trigger",
        {
            "hospital_strain": _field(0.72),
            "policy_alignment": _field(0.41),
            "public_compliance": _field(0.32),
            "testing_capacity": _field(0.46),
            "transmission_pressure": _field(0.76),
            "vaccine_readiness": _field(0.22),
        },
    ).model_copy(
        update={
            "actors": [
                Actor(
                    actor_id="national-government",
                    name="National Government",
                    behavior_profile=BehaviorProfile(
                        domestic_sensitivity=0.88,
                        negotiation_openness=0.48,
                        reputational_sensitivity=0.72,
                    ),
                ),
                Actor(
                    actor_id="public-health-system",
                    name="Public Health System",
                    behavior_profile=BehaviorProfile(
                        domestic_sensitivity=0.64,
                        negotiation_openness=0.62,
                        alliance_dependence=0.58,
                    ),
                ),
            ]
        }
    )

    profile = pack.recommend_objective_profile(intake, state)

    assert profile.name == "domestic-politics-first"
    assert profile.aggregation_mode == "focal-actor"
    assert profile.focal_actor_id == "national-government"


def test_pandemic_response_pack_scores_actor_impacts_from_response_state() -> None:
    from forecasting_harness.domain.pandemic_response import PandemicResponsePack

    pack = PandemicResponsePack()
    state = _state(
        "pandemic-response",
        "surge-response",
        {
            "hospital_strain": _field(0.78),
            "policy_alignment": _field(0.44),
            "public_compliance": _field(0.35),
            "testing_capacity": _field(0.4),
            "transmission_pressure": _field(0.82),
            "vaccine_readiness": _field(0.18),
        },
    ).model_copy(
        update={
            "actors": [
                Actor(
                    actor_id="national-government",
                    name="National Government",
                    behavior_profile=BehaviorProfile(
                        domestic_sensitivity=0.82,
                        economic_pain_tolerance=0.28,
                        negotiation_openness=0.4,
                        reputational_sensitivity=0.75,
                        coercive_bias=0.22,
                    ),
                ),
                Actor(
                    actor_id="public-health-system",
                    name="Public Health System",
                    behavior_profile=BehaviorProfile(
                        domestic_sensitivity=0.68,
                        negotiation_openness=0.58,
                        alliance_dependence=0.64,
                        coercive_bias=0.08,
                    ),
                ),
            ]
        }
    )

    actor_impacts = pack.score_actor_impacts(state)

    assert actor_impacts["national-government"]["domestic_sensitivity"] > 0.8
    assert actor_impacts["national-government"]["negotiation_openness"] < 0.4
    assert actor_impacts["public-health-system"]["alliance_dependence"] > 0.6
    assert actor_impacts["public-health-system"]["coercive_bias"] < 0.1
