from datetime import datetime, timezone

import pytest

from forecasting_harness.knowledge.manifests import AdaptiveActionBias, DomainManifest
from forecasting_harness.models import Actor, BehaviorProfile, BeliefField, BeliefState
from forecasting_harness.objectives import objective_profile_by_name
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


def test_election_pack_prefers_targeted_deal_during_coalition_shaping() -> None:
    from forecasting_harness.domain.election_shock import ElectionShockPack

    pack = ElectionShockPack()
    state = _state(
        "election-shock",
        "coalition-shaping",
        {
            "coalition_fragility": _field(0.34),
            "donor_confidence": _field(0.48),
            "message_discipline": _field(0.5),
            "poll_margin": _field(0.0),
            "turnout_energy": _field(0.5),
        },
    )

    actions = {action["action_id"]: action for action in pack.propose_actions(state)}
    targeted_next = pack.sample_transition(state, actions["targeted-deal"])[0]
    discipline_next = pack.sample_transition(state, actions["discipline-message"])[0]

    targeted_state = targeted_next["next_state"] if isinstance(targeted_next, dict) else targeted_next
    discipline_state = discipline_next["next_state"] if isinstance(discipline_next, dict) else discipline_next

    lens = objective_profile_by_name("balanced-system")
    targeted_score, _ = lens.aggregate(pack.score_state(targeted_state), {})
    discipline_score, _ = lens.aggregate(pack.score_state(discipline_state), {})

    assert targeted_score > discipline_score


def test_election_pack_infers_governing_math_pressure_for_hung_parliament() -> None:
    from forecasting_harness.domain.election_shock import ElectionShockPack
    from forecasting_harness.workflow.models import AssumptionSummary, EvidencePacketItem, IntakeDraft

    pack = ElectionShockPack()
    intake = IntakeDraft(
        event_framing="Assess coalition bargaining after a hung parliament leaves no party able to govern alone.",
        focus_entities=["Conservative Party", "Labour Party"],
        current_development="A fragmented parliament pushes leaders toward confidence-and-supply talks and coalition bargaining.",
        current_stage="coalition-shaping",
        time_horizon="21d",
        known_constraints=["No single party has a governing majority"],
        known_unknowns=["Whether a support pact can stabilize the government quickly"],
    )
    assumptions = AssumptionSummary(summary=["Elite bargaining matters more than fresh persuasion."])
    evidence = [
        EvidencePacketItem(
            evidence_id="r1:hung:1",
            source_id="hung-parliament",
            source_title="Hung parliament",
            reason="test",
            raw_passages=[
                "The election produced a hung parliament with no single party able to govern alone, forcing confidence-and-supply talks."
            ],
        )
    ]

    fields = pack.infer_pack_fields(intake, assumptions, evidence)

    assert "governing_math_pressure" in fields
    assert float(fields["governing_math_pressure"]) > 0.6


def test_election_pack_targeted_deal_has_multiple_outcomes_under_governing_pressure() -> None:
    from forecasting_harness.domain.election_shock import ElectionShockPack

    pack = ElectionShockPack()
    state = _state(
        "election-shock",
        "coalition-shaping",
        {
            "coalition_fragility": _field(0.52),
            "donor_confidence": _field(0.44),
            "governing_math_pressure": _field(0.82),
            "message_discipline": _field(0.47),
            "poll_margin": _field(0.02),
            "turnout_energy": _field(0.51),
        },
    )

    actions = {action["action_id"]: action for action in pack.propose_actions(state)}
    outcomes = pack.sample_transition(state, actions["targeted-deal"])

    assert len(outcomes) >= 2
    assert all(isinstance(item, dict) and "outcome_id" in item for item in outcomes)


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


def test_market_shock_pack_uses_generic_actor_utility_defaults() -> None:
    from forecasting_harness.domain.market_shock import MarketShockPack

    pack = MarketShockPack()
    intake = IntakeDraft(
        event_framing="Assess whether central bank credibility or market stability dominates the next move.",
        focus_entities=["Federal Reserve", "Treasury Market"],
        current_development="Funding stress rises while policymakers face credibility pressure and rapid repricing.",
        current_stage="trigger",
        time_horizon="30d",
    )
    state = _state(
        "market-shock",
        "trigger",
        {
            "contagion_risk": _field(0.74),
            "liquidity_stress": _field(0.81),
            "policy_credibility": _field(0.33),
            "policy_optionality": _field(0.46),
            "rate_pressure": _field(0.79),
        },
    ).model_copy(
        update={
            "actors": [
                Actor(
                    actor_id="federal-reserve",
                    name="Federal Reserve",
                    behavior_profile=BehaviorProfile(
                        domestic_sensitivity=0.88,
                        reputational_sensitivity=0.84,
                        negotiation_openness=0.36,
                    ),
                ),
                Actor(
                    actor_id="treasury-market",
                    name="Treasury Market",
                    behavior_profile=BehaviorProfile(
                        domestic_sensitivity=0.42,
                        economic_pain_tolerance=0.28,
                        negotiation_openness=0.52,
                    ),
                ),
            ]
        }
    )

    profile = pack.recommend_objective_profile(intake, state)
    actor_impacts = pack.score_actor_impacts(state)

    assert profile.name == "domestic-politics-first"
    assert profile.aggregation_mode == "focal-actor"
    assert profile.focal_actor_id == "federal-reserve"
    assert set(actor_impacts) == {"federal-reserve", "treasury-market"}
    assert actor_impacts["federal-reserve"]["domestic_sensitivity"] > actor_impacts["treasury-market"]["domestic_sensitivity"]
    assert actor_impacts["federal-reserve"]["reputational_sensitivity"] > 0.75


