from forecasting_harness.models import ObjectiveProfile


def normalize_objective_profile_name(name: str) -> str:
    normalized_name = {
        "balanced": "balanced-system",
        "balanced-system": "balanced-system",
        "domestic-politics-first": "domestic-politics-first",
    }.get(name, name)
    if normalized_name not in {"balanced-system", "domestic-politics-first"}:
        raise ValueError(f"unknown objective profile: {name}")
    return normalized_name


def normalize_selected_objective_profile_name(name: str | None) -> str:
    if name is None:
        return ""
    stripped_name = name.strip()
    if not stripped_name:
        return ""
    return normalize_objective_profile_name(stripped_name)


def objective_profile_by_name(name: str) -> ObjectiveProfile:
    profile_name = normalize_objective_profile_name(name)

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
            focal_weight=1.0,
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
            focal_weight=2.0,
            destabilization_penalty=0.15,
        )

def default_objective_profile() -> ObjectiveProfile:
    return objective_profile_by_name("balanced")
