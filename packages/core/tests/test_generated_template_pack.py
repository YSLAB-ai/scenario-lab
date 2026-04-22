from __future__ import annotations

from datetime import datetime, timezone

from forecasting_harness.evolution.models import (
    ActionTemplate,
    ActionTransitionOutcome,
    DomainBlueprint,
    FieldInferenceRule,
    FieldRuleTermDelta,
    FocusEntityRule,
    ObjectiveRecommendationRule,
)
from forecasting_harness.models import Actor, BehaviorProfile, BeliefField, BeliefState


def _field(value: object) -> BeliefField:
    return BeliefField(
        value=value,
        normalized_value=value,
        status="observed",
        confidence=1.0,
        last_updated_at=datetime(2026, 4, 21, 12, 0, tzinfo=timezone.utc),
    )


def test_generated_template_pack_infers_fields_and_transitions() -> None:
    from forecasting_harness.domain.generated_template import GeneratedTemplatePack
    from forecasting_harness.domain.base import InteractionModel

    class ProductRecallPack(GeneratedTemplatePack):
        BLUEPRINT = DomainBlueprint(
            slug="product-recall",
            class_name="ProductRecallPack",
            description="Recall response domain",
            focus_entity_rule=FocusEntityRule(min_count=2),
            canonical_stages=["trigger", "response", "resolution"],
            field_schema={"severity": "float", "recall_readiness": "float"},
            follow_up_questions=["How severe is the safety issue?"],
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
                            weight=0.7,
                            field_updates={"recall_readiness": 0.1},
                        ),
                        ActionTransitionOutcome(
                            outcome_id="full-stop-sale",
                            next_stage="response",
                            weight=0.3,
                            field_minimums={"severity": 0.5},
                            field_updates={"recall_readiness": 0.2},
                        ),
                    ],
                ),
            ],
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

    pack = ProductRecallPack()
    inferred = pack.infer_pack_fields(
        intake=type("Intake", (), {"event_framing": "Safety injuries reported", "current_development": "Contingency plan drafted", "known_constraints": [], "known_unknowns": []})(),
        assumptions=type("Assumptions", (), {"summary": []})(),
        approved_evidence_items=[],
    )

    assert inferred["severity"] > 0.2
    assert inferred["recall_readiness"] > 0.3

    state = BeliefState(
        run_id="run-1",
        revision_id="r1",
        domain_pack="product-recall",
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[
            Actor(
                actor_id="acme",
                name="Acme",
                behavior_profile=BehaviorProfile(domestic_sensitivity=0.9),
            )
        ],
        fields={
            "event_framing": _field("Safety injuries reported"),
            "severity": _field(inferred["severity"]),
            "recall_readiness": _field(inferred["recall_readiness"]),
        },
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch="trigger",
        horizon="30d",
        phase="trigger",
    )

    actions = pack.propose_actions(state)
    assert actions
    transitions = pack.sample_transition(state, actions[0])
    assert [item["outcome_id"] for item in transitions] == ["targeted-withdrawal", "full-stop-sale"]
    next_state = transitions[0]["next_state"] if isinstance(transitions[0], dict) else transitions[0]
    assert next_state.phase == "response"
    assert pack.score_state(next_state)
    assert pack.recommend_objective_profile(
        type("Intake", (), {"event_framing": "Assess recall"})(),
        state,
    ).name == "domestic-politics-first"
