from forecasting_harness.models import ObjectiveProfile


def default_objective_profile() -> ObjectiveProfile:
    return ObjectiveProfile(
        name="balanced",
        metric_weights={
            "escalation": -0.4,
            "negotiation": 0.3,
            "economic_stress": -0.3,
        },
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
    )
