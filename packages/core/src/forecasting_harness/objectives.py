from forecasting_harness.models import ObjectiveProfile


def objective_profile_by_name(name: str) -> ObjectiveProfile:
    profile_name = {
        "balanced": "balanced-system",
        "balanced-system": "balanced-system",
        "domestic-politics-first": "domestic-politics-first",
    }.get(name, name)

    if profile_name == "balanced-system":
        return ObjectiveProfile(
            name="balanced-system",
            metric_weights={
                "escalation": -0.4,
                "negotiation": 0.3,
                "economic_stress": -0.3,
            },
            veto_thresholds={},
            risk_tolerance=0.5,
            asymmetry_penalties={},
            actor_metric_weights={
                "domestic_sensitivity": 0.25,
                "economic_pain_tolerance": -0.2,
                "negotiation_openness": 0.2,
                "reputational_sensitivity": 0.15,
                "alliance_dependence": 0.1,
                "coercive_bias": -0.1,
            },
            actor_weights={},
            aggregation_mode="balanced-system",
            focal_actor_id=None,
            destabilization_penalty=0.1,
        )

    if profile_name == "domestic-politics-first":
        return ObjectiveProfile(
            name="domestic-politics-first",
            metric_weights={
                "escalation": -0.4,
                "negotiation": 0.3,
                "economic_stress": -0.3,
            },
            veto_thresholds={},
            risk_tolerance=0.5,
            asymmetry_penalties={},
            actor_metric_weights={
                "domestic_sensitivity": 0.6,
                "economic_pain_tolerance": -0.15,
                "negotiation_openness": 0.15,
                "reputational_sensitivity": 0.2,
                "alliance_dependence": 0.05,
                "coercive_bias": -0.05,
            },
            actor_weights={},
            aggregation_mode="focal-actor",
            focal_actor_id=None,
            destabilization_penalty=0.15,
        )

    raise KeyError(f"unknown objective profile: {name}")


def default_objective_profile() -> ObjectiveProfile:
    return objective_profile_by_name("balanced")