def test_market_pack_infers_institutional_fragility_for_bank_resolution_signal() -> None:
    from forecasting_harness.domain.market_shock import MarketShockPack
    from forecasting_harness.workflow.models import AssumptionSummary, EvidencePacketItem, IntakeDraft

    pack = MarketShockPack()
    intake = IntakeDraft(
        event_framing="Assess market scenarios after a bank failure triggers emergency guarantees and a forced takeover.",
        focus_entities=["Swiss Authorities", "Swiss Banking System"],
        current_development="Officials announce guarantees, extraordinary liquidity support, and a forced takeover to contain market stress.",
        current_stage="trigger",
        time_horizon="21d",
        known_constraints=["Depositor confidence must be preserved quickly"],
        known_unknowns=["Whether the package will fully contain contagion"],
    )
    assumptions = AssumptionSummary(summary=["Authorities will prioritize system stability over a passive wait-and-see response."])
    evidence = [
        EvidencePacketItem(
            evidence_id="r1:rescue:1",
            source_id="rescue-package",
            source_title="Rescue package",
            reason="test",
            raw_passages=[
                "A forced takeover backed by official guarantees and extraordinary liquidity support is used to contain broader financial contagion."
            ],
        )
    ]

    fields = pack.infer_pack_fields(intake, assumptions, evidence)

    assert "institutional_fragility" in fields
    assert float(fields["institutional_fragility"]) > 0.6


def test_market_pack_coordinated_backstop_has_resolution_outcomes_when_fragility_is_high() -> None:
    from forecasting_harness.domain.market_shock import MarketShockPack

    pack = MarketShockPack()
    state = _state(
        "market-shock",
        "trigger",
        {
            "contagion_risk": _field(0.84),
            "institutional_fragility": _field(0.86),
            "liquidity_stress": _field(0.79),
            "policy_credibility": _field(0.46),
            "policy_optionality": _field(0.72),
            "rate_pressure": _field(0.58),
            "event_framing": _field("forced takeover with guarantees"),
        },
    )

    actions = {action["action_id"]: action for action in pack.propose_actions(state)}
    outcomes = pack.sample_transition(state, actions["coordinated-backstop"])

    assert len(outcomes) >= 2
    assert all(isinstance(item, dict) and "outcome_id" in item for item in outcomes)


def test_regulatory_enforcement_pack_uses_generic_actor_utility_defaults() -> None:
    from forecasting_harness.domain.regulatory_enforcement import RegulatoryEnforcementPack

    pack = RegulatoryEnforcementPack()
    intake = IntakeDraft(
        event_framing="Assess whether agency credibility or settlement stability drives the next enforcement move.",
        focus_entities=["Agency", "Target Company"],
        current_development="The agency faces political scrutiny while the company weighs settlement against contesting findings.",
        current_stage="trigger",
        time_horizon="30d",
    )
    state = _state(
        "regulatory-enforcement",
        "trigger",
        {
            "compliance_posture": _field("mixed"),
            "enforcement_momentum": _field(0.76),
            "litigation_readiness": _field(0.62),
            "public_attention": _field(0.8),
            "remedy_severity": _field(0.71),
        },
    ).model_copy(
        update={
            "actors": [
                Actor(
                    actor_id="agency",
                    name="Agency",
                    behavior_profile=BehaviorProfile(
                        domestic_sensitivity=0.83,
                        reputational_sensitivity=0.79,
                        negotiation_openness=0.41,
                    ),
                ),
                Actor(
                    actor_id="target-company",
                    name="Target Company",
                    behavior_profile=BehaviorProfile(
                        domestic_sensitivity=0.56,
                        economic_pain_tolerance=0.34,
                        negotiation_openness=0.58,
                    ),
                ),
            ]
        }
    )

    profile = pack.recommend_objective_profile(intake, state)
    actor_impacts = pack.score_actor_impacts(state)

    assert profile.name == "domestic-politics-first"
    assert profile.aggregation_mode == "focal-actor"
    assert profile.focal_actor_id == "agency"
    assert set(actor_impacts) == {"agency", "target-company"}
    assert actor_impacts["agency"]["domestic_sensitivity"] > actor_impacts["target-company"]["domestic_sensitivity"]
    assert actor_impacts["agency"]["reputational_sensitivity"] > 0.7
